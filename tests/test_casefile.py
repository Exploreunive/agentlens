from __future__ import annotations

import json
from pathlib import Path

from casefile import (
    build_case_board_html,
    parse_case_metadata,
    parse_case_status,
    update_case_index,
    write_case_board,
    write_case_index,
)


def test_write_case_index_creates_shareable_readme(tmp_path: Path):
    previous_cwd = Path.cwd()
    try:
        import os
        os.chdir(tmp_path)
        traces = Path('.agentlens/traces')
        traces.mkdir(parents=True)
        (traces / 'demo.jsonl').write_text(
            '\n'.join([
                json.dumps({'run_id': 'run-123', 'type': 'run.start', 'payload': {}}),
                json.dumps({'run_id': 'run-123', 'type': 'run.end', 'payload': {'final_answer': 'ok'}}),
            ]) + '\n',
            encoding='utf-8',
        )
        out = write_case_index(
            trace_name='demo.jsonl',
            trace_view_path='artifacts/views/demo.html',
            final_answer='ok',
            priority_level='high',
            priority_score=90,
            failure_mode='wrong_tool_selected',
            baseline_name='golden',
            regression_report_path='artifacts/regressions/golden__demo.md',
        )
    finally:
        os.chdir(previous_cwd)

    assert out == Path('artifacts/cases/demo/README.md')
    text = (tmp_path / out).read_text(encoding='utf-8')
    assert 'AgentLens Case File' in text
    assert '- status: `new`' in text
    assert '- owner: `unassigned`' in text
    assert 'artifacts/views/demo.html' in text
    assert 'artifacts/regressions/golden__demo.md' in text
    assert parse_case_status(tmp_path / out) == 'new'
    assert parse_case_metadata(tmp_path / out)['owner'] == 'unassigned'


def test_write_case_index_preserves_existing_metadata(tmp_path: Path):
    previous_cwd = Path.cwd()
    try:
        import os
        os.chdir(tmp_path)
        readme = tmp_path / 'artifacts' / 'cases' / 'demo' / 'README.md'
        readme.parent.mkdir(parents=True)
        readme.write_text(
            '\n'.join([
                '# AgentLens Case File',
                '',
                '- trace: `demo.jsonl`',
                '- status: `investigating`',
                '- owner: `alice`',
                '- next_step: `Replay the failing tool call with fixture inputs.`',
            ]) + '\n',
            encoding='utf-8',
        )
        traces = Path('.agentlens/traces')
        traces.mkdir(parents=True)
        (traces / 'demo.jsonl').write_text(
            '\n'.join([
                json.dumps({'run_id': 'run-123', 'type': 'run.start', 'payload': {}}),
                json.dumps({'run_id': 'run-123', 'type': 'run.end', 'payload': {'final_answer': 'ok'}}),
            ]) + '\n',
            encoding='utf-8',
        )
        out = write_case_index(
            trace_name='demo.jsonl',
            trace_view_path='artifacts/views/demo.html',
            final_answer='ok',
            priority_level='high',
            priority_score=90,
            failure_mode='wrong_tool_selected',
        )
    finally:
        os.chdir(previous_cwd)

    metadata = parse_case_metadata(tmp_path / out)
    assert metadata['status'] == 'investigating'
    assert metadata['owner'] == 'alice'
    assert metadata['next_step'] == 'Replay the failing tool call with fixture inputs.'


def test_update_case_index_updates_owner_status_and_next_step(tmp_path: Path):
    readme = tmp_path / 'artifacts' / 'cases' / 'demo' / 'README.md'
    readme.parent.mkdir(parents=True)
    readme.write_text(
        '\n'.join([
            '# AgentLens Case File',
            '',
            '- trace: `demo.jsonl`',
            '- status: `new`',
            '- owner: `unassigned`',
            '- next_step: `Open the trace.`',
        ]) + '\n',
        encoding='utf-8',
    )
    previous_cwd = Path.cwd()
    try:
        import os
        os.chdir(tmp_path)
        out = update_case_index('demo', status='investigating', owner='alice', next_step='Replay the failing branch.')
    finally:
        os.chdir(previous_cwd)

    assert out == Path('artifacts/cases/demo/README.md')
    metadata = parse_case_metadata(tmp_path / out)
    assert metadata == {
        'status': 'investigating',
        'owner': 'alice',
        'next_step': 'Replay the failing branch.',
    }


def test_build_case_board_html_contains_summary_cards():
    html = build_case_board_html(
        [
            {
                'trace_file': 'run-a.jsonl',
                'trace_recency_rank': 1,
                'priority_score': 90,
                'priority_level': 'high',
                'failure_mode': 'memory_vs_tool_conflict',
                'failure_fingerprint': {'label': 'memory-vs-tool-conflict', 'id': 'memory_conflict|memory_involved'},
                'answer_risk': 'hidden_degradation',
                'final_answer': 'Jog is fine.',
                'regression_detected': True,
                'case_status': 'investigating',
                'case_owner': 'alice',
                'case_next_step': 'Replay the wrong tool selection.',
                'case_index_path': 'artifacts/cases/run-a/README.md',
                'trace_view_path': 'artifacts/views/run-a.html',
                'regression_report_path': 'artifacts/regressions/golden__run-a.md',
            }
        ],
        benchmark_gate={
            'coverage': {'fixtures': 5, 'matched': 5, 'partial': 0, 'missed': 0},
            'baseline_name': 'local-bench',
            'regressions': 0,
            'regressed_fixtures': [],
            'report_path': 'artifacts/benchmark_report.md',
            'regression_report_path': 'artifacts/benchmark_regression.md',
        },
    )
    assert 'AgentLens Incident Board' in html
    assert 'Action Queue' in html
    assert 'Recurring Issue Leaderboard' in html
    assert 'Trend Watch' in html
    assert 'Benchmark Gate' in html
    assert 'local-bench' in html
    assert 'memory-vs-tool-conflict' in html
    assert 'status mix: investigating=1' in html.lower()
    assert 'cases 1' in html
    assert 'unresolved 1' in html
    assert 'matched 5' in html
    assert 'baseline regression' in html
    assert 'owner alice' in html
    assert 'Replay the wrong tool selection.' in html


