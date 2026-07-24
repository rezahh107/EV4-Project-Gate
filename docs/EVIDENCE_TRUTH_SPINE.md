# Project Gate Evidence Truth Spine

## Scope

Project Gate may derive consequential viewport runtime authority only from an execution it performs inside a clean detached Git worktree at an exact pinned owner commit.

This document defines implemented runtime verification and exact-byte publication primitives and the authority conditions they enforce. It does not claim that the production `transition_builder_to_responsive` or applicable Final Gate path currently invokes and consumes those primitives.

```text
ordinary owner checkout (may be dirty)
→ verify owner repository and pinned commit object
→ materialize detached clean worktree at the pinned commit
→ execute the official tool inside that worktree
→ internally create ExecutionRecord and ViewportEvidenceRun
→ read the emitted artifact bytes exactly once
→ verify repository, commit, tool, working directory, output reference and bytes
→ create an immutable exact-byte snapshot after every predicate passes
→ derive an audit receipt from snapshot metadata
→ remove and prune the temporary worktree
→ return durable bytes without returning a stale temporary path
```

This mechanism provides reproducible execution bytes. It is not cryptographic attestation, an authorization service, a hostile-process control, an external trust system, or a persistent artifact store.

## Evidence policy

| Evidence type | Required positive proof |
|---|---|
| Architect, Builder, Responsive and Kernel-owned artifacts with official validators | Accepted official owner validator |
| Viewport runtime artifact | Exact-bound result from Project Gate's pinned-worktree execution path, observed and passed through the applicable production transition |

Keyword and fixture-marker scanning remains rejection-only. Caller fields such as `real_evidence`, `evidence_status`, `verification_status`, `classification` and `synthetic: false` cannot create authority.

## Pinned execution worktree

`materialize_pinned_worktree()` accepts an existing local owner checkout. The source checkout may contain staged, unstaged or untracked operator files; those files are not executed.

The utility:

1. verifies the source checkout origin;
2. verifies the pinned commit object exists locally;
3. creates a temporary detached worktree at that commit;
4. independently verifies its repository and exact `HEAD`;
5. requires an initially clean worktree, including no untracked files;
6. yields a canonical resolved root;
7. removes the worktree in `finally`;
8. prunes Git worktree metadata;
9. returns deterministic cleanup diagnostics and fails closed when cleanup is incomplete.

After execution, Project Gate also verifies that tracked worktree bytes remain equal to `HEAD`. Untracked runtime output is allowed only when it is referenced and verified by the exact runtime result.

## Canonical repository-relative references

Runtime identity uses canonical POSIX references:

```text
producer_tool_ref: scripts/capture-viewports.py
working_directory_ref: .
artifact_ref: runtime/desktop.json
```

References are rejected when they are absolute, Windows drive-qualified, contain backslashes, contain `.` or `..` path components, traverse outside the worktree, resolve through a symlink, or identify the wrong file type. Invalid references are never rewritten into another identity. In particular, `runtime/desktop.json` can never fall back to `desktop.json`.

## Operational runner and pure verifier

The two interfaces have different authority roles.

```yaml
pure_verifier:
  function: verify_viewport_evidence_run
  purpose: isolated tests, diagnostics and verification of an internally produced value
  caller_supplied_checkout_authoritative: false

official_operational_primitive:
  function: execute_pinned_viewport_capture
  accepts: source checkout, pinned repository and commit, tool ref, working-directory ref, subject, viewport, timeout
  internally_creates:
    - detached pinned worktree
    - process result
    - ExecutionRecord
    - ViewportEvidenceRun
    - exact-bound verification
    - immutable artifact snapshot
    - derived receipt
```

The operational caller does not supply the execution record, exit status, output reference, output hash, receipt digest, capture success or validation success.

`execute_pinned_viewport_capture` is implemented as a reusable primitive. The production B2R transition does not currently invoke it or provide its observed result and exact expected tool to viewport evidence resolution.

## Exact runtime bindings

A viewport result can become `real_verified` only when all of the following hold.

### Repository and commit

```text
worktree.repository
== expected_repository
== run.producer_repository
== execution_record.owner_repo
```

```text
worktree.commit
== expected_commit
== run.producer_commit
== execution_record.owner_commit
```

### Tool and working directory

```text
run.producer_tool_ref
== expected_tool_ref
== execution_record.adapter_path
```

The tool must be a regular non-symlink file inside the detached worktree and the executed command must invoke that exact file.

```text
run.working_directory_ref
== expected_working_directory_ref
== execution_record.working_directory_ref
== actual subprocess cwd relative to the worktree
```

### Output path and bytes

```text
execution_record.output_ref
== run.artifact_ref
== verification.verified_artifact_ref
```

```text
SHA256(observed artifact bytes)
== run.artifact_sha256
== execution_record.output_hash
== verification.actual_sha256
== verification.artifact_snapshot.sha256
```

Path equality and hash equality are both mandatory. Identical bytes at two paths do not satisfy the binding.

### Process and content

The record must be an adapter execution with exit code `0`, no failure code, an exact tool entrypoint, a completed capture and an explicitly accepted producer validation result. Run ID, subject and viewport must match the request, runtime result and artifact content. Synthetic conflicts remain fail-closed.

## Durable exact-byte snapshot

`VerifiedArtifactSnapshot` is a frozen in-memory value containing:

```yaml
artifact_ref: canonical repository-relative reference
exact_bytes: immutable bytes, excluded from repr
sha256: SHA-256 of exact_bytes
byte_length: exact byte count
```

The artifact is read once on the official operational primitive path. Hashing, UTF-8 JSON parsing, the snapshot, receipt metadata and publication payload all originate from that same byte sequence. Parsed JSON remains separately available as `ViewportRunVerification.value`; it is never reserialized to reconstruct the verified artifact.

