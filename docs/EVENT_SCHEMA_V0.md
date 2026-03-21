# AgentLens Event Schema v0

## Required fields
Every event includes:

- `event_id`: unique event id
- `run_id`: run identifier
- `span_id`: span identifier
- `parent_span_id`: optional parent span
- `type`: event type
- `ts`: ISO8601 timestamp
- `status`: `ok` | `error`
- `payload`: event-specific data
- `metrics`: numeric or summary metrics

## Event types

### run.start
Marks the beginning of an agent run.

### run.end
Marks the end of an agent run and may include final answer / outcome.

### llm.request
Records model name, prompt, parameters, and context metadata.

### llm.response
Records model output, structured decision, and token/latency stats.

### tool.call
Records the tool name and arguments.

### tool.result
Records the tool output and latency.

### memory.write
Records what memory was written and why.

### memory.recall
Records what memory was recalled for the current step.

### agent.decision
Records intermediate planning / routing / action selection decisions.

### error
Records failures with enough context for debugging.

## Design notes
- Keep schema human-readable first
- Preserve enough structure for future run diffing
- Avoid framework-specific assumptions in core event format
