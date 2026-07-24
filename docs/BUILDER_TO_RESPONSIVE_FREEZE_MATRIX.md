# Builder → Responsive Freeze Matrix

Status: active owner-boundary matrix. Project Gate implements the reusable pinned-runtime verification and exact-byte publication primitives, but the production Builder → Responsive transition is not yet wired to execute and consume an observed official runtime run. The pinned Builder owner also lacks the required official viewport capture/export emitter. Real non-synthetic handoff therefore remains `insufficient_evidence`.

## Non-equivalence rule

```text
implemented runtime primitives
≠ production B2R runtime integration
≠ available Builder emitter
```

These three states must be reported separately.

## Authority rule

- Builder owns Builder artifacts, execution evidence, and the official viewport producer/export tool and contract.
- Responsive owns the Builder-specific intake schema, intake validator, Responsive output contracts, and Responsive behavior.
- Project Gate owns exact pinning, deterministic orchestration, runtime execution isolation, evidence binding, result envelopes, receipts, and safe publication.
- Project Gate must not copy specialist schemas, invent missing evidence, reconstruct exact bytes from parsed JSON, fabricate an official Builder emitter, or treat file-only viewport evidence as observed execution.

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

The current lock binds the relevant Builder schemas, validators and boundary document plus the Responsive Builder-input boundary, schema and official validator. It does not pin an official Builder viewport emitter because none exists at the pinned Builder commit.

## Implemented Project Gate primitives

The following primitives are implemented and regression-tested:

```yaml
pinned_detached_execution_worktree: implemented
runtime_output_exact_binding: implemented
one_read_emitted_artifact_handling: implemented
verified_artifact_snapshot: implemented
metadata_only_runtime_receipt: implemented
cleanup_failure_revocation: implemented
exact_byte_snapshot_staging: implemented
post_write_exact_byte_verification: implemented
grouped_publication_rollback: implemented
viewport_file_pair_authority: forbidden
viewport_runtime_result_interface: implemented_fail_closed
```

### Primitive lifecycle

```text
execute_pinned_viewport_capture
→ verify Builder repository and exact pinned commit
→ materialize a clean detached worktree
→ execute the exact supplied official producer tool
→ read the emitted artifact exactly once
→ derive runtime and ExecutionRecord output hashes from those bytes
→ bind repository, commit, tool, cwd, output ref/hash, subject, viewport and process result
→ parse and validate the same byte sequence
→ create immutable VerifiedArtifactSnapshot only after all positive predicates pass
→ derive metadata-only receipt identity
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

Publication primitives consume `snapshot.exact_bytes` directly. They do not use parsed `verification.value`, `json.dumps`, canonical JSON reconstruction, or a path inside a removed worktree. Post-write verification requires exact byte equality, SHA-256 equality and byte-length equality. Cleanup failure revokes positive proof, snapshot and receipt.

## Production B2R integration state

The production `transition_builder_to_responsive` path is not yet integrated with the pinned runtime execution primitive.

Current production behavior:

```yaml
calls_execute_pinned_viewport_capture: false
supplies_observed_runtime_run_to_viewport_resolution: false
supplies_exact_expected_runtime_tool_to_viewport_resolution: false
consumes_verified_artifact_snapshot_for_b2r_publication: false
consumes_metadata_only_runtime_receipt_for_b2r_publication: false
production_b2r_runtime_integration: not_implemented
```

The production transition currently resolves viewport evidence through the general evidence resolver without an observed `runtime_run` and exact expected runtime tool. Under the active runtime-execution policy, this correctly yields `official_runtime_execution_not_observed` or another fail-closed state rather than `real_verified`.

The presence of `execute_pinned_viewport_capture`, `VerifiedArtifactSnapshot`, receipt derivation and exact-byte publication helpers does not itself integrate them into the production B2R route.

## Final Gate integration state

Applicable Final Gate viewport evidence resolution also does not currently receive and consume the observed verified runtime result, snapshot and receipt.

```yaml
final_gate_observed_runtime_result_integration: not_implemented
final_gate_verified_snapshot_consumption: not_implemented
final_gate_runtime_receipt_consumption: not_implemented
viewport_runtime_authority: insufficient_evidence_until_observed_official_execution
```

Final Gate must remain fail-closed until the production B2R runtime result is carried through the applicable evidence path and independently verified at the Final Gate boundary.

## Builder owner state

The pinned Builder boundary document is explicit:

```yaml
builder_formal_responsive_export:
  status: not_implemented
  schema_file: null
  validator: null
  fixture_suite: null
