#!/usr/bin/env python3
"""
Regression Prevention Test Suite
Run this before making any changes to ensure no validated layers break.
"""

import sys
import subprocess
import os

def run_test(script_name, description):
    """Run a validation script and return result."""
    print(f"\nTesting: {description}")
    print(f"   Script: {script_name}")
    
    try:
        result = subprocess.run([
            sys.executable, script_name, "../../data/SimCity_1.dat"
        ], capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__)))
        
        if result.returncode == 0:
            print(f"   PASSED")
            return True
        else:
            print(f"   FAILED (exit code {result.returncode})")
            if result.stderr:
                print(f"   Error: {result.stderr.strip()}")
            return False
            
    except Exception as e:
        print(f"   FAILED (exception: {e})")
        return False

def main():
    print("REGRESSION PREVENTION TEST SUITE")
    print("="*50)
    
    tests = [
        ("validate_phase1.py", "Layer 1: DBPF File Structure + LotConfiguration Filtering"),
        ("validate_phase2.py", "Layer 2: EQZB Container Parsing + Property Location"),
        ("validate_phase3.py", "Layer 3: Enhanced Parser with New Properties"),
        # Add more validation scripts as they are created
    ]
    
    results = []
    
    for script, description in tests:
        if os.path.exists(script):
            passed = run_test(script, description)
            results.append((description, passed))
        else:
            print(f"\nSkipping: {description}")
            print(f"   Script not found: {script}")
            results.append((description, None))
    
    print(f"\nREGRESSION TEST SUMMARY")
    print("="*50)
    
    passed_count = 0
    failed_count = 0
    skipped_count = 0
    
    for description, result in results:
        if result is True:
            print(f"V {description}")
            passed_count += 1
        elif result is False:
            print(f"X {description}")
            failed_count += 1
        else:
            print(f"{description} (SKIPPED)")
            skipped_count += 1
    
    print(f"\nResults: {passed_count} passed, {failed_count} failed, {skipped_count} skipped")
    
    if failed_count > 0:
        print(f"\nREGRESSION DETECTED! {failed_count} layer(s) broken.")
        print("   Do not proceed with changes until all layers pass.")
        return 1
    elif passed_count > 0:
        print(f"\nAll validated layers are working correctly!")
        print("   Safe to proceed with development.")
        return 0
    else:
        print(f"\nNo validated layers found. Run validation scripts first.")
        return 0

if __name__ == '__main__':
    sys.exit(main())
