import io

def decompress(data: bytes, uncompressed_size: int = None, compressed_size: int = None) -> bytes:
    """
    Decompresses QFS/RefPack compressed data following the exact C reference
    implementation from SC4Mapper-2013 by Denis Auroux.
    
    Args:
        data: QFS compressed data (should start with QFS header)
        uncompressed_size: Expected uncompressed size from DBPF entry (+9 from DBDF)
        compressed_size: Expected compressed size from DBPF entry (should match len(data))
    """
    import os
    debug = os.getenv('QFS_DEBUG') == 'true'
    
    if debug:
        print(f"[QFS DEBUG] Input: {len(data)} bytes")
        print(f"[QFS DEBUG] First 16 input bytes: {data[:16].hex()}")
    
    # Validate compressed size matches DBPF entry
    if compressed_size and len(data) != compressed_size:
        raise ValueError(f"QFS data size {len(data)} doesn't match DBPF compressed size {compressed_size}")
    
    # Extract uncompressed size from QFS header (bytes 2-4, big-endian)
    # Following the C code: outlen=(inbuf[2]<<16)+(inbuf[3]<<8)+inbuf[4];
    header_uncompressed_size = (data[2] << 16) + (data[3] << 8) + data[4]
    
    # Validate uncompressed size matches DBPF entry (+9 from DBDF)
    if uncompressed_size and header_uncompressed_size != uncompressed_size:
        raise ValueError(f"QFS header uncompressed size {header_uncompressed_size} doesn't match DBPF size {uncompressed_size}")
    
    if debug:
        print(f"[QFS DEBUG] Header uncompressed size: {header_uncompressed_size}")
        print(f"[QFS DEBUG] DBPF uncompressed size: {uncompressed_size}")
        print(f"[QFS DEBUG] DBPF compressed size: {compressed_size}")
    
    # Create output buffer
    out = bytearray(header_uncompressed_size)
    
    # Set starting position following C code: if (inbuf[0]&0x01) inpos=8; else inpos=5;
    inpos = 8 if (data[0] & 0x01) else 5
    outpos = 0
    
    if debug:
        print(f"[QFS DEBUG] Starting inpos: {inpos} (based on first byte: 0x{data[0]:02X})")
    
    def memcpy(out_buf, out_start, in_buf, in_start, length):
        """LZ-compatible memcopy - handles overlapping copies correctly"""
        for i in range(length):
            if out_start + i >= len(out_buf) or in_start + i >= len(in_buf):
                break
            out_buf[out_start + i] = in_buf[in_start + i]
    
    # Main decompression loop following C code exactly
    # while ((inpos<inlen)&&(inbuf[inpos]<0xFC))
    while inpos < len(data) and data[inpos] < 0xfc:
        if inpos + 2 >= len(data):
            break
            
        # Extract control codes: packcode=inbuf[inpos]; a=inbuf[inpos+1]; b=inbuf[inpos+2];
        code = data[inpos]
        a = data[inpos + 1]
        b = data[inpos + 2]
        
        if not (code & 0x80):
            # Two-byte control: copy literals then back-reference 
            # len=packcode&3; mmemcpy(outbuf+outpos,inbuf+inpos+2,len);
            length = code & 3
            if inpos + 2 + length <= len(data):
                memcpy(out, outpos, data, inpos + 2, length)
                inpos += length + 2
                outpos += length
            
            # Repeat data already in the output
            # len=((packcode&0x1c)>>2)+3; offset=((packcode>>5)<<8)+a+1;
            length = ((code & 0x1c) >> 2) + 3
            offset = ((code >> 5) << 8) + a + 1
            memcpy(out, outpos, out, outpos - offset, length)
            outpos += length
            
        elif not (code & 0x40):
            # Three-byte control
            # len=(a>>6)&3; mmemcpy(outbuf+outpos,inbuf+inpos+3,len);
            if inpos + 3 >= len(data):
                break
            length = (a >> 6) & 3
            if inpos + 3 + length <= len(data):
                memcpy(out, outpos, data, inpos + 3, length)
                inpos += length + 3
                outpos += length
            
            # Repeat data already in the output
            # len=(packcode&0x3f)+4; offset=(a&0x3f)*256+b+1;
            length = (code & 0x3f) + 4
            offset = (a & 0x3f) * 256 + b + 1
            memcpy(out, outpos, out, outpos - offset, length)
            outpos += length
            
        elif not (code & 0x20):
            # Four-byte control
            # c=inbuf[inpos+3]; len=packcode&3;
            if inpos + 4 >= len(data):
                break
            c = data[inpos + 3]
            length = code & 3
            if inpos + 4 + length <= len(data):
                memcpy(out, outpos, data, inpos + 4, length)
                inpos += length + 4
                outpos += length
            
            # Repeat data already in the output
            # len=((packcode>>2)&3)*256+c+5; offset=((packcode&0x10)<<12)+256*a+b+1;
            length = ((code >> 2) & 3) * 256 + c + 5
            offset = ((code & 0x10) << 12) + 256 * a + b + 1
            memcpy(out, outpos, out, outpos - offset, length)
            outpos += length
            
        else:
            # No compression case - copy literal data
            # len=(packcode&0x1f)*4+4; mmemcpy(outbuf+outpos,inbuf+inpos+1,len);
            length = (code & 0x1f) * 4 + 4
            if inpos + 1 + length <= len(data):
                memcpy(out, outpos, data, inpos + 1, length)
                inpos += length + 1
                outpos += length
            else:
                break
    
    # Handle trailing bytes (control >= 0xfc)
    # mmemcpy(outbuf+outpos,inbuf+inpos+1,inbuf[inpos]&3);
    if inpos < len(data) and outpos < len(out):
        length = data[inpos] & 3
        if inpos + 1 + length <= len(data):
            memcpy(out, outpos, data, inpos + 1, length)
            outpos += length
    
    result = bytes(out[:outpos])
    
    if debug:
        print(f"[QFS DEBUG] Output: {len(result)} bytes (expected {header_uncompressed_size})")
        print(f"[QFS DEBUG] First 64 output bytes: {result[:64].hex()}")
        if len(result) != header_uncompressed_size:
            print(f"[QFS DEBUG] ERROR: Output size mismatch by {header_uncompressed_size - len(result)} bytes")
    
    return result
