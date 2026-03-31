# trace-capture Specification

## Purpose

Describe how AgentLens captures agent execution as structured, local-first trace data.

## Requirements

### Requirement: Local-first structured trace storage

The system SHALL persist agent runs as structured JSONL events in a local workspace without requiring cloud infrastructure.

#### Scenario: Writing a new run locally

- **GIVEN** an instrumented AgentLens run starts
- **WHEN** events are emitted through the SDK or wrappers
- **THEN** the system stores them in a local trace file under `.agentlens/traces/`
- **AND** each event remains machine-readable as JSON

### Requirement: Agent-native event model

The system SHALL capture agent-native event types instead of flattening runs into plain logs.

#### Scenario: Capturing a tool-using run

- **GIVEN** an agent calls a tool and returns a final answer
- **WHEN** AgentLens traces the run
- **THEN** the trace can include `run.start`, `llm.request`, `llm.response`, `tool.call`, `tool.result`, `agent.decision`, `error`, and `run.end`
- **AND** those events retain their payload and metrics fields

### Requirement: Memory-aware instrumentation

The system SHALL support memory-specific events so memory can be debugged as part of the decision path.

#### Scenario: Capturing memory influence

- **GIVEN** an agent recalls or writes memory during execution
- **WHEN** the run is traced
- **THEN** the system records `memory.recall` and `memory.write` events
- **AND** downstream analysis can attribute memory influence to the run summary

### Requirement: Framework-light instrumentation surface

The system SHALL support both direct SDK usage and wrapper-style integrations.

#### Scenario: Tracing a custom loop

- **GIVEN** a developer instruments a custom agent loop with the Python SDK
- **WHEN** the run completes
- **THEN** the trace is stored in the same event format used by built-in demos and adapters

#### Scenario: Tracing through an integration wrapper

- **GIVEN** a developer uses an OpenAI-compatible wrapper or LangGraph adapter
- **WHEN** the runtime emits model and tool activity
- **THEN** the trace remains compatible with the same viewer, inbox, regression, and case workflows
