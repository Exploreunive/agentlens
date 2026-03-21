# AgentLens Project Definition

## One-line pitch
AgentLens is an open-source failure debugging workspace for LLM agents, focused on failure explanation, memory attribution, and run divergence.

## Problem
Developers can usually see that an agent failed, but not why:
- what decision caused the failure
- what tool output misled the agent
- what memory was recalled and whether it was stale
- why two runs diverged

## Why now
Agent systems are moving from demos to production.
Tracing exists, but agent-native debugging is still immature.
Memory behavior is especially under-instrumented.

## User
Primary:
- agent engineers
- applied AI engineers
- indie builders shipping agent products

Secondary:
- PM / QA / researcher types inspecting runs

## Wedge
Start with the narrowest painful problem:
**help developers debug one broken agent run quickly.**

## Product thesis
If we make one run:
- visible
- replayable
- comparable
- memory-aware

then we create a foundation for broader agent engineering workflows.

## Why this can matter
- strong hiring signal
- real developer pain
- differentiated from generic LLM logging
- extensible into eval / regression / quality workflows later
