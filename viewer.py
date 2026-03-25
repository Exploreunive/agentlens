from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from analyzer import summarize_run
from explain import build_failure_card

TRACE_DIR = Path('.agentlens/traces')
OUT = Path('artifacts/latest_trace.html')


def summarize_event_types(events: List[Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for event in events:
        etype = event.get('type', 'unknown')
        counts[etype] = counts.get(etype, 0) + 1
    return counts


def extract_run_metrics(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_latency_ms = 0
    total_input_tokens = 0
    total_output_tokens = 0
    total_tool_calls = 0

    for event in events:
        metrics = event.get('metrics') or {}
        total_latency_ms += int(metrics.get('latency_ms', 0) or 0)
        total_input_tokens += int(metrics.get('input_tokens', 0) or 0)
        total_output_tokens += int(metrics.get('output_tokens', 0) or 0)
        if event.get('type') == 'tool.call':
            total_tool_calls += 1

    return {
        'total_latency_ms': total_latency_ms,
        'total_input_tokens': total_input_tokens,
        'total_output_tokens': total_output_tokens,
        'total_tool_calls': total_tool_calls,
        'event_counts': summarize_event_types(events),
    }


def load_latest_trace() -> List[Dict[str, Any]]:
    files = sorted(TRACE_DIR.glob('*.jsonl'), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        raise SystemExit('No trace files found in .agentlens/traces')

    events = []
    with files[0].open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            events.append(json.loads(line))
    return events


def find_first_suspicious_index(events: List[Dict[str, Any]]) -> Optional[int]:
    for idx, event in enumerate(events):
        if event.get('status') == 'error' or event.get('type') == 'error':
            return idx
    return None


def render_event(event: Dict[str, Any], index: int, *, suspicious_index: Optional[int], failure_index: Optional[int]) -> str:
    etype_raw = event.get('type', 'unknown')
    etype = html.escape(etype_raw)
    ts = html.escape(event.get('ts', ''))
    status_raw = event.get('status', 'ok')
    status = html.escape(status_raw)
    payload = html.escape(json.dumps(event.get('payload', {}), ensure_ascii=False, indent=2))
    metrics = html.escape(json.dumps(event.get('metrics', {}), ensure_ascii=False, indent=2))

    classes = ['event']
    badges: List[str] = []

    if status_raw == 'error' or etype_raw == 'error':
        classes.append('event-error')
        badges.append('<span class="flag flag-error">error</span>')

    if suspicious_index is not None and index == suspicious_index:
        classes.append('event-first-suspicious')
        badges.append('<span class="flag flag-suspicious">first suspicious step</span>')

    if failure_index is not None and index == failure_index:
        classes.append('event-likely-failure')
        badges.append('<span class="flag flag-failure">likely failure point</span>')

    return f'''
    <div class="{' '.join(classes)}" data-event-type="{etype}">
      <div class="event-head">
        <span class="event-index">#{index}</span>
        <span class="etype">{etype}</span>
        <span class="status status-{status}">{status}</span>
        {''.join(badges)}
        <span class="ts">{ts}</span>
      </div>
      <div class="cols">
        <pre><strong>payload</strong>\n{payload}</pre>
        <pre><strong>metrics</strong>\n{metrics}</pre>
      </div>
    </div>
    '''


def build_filter_controls(event_counts: Dict[str, int]) -> str:
    items = []
    for event_type, count in sorted(event_counts.items()):
        safe_type = html.escape(str(event_type))
        items.append(
            f'<label class="filter-chip"><input type="checkbox" data-event-filter="{safe_type}" checked> '
            f'<span>{safe_type} ({count})</span></label>'
        )
    return ''.join(items)


def _truncate(value: Any, limit: int = 160) -> str:
    text = str(value)
    return text if len(text) <= limit else text[: limit - 1] + '…'


def build_html(events: List[Dict[str, Any]]) -> str:
    run_id = html.escape(events[0].get('run_id', 'unknown')) if events else 'unknown'
    summary = summarize_run(events)
    card = build_failure_card(summary)
    metrics = extract_run_metrics(events)
    failure = summary.get('likely_failure_point')
    failure_index = failure.get('event_index') if isinstance(failure, dict) else None
    suspicious_index = find_first_suspicious_index(events)
    cards = '\n'.join(
        render_event(e, idx, suspicious_index=suspicious_index, failure_index=failure_index)
        for idx, e in enumerate(events)
    )
    final_answer = html.escape(str(summary.get('final_answer')))
    notes = ''.join(f'<li>{html.escape(str(n))}</li>' for n in summary.get('notes', []))
    failure_html = html.escape(str(failure)) if failure else 'No explicit failure event detected'
    memory_items = ''.join(
        f"<li>{html.escape(m['kind'])}: {html.escape(str(m['content']))}</li>" for m in summary.get('memory_influence', [])
    ) or '<li>No memory events recorded</li>'
    suspicious_items = ''.join(
        f"<li>{html.escape(str(s.get('type')))}: {html.escape(str(s.get('reason')))}</li>" for s in summary.get('suspicious_signals', [])
    ) or '<li>No suspicious signals detected</li>'
    tool_evidence_items = ''.join(
        f"<li>#{html.escape(str(item.get('event_index')))} · {html.escape(str(item.get('tool_name')))} · {html.escape(_truncate(item.get('content')))}</li>"
        for item in summary.get('tool_evidence', [])
    ) or '<li>No tool evidence captured</li>'
    model_turn_items = ''.join(
        f"<li>#{html.escape(str(item.get('event_index')))} · {html.escape(str(item.get('kind')))} · {html.escape(_truncate(item.get('summary')))}</li>"
        for item in summary.get('model_turns', [])
    ) or '<li>No model turns recorded</li>'
    evidence_items = ''.join(f'<li>{html.escape(str(e))}</li>' for e in card.get('evidence', []))
    inspect_items = ''.join(f'<li>{html.escape(str(i))}</li>' for i in card.get('inspect_next', []))
    chain_items = ''.join(
        f"<li>#{html.escape(str(step.get('event_index')))} · {html.escape(str(step.get('kind')))} · {html.escape(str(step.get('label')))}</li>"
        for step in summary.get('failure_chain', [])
    ) or '<li>No failure chain available</li>'
    event_count_items = ''.join(
        f"<li>{html.escape(str(k))}: {html.escape(str(v))}</li>" for k, v in sorted(metrics.get('event_counts', {}).items())
    ) or '<li>No events recorded</li>'
    filter_controls = build_filter_controls(metrics.get('event_counts', {}))
    first_suspicious_text = (
        f'Event #{suspicious_index}' if suspicious_index is not None else 'No suspicious step detected'
    )
    likely_failure_text = (
        f'Event #{failure_index}' if failure_index is not None else 'No failure step detected'
    )
    runtime_label = html.escape(str(summary.get('runtime') or 'unknown'))
    agent_name = html.escape(str(summary.get('agent_name') or 'unknown'))
    return f'''<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>AgentLens Trace Viewer</title>
  <style>
    body {{ font-family: Inter, system-ui, sans-serif; background:#0b1020; color:#e8ecf3; margin:0; padding:32px; }}
    h1 {{ margin:0 0 8px 0; }}
    h2 {{ margin:0; font-size:16px; }}
    .sub {{ color:#9aa4b2; margin-bottom:24px; }}
    .event {{ border:1px solid #283043; border-radius:14px; padding:16px; margin:14px 0; background:#121a2b; }}
    .event-error {{ border-color:#7a2e2e; box-shadow:0 0 0 1px rgba(255, 93, 93, 0.15) inset; }}
    .event-first-suspicious {{ border-color:#b7791f; box-shadow:0 0 0 1px rgba(255, 196, 107, 0.18) inset; }}
    .event-likely-failure {{ border-color:#2f6feb; box-shadow:0 0 0 1px rgba(124, 196, 255, 0.18) inset; }}
    .event-head {{ display:flex; gap:12px; align-items:center; flex-wrap:wrap; margin-bottom:12px; }}
    .event-index {{ color:#9aa4b2; font-size:13px; font-weight:600; }}
    .etype {{ font-weight:700; color:#7cc4ff; }}
    .ts {{ color:#98a2b3; font-size:13px; margin-left:auto; }}
    .status {{ border-radius:999px; padding:2px 10px; font-size:12px; }}
    .status-ok {{ background:#123524; color:#7ce2a7; }}
    .status-error {{ background:#441919; color:#ff9d9d; }}
    .flag {{ border-radius:999px; padding:2px 10px; font-size:12px; font-weight:600; }}
    .flag-error {{ background:#3b1d1d; color:#ffb4b4; }}
    .flag-suspicious {{ background:#3a2d12; color:#ffd37a; }}
    .flag-failure {{ background:#132c52; color:#9fd3ff; }}
    .cols {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; }}
    .stats {{ display:grid; grid-template-columns:repeat(4, minmax(0, 1fr)); gap:12px; margin:18px 0 22px; }}
    .stat {{ background:#121a2b; border:1px solid #283043; border-radius:14px; padding:14px; }}
    .stat-label {{ color:#98a2b3; font-size:12px; margin-bottom:6px; text-transform:uppercase; letter-spacing:0.04em; }}
    .stat-value {{ font-size:24px; font-weight:700; color:#f8fafc; }}
    .trace-controls {{ display:grid; grid-template-columns:1.2fr 1fr; gap:12px; margin:0 0 18px; }}
    .overview {{ display:grid; grid-template-columns:repeat(3, minmax(0, 1fr)); gap:12px; margin:0 0 18px; }}
    .panel {{ background:#121a2b; border:1px solid #283043; border-radius:14px; padding:14px; }}
    .summary-line {{ color:#d6deeb; margin-top:10px; font-size:14px; }}
    .filter-row {{ display:flex; flex-wrap:wrap; gap:10px; margin-top:12px; }}
    .filter-chip {{ display:inline-flex; align-items:center; gap:6px; background:#0d1422; border:1px solid #283043; border-radius:999px; padding:6px 10px; font-size:13px; color:#d6deeb; }}
    .filter-chip input {{ accent-color:#7cc4ff; }}
    ul {{ margin:8px 0 0 18px; padding:0; }}
    li {{ margin:4px 0; }}
    pre {{ white-space:pre-wrap; word-break:break-word; background:#0d1422; border-radius:10px; padding:12px; overflow:auto; }}
    .hidden {{ display:none; }}
    @media (max-width: 900px) {{
      .stats, .trace-controls, .overview, .cols {{ grid-template-columns:1fr; }}
    }}
  </style>
</head>
<body>
  <h1>AgentLens Trace Viewer</h1>
  <div class="sub">Latest run: <code>{run_id}</code> · {len(events)} events</div>
  <div class="stats">
    <div class="stat">
      <div class="stat-label">total latency</div>
      <div class="stat-value">{metrics.get('total_latency_ms', 0)} ms</div>
    </div>
    <div class="stat">
      <div class="stat-label">input tokens</div>
      <div class="stat-value">{metrics.get('total_input_tokens', 0)}</div>
    </div>
    <div class="stat">
      <div class="stat-label">output tokens</div>
      <div class="stat-value">{metrics.get('total_output_tokens', 0)}</div>
    </div>
    <div class="stat">
      <div class="stat-label">tool calls</div>
      <div class="stat-value">{metrics.get('total_tool_calls', 0)}</div>
    </div>
  </div>
  <div class="trace-controls">
    <div class="panel">
      <h2>trace focus</h2>
      <div class="summary-line">first suspicious step: <strong>{html.escape(first_suspicious_text)}</strong></div>
      <div class="summary-line">likely failure step: <strong>{html.escape(likely_failure_text)}</strong></div>
    </div>
    <div class="panel">
      <h2>event filters</h2>
      <div class="filter-row">{filter_controls}</div>
    </div>
  </div>
  <div class="overview">
    <div class="panel">
      <h2>runtime overview</h2>
      <div class="summary-line">runtime: <strong>{runtime_label}</strong></div>
      <div class="summary-line">agent: <strong>{agent_name}</strong></div>
      <div class="summary-line">events: <strong>{len(events)}</strong></div>
    </div>
    <div class="panel">
      <h2>model turns</h2>
      <ul>{model_turn_items}</ul>
    </div>
    <div class="panel">
      <h2>tool evidence</h2>
      <ul>{tool_evidence_items}</ul>
    </div>
  </div>
  <div class="event">
    <div class="event-head">
      <span class="etype">failure summary</span>
    </div>
    <div class="cols">
      <pre><strong>final answer</strong>\n{final_answer}\n\n<strong>root cause</strong>\n{html.escape(str(card.get('root_cause')))}\n\n<strong>failure mode</strong>\n{html.escape(str(summary.get('failure_mode')))}\n\n<strong>answer risk</strong>\n{html.escape(str(summary.get('answer_risk')))}\n\n<strong>likely failure point</strong>\n{failure_html}</pre>
      <pre><strong>evidence</strong>\n<ul>{evidence_items}</ul>\n<strong>inspect next</strong>\n<ul>{inspect_items}</ul>\n<strong>failure chain</strong>\n<ul>{chain_items}</ul>\n<strong>notes</strong>\n<ul>{notes}</ul>\n<strong>memory influence</strong>\n<ul>{memory_items}</ul>\n<strong>suspicious signals</strong>\n<ul>{suspicious_items}</ul>\n<strong>event counts</strong>\n<ul>{event_count_items}</ul></pre>
    </div>
  </div>
  <div id="trace-events">
    {cards}
  </div>
  <script>
    const filters = Array.from(document.querySelectorAll('[data-event-filter]'));
    const eventsEls = Array.from(document.querySelectorAll('[data-event-type]'));

    function syncFilters() {{
      const enabled = new Set(
        filters.filter((input) => input.checked).map((input) => input.getAttribute('data-event-filter'))
      );
      for (const el of eventsEls) {{
        const eventType = el.getAttribute('data-event-type');
        el.classList.toggle('hidden', !enabled.has(eventType));
      }}
    }}

    for (const input of filters) {{
      input.addEventListener('change', syncFilters);
    }}

    syncFilters();
  </script>
</body>
</html>'''


def main() -> None:
    events = load_latest_trace()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build_html(events), encoding='utf-8')
    print(f'Wrote {OUT}')


if __name__ == '__main__':
    main()
