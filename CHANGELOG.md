# Changelog

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
