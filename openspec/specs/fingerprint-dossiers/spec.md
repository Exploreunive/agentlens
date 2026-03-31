# fingerprint-dossiers Specification

## Purpose

Describe how AgentLens turns recurring failure fingerprints into repair history, recurrence impact, and reusable playbooks.

## Requirements

### Requirement: Fingerprint rollups from incident data

The system SHALL group cases by failure fingerprint and compute recurrence-oriented summaries.

#### Scenario: Rolling up repeated failures

- **GIVEN** multiple inbox items share the same fingerprint label
- **WHEN** AgentLens builds fingerprint reports
- **THEN** it summarizes case count, reopened count, verified count, unresolved count, and regression count for that fingerprint

### Requirement: Fingerprint dossier pages

The system SHALL render a fingerprint index plus one detail page per fingerprint.

#### Scenario: Generating dossier artifacts

- **GIVEN** incident items exist
- **WHEN** an operator runs `python3 cli.py fingerprints report`
- **THEN** AgentLens writes `artifacts/fingerprints/index.html`
- **AND** writes one dossier page per fingerprint under `artifacts/fingerprints/`

### Requirement: Repair playbook suggestion

The system SHALL infer a reusable repair playbook from verified or repeated next steps.

#### Scenario: Reusing a verified repair path

- **GIVEN** a fingerprint has one or more verified repairs
- **WHEN** its dossier is generated
- **THEN** AgentLens surfaces a recommended playbook
- **AND** indicates whether the playbook came from verified fixes or active incident repetition

### Requirement: Recurrence impact messaging

The system SHALL explain whether a fingerprint keeps reopening or already has durable repairs.

#### Scenario: Fingerprint without durable repair

- **GIVEN** a fingerprint has reopenings but no verified repair
- **WHEN** its dossier or inbox rollup is rendered
- **THEN** AgentLens describes it as reopened without a verified repair yet

#### Scenario: Fingerprint with verified repair history

- **GIVEN** a fingerprint has both reopenings and verified repairs
- **WHEN** its dossier is rendered
- **THEN** AgentLens explains the balance between reopenings and verified repairs

### Requirement: Incident-board recurrence visibility

The system SHALL surface fingerprint durability on the main incident board and inbox.

#### Scenario: Recurrence impact on the board

- **GIVEN** case data includes repeated fingerprints
- **WHEN** the incident board is rendered
- **THEN** AgentLens shows a recurrence impact section with reopenings, verified repairs, and active owner context

#### Scenario: Recurrence impact in the inbox

- **GIVEN** an inbox item belongs to a repeated fingerprint
- **WHEN** the inbox report is rendered
- **THEN** AgentLens attaches fingerprint history and a recurrence note to that item
