from __future__ import annotations

import html
from collections import Counter
from pathlib import Path
from typing import Any, Optional

from bundle_export import export_bundle

CASEFILES_DIR = Path('artifacts/cases')
CASE_BOARD_OUT = CASEFILES_DIR / 'index.html'


def case_dir_path(trace_name: str) -> Path:
    return CASEFILES_DIR / Path(trace_name).stem


def write_case_index(
    *,
    trace_name: str,
    trace_view_path: str,
    final_answer: str | None,
    priority_level: str,
    priority_score: int,
    baseline_name: Optional[str] = None,
    regression_report_path: Optional[str] = None,
) -> Path:
    case_dir = case_dir_path(trace_name)
    case_dir.mkdir(parents=True, exist_ok=True)

    bundle_path = export_bundle(trace_name, include_diff=True)
    lines = [
        '# AgentLens Case File',
        '',
        f'- trace: `{trace_name}`',
        f'- priority: `{priority_level}` ({priority_score}/100)',
        f'- final_answer: {final_answer}',
        f'- trace_view: `{trace_view_path}`',
        f'- bundle: `{bundle_path}`',
    ]
    if baseline_name:
        lines.append(f'- baseline_watch: `{baseline_name}`')
    if regression_report_path:
        lines.append(f'- regression_report: `{regression_report_path}`')

    lines += [
        '',
        '## Share Checklist',
        '- Open the trace view first.',
        '- Read the regression report if baseline watch is enabled.',
        '- Share the bundle zip when someone else needs the full artifact set.',
        '',
    ]

    out = case_dir / 'README.md'
    out.write_text('\n'.join(lines), encoding='utf-8')
    return out


