# AgentLens v0.2.2-alpha Launch Notes

## One-line release
AgentLens now traces a real LangGraph-backed agent runtime, exports shareable debug bundles, and presents the trace in a more usable debugging view.

## What changed

### 1. Real LangGraph runtime tracing
- added a LangGraph adapter built around LangChain `create_agent`
- capture model turns, tool calls, tool results, and final answers in AgentLens events
- include a working `demo langgraph` flow for OpenAI-compatible providers

### 2. Better OpenAI-compatible integration
- support direct SDK-style tracing instead of only a tiny wrapper callback shape
- support `OPENAI_BASE_URL` for OpenAI-compatible providers
- normalize usage, response ids, and finish reasons more consistently

### 3. Shareable debug bundles
- export a trace as a zip bundle containing:
  - raw JSONL trace
  - rendered HTML viewer
  - diff report when available
  - summary manifest

### 4. Better trace reading
- add runtime overview to the viewer
- add model-turn summaries
- add tool-evidence summaries
- make the viewer default to the latest trace, which matters more for real workflows

## Suggested GitHub release copy

### Title
v0.2.2-alpha: LangGraph runtime tracing, shareable bundles, better viewer

### Body
AgentLens is an open-source local-first debugger for LLM agents.

This alpha release pushes the project beyond toy traces in a few important ways:

- trace a real LangGraph-backed agent runtime
- export shareable trace bundles for async debugging
- improve OpenAI-compatible tracing
- make the viewer easier to read for real agent runs

The biggest step forward here is the LangGraph path. AgentLens can now capture a real agent runtime flow with:
- model request / response turns
- tool selection
- tool evidence
- final answer

That makes the project more useful as a debugging tool, not just a trace demo.

## Suggested X / Twitter post

AgentLens v0.2.2-alpha is out.

Big step forward: it now traces a real LangGraph-backed agent runtime, not just toy local demos.

Also added:
- shareable trace bundles
- better OpenAI-compatible tracing
- a cleaner trace viewer with model turns + tool evidence

Repo: https://github.com/Exploreunive/agentlens

## Suggested Show HN angle

Show HN: AgentLens — explain why your LangGraph agent failed

## Suggested screenshot pairing

Use:
- `docs/assets/langgraph-trace-real.png` as the README hero
- `docs/assets/langgraph-trace-hero.svg` as an optional stylized social card
