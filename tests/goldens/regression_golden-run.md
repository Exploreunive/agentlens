# AgentLens Regression Report

- baseline: `golden-run` (5316c668-5f54-4bfc-af87-f62a46b9b6d9.jsonl)
- candidate: `e7d0945b-1ab8-433a-b1ae-bdaf34fcb088.jsonl`
- regression_detected: `True`

## Final answer comparison
- baseline: Jog is fine.
- candidate: Jog is fine tomorrow morning.

## Suspicious signals
- baseline: []
- candidate: [{'event_index': 7, 'type': 'stale_memory_override', 'reason': 'Stale recalled memory overrode fresh weather evidence'}]

## First divergence
- {'event_index': 0, 'a_type': 'run.start', 'b_type': 'run.start', 'a_payload': {'task': 'find weather and decide whether to jog'}, 'b_payload': {'task': 'decide whether to jog tomorrow morning'}, 'difference_kind': 'payload_mismatch'}
