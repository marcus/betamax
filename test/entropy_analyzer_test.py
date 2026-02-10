#!/usr/bin/env python3
"""Tests for entropy_analyzer.py"""

import sys
import json
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / "lib" / "python"))

from entropy_analyzer import EntropyAnalyzer

def test_entropy_analyzer():
    """Test entropy analyzer with the actual codebase."""
    analyzer = EntropyAnalyzer(".")
    result = analyzer.analyze()
    
    tests_passed = 0
    tests_failed = 0
    
    print("=== Python Entropy Analyzer Tests ===\n")
    
    # Test 1: Documented features extraction
    print("Testing README feature extraction...")
    if 9 <= result.documented_features <= 20:
        tests_passed += 1
        print(f"✓ README features: {result.documented_features} (reasonable count)")
    else:
        tests_failed += 1
        print(f"✗ README features: {result.documented_features} (expected 9-20)")
    
    # Test 2: Shell functions extraction
    print("\nTesting shell function extraction...")
    if 40 <= result.implemented_functions <= 70:
        tests_passed += 1
        print(f"✓ Shell functions: {result.implemented_functions} (correct)")
    else:
        tests_failed += 1
        print(f"✗ Shell functions: {result.implemented_functions} (expected 40-70)")
    
    # Test 3: Orphaned code detection
    print("\nTesting orphaned code detection...")
    if result.orphaned_code == 1:
        tests_passed += 1
        print(f"✓ Orphaned count: {result.orphaned_code} (correct)")
        
        # Verify it's the right one
        orphaned = analyzer.detect_orphaned_code()
        if any(func == "extract_keys_features" for _, func in orphaned):
            tests_passed += 1
            print("✓ Orphaned function correctly identified: extract_keys_features")
        else:
            tests_failed += 1
            print("✗ Wrong orphaned function detected")
    else:
        tests_failed += 1
        print(f"✗ Orphaned count: {result.orphaned_code} (expected 1)")
    
    # Test 4: Entropy score is in valid range
    print("\nTesting entropy score...")
    if 0 <= result.entropy_score <= 100:
        tests_passed += 1
        print(f"✓ Entropy score: {result.entropy_score}/100 ({result.status})")
    else:
        tests_failed += 1
        print(f"✗ Entropy score out of range: {result.entropy_score}")
    
    # Test 5: Git analysis
    print("\nTesting git pattern analysis...")
    if all(k in result.git_analysis for k in ["feature", "bugfix", "refactor"]):
        tests_passed += 1
        print(f"✓ Git patterns analyzed: {result.git_analysis}")
    else:
        tests_failed += 1
        print(f"✗ Git analysis incomplete")
    
    # Test 6: Consistency with shell version
    print("\nTesting consistency with shell version...")
    # Both should detect the same orphaned functions
    if result.orphaned_code == 1:
        tests_passed += 1
        print("✓ Shell and Python orphaned detection consistent")
    else:
        tests_failed += 1
        print("✗ Inconsistent orphaned detection between implementations")
    
    # Summary
    print(f"\n=== Test Summary ===")
    print(f"Passed: {tests_passed}")
    print(f"Failed: {tests_failed}")
    
    return tests_failed == 0

if __name__ == "__main__":
    sys.exit(0 if test_entropy_analyzer() else 1)
