from __future__ import annotations

from pathlib import Path

from regression import load_trace
from analyzer import summarize_run


FIXTURES = Path(__file__).resolve().parent / 'fixtures' / 'benchmarks'


def _load(name: str):
    return load_trace(FIXTURES / name)


def test_fixture_wrong_tool_selected_maps_to_specific_failure_mode():
    summary = summarize_run(_load('wrong_tool_selected.jsonl'))
    assert summary['failure_mode'] == 'wrong_tool_selected'
    assert summary['failure_fingerprint']['label'] == 'wrong-tool-selected'
    assert summary['debug_priority']['level'] == 'high'


def test_fixture_wrong_tool_argument_maps_to_specific_failure_mode():
    summary = summarize_run(_load('wrong_tool_argument.jsonl'))
    assert summary['failure_mode'] == 'wrong_tool_argument'
    assert summary['failure_fingerprint']['label'] == 'wrong-tool-argument'
    assert summary['suspicious_signals'][0]['type'] == 'used_wrong_tool_argument'


def test_fixture_tool_result_ignored_maps_to_specific_failure_mode():
    summary = summarize_run(_load('tool_result_ignored.jsonl'))
    assert summary['failure_mode'] == 'tool_result_ignored'
    assert summary['failure_fingerprint']['label'] == 'tool-result-ignored'
    assert summary['answer_risk'] in {'visible_failure', 'hidden_degradation'}


def test_fixture_goal_partially_completed_maps_to_specific_failure_mode():
    summary = summarize_run(_load('goal_partially_completed.jsonl'))
    assert summary['failure_mode'] == 'goal_partially_completed'
    assert summary['failure_fingerprint']['label'] == 'goal-partially-completed'
    assert summary['tool_sequence'] == ['create_project', 'invite_user']


def test_fixture_clarification_failure_maps_to_specific_failure_mode():
    summary = summarize_run(_load('clarification_failure.jsonl'))
    assert summary['failure_mode'] == 'clarification_failure'
    assert summary['failure_fingerprint']['label'] == 'clarification-missing'
    assert summary['suspicious_signals'][0]['type'] == 'clarification_missing'
