#!/bin/bash
# flakiness_reporter.sh - Generate flakiness reports in multiple formats
# Outputs JSON, HTML, and plain text reports with actionable insights

set -e

FLAKINESS_TMPDIR="${FLAKINESS_TMPDIR:-.betamax_flakiness}"

# Generate JSON report
generate_json_report() {
  local output_file="$1"

  python3 << 'PYTHON'
import json
import sys
import os
from datetime import datetime

metrics_json = os.environ.get('METRICS_JSON', '{}')
output_file = os.environ.get('OUTPUT_FILE', 'report.json')

try:
    metrics = json.loads(metrics_json)
except:
    metrics = {}

flaky_tests = [
    {'test': name, **stats}
    for name, stats in metrics.items()
    if stats.get('is_flaky', False)
]

stable_tests = [
    {'test': name, **stats}
    for name, stats in metrics.items()
    if not stats.get('is_flaky', False) and stats.get('pass_rate_pct') > 0
]

report = {
    'timestamp': datetime.now().isoformat(),
    'summary': {
        'total_tests': len(metrics),
        'flaky_tests_count': len(flaky_tests),
        'stable_tests_count': len(stable_tests),
        'always_failing': sum(1 for s in metrics.values() if s.get('pass_rate_pct') == 0),
        'always_passing': sum(1 for s in metrics.values() if s.get('pass_rate_pct') == 100)
    },
    'flaky_tests': sorted(flaky_tests, key=lambda x: x.get('pass_rate_pct', 0)),
    'all_metrics': metrics
}

with open(output_file, 'w') as f:
    json.dump(report, f, indent=2)

print('Generated JSON report: ' + output_file)
PYTHON
}

