# Change Proposal: case-history-timeline

## Summary

Add append-only case history timelines so AgentLens can show how an incident evolved over time: when it was created, when it changed owner, when it reopened, and when a repair finally became verified.

## Motivation

- Current case files are strong at showing the latest state, but weak at showing how the case got there.
- Reopened incidents are especially painful because operators cannot quickly answer:
  - how many times this case changed hands
  - when it last reopened
  - whether the current repair path is new or a repeat of an earlier failed attempt
- Fingerprint dossiers can already summarize repeated failures, but they do not yet have case-level workflow history to explain the sequence behind those counts.
- This change matters now because AgentLens has already become an incident cockpit; the next valuable step is operational memory for incidents, not just runs.

## Scope

- In scope
  - append-only structured history for each case
  - history entries for system-detected and operator-driven workflow changes
  - case README timeline summaries
  - dossier-level rollups that reference latest reopen / latest verified repair events
- Out of scope
  - SLA policy enforcement
  - suppression / snooze workflows
  - multi-user identity and auth
  - hosted database-backed incident storage

## Spec impact

- Affected capability specs
  - `incident-ops-cockpit`
  - `fingerprint-dossiers`
- New requirements introduced
  - per-case append-only history
  - material workflow transition capture
  - timeline summaries in case artifacts
  - history-aware fingerprint durability summaries
- Existing requirements changed
  - none yet; this extends the current incident contract

## Acceptance

- Running inbox on an existing case can record a `reopened` timeline event when validation regresses.
- Running `case update` records status, owner, and next-step transitions with before/after values.
- Case artifacts show a readable recent timeline section without hiding the current operational state.
- Fingerprint dossiers can mention the latest reopen event and latest verified repair event when those exist.
- Targeted tests prove duplicate no-op writes do not create misleading extra timeline events.

## Risks

- Timeline noise could make case files harder to scan if every regeneration appends duplicate entries.
- History semantics can become inconsistent if system-generated and operator-generated events use different vocabularies.
- If history is only stored in Markdown, later aggregation will be harder; a structured format is safer but adds another artifact to maintain.
