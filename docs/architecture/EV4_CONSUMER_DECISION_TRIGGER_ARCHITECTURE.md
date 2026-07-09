# EV4 Consumer Decision Trigger Architecture Adoption

Status: Wave 0 adoption reference only.

Project Gate adopts the upstream EV4 Consumer Decision Trigger Architecture as a decision-gate contract for future Project Gate-specific audit and enforcement work.

Canonical upstream source:

```text
EV4-Decision-Kernel/docs/architecture/EV4_CONSUMER_DECISION_TRIGGER_ARCHITECTURE.md
```

Canonical upstream version and profile:

```yaml
architecture_version: "0.4.1"
brc_alignment: Behavioral_Rule_Coverage_v0.4.1
profile: EV4_CONSUMER_DECISION_TRIGGER_ARCHITECTURE_v0.4.1
primary_state_artifact: planning/DECISION_ESCAPE_ROUTES.yml
schema_artifact: planning/decision-escape-routes.schema.json
state_schema_version: 3
```

## Wave 0 Boundary

This file records Project Gate adoption of the upstream contract and the baseline local artifacts required for later waves. It does not record an audit of Project Gate escape routes and does not add enforcement.

Allowed Wave 0 claims:

```yaml
allowed_claims:
  - architecture_document_added
  - upstream_contract_adopted
```

Explicit Wave 0 non-claims:

```yaml
non_claims:
  - escape_routes_audited
  - schema_enforced
  - validator_backed
  - fixture_tested
  - ci_enforced
  - sequence_ci_enforced
  - runtime_monitor_enforced
  - os_harness_enforced
  - downstream_contract_enforced
  - project_gate_rejection_enforced
  - release_ready
  - production_ready
```

## Project Gate Boundary

Project Gate validates lineage, schema, evidence completeness, and release-readiness evidence when such carriers are explicitly implemented and inspected. Project Gate must not repair decisions, invent missing Kernel references, or claim release readiness from this Wave 0 adoption artifact.

Repository-specific decision escape route state starts at `expected_unverified` in `planning/DECISION_ESCAPE_ROUTES.yml`. Any later promotion must be supported by inspected carriers, fixtures, diagnostics, CI evidence, runtime evidence, or downstream rejection evidence according to the upstream architecture.

`resolved` and `production_ready` are derived audit conclusions, not authored fields in Project Gate records.
