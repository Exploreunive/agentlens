# Capability: Runtime Integrations

## Intent

AgentLens should trace real agent runtimes with minimal friction while preserving the reliability workflows defined elsewhere.

## Product contract

### Requirement: OpenAI-compatible runtimes are first-class

AgentLens MUST support tracing agents that use an OpenAI-compatible API surface.

#### Scenario: Compatibility deployment

- **WHEN** a user points AgentLens at an OpenAI-compatible base URL and model
- **THEN** demo and wrapper flows can emit traces without requiring provider-specific infrastructure

### Requirement: LangGraph runtime support preserves useful structure

LangGraph integration MUST preserve enough runtime structure for:

- model turn reconstruction
- tool usage inspection
- stateful debugging

#### Scenario: LangGraph demo trace

- **WHEN** a LangGraph-backed demo run is traced
- **THEN** the resulting artifact is usable in the same viewer, inbox, and incident flows as other runs

### Requirement: Integrations feed the same incident contract

All supported runtimes MUST emit traces that remain compatible with:

- failure analysis
- regression checks
- case generation
- fingerprint grouping

#### Scenario: Mixed runtime repository

- **WHEN** a project contains runs from different supported runtimes
- **THEN** AgentLens can still rank, group, and operationalize them under one incident workflow

### Requirement: New integrations do not weaken the core wedge

New runtime integrations SHOULD be admitted only if they improve the debugging and reliability workflow rather than merely expanding matrix coverage.

#### Scenario: Integration review

- **WHEN** a new framework adapter is proposed
- **THEN** it should show how it improves real incident diagnosis or repair workflows
