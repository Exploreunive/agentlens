from __future__ import annotations

from typing import Any, Dict, List


def build_failure_card(summary: Dict[str, Any]) -> Dict[str, Any]:
    suspicious = summary.get('suspicious_signals', [])
    likely_failure = summary.get('likely_failure_point')
    memory_influence = summary.get('memory_influence', [])

    root_cause = 'No explicit root cause identified yet.'
    evidence: List[str] = []
    inspect_next: List[str] = []

    if suspicious:
        first = suspicious[0]
        root_cause = f"Likely root cause: {first.get('type')}"
        evidence.append(first.get('reason', 'Suspicious signal emitted'))

    if likely_failure:
        evidence.append(f"Likely failure point at event index {likely_failure.get('event_index')}")

    recall_items = [m for m in memory_influence if m.get('kind') == 'recall']
    if recall_items:
        evidence.append(f"{len(recall_items)} memory recall event(s) influenced the run")
        inspect_next.append('Check whether recalled memory was stale or weakly relevant')

    if summary.get('tool_sequence'):
        inspect_next.append('Inspect tool outputs around the divergence/failure step')

    if not inspect_next:
        inspect_next.append('Inspect the earliest non-trivial decision in the run')

    return {
        'root_cause': root_cause,
        'evidence': evidence,
        'inspect_next': inspect_next,
    }
