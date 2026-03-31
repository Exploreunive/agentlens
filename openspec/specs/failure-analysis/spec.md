# Capability: Failure Analysis

## Intent

AgentLens explains why an agent run is suspicious and what an engineer should inspect first.

## Product contract

### Requirement: AgentLens summarizes likely failure evidence

AgentLens MUST derive a run summary that can include:

- likely failure point
- suspicious signals
- answer risk
- tool evidence
- memory influence
- failure fingerprint

#### Scenario: Latest run explanation

- **WHEN** a user renders a trace view
- **THEN** they receive a compact explanation of where the run likely went wrong and why

### Requirement: Debug priority is actionable

AgentLens MUST assign a debugging priority that helps users choose which run to inspect first.

Priority SHOULD account for:

- suspicious signals
- visible or hidden degradation
- weak evidence grounding
- regression against a baseline

#### Scenario: Inbox ordering

- **WHEN** multiple recent traces exist
- **THEN** the debug inbox sorts higher-risk or regressed runs ahead of low-signal runs

### Requirement: Failure fingerprints are stable enough for grouping

AgentLens MUST assign a failure fingerprint label that is suitable for:

- recurring issue grouping
- trend watch
- dossier generation
- repair playbook reuse

#### Scenario: Recurring issue grouping

- **WHEN** multiple runs share the same failure shape
- **THEN** they are grouped under a common fingerprint label in downstream reliability views

### Requirement: Analysis should remain explainable

AgentLens SHOULD produce reasons and evidence strings that an engineer can challenge.

#### Scenario: Analyst review

- **WHEN** an engineer disagrees with a priority score or failure label
- **THEN** they can inspect the supporting reasons rather than treating the result as a black box
