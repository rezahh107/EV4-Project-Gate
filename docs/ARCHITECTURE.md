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

## Authority surfaces

- capability truth: `src/ev4_transition/data/capability-status.v1.json`;
- active role boundary: `docs/ROLE_BOUNDARY_MAP.md`;
- active contracts: `docs/CONTRACT_INVENTORY.md` and `contracts/`;
- compatibility: `docs/COMPATIBILITY_MAP.md`;
- validation: `docs/VALIDATION_STRATEGY.md`;
- reusable producer verifier: `.github/workflows/verify-vendored-common-contract.yml`.

Historical prompt handoffs, merge ledgers, source-evidence archives and duplicate status registries are not architectural authority.
