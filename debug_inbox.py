from __future__ import annotations

import html
from pathlib import Path
from typing import Any, Dict, List, Optional

from casefile import write_case_board, write_case_index
from regression import list_baselines, list_traces, load_baseline, load_trace, summarize_regression, write_regression_report
from analyzer import summarize_run
from viewer import write_trace_view

OUT = Path('artifacts/debug_inbox.md')
HTML_OUT = Path('artifacts/debug_inbox.html')


def _priority_level(score: int) -> str:
    if score >= 70:
        return 'high'
    if score >= 35:
        return 'medium'
    return 'low'


def _resolve_inbox_baseline(baseline_name: Optional[str] = None) -> tuple[Optional[str], Optional[Path], Optional[List[Dict[str, Any]]]]:
    if baseline_name:
        trace_path, events = load_baseline(baseline_name)
        return baseline_name, trace_path, events

    baselines = list_baselines()
    if len(baselines) != 1:
        return None, None, None

    name = baselines[0].stem
    trace_path, events = load_baseline(name)
    return name, trace_path, events


def collect_debug_inbox(limit: int = 10, baseline_name: Optional[str] = None) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    active_baseline_name, active_baseline_path, active_baseline_events = _resolve_inbox_baseline(baseline_name)
    for trace_path in list_traces()[:limit]:
        events = load_trace(trace_path)
        summary = summarize_run(events)
        priority = summary.get('debug_priority', {})
        regression = None
        regression_detected = False
        regression_reasons: List[str] = []
        trace_view_path = write_trace_view(trace_path.stem)
        regression_report = None
        if active_baseline_events is not None and active_baseline_path is not None and trace_path != active_baseline_path:
            regression = summarize_regression(active_baseline_events, events)
            regression_detected = bool(regression.get('regression_detected'))
            regression_reasons = list(regression.get('reasons', []))
            if regression.get('comparable', True):
                regression_report = write_regression_report(
                    active_baseline_name or 'baseline',
                    active_baseline_path.name,
                    trace_path.name,
                    regression,
                )

        priority_score = int(priority.get('score', 0))
        priority_reasons = list(priority.get('reasons', []))
        if regression_detected:
            priority_score = min(priority_score + 25, 100)
            priority_reasons = ['This run regressed against the active baseline.'] + priority_reasons

        priority_level = _priority_level(priority_score)
        case_index_path = write_case_index(
            trace_name=trace_path.name,
            trace_view_path=str(trace_view_path),
            final_answer=summary.get('final_answer'),
            priority_level=priority_level,
            priority_score=priority_score,
            baseline_name=active_baseline_name,
            regression_report_path=str(regression_report) if regression_report else None,
        )

        items.append(
            {
                'trace_file': trace_path.name,
                'run_id': events[0].get('run_id') if events else trace_path.stem,
                'runtime': summary.get('runtime'),
                'agent_name': summary.get('agent_name'),
                'priority_score': priority_score,
                'priority_level': priority_level,
                'priority_reasons': priority_reasons[:4],
                'answer_risk': summary.get('answer_risk'),
                'failure_mode': summary.get('failure_mode'),
                'failure_fingerprint': summary.get('failure_fingerprint'),
                'final_answer': summary.get('final_answer'),
                'suspicious_signals': summary.get('suspicious_signals', []),
                'baseline_name': active_baseline_name,
                'baseline_trace_file': active_baseline_path.name if active_baseline_path else None,
                'regression_detected': regression_detected,
                'regression_reasons': regression_reasons,
                'regression_summary': regression,
                'trace_view_path': str(trace_view_path),
                'regression_report_path': str(regression_report) if regression_report else None,
                'case_index_path': str(case_index_path),
            }
        )
    items.sort(
        key=lambda item: (
            not bool(item.get('regression_detected')),
            -int(item.get('priority_score', 0)),
            str(item.get('trace_file')),
        )
    )
    return items


