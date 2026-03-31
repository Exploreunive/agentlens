# AgentLens OpenSpec

This directory is the spec source of truth for AgentLens.

## Layout

- `openspec/specs/` records what the system does today.
- `openspec/changes/` is reserved for proposed changes before implementation.
- `openspec/changes/archive/` stores completed changes after they have been merged into the main specs.

## How To Use This Repo

For AgentLens, specs should stay centered on the product wedge:

- agent incident operations
- recurring failure detection
- regression triage
- repair verification
- framework-light runtime tracing

Avoid writing vague platform specs such as "general AI observability" unless the capability is already implemented in the repo.

## Current Capability Map

- `product-positioning`: the product wedge, users, and non-goals
- `trace-capture`: structured local-first event capture
- `trace-viewer`: single-run debugging view and root-cause surfacing
- `failure-analysis`: failure explanation, debug priority, and fingerprinting
- `regression-workflows`: baselines, diffs, bundles, and regression review
- `incident-ops-cockpit`: inbox, case files, validation, and reopened workflows
- `fingerprint-dossiers`: recurring failure rollups and repair playbooks
- `runtime-integrations`: OpenAI-compatible wrapper and LangGraph tracing

## Authoring Rules

- Use `SHALL` language for normative requirements.
- Include concrete `Scenario` blocks for operator-visible behavior.
- Update `openspec/specs/` only for behavior that exists on `main`.
- Put future work into `openspec/changes/<change-id>/` before implementation.
