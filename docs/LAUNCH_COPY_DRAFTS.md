# AgentLens Launch Copy Drafts

## GitHub release draft

### Title
AgentLens v0.1.6-alpha — integration-ready tracing and local regression checks

### Body
AgentLens is an open-source, local-first debugging workspace for LLM agents.

This alpha release pushes the project closer to real developer workflows:
- a minimal OpenAI-compatible wrapper demo for lower-friction tracing
- local baseline save/list flows
- Markdown regression reports for comparing a candidate run against a named baseline
- privacy-safe local tracing with optional redaction
- suspicious-step highlighting and event filters in the trace viewer

The core goal remains the same:

> Explain why your agent failed.

This release is still intentionally narrow and local-first, but the workflow is getting closer to something developers can actually plug into their own agents and use during debugging.

## Reddit draft

### Title option 1
I built a local-first debugger for LLM agents that highlights suspicious steps and regression diffs

### Title option 2
I’m building an open-source tool to explain why an agent failed — now with baseline/regression checks

### Body
I’ve been frustrated by how often agent debugging stops at “here’s the trace.”

The harder question is usually:

**where did the run actually start going wrong?**

So I’ve been building AgentLens, a local-first debugging workspace for LLM agents.

Current alpha can:
- capture JSONL traces locally
- highlight the first suspicious step / likely failure step
- surface memory conflicts and stale-memory overrides
- compare runs and show the first divergence
- save a named baseline and generate a regression report against a newer run
- use a minimal OpenAI-compatible wrapper demo for lower-friction integration
- optionally redact common secrets / emails / phone numbers before writing traces

Repo: https://github.com/Exploreunive/agentlens

Would especially love feedback from people debugging tool-calling or memory-heavy agents.

## X / Twitter draft

### Short post
AgentLens update:

- local-first traces for LLM agents
- suspicious-step highlighting
- baseline/regression reports
- minimal OpenAI-compatible wrapper demo
- privacy-safe local redaction

Trying to build something that answers a narrower question than generic observability tools:

**Why did this agent actually fail?**

## HN / Show HN draft

### Title
Show HN: AgentLens – Explain why your agent failed

### Body
Hi HN — I’ve been building AgentLens, a local-first debugging workspace for LLM agents.

A lot of tooling helps log traces, but when I’m debugging agents the real question is usually narrower:

**Where did the run start going wrong, and why?**

AgentLens is my attempt at that wedge.

Current alpha supports:
- local JSONL trace capture
- suspicious-step highlighting and likely-failure-step highlighting
- memory-aware debugging signals
- run divergence reports
- named baselines + regression reports
- a tiny OpenAI-compatible wrapper demo
- optional privacy-safe local redaction

The current version is still intentionally small and local-first, but I’m trying to make it useful before making it big.

Repo: https://github.com/Exploreunive/agentlens

Would love feedback on whether this framing feels useful or too narrow.
