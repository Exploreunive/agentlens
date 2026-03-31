# fingerprint-dossiers Specification Delta

## New Requirements

### Requirement: Dossiers reference case-history durability signals

The system SHALL use case history to explain whether a fingerprint is repeatedly reopening or finally stabilizing.

#### Scenario: Latest reopen signal

- **GIVEN** one or more cases for a fingerprint contain reopened history entries
- **WHEN** the fingerprint dossier is rendered
- **THEN** AgentLens can reference the latest reopen event for that fingerprint

#### Scenario: Latest verified repair signal

- **GIVEN** one or more cases for a fingerprint contain verified repair history entries
- **WHEN** the dossier is rendered
- **THEN** AgentLens can reference the latest verified repair event for that fingerprint

### Requirement: Fingerprint durability summaries prefer history over inference when available

The system SHALL prefer recorded case-history events over purely inferred current-state summaries when both are available.

#### Scenario: Reopen count with history

- **GIVEN** a fingerprint has explicit case history entries showing reopen and verification transitions
- **WHEN** AgentLens summarizes recurrence impact
- **THEN** the dossier uses that recorded history to describe repair durability
- **AND** does not rely only on the current workflow-state snapshot
