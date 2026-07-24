# EV4 Project Gate Result Model

Status: active result-model documentation aligned with the current transition carriers, official runner records, durable verified-artifact snapshot, runtime evidence receipt, report rendering, and publication behavior.

## Scope

This document describes Project Gate-owned result envelopes and report behavior. It does not define any Architect, CE, Builder, or Responsive specialist payload semantics.

## Result schemas

```text
schemas/transition-result/transition-result.v1.schema.json
schemas/architect-to-ce-transition-result/architect-to-ce-transition-result.v1.schema.json
schemas/ce-to-builder-transition-result/ce-to-builder-transition-result.v1.schema.json
schemas/builder-to-responsive-transition-result/builder-to-responsive-transition-result.v1.schema.json
schemas/final-gate-result/final-gate-result.v1.schema.json
schemas/diagnostic/diagnostic.v1.schema.json
```

`transition-result.v1` is the common Stage Evidence Bundle validation result. It is intentionally narrow:

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

`valid` remains a legacy validation alias for the current Stage Bundle and Architect→CE implementation. The target Project Gate transition vocabulary is:

```text
accepted
repair_needed
insufficient_evidence
invalid
```

`presentation/status_mapping.py` normalizes `valid` to `accepted` for exit-code and Persian presentation purposes.

## Status/schema correlation

`transition-result.v1` enforces the target result correlation at carrier level:

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

Transition-specific result schemas add stricter `accepted_requires` and evidence interpretation rules. They must fail closed when evidence, validator execution, schema identity, exact runtime binding, snapshot identity, or lock/hash verification is missing or contradictory.

## Diagnostic ordering

Diagnostics must be deterministic. Current ordering is:

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

Project Gate result hashes use:

```yaml
algorithm: sha256
canonicalization: ev4-canonical-json.v1
encoding: utf8
object_keys: lexicographic
arrays: order_preserved
nan_infinity: rejected
unicode_normalization: not_applied
```

For `accepted`, each hash property has a property-specific scope: `source_bundle_hash.scope` must be `source_bundle`, and `canonical_payload_hash.scope` must be `payload`.

Canonical JSON hashing applies to Project Gate result objects. It must not be confused with exact-byte identity for an externally emitted runtime artifact. A verified runtime artifact preserves its original byte sequence and is never reconstructed from parsed JSON.

Progress/runtime state must not be appended after final result schema validation and must not be included in canonical result hashes.

## Official tool execution record

Project Gate-owned execution-record infrastructure lives under `src/ev4_transition/runners/`. Execution records are runtime evidence metadata for official specialist validators/adapters. They are not specialist schemas and do not encode specialist business rules.

Validator execution record minimum children:

```yaml
owner_repo: owner/repo of official validator
owner_commit: pinned owner commit; successful official validator runs must not use unknown
validator_path: repo-relative validator path
command: command list used by the runner
working_directory: repo-relative/safe working directory label
exit_code: integer or null if execution never completed
stdout_hash: SHA-256 of exact stdout bytes
stderr_hash: SHA-256 of exact stderr bytes
execution_record_hash: SHA-256 over canonical execution record without this field
started_by: runner identity
timeout_policy:
  seconds: numeric timeout
  kill_process_tree: bool
parsed_result_ref: reference to parsed result source, usually stdout:json
```

Adapter execution record minimum children:

```yaml
owner_repo: owner/repo of official adapter
owner_commit: pinned owner commit or explicit unresolved marker
adapter_path: repo-relative adapter path
command_or_entrypoint: command list or entrypoint name used by the runner; must execute adapter_path directly or through a trusted interpreter
input_ref: input artifact reference
input_hash: SHA-256 of canonical input/artifact bytes
output_ref: output artifact reference, if produced
output_hash: SHA-256 of exact output artifact bytes, if produced
execution_record_hash: SHA-256 over canonical execution record without this field
validator_after_adapter_ref: validator evidence reference required after adapter output is produced
```

For the official viewport operational path, `ExecutionRecord.output_ref`, the runtime run `artifact_ref`, and the verification `verified_artifact_ref` must be identical. `ExecutionRecord.output_hash`, the runtime run artifact hash, the verification actual hash, and the snapshot hash must all derive from the same byte sequence read once from the exact producer output.

Raw stdout/stderr are not stored in execution records. Only their hashes are retained.

## Viewport runtime verification result

`ViewportRunVerification` is the Project Gate runtime verification carrier. A positive result may contain:

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

The pure verifier may expose an ephemeral artifact path while a test worktree is alive. The official operational path clears that path after cleanup. No deleted temporary path is represented as durable state.

## Verified artifact snapshot

`VerifiedArtifactSnapshot` is a frozen, slotted internal value:

```yaml
artifact_ref: canonical repository-relative reference
exact_bytes: immutable bytes excluded from repr
sha256: SHA-256 of exact_bytes
byte_length: exact byte count
```

