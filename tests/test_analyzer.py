from __future__ import annotations

from analyzer import summarize_divergence, summarize_run


def test_summarize_run_detects_memory_and_final_answer():
    events = [
        {'type': 'run.start', 'payload': {}},
        {'type': 'tool.call', 'payload': {'tool_name': 'weather.get_forecast'}},
        {'type': 'memory.write', 'payload': {'content': 'forecast=rain'}},
        {'type': 'run.end', 'payload': {'final_answer': 'skip jogging'}},
    ]
    s = summarize_run(events)
    assert s['final_answer'] == 'skip jogging'
    assert s['tool_sequence'] == ['weather.get_forecast']
    assert s['memory_influence'][0]['content'] == 'forecast=rain'


def test_summarize_divergence_finds_first_changed_payload():
    a = [
        {'type': 'run.start', 'payload': {}},
        {'type': 'tool.result', 'payload': {'condition': 'rain'}},
    ]
    b = [
        {'type': 'run.start', 'payload': {}},
        {'type': 'tool.result', 'payload': {'condition': 'sunny'}},
    ]
    d = summarize_divergence(a, b)
    assert d['first_divergence']['event_index'] == 1
    assert d['first_divergence']['a_payload']['condition'] == 'rain'
    assert d['first_divergence']['b_payload']['condition'] == 'sunny'


def test_summarize_run_marks_error_as_suspicious_signal():
    events = [
        {'type': 'run.start', 'payload': {}},
        {'type': 'memory.recall', 'payload': {'content': 'forecast=sunny'}},
        {'type': 'error', 'payload': {'kind': 'memory_conflict', 'message': 'memory conflicts with tool'}},
        {'type': 'run.end', 'payload': {'final_answer': 'jog is fine'}},
    ]
    s = summarize_run(events)
    assert s['likely_failure_point']['type'] == 'error'
    assert s['suspicious_signals'][0]['type'] == 'memory_conflict'
    assert 'memory conflicts with tool' in s['suspicious_signals'][0]['reason']
