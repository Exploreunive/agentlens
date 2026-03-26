from __future__ import annotations

from explain import build_failure_card


def test_build_failure_card_prefers_suspicious_signal():
    card = build_failure_card({
        'runtime': 'langgraph',
        'agent_name': 'weather_agent',
        'turns': [{'tool_calls': [{'tool_name': 'weather_snapshot'}]}],
        'tool_evidence': [{'tool_name': 'weather_snapshot', 'content': 'Shanghai: rain'}],
        'answer_alignment': {'status': 'aligned', 'reason': 'Final answer reflects fresh tool evidence.'},
        'final_answer': 'Skip the jog.',
        'suspicious_signals': [
            {'type': 'memory_conflict', 'reason': 'Recalled memory conflicts with fresh tool result'}
        ],
        'likely_failure_point': {'event_index': 6},
        'memory_influence': [{'kind': 'recall', 'content': 'forecast=sunny'}],
        'tool_sequence': ['weather.get_forecast'],
    })
    assert 'memory_conflict' in card['root_cause']
    assert any('fresh tool result' in e for e in card['evidence'])
    assert any('recalled memory' in x.lower() for x in card['inspect_next'])
    assert any('weather_snapshot' in line for line in card['debug_story'])
    assert any('Answer grounding check' in line for line in card['debug_story'])
    assert any('Rerun turn' in line for line in card['counterfactual_hints'])
    assert any('weather_snapshot' in line for line in card['counterfactual_hints'])