def test_write_case_board_creates_index(tmp_path: Path):
    previous_cwd = Path.cwd()
    try:
        import os
        os.chdir(tmp_path)
        out = write_case_board([
            {
                'trace_file': 'run-a.jsonl',
                'trace_recency_rank': 1,
                'priority_score': 90,
                'priority_level': 'high',
                'failure_mode': 'memory_vs_tool_conflict',
                'failure_fingerprint': {'label': 'memory-vs-tool-conflict', 'id': 'memory_conflict|memory_involved'},
                'answer_risk': 'hidden_degradation',
                'final_answer': 'Jog is fine.',
                'regression_detected': True,
                'case_status': 'new',
                'case_owner': 'alice',
                'case_next_step': 'Replay the wrong tool selection.',
                'case_index_path': 'artifacts/cases/run-a/README.md',
                'trace_view_path': 'artifacts/views/run-a.html',
                'regression_report_path': 'artifacts/regressions/golden__run-a.md',
            }
        ])
    finally:
        os.chdir(previous_cwd)

    assert out == Path('artifacts/cases/index.html')
    assert (tmp_path / out).exists()


def test_build_case_board_html_marks_rising_fingerprint():
    html = build_case_board_html(
        [
            {
                'trace_file': 'recent-a.jsonl',
                'trace_recency_rank': 1,
                'priority_score': 90,
                'priority_level': 'high',
                'failure_mode': 'memory_vs_tool_conflict',
                'failure_fingerprint': {'label': 'memory-vs-tool-conflict', 'id': 'a'},
                'answer_risk': 'hidden_degradation',
                'final_answer': 'Jog is fine.',
                'regression_detected': True,
                'case_status': 'new',
                'case_owner': 'alice',
                'case_next_step': 'Replay recent-a.',
                'case_index_path': 'artifacts/cases/recent-a/README.md',
                'trace_view_path': 'artifacts/views/recent-a.html',
                'regression_report_path': 'artifacts/regressions/golden__recent-a.md',
            },
            {
                'trace_file': 'recent-b.jsonl',
                'trace_recency_rank': 2,
                'priority_score': 70,
                'priority_level': 'high',
                'failure_mode': 'memory_vs_tool_conflict',
                'failure_fingerprint': {'label': 'memory-vs-tool-conflict', 'id': 'b'},
                'answer_risk': 'hidden_degradation',
                'final_answer': 'Jog is fine.',
                'regression_detected': True,
                'case_status': 'new',
                'case_owner': 'bob',
                'case_next_step': 'Replay recent-b.',
                'case_index_path': 'artifacts/cases/recent-b/README.md',
                'trace_view_path': 'artifacts/views/recent-b.html',
                'regression_report_path': 'artifacts/regressions/golden__recent-b.md',
            },
            {
                'trace_file': 'older-a.jsonl',
                'trace_recency_rank': 3,
                'priority_score': 10,
                'priority_level': 'low',
                'failure_mode': 'no_explicit_failure',
                'failure_fingerprint': {'label': 'no-explicit-failure', 'id': 'c'},
                'answer_risk': 'no_explicit_risk_found',
                'final_answer': 'ok',
                'regression_detected': False,
                'case_status': 'fixed',
                'case_owner': 'unassigned',
                'case_next_step': 'No action.',
                'case_index_path': 'artifacts/cases/older-a/README.md',
                'trace_view_path': 'artifacts/views/older-a.html',
                'regression_report_path': None,
            },
            {
                'trace_file': 'older-b.jsonl',
                'trace_recency_rank': 4,
                'priority_score': 10,
                'priority_level': 'low',
                'failure_mode': 'no_explicit_failure',
                'failure_fingerprint': {'label': 'no-explicit-failure', 'id': 'd'},
                'answer_risk': 'no_explicit_risk_found',
                'final_answer': 'ok',
                'regression_detected': False,
                'case_status': 'fixed',
                'case_owner': 'unassigned',
                'case_next_step': 'No action.',
                'case_index_path': 'artifacts/cases/older-b/README.md',
                'trace_view_path': 'artifacts/views/older-b.html',
                'regression_report_path': None,
            },
        ],
        benchmark_gate={
            'coverage': {'fixtures': 5, 'matched': 4, 'partial': 1, 'missed': 0},
            'baseline_name': 'local-bench',
            'regressions': 1,
            'regressed_fixtures': [
                {
                    'fixture': 'wrong_tool_selected.jsonl',
                    'coverage_before': 'matched',
                    'coverage_after': 'partial',
                }
            ],
            'report_path': 'artifacts/benchmark_report.md',
            'regression_report_path': 'artifacts/benchmark_regression.md',
        },
    )
    assert 'recent 2' in html
    assert 'older 0' in html
    assert 'rising' in html
    assert 'avg priority 80' in html
    assert 'wrong_tool_selected.jsonl' in html
    assert 'coverage matched -&gt; partial' not in html
    assert 'coverage matched -> partial' in html
    assert 'recent-a.jsonl' in html