def build_case_board_html(items: list[dict[str, Any]]) -> str:
    regressions = [item for item in items if item.get('regression_detected')]
    top_cases = sorted(items, key=lambda item: (-int(item.get('priority_score', 0)), str(item.get('trace_file'))))[:6]
    fingerprints = Counter(item.get('failure_mode') or 'unknown_failure' for item in items)
    fingerprint_cards = ''.join(
        f'''
        <div class="mini-card">
          <div class="mini-label">Failure Fingerprint</div>
          <div class="mini-value">{html.escape(str(mode))}</div>
          <div class="mini-meta">{count} case(s)</div>
        </div>
        '''
        for mode, count in fingerprints.most_common(6)
    ) or '<div class="empty">No failure fingerprints yet.</div>'

    case_cards = ''.join(
        f'''
        <section class="case-card level-{html.escape(str(item.get("priority_level", "low")))}">
          <div class="case-head">
            <div>
              <div class="eyebrow">{'Regression case' if item.get('regression_detected') else 'Incident case'}</div>
              <h2>{html.escape(str(item.get('trace_file')))}</h2>
            </div>
            <div class="score">{html.escape(str(item.get('priority_score', 0)))}</div>
          </div>
          <div class="meta">
            <span>failure: <strong>{html.escape(str(item.get('failure_mode') or 'unknown'))}</strong></span>
            <span>risk: <strong>{html.escape(str(item.get('answer_risk') or 'unknown'))}</strong></span>
            <span>baseline: <strong>{html.escape('regressed' if item.get('regression_detected') else 'clean')}</strong></span>
          </div>
          <div class="answer">{html.escape(str(item.get('final_answer') or 'No final answer captured.'))}</div>
          <ul>
            <li>Case file: <code>{html.escape(str(item.get('case_index_path') or ''))}</code></li>
            <li>Trace page: <code>{html.escape(str(item.get('trace_view_path') or ''))}</code></li>
            <li>Regression report: <code>{html.escape(str(item.get('regression_report_path') or 'n/a'))}</code></li>
          </ul>
        </section>
        '''
        for item in top_cases
    ) or '<div class="empty">No cases available.</div>'

    return f'''<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>AgentLens Incident Board</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #07101d;
      --panel: rgba(14, 24, 40, 0.92);
      --border: #22324f;
      --text: #edf3fb;
      --muted: #9fb0c8;
      --accent: #7cc4ff;
      --high: #ff8a65;
      --medium: #ffd166;
      --low: #6dd3a0;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: ui-sans-serif, system-ui, sans-serif; background: radial-gradient(circle at top, #132440 0%, var(--bg) 60%); color: var(--text); }}
    main {{ max-width: 1200px; margin: 0 auto; padding: 40px 24px 64px; }}
    h1, h2, h3 {{ margin: 0; }}
    p {{ color: var(--muted); line-height: 1.6; }}
    .hero {{ display: grid; gap: 18px; margin-bottom: 26px; }}
    .stats {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; }}
    .stat, .section, .case-card, .mini-card {{ background: var(--panel); border: 1px solid var(--border); border-radius: 18px; }}
    .stat {{ padding: 18px; }}
    .stat-label {{ color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; }}
    .stat-value {{ margin-top: 8px; font-size: 28px; font-weight: 800; }}
    .layout {{ display: grid; grid-template-columns: 1.2fr 2fr; gap: 16px; }}
    .section {{ padding: 18px; }}
    .mini-grid {{ display: grid; gap: 12px; }}
    .mini-card {{ padding: 14px; }}
    .mini-label {{ color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; }}
    .mini-value {{ margin-top: 8px; font-size: 18px; font-weight: 700; }}
    .mini-meta {{ margin-top: 6px; color: var(--muted); }}
    .case-stack {{ display: grid; gap: 14px; }}
    .case-card {{ padding: 18px; }}
    .case-head {{ display: flex; justify-content: space-between; gap: 12px; align-items: start; }}
    .eyebrow {{ color: var(--accent); font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px; }}
    .score {{ min-width: 58px; height: 58px; border-radius: 16px; display: grid; place-items: center; font-size: 22px; font-weight: 800; background: #0d1728; border: 1px solid var(--border); }}
    .meta {{ display: flex; flex-wrap: wrap; gap: 10px 16px; margin: 14px 0; color: var(--muted); }}
    .answer {{ padding: 12px 14px; border-radius: 14px; background: #0c1524; border: 1px solid var(--border); line-height: 1.6; white-space: pre-wrap; }}
    ul {{ margin: 14px 0 0; padding-left: 18px; color: var(--muted); }}
    li {{ margin: 8px 0; }}
    code {{ color: var(--accent); font-family: ui-monospace, SFMono-Regular, monospace; }}
    .level-high .score {{ border-color: rgba(255, 138, 101, 0.55); }}
    .level-medium .score {{ border-color: rgba(255, 209, 102, 0.55); }}
    .level-low .score {{ border-color: rgba(109, 211, 160, 0.55); }}
    .empty {{ color: var(--muted); }}
    @media (max-width: 900px) {{
      .stats, .layout {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <div>
        <h1>AgentLens Incident Board</h1>
        <p>The board for repeated agent failures, regressions, and the next cases worth debugging.</p>
      </div>
      <div class="stats">
        <div class="stat"><div class="stat-label">Cases</div><div class="stat-value">{len(items)}</div></div>
        <div class="stat"><div class="stat-label">Regressions</div><div class="stat-value">{len(regressions)}</div></div>
        <div class="stat"><div class="stat-label">High Priority</div><div class="stat-value">{sum(1 for item in items if item.get('priority_level') == 'high')}</div></div>
        <div class="stat"><div class="stat-label">Fingerprints</div><div class="stat-value">{len(fingerprints)}</div></div>
      </div>
    </section>
    <section class="layout">
      <div class="section">
        <h2>Recurring Failure Modes</h2>
        <p>Fingerprint clustering for the problems that keep showing up across runs.</p>
        <div class="mini-grid">{fingerprint_cards}</div>
      </div>
      <div class="section">
        <h2>Top Cases</h2>
        <p>Start with the highest-value incidents first, especially baseline regressions.</p>
        <div class="case-stack">{case_cards}</div>
      </div>
    </section>
  </main>
</body>
</html>
'''


def write_case_board(items: list[dict[str, Any]]) -> Path:
    CASEFILES_DIR.mkdir(parents=True, exist_ok=True)
    CASE_BOARD_OUT.write_text(build_case_board_html(items), encoding='utf-8')
    return CASE_BOARD_OUT
