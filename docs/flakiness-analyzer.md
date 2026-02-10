# Betamax Test Flakiness Analyzer

The Betamax Test Flakiness Analyzer identifies and analyzes tests with inconsistent pass/fail behavior. It helps developers discover unreliable tests that pass sometimes and fail other times, which are often the result of timing issues, external dependencies, or non-deterministic test data.

## Overview

Flaky tests are tests that pass on some runs and fail on others without any code changes. They are problematic because:
- They reduce confidence in the test suite
- They waste developer time investigating false failures
- They mask real bugs by appearing to pass/fail randomly
- They slow down CI/CD pipelines with retries

The flakiness analyzer solves this by:
1. **Tracking test execution history** - Records pass/fail outcomes across multiple runs
2. **Computing statistical metrics** - Calculates pass rates, failure patterns, and timing variance
3. **Identifying flaky tests** - Detects tests that fail inconsistently
4. **Generating reports** - Outputs findings in JSON, HTML, and plain text formats

## Quick Start

### Enable Flakiness Analysis

Run the test suite with the `--analyze-flakiness` flag:

```bash
./test/run_tests.sh --analyze-flakiness
```

This will:
1. Collect test execution data during the test run
2. Compute flakiness metrics after all tests complete
3. Generate reports in JSON, HTML, and plain text formats
4. Output reports to `test/output/`

### View Results

After running tests with flakiness analysis:

- **HTML Report**: Open `test/output/flakiness-report.html` in a web browser for a visual summary
- **JSON Report**: Parse `test/output/flakiness-report.json` programmatically
- **Text Report**: View `test/output/flakiness-report.txt` in your terminal

## Standalone Usage

The flakiness analyzer can also be used standalone to analyze previously collected data:

```bash
# Generate all report formats
./bin/betamax-flakiness analyze

# Generate only JSON report
./bin/betamax-flakiness analyze --format json

# Generate HTML report and clean up data
./bin/betamax-flakiness analyze --format html --cleanup

# Generate to custom output directory
./bin/betamax-flakiness analyze -o ./reports --format json,html,txt
```

## Data Collection

Test executions are tracked in `.betamax_flakiness/` directory:

```
.betamax_flakiness/
├── metadata.json           # Analysis metadata
├── test_name_1.json       # Execution history for test 1
├── test_name_2.json       # Execution history for test 2
└── ...
```

Each test file contains an array of execution records:

```json
[
  {
    "timestamp": 1234567890,
    "passed": true,
    "duration_ms": 150
  },
  {
    "timestamp": 1234567900,
    "passed": false,
    "duration_ms": 200
  }
]
```

## Report Formats

### HTML Report

Interactive web-based report showing:
- Summary metrics (total tests, flaky count, failures, stable tests)
- Detailed table of flaky tests with pass rates
- List of always-failing tests
- Visual indicators for test health

Open `flakiness-report.html` in any web browser.

### JSON Report

Structured data including:
- Timestamp of report generation
- Summary statistics
- Detailed metrics for all tests
- Flaky tests sorted by pass rate

Useful for:
- Programmatic analysis
- Integration with other tools
- Historical trend tracking

Example:

```json
{
  "timestamp": "2026-02-10T15:30:45.123456",
  "summary": {
    "total_tests": 42,
    "flaky_tests_count": 3,
    "stable_tests_count": 39,
    "always_failing": 1,
    "always_passing": 38
  },
  "flaky_tests": [
    {
      "test": "test_timeout_handling",
      "pass_rate_pct": 33.33,
      "total_runs": 6,
      "passes": 2,
      "failures": 4,
      "max_consecutive_failures": 2,
      "is_flaky": true,
      "timing": {
        "mean_ms": 250.5,
        "median_ms": 245.0,
        "min_ms": 100,
        "max_ms": 500,
        "stdev_ms": 125.3,
        "variance_pct": 49.9
      }
    }
  ],
  "all_metrics": { ... }
}
```

### Text Report

Human-readable summary showing:
- Test statistics
- Detailed flaky test listings
- Always-failing tests
- Recommendations for investigation

Example output:

```
================================================================================
BETAMAX TEST FLAKINESS REPORT
================================================================================
Generated: 2026-02-10 15:30:45

SUMMARY
--------------------------------------------------------------------------------
Total Tests:        42
Flaky Tests:        3
Always Failing:     1
Stable Passing:     38

FLAKY TESTS (Pass Sometimes, Fail Other Times)
--------------------------------------------------------------------------------
  test_timeout_handling
    Pass Rate: 33.3% (2/6)
    Max Consecutive Failures: 2
    Timing: 250ms avg (σ: 125ms)

  test_network_request
    Pass Rate: 50.0% (3/6)
    Max Consecutive Failures: 1
    Timing: 500ms avg (σ: 75ms)

...
```

