from __future__ import annotations

import json
from pathlib import Path

from debug_inbox import build_debug_inbox_html, build_debug_inbox_report, collect_debug_inbox, write_debug_inbox, write_debug_inbox_html


def test_build_debug_inbox_report_contains_priority_sections():
    report = build_debug_inbox_report([
        {
            'trace_file': 'run-a.jsonl',
            'runtime': 'langgraph',
            'agent_name': 'weather_agent',
            'priority_score': 82,
            'priority_level': 'high',
            'priority_reasons': ['Suspicious signals were emitted during the run.'],
            'answer_risk': 'visible_failure',
            'failure_mode': 'memory_vs_tool_conflict',
            'final_answer': 'Jog is fine.',
            'suspicious_signals': [{'type': 'memory_conflict'}],
        }
    ])
    assert '# AgentLens Debug Inbox' in report
    assert 'priority: `high` (82/100)' in report
    assert 'why this is prioritized' in report


def test_build_debug_inbox_html_contains_cards():
    html = build_debug_inbox_html([
        {
            'trace_file': 'run-a.jsonl',
            'runtime': 'langgraph',
            'agent_name': 'weather_agent',
            'priority_score': 82,
            'priority_level': 'high',
            'priority_reasons': ['Suspicious signals were emitted during the run.'],
            'answer_risk': 'visible_failure',
            'failure_mode': 'memory_vs_tool_conflict',
            'final_answer': 'Jog is fine.',
            'suspicious_signals': [{'type': 'memory_conflict', 'event_index': 7}],
        }
    ])
    assert '<title>AgentLens Debug Inbox</title>' in html
    assert 'Recent traces ranked by debugging value' in html
    assert 'run-a.jsonl' in html


def test_collect_debug_inbox_sorts_by_priority_score(tmp_path: Path):
    previous_cwd = Path.cwd()
    try:
        import os
        os.chdir(tmp_path)
        traces = Path('.agentlens/traces')
        traces.mkdir(parents=True)
        (traces / 'low.jsonl').write_text(
            '\n'.join([
                json.dumps({'run_id': 'low', 'type': 'run.start', 'payload': {}}),
                json.dumps({'run_id': 'low', 'type': 'run.end', 'payload': {'final_answer': 'All good.'}}),
            ]) + '\n',
            encoding='utf-8',
        )
        (traces / 'high.jsonl').write_text(
            '\n'.join([
                json.dumps({'run_id': 'high', 'type': 'run.start', 'payload': {}}),
                json.dumps({'run_id': 'high', 'type': 'error', 'payload': {'kind': 'memory_conflict', 'message': 'bad recall'}}),
                json.dumps({'run_id': 'high', 'type': 'run.end', 'payload': {'final_answer': 'Jog is fine.'}}),
            ]) + '\n',
            encoding='utf-8',
        )
        items = collect_debug_inbox(limit=10)
    finally:
        os.chdir(previous_cwd)

    assert items[0]['run_id'] == 'high'
    assert items[0]['priority_score'] >= items[1]['priority_score']


def test_write_debug_inbox_creates_report(tmp_path: Path):
    previous_cwd = Path.cwd()
    try:
        import os
        os.chdir(tmp_path)
        traces = Path('.agentlens/traces')
        traces.mkdir(parents=True)
        (traces / 'demo.jsonl').write_text(
            '\n'.join([
                json.dumps({'run_id': 'demo', 'type': 'run.start', 'payload': {}}),
                json.dumps({'run_id': 'demo', 'type': 'run.end', 'payload': {'final_answer': 'ok'}}),
            ]) + '\n',
            encoding='utf-8',
        )
        out = write_debug_inbox()
    finally:
        os.chdir(previous_cwd)

    assert out.exists()
    assert 'AgentLens Debug Inbox' in out.read_text(encoding='utf-8')


def test_write_debug_inbox_html_creates_report(tmp_path: Path):
    previous_cwd = Path.cwd()
    try:
        import os
        os.chdir(tmp_path)
        traces = Path('.agentlens/traces')
        traces.mkdir(parents=True)
        (traces / 'demo.jsonl').write_text(
            '\n'.join([
                json.dumps({'run_id': 'demo', 'type': 'run.start', 'payload': {}}),
                json.dumps({'run_id': 'demo', 'type': 'run.end', 'payload': {'final_answer': 'ok'}}),
            ]) + '\n',
            encoding='utf-8',
        )
        out = write_debug_inbox_html()
    finally:
        os.chdir(previous_cwd)

    assert out.exists()
    assert 'AgentLens Debug Inbox' in out.read_text(encoding='utf-8')
