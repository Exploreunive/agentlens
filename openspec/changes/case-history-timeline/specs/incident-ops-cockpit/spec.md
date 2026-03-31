# incident-ops-cockpit Specification Delta

## New Requirements

### Requirement: Per-case append-only history

The system SHALL maintain append-only history for each case so operators can inspect how the incident evolved instead of only seeing the latest state.

#### Scenario: Case creation history

- **GIVEN** a trace enters the inbox and no case history exists yet
- **WHEN** AgentLens creates the case
- **THEN** it records a case-created history entry
- **AND** that entry includes a timestamp, source, and initial workflow context

### Requirement: Material workflow transitions are recorded

The system SHALL record history only for material transitions, including status changes, owner changes, next-step changes, reopened events, and verified repair events.

#### Scenario: Operator updates a case

- **GIVEN** a case already exists
- **WHEN** an operator runs `python3 cli.py case update <trace> --status investigating --owner alice --next-step "Replay the failing branch"`
- **THEN** AgentLens records the before/after transition in case history
- **AND** identifies the source as an operator-driven update

#### Scenario: System detects a reopened incident

- **GIVEN** a case was previously fixed
- **AND** a later inbox run detects validation is no longer clean
- **WHEN** case artifacts are regenerated
- **THEN** AgentLens records a reopened history entry
- **AND** identifies the source as workflow regeneration or baseline validation

### Requirement: No-op rewrites do not create misleading timeline noise

The system SHALL avoid appending duplicate history entries when a case is regenerated without a material workflow change.

#### Scenario: Re-running inbox with unchanged state

- **GIVEN** a case already has the same status, owner, next step, and workflow state as the previous run
- **WHEN** an operator runs inbox again
- **THEN** AgentLens does not append a misleading duplicate transition entry

### Requirement: Timeline summaries are visible in case artifacts

The system SHALL surface recent case history inside the shareable case artifact.

#### Scenario: Opening a case README

- **GIVEN** a case has recorded history
- **WHEN** an engineer opens the case README
- **THEN** they can see a recent timeline section showing the latest material transitions
- **AND** the current status remains easy to find above the timeline
