#!/usr/bin/env python3
"""
INTEGRATION VALIDATION SUITE
============================
True integration testing that validates the actual parsing functions
instead of duplicating logic. Tests the real code paths used in production.

This validates:
1. DBPF header parsing (actual file reading)
2. QFS decompression (actual qfs.decompress function)  
3. Property extraction (actual parse_exemplar_properties function)
4. Full pipeline (actual extract_maxis_lots function)
5. Regression tests against known good values

Usage:
    python integration_validation.py                    # Full validation
    python integration_validation.py --quick            # Essential tests only
    python integration_validation.py --function <name>  # Test specific function
    python integration_validation.py --regression       # Regression tests only
"""
import sys
import os
import time
import json
import struct
import tempfile
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    import qfs
    from extract_maxis_lots import parse_exemplar_properties, extract_maxis_lots
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Make sure qfs.py and extract_maxis_lots.py are in the same directory")
    sys.exit(1)


class IntegrationValidator:
    """Integration test suite that validates actual functions."""
    
    def __init__(self, dbpf_file: str, results_file: str):
        self.dbpf_file = Path(dbpf_file)
        self.results_file = Path(results_file)
        
        # Known good test cases for regression testing
        self.regression_tests = {
            '0x60000474': {
                'name': 'Standard commercial lot',
                'expected': {
                    'GrowthStage': 6,
                    'RoadCornerIndicator': 12,
                    'ExemplarName': 'CO$$6_3x3',
                    'ZoneTypes': [5, 6],
                    'ZoneWealth': [2]
                },
                'description': 'Commercial 3x3 with verified properties'
            },
            '0x6A63633B': {
                'name': 'PZ2x1_LifeGardtower',
                'expected': {
                    'ExemplarName': 'PZ2x1_LifeGardtower',
                    'GrowthStage': 1,
                    'RoadCornerIndicator': 8,
                    'ZoneWealth': 0
                },
                'description': 'Police station lot with single values'
            },
            '0x60004030': {
                'name': 'CS$$1_5x4 commercial',
                'expected': {
                    'ExemplarName': 'CS$$1_5x4',
                    'ZoneTypes': [5, 6],
                    'ZoneWealth': [2],
                    'LotConfigPropertySize': [5, 4]
                },
                'description': 'Commercial 5x4 with array properties'
            }
        }
        
        self.results = {}
        
    def print_header(self, title: str, char: str = "=") -> None:
        """Print formatted section header."""
        print(f"\n{char * 70}")
        print(f"  {title}")
        print(f"{char * 70}")
        
    def print_result(self, test_name: str, passed: bool, details: str = "") -> bool:
        """Print formatted test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name:<40} {status}")
        if details:
            print(f"    {details}")
        return passed

    def test_file_access(self) -> bool:
        """Test basic file access and structure."""
        self.print_header("FILE ACCESS VALIDATION")
        
        # Test DBPF file exists and readable
        if not self.dbpf_file.exists():
            return self.print_result("DBPF File Access", False, f"File not found: {self.dbpf_file}")
            
        try:
            with open(self.dbpf_file, 'rb') as f:
                # Test basic DBPF structure using actual file reading
                magic = f.read(4)
                if magic != b'DBPF':
                    return self.print_result("DBPF Magic", False, f"Invalid magic: {magic}")
                self.print_result("DBPF Magic", True, "Valid DBPF file")
                
                # Test header parsing (same logic as extract_maxis_lots)
                f.seek(36)
                index_entry_count = struct.unpack('<I', f.read(4))[0]
                index_location = struct.unpack('<I', f.read(4))[0]
                
                header_valid = index_entry_count > 0 and index_location > 0
                self.print_result("DBPF Header", header_valid, 
                                f"Entries: {index_entry_count}, Index: {index_location}")
                
                return header_valid
                
        except Exception as e:
            return self.print_result("File Access", False, f"Exception: {e}")

    def test_qfs_decompression(self) -> bool:
        """Test QFS decompression using actual qfs.decompress function."""
        self.print_header("QFS DECOMPRESSION VALIDATION")
        
        try:
            # Find actual compressed lot data from the DBPF file
            with open(self.dbpf_file, 'rb') as f:
                # Use the same parsing logic as extract_maxis_lots
                f.seek(36)
                index_entry_count = struct.unpack('<I', f.read(4))[0]
                index_location = struct.unpack('<I', f.read(4))[0]
                
                compressed_found = 0
                decompression_successes = 0
                test_limit = 50  # Test first 50 compressed entries
                
                for i in range(min(index_entry_count, 1000)):  # Check first 1000 entries
                    if compressed_found >= test_limit:
                        break
                        
                    entry_offset = index_location + i * 20
                    f.seek(entry_offset)
                    entry_data = f.read(20)
                    
                    if len(entry_data) < 20:
                        break
                        
                    tid, gid, iid, location, size = struct.unpack('<IIIII', entry_data)
                    
                    # Focus on LotConfig entries (same filter as extract_maxis_lots)
                    if tid == 0x6534284A and gid == 0xA8FBD372:
                        f.seek(location)
                        raw_data = f.read(size)
                        
                        # Test if compressed (same logic as extract_maxis_lots) 
                        if len(raw_data) >= 6 and raw_data[4:6] == b'\x10\xfb':
                            compressed_found += 1
                            
                            # Test actual qfs.decompress function
                            try:
                                decompressed = qfs.decompress(raw_data[4:])
                                if decompressed and len(decompressed) > 0:
                                    decompression_successes += 1
                            except Exception:
                                pass  # Decompression failure counted
                
                if compressed_found == 0:
                    return self.print_result("QFS Decompression", True, 
                                           "No compressed lots found (normal for Maxis data)")
                
                success_rate = decompression_successes / compressed_found if compressed_found > 0 else 0
                success = success_rate >= 0.8  # 80% success threshold
                
                return self.print_result("QFS Decompression", success,
                                       f"Rate: {success_rate:.1%} ({decompression_successes}/{compressed_found})")
                
        except Exception as e:
            return self.print_result("QFS Decompression", False, f"Exception: {e}")

    def test_property_parsing(self) -> bool:
        """Test property parsing using actual parse_exemplar_properties function."""
        self.print_header("PROPERTY PARSING VALIDATION")
        
        try:
            # Extract sample lot data using the same logic as extract_maxis_lots
            with open(self.dbpf_file, 'rb') as f:
                f.seek(36)
                index_entry_count = struct.unpack('<I', f.read(4))[0]
                index_location = struct.unpack('<I', f.read(4))[0]
                
                test_lots = []
                parsing_successes = 0
                property_successes = 0
                
                for i in range(min(index_entry_count, 500)):  # Test first 500 entries
                    if len(test_lots) >= 10:  # Test 10 lots
                        break
                        
                    entry_offset = index_location + i * 20
                    f.seek(entry_offset)
                    entry_data = f.read(20)
                    
                    if len(entry_data) < 20:
                        break
                        
                    tid, gid, iid, location, size = struct.unpack('<IIIII', entry_data)
                    
                    # Same filter as extract_maxis_lots
                    if tid == 0x6534284A and gid == 0xA8FBD372:
                        try:
                            f.seek(location)
                            raw_data = f.read(size)
                            
                            # Same decompression logic as extract_maxis_lots
                            if len(raw_data) >= 6 and raw_data[4:6] == b'\x10\xfb':
                                eqzb_data = qfs.decompress(raw_data[4:])
                            else:
                                eqzb_data = raw_data
                            
                            # Test actual parse_exemplar_properties function
                            properties = parse_exemplar_properties(eqzb_data)
                            
                            if isinstance(properties, dict):
                                parsing_successes += 1
                                
                                # Check if we found any meaningful properties
                                if any(prop in properties for prop in ['ExemplarName', 'ZoneTypes', 'GrowthStage']):
                                    property_successes += 1
                                    
                            test_lots.append({
                                'iid': f"0x{iid:08X}",
                                'properties': properties
                            })
                            
                        except Exception:
                            test_lots.append({
                                'iid': f"0x{iid:08X}",
                                'properties': {}
                            })
                
                if not test_lots:
                    return self.print_result("Property Parsing", False, "No test lots found")
                
                parse_rate = parsing_successes / len(test_lots)
                prop_rate = property_successes / len(test_lots)
                
                parse_success = parse_rate >= 0.8
                prop_success = prop_rate >= 0.5
                
                self.print_result("Parse Function Success", parse_success,
                                f"Rate: {parse_rate:.1%} ({parsing_successes}/{len(test_lots)})")
                self.print_result("Property Detection", prop_success,
                                f"Rate: {prop_rate:.1%} ({property_successes}/{len(test_lots)})")
                
                return parse_success and prop_success
                
        except Exception as e:
            return self.print_result("Property Parsing", False, f"Exception: {e}")

    def test_full_pipeline(self) -> bool:
        """Test the complete extraction pipeline using actual extract_maxis_lots function."""
        self.print_header("FULL PIPELINE VALIDATION")
        
        try:
            # Create temporary output file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                temp_output = Path(temp_file.name)
            
            try:
                # Test actual extract_maxis_lots function
                start_time = time.time()
                lot_configurations = extract_maxis_lots(self.dbpf_file, temp_output)
                end_time = time.time()
                
                extraction_time = end_time - start_time
                
                # Validate results
                if not isinstance(lot_configurations, list):
                    return self.print_result("Pipeline Execution", False, "Invalid return type")
                
                if len(lot_configurations) < 1000:  # Expect at least 1000 lots from Maxis data
                    return self.print_result("Pipeline Results", False, 
                                           f"Too few lots: {len(lot_configurations)}")
                
                # Check output file was created correctly
                if not temp_output.exists():
                    return self.print_result("Output Generation", False, "Output file not created")
                
                with open(temp_output, 'r') as f:
                    output_data = json.load(f)
                
                metadata_valid = 'metadata' in output_data and 'lot_configurations' in output_data
                
                self.print_result("Pipeline Execution", True, 
                                f"Processed {len(lot_configurations)} lots in {extraction_time:.2f}s")
                self.print_result("Output Generation", metadata_valid, 
                                f"Created valid JSON with metadata")
                
                # Performance validation
                performance_ok = extraction_time < 60.0  # Should complete within 1 minute
                self.print_result("Performance", performance_ok,
                                f"Extraction time: {extraction_time:.2f}s")
                
                return metadata_valid and performance_ok
                
            finally:
                # Clean up temporary file
                if temp_output.exists():
                    temp_output.unlink()
                
        except Exception as e:
            return self.print_result("Full Pipeline", False, f"Exception: {e}")

    def test_regression_cases(self) -> bool:
        """Test known good cases using actual parsing results."""
        self.print_header("REGRESSION TESTING")
        
        try:
            # Load actual results from the real extraction
            if not self.results_file.exists():
                return self.print_result("Results File", False, f"Missing: {self.results_file}")
            
            with open(self.results_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            lots = {lot['iid']: lot for lot in data.get('lot_configurations', [])}
            
            all_passed = True
            
            for test_iid, test_case in self.regression_tests.items():
                if test_iid in lots:
                    lot = lots[test_iid]
                    properties = lot.get('properties', {})
                    
                    test_passed = True
                    failures = []
                    
                    for prop_name, expected_value in test_case['expected'].items():
                        actual_value = properties.get(prop_name)
                        
                        if actual_value != expected_value:
                            test_passed = False
                            failures.append(f"{prop_name}: got {actual_value}, expected {expected_value}")
                    
                    detail_text = test_case['description']
                    if failures:
                        detail_text += f" | Failures: {'; '.join(failures)}"
                    
                    self.print_result(f"Regression {test_iid}", test_passed, detail_text)
                    
                    if not test_passed:
                        all_passed = False
                else:
                    self.print_result(f"Regression {test_iid}", False, "Lot not found in results")
                    all_passed = False
            
            return all_passed
            
        except Exception as e:
            return self.print_result("Regression Testing", False, f"Exception: {e}")

    def test_specific_function(self, function_name: str) -> bool:
        """Test a specific function."""
        function_tests = {
            'file_access': self.test_file_access,
            'qfs_decompression': self.test_qfs_decompression,
            'property_parsing': self.test_property_parsing,
            'full_pipeline': self.test_full_pipeline,
            'regression': self.test_regression_cases
        }
        
        if function_name not in function_tests:
            print(f"Unknown function: {function_name}")
            print(f"Available functions: {', '.join(function_tests.keys())}")
            return False
        
        return function_tests[function_name]()

    def run_validation(self, args) -> bool:
        """Run validation based on arguments."""
        start_time = time.time()
        
        print("INTEGRATION VALIDATION SUITE")
        print("=" * 70)
        print("Testing actual functions from production code")
        print(f"DBPF File: {self.dbpf_file}")
        print(f"Results File: {self.results_file}")
        
        all_passed = True
        
        # Run specific function test
        if args.function:
            return self.test_specific_function(args.function)
        
        # Run regression tests only
        if args.regression:
            return self.test_regression_cases()
        
        # Run test suite
        tests_to_run = [
            ('file_access', self.test_file_access),
            ('qfs_decompression', self.test_qfs_decompression),
            ('property_parsing', self.test_property_parsing)
        ]
        
        if not args.quick:
            tests_to_run.extend([
                ('full_pipeline', self.test_full_pipeline),
                ('regression', self.test_regression_cases)
            ])
        
        for test_name, test_func in tests_to_run:
            if not test_func():
                all_passed = False
        
        # Summary
        elapsed = time.time() - start_time
        self.print_header("INTEGRATION TEST SUMMARY")
        
        status = "🎉 ALL TESTS PASSED" if all_passed else "❌ TEST FAILURES DETECTED"
        message = ("Production code is working correctly" if all_passed else
                  "Review failures and fix issues in production code")
        
        print(f"{status}")
        print(f"   {message}")
        print(f"   Integration testing completed in {elapsed:.2f}s")
        
        return all_passed


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Integration Validation Suite for DBPF Parser",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python integration_validation.py                      # Full test suite
  python integration_validation.py --quick              # Essential tests only
  python integration_validation.py --function qfs       # Test QFS decompression only
  python integration_validation.py --regression         # Regression tests only
        """
    )
    
    parser.add_argument('--dbpf-file',
                       default='../data/SimCity_1.dat',
                       help='Path to DBPF file (default: ../data/SimCity_1.dat)')
    parser.add_argument('--results-file',
                       default='../data/lot_configurations.json',
                       help='Path to results file (default: ../data/lot_configurations.json)')
    parser.add_argument('--quick', action='store_true',
                       help='Run essential tests only')
    parser.add_argument('--function',
                       choices=['file_access', 'qfs_decompression', 'property_parsing', 'full_pipeline', 'regression'],
                       help='Test specific function only')
    parser.add_argument('--regression', action='store_true',
                       help='Run regression tests only')
    
    args = parser.parse_args()
    
    # Create validator
    validator = IntegrationValidator(
        dbpf_file=args.dbpf_file,
        results_file=args.results_file
    )
    
    # Run validation
    success = validator.run_validation(args)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
