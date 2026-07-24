# EV4 Project Gate Result Model

Status: active result-model documentation. The runtime verification and exact-byte publication primitives are implemented, but their existence does not mean the production Builder → Responsive or applicable Final Gate flow currently obtains and consumes an observed official runtime execution.

## Scope

This document describes Project Gate-owned result envelopes, runtime verification values, receipts and report behavior. It does not define any Architect, CE, Builder, or Responsive specialist payload semantics.

The following states are distinct:

```text
implemented runtime primitives
≠ production B2R runtime integration
≠ available Builder emitter
```

## Result schemas

```text
schemas/transition-result/transition-result.v1.schema.json
schemas/architect-to-ce-transition-result/architect-to-ce-transition-result.v1.schema.json
schemas/ce-to-builder-transition-result/ce-to-builder-transition-result.v1.schema.json
schemas/builder-to-responsive-transition-result/builder-to-responsive-transition-result.v1.schema.json
schemas/final-gate-result/final-gate-result.v1.schema.json
schemas/diagnostic/diagnostic.v1.schema.json
```

`transition-result.v1` is the common Stage Evidence Bundle validation result:

```yaml
schema_version: transition-result.v1
result_type: stage_bundle_validation
status: accepted | valid | repair_needed | insufficient_evidence | invalid
source_stage: architect | ce | builder | responsive | null
diagnostics: ordered diagnostic list
hashes: source bundle and payload canonical hashes when computable
provenance: preserved input provenance and producer identity
output: null
```

`valid` remains a legacy validation alias for the current Stage Bundle and Architect→CE implementation. The target transition vocabulary is:

```text
accepted
repair_needed
insufficient_evidence
invalid
```

`presentation/status_mapping.py` normalizes `valid` to `accepted` for exit-code and Persian presentation purposes.

## Status/schema correlation

```yaml
accepted:
  source_stage: architect | ce | builder | responsive
  diagnostics: empty or info-only
  source_bundle_hash: required non-null hashRecord with scope=source_bundle
  canonical_payload_hash: required non-null hashRecord with scope=payload
  source_provenance: required object with non-empty kind
  produced_by: required object with non-empty tool
valid:
  diagnostics: empty, info, or warning
  evidence_requirement: legacy compatibility, not a future-transition acceptance rule
repair_needed:
  diagnostics: at least one warning
  forbidden_diagnostics: error, insufficient_evidence
insufficient_evidence:
  diagnostics: at least one insufficient_evidence
  forbidden_diagnostics: error
invalid:
  diagnostics: at least one error
```

Transition-specific result schemas add stricter `accepted_requires` and evidence rules. They must fail closed when evidence, validator execution, schema identity, exact runtime binding, observed execution, snapshot identity, cleanup, integration wiring, or lock/hash verification is missing or contradictory.

## Diagnostic ordering

Diagnostics are ordered by:

```text
path → severity rank → code → message
```

Severity rank is:

```text
error
insufficient_evidence
warning
info
```

## Hash behavior

Project Gate result hashes use canonical JSON:

```yaml
algorithm: sha256
canonicalization: ev4-canonical-json.v1
encoding: utf8
object_keys: lexicographic
arrays: order_preserved
nan_infinity: rejected
unicode_normalization: not_applied
```

Canonical JSON hashing applies to Project Gate result objects. It must not be confused with exact-byte identity for an externally emitted runtime artifact. A verified runtime artifact preserves its original byte sequence and is never reconstructed from parsed JSON.

Progress/runtime state must not be appended after final result schema validation and must not be included in canonical result hashes.

## Official tool execution record

Project Gate-owned execution-record infrastructure lives under `src/ev4_transition/runners/`. Execution records are runtime evidence metadata for official specialist validators/adapters. They are not specialist schemas and do not encode specialist business rules.

Validator execution record minimum children:

```yaml
owner_repo: owner/repo of official validator
owner_commit: pinned owner commit
validator_path: repo-relative validator path
command: command list used by the runner
working_directory: repo-relative/safe working directory label
exit_code: integer or null
stdout_hash: SHA-256 of exact stdout bytes
stderr_hash: SHA-256 of exact stderr bytes
execution_record_hash: canonical digest
started_by: runner identity
timeout_policy:
  seconds: numeric timeout
  kill_process_tree: bool
parsed_result_ref: reference to parsed result source
```

