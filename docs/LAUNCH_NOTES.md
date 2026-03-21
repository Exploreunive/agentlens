# AgentLens Launch Notes

## Repo description
Explain why your agent failed — root-cause debugging, memory attribution, and run divergence for LLM agents.

## Suggested GitHub topics
- ai-agents
- llm
- observability
- agent-debugging
- tracing
- memory
- evals
- developer-tools
- python

## First release positioning
This is an **alpha** release.
It is intentionally narrow:
- local-first
- debugging-oriented
- focused on failure explanation instead of generic observability dashboards

## What to emphasize publicly
- AgentLens is not trying to replace full-stack observability platforms
- it focuses on a sharper problem: understanding why an agent run became unreliable
- especially when memory and fresh tool evidence conflict

## Best demo commands
```bash
python3 examples/divergent_agent.py
python3 viewer.py
python3 diff_runs.py

python3 examples/failure_answer_agent.py
python3 viewer.py
python3 diff_runs.py
pytest -q
```

## Current release title
v0.1.6-alpha — Explain why your agent failed with integration-ready tracing and local regression checks

## Suggested first release title
v0.1.0-alpha — Explain why your agent failed