## Metrics Explained

### Pass Rate
Percentage of times a test passed across all runs.
- **100%**: Test always passes (stable)
- **0%**: Test never passes (always failing, not flaky)
- **0-100%**: Test is flaky

### Timing Statistics
- **mean_ms**: Average execution time across all runs
- **stdev_ms**: Standard deviation of execution times
- **variance_pct**: Coefficient of variation (stdev / mean * 100)
  - High variance may indicate timing-dependent failures

### Consecutive Failures
The maximum number of consecutive failures observed. Indicates whether failures are:
- **1**: Randomly scattered (likely timing or external dependency)
- **>1**: Clustered (might indicate environmental issues or state pollution)

## Investigation Guide

### High-Variance Timing (variance_pct > 50%)

Tests with high timing variance often fail due to:
- **Race conditions**: Asynchronous operations not properly synchronized
- **Resource contention**: Tests competing for shared resources
- **Slow external services**: Timeouts when dependencies are slow

**Solution**: Add explicit waits, reduce parallelism, use deterministic test data.

### Low Pass Rate (< 50%)

Tests that fail most of the time:
- Check if test dependencies are available
- Verify test data setup is correct
- Look for environment-specific issues

**Solution**: May be better to skip or disable the test while investigating.

### Clustering (max_consecutive_failures > 1)

Tests that fail in clusters:
- Suggests environment state issues (leaked resources, etc.)
- May indicate test ordering dependencies

**Solution**: Run tests in isolation, check for setup/teardown issues.

### External Dependencies

Tests that depend on:
- Network services (APIs, databases)
- System resources (disk space, memory)
- Timing windows

**Solution**: Mock external dependencies, add retry logic, use test containers.

## Integration with CI/CD

Track flakiness trends over time:

```bash
#!/bin/bash
# ci-flakiness.sh

./test/run_tests.sh --analyze-flakiness

# Archive reports with git
git add test/output/flakiness-report.json
git commit -m "test(flakiness): track trends"

# Alert if too many flaky tests
flaky_count=$(jq '.summary.flaky_tests_count' test/output/flakiness-report.json)
if [ "$flaky_count" -gt 3 ]; then
  echo "⚠️  $flaky_count flaky tests detected"
  exit 1
fi
```

## Programmatic Access

The flakiness analyzer provides shell functions for integration:

```bash
source lib/flakiness_collector.sh
source lib/flakiness_analyzer.sh

# Record a test result
record_test_execution "my_test" "false" "150"

# Compute metrics
metrics=$(compute_flakiness_metrics)

# Identify flaky tests
flaky=$(METRICS_JSON="$metrics" identify_flaky_tests)

# Check for specific test
if echo "$flaky" | grep -q "my_test"; then
  echo "Test is flaky!"
fi
```

## Cleaning Up

Remove flakiness data:

```bash
./bin/betamax-flakiness clean
```

Or use the `--cleanup` flag with analysis:

```bash
./bin/betamax-flakiness analyze --cleanup
```

## Examples

### Find Most Flaky Test

```bash
jq '.flaky_tests[0]' test/output/flakiness-report.json
```

### Get All Failing Tests

```bash
jq '.all_metrics | to_entries[] | select(.value.pass_rate_pct == 0) | .key' \
  test/output/flakiness-report.json
```

### Track Improvement

```bash
# Run analysis multiple times, storing reports with timestamps
for run in {1..10}; do
  ./test/run_tests.sh --analyze-flakiness
  cp test/output/flakiness-report.json "flakiness-$run.json"

  # Check progress
  flaky=$(jq '.summary.flaky_tests_count' "flakiness-$run.json")
  echo "Run $run: $flaky flaky tests"
done
```

## Troubleshooting

### No Data Collected

If reports are empty or missing:

1. Ensure tests are running: `./test/run_tests.sh`
2. Check directory permissions: `ls -la .betamax_flakiness/`
3. Verify flag is set: `./test/run_tests.sh --analyze-flakiness`

### All Tests Show as Flaky

This may indicate:
- Tests are running in random order with state pollution
- Insufficient test runs for statistical significance
- Test environment is unstable

Try:
- Running more iterations for better statistics
- Running tests serially instead of in parallel
- Checking test isolation and setup/teardown

### Missing Timing Data

Timing data requires duration_ms in execution records. If missing:
- Ensure records are properly formatted
- Check JSON in `.betamax_flakiness/` directory
- Re-run tests to collect timing data

## See Also

- [Betamax Documentation](../README.md)
- [Test Runner Configuration](../test/run_tests.sh)
- [Unit Tests](../test/flakiness_analyzer_test.sh)
