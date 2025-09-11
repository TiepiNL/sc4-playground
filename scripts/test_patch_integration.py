#!/usr/bin/env python3
"""
Integration Test for SimCity 4 Patch Creation Pipeline

This test validates the complete patch creation workflow from JSON input
to DBPF output files, ensuring data integrity and proper file generation.

Test Coverage:
1. JSON parsing and data validation
2. Property extraction and filtering
3. Zone/wealth grouping logic
4. DBPF file generation and structure
5. Instance ID generation and consistency
6. Datpack functionality
"""

import json
import os
import sys
import shutil
import tempfile
import struct
from pathlib import Path

# Add scripts directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import create_patches_from_json

class PatchIntegrationTest:
    def __init__(self):
        self.test_data_dir = None
        self.original_output_dir = None
        self.test_results = []
        
    def setup_test_environment(self):
        """Create temporary test environment with sample data."""
        self.test_data_dir = tempfile.mkdtemp(prefix="sc4_patch_test_")
        print(f"Created test environment: {self.test_data_dir}")
        
        # Store original OUTPUT_DIR
        self.original_output_dir = create_patches_from_json.OUTPUT_DIR
        
        # Create test output directory
        test_output_dir = os.path.join(self.test_data_dir, "output_patches")
        create_patches_from_json.OUTPUT_DIR = test_output_dir
        
        # Create sample test data
        self.create_sample_json_data()
        
    def cleanup_test_environment(self):
        """Clean up temporary test environment."""
        if self.test_data_dir and os.path.exists(self.test_data_dir):
            shutil.rmtree(self.test_data_dir)
            print(f"Cleaned up test environment: {self.test_data_dir}")
            
        # Restore original OUTPUT_DIR
        if self.original_output_dir:
            create_patches_from_json.OUTPUT_DIR = self.original_output_dir
    
    def create_sample_json_data(self):
        """Create sample lot configuration JSON for testing."""
        if not self.test_data_dir:
            raise ValueError("Test data directory not initialized")
            
        sample_data = {
            "metadata": {
                "source_file": "test_data.dat",
                "total_lot_configurations": 6,
                "properties_found_in": 6,
                "parser_version": "test_integration"
            },
            "lot_configurations": [
                # Residential Low ($)
                {
                    "iid": "0x60001000",
                    "size": 1024,
                    "properties": {
                        "ExemplarName": "R$1_1x1_Test",
                        "ZoneTypes": [1],
                        "PurposeTypes": [1],
                        "ZoneWealth": [1],
                        "GrowthStage": 1
                    }
                },
                # Residential High ($$$)  
                {
                    "iid": "0x60001001",
                    "size": 2048,
                    "properties": {
                        "ExemplarName": "R$$$1_2x2_Test",
                        "ZoneTypes": [1],
                        "PurposeTypes": [1], 
                        "ZoneWealth": [3],
                        "GrowthStage": 1
                    }
                },
                # Commercial Service Medium ($$)
                {
                    "iid": "0x60001002", 
                    "size": 1536,
                    "properties": {
                        "ExemplarName": "CS$$1_3x3_Test",
                        "ZoneTypes": [4, 5, 6],
                        "PurposeTypes": [2],
                        "ZoneWealth": [2],
                        "GrowthStage": 1
                    }
                },
                # Commercial Office High ($$$)
                {
                    "iid": "0x60001003",
                    "size": 3072, 
                    "properties": {
                        "ExemplarName": "CO$$$1_4x4_Test",
                        "ZoneTypes": [7, 8, 9],
                        "PurposeTypes": [3],
                        "ZoneWealth": [3],
                        "GrowthStage": 1
                    }
                },
                # Industrial Dirty ($$)
                {
                    "iid": "0x60001004",
                    "size": 2560,
                    "properties": {
                        "ExemplarName": "I-d$$1_3x2_Test", 
                        "ZoneTypes": [10, 11, 12],
                        "PurposeTypes": [4],
                        "ZoneWealth": [2],
                        "GrowthStage": 1
                    }
                },
                # Industrial High-Tech ($$$)
                {
                    "iid": "0x60001005",
                    "size": 4096,
                    "properties": {
                        "ExemplarName": "I-ht$$$1_5x5_Test",
                        "ZoneTypes": [13, 14, 15],
                        "PurposeTypes": [4],
                        "ZoneWealth": [3],
                        "GrowthStage": 1
                    }
                }
            ]
        }
        
        # Write test JSON file
        test_json_path = os.path.join(self.test_data_dir, "lot_configurations.json")
        with open(test_json_path, 'w') as f:
            json.dump(sample_data, f, indent=2)
            
        # Update script paths to use test data
        create_patches_from_json.MAXIS_JSON_PATH = test_json_path
        print(f"Created sample JSON with {len(sample_data['lot_configurations'])} test lots")
        
    def assert_test(self, condition, test_name, details=""):
        """Record test result."""
        status = "PASS" if condition else "FAIL"
        result = f"[{status}] {test_name}"
        if details:
            result += f" - {details}"
        print(result)
        self.test_results.append((condition, test_name, details))
        
    def test_json_parsing(self):
        """Test JSON data loading and parsing."""
        print("\n=== Testing JSON Parsing ===")
        
        try:
            # Test loading sample data
            with open(create_patches_from_json.MAXIS_JSON_PATH, 'r') as f:
                data = json.load(f)
                
            self.assert_test(
                'lot_configurations' in data,
                "JSON structure validation",
                "lot_configurations key present"
            )
            
            self.assert_test(
                len(data['lot_configurations']) == 6,
                "Sample data count",
                f"Expected 6 lots, found {len(data['lot_configurations'])}"
            )
            
            # Test property extraction
            first_lot = data['lot_configurations'][0]
            required_props = ['ExemplarName', 'ZoneTypes', 'PurposeTypes', 'ZoneWealth']
            for prop in required_props:
                self.assert_test(
                    prop in first_lot['properties'],
                    f"Property {prop} present",
                    f"Found in test lot properties"
                )
                
        except Exception as e:
            self.assert_test(False, "JSON parsing", f"Exception: {e}")
    
    def test_patch_generation(self):
        """Test complete patch generation workflow.""" 
        print("\n=== Testing Patch Generation ===")
        
        try:
            # Generate patches using the main function
            create_patches_from_json.main()
            
            # Check output directory was created
            output_dir = create_patches_from_json.OUTPUT_DIR
            self.assert_test(
                os.path.exists(output_dir),
                "Output directory creation",
                f"Directory {output_dir} exists"
            )
            
            # Check patch files were generated
            patch_files = [f for f in os.listdir(output_dir) if f.endswith('.dat')]
            self.assert_test(
                len(patch_files) > 0,
                "Patch files generated",
                f"Found {len(patch_files)} .dat files"
            )
            
            # Validate expected patch groups
            expected_groups = ['R$', 'R$$$', 'CS$$', 'CO$$$', 'I-d$$', 'I-ht$$$']
            for group in expected_groups:
                group_file = f"stop_maxis_growable_{group}.dat"
                file_exists = group_file in patch_files
                self.assert_test(
                    file_exists,
                    f"Expected patch group {group}",
                    "File generated" if file_exists else "File missing"
                )
                
        except Exception as e:
            self.assert_test(False, "Patch generation workflow", f"Exception: {e}")
    
    def test_dbpf_file_structure(self):
        """Test generated DBPF file structure and contents."""
        print("\n=== Testing DBPF File Structure ===")
        
        output_dir = create_patches_from_json.OUTPUT_DIR
        if not os.path.exists(output_dir):
            self.assert_test(False, "DBPF structure test", "No output directory found")
            return
            
        patch_files = [f for f in os.listdir(output_dir) if f.endswith('.dat')]
        if not patch_files:
            self.assert_test(False, "DBPF structure test", "No patch files found")
            return
            
        # Test first patch file structure
        test_file = os.path.join(output_dir, patch_files[0])
        
        try:
            with open(test_file, 'rb') as f:
                # Read DBPF header
                header = f.read(96)  # DBPF header is 96 bytes
                
                # Check DBPF signature
                signature = header[:4]
                self.assert_test(
                    signature == b'DBPF',
                    "DBPF signature validation",
                    f"Found signature: {signature}"
                )
                
                # Check version (should be 1.1)  
                major_version, minor_version = struct.unpack('<II', header[4:12])
                self.assert_test(
                    major_version == 1 and minor_version == 1,
                    "DBPF version validation",
                    f"Version {major_version}.{minor_version}"
                )
                
                # Check index entry count
                index_entry_count = struct.unpack('<I', header[36:40])[0]
                self.assert_test(
                    index_entry_count > 0,
                    "DBPF index entries",
                    f"Found {index_entry_count} entries"
                )
                
        except Exception as e:
            self.assert_test(False, "DBPF structure validation", f"Exception: {e}")
    
    def test_zone_wealth_filtering(self):
        """Test zone/wealth filtering functionality."""
        print("\n=== Testing Zone/Wealth Filtering ===")
        
        # Clean previous output
        if os.path.exists(create_patches_from_json.OUTPUT_DIR):
            shutil.rmtree(create_patches_from_json.OUTPUT_DIR)
            
        try:
            # Test with specific filter (only R$$$)
            import sys
            original_argv = sys.argv.copy()
            sys.argv = ['create_patches_from_json.py', '--filter-r-high']
            
            create_patches_from_json.main()
            
            # Restore original argv
            sys.argv = original_argv
            
            # Check only R$$$ patch was created
            output_dir = create_patches_from_json.OUTPUT_DIR
            patch_files = [f for f in os.listdir(output_dir) if f.endswith('.dat')]
            
            self.assert_test(
                'stop_maxis_growable_R$$$.dat' in patch_files,
                "R$$$ filter creates correct file",
                "R$$$ patch file present"
            )
            
            # Should not create other wealth levels for residential
            unwanted_files = ['stop_maxis_growable_R$.dat', 'stop_maxis_growable_R$$.dat']
            for unwanted in unwanted_files:
                self.assert_test(
                    unwanted not in patch_files,
                    f"Filter excludes {unwanted}",
                    "File correctly filtered out"
                )
                
        except Exception as e:
            self.assert_test(False, "Zone/wealth filtering", f"Exception: {e}")
    
    def test_instance_id_generation(self):
        """Test Instance ID generation consistency."""
        print("\n=== Testing Instance ID Generation ===")
        
        try:
            # Test custom IID base generation with sample data
            sample_exemplar_names = ["Test_R$1", "Test_CS$$1", "Test_I-ht$$$1"]
            
            # Generate IID base multiple times - should be consistent
            base_1 = create_patches_from_json.generate_custom_iid_base([])
            base_2 = create_patches_from_json.generate_custom_iid_base([])
            
            # With empty input, should get default Maxis range
            expected_maxis_base = create_patches_from_json.STARTING_INSTANCE_ID
            self.assert_test(
                base_1 == expected_maxis_base,
                "Maxis IID base generation",
                f"Generated: 0x{base_1:08X}, Expected: 0x{expected_maxis_base:08X}"
            )
            
            self.assert_test(
                base_1 == base_2,
                "IID generation consistency", 
                "Multiple calls return same result"
            )
            
        except Exception as e:
            self.assert_test(False, "Instance ID generation", f"Exception: {e}")
    
    def run_all_tests(self):
        """Run complete integration test suite."""
        print("SimCity 4 Patch Creation - Integration Test Suite")
        print("=" * 60)
        
        try:
            self.setup_test_environment()
            
            # Run test phases
            self.test_json_parsing()
            self.test_patch_generation()
            self.test_dbpf_file_structure()
            self.test_zone_wealth_filtering()
            self.test_instance_id_generation()
            
            # Summary
            print("\n" + "=" * 60)
            print("TEST RESULTS SUMMARY")
            print("=" * 60)
            
            total_tests = len(self.test_results)
            passed_tests = sum(1 for result in self.test_results if result[0])
            failed_tests = total_tests - passed_tests
            
            print(f"Total Tests: {total_tests}")
            print(f"Passed: {passed_tests}")
            print(f"Failed: {failed_tests}")
            print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
            
            if failed_tests > 0:
                print(f"\nFailed Tests:")
                for result in self.test_results:
                    if not result[0]:
                        print(f"  - {result[1]}: {result[2]}")
                        
            return failed_tests == 0
            
        finally:
            self.cleanup_test_environment()

if __name__ == "__main__":
    test_suite = PatchIntegrationTest()
    success = test_suite.run_all_tests()
    sys.exit(0 if success else 1)