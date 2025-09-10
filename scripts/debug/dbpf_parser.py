#!/usr/bin/env python3
"""
DBPF Parser for SimCity 4 Files

This script can parse DBPF (Database Packed File) format used by SimCity 4
to examine the structure of exemplar patch files and validate our generated patches.
"""

import struct
import sys
import os

class DBPFParser:
    def __init__(self, filepath):
        self.filepath = filepath
        self.file_handle = None
        self.header = {}
        self.index_entries = []
        
    def parse(self):
        """Parse the entire DBPF file and return structured data"""
        try:
            with open(self.filepath, 'rb') as f:
                self.file_handle = f
                self._parse_header()
                self._parse_index()
                entries_data = self._parse_entries()
                
            return {
                'header': self.header,
                'index_entries': self.index_entries,
                'entries': entries_data
            }
        except Exception as e:
            print(f"❌ Error parsing {self.filepath}: {e}")
            return None
    
    def _parse_header(self):
        """Parse the 96-byte DBPF header"""
        # Read magic number
        magic = self.file_handle.read(4)
        if magic != b'DBPF':
            raise ValueError(f"Invalid DBPF magic number: {magic}")
        
        # Read version
        major_ver, minor_ver = struct.unpack('<II', self.file_handle.read(8))
        
        # Skip reserved fields (12 bytes)
        self.file_handle.read(12)
        
        # Read timestamps
        created, modified = struct.unpack('<II', self.file_handle.read(8))
        
        # Read index information
        index_major, index_count, index_offset = struct.unpack('<III', self.file_handle.read(12))
        index_size = struct.unpack('<I', self.file_handle.read(4))[0]
        
        # Skip remaining header
        self.file_handle.read(44)  # Rest of header to get to 96 bytes
        
        self.header = {
            'magic': magic.decode('ascii'),
            'version': f"{major_ver}.{minor_ver}",
            'created': created,
            'modified': modified,
            'index_major': index_major,
            'index_count': index_count,
            'index_offset': index_offset,
            'index_size': index_size
        }
    
    def _parse_index(self):
        """Parse the file index table"""
        self.file_handle.seek(self.header['index_offset'])
        
        for i in range(self.header['index_count']):
            # Read TGI (Type, Group, Instance)
            type_id, group_id, instance_id = struct.unpack('<III', self.file_handle.read(12))
            # Read offset and size
            offset, size = struct.unpack('<II', self.file_handle.read(8))
            
            self.index_entries.append({
                'type_id': type_id,
                'group_id': group_id,
                'instance_id': instance_id,
                'offset': offset,
                'size': size
            })
    
    def _parse_entries(self):
        """Parse the actual file entries"""
        entries = []
        
        for entry in self.index_entries:
            self.file_handle.seek(entry['offset'])
            raw_data = self.file_handle.read(entry['size'])
            
            # Try to parse as exemplar if it's a Cohort type
            if entry['type_id'] == 0x05342861:  # Cohort exemplar type
                parsed_data = self._parse_exemplar(raw_data)
            else:
                parsed_data = {'raw_data': raw_data, 'size': len(raw_data)}
            
            entries.append({
                'entry_info': entry,
                'data': parsed_data
            })
        
        return entries
    
    def _parse_exemplar(self, data):
        """Parse exemplar data to extract properties"""
        properties = {}
        offset = 0
        
        try:
            # Check if this looks like a Cohort exemplar (has CQZB header)
            if len(data) >= 20 and data[0:4] == b'CQZB':
                properties['format'] = 'CQZB_Cohort'
                properties['header'] = data[0:20].hex()
                
                # Skip the CQZB header and parse as exemplar
                offset = 20
                
            # Read property count
            if len(data) < offset + 4:
                return {'error': 'Data too short for property count', 'raw_size': len(data)}
            
            prop_count = struct.unpack('<I', data[offset:offset+4])[0]
            offset += 4
            
            properties['property_count'] = prop_count
            properties['parsed_properties'] = []
            
            for i in range(prop_count):
                if offset + 4 > len(data):
                    properties['parse_error'] = f'Insufficient data for property {i} ID'
                    break
                
                # Read property ID
                prop_id = struct.unpack('<I', data[offset:offset+4])[0]
                offset += 4
                
                if offset + 4 > len(data):
                    properties['parse_error'] = f'Insufficient data for property {i} type info'
                    break
                
                # Read property type info (4 bytes: type, flags, etc.)
                type_info = data[offset:offset+4]
                offset += 4
                
                # Check for padding byte (observed in working exemplars)
                if offset < len(data) and data[offset] == 0x00:
                    offset += 1  # Skip padding byte
                
                # Try to parse property value based on common patterns
                prop_data, bytes_consumed = self._parse_property_value(data[offset:], type_info)
                offset += bytes_consumed
                
                properties['parsed_properties'].append({
                    'id': f"0x{prop_id:08X}",
                    'id_decimal': prop_id,
                    'type_info': [hex(b) for b in type_info],
                    'data': prop_data
                })
            
            properties['total_bytes_parsed'] = offset
            properties['remaining_bytes'] = len(data) - offset
            
        except Exception as e:
            properties['parse_error'] = str(e)
            properties['raw_size'] = len(data)
        
        return properties
    
    def _parse_property_value(self, data, type_info):
        """Parse property value based on type information"""
        if len(data) < 4:
            return {'error': 'insufficient data'}, 0
        
        # Read array length
        array_length = struct.unpack('<I', data[:4])[0]
        offset = 4
        
        # Determine value size based on type_info[1] (common patterns)
        type_byte = type_info[1] if len(type_info) > 1 else 0
        
        if type_byte == 0x0B:  # Float array
            value_size = 4
            values = []
            for i in range(array_length):
                if offset + value_size <= len(data):
                    val = struct.unpack('<f', data[offset:offset+value_size])[0]
                    values.append(val)
                    offset += value_size
                else:
                    break
            return {'type': 'float_array', 'length': array_length, 'values': values}, offset
        
        elif type_byte == 0x09:  # Uint32 array (MinSlope when misidentified)
            # Check if this might actually be a float by trying both interpretations
            if array_length == 1 and offset + 4 <= len(data):
                # Try as float first
                float_val = struct.unpack('<f', data[offset:offset+4])[0]
                uint_val = struct.unpack('<I', data[offset:offset+4])[0]
                
                # If float value makes sense for MinSlope (0-90 degrees), use float
                if 0 <= float_val <= 90:
                    return {'type': 'float_value', 'length': array_length, 'values': [float_val]}, offset + 4
                else:
                    return {'type': 'uint32_array', 'length': array_length, 'values': [f"0x{uint_val:08X}"]}, offset + 4
            else:
                # Multiple values - treat as uint32 array
                value_size = 4
                values = []
                for i in range(array_length):
                    if offset + value_size <= len(data):
                        val = struct.unpack('<I', data[offset:offset+value_size])[0]
                        values.append(f"0x{val:08X}")
                        offset += value_size
                    else:
                        break
                
                # If this is ExemplarPatchTargets, format as Group/Instance pairs
                if len(values) > 10:  # Large array, probably ExemplarPatchTargets
                    pairs = []
                    for i in range(0, min(10, len(values)), 2):  # Show first 5 pairs
                        if i + 1 < len(values):
                            pairs.append(f"Group={values[i]}, Instance={values[i+1]}")
                    return {'type': 'uint32_array_pairs', 'length': array_length, 'sample_pairs': pairs, 'total_targets': len(values)//2}, offset
                else:
                    return {'type': 'uint32_array', 'length': array_length, 'values': values}, offset
        
        elif type_byte == 0x03:  # Uint32 array (from working example)
            value_size = 4
            values = []
            for i in range(array_length):
                if offset + value_size <= len(data):
                    val = struct.unpack('<I', data[offset:offset+value_size])[0]
                    values.append(f"0x{val:08X}")
                    offset += value_size
                else:
                    break
            
            # If this is ExemplarPatchTargets, format as Group/Instance pairs
            if len(values) >= 2:  # Pairs
                pairs = []
                for i in range(0, min(10, len(values)), 2):  # Show first 5 pairs
                    if i + 1 < len(values):
                        pairs.append(f"Group={values[i]}, Instance={values[i+1]}")
                if len(values) > 10:
                    return {'type': 'uint32_array_pairs', 'length': array_length, 'sample_pairs': pairs, 'total_targets': len(values)//2}, offset
                else:
                    return {'type': 'uint32_array_pairs', 'length': array_length, 'pairs': pairs}, offset
            else:
                return {'type': 'uint32_array', 'length': array_length, 'values': values}, offset
        
        else:
            # Unknown type, just return raw bytes
            remaining_data = data[offset:offset + min(array_length * 4, len(data) - offset)]
            return {'type': 'unknown', 'length': array_length, 'raw_bytes': list(remaining_data)}, len(remaining_data) + 4

def format_entry_info(entry):
    """Format entry information for display"""
    info = entry['entry_info']
    type_name = {
        0x05342861: "Cohort",
        0x6534284a: "Exemplar",
        0x6a0f82b2: "Lot",
        0xa8fbd372: "LotConfiguration"
    }.get(info['type_id'], f"0x{info['type_id']:08X}")
    
    return f"Type: {type_name}, Group: 0x{info['group_id']:08X}, Instance: 0x{info['instance_id']:08X}"

def analyze_file(filepath):
    """Analyze a DBPF file and print detailed information"""
    print(f"\n🔍 Analyzing: {os.path.basename(filepath)}")
    print("=" * 60)
    
    parser = DBPFParser(filepath)
    result = parser.parse()
    
    if not result:
        return
    
    # Print header info
    header = result['header']
    print(f"📋 Header:")
    print(f"   Magic: {header['magic']}")
    print(f"   Version: {header['version']}")
    print(f"   Index Count: {header['index_count']}")
    print(f"   Index Offset: {header['index_offset']}")
    print(f"   Index Size: {header['index_size']}")
    
    # Print entries
    print(f"\n📁 Entries ({len(result['entries'])}):")
    for i, entry in enumerate(result['entries']):
        print(f"\n   Entry {i+1}: {format_entry_info(entry)}")
        
        data = entry['data']
        if 'property_count' in data:
            print(f"      Properties: {data['property_count']}")
            
            if 'parsed_properties' in data:
                for prop in data['parsed_properties']:
                    prop_name = get_property_name(prop['id_decimal'])
                    print(f"         • {prop['id']} ({prop_name})")
                    
                    if 'values' in prop['data']:
                        values = prop['data']['values']
                        if len(values) <= 10:
                            print(f"           Values: {values}")
                        else:
                            print(f"           Values: {values[:5]}... ({len(values)} total)")
                    elif 'raw_bytes' in prop['data']:
                        bytes_data = prop['data']['raw_bytes']
                        if len(bytes_data) <= 20:
                            print(f"           Raw: {[hex(b) for b in bytes_data]}")
                        else:
                            print(f"           Raw: {len(bytes_data)} bytes")
        
        if 'parse_error' in data:
            print(f"      ⚠️  Parse Error: {data['parse_error']}")
        
        if 'raw_size' in data:
            print(f"      Raw Size: {data['raw_size']} bytes")

def get_property_name(prop_id):
    """Get human-readable property name"""
    names = {
        0x699b08a4: "MinSlope",
        0x0062e78a: "ExemplarPatchTargets",
        0x6a0f82b2: "ExemplarName",
        0x88edc790: "ZoneTypes",
        0x88edc793: "ZonePurpose", 
        0x88edc794: "ZoneWealth"
    }
    return names.get(prop_id, "Unknown")

def main():
    if len(sys.argv) < 2:
        print("Usage: python dbpf_parser.py <file1.dat> [file2.dat] ...")
        print("\nAnalyze DBPF files and display their structure")
        return
    
    for filepath in sys.argv[1:]:
        if not os.path.exists(filepath):
            print(f"❌ File not found: {filepath}")
            continue
        
        analyze_file(filepath)

if __name__ == "__main__":
    main()
