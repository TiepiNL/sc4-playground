#!/usr/bin/env python3
"""
SimCity 4 Exemplar Patch Generator

This script creates exemplar patch files that modify Maxis LotConfiguration exemplars
to block RCI (Residential, Commercial, Industrial) development by setting MinSlope
to 89.0 degrees, making lots unbuildable.

Uses the sc4-resource-loading-hooks exemplar patching system:
- Creates Cohort files with Group ID 0xb03697d1
- Uses Exemplar Patch Targets property (0x0062e78a) to specify target exemplars
- Groups related lots by ExemplarName patterns into single patch files
- Each patch adds MinSlope=89.0 property to make lots too steep to build on

Input: lot_configurations.json (from extract_maxis_lots.py)
Output: Multiple .dat patch files in output_patches/ directory
"""

import json
import struct
import os
import shutil # Import for directory operations
import zipfile # Import for creating zip archives
from collections import defaultdict

# --- Configuration ---
INPUT_JSON_PATH = "data/lot_configurations.json"
OUTPUT_DIR = "output_patches"
FILENAME_PREFIX = "stop_maxis_growable_"

# --- DBPF/Exemplar Patch Constants ---
PATCH_COHORT_TYPE_ID = 0x05342861          # Cohort exemplar type
PATCH_COHORT_GROUP_ID = 0xb03697d1         # Exemplar patch group (required by sc4-resource-loading-hooks)
LOT_CONFIG_GROUP_ID = 0xA8FBD372           # LotConfiguration group ID (all lots use this)
PROP_MIN_SLOPE_ID = 0x699b08a4             # MinSlope property ID
PROP_PATCH_TARGETS_ID = 0x0062e78a         # Exemplar Patch Targets property ID

# Starting instance ID for generated patches (preserved from original code)
try:
    STARTING_INSTANCE_ID = int(os.getenv('STARTING_INSTANCE_ID', '0xfe7cd975'), 16)
except (ValueError, TypeError):
    print("Warning: Invalid STARTING_INSTANCE_ID format. Using default.")
    STARTING_INSTANCE_ID = 0xfe7cd975

