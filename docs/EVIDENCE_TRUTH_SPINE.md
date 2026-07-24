# Project Gate Evidence Truth Spine

## Scope

Project Gate derives consequential runtime authority only from an execution it performs inside a clean detached Git worktree at an exact pinned owner commit.

```text
ordinary owner checkout (may be dirty)
→ verify owner repository and pinned commit object
→ materialize detached clean worktree at the pinned commit
→ execute the official tool inside that worktree
→ internally create ExecutionRecord and ViewportEvidenceRun
→ verify repository, commit, tool, working directory, output reference and bytes
→ classify evidence
→ derive an audit receipt from verified values
→ remove and prune the temporary worktree
```

This mechanism provides reproducible execution bytes. It is not cryptographic attestation, an authorization service, a hostile-process control, or an external trust system.

## Evidence policy

| Evidence type | Required positive proof |
|---|---|
| Architect, Builder, Responsive and Kernel-owned artifacts with official validators | Accepted official owner validator |
| Viewport runtime artifact | Exact-bound result from Project Gate's pinned-worktree execution path |

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

official_operational_path:
  function: execute_pinned_viewport_capture
  accepts: source checkout, pinned repository and commit, tool ref, working-directory ref, subject, viewport, timeout
  internally_creates:
    - detached pinned worktree
    - process result
    - ExecutionRecord
    - ViewportEvidenceRun
    - exact-bound verification
    - derived receipt
```

The operational caller does not supply the execution record, exit status, output reference, output hash, receipt digest, capture success or validation success.

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
SHA256(verified artifact bytes)
== run.artifact_sha256
== execution_record.output_hash
== verification.actual_sha256
```

Path equality and hash equality are both mandatory. Identical bytes at two paths do not satisfy the binding.

### Process and content

The record must be an adapter execution with exit code `0`, no failure code, an exact tool entrypoint, a completed capture and an explicitly accepted producer validation result. Run ID, subject and viewport must match the request, runtime result and artifact content. Synthetic conflicts remain fail-closed.

## Verified result and receipt

`ViewportRunVerification` exposes verified values only after their checks pass:

- verified repository and commit;
- verified tool and working-directory references;
- verified artifact reference and path;
- actual SHA-256;
- verified execution-record digest;
- verified run ID, subject and viewport.

`build_runtime_evidence_receipt(verification=...)` accepts only a successful exact-bound verification. Receipt fields come exclusively from verified values. The deterministic receipt uses schema `ev4_runtime_evidence_receipt_v2` and remains an audit/debug publication record, not positive-proof input.

A stored artifact and adjacent receipt, even when every field and digest matches, remain:

```yaml
classification: insufficient_evidence
positive_proof_verified: false
reason: official_runtime_execution_not_observed
```

## Current owner dependency

The pinned Builder revision is:

```yaml
repository: rezahh107/EV4-Builder-Assistant-Repo
commit: 69a2c61edf6d06b4418ad770fcefbfdffcf275d6
```

Its Builder→Responsive boundary is documented but the formal export and compatible viewport capture emitter are not implemented. The pinned Responsive intake is schema-bound and non-executing. Project Gate therefore implements the exact-binding infrastructure but does not fabricate an emitter or claim a real viewport run.

```yaml
runtime_binding_infrastructure_complete: true
official_viewport_emitter_found: false
official_viewport_emitter_executed: false
viewport_real_verified_capability: insufficient_evidence
external_dependency_required: true
required_owner: rezahh107/EV4-Builder-Assistant-Repo
required_contract_or_emitter: official viewport capture/export adapter returning the documented bounded runtime result
root_operational_capability_complete: false
```

## A2C publication transaction

The existing Architect→CE publication repair remains unchanged. A denied handoff returns before path resolution, staging, receipt construction or publication. An authorized CE input and A2C receipt are committed through `publish_staged_group()` and are reported as `published_verified` only after both links, directory fsync, exact-byte verification and staged-file cleanup succeed.

Any failure rolls back all linked Project Gate artifacts, removes staged files, preserves the original error and separately reports rollback or cleanup failures and truthful persisted state.

## Capability truth

`src/ev4_transition/data/capability-status.v1.json` remains the sole machine-readable authority. The exact-binding worktree and output binding are implemented. The official Builder emitter and real non-synthetic viewport handoff remain unavailable and `insufficient_evidence`.
