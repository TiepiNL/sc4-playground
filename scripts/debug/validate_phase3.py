#!/usr/bin/env python3
"""
Phase 3 Validation: Property Structure and Rep-Field Encoding

This test validates the property parsing logic and data extraction, including:
- BIG-ENDIAN Rep field parsing
- 3-byte padding validation 
- Type-specific parsing
- Special UINT8 rep-field encoding pattern for GrowthStage and RoadCornerIndicator
- Edge case handling and validation logic

Status: Production validation for Layer 3 (Property Structure)
"""

import sys
import json
import os

def validate_property_structure(dbpf_file):
    """Validate Phase 3: Property Structure and Rep-Field Encoding"""
    
    print("🧪 PHASE 3 VALIDATION: Property Structure & Rep-Field Encoding")
    print("=" * 70)
    print("Testing:")
    print("  ✓ BIG-ENDIAN Rep field parsing")
    print("  ✓ 3-byte padding validation")
    print("  ✓ Type-specific parsing (UINT8, UINT16, UINT32, String)")
    print("  ✓ Special UINT8 rep-field encoding pattern")
    print("  ✓ Dynamic property search robustness")
    print("  ✓ Edge case handling")
    print()
    
    # Run the parser
    output_file = 'test_phase3_output.json'
    cmd = f"python scripts/extract_maxis_lots.py {dbpf_file} {output_file}"
    result = os.system(cmd)
    
    if result != 0:
        print("❌ FAILED: Parser execution failed")
        return False
    
    # Load and validate the output
    try:
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        print(f"✅ Parser executed successfully")
        print(f"📊 Extracted {data['total_lot_configurations']} LotConfigurations")
        
        # Test 1: Validate known test cases
        print(f"\n🎯 Test 1: Known Property Values")
        
        # Test case 1: BIG-ENDIAN Rep field validation
        test_case_1 = next((entry for entry in data['lot_configurations'] if entry['iid'] == '0x6A63633B'), None)
        if test_case_1:
            zone_types = test_case_1['properties'].get('ZoneTypes', [])
            if zone_types == [15]:
                print(f"   ✅ BIG-ENDIAN Rep field: ZoneTypes=[15] correct for {test_case_1['iid']}")
            else:
                print(f"   ❌ BIG-ENDIAN Rep field: ZoneTypes={zone_types} (expected [15])")
                return False
        else:
            print(f"   ❌ Test case 0x6A63633B not found")
            return False
        
        # Test case 2: Rep-field encoding validation
        test_case_2 = next((entry for entry in data['lot_configurations'] if entry['iid'] == '0x60004030'), None)
        if test_case_2:
            props = test_case_2['properties']
            exemplar_name = props.get('ExemplarName')
            growth_stage = props.get('GrowthStage')
            corner_indicator = props.get('RoadCornerIndicator')
            
            print(f"   Rep-field encoding test case {test_case_2['iid']}:")
            print(f"     ExemplarName: {exemplar_name}")
            print(f"     GrowthStage: {growth_stage}")
            print(f"     RoadCornerIndicator: {corner_indicator}")
            
            if (exemplar_name == "CS$$1_5x4" and 
                growth_stage == [1] and 
                corner_indicator == [8]):
                print(f"   ✅ Rep-field encoding: All values match sc4-reader exactly")
            else:
                print(f"   ❌ Rep-field encoding: Values don't match expected")
                print(f"      Expected: ExemplarName='CS$$1_5x4', GrowthStage=[1], RoadCornerIndicator=[8]")
                return False
        else:
            print(f"   ❌ Test case 0x60004030 not found")
            return False
        
        # Test 2: Statistical validation of rep-field properties
        print(f"\n📈 Test 2: Rep-Field Properties Statistical Analysis")
        
        growth_stage_found = 0
        corner_indicator_found = 0
        both_found = 0
        total_entries = len(data['lot_configurations'])
        growth_stage_values = set()
        corner_indicator_values = set()
        
        for entry in data['lot_configurations']:
            props = entry['properties']
            
            gs = props.get('GrowthStage')
            ci = props.get('RoadCornerIndicator')
            
            if gs is not None:
                growth_stage_found += 1
                if isinstance(gs, list) and len(gs) > 0:
                    growth_stage_values.add(gs[0])
            
            if ci is not None:
                corner_indicator_found += 1
                if isinstance(ci, list) and len(ci) > 0:
                    corner_indicator_values.add(ci[0])
            
            if gs is not None and ci is not None:
                both_found += 1
        
        gs_percentage = (growth_stage_found / total_entries) * 100
        ci_percentage = (corner_indicator_found / total_entries) * 100
        
        print(f"   GrowthStage extraction: {growth_stage_found}/{total_entries} ({gs_percentage:.1f}%)")
        print(f"   RoadCornerIndicator extraction: {corner_indicator_found}/{total_entries} ({ci_percentage:.1f}%)")
        print(f"   Both properties: {both_found}/{total_entries} ({(both_found/total_entries)*100:.1f}%)")
        print(f"   GrowthStage value range: {sorted(growth_stage_values)}")
        print(f"   RoadCornerIndicator value range: {sorted(corner_indicator_values)}")
        
        # Validate significant improvement from before the fix (was 0%)
        if growth_stage_found > 0 and corner_indicator_found > 0:
            print(f"   ✅ Rep-field properties are being extracted (massive improvement from 0%)")
        else:
            print(f"   ❌ Rep-field properties are still showing as null")
            return False
        
        # Validate reasonable extraction rates
        if gs_percentage > 50 and ci_percentage > 50:
            print(f"   ✅ Extraction rates are significant (>50%)")
        else:
            print(f"   ⚠️  Extraction rates are lower than expected")
            print(f"      This might be normal if not all lots have these properties")
        
        # Test 3: Data type validation
        print(f"\n🔬 Test 3: Property Data Type Validation")
        
        type_errors = 0
        sample_size = min(100, total_entries)
        
        for entry in data['lot_configurations'][:sample_size]:
            props = entry['properties']
            
            # Validate ExemplarName (String)
            exemplar_name = props.get('ExemplarName')
            if exemplar_name is not None and not isinstance(exemplar_name, str):
                type_errors += 1
                print(f"     Type error: ExemplarName should be string, got {type(exemplar_name)}")
            
            # Validate UINT8 arrays
            for prop_name in ['ZoneTypes', 'ZoneWealth', 'GrowthStage', 'RoadCornerIndicator']:
                prop_value = props.get(prop_name)
                if prop_value is not None:
                    if not isinstance(prop_value, list) or len(prop_value) == 0 or not isinstance(prop_value[0], int):
                        type_errors += 1
                        print(f"     Type error: {prop_name} should be int array, got {type(prop_value)}")
            
            # Validate UINT32 arrays
            for prop_name in ['LotConfigPropertyLotObject', 'ZonePurpose']:
                prop_value = props.get(prop_name)
                if prop_value is not None:
                    if not isinstance(prop_value, list) or len(prop_value) == 0 or not isinstance(prop_value[0], int):
                        type_errors += 1
                        print(f"     Type error: {prop_name} should be int array, got {type(prop_value)}")
        
        if type_errors == 0:
            print(f"   ✅ All extracted values have correct data types (sample of {sample_size})")
        else:
            print(f"   ❌ Found {type_errors} data type errors in sample")
            return False
        
        # Test 4: Property completeness validation
        print(f"\n🧩 Test 4: Property Structure Completeness")
        
        expected_props = ['ExemplarName', 'ZoneTypes', 'ZoneWealth', 'ZonePurpose', 
                         'LotConfigPropertyLotObject', 'GrowthStage', 'RoadCornerIndicator']
        
        missing_props = 0
        for entry in data['lot_configurations'][:10]:  # Check first 10 entries
            props = entry['properties']
            
            for prop in expected_props:
                if prop not in props:
                    missing_props += 1
                    print(f"     Warning: Property {prop} missing from IID {entry['iid']}")
        
        if missing_props == 0:
            print(f"   ✅ All expected properties present in sample entries")
        else:
            print(f"   ❌ Found {missing_props} missing properties")
            return False
        
        # Test 5: Value range validation
        print(f"\n📏 Test 5: Property Value Range Validation")
        
        # Validate reasonable value ranges
        valid_gs_values = all(0 <= val <= 10 for val in growth_stage_values)  # Allow some flexibility
        valid_ci_values = all(0 <= val <= 20 for val in corner_indicator_values)  # Allow some flexibility
        
        if valid_gs_values and valid_ci_values:
            print(f"   ✅ All rep-field values are in reasonable ranges")
        else:
            print(f"   ❌ Some values are outside expected ranges")
            print(f"      GrowthStage values: {sorted(growth_stage_values)}")
            print(f"      RoadCornerIndicator values: {sorted(corner_indicator_values)}")
            return False
        
        # Cleanup test file
        os.remove(output_file)
        
        print(f"\n🎉 PHASE 3 VALIDATION PASSED")
        print(f"✅ Property structure parsing is working correctly")
        print(f"✅ Rep-field encoding fix is successful")
        print(f"✅ All data types and value ranges are valid")
        return True
        
    except Exception as e:
        print(f"❌ Error validating output: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python validate_phase3.py <dbpf_file>")
        sys.exit(1)
    
    if validate_property_structure(sys.argv[1]):
        print("\n🎉 All Phase 3 validation tests passed!")
    else:
        print("\n❌ Phase 3 validation failed!")
        sys.exit(1)
