# Contributing

Thanks for checking out AgentLens.

## Current stage
This project is in a very early alpha stage.
The priority is to keep the core scope sharp:
- runtime traces
- memory observability
- run diff / replay

## Good first contributions
- event filtering in viewer
- better run diff formatting
- memory recall example events
- OpenAI wrapper helper
- more example agents
- packaging / install improvements

## Development
```bash
python3 cli.py demo
python3 cli.py view
python3 diff_runs.py
pytest -q
```

## Principles
- keep the core event schema readable
- avoid framework lock-in too early
- optimize for debugging workflows, not dashboard vanity