Adapter execution record minimum children:

```yaml
owner_repo: owner/repo of official adapter
owner_commit: exact pinned owner commit
adapter_path: repo-relative adapter path
command_or_entrypoint: exact tool invocation
input_ref: input artifact reference
input_hash: SHA-256 of input bytes
output_ref: output artifact reference, if produced
output_hash: SHA-256 of exact output bytes, if produced
execution_record_hash: canonical digest
validator_after_adapter_ref: validator evidence reference when required
```

For an observed viewport execution, `ExecutionRecord.output_ref`, `ViewportEvidenceRun.artifact_ref`, and `ViewportRunVerification.verified_artifact_ref` must be identical. Their output hashes and the snapshot hash must derive from the same byte sequence read once from the exact producer output.

Raw stdout/stderr are not stored in execution records.

## Implemented viewport runtime primitives

### `ViewportEvidenceRun`

`ViewportEvidenceRun` is the typed internal record produced by the runtime execution helper. It can carry repository, commit, tool, working directory, subject, viewport, artifact ref/hash, capture status, validation status and the execution record.

### `ViewportRunVerification`

A successful verification may contain:

```yaml
classification: real_verified
positive_proof_verified: true
verified_repository: exact owner/repo
verified_commit: exact pinned commit
verified_tool_ref: exact repository-relative producer tool
verified_working_directory_ref: exact repository-relative cwd
verified_artifact_ref: canonical repository-relative output ref
ephemeral_artifact_path: null after official operational cleanup
artifact_snapshot: VerifiedArtifactSnapshot
execution_record_digest: canonical digest
verified_subject_ref: exact requested subject
verified_viewport: exact requested viewport
verified_run_id: exact producer run id
value: parsed JSON value for semantic use only
derived_receipt: metadata-only runtime receipt
```

The pure verifier may expose an ephemeral path while a bounded test worktree is alive. The official runtime helper clears that path after cleanup. No deleted temporary path is durable evidence.

### `VerifiedArtifactSnapshot`

```yaml
artifact_ref: canonical repository-relative reference
exact_bytes: immutable bytes excluded from repr
sha256: SHA-256 of exact_bytes
byte_length: exact byte count
```

The snapshot primitive is created only after repository, commit, tool, working-directory, output-reference, output-hash, subject, viewport, process, capture, producer-validation, schema and synthetic-conflict predicates pass.

A failed or insufficient-evidence verification contains no snapshot. Raw snapshot bytes must not appear in repr output, diagnostics, logs, receipts, service responses, UI state or JSON serialization.

### Runtime receipt

The active viewport runtime receipt identifier is:

```text
ev4_runtime_evidence_receipt_v2
```

Receipt identity derives only from:

```text
snapshot.artifact_ref
snapshot.sha256
snapshot.byte_length
```

The receipt contains metadata only. It never contains raw bytes, temporary paths, caller-authored paths or reconstructed JSON. A stored artifact and adjacent receipt remain non-authoritative without observed official execution.

### Cleanup revocation

```yaml
classification: insufficient_evidence
positive_proof_verified: false
reason: pinned_worktree_cleanup_failed
artifact_snapshot: null
ephemeral_artifact_path: null
execution_record_digest: null
verified_subject_ref: null
verified_viewport: null
verified_run_id: null
derived_receipt: null
```

Retained in-memory bytes cannot override incomplete cleanup.

### Exact-byte publication primitives

`stage_verified_artifact_snapshot()` stages `snapshot.exact_bytes` directly. Forbidden reconstruction sources include:

```text
json.dumps
canonical JSON serialization
parsed verification.value
a path inside the removed worktree
```

`verify_published_artifact_snapshot()` requires:

```yaml
exact_byte_equality: true
sha256_equality: true
byte_length_equality: true
```

Grouped publication uses no-overwrite publication, directory fsync, exact-byte reread, complete rollback, staging cleanup and truthful persisted-state diagnostics.

## Production B2R result integration gap

