# AgentLens Roadmap

## Phase 0 — Define the wedge
Goal: avoid building a vague 'AI platform'.

### Deliverables
- [x] project positioning
- [x] MVP scope
- [x] architecture draft
- [x] event schema v0
- [x] first example agent

---

## Phase 1 — Local-first trace capture
Goal: make a single run visible end-to-end.

### Features
- [x] Python SDK: create trace / span / event
- [x] local JSONL storage
- [ ] event types:
  - [x] run.start
  - [x] run.end
  - [x] llm.request
  - [x] llm.response
  - [x] tool.call
  - [x] tool.result
  - [x] memory.write
  - [x] memory.recall
  - [x] agent.decision
  - [x] error
- [x] basic run viewer

### Success criteria
- Can inspect one agent run from browser
- Can see where latency and failure happened

---

## Phase 2 — Run divergence
Goal: explain where and why two runs diverged.

### Features
- [x] compare two runs in a divergence report
- [ ] prompt diff
- [x] tool call diff
- [x] output diff
- [x] cost / latency diff

### Success criteria
- A user can answer: “why did this agent behave differently?”

---

## Phase 3 — Memory observability
Goal: make memory behavior inspectable.

### Features
- [x] memory write events
- [x] memory recall events
- [ ] recall hit visualization
- [x] stale / conflicting memory markers
- [x] memory influence panel

### Success criteria
- A user can answer: “which memory changed the outcome?”

---

## Phase 4 — Regression workflows
Goal: turn traces into engineering workflows.

### Features
- [x] save named test runs
- [x] compare new runs against baseline
- [x] regression warning rules
- [x] export trace bundle

---

## Phase 5 — Integrations
### Targets
- [x] OpenAI SDK wrapper
- [ ] LiteLLM integration
- [x] LangGraph adapter
- [ ] AutoGen adapter
- [ ] OpenClaw example integration
