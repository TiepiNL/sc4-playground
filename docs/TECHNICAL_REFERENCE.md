# SimCity 4 DBPF Technical Reference

## Complete Guide to DBPF Parsing, Property Extraction, and Patch Generation

This document provides the definitive technical reference for working with SimCity 4 DBPF (Database Packed File) format. It captures all data structures, parsing algorithms, and file generation techniques discovered through extensive reverse engineering and validation.

**Target Audience:** Future developers (human or AI) who need to recreate or extend this codebase with minimal experimentation.

**Validation Status:** All structures documented here are implemented in production code and validated through comprehensive integration tests.

---

## Table of Contents

1. [DBPF File Structure](#dbpf-file-structure)
2. [Property Extraction Pipeline](#property-extraction-pipeline)  
3. [Critical Parsing Insights](#critical-parsing-insights)
4. [Patch File Generation](#patch-file-generation)
5. [Datpacking System](#datpacking-system)
6. [Implementation Guide](#implementation-guide)
7. [Validation Framework](#validation-framework)

---

## DBPF File Structure

### Overview

DBPF (Database Packed File) is the proprietary archive format used by SimCity 4 to store game assets. This format was developed by Maxis/EA and consists of:

- **96-byte header** with metadata
- **Variable-length data section** containing compressed and/or uncompressed files
- **Index table** with file locations and identifiers

**Reference:** For additional DBPF format documentation, see the [SC4Devotion DBPF Wiki](https://www.wiki.sc4devotion.com/index.php?title=DBPF).

### DBPF Header (96 bytes)

```md
Offset | Size | Field              | Endianness | Description
-------|------|--------------------|------------|------------------
0      | 4    | Magic              | ASCII      | Always "DBPF"
4      | 4    | MajorVersion       | LE         | Format version (usually 1)
8      | 4    | MinorVersion       | LE         | Format sub-version (usually 0)
12     | 12   | Reserved1          | -          | Always zero
24     | 4    | DateCreated        | LE         | Unix timestamp
28     | 4    | DateModified       | LE         | Unix timestamp  
32     | 4    | IndexMajorVersion  | LE         | Index format version (usually 7)
36     | 4    | IndexEntryCount    | LE         | Number of files in archive
40     | 4    | IndexOffset        | LE         | Byte offset to index table
44     | 4    | IndexSize          | LE         | Size of index table in bytes
48     | 32   | Reserved2          | -          | Always zero
80     | 4    | Reserved3          | LE         | Always zero
84     | 12   | Reserved4          | -          | Always zero
```

**Critical Fields for Parsing:**

- **IndexEntryCount** (offset 36): Number of files to process
- **IndexOffset** (offset 40): Location of index table

### Index Table Structure

Each index entry is exactly **20 bytes**:

```md
Offset | Size | Field        | Endianness | Description
-------|------|--------------|------------|------------------
0      | 4    | TypeID       | LE         | File type identifier
4      | 4    | GroupID      | LE         | File group identifier
8      | 4    | InstanceID   | LE         | Unique instance identifier
12     | 4    | FileOffset   | LE         | Byte offset in archive
16     | 4    | FileSize     | LE         | Size of file data
```

### LotConfiguration Identification

**Target Criteria for filtering:**

- `TypeID = 0x6534284A` (Exemplar type)
- `GroupID = 0xA8FBD372` (LotConfiguration group)

**Production Statistics:**

- SimCity_1.dat contains **60,440+ total entries**  
- Yields **1,908 LotConfiguration entries** (3.2% of total)

---

## Property Extraction Pipeline

### 4-Layer Parsing Architecture

```md
Layer 1: DBPF File Access     → Locate and read exemplar files
Layer 2: QFS Decompression    → Extract EQZB container data
Layer 3: Property Structure   → Parse individual property headers
Layer 4: Data Interpretation  → Convert to meaningful values
```

### Layer 1: File Access

```python
# Read DBPF header
with open('SimCity_1.dat', 'rb') as f:
    data = f.read()
    index_count = struct.unpack('<I', data[36:40])[0]
    index_offset = struct.unpack('<I', data[40:44])[0]

# Process index entries
for i in range(index_count):
    entry_offset = index_offset + i * 20
    tid, gid, iid, offset, size = struct.unpack('<IIIII', data[entry_offset:entry_offset+20])
    
    # Filter for LotConfigurations
    if tid == 0x6534284A and gid == 0xA8FBD372:
        # Extract file data...
```

### Layer 2: QFS Decompression

**QFS Compression Detection:**

```python
raw_data = data[location:location+size]

# Check for QFS compression signature
if len(raw_data) >= 6 and raw_data[4:6] == b'\x10\xfb':
    # Data is compressed - decompress starting at offset 4
    eqzb_data = qfs.decompress(raw_data[4:])
else:
    # Data is not compressed
    eqzb_data = raw_data
```

**Reference:** For detailed QFS compression algorithm documentation, see [SC4Devotion DBPF Compression Wiki](https://www.wiki.sc4devotion.com/index.php?title=DBPF_Compression).

**EQZB Container Structure:**

```md
Offset | Size | Description
-------|------|------------------
0      | 4    | Magic "EQZB"
4      | 4    | Version "1###"  
8      | 12   | TGI (Type/Group/Instance)
20     | 4    | Property count
24+    | Var  | Property data
```

**Critical Insight:** Property data starts at **offset 20** (not 32 as in some documentation).

### Layer 3: Property Structure

**Standard Property Header (13 bytes):**

```md
Offset | Size | Field       | Endianness | Description
-------|------|-------------|------------|------------------
0      | 4    | PropertyID  | LE         | Property identifier
4      | 2    | DataType    | LE         | Data type code
6      | 2    | W8          | LE         | First word (usually 0x8000)
8      | 2    | Rep         | **BE**     | Repetition count (BIG-ENDIAN!)
10     | 3    | Padding     | -          | Always 0x000000
13+    | Var  | Data        | LE         | Property value(s)
```

**🚨 CRITICAL:** The Rep field at offset 8 is **BIG-ENDIAN** while everything else is little-endian!

### Layer 4: Target Properties

**LotConfiguration Properties (7 targeted for extraction):**

*Note: LotConfiguration exemplars may contain additional properties beyond these 7, but our extraction focuses on these core properties for lot analysis and patch generation.*

**Reference:** For comprehensive documentation of all exemplar properties, see [SC4Devotion Exemplar Properties Wiki](https://www.wiki.sc4devotion.com/index.php?title=Exemplar_properties).

| Property | ID | Type | Description | Data Type |
|----------|----|----|-------------|-----------|
| ExemplarName | 0x00000020 | String | Lot identifier | UTF-8 string |
| LotConfigPropertySize | 0x88EDC790 | Array | Lot dimensions | UINT8 array [width, height] |
| ZoneTypes | 0x88EDC793 | Array | Zone compatibility | UINT8 array (1-9=zones, 15=all) |
| ZoneWealth | 0x88EDC795 | Array | Wealth levels | UINT8 array (1=§, 2=§§, 3=§§§) |
| PurposeTypes | 0x88EDC796 | Array | Purpose codes | UINT32 array |
| GrowthStage | 0x27812837 | **Special** | Development stage | UINT8 (rep-encoded) |
| RoadCornerIndicator | 0x4A4A88F0 | **Special** | Corner placement | UINT8 (rep-encoded) |

### Property Parsing Algorithm

```python
def parse_exemplar_properties(data):
    """Parse exemplar properties using reference implementation."""
    offset = 20  # Skip EQZB header
    
    if offset + 4 > len(data):
        return {}
        
    # Read property count
    prop_count = struct.unpack('<L', data[offset:offset+4])[0]
    offset += 4
    
    properties = {}
    
    for _ in range(prop_count):
        if offset + 13 > len(data):
            break
            
        # Parse 13-byte property header
        property_id = struct.unpack('<I', data[offset:offset+4])[0]
        data_type = struct.unpack('<H', data[offset+4:offset+6])[0]
        w8 = struct.unpack('<H', data[offset+6:offset+8])[0]
        rep = struct.unpack('>H', data[offset+8:offset+10])[0]  # BIG-ENDIAN!
        padding = data[offset+10:offset+13]
        
        # Validate padding is zero
        if padding != b'\x00\x00\x00':
            continue
            
        offset += 13
        
        # Handle special rep-encoded properties
        if property_id in {0x27812837, 0x4A4A88F0} and data_type == 0x0100:
            # Value stored in rep field itself
            properties[get_property_name(property_id)] = rep
            continue
            
        # Parse regular properties based on data type
        if data_type == 0x0C00:  # String
            value = parse_string_property(data, offset, rep)
        elif data_type == 0x0100:  # UINT8 array
            value = parse_uint8_array(data, offset, rep)
        elif data_type == 0x0700:  # UINT32 array
            value = parse_uint32_array(data, offset, rep)
        else:
            continue
            
        properties[get_property_name(property_id)] = value
        offset += calculate_property_size(data_type, rep)
    
    return properties
```

---

## Critical Parsing Insights

### 1. BIG-ENDIAN Rep Field Discovery

**The Most Critical Finding:** The Rep field is BIG-ENDIAN while everything else is little-endian.

```python
# WRONG - causes complete parsing failure
rep = struct.unpack('<H', data[offset+8:offset+10])[0]  # Little-endian

# CORRECT - enables successful parsing
rep = struct.unpack('>H', data[offset+8:offset+10])[0]  # Big-endian
```

**Impact:** This single endianness difference prevented all array properties from parsing correctly.

### 2. Special Rep-Field Encoding

**Problem:** GrowthStage and RoadCornerIndicator properties appeared as null despite being present in the data.

**Discovery:** These properties use special encoding where the actual value is stored in the Rep field itself, not in the data section.

```python
# Special case handling
special_rep_properties = {0x27812837, 0x4A4A88F0}

if property_id in special_rep_properties and data_type == 0x0100:
    # Value is in the rep field itself
    return rep  # Direct return, no data section parsing
```

**Results:**

- Before fix: 0% extraction rate for these properties
- After fix: 79.8% GrowthStage, 93.9% RoadCornerIndicator extraction

### 3. Property ID Verification

**Critical Correction:** ExemplarName property ID is `0x00000020`, NOT `0x88EDC790`.

**Evidence Sources:**

- SC4Reader source code: `pPropName = pEx->FindProp(0x20);`
- Binary data validation: EQZB files show `0x00000020:{"Exemplar Name"}`
- Correction: `0x88EDC790` is actually "LotConfigPropertySize"

### 4. Case Sensitivity Bug

**Root Cause:** Validation logic used lowercase hex while parser generated uppercase.

```python
# WRONG - caused validation failures
if prop_type == '0x0c00':  # lowercase

# CORRECT - matches parser output
if prop_type == '0x0C00':  # uppercase
```

### 5. False Positive Prevention

Property ID bytes appear multiple times in binary data. Robust validation required:

```python
def validate_property_structure(property_id, data_type, rep, padding):
    # Check valid property type
    if data_type not in {0x0C00, 0x0100, 0x0700}:
        return False
    
    # Check reasonable rep count
    if rep > 100:
        return False
        
    # Verify padding is zero
    if padding != b'\x00\x00\x00':
        return False
        
    return True
```

---

## Patch File Generation

### Overview

Exemplar patches allow selective override of specific properties in existing exemplars without copying the entire exemplar file. This is a general SimCity 4 mechanism that enables targeted modifications while preserving the original exemplar data.

**Our Use Case:** We leverage this patch system to create "blocker files" that prevent RCI (Residential, Commercial, Industrial) lots from growing by setting MinSlope to 89.0 degrees, making them unbuildable while preserving all other lot properties and custom content compatibility.

**Reference:** For detailed information about exemplar patching mechanics, see [SC4 Resource Loading Hooks - Exemplar Patching](https://github.com/0xC0000054/sc4-resource-loading-hooks?tab=readme-ov-file#exemplar-patching).

### Cohort Exemplar Structure

**CQZB Header (20 bytes):**

```md
Offset | Data | Description
-------|------|------------------
0      | "CQZB1###" | Magic signature + version
8      | 12 zero bytes | Reserved
```

**Property Structure:**

```md
Property 1 - ExemplarPatchTargets (0x0062E78A):
├── Type Info: 00 03 80 00 (UINT32 array)
├── Padding: 00 (required!)
├── Array Length: number_of_targets × 2
└── Data: [GroupID, InstanceID] pairs

Property 2 - MinSlope (0x699B08A4):
├── Type Info: 00 09 80 00 (Float32 array)  
├── Padding: 00 (required!)
├── Array Length: 1
└── Data: 89.0 (IEEE 754 float32)
```

### Implementation Details

```python
def create_cohort_exemplar(target_instances, instance_id):
    """Create a cohort exemplar for patching lots.
    
    Args:
        target_instances: List of Instance IDs to be patched by this cohort
        instance_id: Unique ID for the cohort exemplar itself
    """
    cohort_data = bytearray()
    
    # CQZB header
    cohort_data.extend(b'CQZB1###')
    cohort_data.extend(b'\x00' * 12)
    
    # Property count (always 2)
    cohort_data.extend(struct.pack('<I', 2))
    
    # Property 1: ExemplarPatchTargets
    cohort_data.extend(struct.pack('<I', 0x0062E78A))  # Property ID
    cohort_data.extend(struct.pack('<BBBB', 0x00, 0x03, 0x80, 0x00))  # Type info
    cohort_data.extend(struct.pack('<B', 0x00))  # REQUIRED padding byte
    
    num_target_values = len(target_instances) * 2
    cohort_data.extend(struct.pack('<I', num_target_values))
    
    # Add target pairs [GroupID, InstanceID]
    for instance in target_instances:
        cohort_data.extend(struct.pack('<I', 0xA8FBD372))  # GroupID
        cohort_data.extend(struct.pack('<I', instance))     # InstanceID
    
    # Property 2: MinSlope
    cohort_data.extend(struct.pack('<I', 0x699B08A4))  # Property ID
    cohort_data.extend(struct.pack('<BBBB', 0x00, 0x09, 0x80, 0x00))  # Type info
    cohort_data.extend(struct.pack('<B', 0x00))  # REQUIRED padding byte
    cohort_data.extend(struct.pack('<I', 1))     # Array length
    cohort_data.extend(struct.pack('<f', 89.0))  # MinSlope value
    
    return bytes(cohort_data)
```

### Instance ID Generation

**Cohort exemplars require unique Instance IDs to avoid conflicts.** Our implementation uses a hash-based approach within the private ID range:

```python
def generate_instance_id(group_name):
    """Generate unique instance ID for cohort exemplar."""
    # Use private range to avoid conflicts with Maxis content
    # Private range: 0x10000000 - 0x1FFFFFFF (268,435,456 - 536,870,911)
    PRIVATE_RANGE_START = 0x10000000
    
    # Create hash from group name for reproducible IDs
    import hashlib
    hash_object = hashlib.md5(group_name.encode())
    hash_hex = hash_object.hexdigest()
    
    # Convert first 8 hex chars to int and map to private range
    hash_int = int(hash_hex[:8], 16)
    instance_id = PRIVATE_RANGE_START + (hash_int % 0x10000000)
    
    return instance_id
```

**Benefits:**

- **Collision Avoidance:** Private range prevents conflicts with official Maxis content
- **Reproducibility:** Same group name always generates same instance ID
- **Distribution:** Hash function ensures good distribution across private range

### DBPF File Structure for Patches

```python
def create_patch_dbpf(cohort_data, instance_id):
    """Create complete DBPF file containing cohort exemplar."""
    
    # Calculate data offset (after 96-byte header)
    data_offset = 96
    data_size = len(cohort_data)
    index_offset = data_offset + data_size
    
    # Build DBPF file
    dbpf_data = bytearray()
    
    # Header (96 bytes)
    dbpf_data.extend(b'DBPF')                           # Magic
    dbpf_data.extend(struct.pack('<II', 1, 0))          # Version
    dbpf_data.extend(b'\x00' * 12)                      # Reserved
    dbpf_data.extend(struct.pack('<II', timestamp, timestamp))  # Dates
    dbpf_data.extend(struct.pack('<III', 7, 1, index_offset))   # Index info
    dbpf_data.extend(struct.pack('<I', 20))             # Index size
    dbpf_data.extend(b'\x00' * 32)                      # Reserved
    dbpf_data.extend(struct.pack('<I', 0))              # Reserved
    dbpf_data.extend(b'\x00' * 12)                      # Reserved
    
    # Cohort data
    dbpf_data.extend(cohort_data)
    
    # Index entry (20 bytes)
    dbpf_data.extend(struct.pack('<I', 0x05342861))     # TypeID (Cohort)
    dbpf_data.extend(struct.pack('<I', 0xb03697d1))     # GroupID (Patches)
    dbpf_data.extend(struct.pack('<I', instance_id))    # InstanceID
    dbpf_data.extend(struct.pack('<I', data_offset))    # Offset
    dbpf_data.extend(struct.pack('<I', data_size))      # Size
    
    return bytes(dbpf_data)
```

### Grouping Logic

Lots are grouped by ZonePurpose + ZoneWealth combinations:

| Group | ZonePurpose | ZoneWealth | Description |
|-------|-------------|------------|-------------|
| R$ | 1 | 1 | Low wealth residential |
| R$$ | 1 | 2 | Medium wealth residential |
| R$$$ | 1 | 3 | High wealth residential |
| CS$ | 2 | 1 | Low wealth commercial services |
| CS$$ | 2 | 2 | Medium wealth commercial services |
| CS$$$ | 2 | 3 | High wealth commercial services |
| CO$$ | 3 | 2 | Medium wealth commercial office |
| CO$$$ | 3 | 3 | High wealth commercial office |
| I-r$ | 5 | 1 | Raw materials industrial |
| I-d$$ | 6 | 2 | Dirty industrial |
| I-m$$ | 7 | 2 | Manufacturing industrial |
| I-ht$$$ | 8 | 3 | High-tech industrial |

**Filtering Logic:**

- Exclude ZoneTypes: 10-15 (special buildings, landmarks, civic)
- Require valid ZonePurpose and ZoneWealth
- Result: 1,734 lots targeted (91% coverage)

---

## Datpacking System

### Purpose

Combine multiple .dat patch files into a single DBPF file for easier installation and management.

### Process Overview

1. **Read Source Files:** Parse each input .dat file's DBPF structure
2. **Collect Entries:** Extract all exemplar data and index information
3. **Detect Conflicts:** Check for duplicate TGI (Type/Group/Instance) combinations
4. **Combine Data:** Merge all exemplars into single archive
5. **Generate Output:** Create new DBPF file with combined index

### Implementation

```python
def datpack_files(input_files, output_path):
    """Combine multiple DBPF files into single archive."""
    combined_entries = {}
    
    # Process each input file
    for file_path in input_files:
        header = read_dbpf_header(file_path)
        entries = read_dbpf_index(file_path, header)
        
        for entry in entries:
            tgi = (entry['type_id'], entry['group_id'], entry['instance_id'])
            
            # Check for conflicts
            if tgi in combined_entries:
                print(f"WARNING: Duplicate TGI {tgi} - overwriting")
            
            # Read entry data
            data = read_entry_data(file_path, entry)
            combined_entries[tgi] = (entry, data)
    
    # Write combined DBPF
    write_datpacked_dbpf(output_path, combined_entries)
    
    return len(combined_entries)
```

### DBPF Generation

```python
def write_datpacked_dbpf(output_path, combined_entries):
    """Write combined entries to new DBPF file."""
    with open(output_path, 'wb') as f:
        # Write header
        f.write(b'DBPF')
        f.write(struct.pack('<II', 1, 0))  # Version
        f.write(b'\x00' * 12)  # Reserved
        
        timestamp = int(time.time())
        f.write(struct.pack('<II', timestamp, timestamp))
        
        index_count = len(combined_entries)
        # Write placeholder for index offset - will update later
        index_offset_pos = f.tell()
        f.write(struct.pack('<III', 7, index_count, 0))
        f.write(struct.pack('<I', index_count * 20))  # Index size
        f.write(b'\x00' * 44)  # Remaining header
        
        # Write entry data and track positions
        entry_positions = {}
        for tgi, (entry, data) in combined_entries.items():
            entry_start = f.tell()
            f.write(data)
            entry_positions[tgi] = {
                'offset': entry_start,
                'size': len(data),
                'entry': entry
            }
        
        # Write index table
        index_start = f.tell()
        for tgi, pos_info in entry_positions.items():
            f.write(struct.pack('<IIIII',
                pos_info['entry']['type_id'],
                pos_info['entry']['group_id'], 
                pos_info['entry']['instance_id'],
                pos_info['offset'],
                pos_info['size']
            ))
        
        # Update index offset in header
        f.seek(index_offset_pos + 8)
        f.write(struct.pack('<I', index_start))
```

---

## Implementation Guide

### 1. Basic Parser Setup

```python
import struct
import qfs  # QFS decompression module

def extract_lot_configurations(dbpf_file):
    """Extract all LotConfiguration exemplars from DBPF file."""
    with open(dbpf_file, 'rb') as f:
        data = f.read()
    
    # Parse DBPF header
    if data[:4] != b'DBPF':
        raise ValueError("Not a valid DBPF file")
    
    index_count = struct.unpack('<I', data[36:40])[0]
    index_offset = struct.unpack('<I', data[40:44])[0]
    
    lot_configurations = []
    
    # Process each entry
    for i in range(index_count):
        entry_offset = index_offset + i * 20
        tid, gid, iid, offset, size = struct.unpack('<IIIII', 
            data[entry_offset:entry_offset+20])
        
        # Filter for LotConfigurations
        if tid == 0x6534284A and gid == 0xA8FBD372:
            raw_data = data[offset:offset+size]
            
            # Decompress if needed
            if len(raw_data) >= 6 and raw_data[4:6] == b'\x10\xfb':
                eqzb_data = qfs.decompress(raw_data[4:])
            else:
                eqzb_data = raw_data
            
            # Parse properties
            properties = parse_exemplar_properties(eqzb_data)
            
            lot_configurations.append({
                'iid': f"0x{iid:08X}",
                'size': size,
                'properties': properties
            })
    
    return lot_configurations
```

### 2. Property Parsing Function

```python
def parse_exemplar_properties(data):
    """Parse exemplar properties using validated structure."""
    offset = 20  # Skip EQZB header
    
    if offset + 4 > len(data):
        return {}
    
    prop_count = struct.unpack('<L', data[offset:offset+4])[0]
    offset += 4
    
    properties = {}
    
    for _ in range(prop_count):
        if offset + 13 > len(data):
            break
        
        # Parse property header (13 bytes)
        property_id = struct.unpack('<I', data[offset:offset+4])[0]
        data_type = struct.unpack('<H', data[offset+4:offset+6])[0]
        w8 = struct.unpack('<H', data[offset+6:offset+8])[0]
        rep = struct.unpack('>H', data[offset+8:offset+10])[0]  # BIG-ENDIAN!
        padding = data[offset+10:offset+13]
        
        if padding != b'\x00\x00\x00':
            continue
        
        offset += 13
        
        # Handle special rep-encoded properties
        if property_id in {0x27812837, 0x4A4A88F0} and data_type == 0x0100:
            properties[get_property_name(property_id)] = rep
            continue
        
        # Parse based on data type
        if data_type == 0x0C00:  # String
            if rep > 0:
                str_data = data[offset:offset+rep]
                properties[get_property_name(property_id)] = str_data.decode('utf-8', errors='ignore')
                offset += rep
        elif data_type == 0x0100:  # UINT8 array
            if rep > 0:
                values = struct.unpack(f'<{rep}B', data[offset:offset+rep])
                properties[get_property_name(property_id)] = list(values)
                offset += rep
        elif data_type == 0x0700:  # UINT32 array
            if rep > 0:
                values = struct.unpack(f'<{rep}I', data[offset:offset+rep*4])
                properties[get_property_name(property_id)] = list(values)
                offset += rep * 4
    
    return properties

def get_property_name(property_id):
    """Convert property ID to human-readable name."""
    property_names = {
        0x00000020: 'ExemplarName',
        0x88EDC790: 'LotConfigPropertySize',
        0x88EDC793: 'ZoneTypes',
        0x88EDC795: 'ZoneWealth',
        0x88EDC796: 'PurposeTypes',
        0x27812837: 'GrowthStage',
        0x4A4A88F0: 'RoadCornerIndicator'
    }
    return property_names.get(property_id, f'Unknown_0x{property_id:08X}')
```

### 3. Complete Working Example

See `scripts/extract_maxis_lots.py` for the complete, production-tested implementation.

---

## Validation Framework

### Integration Test Suite

The validation framework tests actual production functions rather than duplicating logic:

```python
# integration_validation.py
def test_full_pipeline():
    """Test complete extraction using actual extract_maxis_lots function."""
    lot_configurations = extract_maxis_lots(dbpf_file, temp_output)
    
    # Validate results
    assert len(lot_configurations) >= 1900  # Expected lot count
    assert all('properties' in lot for lot in lot_configurations)
    
def test_regression_cases():
    """Test known good values from actual results."""
    regression_tests = {
        '0x60000474': {
            'GrowthStage': 6,
            'RoadCornerIndicator': 12,
            'ExemplarName': 'CO$$6_3x3'
        }
    }
    # Validate against actual extraction results...
```

### Test Coverage

- **File Access:** DBPF header parsing, index table reading
- **QFS Decompression:** Compression detection, decompression success
- **Property Parsing:** All 7 target properties, special encoding cases
- **Full Pipeline:** End-to-end extraction with performance validation
- **Regression Testing:** Known good values from working lots

### Running Validation

```bash
# Quick validation
python integration_validation.py --quick

# Full validation with regression tests
python integration_validation.py

# Test specific functionality
python integration_validation.py --function property_parsing
```

---

## Production Statistics

### Extraction Results

- **Total DBPF Entries:** 60,440+
- **LotConfigurations Found:** 1,908 (3.2%)
- **Property Extraction Success:** 100%
- **Coverage by Property:**
  - ExemplarName: 100% (1,908/1,908)
  - LotConfigPropertySize: 99.4% (1,897/1,908)
  - ZoneTypes: 99.4% (1,897/1,908)
  - ZoneWealth: 100% (1,908/1,908)
  - PurposeTypes: 100% (1,908/1,908)
  - GrowthStage: 79.8% (1,523/1,908)
  - RoadCornerIndicator: 93.9% (1,791/1,908)

### Patch Generation Results

- **Total Lots Processed:** 1,908
- **Lots Excluded (special buildings):** 174 (9.1%)
- **Lots Targeted for Patching:** 1,734 (90.9%)
- **Patch Files Generated:** 12 (one per RCI/wealth combination)

### Performance Metrics

- **Extraction Time:** ~1.2 seconds for full SimCity_1.dat
- **Processing Rate:** ~1,600 lots/second
- **Memory Usage:** <100MB peak during processing
- **File Sizes:** 
  - Input: SimCity_1.dat (144MB)
  - Output: lot_configurations.json (1.2MB)
  - Patches: 12 files totaling ~150KB

---

## Quick Reference

### Critical Constants

```python
# File type identifiers
EXEMPLAR_TYPE_ID = 0x6534284A
LOTCONFIG_GROUP_ID = 0xA8FBD372
COHORT_TYPE_ID = 0x05342861
PATCH_GROUP_ID = 0xb03697d1

# Property IDs
PROPERTIES = {
    'ExemplarName': 0x00000020,
    'LotConfigPropertySize': 0x88EDC790,
    'ZoneTypes': 0x88EDC793,
    'ZoneWealth': 0x88EDC795,
    'PurposeTypes': 0x88EDC796,
    'GrowthStage': 0x27812837,
    'RoadCornerIndicator': 0x4A4A88F0
}

# Special rep-encoded properties
REP_ENCODED_PROPERTIES = {0x27812837, 0x4A4A88F0}

# Data types
DATA_TYPES = {
    'STRING': 0x0C00,
    'UINT8': 0x0100,
    'UINT32': 0x0700,
    'FLOAT32': 0x0900
}
```

### Key Endianness Rules

- **Everything is little-endian EXCEPT:**
  - Rep field in property header (BIG-ENDIAN)
  - Magic signatures (ASCII)

### Validation Checklist

- [ ] DBPF magic signature = "DBPF"
- [ ] Index entry count > 0
- [ ] LotConfiguration count ≈ 1,900
- [ ] QFS decompression success rate > 80%
- [ ] Property extraction success rate > 95%
- [ ] Known test cases pass regression tests

---

## Dependencies

### Required Modules

- **qfs.py:** QFS decompression (included in codebase)
- **struct:** Binary data parsing (Python standard library)
- **json:** Output format (Python standard library)

### File Requirements

- **Input:** SimCity_1.dat (144MB DBPF file)
- **Output:** lot_configurations.json (1.2MB extracted data)
- **Validation:** integration_validation.py (test suite)

### System Requirements

- **Python:** 3.6+ (for f-strings and type hints)
- **Memory:** 200MB+ available RAM
- **Storage:** 200MB+ free space for output files
- **Performance:** ~1-2 seconds extraction time on modern hardware

---

This technical reference contains all information necessary to recreate and extend the DBPF parsing system. All data structures, algorithms, and critical insights have been validated through production use and comprehensive testing.

**Last Updated:** September 2025  
**Codebase Version:** Integration-validated production release
