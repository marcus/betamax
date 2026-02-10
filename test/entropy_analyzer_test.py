#!/usr/bin/env python3
"""Tests for entropy_analyzer.py"""

import json
import sys
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / "lib" / "python"))

from entropy_analyzer import EntropyAnalyzer


def test_entropy_analyzer():
    """Test entropy analyzer functionality."""
    repo_dir = Path(__file__).parent.parent
    analyzer = EntropyAnalyzer(str(repo_dir))

    print("=== Testing Entropy Analyzer ===\n")

    # Test 1: Extract README features
    print("Test 1: Extract README features")
    features = analyzer.extract_readme_features()
    print(f"  Found {len(features)} features in README")
    assert len(features) > 5, "Should find features in README"
    print("  ✓ PASSED\n")

    # Test 2: Extract shell functions
    print("Test 2: Extract shell functions")
    shell_funcs = analyzer.extract_shell_functions()
    print(f"  Found {len(shell_funcs)} shell functions")
    assert len(shell_funcs) > 5, "Should find shell functions"
    print("  ✓ PASSED\n")

    # Test 3: Extract Python functions
    print("Test 3: Extract Python functions")
    py_funcs = analyzer.extract_python_functions()
    print(f"  Found {len(py_funcs)} Python functions")
    assert len(py_funcs) > 0, "Should find Python functions"
    print("  ✓ PASSED\n")

    # Test 4: Extract bin scripts
    print("Test 4: Extract bin scripts")
    scripts = analyzer.extract_bin_scripts()
    print(f"  Found {len(scripts)} bin scripts")
    assert len(scripts) > 0, "Should find bin scripts"
    print("  ✓ PASSED\n")

    # Test 5: Detect orphaned code
    print("Test 5: Detect orphaned code")
    orphaned = analyzer.detect_orphaned_code()
    print(f"  Found {len(orphaned)} orphaned items")
    assert isinstance(orphaned, list), "Should return list"
    print("  ✓ PASSED\n")

    # Test 6: Analyze git patterns
    print("Test 6: Analyze git patterns")
    patterns = analyzer.analyze_git_patterns()
    print(f"  Features: {patterns['feature']}")
    print(f"  Bugfixes: {patterns['bugfix']}")
    assert isinstance(patterns, dict), "Should return dict"
    print("  ✓ PASSED\n")

    # Test 7: Detect scope creep
    print("Test 7: Detect scope creep")
    creep = analyzer.detect_scope_creep()
    print(f"  Found {len(creep)} scope creep items")
    assert isinstance(creep, list), "Should return list"
    print("  ✓ PASSED\n")

    # Test 8: Detect unimplemented features
    print("Test 8: Detect unimplemented features")
    unimpl = analyzer.detect_unimplemented_features()
    print(f"  Found {len(unimpl)} unimplemented features")
    assert isinstance(unimpl, list), "Should return list"
    print("  ✓ PASSED\n")

    # Test 9: Compute entropy score
    print("Test 9: Compute entropy score")
    score = analyzer.compute_entropy_score()
    print(f"  Entropy score: {score}/100")
    assert 0 <= score <= 100, "Score should be 0-100"
    print("  ✓ PASSED\n")

    # Test 10: Full analysis
    print("Test 10: Full analysis")
    result = analyzer.analyze()
    print(f"  Status: {result.status}")
    print(f"  Entropy: {result.entropy_score}")
    assert result.entropy_score == score, "Scores should match"
    assert result.status in ["healthy", "warning", "critical"], "Status should be valid"
    print("  ✓ PASSED\n")

    # Test 11: JSON serialization
    print("Test 11: JSON serialization")
    from dataclasses import asdict
    data = asdict(result)
    json_str = json.dumps(data)
    print(f"  Generated {len(json_str)} bytes of JSON")
    assert "entropy_score" in json_str, "JSON should contain entropy_score"
    print("  ✓ PASSED\n")

    print("=== All Tests Passed ===")


if __name__ == "__main__":
    try:
        test_entropy_analyzer()
        sys.exit(0)
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
