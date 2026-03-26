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
            'failure_fingerprint': {'label': 'memory-vs-tool-conflict', 'id': 'memory_conflict|memory_involved'},
            'final_answer': 'Jog is fine.',
            'suspicious_signals': [{'type': 'memory_conflict'}],
            'baseline_name': 'golden',
            'regression_detected': True,
            'regression_reasons': ['Candidate emits more suspicious signals than the baseline.'],
            'trace_view_path': 'artifacts/views/run-a.html',
            'case_index_path': 'artifacts/cases/run-a/README.md',
            'regression_report_path': 'artifacts/regressions/golden__run-a.md',
        }
    ])
    assert '# AgentLens Debug Inbox' in report
    assert 'priority: `high` (82/100)' in report
    assert 'why this is prioritized' in report
    assert 'baseline_watch: `golden` -> regression=`True`' in report
    assert 'trace_view: `artifacts/views/run-a.html`' in report
    assert 'case_file: `artifacts/cases/run-a/README.md`' in report
    assert 'regression_report: `artifacts/regressions/golden__run-a.md`' in report


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
            'failure_fingerprint': {'label': 'memory-vs-tool-conflict', 'id': 'memory_conflict|memory_involved'},
            'final_answer': 'Jog is fine.',
            'suspicious_signals': [{'type': 'memory_conflict', 'event_index': 7}],
            'baseline_name': 'golden',
            'regression_detected': True,
            'regression_reasons': ['Final answer changed relative to the baseline.'],
            'trace_view_path': 'artifacts/views/run-a.html',
            'case_index_path': 'artifacts/cases/run-a/README.md',
            'regression_report_path': 'artifacts/regressions/golden__run-a.md',
        }
    ])
    assert '<title>AgentLens Debug Inbox</title>' in html
    assert 'Recent traces ranked by debugging value' in html
    assert 'run-a.jsonl' in html
    assert 'regressed' in html
    assert 'artifacts/views/run-a.html' in html
    assert 'artifacts/cases/run-a/README.md' in html
    assert 'artifacts/regressions/golden__run-a.md' in html


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


def test_collect_debug_inbox_surfaces_regressions_when_baseline_is_present(tmp_path: Path):
    previous_cwd = Path.cwd()
    try:
        import os
        os.chdir(tmp_path)
        traces = Path('.agentlens/traces')
        traces.mkdir(parents=True)
        baseline_trace = traces / 'baseline.jsonl'
        baseline_trace.write_text(
            '\n'.join([
                json.dumps({'run_id': 'baseline', 'type': 'run.start', 'payload': {}}),
                json.dumps({'run_id': 'baseline', 'type': 'run.end', 'payload': {'final_answer': 'Skip jogging.'}}),
            ]) + '\n',
            encoding='utf-8',
        )
        baselines = Path('.agentlens/baselines')
        baselines.mkdir(parents=True)
        (baselines / 'golden.json').write_text(
            json.dumps({'name': 'golden', 'trace_file': 'baseline.jsonl'}),
            encoding='utf-8',
        )
        (traces / 'candidate.jsonl').write_text(
            '\n'.join([
                json.dumps({'run_id': 'candidate', 'type': 'run.start', 'payload': {}}),
                json.dumps({'run_id': 'candidate', 'type': 'error', 'payload': {'kind': 'memory_conflict', 'message': 'bad recall'}}),
                json.dumps({'run_id': 'candidate', 'type': 'run.end', 'payload': {'final_answer': 'Jog is fine.'}}),
            ]) + '\n',
            encoding='utf-8',
        )
        items = collect_debug_inbox(limit=10, baseline_name='golden')
    finally:
        os.chdir(previous_cwd)

    assert items[0]['trace_file'] == 'candidate.jsonl'
    assert items[0]['regression_detected'] is True
    assert items[0]['baseline_name'] == 'golden'
    assert items[0]['trace_view_path'].endswith('candidate.html')
    assert items[0]['case_index_path'].endswith('candidate/README.md')
    assert items[0]['case_status'] == 'new'
    assert items[0]['regression_report_path'].endswith('golden__candidate.md')


def test_collect_debug_inbox_skips_regression_report_for_non_comparable_run(tmp_path: Path):
    previous_cwd = Path.cwd()
    try:
        import os
        os.chdir(tmp_path)
        traces = Path('.agentlens/traces')
        traces.mkdir(parents=True)
        baseline_trace = traces / 'baseline.jsonl'
        baseline_trace.write_text(
            '\n'.join([
                json.dumps({'run_id': 'baseline', 'type': 'run.start', 'payload': {'runtime': 'langgraph', 'agent_name': 'weather_agent'}}),
                json.dumps({'run_id': 'baseline', 'type': 'run.end', 'payload': {'final_answer': 'Skip jogging.'}}),
            ]) + '\n',
            encoding='utf-8',
        )
        baselines = Path('.agentlens/baselines')
        baselines.mkdir(parents=True)
        (baselines / 'golden.json').write_text(
            json.dumps({'name': 'golden', 'trace_file': 'baseline.jsonl'}),
            encoding='utf-8',
        )
        (traces / 'candidate.jsonl').write_text(
            '\n'.join([
                json.dumps({'run_id': 'candidate', 'type': 'run.start', 'payload': {'runtime': 'custom', 'agent_name': 'weather_agent'}}),
                json.dumps({'run_id': 'candidate', 'type': 'run.end', 'payload': {'final_answer': 'Different domain answer.'}}),
            ]) + '\n',
            encoding='utf-8',
        )
        items = collect_debug_inbox(limit=10, baseline_name='golden')
    finally:
        os.chdir(previous_cwd)

    candidate_item = next(item for item in items if item['trace_file'] == 'candidate.jsonl')
    assert candidate_item['regression_detected'] is False
    assert candidate_item['regression_report_path'] is None
    assert 'Runtime differs' in candidate_item['regression_reasons'][0]


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
    assert (tmp_path / 'artifacts' / 'views' / 'demo.html').exists()
    assert (tmp_path / 'artifacts' / 'cases' / 'demo' / 'README.md').exists()
    assert (tmp_path / 'artifacts' / 'cases' / 'index.html').exists()


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
