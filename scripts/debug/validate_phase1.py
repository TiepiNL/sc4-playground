#!/usr/bin/env python3
"""
Phase 1: Validate DBPF + Compression Layer
Focus on TID=0x6534284A + GID=0xA8FBD372 filtering and QFS decompression
"""

import os
import sys
import struct

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import qfs

def validate_phase1(filename):
    """Phase 1: Validate DBPF parsing and LotConfiguration identification."""
    
    print("=== PHASE 1: DBPF + Compression Validation ===")
    
    with open(filename, 'rb') as f:
        # Read DBPF header
        header = f.read(96)
        if header[:4] != b'DBPF':
            print("[FAIL] Not a valid DBPF file")
            return False
        
        major_version = struct.unpack('<I', header[4:8])[0]
        minor_version = struct.unpack('<I', header[8:12])[0]
        index_entry_count = struct.unpack('<I', header[36:40])[0]
        index_offset = struct.unpack('<I', header[40:44])[0]
        index_size = struct.unpack('<I', header[44:48])[0]
        
        print(f"[OK] DBPF Version: {major_version}.{minor_version}")
        print(f"[OK] Total index entries: {index_entry_count}")
        
        # Read entire file
        f.seek(0)
        all_data = f.read()
        
        # Read index
        index_data = all_data[index_offset:index_offset + index_size]
        
        # Parse DBDF for compression info
        compressed_files = {}
        dbdf_tid = 0xE86B1EEF
        dbdf_gid = 0xE86B1EEF  
        dbdf_iid = 0x286B1F03
        
        for i in range(index_entry_count):
            entry_offset = i * 20
            entry = index_data[entry_offset:entry_offset + 20]
            tid = struct.unpack('<I', entry[0:4])[0]
            gid = struct.unpack('<I', entry[4:8])[0]
            iid = struct.unpack('<I', entry[8:12])[0]
            offset = struct.unpack('<I', entry[12:16])[0]
            size = struct.unpack('<I', entry[16:20])[0]
            
            if tid == dbdf_tid and gid == dbdf_gid and iid == dbdf_iid:
                print(f"[OK] Found DBDF at offset {offset}, size {size}")
                
                dbdf_data = all_data[offset:offset + size]
                pos = 0
                while pos + 16 <= len(dbdf_data):
                    entry_tid = struct.unpack('<I', dbdf_data[pos:pos+4])[0]
                    entry_gid = struct.unpack('<I', dbdf_data[pos+4:pos+8])[0] 
                    entry_iid = struct.unpack('<I', dbdf_data[pos+8:pos+12])[0]
                    uncompressed_size = struct.unpack('<I', dbdf_data[pos+12:pos+16])[0]
                    
                    tgi_key = (entry_tid, entry_gid, entry_iid)
                    compressed_files[tgi_key] = uncompressed_size
                    pos += 16
                break
        
        print(f"[OK] Found {len(compressed_files)} compressed files in DBDF")
        
        # Filter for LotConfiguration exemplars
        lot_config_candidates = []
        lot_config_tid = 0x6534284A
        lot_config_gid = 0xA8FBD372
        
        for i in range(index_entry_count):
            entry_offset = i * 20
            entry = index_data[entry_offset:entry_offset + 20]
            
            tid = struct.unpack('<I', entry[0:4])[0]
            gid = struct.unpack('<I', entry[4:8])[0] 
            iid = struct.unpack('<I', entry[8:12])[0]
            offset = struct.unpack('<I', entry[12:16])[0]
            size = struct.unpack('<I', entry[16:20])[0]
            
            # Filter for LotConfiguration exemplars
            if tid == lot_config_tid and gid == lot_config_gid:
                lot_config_candidates.append({
                    'tid': tid,
                    'gid': gid,
                    'iid': iid,
                    'offset': offset,
                    'size': size
                })
        
        print(f"[OK] Found {len(lot_config_candidates)} LotConfiguration candidates (TID=0x{lot_config_tid:08X}, GID=0x{lot_config_gid:08X})")
        
        # Test decompression on first few candidates
        decompression_results = []
        
        for i, candidate in enumerate(lot_config_candidates[:10]):  # Test first 10
            iid = candidate['iid']
            offset = candidate['offset']
            size = candidate['size']
            
            # Get file data
            file_data = all_data[offset:offset + size]
            tgi_key = (lot_config_tid, lot_config_gid, iid)
            expected_size = compressed_files.get(tgi_key)
            
            # Check compression format
            is_compressed = False
            decompressed_size = None
            format_type = "Unknown"
            
            if len(file_data) >= 6 and file_data[4:6] == b'\x10\xfb':
                # QFS compressed with 4-byte wrapper
                is_compressed = True
                format_type = "QFS+Wrapper"
                try:
                    # Skip 4-byte wrapper and decompress
                    qfs_data = file_data[4:]
                    decompressed = qfs.decompress(qfs_data, expected_size, len(qfs_data))
                    decompressed_size = len(decompressed)
                except Exception as e:
                    format_type = f"QFS+Wrapper (FAILED: {e})"
                    
            elif file_data[:4] == b'EQZB':
                # Uncompressed EQZB
                format_type = "EQZB (Uncompressed)"
                decompressed_size = len(file_data)
            
            result = {
                'iid': f"0x{iid:08X}",
                'compressed_size': len(file_data),
                'expected_uncompressed': expected_size,
                'actual_uncompressed': decompressed_size,
                'format': format_type,
                'decompression_ok': decompressed_size == expected_size if expected_size else None
            }
            
            decompression_results.append(result)
            
            status = "[OK]" if result['decompression_ok'] else "[FAIL]" if result['decompression_ok'] is False else "[?]"
            print(f"  {status} {result['iid']}: {result['compressed_size']} -> {result['actual_uncompressed']} bytes ({result['format']})")
        
        # Summary
        successful_decompressions = sum(1 for r in decompression_results if r['decompression_ok'])
        failed_decompressions = sum(1 for r in decompression_results if r['decompression_ok'] is False)
        
        print(f"\n=== PHASE 1 SUMMARY ===")
        print(f"[OK] LotConfiguration candidates found: {len(lot_config_candidates)}")
        print(f"[OK] Successful decompressions: {successful_decompressions}")
        print(f"[FAIL] Failed decompressions: {failed_decompressions}")
        
        if len(lot_config_candidates) >= 100:
            print(f"[OK] PHASE 1 PASSED: Found expected number of LotConfigurations ({len(lot_config_candidates)})")
        else:
            print(f"[FAIL] PHASE 1 WARNING: Only found {len(lot_config_candidates)} LotConfigurations (expected hundreds)")
        
        return len(lot_config_candidates) > 0

def main():
    if len(sys.argv) != 2:
        print("Usage: python validate_phase1.py <dbpf_file>")
        return 1
    
    filename = sys.argv[1]
    success = validate_phase1(filename)
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
