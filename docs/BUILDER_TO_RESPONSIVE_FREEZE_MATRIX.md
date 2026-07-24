# Builder → Responsive Freeze Matrix

Status: active owner-boundary matrix aligned with the current Project Gate implementation. The orchestration, pinned-worktree runtime verifier, exact output binding, immutable verified-artifact snapshot, and exact-byte publication support are implemented. Real non-synthetic handoff remains `insufficient_evidence` because the pinned Builder owner does not provide the required official viewport capture/export emitter.

## Authority rule

- Builder owns Builder artifacts, execution evidence, and any official viewport producer/export tool.
- Responsive owns the Builder-specific intake schema, intake validator, Responsive output contracts, and Responsive behavior.
- Project Gate owns exact pinning, deterministic orchestration, runtime execution isolation, evidence binding, result envelopes, receipts, and safe publication.
- Project Gate must not copy specialist schemas, invent missing evidence, reconstruct exact bytes from parsed JSON, or fabricate an official Builder emitter.

## Active pins

```yaml
builder:
  repository: rezahh107/EV4-Builder-Assistant-Repo
  commit: 69a2c61edf6d06b4418ad770fcefbfdffcf275d6
responsive:
  repository: rezahh107/EV4-Responsive-Architect
  commit: df74c7ba2ffbed1a4136b5ea6be6ce30db4e161a
project_gate_lock: contracts/locks/builder-to-responsive-transition.v1.lock.json
lock_state: computed_from_pinned_owner_file_bytes
transition_id: ev4-builder-to-responsive-transition@1.0.0
```

The lock currently binds the relevant Builder schemas/validators and boundary document plus the Responsive Builder-input boundary, schema, and official validator.

## Current Project Gate implementation

```yaml
orchestration_baseline: implemented
cli_exposure: guarded
pinned_detached_execution_worktree: implemented
runtime_output_exact_binding: implemented
verified_artifact_snapshot: implemented
exact_byte_snapshot_staging: implemented
post_write_exact_byte_verification: implemented
viewport_file_pair_authority: forbidden
viewport_runtime_result_interface: implemented_fail_closed
official_responsive_validator_integration: implemented
real_non_synthetic_handoff: insufficient_evidence
```

### Exact runtime lifecycle

```text
verify Builder repository and exact pinned commit
→ materialize a clean detached worktree
→ execute the exact official viewport producer tool inside that worktree
→ read the emitted artifact exactly once
→ derive runtime and ExecutionRecord output hashes from those bytes
→ bind repository, commit, tool, cwd, output ref/hash, subject, viewport and process result
→ parse and validate the same byte sequence
→ create immutable VerifiedArtifactSnapshot only after all positive predicates pass
→ derive receipt metadata from the snapshot
→ remove and prune the worktree
→ return durable snapshot bytes with ephemeral_artifact_path=null
```

`VerifiedArtifactSnapshot` contains:

```yaml
artifact_ref: canonical repository-relative reference
exact_bytes: immutable bytes excluded from repr
sha256: SHA-256 of exact_bytes
byte_length: exact byte count
```

Publication consumes `snapshot.exact_bytes` directly. It must not use parsed `verification.value`, `json.dumps`, canonical JSON reconstruction, or a deleted worktree path. Post-write verification requires exact byte equality, SHA-256 equality, and byte-length equality.

Cleanup is authority-bearing. Any worktree cleanup failure revokes positive proof, snapshot, and receipt and returns `insufficient_evidence`.

## Builder owner state

The pinned Builder boundary document is explicit:

```yaml
builder_formal_responsive_export:
  status: not_implemented
  schema_file: null
  validator: null
  fixture_suite: null
builder_official_viewport_capture_or_export_emitter:
  status: not_implemented_at_pinned_commit
```

Builder does provide pinned evidence surfaces consumed by the lock:

