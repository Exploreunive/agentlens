# AgentLens

**Explain why your agent failed.**

AgentLens is a **local-first debugger for LLM agents**.
It helps you go beyond “here’s the trace” and answer a more useful question:

> **Where did the run actually start going wrong?**

AgentLens focuses on:

1. **Failure explanation** — where the run likely went wrong
2. **Memory attribution** — which memory influenced the outcome
3. **Run divergence** — where run B started behaving differently from run A

Most tools help you log traces.
AgentLens is being built to help you answer the harder question:

> Why did this agent make the wrong decision?

## Why AgentLens

Most LLM observability tools are good at showing traces.
Agent systems need more than traces — they need **failure explanation**.

Real agent failures are often caused by:

- tool output being misinterpreted
- recalled memory conflicting with fresh evidence
- the run diverging from a previously good trajectory
- the true failure starting earlier than the final bad answer

External signals point in the same direction:
- practitioners increasingly talk about **agent debugging** and **replayability** as missing layers
- recent work like Microsoft Research's **AgentRx** frames the problem as locating the **critical failure step** and the **root cause** in agent trajectories

AgentLens is built around that wedge: **explain where an agent run went wrong, and why.**

## Positioning

AgentLens is **not** trying to replace Langfuse, LangSmith, or Helicone head-on.

Instead, it starts with a sharper wedge:

- **agent runtime debugging**
- **memory observability**
- **run replay + regression diff**

## MVP

### v0.1-alpha
- capture one agent run as structured events
- store traces locally
- generate a failure summary for the latest run
- render a small local HTML debugging view
- compare two runs and surface the first divergence
- highlight suspicious signals such as memory/tool conflicts

### v0.2
- stronger failure heuristics
- explicit stale-memory / conflicting-evidence summaries
- improved divergence rendering
- better replay-oriented inspection flow

### v0.3
- richer memory attribution
- run bundles for sharing/debugging
- framework adapters

## Initial users

- solo builders shipping AI agents
- small teams building internal copilots
- developers working with tool-calling agents
- engineers debugging memory-enabled agent systems

## What makes this different

### 1. Root-cause debugging, not just observability
The goal is not only to log a run, but to identify the likely failure point and suspicious signals.

### 2. Memory attribution is first-class
Most tools treat memory as metadata.
AgentLens treats memory as part of the decision path and highlights when memory conflicts with fresh tool evidence.

### 3. Run divergence is a core workflow
Not just dashboards — the system should help answer where run B started behaving differently from run A.

### 4. Framework-light
The SDK should work with:
- OpenAI SDK
- custom agent loops
- lightweight wrappers
- eventually LangGraph / AutoGen / CrewAI adapters

## Repo plan

- `sdk/python/` — Python SDK for event capture
- `server/` — ingestion + storage API
- `web/` — trace viewer UI
- `docs/` — architecture, schema, roadmap
- `examples/` — minimal instrumented agents


## Requirements

- Python **3.10+**
- A local shell environment that can run `python3`
- No external model/API dependency is required for the current alpha demos

## Installation

```bash
git clone https://github.com/Exploreunive/agentlens.git
cd agentlens
```

Optional: create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Run tests:

```bash
pytest -q
```

## Project structure

```text
agentlens/
├── sdk/python/agentlens/   # trace capture SDK
├── examples/               # demo agent runs
├── docs/                   # architecture, schema, launch notes
├── tests/                  # automated tests
├── analyzer.py             # run analysis heuristics
├── explain.py              # root-cause card builder
├── viewer.py               # local HTML trace viewer
├── diff_runs.py            # run divergence report
└── cli.py                  # minimal CLI entrypoint
```

## Quickstart

```bash
cd agentlens
python3 examples/divergent_agent.py  # generate two runs with hidden memory/tool conflict
python3 viewer.py                    # render latest run with root-cause card
python3 diff_runs.py                 # show where the two runs diverged
pytest -q                            # run tests
```

## CLI

```bash
python3 cli.py demo                  # minimal run
python3 cli.py demo divergent        # hidden degradation demo
python3 cli.py demo failure          # visible failure demo
python3 cli.py demo openai-wrapper   # minimal OpenAI-compatible wrapper demo
python3 cli.py view                  # latest trace -> HTML
python3 cli.py diff                  # latest two runs -> Markdown diff
python3 cli.py explain               # generate both HTML + diff artifacts
python3 cli.py baseline save good-run
python3 cli.py baseline list
python3 cli.py regression check good-run
```

The trace viewer now also highlights:
- the **first suspicious step**
- the **likely failure step**
- **error events** directly in the timeline
- **event-type filters** for narrowing the trace quickly


## Two demo failure modes

