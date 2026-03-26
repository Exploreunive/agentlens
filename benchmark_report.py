from __future__ import annotations

import html
from pathlib import Path
from typing import Any

from analyzer import summarize_run
from regression import load_trace

FIXTURES_DIR = Path('tests/fixtures/benchmarks')
OUT_MD = Path('artifacts/benchmark_report.md')
OUT_HTML = Path('artifacts/benchmark_report.html')


def collect_benchmark_cases() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for path in sorted(FIXTURES_DIR.glob('*.jsonl')):
        events = load_trace(path)
        summary = summarize_run(events)
        items.append(
            {
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
        )
    return items


def build_benchmark_report(items: list[dict[str, Any]]) -> str:
    lines = ['# AgentLens Benchmark Coverage Report', '']
    if not items:
        lines.append('No benchmark fixtures found.')
        return '\n'.join(lines) + '\n'

    lines.append('Public benchmark-inspired failure fixtures currently recognized by AgentLens.')
    lines.append('')
    for item in items:
        lines.append(f"## `{item['fixture']}`")
        lines.append(f"- failure_mode: `{item['failure_mode']}`")
        lines.append(f"- fingerprint: `{item['fingerprint']}`")
        lines.append(f"- priority: `{item['priority_level']}` ({item['priority_score']}/100)")
        lines.append(f"- answer_risk: `{item['answer_risk']}`")
        lines.append(f"- signal: `{item['signal']}`")
        lines.append(f"- final_answer: {item['final_answer']}")
        lines.append('')
    return '\n'.join(lines)


def build_benchmark_report_html(items: list[dict[str, Any]]) -> str:
    cards = ''.join(
        f'''
        <section class="card level-{html.escape(str(item.get("priority_level") or "low"))}">
          <div class="head">
            <div>
              <div class="eyebrow">Benchmark Fixture</div>
              <h2>{html.escape(str(item.get("fixture")))}</h2>
            </div>
            <div class="score">{html.escape(str(item.get("priority_score") or 0))}</div>
          </div>
          <div class="meta">
            <span>failure: <strong>{html.escape(str(item.get("failure_mode") or "unknown"))}</strong></span>
            <span>fingerprint: <strong>{html.escape(str(item.get("fingerprint") or "unknown"))}</strong></span>
            <span>risk: <strong>{html.escape(str(item.get("answer_risk") or "unknown"))}</strong></span>
            <span>signal: <strong>{html.escape(str(item.get("signal") or "unknown"))}</strong></span>
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
    .card {{ background: var(--panel); border: 1px solid var(--border); border-radius: 18px; padding: 18px; }}
    .head {{ display: flex; justify-content: space-between; gap: 16px; align-items: start; }}
    .eyebrow {{ color: var(--accent); font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px; }}
    .score {{ min-width: 56px; height: 56px; display: grid; place-items: center; border-radius: 16px; border: 1px solid var(--border); background: #0d1728; font-weight: 800; font-size: 22px; }}
    .meta {{ display: flex; flex-wrap: wrap; gap: 10px 16px; margin: 12px 0; color: var(--muted); }}
    .answer {{ padding: 12px 14px; border-radius: 14px; background: #0c1524; border: 1px solid var(--border); line-height: 1.6; white-space: pre-wrap; }}
  </style>
</head>
<body>
  <main>
    <h1>AgentLens Benchmark Coverage</h1>
    <p>How AgentLens currently interprets public benchmark-inspired agent failure fixtures.</p>
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
