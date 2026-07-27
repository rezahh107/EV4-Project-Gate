# EV4 Compatibility Map

Compatibility is established only through exact pinned owner contracts, observed official execution where required, and official validators. Moving default branches, semantic similarity, copied schemas, synthetic fixtures, file-only receipts, or local approximations are not compatibility proof.

## Active boundaries

| Boundary | Required producer input | Required consumer validation | Project Gate compatibility proof |
|---|---|---|---|
| Architect → CE | Architect Stage Payload at the pinned Architect contract | CE intake schema, CE-owned mapping and CE official validator | Exact owner bytes, source identity, deterministic projection, source binding, result schema |
| CE → Builder | CE executable package with valid evidence and lineage | Builder contract gate, adapter, context schema and output validator | CE/Builder lock, source/receipt binding, no fabricated lineage, safe publication |
| Builder → Responsive | Builder evidence plus an observed official viewport producer execution at the pinned Builder commit | Responsive schema-bound input and official input/tree validators | Builder/Responsive lock reproduction; production invocation of pinned runtime execution; exact observed runtime result/tool propagation; immutable verified snapshot and receipt consumption; official Responsive validator execution |
| Final Gate | Responsive evidence plus required prior lock chain and verified runtime evidence when applicable | Final result schema, receipt semantics and Kernel intake when selected | Evidence sufficiency, lock validation, observed runtime propagation when required, snapshot/receipt identity, deterministic result and receipt |
| Producer integration | Producer Gate Export and adoption/target records | Recorded producer validator and Project Gate intake/dispatch | Exact producer commit/path/hash identity and supported routing |
| EV4-PCVP carrier intake | Optional `continuation_assurance`; legacy absence remains valid and dependency-free | Official Decision Kernel `validatePcvpBundle()` and `evaluatePcvpCarrier()`, then exact source Profile and resolved Stage checks | Exact repository/commit/file identities; tracked-byte disposable execution tree; exact `package-lock.json` installation via `npm ci --ignore-scripts --no-audit --no-fund`; caller `node_modules` ignored; owner rejection preservation; one unique exact Profile `effect_class` and `scope` match for `PROFILE_PREAUTHORIZED`; exact `stage_scope` endpoints; immutable lossless projection |

## Three-layer runtime rule

```text
implemented runtime primitives
≠ production B2R runtime integration
≠ available Builder emitter
```

### Implemented primitives

Project Gate has reusable primitives for:

- detached execution worktrees at exact pinned commits;
- exact repository, commit, tool, working-directory, output-ref and output-hash binding;
- one-read artifact handling;
- `VerifiedArtifactSnapshot` creation;
- metadata-only runtime receipt derivation;
- cleanup-failure revocation;
- exact-byte staging, verification and grouped rollback.

### Missing production integration

The production `transition_builder_to_responsive` path does not currently call `execute_pinned_viewport_capture` and does not supply an observed `runtime_run` and exact expected runtime tool to viewport evidence resolution. Applicable Final Gate viewport resolution also does not yet consume the observed verified runtime result, snapshot and receipt.

### Missing owner emitter

The pinned Builder commit lacks the required official viewport capture/export emitter and associated pinned contract. This is a separate dependency from Project Gate integration.

## Compatibility rules

- A contract lock compares exact file bytes at immutable commits.
- Official owner validators run through the runner boundary; Project Gate does not duplicate specialist semantics.
- Viewport runtime compatibility requires an observed official execution inside a detached worktree at the exact pinned owner commit.
- The production B2R path must itself invoke that execution and pass the exact observed result plus expected tool through evidence resolution.
- The official operational path reads the emitted artifact once; runtime hashes, parsing, snapshot identity, receipt metadata and publication payload derive from that byte sequence.
- Parsed JSON equality is not exact artifact compatibility. Publication must preserve exact bytes, SHA-256 and byte length.
- A temporary worktree path is ephemeral and is cleared after cleanup; it is never durable evidence.
- Cleanup failure revokes positive proof, snapshot and receipt.
- File-only viewport evidence or an adjacent receipt cannot substitute for observed execution.
- The verified snapshot and metadata-only receipt must be consumed by the production B2R publication path and carried into applicable Final Gate verification.
- Invalid, stale, incompatible or insufficient inputs fail closed.
- Synthetic or owner fixtures retain their evidence class and cannot establish real handoff readiness.
- EV4-PCVP carrier absence preserves the legacy Producer Gate Export path without Git, Node, npm or a Decision Kernel checkout.
- A present EV4-PCVP carrier can be `validated` only after exact owner identity, clean lock-derived owner execution and source Profile/Stage integration all pass.
- Project Gate never resolves Ajv or YAML from the caller-supplied Decision Kernel checkout; dependencies are installed only in an automatically cleaned tracked-byte tree.
- `PROFILE_PREAUTHORIZED` requires exactly one Profile entry with the same `effect_class` and scope text exactly equal to both Effect and Authorization `permitted_scope`.
- Broader, narrower, contained, semantically similar and duplicate Profile scope candidates are rejected; free-form Profile prose is never inferred.
- Missing owner checkout, Git, Node, npm, locked installation or executable authority yields `insufficient_evidence`; owner or Profile rejection yields `invalid`.
- The supplied Decision Kernel checkout is verified read-only before execution and reverified unchanged after success or failure.
- This boundary reader does not emit the carrier into specialist artifacts, set `handoff_allowed`, claim official PASS or activate PCVP.
- Runtime publication is atomic, collision-safe and no-overwrite, with active handoff receipts.
- Adding the Builder emitter alone does not establish compatibility; Project Gate production integration and applicable Final Gate integration must also be completed and verified.
- `src/ev4_transition/data/capability-status.v1.json` is the only machine-readable capability authority.

Current status:

```yaml
runtime_primitives: implemented
production_b2r_runtime_integration: not_implemented
official_builder_viewport_emitter: missing_in_pinned_builder_owner
applicable_final_gate_runtime_integration: not_implemented
real_non_synthetic_handoff: insufficient_evidence
root_operational_handoff_complete: false
```

CI compatibility checks are selected by `scripts/classify-validation-scope.py`. PCVP authority, lock and test changes select `kernel_intake`; shared, unknown, Workflow, dependency, schema-infrastructure or contract-infrastructure changes execute all boundaries. Full internal tests still run once on every PR Head.

No compatibility statement in this document proves responsive correctness, frontend correctness, accessibility completion, export validity, release readiness or production readiness.