The production `transition_builder_to_responsive` function currently calls the general evidence resolver for viewport slots without supplying:

```yaml
runtime_run: observed ViewportEvidenceRun
expected_runtime_tool: exact pinned Builder tool path
```

It also does not invoke `execute_pinned_viewport_capture` itself. Therefore the production B2R result model does not currently receive a verified snapshot or metadata-only runtime receipt for viewport evidence, and file-only viewport artifacts correctly remain `insufficient_evidence`.

```yaml
production_b2r_calls_pinned_runtime_execution: false
production_b2r_passes_observed_runtime_run: false
production_b2r_passes_expected_runtime_tool: false
production_b2r_consumes_verified_snapshot: false
production_b2r_consumes_runtime_receipt: false
production_b2r_runtime_integration: not_implemented
```

The implemented runtime classes and helper functions are valid primitives, not evidence that the production B2R carrier is integrated.

## Applicable Final Gate integration gap

Applicable Final Gate viewport evidence resolution also currently omits the observed `runtime_run` and exact expected runtime tool. It does not consume the B2R verified snapshot and receipt as an observed runtime result.

```yaml
final_gate_observed_runtime_result_integration: not_implemented
final_gate_verified_snapshot_consumption: not_implemented
final_gate_runtime_receipt_consumption: not_implemented
viewport_runtime_authority: insufficient_evidence_until_observed_official_execution
```

Final Gate must remain fail-closed until the production runtime result is propagated and verified through the applicable Final Gate path.

## Builder owner dependency

The pinned Builder commit lacks the official viewport capture/export emitter and associated contract. This is separate from the production integration gap.

Adding the emitter alone does not complete the result flow. Completion requires:

1. implement the official Builder emitter;
2. pin its exact commit, tool path and contract;
3. wire B2R to call `execute_pinned_viewport_capture`;
4. pass the exact observed runtime result and expected tool through evidence resolution;
5. consume and publish the verified snapshot and receipt;
6. verify applicable Final Gate integration;
7. run exact-Head CI and obtain a fresh independent PR Inspector review.

## Deterministic failure mapping

Common runner failures remain fail-closed:

```yaml
validator_timeout: insufficient_evidence
adapter_timeout: insufficient_evidence
command_not_found: insufficient_evidence
validator_missing: insufficient_evidence
adapter_missing: insufficient_evidence
nonzero_exit_with_structured_repair: repair_needed
nonzero_exit_with_contract_violation: invalid
unparseable_output: insufficient_evidence
execution_crash_without_structured_result: insufficient_evidence
fallback_adapter_used: invalid
adapter_command_path_mismatch: invalid
```

Viewport mismatches for repository, commit, tool, working directory, output ref/hash, subject, viewport, schema, synthetic conflict, capture or validation cannot create a snapshot.

## Report rendering record

Persian report rendering is presentation over already-computed results:

```yaml
allowed:
  - deep copy result payload before rendering
  - map status to icon/text/tone/exit metadata
  - isolate technical fragments as LTR/copyable text
  - compute report-only hash excluding UI/progress-only events
forbidden:
  - mutate transition result object
  - change status
  - add diagnostics after final validation
  - repair missing evidence
  - normalize specialist output
  - reconstruct verified runtime artifact bytes
  - imply production runtime integration from primitive availability
  - include progress events in canonical final result hash
```

Output-write records must not report success/download availability unless atomic write has completed and the final path exists.

## Evidence rule

No result may be presented as `accepted` unless required evidence is explicit and the relevant production integration path actually observed and consumed it. Missing, empty, swapped, synthetic-only, unresolved, replay-only, cleanup-incomplete, integration-absent or unverified evidence must remain `insufficient_evidence` or `invalid`.

Current status:

```yaml
runtime_primitives: implemented
production_b2r_runtime_integration: not_implemented
official_builder_viewport_emitter: missing_in_pinned_builder_owner
applicable_final_gate_runtime_integration: not_implemented
real_non_synthetic_handoff: insufficient_evidence
root_operational_handoff_complete: false
```

Nothing in this result model proves responsive correctness, frontend correctness, accessibility completion, export validity, release readiness or production readiness.