def build_debug_inbox_report(items: List[Dict[str, Any]]) -> str:
    lines = ['# AgentLens Debug Inbox', '']
    if not items:
        lines.append('No traces available.')
        return '\n'.join(lines) + '\n'

    lines.append('Runs are sorted by debug priority so you can triage what to inspect first.')
    baseline_name = next((item.get('baseline_name') for item in items if item.get('baseline_name')), None)
    if baseline_name:
        lines.append(f'Active baseline: `{baseline_name}`.')
    lines.append('')
    for index, item in enumerate(items, start=1):
        lines.append(f"## {index}. `{item.get('trace_file')}`")
        lines.append(f"- priority: `{item.get('priority_level')}` ({item.get('priority_score')}/100)")
        lines.append(f"- runtime: `{item.get('runtime')}`")
        lines.append(f"- agent: `{item.get('agent_name')}`")
        lines.append(f"- answer_risk: `{item.get('answer_risk')}`")
        lines.append(f"- failure_mode: `{item.get('failure_mode')}`")
        if item.get('baseline_name'):
            lines.append(f"- baseline_watch: `{item.get('baseline_name')}` -> regression=`{item.get('regression_detected')}`")
        lines.append(f"- trace_view: `{item.get('trace_view_path')}`")
        lines.append(f"- case_file: `{item.get('case_index_path')}`")
        if item.get('regression_report_path'):
            lines.append(f"- regression_report: `{item.get('regression_report_path')}`")
        lines.append(f"- final_answer: {item.get('final_answer')}")
        lines.append(f"- suspicious_signals: {item.get('suspicious_signals')}")
        reasons = item.get('priority_reasons', [])
        if reasons:
            lines.append('- why this is prioritized:')
            for reason in reasons:
                lines.append(f"  - {reason}")
        regression_reasons = item.get('regression_reasons', [])
        if regression_reasons:
            lines.append('- regression review:')
            for reason in regression_reasons:
                lines.append(f"  - {reason}")
        lines.append('')
    return '\n'.join(lines)


