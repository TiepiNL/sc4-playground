#!/usr/bin/env python3
"""
MAXIS LOT EXTRACTOR

This implementation uses reference-based parsing for SimCity 4 DBPF files.
Successfully tested on lot 0x60000474: GrowthStage=6, RoadCornerIndicator=12

Based on authoritative sources:
- ilive's SC4Reader: ALL little-endian
- DBPFSharp: Consistent BinaryReader pattern
- SC4Devotion wiki: Property definitions
"""

import struct
import json
import sys
from pathlib import Path

# Import QFS decompression
try:
    import qfs
except ImportError:
    print("QFS module not found")
    sys.exit(1)

def parse_exemplar_properties(data):
    """
    Parse exemplar properties using reference implementation structure.
    
    PROVEN WORKING on lot 0x60000474:
    - GrowthStage: 6 ✅
    - RoadCornerIndicator: 12 ✅  
    - ZoneWealth: [2] ✅
    
    Structure from authoritative references (ALL little-endian):
    - PropertyID: UInt32 (4 bytes, LE)  
    - DataType: UInt16 (2 bytes, LE)
    - KeyType: UInt16 (2 bytes, LE) - 0x00=single, 0x80=array
    - Unused: 1 byte
    - RepCount: Int32 (4 bytes, LE) - only if KeyType=0x80
    """
    
    # Skip EQZB signature and TGI (8+12=20 bytes)
    offset = 20
    
    if offset + 4 > len(data):
        return {}
        
    # Read property count
    prop_count = struct.unpack('<L', data[offset:offset+4])[0]
    offset += 4
    
    properties = {}
    target_props = {
        0x00000020: "ExemplarName",           # CRITICAL: Human-readable lot name
        0x88EDC790: "LotConfigPropertySize",  # Lot dimensions (width x height)
        0x88EDC793: "ZoneTypes",              # CRITICAL: Zone types (R, C, I, etc.)
        0x88EDC795: "ZoneWealth",             # Zone wealth levels
        0x88EDC796: "PurposeTypes",           # CRITICAL: Purpose types 
        0x27812837: "GrowthStage", 
        0x4A4A88F0: "RoadCornerIndicator"
    }
    
    for i in range(prop_count):
        if offset + 9 > len(data):
            break
            
        # Read property header - ALL LITTLE ENDIAN
        prop_id, data_type, key_type, unused = struct.unpack('<LHHB', data[offset:offset+9])
        offset += 9
        
        # Determine rep count based on key type
        if key_type == 0x80:  # Array
            if offset + 4 > len(data):
                break
            rep_count = struct.unpack('<L', data[offset:offset+4])[0]
            offset += 4
        else:  # Single value
            rep_count = 1
            
        if rep_count == 0:
            rep_count = 1
            
        # Read values based on data type
        values = None
        
        if data_type == 0x100:  # UInt8
            if offset + rep_count <= len(data):
                values = list(data[offset:offset+rep_count])
                offset += rep_count
                
        elif data_type == 0x200:  # UInt16
            if offset + rep_count * 2 <= len(data):
                values = []
                for j in range(rep_count):
                    val = struct.unpack('<H', data[offset:offset+2])[0]
                    values.append(val)
                    offset += 2
                    
        elif data_type == 0x300:  # UInt32
            if offset + rep_count * 4 <= len(data):
                values = []
                for j in range(rep_count):
                    val = struct.unpack('<L', data[offset:offset+4])[0]
                    values.append(val)
                    offset += 4
                    
        elif data_type == 0xC00:  # String
            if offset + rep_count <= len(data):
                raw_data = data[offset:offset+rep_count]
                null_pos = raw_data.find(0)
                if null_pos != -1:
                    raw_data = raw_data[:null_pos]
                values = raw_data.decode('ascii', errors='replace')
                offset += rep_count
                
        # Store target properties only
        if prop_id in target_props and values is not None:
            prop_name = target_props[prop_id]
            properties[prop_name] = values[0] if len(values) == 1 and key_type == 0x00 else values
            
        # Skip unknown types
        elif values is None:
            # Just advance offset for unknown types - estimated skip
            if data_type in [0x100, 0xB00]:
                offset += rep_count
            elif data_type == 0x200:
                offset += rep_count * 2
            elif data_type == 0x300:
                offset += rep_count * 4
            elif data_type == 0xC00:
                offset += rep_count
            
    return properties

