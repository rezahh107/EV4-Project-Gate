# EV4 Project Gate Architecture

## Mental model

```text
Architect → Project Gate → CE → Project Gate → Builder
→ Project Gate → Responsive → Project Gate → Final Gate / Decision Kernel
```

Project Gate is a deterministic checkpoint and handoff orchestrator, not another specialist engine.

## Three practical layers

### Personal operator runtime

```text
select input → one authoritative action → Preflight same request
→ execute same request → publish result
```

Preview is optional and non-authorizing. Execution binds one request fingerprint to one immutable source snapshot, reruns backend Preflight, rejects drift/mismatch/warnings/blocked states and duplicate dispatch, then publishes atomically with no overwrite and a runtime receipt.

### Cross-repository boundary validation

```text
immutable source snapshot
→ canonical parsing
→ schema and semantic validation
→ relevant repository identity
→ pinned owner contract bytes
→ official owner validator/tool
→ deterministic transition
→ output schema validation
→ safe publication and runtime receipt
```

Specialist repositories own specialist contracts and semantics. Project Gate pins and executes those authorities through `src/ev4_transition/runners/`; it does not copy or approximate them.

### Repository-change validation

```text
scope → core-quality → affected-boundaries → quality-gate
```

`.github/workflows/validate.yml` runs the full internal suite, wheel build and clean install once per exact Head. `scripts/classify-validation-scope.py` selects external boundaries and fails safe to all for shared, unknown, Workflow, dependency, schema or contract infrastructure changes. Node exists only in the actual Decision Kernel boundary.

## Viewport runtime architecture

The architecture has three distinct layers:

```text
runtime verification/publication primitives
≠ production B2R orchestration integration
≠ Builder-owned official viewport emitter
```

### Implemented primitives

Project Gate currently implements and regression-tests:

```text
materialize detached worktree at exact owner commit
→ execute an exact official producer tool when one is supplied
→ read emitted artifact bytes exactly once
→ derive runtime hash and ExecutionRecord output hash from those bytes
→ verify repository, commit, tool, cwd, output ref/hash, subject and viewport
→ parse and validate the same bytes
→ create immutable VerifiedArtifactSnapshot after all predicates pass
→ derive metadata-only receipt identity
→ remove and prune the worktree
→ retain no durable temporary path
→ stage snapshot.exact_bytes
→ verify post-write bytes, SHA-256 and length
→ rollback grouped publication on failure
```

The snapshot contains canonical artifact ref, exact immutable bytes, SHA-256, and byte length. Raw bytes are excluded from repr, diagnostics, receipts, service responses, and UI state. Cleanup remains authority-bearing: a cleanup failure revokes positive proof, snapshot and receipt.

### Production integration gap

The production `transition_builder_to_responsive` flow does not currently invoke `execute_pinned_viewport_capture`. Its viewport evidence resolution does not receive an observed `runtime_run` or exact expected runtime tool, so the runtime-execution policy correctly remains fail-closed.

Applicable Final Gate viewport resolution also does not currently receive and consume the observed verified runtime result, snapshot and receipt. Therefore the existence of the primitives does not mean the production B2R or Final Gate runtime path is integrated.

### Owner dependency

The pinned `EV4-Builder-Assistant-Repo` commit also lacks the required official viewport capture/export emitter and formal associated contract. This is a separate dependency from Project Gate integration.

Adding the emitter alone is insufficient. Completion requires:

1. implement the official Builder emitter;
2. pin its exact commit, tool path and contract;
3. wire production B2R to call `execute_pinned_viewport_capture`;
4. pass the exact observed result through evidence resolution;
5. consume and publish the verified snapshot and receipt;
6. verify applicable Final Gate integration;
7. run exact-Head CI and obtain a fresh independent PR Inspector review.

Until both owner and integration work are complete:

```yaml
runtime_primitives: implemented
production_b2r_runtime_integration: not_implemented
official_builder_viewport_emitter: missing_in_pinned_builder_owner
real_non_synthetic_handoff: insufficient_evidence
root_operational_handoff_complete: false
```

No part of this architecture proves responsive correctness, frontend correctness, accessibility completion, export validity, release readiness or production readiness.

## Authority surfaces

- capability truth: `src/ev4_transition/data/capability-status.v1.json`;
- runtime primitive rules: `docs/EVIDENCE_TRUTH_SPINE.md`;
- active role boundary: `docs/ROLE_BOUNDARY_MAP.md`;
- active contracts: `docs/CONTRACT_INVENTORY.md` and `contracts/`;
- compatibility: `docs/COMPATIBILITY_MAP.md`;
- validation: `docs/VALIDATION_STRATEGY.md`;
- reusable producer verifier: `.github/workflows/verify-vendored-common-contract.yml`.

Historical prompt handoffs, merge ledgers, source-evidence archives and duplicate status registries are not architectural authority.
