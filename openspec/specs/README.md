# Capability Specs

These specs define the stable product contract for AgentLens.

## Capability map

- `product-positioning`
  Defines the product wedge, target users, and non-goals.
- `trace-capture`
  Defines what execution data AgentLens must capture and persist.
- `trace-viewer`
  Defines how a single trace becomes a local HTML debugging surface.
- `failure-analysis`
  Defines how AgentLens explains failures and prioritizes debugging.
- `regression-workflows`
  Defines baselines, run divergence, regression reports, bundles, and benchmark validation.
- `incident-ops-cockpit`
  Defines inbox, case files, incident board, reopened workflows, and validation gates.
- `fingerprint-dossiers`
  Defines recurring issue rollups, recurrence impact, and reusable repair playbooks.
- `runtime-integrations`
  Defines support expectations for OpenAI-compatible and LangGraph-backed runtimes.

## Reading order

1. `product-positioning`
2. `incident-ops-cockpit`
3. `failure-analysis`
4. `fingerprint-dossiers`
5. `regression-workflows`
6. `trace-viewer`
7. `trace-capture`
8. `runtime-integrations`
