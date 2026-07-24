# EV4 Transition Boundary Map

Status: active boundary map. `src/ev4_transition/data/capability-status.v1.json` is the only machine-readable capability authority. This document summarizes current behavior and must not become a competing status registry.

## Status vocabulary

Project Gate transition decisions use:

```text
accepted
repair_needed
insufficient_evidence
invalid
```

`accepted` is allowed only when every transition-specific `accepted_requires` item is true and no blocking diagnostic exists.

## Architect → CE

```yaml
transition_id: ev4-architect-to-ce-transition@1.0.0
orchestration_baseline: implemented
cli_exposure: implemented
verification_state: synthetic_fixture_only
real_non_synthetic_handoff: insufficient_evidence
```

Allowed Project Gate behavior:

```text
Architect Stage Evidence Bundle
→ Project Gate envelope validation
→ pinned Architect/CE contract hash checks
→ official Architect validator
→ deterministic Project Gate projection using CE-owned mapping contract
→ official CE validator
→ Architect→CE transition result validation
```

Forbidden Project Gate behavior includes creating CE constructability decisions, proving Elementor buildability, authorizing Builder runtime, or claiming production readiness.

## CE → Builder

```yaml
transition_id: ev4-ce-to-builder-transition@1.0.0
orchestration_baseline: implemented
cli_exposure: guarded
owner_fixture_integration: verified
real_non_synthetic_handoff: insufficient_evidence
source_repository: rezahh107/EV4-Constructability-Engineer-Repo
source_commit: cfceec5c20269c75a1cc19b2675d7087cede4599
consumer_repository: rezahh107/EV4-Builder-Assistant-Repo
consumer_commit: 69a2c61edf6d06b4418ad770fcefbfdffcf275d6
project_gate_lock: contracts/locks/ce-to-builder-transition.v1.lock.json
project_gate_result_schema: schemas/ce-to-builder-transition-result/ce-to-builder-transition-result.v1.schema.json
```

Allowed Project Gate behavior:

```text
CE package / Builder executable package
→ Project Gate identity and evidence checks
→ exact CE/Builder lock verification
→ official CE package validator
→ official Builder Contract Gate
→ official Builder adapter
→ Builder-owned context schema
→ official Builder output validator
→ Project Gate CE→Builder result
```

Pinned owner-fixture integration proves the bounded integration only. It does not prove real non-synthetic Builder execution.

## Builder → Responsive

```yaml
transition_id: ev4-builder-to-responsive-transition@1.0.0
orchestration_baseline: implemented
cli_exposure: guarded
producer_repository: rezahh107/EV4-Builder-Assistant-Repo
producer_commit: 69a2c61edf6d06b4418ad770fcefbfdffcf275d6
consumer_repository: rezahh107/EV4-Responsive-Architect
consumer_commit: df74c7ba2ffbed1a4136b5ea6be6ce30db4e161a
owner_contract_lock: contracts/locks/builder-to-responsive-transition.v1.lock.json
official_responsive_input_validator: validation/e2e/run_builder_responsive_input_boundary_check.py
pinned_detached_execution_worktree: implemented
runtime_output_exact_binding: implemented
verified_artifact_snapshot: implemented
viewport_file_pair_authority: forbidden
viewport_runtime_result_interface: implemented_fail_closed
viewport_runtime_emitter: missing_in_pinned_builder_owner
real_non_synthetic_handoff: insufficient_evidence
project_gate_result_schema: schemas/builder-to-responsive-transition-result/builder-to-responsive-transition-result.v1.schema.json
```

The current Project Gate runtime authority is:

```text
materialize a detached worktree at the exact pinned Builder commit
→ execute the exact official Builder producer tool
→ read its emitted artifact exactly once
→ bind repository, commit, tool, working directory, output ref/hash, subject, viewport and process result
→ parse and validate the same bytes
→ create immutable VerifiedArtifactSnapshot only after all predicates pass
→ derive receipt metadata from the snapshot
→ remove and prune the worktree
→ return the snapshot with no temporary path
→ stage and publish snapshot.exact_bytes directly
```

The snapshot infrastructure, exact-byte staging and post-write byte/hash/length verification are implemented. A cleanup failure revokes the snapshot and receipt.

The pinned Builder owner does not currently define the required official viewport capture/export emitter. Project Gate must not add a fake emitter, reconstruct bytes from parsed JSON, authorize file-only evidence, or claim a real Builder → Responsive handoff.

Responsive owns a schema-bound Builder intake package and official validator at the pinned Responsive commit. That intake eligibility boundary is not responsive-correctness evidence.

## Final Evidence Gate

```yaml
gate_id: ev4-final-evidence-gate@1.0.0
orchestration_baseline: implemented
cli_exposure: guarded
prior_lock_chain: pinned_to_immutable_project_gate_commit
official_output_validator: validation/e2e/run_responsive_tree_architecture_refactor_check.py
viewport_runtime_authority: insufficient_evidence_until_observed_official_execution
real_non_synthetic_evidence: insufficient_evidence
project_gate_result_schema: schemas/final-gate-result/final-gate-result.v1.schema.json
```

The final gate verifies the immutable prior lock chain, Responsive-owned output schema and validator execution, explicit real-evidence presence, and runtime snapshot/receipt identity when viewport evidence is required. Synthetic fixtures, file-only receipts, parsed JSON equivalence and CI success cannot be promoted into frontend or production correctness.

## Report and UX boundary

Persian report rendering and UI presentation are non-authorizing layers over already-computed Project Gate results. Reports may explain a result but must not change transition status, add diagnostics after validation, repair evidence, normalize specialist output, reconstruct verified artifact bytes, or treat output-write failure as success.

## Evidence interpretation

A green Project Gate CI run proves only that the checked implementation, fixtures, immutable locks, owner-tool integrations and fail-closed behavior passed for the exact tested Head. It does not prove real Elementor execution, Responsive correctness, accessibility, export validity, release readiness, or production readiness.

Current limits must be read from `src/ev4_transition/data/capability-status.v1.json`. The active detailed runtime rule is `docs/EVIDENCE_TRUTH_SPINE.md`.