def build_debug_inbox_html(items: List[Dict[str, Any]]) -> str:
    if not items:
        cards = '<div class="empty">No traces available.</div>'
    else:
        cards = ''.join(
            f'''
            <section class="card level-{html.escape(str(item.get("priority_level", "low")))}">
              <div class="card-head">
                <div>
                  <div class="eyebrow">Run #{index}</div>
                  <h2>{html.escape(str(item.get("trace_file")))}</h2>
                </div>
                <div class="score">
                  <span>{html.escape(str(item.get("priority_score", 0)))}</span>
                  <small>{html.escape(str(item.get("priority_level", "low")))}</small>
                </div>
              </div>
              <div class="meta">
                <span>runtime: <strong>{html.escape(str(item.get("runtime") or "unknown"))}</strong></span>
                <span>agent: <strong>{html.escape(str(item.get("agent_name") or "unknown"))}</strong></span>
                <span>risk: <strong>{html.escape(str(item.get("answer_risk") or "unknown"))}</strong></span>
                <span>failure: <strong>{html.escape(str(item.get("failure_mode") or "none"))}</strong></span>
                <span>baseline watch: <strong>{html.escape("regressed" if item.get("regression_detected") else "clean")}</strong></span>
              </div>
              <div class="answer">{html.escape(str(item.get("final_answer") or "No final answer captured."))}</div>
              <div class="command-hint">
                Open this run with <code>python3 cli.py view {html.escape(str(Path(str(item.get("trace_file"))).stem))}</code>
                <br />
                Trace page: <code>{html.escape(str(item.get("trace_view_path") or ""))}</code>
                <br />
                Case file: <code>{html.escape(str(item.get("case_index_path") or ""))}</code>
              </div>
              <div class="columns">
                <div>
                  <h3>Priority reasons</h3>
                  <ul>{"".join(f"<li>{html.escape(str(reason))}</li>" for reason in item.get("priority_reasons", [])) or "<li>No priority reasons recorded.</li>"}</ul>
                </div>
                <div>
                  <h3>Suspicious signals</h3>
                  <ul>{"".join(f"<li>{html.escape(str(signal.get('type')))} at event #{html.escape(str(signal.get('event_index')))}</li>" for signal in item.get("suspicious_signals", [])) or "<li>No suspicious signals detected.</li>"}</ul>
                </div>
                <div>
                  <h3>Regression watch</h3>
                  <ul>{"".join(f"<li>{html.escape(str(reason))}</li>" for reason in item.get("regression_reasons", [])) or "<li>No baseline regression review attached.</li>"}</ul>
                  {f'<div class="report-hint">Report: <code>{html.escape(str(item.get("regression_report_path")))}</code></div>' if item.get("regression_report_path") else ''}
                </div>
              </div>
            </section>
            '''
            for index, item in enumerate(items, start=1)
        )

    high_count = sum(1 for item in items if item.get('priority_level') == 'high')
    medium_count = sum(1 for item in items if item.get('priority_level') == 'medium')
    low_count = sum(1 for item in items if item.get('priority_level') == 'low')
    regression_count = sum(1 for item in items if item.get('regression_detected'))
    baseline_name = next((item.get('baseline_name') for item in items if item.get('baseline_name')), None)

    return f'''<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>AgentLens Debug Inbox</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #08111f;
      --panel: #101b2d;
      --panel-2: #0d1728;
      --border: #23314a;
      --text: #edf3fb;
      --muted: #9cb0c8;
      --high: #ff8a65;
      --medium: #ffd166;
      --low: #6dd3a0;
      --accent: #7cc4ff;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: ui-sans-serif, system-ui, sans-serif; background: radial-gradient(circle at top, #10233f 0%, var(--bg) 55%); color: var(--text); }}
    main {{ max-width: 1120px; margin: 0 auto; padding: 40px 24px 56px; }}
    h1 {{ margin: 0; font-size: 40px; }}
    p {{ color: var(--muted); line-height: 1.6; }}
    .hero {{ display: grid; gap: 18px; margin-bottom: 28px; }}
    .stats {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; }}
    .stat, .card {{ background: rgba(16, 27, 45, 0.88); border: 1px solid var(--border); border-radius: 18px; }}
    .stat {{ padding: 18px; }}
    .stat .label {{ color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; }}
    .stat .value {{ margin-top: 8px; font-size: 28px; font-weight: 700; }}
    .stack {{ display: grid; gap: 16px; }}
    .card {{ padding: 20px; }}
    .card-head {{ display: flex; justify-content: space-between; gap: 16px; align-items: start; }}
    .eyebrow {{ color: var(--accent); font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px; }}
    .card h2 {{ margin: 0; font-size: 22px; word-break: break-word; }}
    .score {{ min-width: 88px; border-radius: 16px; padding: 12px; text-align: center; background: var(--panel-2); border: 1px solid var(--border); }}
    .score span {{ display: block; font-size: 28px; font-weight: 800; }}
    .score small {{ color: var(--muted); text-transform: uppercase; letter-spacing: 0.08em; }}
    .meta {{ display: flex; flex-wrap: wrap; gap: 10px 18px; margin: 16px 0 14px; color: var(--muted); }}
    .answer {{ padding: 14px 16px; border-radius: 14px; background: var(--panel-2); border: 1px solid var(--border); line-height: 1.6; white-space: pre-wrap; }}
    .command-hint {{ margin-top: 12px; color: var(--muted); font-size: 14px; }}
    .report-hint {{ margin-top: 12px; color: var(--muted); font-size: 13px; }}
    code {{ color: var(--accent); font-family: ui-monospace, SFMono-Regular, monospace; }}
    .columns {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; margin-top: 16px; }}
    .columns h3 {{ margin: 0 0 10px; font-size: 14px; color: var(--accent); }}
    ul {{ margin: 0; padding-left: 18px; color: var(--muted); }}
    li {{ margin: 8px 0; }}
    .level-high .score {{ border-color: rgba(255, 138, 101, 0.55); }}
    .level-medium .score {{ border-color: rgba(255, 209, 102, 0.55); }}
    .level-low .score {{ border-color: rgba(109, 211, 160, 0.55); }}
    .empty {{ padding: 28px; border-radius: 18px; background: rgba(16, 27, 45, 0.88); border: 1px solid var(--border); color: var(--muted); }}
    @media (max-width: 800px) {{
      .stats, .columns {{ grid-template-columns: 1fr; }}
      .card-head {{ flex-direction: column; }}
    }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <div>
        <h1>AgentLens Debug Inbox</h1>
        <p>Recent traces ranked by debugging value, so the first thing you open is the run most likely to hide a real agent failure.</p>
        <p>{html.escape(f"Baseline watch: {baseline_name}" if baseline_name else "Baseline watch: disabled")}</p>
      </div>
      <div class="stats">
        <div class="stat"><div class="label">Traces</div><div class="value">{len(items)}</div></div>
        <div class="stat"><div class="label">High Priority</div><div class="value">{high_count}</div></div>
        <div class="stat"><div class="label">Regressions</div><div class="value">{regression_count}</div></div>
        <div class="stat"><div class="label">Low Priority</div><div class="value">{low_count + medium_count}</div></div>
      </div>
    </section>
    <section class="stack">
      {cards}
    </section>
  </main>
</body>
</html>
'''


def write_debug_inbox(limit: int = 10, baseline_name: Optional[str] = None) -> Path:
    items = collect_debug_inbox(limit=limit, baseline_name=baseline_name)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build_debug_inbox_report(items), encoding='utf-8')
    write_case_board(items)
    return OUT


def write_debug_inbox_html(limit: int = 10, baseline_name: Optional[str] = None) -> Path:
    items = collect_debug_inbox(limit=limit, baseline_name=baseline_name)
    HTML_OUT.parent.mkdir(parents=True, exist_ok=True)
    HTML_OUT.write_text(build_debug_inbox_html(items), encoding='utf-8')
    write_case_board(items)
    return HTML_OUT
