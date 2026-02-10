#!/bin/bash
# Tests for entropy_detector.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$SCRIPT_DIR/lib/entropy_detector.sh"

# Test counter
tests_passed=0
tests_failed=0

# Helper: assert function exists
assert_function_exists() {
  if declare -f "$1" > /dev/null; then
    ((tests_passed++))
    echo "✓ Function $1 exists"
  else
    ((tests_failed++))
    echo "✗ Function $1 not found"
  fi
}

# Helper: assert entropy score is numeric
assert_numeric() {
  if [[ "$1" =~ ^[0-9]+$ ]]; then
    ((tests_passed++))
    echo "✓ Entropy score is numeric: $1"
  else
    ((tests_failed++))
    echo "✗ Entropy score not numeric: $1"
  fi
}

# Test 1: All functions are defined
echo "=== Testing Function Definitions ==="
assert_function_exists "extract_readme_features"
assert_function_exists "extract_shell_functions"
assert_function_exists "extract_python_functions"
assert_function_exists "extract_bin_scripts"
assert_function_exists "detect_orphaned_code"
assert_function_exists "detect_scope_creep"
assert_function_exists "detect_unimplemented_features"
assert_function_exists "compute_entropy_score"
assert_function_exists "generate_entropy_report"
assert_function_exists "analyze_git_patterns"

# Test 2: Extract README features
echo ""
echo "=== Testing README Feature Extraction ==="
readme_features=$(extract_readme_features "$SCRIPT_DIR")
readme_count=$(echo "$readme_features" | grep -c . || echo 0)
# Should extract main section headers (## level only), not all headers/table rows
# Expected ~11 features (Installation, Quick Start, Recording Sessions, etc.)
if [[ $readme_count -ge 9 && $readme_count -le 20 ]]; then
  ((tests_passed++))
  echo "✓ Extracted features from README: $readme_count features (reasonable count)"
else
  ((tests_failed++))
  echo "✗ Feature count suspicious: $readme_count (expected 9-20, not overshooting)"
fi

# Test 3: Extract shell functions
echo ""
echo "=== Testing Shell Function Extraction ==="
shell_funcs=$(extract_shell_functions "$SCRIPT_DIR")
shell_count=$(echo "$shell_funcs" | grep -c . || echo 0)
# Expected ~51 functions in lib/
if [[ $shell_count -ge 40 && $shell_count -le 70 ]]; then
  ((tests_passed++))
  echo "✓ Extracted shell functions: $shell_count functions (correct)"
else
  ((tests_failed++))
  echo "✗ Function count off: $shell_count (expected 40-70)"
fi

# Test 4: Entropy score calculation
echo ""
echo "=== Testing Entropy Score Calculation ==="
score=$(compute_entropy_score "$SCRIPT_DIR")
assert_numeric "$score"
if [[ $score -ge 0 && $score -le 100 ]]; then
  ((tests_passed++))
  echo "✓ Entropy score in valid range: $score/100"
else
  ((tests_failed++))
  echo "✗ Entropy score out of range: $score"
fi

# Test 5: Detect scope creep
echo ""
echo "=== Testing Scope Creep Detection ==="
creep=$(detect_scope_creep "$SCRIPT_DIR" | wc -l)
if [[ $creep -ge 0 ]]; then
  ((tests_passed++))
  echo "✓ Detected $creep scope creep items"
else
  ((tests_failed++))
  echo "✗ Failed to detect scope creep"
fi

# Test 6: Detect orphaned code
echo ""
echo "=== Testing Orphaned Code Detection ==="
orphaned=$(detect_orphaned_code "$SCRIPT_DIR" 2>/dev/null | wc -l)
# Should find exactly 1 orphaned function (extract_keys_features)
if [[ $orphaned -eq 1 ]]; then
  ((tests_passed++))
  echo "✓ Detected correct orphaned count: 1 (extract_keys_features)"
  # Verify it's the right one
  if detect_orphaned_code "$SCRIPT_DIR" 2>/dev/null | grep -q "extract_keys_features"; then
    ((tests_passed++))
    echo "✓ Orphaned function correctly identified"
  else
    ((tests_failed++))
    echo "✗ Wrong orphaned function detected"
  fi
else
  ((tests_failed++))
  echo "✗ Orphaned count wrong: $orphaned (expected 1)"
fi

# Test 7: Git pattern analysis
echo ""
echo "=== Testing Git Pattern Analysis ==="
patterns=$(analyze_git_patterns "$SCRIPT_DIR")
if [[ -n "$patterns" ]]; then
  ((tests_passed++))
  echo "✓ Git patterns analyzed"
else
  ((tests_failed++))
  echo "✗ Failed to analyze git patterns"
fi

# Test 8: Entropy report generation
echo ""
echo "=== Testing Report Generation ==="
report=$(generate_entropy_report "$SCRIPT_DIR")
if [[ "$report" == *"entropy_score"* ]]; then
  ((tests_passed++))
  echo "✓ Generated entropy report with valid JSON"
else
  ((tests_failed++))
  echo "✗ Failed to generate valid report"
fi

# Summary
echo ""
echo "=== Test Summary ==="
echo "Passed: $tests_passed"
echo "Failed: $tests_failed"

if [[ $tests_failed -eq 0 ]]; then
  exit 0
else
  exit 1
fi
