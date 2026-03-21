from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any, Dict, List

from analyzer import summarize_run
from explain import build_failure_card

TRACE_DIR = Path('.agentlens/traces')
OUT = Path('artifacts/latest_trace.html')


def load_latest_trace() -> List[Dict[str, Any]]:
    files = sorted(TRACE_DIR.glob('*.jsonl'), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        raise SystemExit('No trace files found in .agentlens/traces')
    latest = files[0]
    events = []
    with latest.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            events.append(json.loads(line))
    return events


def render_event(event: Dict[str, Any]) -> str:
    etype = html.escape(event.get('type', 'unknown'))
    ts = html.escape(event.get('ts', ''))
    status = html.escape(event.get('status', 'ok'))
    payload = html.escape(json.dumps(event.get('payload', {}), ensure_ascii=False, indent=2))
    metrics = html.escape(json.dumps(event.get('metrics', {}), ensure_ascii=False, indent=2))
    return f'''
    <div class="event">
      <div class="event-head">
        <span class="etype">{etype}</span>
        <span class="status status-{status}">{status}</span>
        <span class="ts">{ts}</span>
      </div>
      <div class="cols">
        <pre><strong>payload</strong>\n{payload}</pre>
        <pre><strong>metrics</strong>\n{metrics}</pre>
      </div>
    </div>
    '''


def build_html(events: List[Dict[str, Any]]) -> str:
    run_id = html.escape(events[0].get('run_id', 'unknown')) if events else 'unknown'
    cards = '\n'.join(render_event(e) for e in events)
    summary = summarize_run(events)
    card = build_failure_card(summary)
    final_answer = html.escape(str(summary.get('final_answer')))
    notes = ''.join(f'<li>{html.escape(str(n))}</li>' for n in summary.get('notes', []))
    failure = summary.get('likely_failure_point')
    failure_html = html.escape(str(failure)) if failure else 'No explicit failure event detected'
    memory_items = ''.join(
        f"<li>{html.escape(m['kind'])}: {html.escape(str(m['content']))}</li>" for m in summary.get('memory_influence', [])
    ) or '<li>No memory events recorded</li>'
    suspicious_items = ''.join(
        f"<li>{html.escape(str(s.get('type')))}: {html.escape(str(s.get('reason')))}</li>" for s in summary.get('suspicious_signals', [])
    ) or '<li>No suspicious signals detected</li>'
    evidence_items = ''.join(f'<li>{html.escape(str(e))}</li>' for e in card.get('evidence', []))
    inspect_items = ''.join(f'<li>{html.escape(str(i))}</li>' for i in card.get('inspect_next', []))
    return f'''<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>AgentLens Trace Viewer</title>
  <style>
    body {{ font-family: Inter, system-ui, sans-serif; background:#0b1020; color:#e8ecf3; margin:0; padding:32px; }}
    h1 {{ margin:0 0 8px 0; }}
    .sub {{ color:#9aa4b2; margin-bottom:24px; }}
    .event {{ border:1px solid #283043; border-radius:14px; padding:16px; margin:14px 0; background:#121a2b; }}
    .event-head {{ display:flex; gap:12px; align-items:center; flex-wrap:wrap; margin-bottom:12px; }}
    .etype {{ font-weight:700; color:#7cc4ff; }}
    .ts {{ color:#98a2b3; font-size:13px; }}
    .status {{ border-radius:999px; padding:2px 10px; font-size:12px; }}
    .status-ok {{ background:#123524; color:#7ce2a7; }}
    .status-error {{ background:#441919; color:#ff9d9d; }}
    .cols {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; }}
    pre {{ white-space:pre-wrap; word-break:break-word; background:#0d1422; border-radius:10px; padding:12px; overflow:auto; }}
  </style>
</head>
<body>
  <h1>AgentLens Trace Viewer</h1>
  <div class="sub">Latest run: <code>{run_id}</code> · {len(events)} events</div>
  <div class="event">
    <div class="event-head">
      <span class="etype">failure summary</span>
    </div>
    <div class="cols">
      <pre><strong>final answer</strong>\n{final_answer}\n\n<strong>root cause</strong>\n{html.escape(str(card.get('root_cause')))}\n\n<strong>likely failure point</strong>\n{failure_html}</pre>
      <pre><strong>evidence</strong>\n<ul>{evidence_items}</ul>\n<strong>inspect next</strong>\n<ul>{inspect_items}</ul>\n<strong>notes</strong>\n<ul>{notes}</ul>\n<strong>memory influence</strong>\n<ul>{memory_items}</ul>\n<strong>suspicious signals</strong>\n<ul>{suspicious_items}</ul></pre>
    </div>
  </div>
  {cards}
</body>
</html>'''


def main() -> None:
    events = load_latest_trace()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build_html(events), encoding='utf-8')
    print(f'Wrote {OUT}')


if __name__ == '__main__':
    main()