def write_patch_file(filename: str, patch_instance_id: int, targets: list):
    """
    Writes a binary-correct DBPF file containing a Cohort Exemplar Patch.
    
    Format follows DBPF specification and sc4-resource-loading-hooks requirements:
    - DBPF header (96 bytes)
    - Cohort file with Group ID 0xb03697d1 
    - Contains MinSlope property set to 89.0 degrees
    - Contains Exemplar Patch Targets property with list of target exemplars
    - File index table pointing to the Cohort entry
    
    Args:
        filename: Output .dat file path
        patch_instance_id: Unique instance ID for this patch
        targets: List of (group_id, instance_id) tuples for target exemplars
    """
    with open(filename, 'wb') as f:
        # === DBPF Header (96 bytes) ===
        # Magic number "DBPF"
        f.write(b'DBPF')
        
        # Version (1.0)
        f.write(struct.pack('<II', 1, 0))  # Major, Minor version
        
        # Reserved fields (12 bytes of zeros)
        f.write(b'\x00' * 12)
        
        # Timestamps (created, modified - Unix timestamps)
        import time
        timestamp = int(time.time())
        f.write(struct.pack('<II', timestamp, timestamp))
        
        # Index information (will be filled in later)
        index_major = 7
        index_count = 1  # We have one entry (the Cohort)
        index_offset_pos = f.tell()  # Remember position to update later
        f.write(struct.pack('<III', index_major, index_count, 0))  # index_offset will be updated
        index_size_pos = f.tell()  # Remember position to update later
        f.write(struct.pack('<I', 0))  # index_size will be updated
        
        # More reserved fields
        f.write(b'\x00' * 32)
        
        # Index minor version
        f.write(struct.pack('<I', 0))
        
        # Pad header to 96 bytes
        f.write(b'\x00' * 12)
        
        # === Cohort Entry Data ===
        entry_start = f.tell()
        
        # Build the Cohort exemplar data
        cohort_data = bytearray()
        
        # Cohort Exemplar Header (CQZB format)
        # Magic number "CQZB" + additional header bytes (20 bytes total)
        cohort_data.extend(b'CQZB')                    # Magic number
        cohort_data.extend(b'1###')                    # Version/type identifier 
        cohort_data.extend(b'\x00' * 12)              # Reserved/padding bytes
        
        # Property count (2 properties: ExemplarPatchTargets + MinSlope)
        cohort_data.extend(struct.pack('<I', 2))
        
        # Property 1: Exemplar Patch Targets (list of target exemplars) - FIRST
        cohort_data.extend(struct.pack('<I', PROP_PATCH_TARGETS_ID))
        cohort_data.extend(struct.pack('<BBBB', 0x00, 0x03, 0x80, 0x00))  # Exact format from working example
        cohort_data.extend(struct.pack('<B', 0x00))  # Extra padding byte (required for correct parsing)
        num_target_values = len(targets) * 2  # Each target = group_id + instance_id
        cohort_data.extend(struct.pack('<I', num_target_values))
        
        # Write alternating group_id, instance_id pairs
        for group_id, instance_id in targets:
            cohort_data.extend(struct.pack('<II', group_id, instance_id))
        
        # Property 2: MinSlope = 89.0 degrees (makes lots unbuildable) - SECOND
        cohort_data.extend(struct.pack('<I', PROP_MIN_SLOPE_ID))
        cohort_data.extend(struct.pack('<BBBB', 0x00, 0x09, 0x80, 0x00))  # Format for float property
        cohort_data.extend(struct.pack('<B', 0x00))  # Extra padding byte (for consistency)
        cohort_data.extend(struct.pack('<I', 1))  # Array length
        cohort_data.extend(struct.pack('<f', 89.0))  # MinSlope value
        
        # Write the Cohort data
        f.write(cohort_data)
        entry_size = len(cohort_data)
        
        # === File Index Table ===
        index_start = f.tell()
        
        # Index entry for our Cohort file
        # TGI (Type, Group, Instance)
        f.write(struct.pack('<III', PATCH_COHORT_TYPE_ID, PATCH_COHORT_GROUP_ID, patch_instance_id))
        # Offset and size
        f.write(struct.pack('<II', entry_start, entry_size))
        
        index_end = f.tell()
        index_size = index_end - index_start
        
        # === Update header with index information ===
        # Go back and update index_offset
        f.seek(index_offset_pos)
        f.write(struct.pack('<III', index_major, index_count, index_start))
        
        # Update index_size
        f.seek(index_size_pos)
        f.write(struct.pack('<I', index_size))
    
    print(f"  -> Created '{os.path.basename(filename)}' with InstanceID 0x{patch_instance_id:08X} ({len(targets)} targets)")

def get_group_name_from_purpose_wealth(zone_purpose, zone_wealth):
    """
    Generate patch group name based on ZonePurpose and ZoneWealth values.
    
    Args:
        zone_purpose: ZonePurpose value (single integer)
        zone_wealth: ZoneWealth value (single integer)
    
    Returns:
        String representing the group name for the patch file
    """
    # Purpose mapping: 0x01=R, 0x02=CS, 0x03=CO, 0x05=I-R, 0x06=I-D, 0x07=I-M, 0x08=I-HT
    purpose_map = {
        1: "R",        # Residential
        2: "CS",       # Commercial Service  
        3: "CO",       # Commercial Office
        5: "I-r",      # Industrial - Resource/Raw Materials
        6: "I-d",      # Industrial - Dirty/Manufacturing
        7: "I-m",      # Industrial - Manufacturing  
        8: "I-ht"      # Industrial - High Tech
    }
    
    # Wealth mapping: 0x01=$, 0x02=$$, 0x03=$$$
    wealth_map = {
        1: "$",
        2: "$$", 
        3: "$$$"
    }
    
    purpose_str = purpose_map.get(zone_purpose, f"Unknown{zone_purpose}")
    wealth_str = wealth_map.get(zone_wealth, f"W{zone_wealth}")
    
    return f"{purpose_str}{wealth_str}"

