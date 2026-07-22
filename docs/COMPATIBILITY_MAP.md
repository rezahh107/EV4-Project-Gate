# EV4 Compatibility Map

Compatibility is established only through exact pinned owner contracts and official validators. Moving default branches, semantic similarity, copied schemas, synthetic fixtures, or local approximations are not compatibility proof.

## Active boundaries

| Boundary | Required producer input | Required consumer validation | Project Gate compatibility proof |
|---|---|---|---|
| Architect → CE | Architect Stage Payload at the pinned Architect contract | CE intake schema, CE-owned mapping and CE official validator | Exact owner bytes, source identity, deterministic projection, source binding, result schema |
| CE → Builder | CE executable package with valid evidence and lineage | Builder contract gate, adapter, context schema and output validator | CE/Builder lock, source/receipt binding, no fabricated lineage, safe publication |
| Builder → Responsive | Builder output accepted by the pinned Responsive input contract | Responsive input and tree/output validators | Builder/Responsive lock reproduction and official validator execution |
| Final Gate | Responsive evidence plus required prior lock chain | Final result schema, receipt semantics and Kernel intake when selected | Evidence sufficiency, lock validation, deterministic result and receipt |
| Producer integration | Producer Gate Export and adoption/target records | Recorded producer validator and Project Gate intake/dispatch | Exact producer commit/path/hash identity and supported routing |

## Compatibility rules

- A contract lock compares exact file bytes at immutable commits.
- Official owner validators run through the runner boundary; Project Gate does not duplicate specialist semantics.
- Invalid, stale, incompatible or insufficient inputs fail closed.
- Synthetic or owner fixtures retain their evidence class and cannot establish real handoff readiness.
- Runtime publication is atomic, collision-safe and no-overwrite, with active handoff receipts.
- `src/ev4_transition/data/capability-status.v1.json` is the only machine-readable capability authority.

CI compatibility checks are selected by `scripts/classify-validation-scope.py`. Shared, unknown, Workflow, dependency, schema-infrastructure or contract-infrastructure changes execute all boundaries; ordinary transition-specific changes execute the affected boundary only, while full internal tests still run once on every PR Head.
