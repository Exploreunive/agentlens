# AgentLens Regression Report

- baseline: `golden-run` (fca2ae6a-3a4d-4191-a8f1-04f5597d6046.jsonl)
- candidate: `9d06a0a0-2f50-40f4-a016-d638b02d9345.jsonl`
- regression_detected: `True`

## Final answer comparison
- baseline: Jog is fine.
- candidate: Jog is fine tomorrow morning.

## Suspicious signals
- baseline: []
- candidate: [{'event_index': 7, 'type': 'stale_memory_override', 'reason': 'Stale recalled memory overrode fresh weather evidence'}]

## First divergence
- {'event_index': 0, 'a_type': 'run.start', 'b_type': 'run.start', 'a_payload': {'task': 'find weather and decide whether to jog'}, 'b_payload': {'task': 'decide whether to jog tomorrow morning'}}
