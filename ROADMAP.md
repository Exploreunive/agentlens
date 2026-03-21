# AgentLens Roadmap

## Phase 0 — Define the wedge
Goal: avoid building a vague 'AI platform'.

### Deliverables
- [x] project positioning
- [x] MVP scope
- [x] architecture draft
- [ ] event schema v0
- [ ] first example agent

---

## Phase 1 — Local-first trace capture
Goal: make a single run visible end-to-end.

### Features
- [ ] Python SDK: create trace / span / event
- [ ] local JSONL storage
- [ ] event types:
  - [ ] run.start
  - [ ] run.end
  - [ ] llm.request
  - [ ] llm.response
  - [ ] tool.call
  - [ ] tool.result
  - [ ] memory.write
  - [ ] memory.recall
  - [ ] agent.decision
  - [ ] error
- [ ] basic run viewer

### Success criteria
- Can inspect one agent run from browser
- Can see where latency and failure happened

---

## Phase 2 — Run divergence
Goal: explain where and why two runs diverged.

### Features
- [ ] compare two runs side by side
- [ ] prompt diff
- [ ] tool call diff
- [ ] output diff
- [ ] cost / latency diff

### Success criteria
- A user can answer: “why did this agent behave differently?”

---

## Phase 3 — Memory observability
Goal: make memory behavior inspectable.

### Features
- [ ] memory write events
- [ ] memory recall events
- [ ] recall hit visualization
- [ ] stale / conflicting memory markers
- [ ] memory influence panel

### Success criteria
- A user can answer: “which memory changed the outcome?”

---

## Phase 4 — Regression workflows
Goal: turn traces into engineering workflows.

### Features
- [ ] save named test runs
- [ ] compare new runs against baseline
- [ ] regression warning rules
- [ ] export trace bundle

---

## Phase 5 — Integrations
### Targets
- [ ] OpenAI SDK wrapper
- [ ] LiteLLM integration
- [ ] LangGraph adapter
- [ ] AutoGen adapter
- [ ] OpenClaw example integration