```yaml
builder_context_package:
  schema: ev4-builder-context-package@1.0.0
  schema_file: schemas/builder-context-package.schema.json
  validator: scripts/validate-package.mjs

action_batch:
  schema: ev4-action-batch@1.0.0
  schema_file: schemas/action-batch.schema.json
  validator: scripts/validate-action-batch.mjs

layout_check:
  schema: ev4-layout-check@0.1.0
  schema_file: schemas/layout-check.schema.json
  validator: scripts/validate-layout-check.mjs

completion_gate:
  schema: ev4-completion-gate@0.1.0
  schema_file: schemas/completion-gate.schema.json
  validator: scripts/validate-completion-gate.mjs

real_elementor_execution_evidence:
  schema: ev4-real-elementor-execution-evidence@1.0.0
  schema_file: schemas/real-elementor-execution-evidence.schema.json
  validator: scripts/validate-real-elementor-execution-evidence.mjs
```

These artifacts may support a handoff, but none substitutes for the missing observed official viewport producer execution.

## Responsive owner state

The pinned Responsive owner has an implemented schema-bound, non-executing Builder intake eligibility boundary:

```yaml
builder_to_responsive_input_package:
  status: schema_bound_non_executing
  schema: ev4-builder-responsive-input@0.1.0
  schema_file: schemas/ev4-builder-responsive-input.schema.json
  validator: validation/e2e/run_builder_responsive_input_boundary_check.py
  claim_boundary: input eligibility only; not responsive correctness evidence
```

Responsive also owns its output schema and validators. Passing the intake validator proves contract eligibility only. It does not prove frontend correctness, responsive correctness, accessibility completion, export validity, release readiness, or production readiness.

## Accepted-result requirements

Builder → Responsive may become `accepted` only when all applicable requirements are true:

```yaml
owner_contract_lock_verified: true
builder_repository_exact: true
builder_commit_exact: true
official_builder_viewport_tool_exists: true
official_builder_viewport_tool_executed: true
working_directory_exact: true
process_completed_successfully: true
capture_status_completed: true
producer_validation_accepted: true
output_ref_binding_exact: true
output_hash_binding_exact: true
subject_binding_exact: true
viewport_binding_exact: true
artifact_schema_valid: true
synthetic_conflict_absent: true
verified_artifact_snapshot_present: true
snapshot_hash_and_length_valid: true
pinned_worktree_cleanup_complete: true
responsive_input_schema_verified: true
responsive_input_validator_passed: true
result_schema_valid: true
```

## Fail-closed matrix

| Condition | Result |
|---|---|
| Official Builder viewport emitter missing | `insufficient_evidence` |
| Official execution not observed | `insufficient_evidence` |
| File-only artifact/receipt replay | `insufficient_evidence` |
| Cleanup incomplete | `insufficient_evidence`, snapshot and receipt revoked |
| Repository, commit, tool, cwd, output ref, hash, subject or viewport mismatch | `invalid` or fail-closed diagnostic according to the active verifier |
| Parsed JSON matches but exact bytes/hash/length differ | publication failure and rollback |
| Responsive schema or official validator unavailable | `insufficient_evidence` |
| Contract/hash/schema identity mismatch or forbidden correctness claim | `invalid` |
| Synthetic-only evidence presented as real | blocked; never `accepted` |

## Explicit non-claims

```yaml
project_gate_builder_to_responsive_orchestration: implemented
project_gate_exact_byte_snapshot_repair: implemented
builder_runtime_behavior_changed: false
responsive_repair_behavior_changed: false
official_builder_viewport_emitter_found: false
official_builder_viewport_emitter_executed: false
real_elementor_validation_claimed: false
frontend_correctness_claimed: false
responsive_correctness_claimed: false
accessibility_completion_claimed: false
export_validation_claimed: false
production_ready_claimed: false
root_operational_handoff_complete: false
```

## Remaining owner action

```yaml
required_owner: rezahh107/EV4-Builder-Assistant-Repo
required_change: official viewport capture/export adapter returning the bounded runtime result expected by Project Gate
follow_up_after_owner_change:
  - pin the new Builder commit and exact owner files
  - update the Builder → Responsive lock
  - execute exact-head Project Gate validation
  - run a real non-synthetic Builder → Responsive handoff
  - verify Final Gate behavior with observed official runtime evidence
```

Until that owner dependency is implemented and pinned, `viewport_real_verified_capability` and the root operational handoff remain `insufficient_evidence`.
