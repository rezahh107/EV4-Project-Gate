# EV4 Compatibility Map

Compatibility is established only through exact pinned owner contracts and official validators. Moving default branches, semantic similarity, copied schemas, synthetic fixtures, or local approximations are not compatibility proof.

## Active boundaries

| Boundary | Required producer input | Required consumer validation | Project Gate compatibility proof |
|---|---|---|---|
| Architect → CE | Architect Stage Payload at the pinned Architect contract | CE intake schema, CE-owned mapping and CE official validator | Exact owner bytes, source identity, deterministic projection, source binding, result schema |
| CE → Builder | CE executable package with valid evidence and lineage | Builder contract gate, adapter, context schema and output validator | CE/Builder lock, source/receipt binding, no fabricated lineage, safe publication |
| Builder → Responsive | Builder evidence plus an observed official viewport producer execution at the pinned Builder commit | Responsive schema-bound input and official input/tree validators | Builder/Responsive lock reproduction; detached exact-commit execution; exact repo/tool/cwd/ref/hash/subject/viewport binding; immutable exact-byte snapshot; successful cleanup; official Responsive validator execution |
| Final Gate | Responsive evidence plus required prior lock chain and verified runtime evidence when applicable | Final result schema, receipt semantics and Kernel intake when selected | Evidence sufficiency, lock validation, snapshot/receipt identity, deterministic result and receipt |
| Producer integration | Producer Gate Export and adoption/target records | Recorded producer validator and Project Gate intake/dispatch | Exact producer commit/path/hash identity and supported routing |

## Compatibility rules

- A contract lock compares exact file bytes at immutable commits.
- Official owner validators run through the runner boundary; Project Gate does not duplicate specialist semantics.
- Viewport runtime compatibility requires observed official execution inside a detached worktree at the exact pinned owner commit.
- The official operational path reads the emitted artifact once; all runtime hashes, parsing, snapshot identity, receipt metadata and publication payload derive from that byte sequence.
- Parsed JSON equality is not exact artifact compatibility. Publication must preserve exact bytes, SHA-256 and byte length.
- A temporary worktree path is ephemeral and is cleared after cleanup; it is never durable evidence.
- Cleanup failure revokes positive proof, snapshot and receipt.
- Invalid, stale, incompatible or insufficient inputs fail closed.
- Synthetic or owner fixtures retain their evidence class and cannot establish real handoff readiness.
- Runtime publication is atomic, collision-safe and no-overwrite, with active handoff receipts.
- The pinned Builder owner currently lacks the official viewport emitter, so real Builder → Responsive compatibility remains `insufficient_evidence` despite implemented Project Gate verification and snapshot infrastructure.
- `src/ev4_transition/data/capability-status.v1.json` is the only machine-readable capability authority.

CI compatibility checks are selected by `scripts/classify-validation-scope.py`. Shared, unknown, Workflow, dependency, schema-infrastructure or contract-infrastructure changes execute all boundaries; ordinary transition-specific changes execute the affected boundary only, while full internal tests still run once on every PR Head.
