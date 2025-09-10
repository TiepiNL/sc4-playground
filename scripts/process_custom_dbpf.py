#!/usr/bin/env python3
"""
Custom DBPF Processor for SimCity 4 RCI Blockers

This script processes custom building packs (multiple DBPF files) to extract
LotConfiguration exemplars and generate RCI blocker patches, similar to the
Maxis lot processing but for user-provided custom content.

Process:
1. Extract custom.zip to data/custom/
2. Recursively find all DBPF files regardless of extension
3. Extract LotConfiguration exemplars from each DBPF
4. Generate blocker patches by zone/wealth combination
5. Datpack into single file for easy installation
"""

import os
import sys
import zipfile
import json
import struct
from pathlib import Path
from collections import defaultdict

# Add the scripts directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import qfs
from extract_maxis_lots import parse_lot_configuration_corrected

# Constants
CUSTOM_ZIP_PATH = "data/custom.zip"
CUSTOM_EXTRACT_DIR = "data/custom"
CUSTOM_OUTPUT_JSON = "data/custom_lot_configurations.json"
LOT_CONFIG_TYPE_ID = 0x6534284A  # LotConfiguration exemplar type
LOT_CONFIG_GROUP_ID = 0xA8FBD372  # LotConfiguration group ID

def extract_custom_zip():
    """Extract custom.zip to data/custom/ directory."""
    print(f"Custom DBPF Processor")
    print(f"====================")
    
    if not os.path.exists(CUSTOM_ZIP_PATH):
        raise FileNotFoundError(f"Custom zip file not found: {CUSTOM_ZIP_PATH}")
    
    # Clean and create extraction directory
    if os.path.exists(CUSTOM_EXTRACT_DIR):
        import shutil
        shutil.rmtree(CUSTOM_EXTRACT_DIR)
    
    os.makedirs(CUSTOM_EXTRACT_DIR, exist_ok=True)
    
    print(f"Extracting {CUSTOM_ZIP_PATH} to {CUSTOM_EXTRACT_DIR}/")
    
    with zipfile.ZipFile(CUSTOM_ZIP_PATH, 'r') as zip_ref:
        zip_ref.extractall(CUSTOM_EXTRACT_DIR)
    
    print(f"Extraction complete.")
    return CUSTOM_EXTRACT_DIR

def find_dbpf_files(directory):
    """Recursively find all DBPF files regardless of extension."""
    dbpf_files = []
    
    print(f"Scanning for DBPF files in {directory}/")
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            
            # Check if file has DBPF magic header
            try:
                with open(file_path, 'rb') as f:
                    magic = f.read(4)
                    if magic == b'DBPF':
                        relative_path = os.path.relpath(file_path, directory)
                        dbpf_files.append({
                            'path': file_path,
                            'relative_path': relative_path,
                            'filename': file
                        })
                        print(f"   Found DBPF: {relative_path}")
            except (IOError, OSError):
                # Skip files that can't be read
                continue
    
    print(f"Found {len(dbpf_files)} DBPF files")
    return dbpf_files

def extract_lot_configurations_from_dbpf(file_path):
    """Extract LotConfiguration exemplars from a single DBPF file using the same logic as extract_maxis_lots.py."""
    lot_configurations = []
    
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
        
        # Parse DBPF header
        magic = data[:4]
        if magic != b'DBPF':
            return lot_configurations  # Not a valid DBPF file
        
        index_entry_count = struct.unpack('<I', data[36:40])[0]
        index_location = struct.unpack('<I', data[40:44])[0]
        
        if index_entry_count == 0:
            return lot_configurations
        
        lot_config_count = 0
        
        # Process each entry looking for LotConfigurations
        for i in range(index_entry_count):
            entry_offset = index_location + i * 20
            tid = struct.unpack('<I', data[entry_offset:entry_offset+4])[0]
            gid = struct.unpack('<I', data[entry_offset+4:entry_offset+8])[0]
            iid = struct.unpack('<I', data[entry_offset+8:entry_offset+12])[0]
            
            # Filter for LotConfiguration entries
            if tid == LOT_CONFIG_TYPE_ID and gid == LOT_CONFIG_GROUP_ID:
                size = struct.unpack('<I', data[entry_offset+16:entry_offset+20])[0]
                location = struct.unpack('<I', data[entry_offset+12:entry_offset+16])[0]
                
                try:
                    raw_data = data[location:location+size]
                    
                    # Decompress if QFS compressed
                    if len(raw_data) >= 6 and raw_data[4:6] == b'\x10\xfb':
                        eqzb_data = qfs.decompress(raw_data[4:])
                    else:
                        eqzb_data = raw_data
                    
                    # Parse using corrected structure from extract_maxis_lots.py
                    properties = parse_lot_configuration_corrected(eqzb_data)
                    
                    lot_config = {
                        'source_file': os.path.basename(file_path),
                        'iid': f"0x{iid:08X}",
                        'size': size,
                        'properties': properties
                    }
                    
                    lot_configurations.append(lot_config)
                    lot_config_count += 1
                    
                except Exception as e:
                    print(f"         Warning: Error processing IID 0x{iid:08X}: {e}")
                    continue
        
        if lot_config_count > 0:
            print(f"      Found {lot_config_count} LotConfiguration exemplars")
    
    except Exception as e:
        print(f"      Error processing DBPF {os.path.basename(file_path)}: {e}")
    
    return lot_configurations

def process_custom_dbpf_files():
    """Main processing function to extract LotConfigurations from all custom DBPF files."""
    
    # Step 1: Extract the zip file
    extract_dir = extract_custom_zip()
    
    # Step 2: Find all DBPF files
    dbpf_files = find_dbpf_files(extract_dir)
    
    if not dbpf_files:
        print("No DBPF files found in custom package.")
        return None
    
    # Step 3: Extract LotConfigurations from each DBPF
    all_lot_configurations = []
    
    print(f"\nExtracting LotConfiguration exemplars:")
    for dbpf_file in dbpf_files:
        print(f"   Processing: {dbpf_file['relative_path']}")
        lot_configs = extract_lot_configurations_from_dbpf(dbpf_file['path'])
        all_lot_configurations.extend(lot_configs)
    
    print(f"\nExtraction Summary:")
    print(f"   Total DBPF files processed: {len(dbpf_files)}")
    print(f"   Total LotConfigurations found: {len(all_lot_configurations)}")
    
    # Step 4: Save to JSON file
    output_data = {
        'source': 'custom_dbpf_files',
        'total_files_processed': len(dbpf_files),
        'dbpf_files': [f['relative_path'] for f in dbpf_files],
        'lot_configurations': all_lot_configurations
    }
    
    with open(CUSTOM_OUTPUT_JSON, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"   Output saved to: {CUSTOM_OUTPUT_JSON}")
    
    return output_data

def main():
    """Main function."""
    try:
        result = process_custom_dbpf_files()
        if result:
            print(f"\nCustom DBPF processing complete!")
            print(f"Found {len(result['lot_configurations'])} LotConfiguration exemplars")
            print(f"Ready for RCI blocker patch generation.")
        else:
            print("No LotConfiguration exemplars found.")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
