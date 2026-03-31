# Capability: Product Positioning

## Intent

AgentLens exists to help engineers diagnose, triage, and repair failing agent behavior.

## Product contract

### Requirement: AgentLens stays focused on agent reliability workflows

AgentLens MUST optimize for:

- locating where an agent run started going wrong
- surfacing evidence that explains the failure
- turning failures into repeatable repair workflows

AgentLens MUST NOT drift into a generic observability product whose main value is dashboards or logging alone.

#### Scenario: Product scope review

- **WHEN** a new feature is proposed
- **THEN** the proposal must show how it improves failure explanation, incident triage, repair verification, or recurring issue handling

### Requirement: AgentLens serves engineering operators first

Primary users MUST be treated as:

- agent engineers
- applied AI engineers
- builders operating tool-using or memory-enabled agents

Secondary audiences MAY be supported, but not at the cost of weakening the engineering workflow.

#### Scenario: Workflow prioritization

- **WHEN** a tradeoff exists between a prettier overview and a stronger debugging signal
- **THEN** the debugging signal wins

### Requirement: Local-first remains the default operating model

AgentLens MUST remain usable from local artifacts without requiring hosted backend infrastructure.

#### Scenario: Offline inspection

- **WHEN** a user has only local traces and generated artifacts
- **THEN** they can still inspect runs, triage incidents, and export repair context

### Requirement: Incident operations are a first-class wedge

AgentLens MUST treat the following as first-class workflows:

- debug inbox triage
- case ownership and next step tracking
- fixed-state validation
- reopened regression handling
- recurring fingerprint tracking

#### Scenario: Reliability homepage

- **WHEN** a user runs the incident workflow
- **THEN** the output must prioritize active incidents and recurring failure repair decisions rather than raw trace volume

## Non-goals

- prompt management suite
- hosted SaaS control plane
- generic analytics warehouse
- framework lock-in
