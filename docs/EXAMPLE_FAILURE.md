# Example Failure: memory conflicts with fresh tool evidence

## Scenario
Two runs look similar at a glance:
- same task
- same recalled memory
- same tool call
- same final answer text

But one run contains a hidden problem:
- the recalled memory suggests `sunny`
- the fresh weather tool returns `rain`
- the agent still gives the same optimistic answer

## Why this matters
A plain trace viewer may show the events, but not emphasize the real debugging question:

> The final answer did not visibly diverge, but did the reasoning quality degrade?

AgentLens tries to surface that hidden failure signal by showing:
- suspicious signals (`memory_conflict`)
- likely failure point
- first divergence between two runs
- memory influence summary

## What this demonstrates
Agent debugging is not only about final-answer mismatch.
It is also about detecting when the decision process became unreliable before the answer obviously broke.