builder_official_viewport_capture_or_export_emitter:
  status: missing_in_pinned_builder_owner
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

These artifacts may support a handoff, but none substitutes for an observed official viewport producer execution.

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

Passing this validator proves contract eligibility only. It does not prove responsive correctness, frontend correctness, accessibility completion, export validity, release readiness or production readiness.

## Accepted-result requirements

Builder → Responsive may become `accepted` only when all applicable requirements are true:

```yaml
owner_contract_lock_verified: true
builder_repository_exact: true
builder_commit_exact: true
official_builder_viewport_tool_exists: true
official_builder_viewport_tool_contract_pinned: true
official_builder_viewport_tool_executed: true
production_b2r_calls_execute_pinned_viewport_capture: true
observed_runtime_run_passed_to_evidence_resolution: true
expected_runtime_tool_passed_to_evidence_resolution: true
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
verified_snapshot_and_receipt_consumed_by_b2r: true
responsive_input_schema_verified: true
responsive_input_validator_passed: true
applicable_final_gate_runtime_integration_verified: true
result_schema_valid: true
```

## Fail-closed matrix

| Condition | Result |
|---|---|
| Official Builder viewport emitter missing | `insufficient_evidence` |
| Production B2R does not invoke pinned runtime execution | `insufficient_evidence` |
| Observed runtime run or exact expected tool not passed to evidence resolution | `insufficient_evidence` |
| File-only artifact/receipt replay | `insufficient_evidence` |
| Cleanup incomplete | `insufficient_evidence`, snapshot and receipt revoked |
| Repository, commit, tool, cwd, output ref, hash, subject or viewport mismatch | `invalid` or fail-closed diagnostic according to the active verifier |
| Parsed JSON matches but exact bytes/hash/length differ | publication failure and rollback |
| B2R does not consume/publish the verified snapshot and receipt | root operational handoff incomplete |
| Applicable Final Gate integration absent | Final Gate remains `insufficient_evidence` |
| Responsive schema or official validator unavailable | `insufficient_evidence` |
| Contract/hash/schema identity mismatch or forbidden correctness claim | `invalid` |
| Synthetic-only evidence presented as real | blocked; never `accepted` |

## Explicit status

```yaml
project_gate_runtime_primitives: implemented
production_b2r_runtime_integration: not_implemented
official_builder_viewport_emitter_found: false
official_builder_viewport_emitter_executed: false
applicable_final_gate_runtime_integration: not_implemented
real_non_synthetic_handoff: insufficient_evidence
root_operational_handoff_complete: false
responsive_correctness_claimed: false
frontend_correctness_claimed: false
accessibility_completion_claimed: false
export_validation_claimed: false
release_ready_claimed: false
production_ready_claimed: false
```

## Remaining implementation sequence

```yaml
remaining_actions:
  - implement the official Builder viewport capture/export emitter
  - define and pin its exact Builder commit, tool path and contract
  - wire production B2R to call execute_pinned_viewport_capture
  - pass the exact observed runtime result and exact expected tool through evidence resolution
  - consume and publish the verified snapshot and metadata-only receipt
  - verify applicable Final Gate runtime integration
  - run exact-Head CI
  - obtain a fresh independent PR Inspector review
```

The Builder owner is not the sole remaining dependency. Both the owner emitter and Project Gate production integration are required. Adding the emitter alone does not complete the root operational handoff.
