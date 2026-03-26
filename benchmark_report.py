from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from analyzer import summarize_run
from regression import load_trace

FIXTURES_DIR = Path('tests/fixtures/benchmarks')
OUT_MD = Path('artifacts/benchmark_report.md')
OUT_HTML = Path('artifacts/benchmark_report.html')
BASELINE_DIR = Path('.agentlens/benchmark_baselines')
REGRESSION_MD = Path('artifacts/benchmark_regression.md')

EXPECTATIONS = {
    'clarification_failure.jsonl': {
        'failure_mode': 'clarification_failure',
        'fingerprint': 'clarification-missing',
        'signal': 'clarification_missing',
    },
    'goal_partially_completed.jsonl': {
        'failure_mode': 'goal_partially_completed',
        'fingerprint': 'goal-partially-completed',
        'signal': 'goal_partially_completed',
    },
    'tool_result_ignored.jsonl': {
        'failure_mode': 'tool_result_ignored',
        'fingerprint': 'tool-result-ignored',
        'signal': 'tool_result_ignored',
    },
    'wrong_tool_argument.jsonl': {
        'failure_mode': 'wrong_tool_argument',
        'fingerprint': 'wrong-tool-argument',
        'signal': 'used_wrong_tool_argument',
    },
    'wrong_tool_selected.jsonl': {
        'failure_mode': 'wrong_tool_selected',
        'fingerprint': 'wrong-tool-selected',
        'signal': 'used_wrong_tool',
    },
}


def _coverage_status(item: dict[str, Any], expected: dict[str, str]) -> tuple[str, list[str], list[str]]:
    matched: list[str] = []
    missed: list[str] = []
    for key in ('failure_mode', 'fingerprint', 'signal'):
        if item.get(key) == expected.get(key):
            matched.append(key)
        else:
            missed.append(key)

    if len(matched) == 3:
        return 'matched', matched, missed
    if matched:
        return 'partial', matched, missed
    return 'missed', matched, missed


def collect_benchmark_cases() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for path in sorted(FIXTURES_DIR.glob('*.jsonl')):
        events = load_trace(path)
        summary = summarize_run(events)
        item = {
            'fixture': path.name,
            'run_id': events[0].get('run_id') if events else path.stem,
            'failure_mode': summary.get('failure_mode'),
            'fingerprint': (summary.get('failure_fingerprint') or {}).get('label'),
            'priority_level': (summary.get('debug_priority') or {}).get('level'),
            'priority_score': (summary.get('debug_priority') or {}).get('score'),
            'answer_risk': summary.get('answer_risk'),
            'signal': (summary.get('suspicious_signals') or [{}])[0].get('type'),
            'final_answer': summary.get('final_answer'),
        }
        expected = EXPECTATIONS.get(path.name)
        if expected:
            coverage, matched_fields, missed_fields = _coverage_status(item, expected)
            item['expected'] = expected
            item['coverage_status'] = coverage
            item['matched_fields'] = matched_fields
            item['missed_fields'] = missed_fields
        items.append(item)
    return items


def build_benchmark_report(items: list[dict[str, Any]]) -> str:
    lines = ['# AgentLens Benchmark Coverage Report', '']
    if not items:
        lines.append('No benchmark fixtures found.')
        return '\n'.join(lines) + '\n'

    matched = sum(1 for item in items if item.get('coverage_status') == 'matched')
    partial = sum(1 for item in items if item.get('coverage_status') == 'partial')
    missed = sum(1 for item in items if item.get('coverage_status') == 'missed')

    lines.append('Public benchmark-inspired failure fixtures currently recognized by AgentLens.')
    lines.append(f'- coverage_summary: matched={matched} partial={partial} missed={missed}')
    lines.append('')
    for item in items:
        lines.append(f"## `{item['fixture']}`")
        if item.get('expected'):
            lines.append(f"- expected_failure_mode: `{item['expected']['failure_mode']}`")
            lines.append(f"- expected_fingerprint: `{item['expected']['fingerprint']}`")
            lines.append(f"- expected_signal: `{item['expected']['signal']}`")
            lines.append(f"- coverage_status: `{item.get('coverage_status')}`")
            lines.append(f"- matched_fields: `{item.get('matched_fields')}`")
            lines.append(f"- missed_fields: `{item.get('missed_fields')}`")
        lines.append(f"- failure_mode: `{item['failure_mode']}`")
        lines.append(f"- fingerprint: `{item['fingerprint']}`")
        lines.append(f"- priority: `{item['priority_level']}` ({item['priority_score']}/100)")
        lines.append(f"- answer_risk: `{item['answer_risk']}`")
        lines.append(f"- signal: `{item['signal']}`")
        lines.append(f"- final_answer: {item['final_answer']}")
        lines.append('')
    return '\n'.join(lines)


