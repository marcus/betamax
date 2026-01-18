#!/bin/bash
# betamax validation test harness

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

PASSED=0
FAILED=0

pass() {
  echo -e "${GREEN}✓${NC} $1"
  ((PASSED++)) || true
}

fail() {
  echo -e "${RED}✗${NC} $1"
  ((FAILED++)) || true
}

# Test that keys content produces expected error
expect_error() {
  local keys_content="$1"
  local expected_error="$2"
  local desc="$3"

  local tmpfile
  tmpfile=$(mktemp)
  echo -e "$keys_content" > "$tmpfile"

  local output
  output=$("$PROJECT_DIR/betamax" echo -f "$tmpfile" 2>&1) || true

  if echo "$output" | grep -q "$expected_error"; then
    pass "$desc"
  else
    fail "$desc (expected: '$expected_error', got: '$output')"
  fi

  rm -f "$tmpfile"
}

# Test that keys content produces warning
expect_warning() {
  local keys_content="$1"
  local expected_warning="$2"
  local desc="$3"

  local tmpfile
  tmpfile=$(mktemp)
  echo -e "$keys_content" > "$tmpfile"

  local output
  output=$("$PROJECT_DIR/betamax" echo -f "$tmpfile" 2>&1) || true

  if echo "$output" | grep -q "Warning.*$expected_warning"; then
    pass "$desc"
  else
    fail "$desc (expected warning: '$expected_warning', got: '$output')"
  fi

  rm -f "$tmpfile"
}

# Test that keys content validates successfully
expect_valid() {
  local keys_content="$1"
  local desc="$2"

  local tmpfile
  tmpfile=$(mktemp)
  echo -e "$keys_content" > "$tmpfile"

  local output
  local exit_code=0
  output=$("$PROJECT_DIR/betamax" echo --validate-only -f "$tmpfile" 2>&1) || exit_code=$?

  if [[ $exit_code -eq 0 ]] && echo "$output" | grep -q "Validation passed"; then
    pass "$desc"
  else
    fail "$desc (got: '$output')"
  fi

  rm -f "$tmpfile"
}

# ============================================================
# @set directive tests
# ============================================================
test_set_directives() {
  echo ""
  echo "=== Testing @set directive validation ==="

  # Valid cases
  expect_valid "@set:cols:120" "@set:cols valid integer"
  expect_valid "@set:rows:40" "@set:rows valid integer"
  expect_valid "@set:delay:0" "@set:delay allows zero"
  expect_valid "@set:delay:100" "@set:delay valid positive"
  expect_valid "@set:output:./out" "@set:output valid path"
  expect_valid "@set:timeout:30" "@set:timeout valid"
  expect_valid "@set:shell:/bin/zsh" "@set:shell valid path"
  expect_valid "@set:gif_delay:50" "@set:gif_delay valid"

  # Error cases
  expect_error "@set:cols:" "Missing value" "@set:cols missing value"
  expect_error "@set:cols:abc" "Invalid integer" "@set:cols non-integer"
  expect_error "@set:rows:-5" "must be positive" "@set:rows negative"
  expect_error "@set:rows:0" "must be positive" "@set:rows zero"
  expect_error "@set:unknown:foo" "Unknown setting" "@set unknown key"
  expect_error "@set:output:" "Missing value" "@set:output empty"
}

# ============================================================
# @repeat/@end structure tests
# ============================================================
test_repeat_directives() {
  echo ""
  echo "=== Testing @repeat/@end validation ==="

  # Valid cases
  expect_valid "@repeat:3\nj\nk\n@end" "@repeat:N ... @end valid"
  expect_valid "@repeat:1\n@end" "@repeat:1 with empty body"

  # Error cases
  expect_error "@repeat" "Missing repeat count" "@repeat without count"
  expect_error "@repeat:abc" "Invalid repeat count" "@repeat non-integer"
  expect_error "@repeat:0" "must be positive" "@repeat zero"
  expect_error "@repeat:-1" "must be positive" "@repeat negative"
  expect_error "@repeat:3\nj" "no matching @end" "@repeat without @end"
  expect_error "@end" "without matching @repeat" "lone @end"
  expect_error "@repeat:2\n@repeat:3\n@end\n@end" "Nested @repeat" "nested @repeat"
  expect_error "@repeat:2\n@end\n@end" "without matching @repeat" "extra @end"
}

# ============================================================
# @sleep directive tests
# ============================================================
test_sleep_directives() {
  echo ""
  echo "=== Testing @sleep validation ==="

  # Valid cases
  expect_valid "@sleep:100" "@sleep:100 valid"
  expect_valid "@sleep:100:capture" "@sleep:100:capture valid"
  expect_valid "@sleep:1" "@sleep:1 valid (minimum)"

  # Error cases
  expect_error "@sleep:" "Missing sleep duration" "@sleep: empty"
  expect_error "@sleep:abc" "Invalid sleep duration" "@sleep non-integer"
  expect_error "@sleep:0" "must be positive" "@sleep zero"
  expect_error "@sleep:-100" "Invalid sleep duration" "@sleep negative"
  expect_error "@sleep:100:foo" "Invalid sleep option" "@sleep bad option"
  expect_error "@sleep:100:capture:extra" "Invalid @sleep format" "@sleep extra colon"
}

