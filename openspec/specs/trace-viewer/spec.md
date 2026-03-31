# trace-viewer Specification

## Purpose

Describe how AgentLens turns one trace into a debugging surface that explains where an agent likely started going wrong.

## Requirements

### Requirement: Latest-run HTML viewer

The system SHALL render the latest trace or a named trace into a standalone HTML debugging view.

#### Scenario: Rendering the latest trace

- **GIVEN** at least one trace exists locally
- **WHEN** an operator runs `python3 cli.py view`
- **THEN** AgentLens writes an HTML trace page under `artifacts/`
- **AND** the page can be opened without a web backend

#### Scenario: Rendering a specific trace

- **GIVEN** a trace stem or file name is provided
- **WHEN** an operator runs `python3 cli.py view <trace>`
- **THEN** AgentLens resolves that trace and renders its HTML view

### Requirement: Root-cause oriented run summary

The system SHALL summarize a run in terms of failure explanation rather than only raw event playback.

#### Scenario: Viewing a degraded run

- **GIVEN** a trace includes suspicious signals, tool evidence, or conflicting memory
- **WHEN** the trace viewer is generated
- **THEN** the page highlights a likely failure point
- **AND** it includes a debug story, evidence list, and inspect-next hints

### Requirement: First suspicious step highlighting

The system SHALL call out the earliest suspicious point in the visible event timeline.

#### Scenario: Highlighting the first suspicious event

- **GIVEN** a trace contains an error or suspicious event
- **WHEN** the event timeline is rendered
- **THEN** the first suspicious event is visually labeled
- **AND** likely failure points are separately highlighted when available

### Requirement: Tool and answer grounding review

The system SHALL compare tool evidence against the final answer and surface grounding quality.

#### Scenario: Answer-evidence review

- **GIVEN** tool results and a final answer are present in the trace
- **WHEN** the viewer summary is generated
- **THEN** AgentLens reports whether the answer appears aligned, unclear, or in need of review

### Requirement: Event filtering

The system SHALL provide event-type filters in the HTML trace viewer.

#### Scenario: Narrowing a large trace

- **GIVEN** a trace contains multiple event types
- **WHEN** the viewer is opened
- **THEN** operators can filter the event list by event type
- **AND** inspect a smaller subset without regenerating the trace