def build_benchmark_report_html(items: list[dict[str, Any]]) -> str:
    matched = sum(1 for item in items if item.get('coverage_status') == 'matched')
    partial = sum(1 for item in items if item.get('coverage_status') == 'partial')
    missed = sum(1 for item in items if item.get('coverage_status') == 'missed')
    cards = ''.join(
        f'''
        <section class="card level-{html.escape(str(item.get("priority_level") or "low"))} coverage-{html.escape(str(item.get("coverage_status") or "unknown"))}">
          <div class="head">
            <div>
              <div class="eyebrow">Benchmark Fixture</div>
              <h2>{html.escape(str(item.get("fixture")))}</h2>
            </div>
            <div class="score">{html.escape(str(item.get("priority_score") or 0))}</div>
          </div>
          <div class="meta">
            <span>coverage: <strong>{html.escape(str(item.get("coverage_status") or "unknown"))}</strong></span>
            <span>failure: <strong>{html.escape(str(item.get("failure_mode") or "unknown"))}</strong></span>
            <span>fingerprint: <strong>{html.escape(str(item.get("fingerprint") or "unknown"))}</strong></span>
            <span>risk: <strong>{html.escape(str(item.get("answer_risk") or "unknown"))}</strong></span>
            <span>signal: <strong>{html.escape(str(item.get("signal") or "unknown"))}</strong></span>
          </div>
          <div class="meta">
            <span>expected failure: <strong>{html.escape(str((item.get("expected") or {}).get("failure_mode") or "n/a"))}</strong></span>
            <span>expected fingerprint: <strong>{html.escape(str((item.get("expected") or {}).get("fingerprint") or "n/a"))}</strong></span>
            <span>matched: <strong>{html.escape(', '.join(item.get("matched_fields") or []) or 'none')}</strong></span>
            <span>missed: <strong>{html.escape(', '.join(item.get("missed_fields") or []) or 'none')}</strong></span>
          </div>
          <div class="answer">{html.escape(str(item.get("final_answer") or "No final answer captured."))}</div>
        </section>
        '''
        for item in items
    ) or '<div class="empty">No benchmark fixtures found.</div>'

    return f'''<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>AgentLens Benchmark Coverage</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #07101d;
      --panel: rgba(14, 24, 40, 0.92);
      --border: #22324f;
      --text: #edf3fb;
      --muted: #9fb0c8;
      --accent: #7cc4ff;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: ui-sans-serif, system-ui, sans-serif; background: radial-gradient(circle at top, #132440 0%, var(--bg) 60%); color: var(--text); }}
    main {{ max-width: 1100px; margin: 0 auto; padding: 40px 24px 64px; }}
    .stack {{ display: grid; gap: 14px; }}
    .summary {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; margin: 18px 0 22px; }}
    .stat {{ background: var(--panel); border: 1px solid var(--border); border-radius: 18px; padding: 16px; }}
    .stat-label {{ color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; }}
    .stat-value {{ margin-top: 8px; font-size: 28px; font-weight: 800; }}
    .card {{ background: var(--panel); border: 1px solid var(--border); border-radius: 18px; padding: 18px; }}
    .head {{ display: flex; justify-content: space-between; gap: 16px; align-items: start; }}
    .eyebrow {{ color: var(--accent); font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px; }}
    .score {{ min-width: 56px; height: 56px; display: grid; place-items: center; border-radius: 16px; border: 1px solid var(--border); background: #0d1728; font-weight: 800; font-size: 22px; }}
    .meta {{ display: flex; flex-wrap: wrap; gap: 10px 16px; margin: 12px 0; color: var(--muted); }}
    .answer {{ padding: 12px 14px; border-radius: 14px; background: #0c1524; border: 1px solid var(--border); line-height: 1.6; white-space: pre-wrap; }}
    .coverage-matched {{ box-shadow: 0 0 0 1px rgba(109, 211, 160, 0.18) inset; }}
    .coverage-partial {{ box-shadow: 0 0 0 1px rgba(255, 209, 102, 0.18) inset; }}
    .coverage-missed {{ box-shadow: 0 0 0 1px rgba(255, 138, 101, 0.18) inset; }}
  </style>
</head>
<body>
  <main>
    <h1>AgentLens Benchmark Coverage</h1>
    <p>How AgentLens currently interprets public benchmark-inspired agent failure fixtures.</p>
    <div class="summary">
      <div class="stat"><div class="stat-label">Matched</div><div class="stat-value">{matched}</div></div>
      <div class="stat"><div class="stat-label">Partial</div><div class="stat-value">{partial}</div></div>
      <div class="stat"><div class="stat-label">Missed</div><div class="stat-value">{missed}</div></div>
    </div>
    <div class="stack">{cards}</div>
  </main>
</body>
</html>
'''


