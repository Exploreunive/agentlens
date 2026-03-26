from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from regression import list_traces, load_trace
from analyzer import summarize_run

OUT = Path('artifacts/debug_inbox.md')


def collect_debug_inbox(limit: int = 10) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for trace_path in list_traces()[:limit]:
        events = load_trace(trace_path)
        summary = summarize_run(events)
        priority = summary.get('debug_priority', {})
        items.append(
            {
                'trace_file': trace_path.name,
                'run_id': events[0].get('run_id') if events else trace_path.stem,
                'runtime': summary.get('runtime'),
                'agent_name': summary.get('agent_name'),
                'priority_score': priority.get('score', 0),
                'priority_level': priority.get('level', 'low'),
                'priority_reasons': priority.get('reasons', []),
                'answer_risk': summary.get('answer_risk'),
                'failure_mode': summary.get('failure_mode'),
                'final_answer': summary.get('final_answer'),
                'suspicious_signals': summary.get('suspicious_signals', []),
            }
        )
    items.sort(key=lambda item: (-int(item.get('priority_score', 0)), str(item.get('trace_file'))))
    return items


def build_debug_inbox_report(items: List[Dict[str, Any]]) -> str:
    lines = ['# AgentLens Debug Inbox', '']
    if not items:
        lines.append('No traces available.')
        return '\n'.join(lines) + '\n'

    lines.append('Runs are sorted by debug priority so you can triage what to inspect first.')
    lines.append('')
    for index, item in enumerate(items, start=1):
        lines.append(f"## {index}. `{item.get('trace_file')}`")
        lines.append(f"- priority: `{item.get('priority_level')}` ({item.get('priority_score')}/100)")
        lines.append(f"- runtime: `{item.get('runtime')}`")
        lines.append(f"- agent: `{item.get('agent_name')}`")
        lines.append(f"- answer_risk: `{item.get('answer_risk')}`")
        lines.append(f"- failure_mode: `{item.get('failure_mode')}`")
        lines.append(f"- final_answer: {item.get('final_answer')}")
        lines.append(f"- suspicious_signals: {item.get('suspicious_signals')}")
        reasons = item.get('priority_reasons', [])
        if reasons:
            lines.append('- why this is prioritized:')
            for reason in reasons:
                lines.append(f"  - {reason}")
        lines.append('')
    return '\n'.join(lines)


def write_debug_inbox(limit: int = 10) -> Path:
    items = collect_debug_inbox(limit=limit)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build_debug_inbox_report(items), encoding='utf-8')
    return OUT
