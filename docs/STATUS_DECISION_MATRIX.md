# EV4 Project Gate Status Decision Matrix

Status: active status and fail-closed decision matrix. `src/ev4_transition/data/capability-status.v1.json` remains the only machine-readable capability authority.

## Target Project Gate statuses

| Status | Meaning | Exit code | Presentation |
|---|---|---:|---|
| `accepted` | Required evidence for this check is explicit and no blocking diagnostic exists. | `0` | ✅ / success / پذیرفته شد |
| `repair_needed` | Input is structurally understandable, but repairable warning diagnostics exist. | `1` | 🛠️ / warning / نیازمند اصلاح |
| `insufficient_evidence` | Input is parseable/understood, but required evidence is missing or unresolved. | `2` | ⚠️ / warning / شواهد کافی نیست |
| `invalid` | Input violates schema, identity, hash, lock, runtime binding, or fail-closed rules. | `1` | ❌ / danger / نامعتبر |

`insufficient_evidence` is a warning/blocking state, not ordinary info.

## Diagnostic-to-status mapping

Target transition mapping:

```yaml
error: invalid
insufficient_evidence: insufficient_evidence
warning: repair_needed
none_or_info_only: accepted
```

Legacy validation mapping remains only for older Stage Bundle and Architect→CE paths:

```yaml
error: invalid
insufficient_evidence: insufficient_evidence
none_or_warning_or_info: valid
```

## Builder → Responsive accepted policy

`ev4-builder-to-responsive-transition@1.0.0` may emit `accepted` only when all applicable requirements are true:

```yaml
builder_evidence_refs_present: true
builder_lock_hashes_match: true
builder_repository_exact: true
builder_commit_exact: true
official_builder_viewport_tool_exists: true
official_builder_viewport_tool_executed: true
producer_tool_ref_exact: true
working_directory_ref_exact: true
process_exit_zero: true
capture_status_completed: true
producer_validation_accepted: true
output_ref_binding_exact: true
output_hash_binding_exact: true
subject_binding_exact: true
viewport_binding_exact: true
artifact_schema_valid: true
synthetic_conflict_absent: true
verified_artifact_snapshot_present: true
snapshot_hash_valid: true
snapshot_byte_length_valid: true
pinned_worktree_cleanup_complete: true
responsive_input_schema_verified: true
responsive_input_validator_passed: true
no_forbidden_claim: true
result_schema_valid: true
```

The official operational path must create the verified snapshot from the same byte sequence read once from the exact producer output. Parsed JSON, a caller-authored execution record, a file-only artifact/receipt pair, or a path inside a removed worktree cannot authorize `accepted`.

Builder → Responsive must emit `insufficient_evidence` when any required owner checkout, official Builder emitter, observed official execution, snapshot, cleanup proof, Responsive schema, or official Responsive validator execution is absent or unverifiable.

The current pinned Builder owner does not provide the official viewport capture/export emitter. Therefore current real non-synthetic Builder → Responsive capability remains `insufficient_evidence` even though Project Gate's pinned-worktree verifier, exact output binding, immutable snapshot, and exact-byte publication infrastructure are implemented.

Builder → Responsive must emit `invalid` when a lock/hash/schema identity mismatch, exact runtime binding mismatch, synthetic conflict, or forbidden readiness/correctness claim is detected.

## Snapshot and publication policy

A positive runtime verification may retain:

```yaml
artifact_snapshot:
  artifact_ref: canonical repository-relative reference
  exact_bytes: immutable internal bytes
  sha256: SHA-256 of exact_bytes
  byte_length: exact byte count
ephemeral_artifact_path: null after operational cleanup
```

Publication must stage `snapshot.exact_bytes` directly. It must not reconstruct bytes with `json.dumps`, canonical serialization, parsed JSON, or a stale temporary path. Post-write verification requires exact byte equality, SHA-256 equality, and byte-length equality.

A cleanup failure revokes positive proof:

```yaml
classification: insufficient_evidence
positive_proof_verified: false
reason: pinned_worktree_cleanup_failed
artifact_snapshot: null
ephemeral_artifact_path: null
derived_receipt: null
```

## Final Evidence Gate accepted policy

`ev4-final-evidence-gate@1.0.0` may emit `accepted` only when all applicable requirements are true:

```yaml
prior_lock_chain_verified: true
responsive_output_present: true
responsive_output_schema_verified: true
responsive_output_validator_passed: true
real_evidence_present: true
observed_official_runtime_execution_present_when_required: true
verified_runtime_snapshot_identity_consistent_when_required: true
runtime_receipt_identity_consistent_when_required: true
no_forbidden_final_claim: true
result_schema_valid: true
```

The Final Gate must emit `invalid` for `production_ready`, `release_ready`, `frontend_correctness`, `responsive_correctness`, `pixel_perfect`, `accessibility_passed`, `export_json_validated`, or equivalent claims unless owner evidence and owner validators explicitly authorize them.

The Final Gate must emit `insufficient_evidence` when real non-synthetic Responsive evidence, observed official viewport execution when required, verified snapshot identity, Responsive output schema access, official validator execution, or prior lock-chain verification is missing.

## CI and screenshot limits

CI success is never frontend correctness evidence. Raw screenshots are never sufficient to prove responsive correctness. These inputs can be recorded as artifacts, but they cannot unlock `accepted` unless they are tied to explicit owner-validated evidence contracts and the active runtime authority requirements.
