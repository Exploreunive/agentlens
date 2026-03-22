from __future__ import annotations

from typing import Any, Dict, List


def build_failure_card(summary: Dict[str, Any]) -> Dict[str, Any]:
    suspicious = summary.get('suspicious_signals', [])
    likely_failure = summary.get('likely_failure_point')
    memory_influence = summary.get('memory_influence', [])
    failure_chain = summary.get('failure_chain', [])
    evidence_summary = summary.get('evidence_summary', [])

    root_cause = 'No explicit root cause identified yet.'
    evidence: List[str] = []
    inspect_next: List[str] = []

    if suspicious:
        first = suspicious[0]
        failure_mode = summary.get('failure_mode', 'unknown_failure_mode')
        answer_risk = summary.get('answer_risk', 'unknown')
        confidence = summary.get('confidence', 'low')
        root_cause = f"Likely root cause: {first.get('type')} ({failure_mode}, risk={answer_risk}, confidence={confidence})"
        evidence.append(first.get('reason', 'Suspicious signal emitted'))

    if likely_failure:
        evidence.append(f"Likely failure point at event index {likely_failure.get('event_index')}")

    recall_items = [m for m in memory_influence if m.get('kind') == 'recall']
    if recall_items:
        evidence.append(f"{len(recall_items)} memory recall event(s) influenced the run")
        inspect_next.append('Check whether recalled memory was stale or weakly relevant')

    if evidence_summary:
        evidence.extend(evidence_summary[:3])

    if failure_chain:
        inspect_next.append('Walk the failure chain from the first suspicious step to the final answer')

    if summary.get('tool_sequence'):
        inspect_next.append('Inspect tool outputs around the divergence/failure step')

    if not inspect_next:
        inspect_next.append('Inspect the earliest non-trivial decision in the run')

    return {
        'root_cause': root_cause,
        'evidence': evidence,
        'inspect_next': inspect_next,
    }