The snapshot is created only after all positive-proof predicates pass. Synthetic, invalid or insufficient-evidence results contain no snapshot.

While the pure verifier runs inside a live worktree it may expose `ephemeral_artifact_path`. After `execute_pinned_viewport_capture()` returns, the worktree has been removed and the primitive result always exposes:

```yaml
artifact_snapshot: present only for real_verified
ephemeral_artifact_path: null
```

No deleted temporary path is represented as durable state.

## Cleanup failure revocation

Worktree cleanup remains authority-bearing. Any cleanup failure revokes the otherwise successful result:

```yaml
classification: insufficient_evidence
positive_proof_verified: false
reason: pinned_worktree_cleanup_failed
artifact_snapshot: null
ephemeral_artifact_path: null
derived_receipt: null
```

Retained in-memory bytes do not override incomplete cleanup.

## Receipt boundary

`build_runtime_evidence_receipt(verification=...)` accepts only a successful exact-bound verification with a valid snapshot. Artifact identity comes from snapshot metadata:

```text
artifact_ref
artifact_sha256
artifact_byte_length
```

The receipt never contains raw artifact bytes, temporary paths, caller paths, or reconstructed JSON. Schema `ev4_runtime_evidence_receipt_v2` remains a deterministic audit/debug record, not positive-proof input.

A stored artifact and adjacent receipt, even when every field and digest matches, remain:

```yaml
classification: insufficient_evidence
positive_proof_verified: false
reason: official_runtime_execution_not_observed
```

## Exact-byte publication

`stage_verified_artifact_snapshot()` validates snapshot integrity and stages `snapshot.exact_bytes` directly. It does not call `json.dumps`, canonical serialization, or a deleted worktree path.

The existing `publish_staged_group()` transaction remains the grouped publication primitive:

```text
stage exact artifact bytes and receipt bytes
→ assert every destination unused
→ link every destination
→ fsync destination directories
→ reread and compare every exact byte sequence
→ remove staging files
→ return published_verified records
```

Post-write semantic JSON equality is insufficient. Direct byte equality, SHA-256 equality and byte-length equality are required. Any mismatch invokes the existing complete rollback, cleanup and persisted-state diagnostics.

Raw snapshot bytes are excluded from snapshot and staging dataclass representations. JSON-safe consumers use snapshot metadata only; bytes are not base64 encoded into logs, receipts, service responses or UI state.

The existence of these publication helpers does not mean the production B2R route currently consumes and publishes a verified viewport snapshot and receipt.

## Production integration and owner dependencies

The following states are separate:

```text
implemented runtime primitives
≠ production B2R runtime integration
≠ available Builder emitter
```

### Project Gate production integration gap

The production `transition_builder_to_responsive` path currently resolves viewport evidence without supplying an observed `runtime_run` and exact expected runtime tool. It does not call `execute_pinned_viewport_capture` or consume/publish the resulting snapshot and receipt.

Applicable Final Gate viewport evidence resolution also does not currently consume the observed verified runtime result, snapshot and receipt.

```yaml
production_b2r_calls_execute_pinned_viewport_capture: false
production_b2r_passes_observed_runtime_run: false
production_b2r_passes_expected_runtime_tool: false
production_b2r_consumes_verified_snapshot_and_receipt: false
applicable_final_gate_runtime_integration: not_implemented
```

### Builder owner dependency

The pinned Builder revision is:

```yaml
repository: rezahh107/EV4-Builder-Assistant-Repo
commit: 69a2c61edf6d06b4418ad770fcefbfdffcf275d6
```

Its Builder→Responsive boundary is documented but the formal export and compatible viewport capture emitter are not implemented. The pinned Responsive intake is schema-bound and non-executing.

```yaml
verified_artifact_snapshot_complete: true
exact_bytes_survive_cleanup: true
publication_from_exact_bytes_supported: true
production_b2r_runtime_integration: not_implemented
official_viewport_emitter_found: false
official_viewport_emitter_executed: false
applicable_final_gate_runtime_integration: not_implemented
viewport_real_verified_capability: insufficient_evidence
root_operational_handoff_complete: false
```

The Builder owner is not the sole remaining implementation dependency. Adding the emitter alone does not complete the root operational handoff.

Remaining sequence:

1. implement the official Builder viewport capture/export emitter;
2. pin its exact commit, tool path and contract;
3. wire production B2R to call `execute_pinned_viewport_capture`;
4. pass the exact observed runtime result and exact expected tool through evidence resolution;
5. consume and publish the verified snapshot and metadata-only receipt;
6. verify applicable Final Gate integration;
7. run exact-Head CI and obtain a fresh independent PR Inspector review.

## A2C publication transaction

The existing Architect→CE publication repair remains unchanged. A denied handoff returns before path resolution, staging, receipt construction or publication. An authorized CE input and A2C receipt are committed through `publish_staged_group()` and are reported as `published_verified` only after both links, directory fsync, exact-byte verification and staged-file cleanup succeed.

Any failure rolls back all linked Project Gate artifacts, removes staged files, preserves the original error and separately reports rollback or cleanup failures and truthful persisted state.

## Capability truth

`src/ev4_transition/data/capability-status.v1.json` remains the sole machine-readable authority. Pinned-worktree verification, exact runtime binding, durable exact-byte snapshot and exact-byte publication primitives are implemented. Production B2R runtime integration, the official Builder emitter, applicable Final Gate runtime propagation and real non-synthetic viewport handoff remain unavailable or `insufficient_evidence`.

Nothing in this document proves responsive correctness, frontend correctness, accessibility completion, export validity, release readiness or production readiness.
