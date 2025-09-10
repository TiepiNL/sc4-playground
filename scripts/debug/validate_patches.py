#!/usr/bin/env python3
"""
Patch File Validation Script

This script validates that our generated exemplar patch files have the correct structure
and properties compared to the working example patch file.
"""

import os
import sys
from dbpf_parser import DBPFParser

def validate_patch_file(filepath, expected_targets=None):
    """Validate a single patch file"""
    print(f"\n🔍 Validating: {os.path.basename(filepath)}")
    
    parser = DBPFParser(filepath)
    result = parser.parse()
    
    if not result:
        print("❌ Failed to parse file")
        return False
    
    # Check basic structure
    issues = []
    
    # Should have exactly 1 entry
    if len(result['entries']) != 1:
        issues.append(f"Expected 1 entry, found {len(result['entries'])}")
    
    entry = result['entries'][0]
    entry_info = entry['entry_info']
    
    # Check TGI values
    if entry_info['type_id'] != 0x05342861:
        issues.append(f"Wrong Type ID: 0x{entry_info['type_id']:08X} (expected 0x05342861)")
    
    if entry_info['group_id'] != 0xb03697d1:
        issues.append(f"Wrong Group ID: 0x{entry_info['group_id']:08X} (expected 0xB03697D1)")
    
    # Check exemplar structure
    data = entry['data']
    
    if 'property_count' not in data:
        issues.append("No property count found")
        print(f"❌ Issues found: {'; '.join(issues)}")
        return False
    
    if data['property_count'] != 2:
        issues.append(f"Expected 2 properties, found {data['property_count']}")
    
    # Check for required properties
    found_properties = {}
    if 'parsed_properties' in data:
        for prop in data['parsed_properties']:
            prop_id = prop['id_decimal']
            found_properties[prop_id] = prop
    
    # Must have ExemplarPatchTargets (0x0062e78a)
    if 0x0062e78a not in found_properties:
        issues.append("Missing ExemplarPatchTargets property (0x0062E78A)")
    else:
        prop = found_properties[0x0062e78a]
        if 'total_targets' in prop['data']:
            targets_found = prop['data']['total_targets']
            print(f"   ✅ ExemplarPatchTargets: {targets_found} targets")
            if expected_targets and targets_found != expected_targets:
                issues.append(f"Expected {expected_targets} targets, found {targets_found}")
        elif 'pairs' in prop['data']:
            targets_found = len(prop['data']['pairs'])
            print(f"   ✅ ExemplarPatchTargets: {targets_found} targets")
    
    # Must have MinSlope (0x699b08a4)
    if 0x699b08a4 not in found_properties:
        issues.append("Missing MinSlope property (0x699B08A4)")
    else:
        prop = found_properties[0x699b08a4]
        if 'values' in prop['data'] and len(prop['data']['values']) > 0:
            min_slope = prop['data']['values'][0]
            print(f"   ✅ MinSlope: {min_slope}°")
            if abs(min_slope - 89.0) > 0.1:
                issues.append(f"Wrong MinSlope value: {min_slope} (expected 89.0)")
        else:
            issues.append("MinSlope property has no value")
    
    if issues:
        print(f"❌ Issues found: {'; '.join(issues)}")
        return False
    else:
        print("   ✅ File structure is correct!")
        return True

def main():
    """Validate all patch files"""
    print("🔧 SC4 Exemplar Patch File Validator")
    print("====================================")
    
    # Expected target counts for each file (from the last run)
    expected_counts = {
        'stop_maxis_growable_CO$$$.dat': 278,
        'stop_maxis_growable_CO$$.dat': 291,
        'stop_maxis_growable_CS$$$.dat': 201,
        'stop_maxis_growable_CS$$.dat': 238,
        'stop_maxis_growable_CS$.dat': 144,
        'stop_maxis_growable_I-d$$.dat': 89,
        'stop_maxis_growable_I-ht$$$.dat': 71,
        'stop_maxis_growable_I-m$$.dat': 90,
        'stop_maxis_growable_I-r$.dat': 31,
        'stop_maxis_growable_R$$$.dat': 95,
        'stop_maxis_growable_R$$.dat': 101,
        'stop_maxis_growable_R$.dat': 105
    }
    
    output_dir = 'output_patches'
    if not os.path.exists(output_dir):
        print(f"❌ Output directory not found: {output_dir}")
        return
    
    # Get all .dat files
    dat_files = [f for f in os.listdir(output_dir) if f.endswith('.dat')]
    if not dat_files:
        print(f"❌ No .dat files found in {output_dir}")
        return
    
    print(f"📁 Found {len(dat_files)} patch files to validate")
    
    # Validate each file
    valid_files = 0
    total_targets = 0
    
    for filename in sorted(dat_files):
        filepath = os.path.join(output_dir, filename)
        expected_targets = expected_counts.get(filename)
        
        if validate_patch_file(filepath, expected_targets):
            valid_files += 1
            if expected_targets:
                total_targets += expected_targets
    
    print(f"\n📊 Validation Summary:")
    print(f"   ✅ Valid files: {valid_files}/{len(dat_files)}")
    print(f"   🎯 Total targets: {total_targets}")
    
    if valid_files == len(dat_files):
        print(f"\n🎉 All patch files are valid and ready for use!")
        print(f"📋 Installation: Copy all .dat files to your SimCity 4 Plugins folder")
        print(f"🔧 Requirement: sc4-resource-loading-hooks.dll must also be in Plugins folder")
    else:
        print(f"\n⚠️  Some files failed validation. Check the issues above.")

if __name__ == "__main__":
    main()
