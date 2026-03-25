# Changelog

## v0.2.2-alpha
- add a LangGraph-backed agent runtime adapter that traces real model and tool execution into AgentLens events
- add a real LangGraph demo wired to OpenAI-compatible providers through LangChain `create_agent`
- add shareable trace bundle export so a run can be zipped with raw trace, HTML view, diff, and summary manifest
- strengthen the OpenAI-compatible wrapper to support direct SDK calls, provider `base_url`, and better response normalization
- update README, roadmap, and next-step docs so the published project state matches the actual implementation

## v0.2.1-alpha
- add failure chains and answer-risk labels to make failure explanation more actionable
- add divergence timelines and severity labels to make run comparison more useful
- extend viewer summary to show failure mode and chain evidence

## v0.2.0-alpha
- add golden-output tests for diff and regression report snapshots
- add malformed-input coverage for trace loading, wrapper fallbacks, viewer rendering, and baseline failure paths
- move the validation strategy beyond self-authored happy-path tests toward output contracts and adversarial cases

## v0.1.9-alpha
- extend regression workflow tests to cover baseline listing and report contents
- extend viewer tests to assert more of the highlighted debugging controls
- keep tightening coverage around the developer-facing workflows added in recent iterations

## v0.1.8-alpha
- add deeper regression coverage for baseline persistence and wrapper instrumentation
- add explicit tests for span error emission and OpenAI-compatible wrapper metrics capture
- strengthen confidence that the newer integration and regression workflows behave as expected

## v0.1.7-alpha
- tighten the README opening around the local-first debugging wedge
- add go-to-market notes covering positioning, launch channels, and demo hooks
- add first-pass launch copy drafts for GitHub, Reddit, X, and Show HN
- strengthen the external narrative around failure explanation, memory attribution, and regression diffing

## v0.1.6-alpha
- add a minimal OpenAI-compatible wrapper demo for lower-friction LLM tracing
- add local baseline save/list commands and Markdown regression reports
- extend the CLI with `demo openai-wrapper`, `baseline`, and `regression check`
- document integration and regression workflows in the README

## v0.1.5-alpha
- add optional privacy-safe redaction for local traces
- redact common secret-like strings, emails, phone numbers, and configured sensitive keys before writing JSONL events
- expose redaction helpers from the SDK for downstream integrations
- document privacy-safe local tracing and cover it with regression tests

## v0.1.4-alpha
- add ergonomic SDK helpers for spans, LLM calls, tool calls, and memory events
- refactor demo agents to use the higher-level instrumentation flow
- strengthen SDK regression coverage for the new helper methods
- document a more realistic local-first instrumentation style in the README

## v0.1.3-alpha
- highlight the first suspicious step and likely failure step directly in the local trace viewer
- visually emphasize error events in the timeline
- add event-type filters for narrowing noisy traces faster
- strengthen viewer regression coverage for the new debugging controls

## v0.1.2-alpha
- expand CLI into a more usable debugging entrypoint with `demo`, `view`, `diff`, and `explain`
- support built-in demo scenarios for minimal, divergent, and visible-failure runs
- add regression coverage for CLI diff/explain flows
- document the CLI workflow in the README

## v0.1.1-alpha
- add run-level metrics to the local HTML trace viewer
- surface total latency, input/output tokens, and tool call count at the top of each run
- add event-type counts to the failure summary panel
- strengthen viewer regression coverage for the new stats panel

## v0.1.0-alpha
- define project positioning and architecture draft
- add Python SDK for local JSONL trace capture
- add minimal example agent and a divergent failure-focused example
- add static HTML trace viewer with failure summary
- add run divergence generator
- add initial failure analysis / suspicious signal heuristics
- add divergent hidden-failure and visible-failure demo scenarios
- add automated tests (`10 passed`)
