# Tasks: case-history-timeline

## Implementation

- [ ] Add a structured per-case history artifact, likely under `artifacts/cases/<trace>/`
- [ ] Define normalized history event types for create, assign, status change, next-step change, reopened, and verified
- [ ] Record history entries from both `inbox` regeneration and `case update`
- [ ] Render a recent timeline section inside case README output
- [ ] Surface latest reopen / latest verified history in fingerprint dossiers
- [ ] Add or update targeted tests for timeline creation, transition recording, and duplicate-entry protection
- [ ] Update README if the user-facing workflow changes materially

## Verification

- [ ] Automated tests pass
- [ ] `python3 cli.py inbox --baseline <name>` can create or update history for a regressed case
- [ ] `python3 cli.py case update ...` records explicit operator transitions
- [ ] Generated case README and dossier artifacts reflect the new history contract
