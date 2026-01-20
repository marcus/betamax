#!/bin/bash
# Tests for @source directive

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BETAMAX="$PROJECT_ROOT/betamax"
TEST_DIR=$(mktemp -d)

cleanup() {
  rm -rf "$TEST_DIR"
}
trap cleanup EXIT

# Test counter
TESTS=0
PASSED=0

pass() {
  echo "  PASS: $1"
  PASSED=$((PASSED + 1))
}

fail() {
  echo "  FAIL: $1"
  echo "    $2"
}

run_test() {
  TESTS=$((TESTS + 1))
}

echo "=== @source directive tests ==="

# Test 1: Basic @source works
run_test
cat > "$TEST_DIR/common.keys" << 'EOF'
@set:cols:100
echo hello
EOF
cat > "$TEST_DIR/main.keys" << 'EOF'
@source:common.keys
echo world
EOF
if "$BETAMAX" --validate-only -f "$TEST_DIR/main.keys" echo 2>&1 | grep -q "Validation passed"; then
  pass "Basic @source validation"
else
  fail "Basic @source validation" "Expected validation to pass"
fi

# Test 2: Circular import detection
run_test
cat > "$TEST_DIR/a.keys" << 'EOF'
@source:b.keys
a
EOF
cat > "$TEST_DIR/b.keys" << 'EOF'
@source:a.keys
b
EOF
if "$BETAMAX" --validate-only -f "$TEST_DIR/a.keys" echo 2>&1 | grep -q "Circular @source detected"; then
  pass "Circular import detection"
else
  fail "Circular import detection" "Expected circular import error"
fi

# Test 3: Self-import detection
run_test
cat > "$TEST_DIR/self.keys" << 'EOF'
@source:self.keys
test
EOF
if "$BETAMAX" --validate-only -f "$TEST_DIR/self.keys" echo 2>&1 | grep -q "Circular @source detected"; then
  pass "Self-import detection"
else
  fail "Self-import detection" "Expected circular import error"
fi

# Test 4: Missing file detection
run_test
cat > "$TEST_DIR/missing.keys" << 'EOF'
@source:nonexistent.keys
test
EOF
if "$BETAMAX" --validate-only -f "$TEST_DIR/missing.keys" echo 2>&1 | grep -q "@source file not found"; then
  pass "Missing file detection"
else
  fail "Missing file detection" "Expected file not found error"
fi

# Test 5: Nested @source (depth 2)
run_test
mkdir -p "$TEST_DIR/lib"
cat > "$TEST_DIR/lib/base.keys" << 'EOF'
@set:rows:30
base
EOF
cat > "$TEST_DIR/lib/common.keys" << 'EOF'
@source:base.keys
common
EOF
cat > "$TEST_DIR/top.keys" << 'EOF'
@source:lib/common.keys
top
EOF
if "$BETAMAX" --validate-only -f "$TEST_DIR/top.keys" echo 2>&1 | grep -q "Validation passed"; then
  pass "Nested @source (depth 2)"
else
  fail "Nested @source (depth 2)" "Expected validation to pass"
fi

# Test 6: Relative path resolution in subdirectory
run_test
# lib/common.keys sources lib/base.keys via relative path
# Test that relative paths work from the sourced file's directory
if "$BETAMAX" --validate-only -f "$TEST_DIR/top.keys" echo 2>&1 | grep -q "Validation passed"; then
  pass "Relative path resolution in subdirectory"
else
  fail "Relative path resolution in subdirectory" "Expected validation to pass"
fi

# Test 7: @source with @set directives preserved
run_test
cat > "$TEST_DIR/settings.keys" << 'EOF'
@set:cols:150
@set:rows:50
EOF
cat > "$TEST_DIR/with-settings.keys" << 'EOF'
@source:settings.keys
echo test
EOF
if "$BETAMAX" --validate-only -f "$TEST_DIR/with-settings.keys" echo 2>&1 | grep -q "Validation passed"; then
  pass "@source with @set directives"
else
  fail "@source with @set directives" "Expected validation to pass"
fi

# Test 8: Non-.keys extension still works (warning is optional)
run_test
cat > "$TEST_DIR/noext.txt" << 'EOF'
echo test
EOF
cat > "$TEST_DIR/other-ext.keys" << 'EOF'
@source:noext.txt
test
EOF
if "$BETAMAX" --validate-only -f "$TEST_DIR/other-ext.keys" echo 2>&1 | grep -q "Validation passed"; then
  pass "Non-.keys extension still works"
else
  fail "Non-.keys extension still works" "Expected validation to pass"
fi

# Summary
echo ""
echo "=== Results: $PASSED/$TESTS tests passed ==="
if [[ $PASSED -eq $TESTS ]]; then
  exit 0
else
  exit 1
fi
