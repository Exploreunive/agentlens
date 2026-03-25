from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_viewer_contains_failure_summary_and_suspicious_signals(tmp_path: Path):
    work = tmp_path / 'proj'
    shutil.copytree(ROOT, work)

    subprocess.run([sys.executable, 'examples/divergent_agent.py'], cwd=work, check=True)
    subprocess.run([sys.executable, 'viewer.py'], cwd=work, check=True)

    html_file = work / 'artifacts' / 'latest_trace.html'
    html = html_file.read_text(encoding='utf-8')
    assert 'failure summary' in html
    assert 'suspicious signals' in html
    assert 'memory_conflict' in html
    assert 'total latency' in html
    assert 'input tokens' in html
    assert 'tool calls' in html
    assert '<strong>event counts</strong>' in html
    assert 'first suspicious step' in html
    assert 'likely failure step' in html
    assert 'event filters' in html
    assert 'data-event-filter="error"' in html
    assert 'data-event-filter="memory.recall"' in html
    assert 'first suspicious step: <strong>Event #' in html
    assert 'likely failure step: <strong>Event #' in html
    assert 'flag-suspicious' in html
    assert 'flag-failure' in html
    assert '<strong>failure mode</strong>' in html
    assert '<strong>answer risk</strong>' in html
    assert '<strong>failure chain</strong>' in html


def test_viewer_contains_runtime_overview_for_langgraph_like_trace():
    from viewer import build_html

    html = build_html([
        {'type': 'run.start', 'run_id': 'run-lg', 'payload': {'runtime': 'langgraph', 'agent_name': 'weather_agent'}},
        {'type': 'llm.response', 'run_id': 'run-lg', 'payload': {'tool_calls': [{'name': 'weather_snapshot', 'id': 'call_1'}], 'decision': 'tool_calls=weather_snapshot'}},
        {'type': 'tool.call', 'run_id': 'run-lg', 'payload': {'tool_name': 'weather_snapshot', 'tool_call_id': 'call_1', 'args': {'city': 'Shanghai'}}},
        {'type': 'tool.result', 'run_id': 'run-lg', 'payload': {'tool_call_id': 'call_1', 'content': 'Shanghai: rain'}},
        {'type': 'run.end', 'run_id': 'run-lg', 'payload': {'final_answer': 'Skip the jog.'}},
    ])

    assert 'runtime overview' in html
    assert 'model turns' in html
    assert 'tool evidence' in html
    assert 'langgraph' in html
    assert 'weather_snapshot' in html


def test_load_latest_trace_prefers_most_recent_file(tmp_path: Path):
    from viewer import load_latest_trace

    previous_cwd = Path.cwd()
    try:
        import os
        os.chdir(tmp_path)
        traces = Path('.agentlens/traces')
        traces.mkdir(parents=True)
        older = traces / 'older.jsonl'
        newer = traces / 'newer.jsonl'
        older.write_text(json.dumps({'run_id': 'older', 'type': 'error', 'payload': {'kind': 'memory_conflict'}}) + '\n', encoding='utf-8')
        newer.write_text(json.dumps({'run_id': 'newer', 'type': 'run.start', 'payload': {'runtime': 'langgraph'}}) + '\n', encoding='utf-8')
        events = load_latest_trace()
    finally:
        os.chdir(previous_cwd)

    assert events[0]['run_id'] == 'newer'