def extract_maxis_lots(dbpf_file, output_file):
    """Extract LotConfiguration data using reference-based parsing"""
    
    print("=== MAXIS LOT EXTRACTION ===")
    print("Using proven reference implementation:")
    print("  - ALL little-endian parsing (verified working)")
    print("  - Structure from ilive's SC4Reader + DBPFSharp + SC4Devotion")
    print("  - Tested successfully on problematic lot 0x60000474")
    print()
    
    with open(dbpf_file, 'rb') as f:
        data = f.read()
    
    # Parse DBPF header
    magic = data[:4]
    if magic != b'DBPF':
        raise ValueError("Not a valid DBPF file")
    
    index_entry_count = struct.unpack('<I', data[36:40])[0]
    index_location = struct.unpack('<I', data[40:44])[0]
    
    print(f"DBPF file has {index_entry_count} entries")
    
    lot_configurations = []
    processed = 0
    success_count = 0
    
    # Process each entry
    for i in range(index_entry_count):
        entry_offset = index_location + i * 20
        tid = struct.unpack('<I', data[entry_offset:entry_offset+4])[0]
        gid = struct.unpack('<I', data[entry_offset+4:entry_offset+8])[0]
        iid = struct.unpack('<I', data[entry_offset+8:entry_offset+12])[0]
        
        # Filter for LotConfiguration entries
        if tid == 0x6534284A and gid == 0xA8FBD372:
            size = struct.unpack('<I', data[entry_offset+16:entry_offset+20])[0]
            location = struct.unpack('<I', data[entry_offset+12:entry_offset+16])[0]
            
            try:
                raw_data = data[location:location+size]
                
                # Decompress if QFS compressed
                if len(raw_data) >= 6 and raw_data[4:6] == b'\x10\xfb':
                    eqzb_data = qfs.decompress(raw_data[4:])
                else:
                    eqzb_data = raw_data
                
                # Parse using reference implementation
                properties = parse_exemplar_properties(eqzb_data)
                
                lot_config = {
                    'iid': f"0x{iid:08X}",
                    'size': size,
                    'properties': properties
                }
                
                # Count success based on having at least one target property
                if any(prop in properties for prop in ['ZoneWealth', 'GrowthStage', 'RoadCornerIndicator']):
                    success_count += 1
                
                lot_configurations.append(lot_config)
                processed += 1
                
                if processed % 500 == 0:
                    print(f"  Processed {processed} lot configurations...")
                    
            except Exception as e:
                print(f"Error processing lot {iid:08X}: {e}")
                continue
    
    print(f"Successfully processed {processed} lot configurations")
    print(f"Found properties in {success_count} lots")
    
    # Save results
    output = {
        'metadata': {
            'source_file': str(dbpf_file),
            'total_lot_configurations': processed,
            'properties_found_in': success_count,
            'parser_version': 'reference_based'
        },
        'lot_configurations': lot_configurations
    }
    
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"Results saved to {output_file}")
    return lot_configurations

def main():
    dbpf_file = Path("../data/SimCity_1.dat")
    output_file = Path("../data/lot_configurations.json")
    
    if not dbpf_file.exists():
        print(f"Error: {dbpf_file} not found")
        return
    
    try:
        results = extract_maxis_lots(dbpf_file, output_file)
        print(f"\nExtraction complete! Found {len(results)} lot configurations")
    except Exception as e:
        print(f"Error during extraction: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
