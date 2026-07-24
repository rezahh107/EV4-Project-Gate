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

## Durable runtime artifact lifecycle

Viewport runtime evidence has a stricter lifetime than ordinary parsed transition data:

```text
materialize detached worktree at exact owner commit
→ execute exact official producer tool
→ read emitted artifact bytes exactly once
→ derive runtime hash and execution-record output hash from those bytes
→ parse and validate the same bytes
→ create immutable VerifiedArtifactSnapshot after all predicates pass
→ derive receipt metadata from the snapshot
→ remove and prune the worktree
→ return snapshot with no temporary path
```

The snapshot contains canonical artifact ref, exact immutable bytes, SHA-256, and byte length. Raw bytes are excluded from repr, diagnostics, receipts, service responses, and UI state. Publication stages `snapshot.exact_bytes` directly and post-write verification requires exact byte, hash, and length equality.

Cleanup remains authority-bearing. A cleanup failure revokes the snapshot and receipt and returns `insufficient_evidence`.

The infrastructure is implemented, but the pinned Builder owner does not yet expose the required official viewport emitter. Project Gate therefore must not claim a real Builder → Responsive or Final Gate handoff.

## Authority surfaces

- capability truth: `src/ev4_transition/data/capability-status.v1.json`;
- runtime evidence rules: `docs/EVIDENCE_TRUTH_SPINE.md`;
- active role boundary: `docs/ROLE_BOUNDARY_MAP.md`;
- active contracts: `docs/CONTRACT_INVENTORY.md` and `contracts/`;
- compatibility: `docs/COMPATIBILITY_MAP.md`;
- validation: `docs/VALIDATION_STRATEGY.md`;
- reusable producer verifier: `.github/workflows/verify-vendored-common-contract.yml`.

Historical prompt handoffs, merge ledgers, source-evidence archives and duplicate status registries are not architectural authority.
