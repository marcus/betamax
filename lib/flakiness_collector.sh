#!/bin/bash
# flakiness_collector.sh - Collect test execution history and metrics
# Tracks pass/fail outcomes and execution times for flakiness analysis

set -e

FLAKINESS_DB="${FLAKINESS_DB:-.betamax_flakiness.db}"
FLAKINESS_TMPDIR="${FLAKINESS_TMPDIR:-.betamax_flakiness}"

# Initialize flakiness database
init_flakiness_db() {
  mkdir -p "$FLAKINESS_TMPDIR"

  # Create metadata file
  cat > "$FLAKINESS_TMPDIR/metadata.json" << 'EOF'
{
  "version": "1.0",
  "created_at": "",
  "total_runs": 0,
  "tests": {}
}
EOF
}

# Record a single test execution
record_test_execution() {
  local test_name="$1"
  local passed="$2"  # true/false
  local duration_ms="$3"
  local timestamp=$(date +%s)

  # Create test history file if it doesn't exist
  local test_file="$FLAKINESS_TMPDIR/${test_name// /_}.json"

  if [[ ! -f "$test_file" ]]; then
    echo "[]" > "$test_file"
  fi

  # Use Python to safely append to JSON array
  python3 << PYTHON
import json

test_file = '$test_file'
timestamp = $timestamp
passed = json.loads('$passed'.lower())
duration_ms = int('$duration_ms')

record = {
    'timestamp': timestamp,
    'passed': passed,
    'duration_ms': duration_ms
}

try:
    with open(test_file, 'r') as f:
        data = json.load(f)
except:
    data = []

data.append(record)

with open(test_file, 'w') as f:
    json.dump(data, f, indent=2)
PYTHON
}

# Parse test output and extract results
parse_test_results() {
  local output_file="$1"

  if [[ ! -f "$output_file" ]]; then
    return
  fi

  # Parse test results from captured output
  # Format: assumes "✓ test_name" for pass, "✗ test_name" for fail
  grep -E '✓|✗' "$output_file" | while read -r line; do
    if [[ "$line" =~ ^[[:space:]]*✓[[:space:]]*(.+)$ ]]; then
      local test_name="${BASH_REMATCH[1]}"
      record_test_execution "$test_name" "true" "0"
    elif [[ "$line" =~ ^[[:space:]]*✗[[:space:]]*(.+)$ ]]; then
      local test_name="${BASH_REMATCH[1]}"
      record_test_execution "$test_name" "false" "0"
    fi
  done
}

# Get all recorded tests
get_all_tests() {
  if [[ ! -d "$FLAKINESS_TMPDIR" ]]; then
    return
  fi

  for file in "$FLAKINESS_TMPDIR"/*.json; do
    [[ "$file" == "$FLAKINESS_TMPDIR/metadata.json" ]] && continue
    basename "$file" .json | sed 's/_/ /g'
  done
}

# Get execution history for a test
get_test_history() {
  local test_name="$1"
  local test_file="$FLAKINESS_TMPDIR/${test_name// /_}.json"

  if [[ ! -f "$test_file" ]]; then
    echo "[]"
    return
  fi

  cat "$test_file"
}

# Clean up flakiness data
cleanup_flakiness() {
  if [[ -d "$FLAKINESS_TMPDIR" ]]; then
    rm -rf "$FLAKINESS_TMPDIR"
  fi
}

export -f init_flakiness_db record_test_execution parse_test_results get_all_tests get_test_history cleanup_flakiness