# ============================================================
# @wait directive tests
# ============================================================
test_wait_directives() {
  echo ""
  echo "=== Testing @wait validation ==="

  # Valid cases
  expect_valid "@wait:pattern" "@wait:pattern valid"
  expect_valid "@wait:/regex/" "@wait:/regex/ valid"
  expect_valid "@wait:/complex.*regex/" "@wait regex with metachar"

  # Error cases
  expect_error "@wait:" "Missing wait pattern" "@wait: empty"
  expect_error "@wait:/unclosed" "Unclosed regex" "@wait unclosed regex"
}

# ============================================================
# @capture directive tests
# ============================================================
test_capture_directives() {
  echo ""
  echo "=== Testing @capture validation ==="

  # Valid cases
  expect_valid "@capture" "@capture (stdout) valid"
  expect_valid "@capture:name.txt" "@capture:name.txt valid"
  expect_valid "@capture:name.html" "@capture:name.html valid"
  expect_valid "@capture:name.png" "@capture:name.png valid"
  expect_valid "@capture:name" "@capture:name (all formats) valid"

  # Error cases
  expect_error "@capture:name.mp4" "Invalid capture format" "@capture bad extension"
  expect_error "@capture:name.gif" "Invalid capture format" "@capture gif not valid (use @record)"
}

# ============================================================
# @record directive tests
# ============================================================
test_record_directives() {
  echo ""
  echo "=== Testing @record validation ==="

  # Valid cases
  expect_valid "@record:start" "@record:start valid"
  expect_valid "@record:stop:out.gif" "@record:stop:out.gif valid"

  # Error cases
  expect_error "@record" "Invalid @record format" "@record alone"
  expect_error "@record:pause" "Unknown @record command" "@record:pause unknown"
  expect_error "@record:stop:" "Missing GIF filename" "@record:stop: empty"
  expect_error "@record:stop:out.mp4" "must end with .gif" "@record:stop wrong ext"
}

# ============================================================
# @require directive tests
# ============================================================
test_require_directives() {
  echo ""
  echo "=== Testing @require validation ==="

  # Valid cases
  expect_valid "@require:termshot" "@require:termshot valid"
  expect_valid "@require:bash" "@require:bash valid"

  # Error cases
  expect_error "@require:" "Missing command name" "@require: empty"
  expect_error "@require:foo bar" "contains spaces" "@require with spaces"
}

# ============================================================
# Unknown directive warning tests
# ============================================================
test_unknown_directives() {
  echo ""
  echo "=== Testing unknown directive warnings ==="

  expect_warning "@seet:cols:80" "did you mean @set" "@seet typo suggests @set"
  expect_warning "@slep:100" "did you mean @sleep" "@slep typo suggests @sleep"
  expect_warning "@wiat:pattern" "did you mean @wait" "@wiat typo suggests @wait"
  expect_warning "@recrod:start" "did you mean @record" "@recrod typo suggests @record"
  expect_warning "@unknowndir" "Unknown directive" "truly unknown directive"
}

# ============================================================
# Inline timing validation tests
# ============================================================
test_inline_timing() {
  echo ""
  echo "=== Testing inline timing validation ==="

  # Valid cases
  expect_valid "j@50" "j@50 valid timing"
  expect_valid "Enter@200" "Enter@200 valid timing"
  expect_valid "C-c@100" "C-c@100 valid timing"

  # Error cases
  expect_error "j@" "missing milliseconds" "j@ missing timing"
  expect_error "j@0" "must be positive" "j@0 zero timing"
  expect_error "j@fast" "Invalid timing value" "j@fast non-numeric"
}

# ============================================================
# Integration tests with complete files
# ============================================================
test_integration() {
  echo ""
  echo "=== Testing integration ==="

  # Valid complete file
  local valid_file="@set:cols:120
@set:rows:40
@set:delay:50
@require:bash
@repeat:2
@sleep:100
j
@end
@wait:prompt
@capture:test.txt
@record:start
@frame
@record:stop:demo.gif"

  expect_valid "$valid_file" "complete valid .keys file"

  # Multiple errors detected
  local multi_error="@set:cols:abc
@repeat"

  local tmpfile
  tmpfile=$(mktemp)
  echo -e "$multi_error" > "$tmpfile"
  local output
  output=$("$PROJECT_DIR/betamax" echo -f "$tmpfile" 2>&1) || true
  rm -f "$tmpfile"

  if echo "$output" | grep -q "Invalid integer" && echo "$output" | grep -q "Missing repeat count"; then
    pass "multiple errors: reports all validation errors"
  else
    fail "multiple errors: should report all errors (got: $output)"
  fi
}

# Summary
summary() {
  echo ""
  echo "================================"
  echo -e "Validation tests: ${GREEN}$PASSED passed${NC}, ${RED}$FAILED failed${NC}"
  echo "================================"

  if [[ $FAILED -gt 0 ]]; then
    exit 1
  fi
}

# Main
main() {
  echo "Running betamax validation tests..."
  test_set_directives
  test_repeat_directives
  test_sleep_directives
  test_wait_directives
  test_capture_directives
  test_record_directives
  test_require_directives
  test_unknown_directives
  test_inline_timing
  test_integration
  summary
}

main "$@"
