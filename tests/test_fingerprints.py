from __future__ import annotations

from pathlib import Path

from fingerprints import (
    build_fingerprint_detail_html,
    build_fingerprint_dossiers,
    build_fingerprint_index_html,
    fingerprint_report_path,
    write_fingerprint_reports,
)


def _sample_items() -> list[dict]:
    return [
        {
            'trace_file': 'run-a.jsonl',
            'trace_recency_rank': 1,
            'priority_score': 88,
            'failure_mode': 'wrong_tool_selected',
            'failure_fingerprint': {'label': 'wrong-tool-selected', 'id': 'a'},
            'answer_risk': 'hidden_degradation',
            'regression_detected': True,
            'case_status': 'fixed',
            'case_workflow_state': 'reopened',
            'case_owner': 'alice',
            'case_next_step': 'Replay the tool call with the baseline payload.',
            'case_index_path': 'artifacts/cases/run-a/README.md',
            'trace_view_path': 'artifacts/views/run-a.html',
        },
        {
            'trace_file': 'run-b.jsonl',
            'trace_recency_rank': 2,
            'priority_score': 72,
            'failure_mode': 'wrong_tool_selected',
            'failure_fingerprint': {'label': 'wrong-tool-selected', 'id': 'b'},
            'answer_risk': 'hidden_degradation',
            'regression_detected': False,
            'case_status': 'fixed',
            'case_workflow_state': 'verified',
            'case_owner': 'alice',
            'case_next_step': 'Replay the tool call with the baseline payload.',
            'case_index_path': 'artifacts/cases/run-b/README.md',
            'trace_view_path': 'artifacts/views/run-b.html',
        },
        {
            'trace_file': 'run-c.jsonl',
            'trace_recency_rank': 3,
            'priority_score': 61,
            'failure_mode': 'memory_vs_tool_conflict',
            'failure_fingerprint': {'label': 'memory-vs-tool-conflict', 'id': 'c'},
            'answer_risk': 'hidden_degradation',
            'regression_detected': False,
            'case_status': 'investigating',
            'case_workflow_state': 'investigating',
            'case_owner': 'bob',
            'case_next_step': 'Inspect the first memory recall that disagrees with tool evidence.',
            'case_index_path': 'artifacts/cases/run-c/README.md',
            'trace_view_path': 'artifacts/views/run-c.html',
        },
    ]


def test_build_fingerprint_dossiers_rolls_up_reopened_and_verified_history():
    dossiers = build_fingerprint_dossiers(_sample_items())
    wrong_tool = next(row for row in dossiers if row['label'] == 'wrong-tool-selected')

    assert wrong_tool['count'] == 2
    assert wrong_tool['reopened'] == 1
    assert wrong_tool['verified'] == 1
    assert wrong_tool['regressions'] == 1
    assert wrong_tool['playbook'] == 'Replay the tool call with the baseline payload.'
    assert wrong_tool['playbook_source'] == 'from the latest verified repair path'


def test_build_fingerprint_pages_include_playbook_and_case_links():
    dossiers = build_fingerprint_dossiers(_sample_items())
    wrong_tool = next(row for row in dossiers if row['label'] == 'wrong-tool-selected')

    index_html = build_fingerprint_index_html(dossiers)
    detail_html = build_fingerprint_detail_html(wrong_tool)

    assert 'AgentLens Fingerprint Dossiers' in index_html
    assert 'wrong-tool-selected' in index_html
    assert str(fingerprint_report_path('wrong-tool-selected')) in index_html
    assert 'Recommended playbook' in detail_html
    assert 'Replay the tool call with the baseline payload.' in detail_html
    assert 'artifacts/cases/run-a/README.md' in detail_html


def test_write_fingerprint_reports_creates_index_and_detail_files(tmp_path: Path):
    previous = Path.cwd()
    try:
        import os
        os.chdir(tmp_path)
        index_out, detail_paths = write_fingerprint_reports(_sample_items())
    finally:
        os.chdir(previous)

    assert index_out == Path('artifacts/fingerprints/index.html')
    assert detail_paths
    assert (tmp_path / index_out).exists()
    assert (tmp_path / fingerprint_report_path('wrong-tool-selected')).exists()
