# regression-workflows Specification

## Purpose

Describe how AgentLens compares current runs against known-good baselines and benchmark-inspired gates.

## Requirements

### Requirement: Named baseline management

The system SHALL allow operators to save and list named baseline traces.

#### Scenario: Saving a baseline

- **GIVEN** a latest trace exists
- **WHEN** an operator runs `python3 cli.py baseline save <name>`
- **THEN** AgentLens stores a named baseline reference under `.agentlens/baselines/`

#### Scenario: Listing baselines

- **GIVEN** one or more baselines have been saved
- **WHEN** an operator runs `python3 cli.py baseline list`
- **THEN** AgentLens prints the available baseline names

### Requirement: Regression review against a baseline

The system SHALL compare a candidate run against a saved baseline and explain why it regressed.

#### Scenario: Writing a regression report

- **GIVEN** a baseline exists and a newer candidate trace is available
- **WHEN** an operator runs `python3 cli.py regression check <name>`
- **THEN** AgentLens writes a regression report artifact
- **AND** the report includes whether the runs were comparable and why the candidate regressed

### Requirement: Run divergence reporting

The system SHALL surface where two runs started behaving differently.

#### Scenario: Comparing divergent runs

- **GIVEN** two traces differ in model behavior, tool calls, or output
- **WHEN** the diff workflow runs
- **THEN** AgentLens produces a divergence report covering the first meaningful change
- **AND** includes output, tool, cost, or latency differences when available

### Requirement: Shareable debugging bundles

The system SHALL export a shareable debugging bundle for a trace.

#### Scenario: Exporting a bundle

- **GIVEN** a trace has been analyzed
- **WHEN** an operator runs `python3 cli.py bundle export`
- **THEN** AgentLens packages the relevant trace and debugging artifacts into a bundle

### Requirement: Benchmark-inspired validation gate

The system SHALL track benchmark fixture coverage and regression status as a release-confidence gate.

#### Scenario: Rendering benchmark coverage

- **GIVEN** benchmark fixtures are available
- **WHEN** an operator runs `python3 cli.py bench report`
- **THEN** AgentLens writes benchmark coverage artifacts
- **AND** reports matched, partial, and missed coverage

#### Scenario: Checking a benchmark baseline

- **GIVEN** a benchmark baseline was previously saved
- **WHEN** an operator runs `python3 cli.py bench check <name>`
- **THEN** AgentLens writes a benchmark regression report
- **AND** that report can be used to block unsafe case closure
