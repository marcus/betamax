#!/bin/bash
# flakiness_analyzer.sh - Compute statistical metrics for flaky tests
# Analyzes pass rates, failure patterns, and execution variance

set -e

FLAKINESS_TMPDIR="${FLAKINESS_TMPDIR:-.betamax_flakiness}"

# Compute flakiness metrics for all tests
compute_flakiness_metrics() {
  python3 << 'PYTHON'
import json
import os
from pathlib import Path
from statistics import mean, stdev, median
import sys

tmpdir = os.environ.get('FLAKINESS_TMPDIR', '.betamax_flakiness')

metrics = {}

# Process each test file
test_files = Path(tmpdir).glob('*.json')
for test_file in sorted(test_files):
    if test_file.name == 'metadata.json':
        continue

    test_name = test_file.stem.replace('_', ' ')

    try:
        with open(test_file, 'r') as f:
            history = json.load(f)
    except:
        continue

    if not history:
        continue

    # Calculate metrics
    passes = sum(1 for e in history if e.get('passed', False))
    fails = len(history) - passes
    total_runs = len(history)
    pass_rate = (passes / total_runs * 100) if total_runs > 0 else 0

    # Timing metrics
    durations = [e.get('duration_ms', 0) for e in history if e.get('duration_ms', 0) > 0]
    timing_stats = {}
    if durations:
        timing_stats['mean_ms'] = round(mean(durations), 2)
        timing_stats['median_ms'] = round(median(durations), 2)
        timing_stats['min_ms'] = min(durations)
        timing_stats['max_ms'] = max(durations)
        if len(durations) > 1:
            timing_stats['stdev_ms'] = round(stdev(durations), 2)
            timing_stats['variance_pct'] = round((timing_stats['stdev_ms'] / timing_stats['mean_ms'] * 100) if timing_stats['mean_ms'] > 0 else 0, 2)

    # Failure pattern analysis
    is_flaky = 0 < pass_rate < 100
    consecutive_fails = 0
    max_consecutive_fails = 0
    for e in history:
        if not e.get('passed', False):
            consecutive_fails += 1
            max_consecutive_fails = max(max_consecutive_fails, consecutive_fails)
        else:
            consecutive_fails = 0

    metrics[test_name] = {
        'total_runs': total_runs,
        'passes': passes,
        'failures': fails,
        'pass_rate_pct': round(pass_rate, 2),
        'is_flaky': is_flaky,
        'max_consecutive_failures': max_consecutive_fails,
        'timing': timing_stats
    }

# Sort by pass_rate (flakiest first)
sorted_metrics = dict(sorted(metrics.items(), key=lambda x: (
    x[1]['pass_rate_pct'],  # Ascending: 0% first
    -x[1]['total_runs']     # Descending: more runs first
)))

print(json.dumps(sorted_metrics, indent=2))
PYTHON
}

# Identify flaky tests (pass sometimes, fail other times)
identify_flaky_tests() {
  local metrics_json="$1"

  python3 << 'PYTHON'
import json
import sys
import os

metrics_json = os.environ.get('METRICS_JSON', '{}')

try:
    metrics = json.loads(metrics_json)
except:
    metrics = {}

flaky_tests = []
for test_name, stats in metrics.items():
    if stats.get('is_flaky', False):
        flaky_tests.append({
            'test': test_name,
            'pass_rate': stats.get('pass_rate_pct', 0),
            'runs': stats.get('total_runs', 0),
            'failures': stats.get('failures', 0)
        })

# Sort by lowest pass rate
flaky_tests.sort(key=lambda x: x['pass_rate'])

print(json.dumps(flaky_tests, indent=2))
PYTHON
}

# Detect failure clustering patterns
detect_failure_clusters() {
  local test_file="$1"

  python3 << PYTHON
import json

try:
    with open('$test_file', 'r') as f:
        history = json.load(f)
except:
    history = []

if not history:
    print('{}')
    exit(0)

# Find clusters of failures
clusters = []
current_cluster = {
    'start_idx': None,
    'length': 0,
    'start_time': None,
    'end_time': None
}

for i, execution in enumerate(history):
    if not execution.get('passed', False):
        if current_cluster['start_idx'] is None:
            current_cluster['start_idx'] = i
            current_cluster['start_time'] = execution.get('timestamp')
        current_cluster['length'] += 1
        current_cluster['end_time'] = execution.get('timestamp')
    else:
        if current_cluster['start_idx'] is not None:
            clusters.append(current_cluster)
            current_cluster = {
                'start_idx': None,
                'length': 0,
                'start_time': None,
                'end_time': None
            }

if current_cluster['start_idx'] is not None:
    clusters.append(current_cluster)

# Filter out clusters of length 1 (isolated failures)
significant_clusters = [c for c in clusters if c['length'] > 1]

result = {
    'total_clusters': len(clusters),
    'significant_clusters': len(significant_clusters),
    'clusters': significant_clusters
}

print(json.dumps(result, indent=2))
PYTHON
}

# Compare test runs to identify regressions
compare_runs() {
  local run1_json="$1"
  local run2_json="$2"

  python3 << PYTHON
import json
import sys

try:
    run1 = json.loads('$run1_json')
except:
    run1 = {}

try:
    run2 = json.loads('$run2_json')
except:
    run2 = {}

regressions = []
improvements = []

all_tests = set(run1.keys()) | set(run2.keys())

for test in sorted(all_tests):
    r1_pass = run1.get(test, {}).get('passed', False) if test in run1 else None
    r2_pass = run2.get(test, {}).get('passed', False) if test in run2 else None

    if r1_pass is True and r2_pass is False:
        regressions.append({'test': test, 'was': 'pass', 'now': 'fail'})
    elif r1_pass is False and r2_pass is True:
        improvements.append({'test': test, 'was': 'fail', 'now': 'pass'})

result = {
    'regressions': regressions,
    'improvements': improvements,
    'regression_count': len(regressions),
    'improvement_count': len(improvements)
}

print(json.dumps(result, indent=2))
PYTHON
}

export -f compute_flakiness_metrics identify_flaky_tests detect_failure_clusters compare_runs
