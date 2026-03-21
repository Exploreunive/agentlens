# AgentLens Go-To-Market Notes

## Core thesis
Do **not** market AgentLens as "another observability platform".
That frame is crowded and too abstract.

Market it as a sharper developer painkiller:

> **Explain why your agent failed.**

More specifically:
- trace the run
- highlight the suspicious step
- compare against a better run
- show when memory or tool evidence caused the run to go off-track

## Positioning wedge

### Bad frame
- AI observability platform
- tracing dashboard
- telemetry layer

### Better frame
- local-first debugger for LLM agents
- root-cause debugging for agent failures
- memory-aware debugging and regression diffing

## Best hooks

### Hook 1
**Explain why your agent failed.**

### Hook 2
**Traces tell you what happened. AgentLens helps you see where things started going wrong.**

### Hook 3
**Your agent can fail before the final answer looks obviously wrong. AgentLens helps surface that earlier failure step.**

## Strong demo narratives

### 1. Hidden degradation
The answer still looks acceptable, but the run already contains a `memory_conflict`.

Why this matters:
- surprising
- concrete
- easy to share
- feels like a real production problem

### 2. Visible failure
Stale recalled memory overrides fresh tool evidence and the final answer clearly degrades.

Why this matters:
- obvious outcome difference
- easy to understand in one screenshot
- supports the root-cause story

### 3. Baseline vs regression
A previously acceptable run becomes worse, and the diff/report shows where divergence began.

Why this matters:
- speaks to engineering workflows, not just demos
- closer to how developers actually debug regressions

## Channel strategy

### GitHub first
The repo itself should convert cold visitors.

Must-haves:
- sharp tagline in first screen
- one quick command path to value
- clear differentiation from generic tracing tools
- screenshots / gifs showing suspicious-step highlighting and regression report

### Reddit
Best likely subreddits:
- r/LocalLLaMA
- r/Python
- r/AI_Agents

Angle:
- local-first
- privacy-safe
- debugging real agent failures, not just logging tokens

### Hacker News / Show HN
Works best when the framing is:
- technical
- concrete
- privacy-aware
- honest about scope

Likely strongest title direction:
- Show HN: AgentLens – Explain why your agent failed
- Show HN: A local-first debugger for LLM agents

### X / Twitter
Focus on short contrasts:
- traces vs root-cause explanation
- “looked fine” vs “already degraded”
- baseline vs regression

## Assets to prepare

### 1. README tightening
- one stronger opening paragraph
- faster path to demo
- stronger contrast vs generic observability tools

### 2. Screenshot / GIF set
Minimum useful set:
1. viewer with suspicious step highlighted
2. regression report markdown
3. OpenAI wrapper demo trace

### 3. Launch copy variants
Need separate copy for:
- GitHub release notes
- Reddit post
- X thread
- HN / Show HN post

## Messaging rules
- be concrete, not broad
- show one painful debugging scenario, not ten features
- avoid “platform” language
- emphasize local-first + privacy-safe + engineering usefulness
- always anchor on a debugging question developers already ask

## Near-term marketing tasks
1. tighten README first screen
2. add screenshots / demo artifacts
3. prepare launch copy drafts
4. publish when the story feels coherent, not just when the feature count is high