The official operational path reads the emitted artifact exactly once. Runtime hash, execution-record output hash, JSON parsing, semantic validation, snapshot identity, receipt metadata, and publication payload all originate from that one byte sequence.

The snapshot is created only after all repository, commit, tool, working-directory, output-reference, output-hash, subject, viewport, process, capture, producer-validation, schema, and synthetic-conflict predicates pass.

A failed or insufficient-evidence result contains no snapshot.

Raw snapshot bytes must not appear in:

```text
repr output
diagnostics
logs
receipts
service responses
UI state
JSON serialization
```

JSON-safe consumers use snapshot metadata only.

## Runtime evidence receipt

The active viewport runtime receipt schema identifier is:

```text
ev4_runtime_evidence_receipt_v2
```

`build_runtime_evidence_receipt(verification=...)` accepts only a successful exact-bound verification with a valid snapshot. Artifact identity is derived from:

```text
snapshot.artifact_ref
snapshot.sha256
snapshot.byte_length
```

The receipt contains metadata only. It never contains raw bytes, temporary paths, caller-authored paths, or reconstructed JSON.

A stored artifact and adjacent receipt remain non-authoritative when replayed without an observed official execution:

```yaml
classification: insufficient_evidence
positive_proof_verified: false
reason: official_runtime_execution_not_observed
```

## Cleanup revocation

Worktree cleanup is authority-bearing. Any cleanup failure revokes an otherwise successful result:

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

## Exact-byte staging and publication

`stage_verified_artifact_snapshot()` validates snapshot integrity and stages `snapshot.exact_bytes` directly.

Forbidden reconstruction sources include:

```text
json.dumps
canonical JSON serialization
parsed verification.value
a path inside the removed worktree
```

`verify_published_artifact_snapshot()` rereads the destination and requires:

```yaml
exact_byte_equality: true
sha256_equality: true
byte_length_equality: true
```

Grouped publication continues through `publish_staged_group()` with no-overwrite, hard-link publication, directory fsync, exact-byte reread, complete rollback, staged-file cleanup, and truthful persisted-state diagnostics.

## Deterministic failure mapping

Common runner failures remain fail-closed:

```yaml
validator_timeout:
  status: insufficient_evidence
  diagnostic: PG.VALIDATOR.TIMEOUT
adapter_timeout:
  status: insufficient_evidence
  diagnostic: PG.ADAPTER.TIMEOUT
command_not_found:
  status: insufficient_evidence
  diagnostic: PG.RUNNER.COMMAND_NOT_FOUND
validator_missing:
  status: insufficient_evidence
  diagnostic: PG.VALIDATOR.MISSING
adapter_missing:
  status: insufficient_evidence
  diagnostic: PG.ADAPTER.MISSING
nonzero_exit_with_structured_repair:
  status: repair_needed
  diagnostic: PG.VALIDATOR.REPAIR_NEEDED
nonzero_exit_with_contract_violation:
  status: invalid
  diagnostic: PG.VALIDATOR.CONTRACT_VIOLATION
unparseable_output:
  status: insufficient_evidence
  diagnostic: PG.RUNNER.UNPARSEABLE_OUTPUT
execution_crash_without_structured_result:
  status: insufficient_evidence
  diagnostic: PG.RUNNER.EXECUTION_FAILED
fallback_adapter_used:
  status: invalid
  diagnostic: PG.ADAPTER.FALLBACK_FORBIDDEN
adapter_command_path_mismatch:
  status: invalid
  diagnostic: PG.ADAPTER.COMMAND_PATH_MISMATCH
```

Viewport-specific mismatches for repository, commit, tool, working directory, output ref/hash, subject, viewport, schema, synthetic conflict, capture, or validation remain fail-closed and cannot create a snapshot.

## Report rendering record

Persian report rendering is a presentation layer over already-computed Project Gate results:

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
  - include progress events in canonical final result hash
```

Output-write records must not report success/download availability unless atomic write has completed and the final path exists.

## Progress events

Progress events are runtime/UI artifacts only. They must not be included in canonical final result hashes.

Progress event sanitization rejects:

```yaml
- secret/token/password/API-key-like keys or values
- raw environment variables
- raw stdout
- raw stderr
- raw verified artifact bytes
- private absolute paths unless explicitly allowed
```

By default, paths in progress events are converted to repo-relative paths when a `repo_root` is provided.

## Evidence rule

No result may be presented as `accepted` unless the required evidence for that result scope is explicit. Missing, empty, swapped, synthetic-only, unresolved, replay-only, cleanup-incomplete, or unverified evidence must remain `insufficient_evidence` or `invalid` according to the diagnostic set.

The implemented snapshot infrastructure does not itself prove a real Builder → Responsive handoff. Until the pinned Builder owner provides an official viewport capture/export emitter and Project Gate observes that execution, real runtime capability remains `insufficient_evidence`.
