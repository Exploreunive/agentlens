from __future__ import annotations

from typing import Any, Dict, List, Optional


def summarize_run(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    summary: Dict[str, Any] = {
        'final_answer': None,
        'likely_failure_point': None,
        'memory_influence': [],
        'tool_sequence': [],
        'suspicious_signals': [],
        'notes': [],
    }

    for idx, e in enumerate(events):
        et = e.get('type')
        payload = e.get('payload') or {}

        if et == 'tool.call':
            tool_name = payload.get('tool_name')
            if tool_name:
                summary['tool_sequence'].append(tool_name)

        if et == 'memory.write':
            content = payload.get('content')
            if content:
                summary['memory_influence'].append({
                    'kind': 'write',
                    'content': content,
                    'event_index': idx,
                })

        if et == 'memory.recall':
            content = payload.get('content')
            if content:
                summary['memory_influence'].append({
                    'kind': 'recall',
                    'content': content,
                    'event_index': idx,
                })

        if et == 'error':
            summary['suspicious_signals'].append({
                'event_index': idx,
                'type': payload.get('kind') or 'error',
                'reason': payload.get('message') or 'error event emitted',
            })
            if summary['likely_failure_point'] is None:
                summary['likely_failure_point'] = {
                    'event_index': idx,
                    'type': 'error',
                    'reason': payload.get('message') or 'error event emitted',
                }

        if et == 'run.end':
            summary['final_answer'] = payload.get('final_answer')

    if summary['likely_failure_point'] is None:
        recall_events = [m for m in summary['memory_influence'] if m['kind'] == 'recall']
        if recall_events:
            summary['notes'].append('Memory recall occurred; verify whether recalled memory was relevant.')
        if summary['tool_sequence']:
            summary['notes'].append('Inspect tool outputs if final answer quality looks wrong.')
        if not summary['notes']:
            summary['notes'].append('No explicit failure signal found; inspect decision quality manually.')

    return summary


def summarize_divergence(a: List[Dict[str, Any]], b: List[Dict[str, Any]]) -> Dict[str, Any]:
    max_len = min(len(a), len(b))
    divergence = None
    for i in range(max_len):
        ea, eb = a[i], b[i]
        if ea.get('type') != eb.get('type') or (ea.get('payload') or {}) != (eb.get('payload') or {}):
            divergence = {
                'event_index': i,
                'a_type': ea.get('type'),
                'b_type': eb.get('type'),
                'a_payload': ea.get('payload') or {},
                'b_payload': eb.get('payload') or {},
            }
            break

    if divergence is None and len(a) != len(b):
        divergence = {
            'event_index': max_len,
            'a_type': a[max_len].get('type') if len(a) > max_len else None,
            'b_type': b[max_len].get('type') if len(b) > max_len else None,
            'a_payload': a[max_len].get('payload') if len(a) > max_len else {},
            'b_payload': b[max_len].get('payload') if len(b) > max_len else {},
        }

    a_summary = summarize_run(a)
    b_summary = summarize_run(b)
    return {
        'first_divergence': divergence,
        'a_final_answer': a_summary.get('final_answer'),
        'b_final_answer': b_summary.get('final_answer'),
        'a_suspicious_signals': a_summary.get('suspicious_signals', []),
        'b_suspicious_signals': b_summary.get('suspicious_signals', []),
    }
