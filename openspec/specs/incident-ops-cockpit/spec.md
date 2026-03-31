# Capability: Incident Ops Cockpit

## Intent

AgentLens turns trace debugging into an operational workflow for triaging, assigning, validating, and closing agent incidents.

## Product contract

### Requirement: Inbox output is an operational queue

Running the inbox workflow MUST generate artifacts that support active triage, not just reporting.

Artifacts MUST include:

- ranked inbox output
- per-run trace pages
- case files
- incident board homepage

#### Scenario: Triage run

- **WHEN** a user runs `cli.py inbox`
- **THEN** AgentLens emits enough artifacts to inspect the run, assign work, and track follow-up

### Requirement: Case files store operational metadata

Each case file MUST support:

- status
- owner
- next step
- validation summary
- repair checklist
- recheck commands

#### Scenario: Handoff

- **WHEN** one engineer hands a case to another
- **THEN** the case file contains the next concrete action and the relevant artifact links

### Requirement: Fixed-state transitions are guarded by validation

AgentLens MUST block closing a case as `fixed` when validation is not clean, unless the user explicitly overrides the guard.

Validation MUST account for:

- baseline regression state
- benchmark regression state

#### Scenario: Unsafe close attempt

- **WHEN** a case is still regressed or benchmark coverage is failing
- **THEN** `case update --status fixed` is rejected unless `--force` is provided

### Requirement: Reopened incidents are first-class workflow states

AgentLens MUST distinguish a merely fixed case from a case whose fingerprint has resurfaced.

`reopened` MUST be treated as:

- unresolved
- visible on the incident board
- eligible for action queue prioritization

#### Scenario: Fixed case regresses again

- **WHEN** a case previously marked `fixed` fails validation on a later inbox run
- **THEN** the workflow state becomes `reopened` and the board surfaces it accordingly

### Requirement: Incident board highlights the next operational decision

The incident board MUST help a user decide what to do next by surfacing:

- action queue
- focus views
- owner load
- recurring issue leaderboard
- recurrence impact
- benchmark gate state

#### Scenario: Limited triage time

- **WHEN** a user only has time to inspect a few incidents
- **THEN** the board presents the highest-value unresolved work first

### Requirement: Board semantics favor operational truth over raw status text

Derived workflow state MAY differ from stored case status when validation or recurrence changes the operational meaning.

#### Scenario: Forced fixed case

- **WHEN** a case remains stored as `fixed` but validation shows the issue has resurfaced
- **THEN** the board and inbox show it as `reopened`