# Generate HTML report
generate_html_report() {
  local output_file="$1"

  python3 << 'PYTHON'
import json
import sys
from datetime import datetime
import os

metrics_json = os.environ.get('METRICS_JSON', '{}')

try:
    metrics = json.loads(metrics_json)
except:
    metrics = {}

flaky_tests = [
    {'test': name, **stats}
    for name, stats in metrics.items()
    if stats.get('is_flaky', False)
]

stable_pass = [
    {'test': name, **stats}
    for name, stats in metrics.items()
    if stats.get('pass_rate_pct') == 100
]

always_fail = [
    {'test': name, **stats}
    for name, stats in metrics.items()
    if stats.get('pass_rate_pct') == 0
]

html = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Betamax Test Flakiness Report</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #f5f5f5;
            color: #333;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
        }
        h1 { font-size: 28px; margin-bottom: 10px; }
        .timestamp { opacity: 0.9; font-size: 14px; }
        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .metric {
            display: grid;
            grid-template-columns: 1fr 1fr;
            align-items: center;
            gap: 15px;
        }
        .metric-value {
            font-size: 36px;
            font-weight: bold;
            color: #667eea;
        }
        .metric-label {
            font-size: 12px;
            text-transform: uppercase;
            color: #666;
            font-weight: 600;
        }
        .section { margin-bottom: 30px; }
        .section h2 {
            font-size: 20px;
            margin-bottom: 15px;
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        th {
            background: #f8f9fa;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #333;
            border-bottom: 1px solid #dee2e6;
        }
        td {
            padding: 12px;
            border-bottom: 1px solid #dee2e6;
        }
        tr:hover { background: #f8f9fa; }
        .pass-rate {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 12px;
        }
        .pass-rate.high { background: #d4edda; color: #155724; }
        .pass-rate.medium { background: #fff3cd; color: #856404; }
        .pass-rate.low { background: #f8d7da; color: #721c24; }
        .pass-rate.zero { background: #e2e3e5; color: #383d41; }
        .no-data {
            text-align: center;
            padding: 40px;
            color: #999;
            background: white;
            border-radius: 8px;
        }
        .timing {
            font-size: 12px;
            color: #666;
        }
        footer {
            text-align: center;
            margin-top: 40px;
            color: #999;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Betamax Test Flakiness Report</h1>
            <div class="timestamp">Generated: ''' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '''</div>
        </header>

        <div class="summary">
            <div class="card">
                <div class="metric">
                    <div class="metric-value">''' + str(len(metrics)) + '''</div>
                    <div class="metric-label">Total Tests</div>
                </div>
            </div>
            <div class="card">
                <div class="metric">
                    <div class="metric-value">''' + str(len(flaky_tests)) + '''</div>
                    <div class="metric-label">Flaky Tests</div>
                </div>
            </div>
            <div class="card">
                <div class="metric">
                    <div class="metric-value">''' + str(len(always_fail)) + '''</div>
                    <div class="metric-label">Always Failing</div>
                </div>
            </div>
            <div class="card">
                <div class="metric">
                    <div class="metric-value">''' + str(len(stable_pass)) + '''</div>
                    <div class="metric-label">Stable Passing</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>Flaky Tests ''' + (f'({len(flaky_tests)})' if flaky_tests else '(0)') + '''</h2>
'''

if flaky_tests:
    html += '''
            <table>
                <thead>
                    <tr>
                        <th>Test Name</th>
                        <th>Pass Rate</th>
                        <th>Runs</th>
                        <th>Failures</th>
                        <th>Max Consecutive Failures</th>
                    </tr>
                </thead>
                <tbody>
'''
    for test in flaky_tests:
        pass_rate = test.get('pass_rate_pct', 0)
        if pass_rate < 33:
            rate_class = 'low'
        elif pass_rate < 66:
            rate_class = 'medium'
        else:
            rate_class = 'high'

        html += f'''
                    <tr>
                        <td>{test['test']}</td>
                        <td><span class="pass-rate {rate_class}">{pass_rate:.1f}%</span></td>
                        <td>{test.get('total_runs', 0)}</td>
                        <td>{test.get('failures', 0)}</td>
                        <td>{test.get('max_consecutive_failures', 0)}</td>
                    </tr>
'''
    html += '''
                </tbody>
            </table>
'''
else:
    html += '<div class="no-data">No flaky tests detected</div>'

html += '''
        </div>

        <div class="section">
            <h2>Always Failing Tests ''' + (f'({len(always_fail)})' if always_fail else '(0)') + '''</h2>
'''

if always_fail:
    html += '''
            <table>
                <thead>
                    <tr>
                        <th>Test Name</th>
                        <th>Total Runs</th>
                    </tr>
                </thead>
                <tbody>
'''
    for test in always_fail:
        html += f'''
                    <tr>
                        <td>{test['test']}</td>
                        <td>{test.get('total_runs', 0)}</td>
                    </tr>
'''
    html += '''
                </tbody>
            </table>
'''
else:
    html += '<div class="no-data">No always-failing tests found</div>'

html += '''
        </div>

        <footer>
            <p>Test flakiness analysis by Betamax</p>
        </footer>
    </div>
</body>
</html>
'''

with open(os.environ.get('OUTPUT_FILE', 'report.html'), 'w') as f:
    f.write(html)

print('Generated HTML report')
PYTHON
}

# Generate plain text report
generate_text_report() {
  local output_file="$1"

  python3 << 'PYTHON'
import json
import os
from datetime import datetime

metrics_json = os.environ.get('METRICS_JSON', '{}')

try:
    metrics = json.loads(metrics_json)
except:
    metrics = {}

flaky_tests = [
    {'test': name, **stats}
    for name, stats in metrics.items()
    if stats.get('is_flaky', False)
]

always_fail = [
    {'test': name, **stats}
    for name, stats in metrics.items()
    if stats.get('pass_rate_pct') == 0
]

stable_pass = [
    {'test': name, **stats}
    for name, stats in metrics.items()
    if stats.get('pass_rate_pct') == 100
]

report = []
report.append("=" * 80)
report.append("BETAMAX TEST FLAKINESS REPORT")
report.append("=" * 80)
report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
report.append("")

report.append("SUMMARY")
report.append("-" * 80)
report.append(f"Total Tests:        {len(metrics)}")
report.append(f"Flaky Tests:        {len(flaky_tests)}")
report.append(f"Always Failing:     {len(always_fail)}")
report.append(f"Stable Passing:     {len(stable_pass)}")
report.append("")

if flaky_tests:
    report.append("FLAKY TESTS (Pass Sometimes, Fail Other Times)")
    report.append("-" * 80)
    for test in sorted(flaky_tests, key=lambda x: x.get('pass_rate_pct', 0)):
        report.append(f"  {test['test']}")
        report.append(f"    Pass Rate: {test.get('pass_rate_pct', 0):.1f}% ({test.get('passes', 0)}/{test.get('total_runs', 0)})")
        report.append(f"    Max Consecutive Failures: {test.get('max_consecutive_failures', 0)}")
        if test.get('timing'):
            timing = test['timing']
            report.append(f"    Timing: {timing.get('mean_ms', 0):.0f}ms avg (σ: {timing.get('stdev_ms', 0):.0f}ms)")
        report.append("")

if always_fail:
    report.append("ALWAYS FAILING TESTS (Never Pass)")
    report.append("-" * 80)
    for test in always_fail:
        report.append(f"  {test['test']}")
        report.append(f"    Runs: {test.get('total_runs', 0)}")
        report.append("")

report.append("")
report.append("RECOMMENDATIONS")
report.append("-" * 80)
if flaky_tests:
    report.append(f"• Investigate {len(flaky_tests)} flaky test(s) for:")
    report.append("  - Timing-dependent behavior (race conditions)")
    report.append("  - External service dependencies")
    report.append("  - Non-deterministic test data")
    report.append("  - Test ordering dependencies")
else:
    report.append("• All tests are stable or failing consistently")

if always_fail:
    report.append(f"• Fix {len(always_fail)} always-failing test(s)")

report.append("=" * 80)

with open(os.environ.get('OUTPUT_FILE', 'report.txt'), 'w') as f:
    f.write("\n".join(report))

print('Generated text report: ' + os.environ.get('OUTPUT_FILE', 'report.txt'))
PYTHON
}

export -f generate_json_report generate_html_report generate_text_report
