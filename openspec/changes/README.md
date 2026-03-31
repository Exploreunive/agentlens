# OpenSpec Changes

Use `changes/` for work that alters a stable spec.

Each change should live in its own directory:

```text
openspec/changes/<change-id>/
├── proposal.md
├── tasks.md
└── specs/
    └── <capability>/
        └── spec.md
```

## Naming

Use a short, action-oriented id:

- `case-history-timeline`
- `suppression-expiry`
- `langgraph-checkpoint-replay`

## Required contents

- `proposal.md`
  Explains motivation, scope, risks, and acceptance.
- `tasks.md`
  Breaks work into verifiable implementation steps.
- `specs/.../spec.md`
  Contains only the delta for each affected capability.

## Change bar

Create a change when:

- user-facing workflow semantics change
- CLI output or artifact structure changes
- a new first-class page/report is introduced
- case status logic or incident routing changes
- a new runtime integration becomes part of the supported contract

Do not create a change for:

- refactors with no contract impact
- typo fixes
- pure test maintenance
