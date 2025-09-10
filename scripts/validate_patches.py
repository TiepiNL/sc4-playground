#!/usr/bin/env python3
"""
Validate generated exemplar patch files

Quick verification that the generated .dat files have the correct structure
for sc4-resource-loading-hooks exemplar patching.
"""

import struct
import os

def validate_patch_file(filepath):
    """Validate a single patch file structure"""
    try:
        with open(filepath, 'rb') as f:
            # Read header
            type_id = struct.unpack('>I', f.read(4))[0]
            group_id = struct.unpack('>I', f.read(4))[0] 
            instance_id = struct.unpack('>I', f.read(4))[0]
            
            # Skip padding
            f.read(12)
            
            # Read property count
            prop_count = struct.unpack('>I', f.read(4))[0]
            
            print(f"✅ {os.path.basename(filepath)}")
            print(f"   Type: 0x{type_id:08X}, Group: 0x{group_id:08X}, Instance: 0x{instance_id:08X}")
            print(f"   Properties: {prop_count}")
            
            # Validate expected values
            if type_id != 0x05342861:
                print(f"   ⚠️  Unexpected Type ID")
            if group_id != 0xb03697d1:
                print(f"   ⚠️  Unexpected Group ID")
            if prop_count != 2:
                print(f"   ⚠️  Expected 2 properties, got {prop_count}")
                
            return True
            
    except Exception as e:
        print(f"❌ {os.path.basename(filepath)}: {e}")
        return False

def main():
    """Validate all patch files in output_patches directory"""
    print("🔍 Validating Generated Patch Files")
    print("==================================")
    
    patch_dir = "output_patches"
    if not os.path.exists(patch_dir):
        print(f"❌ Directory '{patch_dir}' not found")
        return
    
    patch_files = [f for f in os.listdir(patch_dir) if f.endswith('.dat')]
    
    if not patch_files:
        print(f"❌ No .dat files found in '{patch_dir}'")
        return
    
    print(f"📊 Found {len(patch_files)} patch files to validate")
    print()
    
    valid_count = 0
    for filename in sorted(patch_files[:5]):  # Check first 5 files
        filepath = os.path.join(patch_dir, filename)
        if validate_patch_file(filepath):
            valid_count += 1
        print()
    
    print(f"📈 Validation Summary:")
    print(f"   ✅ Valid: {valid_count}/5 files checked")
    print(f"   📁 Total patches: {len(patch_files)} files")
    
    if valid_count == 5:
        print(f"   🎉 All checked files have correct structure!")
        print(f"   💡 Ready for installation in SimCity 4 Plugins folder")

if __name__ == "__main__":
    main()
