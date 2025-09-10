#!/usr/bin/env python3
"""
SimCity 4 Datpack Script - Simple ASCII Version

Combines multiple .dat patch files into a single DBPF file without Unicode characters.
"""

import os
import sys
import struct
import argparse
import time
from collections import defaultdict
from pathlib import Path

# Import our existing QFS module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import qfs

def read_dbpf_header(file_path):
    """Read and parse DBPF header from a .dat file."""
    with open(file_path, 'rb') as f:
        header = f.read(96)
        if header[:4] != b'DBPF':
            raise ValueError(f"Not a valid DBPF file: {file_path}")
        
        index_entry_count = struct.unpack('<I', header[36:40])[0]
        index_offset = struct.unpack('<I', header[40:44])[0]
        
        return {
            'index_entry_count': index_entry_count,
            'index_offset': index_offset
        }

def read_dbpf_index(file_path, header):
    """Read the DBPF index table and return list of entries."""
    entries = []
    
    with open(file_path, 'rb') as f:
        f.seek(header['index_offset'])
        
        for i in range(header['index_entry_count']):
            entry_data = f.read(20)
            if len(entry_data) != 20:
                raise ValueError(f"Incomplete index entry in {file_path}")
            
            type_id = struct.unpack('<I', entry_data[0:4])[0]
            group_id = struct.unpack('<I', entry_data[4:8])[0]
            instance_id = struct.unpack('<I', entry_data[8:12])[0]
            file_offset = struct.unpack('<I', entry_data[12:16])[0]
            file_size = struct.unpack('<I', entry_data[16:20])[0]
            
            entries.append({
                'tgi': (type_id, group_id, instance_id),
                'type_id': type_id,
                'group_id': group_id,
                'instance_id': instance_id,
                'file_offset': file_offset,
                'file_size': file_size
            })
    
    return entries

def read_entry_data(file_path, entry):
    """Read the raw data for a specific DBPF entry."""
    with open(file_path, 'rb') as f:
        f.seek(entry['file_offset'])
        return f.read(entry['file_size'])

def write_datpacked_dbpf(output_path, combined_entries):
    """Write combined entries to a new DBPF file."""
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    
    with open(output_path, 'wb') as f:
        # Write DBPF header
        f.write(b'DBPF')
        f.write(struct.pack('<II', 1, 0))  # Version
        f.write(b'\x00' * 12)  # Reserved
        
        timestamp = int(time.time())
        f.write(struct.pack('<II', timestamp, timestamp))
        
        index_major = 7
        index_count = len(combined_entries)
        index_offset_pos = f.tell()
        f.write(struct.pack('<III', index_major, index_count, 0))
        index_size_pos = f.tell()
        f.write(struct.pack('<I', 0))
        
        f.write(b'\x00' * 32)
        f.write(struct.pack('<I', 0))
        f.write(b'\x00' * 12)
        
        # Write entry data
        entry_positions = {}
        for tgi, (entry, data) in combined_entries.items():
            entry_start = f.tell()
            f.write(data)
            entry_positions[tgi] = {
                'offset': entry_start,
                'size': len(data),
                'type_id': entry['type_id'],
                'group_id': entry['group_id'],
                'instance_id': entry['instance_id']
            }
        
        # Write index table
        index_start = f.tell()
        for tgi, pos_info in entry_positions.items():
            f.write(struct.pack('<III', pos_info['type_id'], pos_info['group_id'], pos_info['instance_id']))
            f.write(struct.pack('<II', pos_info['offset'], pos_info['size']))
        
        index_end = f.tell()
        index_size = index_end - index_start
        
        # Update header
        f.seek(index_offset_pos)
        f.write(struct.pack('<III', index_major, index_count, index_start))
        f.seek(index_size_pos)
        f.write(struct.pack('<I', index_size))
    
    return output_path

def datpack_directory(input_dir, output_file, remove_source=False):
    """Datpack all .dat files in a directory into a single DBPF file."""
    input_path = Path(input_dir)
    if not input_path.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")
    
    dat_files = list(input_path.glob("*.dat"))
    if not dat_files:
        raise ValueError(f"No .dat files found in directory: {input_dir}")
    
    print(f"SimCity 4 Datpack Utility")
    print(f"============================")
    print(f"Input directory: {input_dir}")
    print(f"Output file: {output_file}")
    print(f"Found {len(dat_files)} .dat files to combine")
    
    combined_entries = {}
    duplicates_found = 0
    total_entries = 0
    
    for i, dat_file in enumerate(sorted(dat_files)):
        print(f"   Processing {dat_file.name} ({i+1}/{len(dat_files)})")
        
        try:
            header = read_dbpf_header(dat_file)
            entries = read_dbpf_index(dat_file, header)
            
            print(f"      Found {len(entries)} entries")
            
            for entry in entries:
                tgi = entry['tgi']
                total_entries += 1
                
                if tgi in combined_entries:
                    duplicates_found += 1
                    print(f"      WARNING: Duplicate TGI found (overriding)")
                
                entry_data = read_entry_data(dat_file, entry)
                combined_entries[tgi] = (entry, entry_data)
                
        except Exception as e:
            print(f"      ERROR: Error processing {dat_file.name}: {e}")
            continue
    
    print(f"")
    print(f"Datpack Statistics:")
    print(f"   Total entries processed: {total_entries}")
    print(f"   Duplicate entries found: {duplicates_found}")
    print(f"   Unique entries to combine: {len(combined_entries)}")
    
    if not combined_entries:
        raise ValueError("No valid entries found to datpack")
    
    total_size = sum(len(data) for _, data in combined_entries.values())
    print(f"   Combined data size: {total_size:,} bytes ({total_size / (1024*1024):.1f} MB)")
    
    print(f"")
    print(f"Creating datpacked file: {output_file}")
    output_path = write_datpacked_dbpf(output_file, combined_entries)
    
    output_size = os.path.getsize(output_path)
    print(f"OK Successfully created datpacked file")
    print(f"   Output file size: {output_size:,} bytes ({output_size / (1024*1024):.1f} MB)")
    
    if remove_source:
        print(f"")
        print(f"Removing source .dat files...")
        removed_count = 0
        for dat_file in dat_files:
            try:
                dat_file.unlink()
                removed_count += 1
                print(f"   OK Removed {dat_file.name}")
            except Exception as e:
                print(f"   ERROR Could not remove {dat_file.name}: {e}")
        
        print(f"Removed {removed_count}/{len(dat_files)} source files")
    
    print(f"")
    print(f"Datpack complete!")
    print(f"Install: Copy {output_file} to your SimCity 4 Plugins folder")
    print(f"Effect: Combined functionality of all {len(dat_files)} original patch files")
    
    return output_path

def main():
    """Main function with argument parsing."""
    parser = argparse.ArgumentParser(description='Combine multiple SimCity 4 .dat files into a single datpacked DBPF file')
    
    parser.add_argument('-i', '--input', default='output_patches', help='Input directory containing .dat files to combine')
    parser.add_argument('-o', '--output', default='datpacked_maxis_blockers.dat', help='Output datpacked file name')
    parser.add_argument('--remove-source', action='store_true', help='Remove source .dat files after successful datpacking')
    parser.add_argument('--max-size', type=int, default=500, help='Maximum file size in MB before warning')
    
    args = parser.parse_args()
    
    # If output is just a filename (no path), put it in the input directory
    output_path = args.output
    if not os.path.dirname(output_path):
        output_path = os.path.join(args.input, output_path)
    
    try:
        datpack_directory(args.input, output_path, args.remove_source)
        
    except Exception as e:
        print(f"")
        print(f"ERROR Datpack failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