def main():
    """
    Main function to read JSON and generate exemplar patch files.
    
    Reads the lot_configurations.json file produced by extract_maxis_lots.py
    and creates exemplar patch files that make Maxis lots unbuildable by 
    setting MinSlope to 89.0 degrees.
    
    Lots are grouped by ZonePurpose and ZoneWealth combinations (e.g., all "CS$$" lots
    go into one patch file) to create manageable, organized patch files.
    """
    print("🏗️  SimCity 4 Exemplar Patch Generator")
    print("=====================================")
    print(f"Reading extracted data from {INPUT_JSON_PATH}")
    
    try:
        with open(INPUT_JSON_PATH, 'r') as f: 
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ ERROR: Input file not found at '{INPUT_JSON_PATH}'.")
        print("   Run the extraction script first:")
        print("   python scripts/extract_maxis_lots.py data/SimCity_1.dat")
        return
    except json.JSONDecodeError as e:
        print(f"❌ ERROR: Invalid JSON format in '{INPUT_JSON_PATH}': {e}")
        return

    # Validate JSON structure
    if 'lot_configurations' not in data:
        print(f"❌ ERROR: Expected 'lot_configurations' key in JSON file")
        print("   Make sure the file was generated by extract_maxis_lots.py")
        return
    
    lot_configurations = data['lot_configurations']
    print(f"📊 Found {len(lot_configurations)} LotConfigurations to process")

    # Clean output directory before starting
    if os.path.exists(OUTPUT_DIR):
        print(f"🧹 Cleaning existing output directory: {OUTPUT_DIR}")
        try:
            # Remove all .dat files in the directory
            for filename in os.listdir(OUTPUT_DIR):
                if filename.endswith('.dat'):
                    filepath = os.path.join(OUTPUT_DIR, filename)
                    os.remove(filepath)
            print(f"🗑️  Removed existing .dat files from {OUTPUT_DIR}")
        except Exception as e:
            print(f"⚠️  Warning: Could not clean directory completely: {e}")
    else:
        # Create output directory if it doesn't exist
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        print(f"📁 Created output directory: {OUTPUT_DIR}")

    # Group lots by ExemplarName pattern for organized patch files
    # Only process lots with valid ZoneTypes (excludes null and zones 10-15: Military/Airport/Seaport/Spaceport/Landmark/Civic)
    grouped_targets = defaultdict(list)
    valid_exemplars_found = 0
    skipped_no_name = 0
    skipped_invalid_name = 0
    skipped_invalid_iid = 0
    skipped_invalid_zone_types = 0

    for lot_config in lot_configurations:
        # Extract data from new JSON structure
        instance_id_str = lot_config.get('iid')
        properties = lot_config.get('properties', {})
        
        # Handle case where properties might not be a dictionary
        if not isinstance(properties, dict):
            skipped_invalid_name += 1
            continue
            
        exemplar_name = properties.get('ExemplarName')
        zone_types = properties.get('ZoneTypes')
        zone_purpose = properties.get('ZonePurpose')
        zone_wealth = properties.get('ZoneWealth')
        
        # 1. Skip if instance ID is missing
        if not instance_id_str:
            skipped_invalid_iid += 1
            continue
        
        # 2. Skip if ZoneTypes contains values that should be excluded
        # Exclusion list:
        # - null: Incomplete lot definitions
        # - 0x0A (10): Military zones
        # - 0x0B (11): Airport zones  
        # - 0x0C (12): Seaport zones
        # - 0x0D (13): Spaceport zones
        # - 0x0E (14): Landmark zones
        # - 0x0F (15): Civic/Plopped buildings (all zones compatible)
        excluded_zone_types = {10, 11, 12, 13, 14, 15}  # 0x0A through 0x0F
        
        if zone_types is None:
            skipped_invalid_zone_types += 1
            continue
        
        # Check if ZoneTypes contains any excluded values
        if isinstance(zone_types, list):
            if any(zt in excluded_zone_types for zt in zone_types):
                skipped_invalid_zone_types += 1
                continue
        elif zone_types in excluded_zone_types:
            skipped_invalid_zone_types += 1
            continue
            
        # 3. Skip if ZonePurpose is missing or null
        if zone_purpose is None:
            skipped_no_name += 1
            continue
            
        # 4. Skip if ZoneWealth is missing or null
        if zone_wealth is None:
            skipped_invalid_name += 1
            continue

        # 5. Handle ZonePurpose and ZoneWealth arrays
        # Extract single values or first value from arrays
        if isinstance(zone_purpose, list):
            if not zone_purpose:  # Empty list
                skipped_no_name += 1
                continue
            purpose_values = zone_purpose
        else:
            purpose_values = [zone_purpose]
            
        if isinstance(zone_wealth, list):
            if not zone_wealth:  # Empty list
                skipped_invalid_name += 1
                continue
            wealth_values = zone_wealth
        else:
            wealth_values = [zone_wealth]

        # 6. Generate patch files for each purpose/wealth combination
        # This handles lots with multiple wealth values by adding them to multiple groups
        for purpose in purpose_values:
            for wealth in wealth_values:
                group_name = get_group_name_from_purpose_wealth(purpose, wealth)
                filename = f"{FILENAME_PREFIX}{group_name}.dat"
        
                try:
                    # Convert hex string to integer (remove 0x prefix if present)
                    instance_id_str_clean = instance_id_str.replace('0x', '').replace('0X', '')
                    instance_id_int = int(instance_id_str_clean, 16)
                    
                    # All LotConfigurations use the same Group ID
                    group_id_int = LOT_CONFIG_GROUP_ID
                    
                    # Add to the appropriate patch file group
                    grouped_targets[filename].append((group_id_int, instance_id_int))
                    
                except (ValueError, TypeError) as e:
                    # Skip if conversion from hex string to int fails
                    skipped_invalid_iid += 1
                    continue
        
        # Count this as one valid exemplar (even if added to multiple groups)
        valid_exemplars_found += 1

    # Report processing statistics
    print(f"\n📈 Processing Statistics:")
    print(f"   ✅ Valid exemplars: {valid_exemplars_found}")
    print(f"   ⚠️  Skipped (invalid ZoneTypes): {skipped_invalid_zone_types}")
    print(f"   ⚠️  Skipped (no ZonePurpose): {skipped_no_name}")
    print(f"   ⚠️  Skipped (no ZoneWealth): {skipped_invalid_name}")
    print(f"   ⚠️  Skipped (invalid Instance ID): {skipped_invalid_iid}")

    if not grouped_targets:
        print("\n❌ No valid groups to generate patch files for. Halting.")
        print("   Note: All lots may have been filtered out due to ZoneTypes restrictions.")
        print("   ZoneTypes filter excludes: null, 0x0A-0x0F (Military, Airport, Seaport, Spaceport, Landmark, Civic)")
        return

    print(f"\n🚀 Generating {len(grouped_targets)} patch files in '{OUTPUT_DIR}/'...")
    print(f"📍 Using starting InstanceID: 0x{STARTING_INSTANCE_ID:08X}")
    print(f"🎯 Target lots will have MinSlope set to 89.0° (unbuildable)")
    print(f"📋 Grouping: By ZonePurpose + ZoneWealth (R/CS/CO/I-* + $/$$/$$$ combinations)")
    print(f"📋 Filtering: ZoneTypes excluding null, 0x0A-0x0F (Military/Airport/Seaport/Spaceport/Landmark/Civic)")

    # Generate patch files in alphabetical order for consistency
    sorted_filenames = sorted(grouped_targets.keys())
    current_instance_id = STARTING_INSTANCE_ID
    
    for filename in sorted_filenames:
        targets = grouped_targets[filename]
        full_path = os.path.join(OUTPUT_DIR, filename)
        write_patch_file(full_path, current_instance_id, targets)
        current_instance_id += 1

    print(f"\n🎉 Patch generation complete!")
    print(f"📁 Generated {len(grouped_targets)} patch files in '{OUTPUT_DIR}/'")
    
    # Create zip file containing all patch files
    zip_filename = os.path.join(OUTPUT_DIR, "maxis_blockers.zip")
    print(f"📦 Creating zip archive: {zip_filename}")
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add all .dat files to the zip
        dat_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.dat')]
        for dat_file in sorted(dat_files):
            file_path = os.path.join(OUTPUT_DIR, dat_file)
            zipf.write(file_path, dat_file)  # Store with just filename, not full path
            print(f"  ✅ Added {dat_file}")
    
    zip_size = os.path.getsize(zip_filename)
    print(f"📦 Created maxis_blockers.zip ({zip_size:,} bytes)")
    
    print(f"🎮 Install: Copy .dat files to your SimCity 4 Plugins folder")
    print(f"💡 Effect: Targeted Maxis lots will become unbuildable (RCI blocked)")
    print(f"🔧 Requires: sc4-resource-loading-hooks.dll in Plugins folder")

if __name__ == "__main__":
    main()