def write_benchmark_report() -> tuple[Path, Path]:
    items = collect_benchmark_cases()
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(build_benchmark_report(items), encoding='utf-8')
    OUT_HTML.write_text(build_benchmark_report_html(items), encoding='utf-8')
    return OUT_MD, OUT_HTML


def save_benchmark_baseline(name: str) -> Path:
    items = collect_benchmark_cases()
    BASELINE_DIR.mkdir(parents=True, exist_ok=True)
    out = BASELINE_DIR / f'{name}.json'
    out.write_text(json.dumps(items, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return out


def load_benchmark_baseline(name: str) -> list[dict[str, Any]]:
    path = BASELINE_DIR / f'{name}.json'
    if not path.exists():
        raise SystemExit(f'Benchmark baseline not found: {name}')
    return json.loads(path.read_text(encoding='utf-8'))


def build_benchmark_regression_report(baseline_name: str, baseline_items: list[dict[str, Any]], current_items: list[dict[str, Any]]) -> str:
    baseline_by_fixture = {item['fixture']: item for item in baseline_items}
    current_by_fixture = {item['fixture']: item for item in current_items}
    lines = ['# AgentLens Benchmark Regression Report', '']
    regressions = 0
    for fixture in sorted(set(baseline_by_fixture) | set(current_by_fixture)):
        before = baseline_by_fixture.get(fixture, {})
        after = current_by_fixture.get(fixture, {})
        before_status = before.get('coverage_status', 'missing')
        after_status = after.get('coverage_status', 'missing')
        if before_status == 'matched' and after_status != 'matched':
            regressions += 1
        lines.append(f"## `{fixture}`")
        lines.append(f"- baseline: `{baseline_name}`")
        lines.append(f"- coverage_before: `{before_status}`")
        lines.append(f"- coverage_after: `{after_status}`")
        lines.append(f"- fingerprint_before: `{before.get('fingerprint')}`")
        lines.append(f"- fingerprint_after: `{after.get('fingerprint')}`")
        lines.append('')
    lines.insert(2, f'- regressions: `{regressions}`')
    return '\n'.join(lines)


def write_benchmark_regression_report(name: str) -> Path:
    baseline_items = load_benchmark_baseline(name)
    current_items = collect_benchmark_cases()
    REGRESSION_MD.parent.mkdir(parents=True, exist_ok=True)
    REGRESSION_MD.write_text(
        build_benchmark_regression_report(name, baseline_items, current_items),
        encoding='utf-8',
    )
    return REGRESSION_MD
