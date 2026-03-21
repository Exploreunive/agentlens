from __future__ import annotations

from explain import build_failure_card


def test_build_failure_card_prefers_suspicious_signal():
    card = build_failure_card({
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
