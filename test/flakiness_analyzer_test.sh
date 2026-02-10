#!/bin/bash
# flakiness_analyzer_test.sh - Unit tests for flakiness analyzer
# Tests data collection, statistics computation, and reporting

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
TEST_TMPDIR=$(mktemp -d)

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
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

# Setup test environment
setup() {
  export FLAKINESS_TMPDIR="$TEST_TMPDIR/flakiness"
  mkdir -p "$FLAKINESS_TMPDIR"
  source "$PROJECT_DIR/lib/flakiness_collector.sh"
  source "$PROJECT_DIR/lib/flakiness_analyzer.sh"
}

# Test data collection
test_collect_single_pass() {
  local test_name="sample_test_pass"
  record_test_execution "$test_name" "true" "100"

  local history=$(get_test_history "$test_name")
  if echo "$history" | grep -q '"passed": true'; then
    pass "collect: record passing test"
  else
    fail "collect: failed to record passing test"
  fi
}

test_collect_single_fail() {
  local test_name="sample_test_fail"
  record_test_execution "$test_name" "false" "150"

  local history=$(get_test_history "$test_name")
  if echo "$history" | grep -q '"passed": false'; then
    pass "collect: record failing test"
  else
    fail "collect: failed to record failing test"
  fi
}

test_collect_multiple_executions() {
  local test_name="multiple_exec_test"

  for i in {1..5}; do
    if [[ $((i % 2)) -eq 0 ]]; then
      record_test_execution "$test_name" "true" "$((100 + i * 10))"
    else
      record_test_execution "$test_name" "false" "$((100 + i * 10))"
    fi
  done

  local history=$(get_test_history "$test_name")
  local count=$(echo "$history" | grep -c '"passed"' || true)

  if [[ $count -eq 5 ]]; then
    pass "collect: record multiple executions"
  else
    fail "collect: expected 5 executions, got $count"
  fi
}

# Test metrics computation
test_compute_metrics_simple() {
  local test_name="simple_metric_test"

  record_test_execution "$test_name" "true" "100"
  record_test_execution "$test_name" "true" "100"
  record_test_execution "$test_name" "false" "100"
  record_test_execution "$test_name" "false" "100"

  local metrics=$(compute_flakiness_metrics)

  if echo "$metrics" | grep -q '"pass_rate_pct": 50'; then
    pass "metrics: compute correct pass rate (50%)"
  else
    fail "metrics: pass rate calculation incorrect"
  fi

  if echo "$metrics" | grep -q '"is_flaky": true'; then
    pass "metrics: correctly identify flaky test"
  else
    fail "metrics: flaky test not identified"
  fi
}

test_compute_metrics_always_pass() {
  local test_name="always_pass_test"

  for i in {1..3}; do
    record_test_execution "$test_name" "true" "100"
  done

  local metrics=$(compute_flakiness_metrics)

  if echo "$metrics" | grep -q '"pass_rate_pct": 100'; then
    pass "metrics: identify always-passing test (100%)"
  else
    fail "metrics: always-passing test not detected correctly"
  fi

  if echo "$metrics" | grep -q '"is_flaky": false'; then
    pass "metrics: correctly mark always-passing as not flaky"
  else
    fail "metrics: always-passing marked as flaky"
  fi
}

test_compute_metrics_never_pass() {
  local test_name="never_pass_test"

  for i in {1..3}; do
    record_test_execution "$test_name" "false" "100"
  done

  local metrics=$(compute_flakiness_metrics)

  if echo "$metrics" | grep -q '"pass_rate_pct": 0'; then
    pass "metrics: identify always-failing test (0%)"
  else
    fail "metrics: always-failing test not detected correctly"
  fi

  if echo "$metrics" | grep -q '"is_flaky": false'; then
    pass "metrics: correctly mark always-failing as not flaky"
  else
    fail "metrics: always-failing marked as flaky"
  fi
}

test_compute_timing_variance() {
  local test_name="timing_variance_test"

  record_test_execution "$test_name" "true" "100"
  record_test_execution "$test_name" "true" "200"
  record_test_execution "$test_name" "true" "300"

  local metrics=$(compute_flakiness_metrics)

  if echo "$metrics" | grep -q '"mean_ms": 200'; then
    pass "metrics: compute correct mean timing"
  else
    fail "metrics: mean timing calculation incorrect"
  fi

  if echo "$metrics" | grep -q '"stdev_ms"' && echo "$metrics" | grep -q '"variance_pct"'; then
    pass "metrics: compute timing variance stats"
  else
    fail "metrics: timing variance stats missing"
  fi
}

test_consecutive_failures() {
  local test_name="consecutive_fail_test"

  record_test_execution "$test_name" "false" "100"
  record_test_execution "$test_name" "false" "100"
  record_test_execution "$test_name" "false" "100"
  record_test_execution "$test_name" "true" "100"

  local metrics=$(compute_flakiness_metrics)

  if echo "$metrics" | grep -q '"max_consecutive_failures": 3'; then
    pass "metrics: detect max consecutive failures (3)"
  else
    fail "metrics: max consecutive failures calculation incorrect"
  fi
}

# Test identify flaky tests
test_identify_flaky() {
  # Clear and setup fresh data
  rm -rf "$FLAKINESS_TMPDIR"
  mkdir -p "$FLAKINESS_TMPDIR"

  local flaky_test="flaky candidate"
  for i in {1..4}; do
    if [[ $((i % 2)) -eq 0 ]]; then
      record_test_execution "$flaky_test" "true" "100"
    else
      record_test_execution "$flaky_test" "false" "100"
    fi
  done

  local metrics=$(compute_flakiness_metrics)
  local flaky=$(METRICS_JSON="$metrics" identify_flaky_tests)

  if echo "$flaky" | grep -q "\"test\": \"$flaky_test\""; then
    pass "analyze: identify flaky tests"
  else
    fail "analyze: failed to identify flaky tests"
  fi
}

# Cleanup
cleanup() {
  rm -rf "$TEST_TMPDIR"
}

# Summary
summary() {
  echo ""
  echo "================================"
  echo -e "Results: ${GREEN}$PASSED passed${NC}, ${RED}$FAILED failed${NC}"
  echo "================================"

  cleanup

  if [[ $FAILED -gt 0 ]]; then
    exit 1
  fi
}

# Main test execution
main() {
  setup

  echo "=== Testing Data Collection ==="
  test_collect_single_pass
  test_collect_single_fail
  test_collect_multiple_executions

  echo ""
  echo "=== Testing Metrics Computation ==="
  test_compute_metrics_simple
  test_compute_metrics_always_pass
  test_compute_metrics_never_pass
  test_compute_timing_variance
  test_consecutive_failures

  echo ""
  echo "=== Testing Flaky Test Identification ==="
  test_identify_flaky

  summary
}

main "$@"
