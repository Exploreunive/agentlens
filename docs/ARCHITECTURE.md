# AgentLens Architecture (Draft)

## Core idea
AgentLens stores agent execution as a structured event stream.

Instead of thinking in terms of logs, we think in terms of:
- runs
- spans
- events
- artifacts
- comparisons

## Core components

### 1. SDK
Responsible for instrumentation.

Responsibilities:
- create run IDs
- emit structured events
- wrap model / tool / memory calls
- send to local file or HTTP ingest endpoint

### 2. Ingest server
Responsible for receiving and storing events.

Initial version:
- FastAPI
- SQLite
- JSON artifact blobs on disk

### 3. Web UI
Responsible for debugging workflow.

Primary views:
- run list
- run detail timeline
- tool call tree
- memory panel
- run diff view

## Event model
Every event should include:
- event_id
- run_id
- span_id
- parent_span_id (optional)
- type
- ts
- status
- payload
- metrics

## Event types (v0)
- `run.start`
- `run.end`
- `llm.request`
- `llm.response`
- `tool.call`
- `tool.result`
- `memory.write`
- `memory.recall`
- `agent.decision`
- `error`

## Design principles

### Local-first
Must be useful without cloud infra.

### Readable before scalable
A small team should understand the data model quickly.

### Agent-specific
Do not flatten away tool + memory + decision structure.

### Replayable
A trace should be reconstructable enough for debugging.

## Non-goals (for now)
- full prompt management suite
- dataset labeling platform
- hosted production SaaS
- framework lock-in