### 1. Hidden degradation
```bash
python3 examples/divergent_agent.py
python3 diff_runs.py
python3 viewer.py
```
Shows a case where the final answer still looks acceptable, but the run already contains a `memory_conflict` signal.

### 2. Visible failure
```bash
python3 examples/failure_answer_agent.py
python3 diff_runs.py
python3 viewer.py
```
Shows a case where stale recalled memory overrides fresh tool evidence and the final answer visibly degrades.

## What you get today

Current alpha prototype can already:
- emit structured JSONL traces
- generate a root-cause style failure card
- surface suspicious signals such as `memory_conflict` and `stale_memory_override`
- compare two runs and show the first divergence
- render a local HTML debugging view
- demonstrate both hidden degradation and visible failure scenarios
- instrument agent runs with higher-level SDK helpers for spans, LLM calls, tool calls, and memory events
- use a minimal OpenAI-compatible wrapper for lower-friction LLM tracing
- save named baselines and generate regression reports against newer runs
- support privacy-safe local tracing with optional redaction

## Why someone would try this instead of another tracing tool

Because the point is not just to collect events.

The point is to help answer questions like:
- Why did this run become unreliable?
- Which suspicious step showed up before the final answer visibly degraded?
- Did the latest run regress against a known-good baseline?
- Did stale memory or fresh tool evidence change the outcome?

## Example: hidden failure before obvious answer degradation

A useful debugging tool should catch this situation:
- the final answer still *looks* acceptable
- but recalled memory conflicts with fresh tool evidence
- the run is already unreliable even before the answer visibly breaks

That is the kind of failure AgentLens is trying to surface.

See also: `docs/EXAMPLE_FAILURE.md`

## SDK helpers

The Python SDK now supports a more ergonomic, local-first instrumentation style:

```python
from agentlens import AgentLensClient

client = AgentLensClient()
run_id = client.new_run()
client.emit(type='run.start', run_id=run_id, payload={'task': 'answer a question'})

with client.span(run_id=run_id, name='research_and_answer') as span:
    llm = client.record_llm_call(
        run_id=run_id,
        model='gpt-4o-mini',
        prompt='Should we call the weather tool?',
        decision='call_weather_tool',
        reason='Need fresh evidence',
        metrics={'latency_ms': 42, 'input_tokens': 30, 'output_tokens': 16},
        parent_span_id=span.span_id,
    )
    client.record_tool_call(
        run_id=run_id,
        tool_name='weather.get_forecast',
        args={'city': 'Shanghai'},
        result={'condition': 'rain'},
        parent_span_id=llm['response'].span_id,
    )
    client.record_memory_recall(
        run_id=run_id,
        content='User usually jogs when it is sunny',
        parent_span_id=span.span_id,
    )
```

This keeps the local JSONL event model explicit, while reducing repetitive boilerplate for common agent flows.

## OpenAI-compatible wrapper demo

AgentLens now includes a minimal OpenAI-compatible wrapper example for lower-friction LLM tracing:

```bash
python3 cli.py demo openai-wrapper
python3 cli.py view
```

The wrapper lives in `sdk/python/agentlens/openai_wrapper.py` and is intentionally tiny. The goal is not to be a full SDK replacement, but to show the smallest useful integration shape for tracing real LLM calls.

## Baselines and regression checks

AgentLens now also supports a simple local baseline workflow:

```bash
python3 cli.py demo minimal
python3 cli.py baseline save good-run
python3 cli.py demo failure
python3 cli.py regression check good-run
```

This writes a Markdown regression report that makes it easier to answer a higher-value debugging question:

> Did the latest run get worse than the baseline, and where did it diverge?

## Privacy-safe tracing

AgentLens now also supports an optional local redaction mode for sensitive payloads:

```python
from agentlens import AgentLensClient

client = AgentLensClient(redact_sensitive=True)
```

When enabled, AgentLens will automatically:
- redact common sensitive keys like `api_key`, `token`, and `password`
- scrub common secrets such as `sk-...` and `ghp_...`
- mask email addresses and phone numbers in captured strings

This is especially useful when developers want to trace real agent runs locally without dumping obvious secrets into JSONL artifacts.

## Vision

Make agent systems debuggable, replayable, and trustworthy.


## Road to v0.2
- stronger root-cause heuristics
- better divergence explanation wording
- richer memory attribution
- replay-oriented run inspection
- framework adapters (starting with OpenAI SDK)


## Current limitations

This is still an **alpha** project.

Current limitations:
- local-first only
- no hosted service
- no production-grade replay engine yet
- no official OpenAI / LangGraph / AutoGen adapters yet
- root-cause analysis is heuristic-based, not model-judged or formally verified
- current UI is a minimal local HTML viewer, not a polished multi-page app
