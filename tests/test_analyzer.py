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
    assert d['severity'] == 'low'


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
    assert s['failure_mode'] == 'memory_vs_tool_conflict'
    assert s['answer_risk'] == 'hidden_degradation'
    assert any(step['kind'] == 'memory_recall' for step in s['failure_chain'])


def test_summarize_divergence_emits_timeline_and_count():
    a = [
        {'type': 'run.start', 'payload': {}},
        {'type': 'tool.result', 'payload': {'condition': 'rain'}},
        {'type': 'run.end', 'payload': {'final_answer': 'skip jogging'}},
    ]
    b = [
        {'type': 'run.start', 'payload': {}},
        {'type': 'tool.result', 'payload': {'condition': 'sunny'}},
        {'type': 'run.end', 'payload': {'final_answer': 'jog is fine'}},
    ]
    d = summarize_divergence(a, b)
    assert d['divergence_count'] == 2
    assert len(d['divergence_timeline']) == 2
    assert d['divergence_timeline'][0]['difference_kind'] == 'payload_mismatch'
    assert d['severity'] == 'high'


def test_summarize_run_extracts_langgraph_tool_evidence_and_turns():
    events = [
        {'type': 'run.start', 'payload': {'runtime': 'langgraph', 'agent_name': 'weather_agent'}},
        {'type': 'llm.request', 'payload': {'model': 'gpt-5.2', 'prompt': 'Should I jog?'}},
        {'type': 'llm.response', 'payload': {'tool_calls': [{'name': 'weather_snapshot', 'id': 'call_1', 'args': {'city': 'Shanghai'}}], 'decision': 'tool_calls=weather_snapshot'}},
        {'type': 'tool.call', 'payload': {'tool_name': 'weather_snapshot', 'tool_call_id': 'call_1', 'args': {'city': 'Shanghai'}}},
        {'type': 'tool.result', 'payload': {'tool_call_id': 'call_1', 'content': 'Shanghai: rain'}},
        {'type': 'llm.response', 'payload': {'response': 'Skip the jog.'}},
        {'type': 'run.end', 'payload': {'final_answer': 'Skip the jog.'}},
    ]
    summary = summarize_run(events)
    assert summary['runtime'] == 'langgraph'
    assert summary['agent_name'] == 'weather_agent'
    assert summary['tool_evidence'][0]['tool_name'] == 'weather_snapshot'
    assert summary['tool_evidence'][0]['content'] == 'Shanghai: rain'
    assert any(turn['kind'] == 'llm_response' for turn in summary['model_turns'])
