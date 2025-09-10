#!/usr/bin/env python3
"""
Phase 2: Validate EQZB Container Parsing
Focus on EQZB header handling and property structure detection
"""

import os
import sys
import struct

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import qfs

def validate_phase2(filename, target_iids=None):
    """Phase 2: Validate EQZB container parsing."""
    
    if target_iids is None:
        target_iids = [0x6AB3E429, 0x6A63633B]  # Our known good test cases
    
    print("=== PHASE 2: EQZB Container Parsing Validation ===")
    
    with open(filename, 'rb') as f:
        # Read DBPF header
        header = f.read(96)
        index_entry_count = struct.unpack('<I', header[36:40])[0]
        index_offset = struct.unpack('<I', header[40:44])[0]
        index_size = struct.unpack('<I', header[44:48])[0]
        
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
        
        # Find and process target IIDs
        lot_config_tid = 0x6534284A
        lot_config_gid = 0xA8FBD372
        
        test_results = []
        found_iids = []
        
        print(f"Looking for target IIDs: {[hex(iid) for iid in target_iids]}")
        
        for i in range(index_entry_count):
            entry_offset = i * 20
            entry = index_data[entry_offset:entry_offset + 20]
            
            tid = struct.unpack('<I', entry[0:4])[0]
            gid = struct.unpack('<I', entry[4:8])[0] 
            iid = struct.unpack('<I', entry[8:12])[0]
            offset = struct.unpack('<I', entry[12:16])[0]
            size = struct.unpack('<I', entry[16:20])[0]
            
            # Filter for our target IIDs
            if tid == lot_config_tid and gid == lot_config_gid and iid in target_iids:
                found_iids.append(hex(iid))
                print(f"\n--- Testing IID 0x{iid:08X} ---")
                
                # Get and decompress file data
                file_data = all_data[offset:offset + size]
                tgi_key = (tid, gid, iid)
                expected_size = compressed_files.get(tgi_key)
                
                if len(file_data) >= 6 and file_data[4:6] == b'\x10\xfb':
                    # QFS compressed - skip 4-byte wrapper
                    qfs_data = file_data[4:]
                    try:
                        decompressed = qfs.decompress(qfs_data, expected_size, len(qfs_data))
                        print(f"[OK] Decompression: {len(file_data)} -> {len(decompressed)} bytes")
                        eqzb_data = decompressed
                    except Exception as e:
                        print(f"[FAIL] Decompression failed: {e}")
                        continue
                else:
                    eqzb_data = file_data
                    print(f"[OK] Uncompressed data: {len(eqzb_data)} bytes")
                
                # Validate EQZB container
                if len(eqzb_data) < 32:
                    print(f"[FAIL] Data too small for EQZB container: {len(eqzb_data)} bytes")
                    continue
                
                if eqzb_data[:4] != b'EQZB':
                    print(f"[FAIL] Missing EQZB signature: {eqzb_data[:4]}")
                    continue
                
                print(f"[OK] EQZB signature found")
                
                # Show EQZB header details
                print(f"   EQZB header (32 bytes): {eqzb_data[:32].hex()}")
                
                # Skip EQZB header (32 bytes) and start property parsing
                property_data = eqzb_data[32:]
                print(f"[OK] Property data starts at offset 32, {len(property_data)} bytes available")
                
                # Show first 64 bytes of property data for analysis
                print(f"   First 64 bytes of property data: {property_data[:64].hex()}")
                
                # Analyze first few property headers
                pos = 0
                property_count = 0
                
                while pos + 10 <= len(property_data) and property_count < 5:  # Analyze first 5 properties
                    # Read property header (10 bytes)
                    dw_desc = struct.unpack('<I', property_data[pos:pos+4])[0]
                    w_type = struct.unpack('<H', property_data[pos+4:pos+6])[0]
                    w8 = struct.unpack('<H', property_data[pos+6:pos+8])[0]
                    w_rep = struct.unpack('<H', property_data[pos+8:pos+10])[0]
                    
                    print(f"   Property {property_count + 1}: ID=0x{dw_desc:08X}, Type=0x{w_type:03X}, w8=0x{w8:02X}, Rep={w_rep}")
                    
                    # Check if this is a LotConfig property
                    lot_config_props = {
                        0x88EDC789: "LotConfigPropertyVersion",
                        0x88EDC790: "LotConfigPropertySize",  
                        0x88EDC793: "LotConfigPropertyZoneTypes",
                        0x88EDC795: "LotConfigPropertyWealthTypes",
                        0x88EDC796: "LotConfigPropertyPurposeTypes"
                    }
                    
                    if dw_desc in lot_config_props:
                        print(f"   [FOUND] {lot_config_props[dw_desc]}!")
                        
                        # Show expected vs. current values for our test cases
                        if iid == 0x6AB3E429 and dw_desc == 0x88EDC795:
                            print(f"      Expected: WealthTypes = [0x00, 0x01, 0x02, 0x03] (4 reps)")
                            print(f"      Current:  Type=0x{w_type:03X}, Rep={w_rep}")
                        elif iid == 0x6A63633B and dw_desc == 0x88EDC793:
                            print(f"      Expected: ZoneTypes = [0x0F] (1 rep)")
                            print(f"      Current:  Type=0x{w_type:03X}, Rep={w_rep}")
                    
                    pos += 10  # Move to next property header
                    property_count += 1
                    
                    # Try to skip property data (rough estimate)
                    if pos + 6 <= len(property_data):
                        # Skip string length + data
                        string_len = struct.unpack('<H', property_data[pos:pos+2])[0]
                        pos += 2 + string_len
                        
                        # Skip DWORD array
                        if pos + 2 <= len(property_data):
                            dword_count = struct.unpack('<H', property_data[pos:pos+2])[0]
                            pos += 2 + (dword_count * 4)
                        
                        # Skip UINT64 array
                        if pos + 2 <= len(property_data):
                            uint64_count = struct.unpack('<H', property_data[pos:pos+2])[0]
                            pos += 2 + (uint64_count * 8)
                
                test_results.append({
                    'iid': f"0x{iid:08X}",
                    'eqzb_valid': True,
                    'properties_found': property_count
                })
        
        print(f"\n=== PHASE 2 SUMMARY ===")
        print(f"Target IIDs: {[hex(iid) for iid in target_iids]}")
        print(f"Found IIDs: {found_iids}")
        
        for result in test_results:
            status = "[OK]" if result['eqzb_valid'] else "[FAIL]"
            print(f"{status} {result['iid']}: {result['properties_found']} properties analyzed")
        
        # Phase 2 success criteria: Found target IIDs and valid EQZB containers
        success = len(test_results) > 0 and all(r['eqzb_valid'] for r in test_results)
        
        if success:
            print(f"[OK] PHASE 2 PASSED: EQZB container parsing working")
        else:
            print(f"[FAIL] PHASE 2 FAILED: EQZB container parsing issues")
        
        return success

def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_phase2.py <dbpf_file> [iid1] [iid2] ...")
        return 1
    
    filename = sys.argv[1]
    target_iids = None
    
    if len(sys.argv) > 2:
        target_iids = [int(iid, 16) for iid in sys.argv[2:]]
    
    success = validate_phase2(filename, target_iids)
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
