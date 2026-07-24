# Project Gate Evidence Truth Spine

## Scope

This document defines the lean runtime authority path for consequential Project Gate transitions.

```text
Observed Official Producer Execution
→ Typed Runtime Result
→ Checkout / Commit / Tool Verification
→ Exact Artifact Byte Read
→ SHA-256 Recalculation
→ Schema and Binding Validation
→ Runtime-derived Classification
→ Derived Receipt
```

A caller-authored artifact and adjacent receipt are not an execution observation and cannot create operational authority.

The implementation remains local to Project Gate. It does not create an authorization service, cryptographic attestation, key infrastructure, external verifier, or hostile-process security layer.

## Evidence policy registry

Operational evidence uses a small explicit registry keyed by evidence type.

| Evidence type | Required positive proof |
|---|---|
| Architect, Builder, Responsive, and Kernel-owned artifacts with official validators | Accepted official owner validator |
| Viewport runtime artifacts | Verified typed result from an observed official runtime execution |

An unavailable, skipped, unknown, or non-accepted owner validator never authorizes operational evidence.

Keyword and fixture-marker scanning remains rejection-only. It may derive `synthetic`; it cannot create `real_verified`.

## Canonical classification

Caller-authored fields such as `synthetic`, `real_evidence`, `evidence_status`, `verification_status`, and `classification` are metadata only.

```text
real_verified =
    source_resolved
    and hash_verified
    and schema_valid
    and claim_binding_valid
    and subject_binding_valid
    and positive_proof_verified
    and not synthetic_conflict
```

Classifications:

- `real_verified`: every required predicate is true and the positive-proof policy is satisfied.
- `synthetic`: an authoritative source contains a derived synthetic conflict.
- `insufficient_evidence`: execution observation, bytes, digest, schema, binding, or owner validation is missing.

A renamed fixture with valid JSON and a matching digest remains `insufficient_evidence` unless its evidence-type policy is positively satisfied.

## Viewport runtime authority

`ViewportEvidenceRun` is a typed description of an observed official producer execution. It reuses the repository's `ExecutionRecord` model and includes:

- run ID;
- producer repository and exact commit;
- official producer tool path;
- subject and viewport;
- resulting artifact path and recorded SHA-256;
- capture and validation status;
- typed execution record.

`verify_viewport_evidence_run()` independently verifies:

1. producer checkout origin and exact HEAD;
2. producer repository and commit carried by the run;
3. official tool path and execution-record identity;
4. typed adapter execution record and successful exit;
5. artifact location inside the producer checkout;
6. current artifact bytes and SHA-256;
7. recorded run hash and execution-record output hash;
8. JSON structure, run ID, subject and viewport;
9. completed capture and accepted validation;
10. absence of synthetic conflicts.

A mutation after execution changes the current bytes and fails the recorded-hash comparison.

## Receipt boundary

The adjacent file:

```text
<artifact_ref>.receipt.json
```

may be inspected for migration diagnostics, but it is never positive-proof input. A matching caller-authored artifact and receipt return:

```yaml
classification: insufficient_evidence
positive_proof_verified: false
reason: official_runtime_execution_not_observed
```

After successful typed runtime verification, Project Gate may derive a deterministic audit record:

```yaml
schema: ev4_runtime_evidence_receipt_v2
evidence_type: viewport_artifact
run_id: ...
producer_repository: ...
producer_commit: ...
producer_tool: ...
execution_status: accepted
execution_record_digest: ...
subject_ref: ...
viewport: ...
artifact_ref: ...
artifact_sha256: ...
capture_status: completed
validation_status: accepted
```

This receipt summarizes already verified execution. It does not grant authority and is never read back as a substitute for runtime execution.

## Current producer dependency

The pinned Builder owner revision is:

```yaml
repository: rezahh107/EV4-Builder-Assistant-Repo
commit: 69a2c61edf6d06b4418ad770fcefbfdffcf275d6
```

That revision owns Elementor execution and evidence retention, but explicitly records Builder→Responsive export as `documented_not_implemented` and real execution as pending user execution. It has no compatible official viewport capture/export emitter that Project Gate can invoke.

The pinned Responsive revision is:

```yaml
repository: rezahh107/EV4-Responsive-Architect
commit: df74c7ba2ffbed1a4136b5ea6be6ce30db4e161a
```

Its Builder→Responsive intake is schema-bound and non-executing. It does not provide the missing upstream capture emitter.

Therefore Project Gate follows the fail-closed Case B behavior:

```yaml
project_gate_false_authority_closed: true
viewport_real_verified_capability: insufficient_evidence
external_dependency_required: true
required_owner: rezahh107/EV4-Builder-Assistant-Repo
required_contract_or_emitter: official viewport capture/export adapter returning a typed execution result
```

Project Gate does not fabricate this upstream runtime or modify the external repository in this repair.

## A2C publication transaction

Operational A2C publication first evaluates:

```text
publication_allowed =
    transition_authorized
    and handoff_allowed
    and evidence_ready
    and validation_passed
```

When false, it returns before path resolution, staging, receipt construction, or publication.

When true, CE input and the A2C receipt are staged and committed through one `publish_staged_group()` transaction:

```text
stage both exact byte sequences
→ verify source snapshot unchanged
→ assert both destinations unused
→ link both destinations
→ fsync destination directories
→ verify both exact byte sequences
→ remove both temporary files
→ return both published records
```

No artifact is reported as `published_verified` until every step succeeds for both files.

On failure, the helper:

- preserves the original publication diagnostic;
- rolls back every linked final path;
- removes every staged temporary file;
- fsyncs affected directories after rollback;
- reports rollback and cleanup errors separately;
- reports exact persisted paths if rollback itself fails.

The normal failure contract is:

```yaml
publication_allowed: false
handoff_allowed: false
downstream_artifact:
  status: not_published
receipt:
  status: not_generated
```

No-overwrite, path safety, symlink checks, source/output collision checks, snapshot verification, deterministic serialization and exact-byte verification remain active.

## Boundary behavior

### Architect → CE

- Official Architect and CE validators remain authoritative.
- `handoff.allowed=false` stops before every publication action.
- Authorized CE input and receipt publish as one group.
- A group failure rolls back all Project Gate-created final artifacts.

### CE → Builder

Existing C2B early-return and publication behavior remain unchanged.

### Builder → Responsive

Source-bound Builder artifacts continue to require accepted pinned owner validators. File-only desktop, tablet and mobile evidence remain `insufficient_evidence` until the missing Builder runtime emitter supplies an observed typed result.

### Final Gate

Responsive output continues to require its official owner validator. File-only viewport artifacts cannot satisfy `required_viewports_verified` or `real_evidence_present`. Raw Kernel intake remains mandatory and internally executed; supplied projections remain non-authoritative and drift-checked.

## Capability truth

This repair closes false runtime authority and partial A2C publication inside Project Gate. It does not implement the missing external viewport emitter and therefore does not claim a real non-synthetic ecosystem handoff, browser validation, release readiness, or production readiness.
