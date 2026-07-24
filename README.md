# EV4 Project Gate

`EV4-Project-Gate` is a local, deterministic validation and handoff orchestrator between the EV4 specialist repositories. It coordinates strict cross-repository boundaries without becoming a competing schema or domain authority.

## Active capability authority

The only machine-readable capability authority is:

```text
src/ev4_transition/data/capability-status.v1.json
```

Use `uv run ev4-transition inspect` for the current layered capability view. Real non-synthetic handoff evidence remains explicit; guarded transitions fail closed when owner checkouts, official tools, or evidence are missing.

## Operator flow

```text
select input
→ one authoritative action
→ Preflight the same request
→ execute the same request
→ publish the result
```

Preview is optional and non-authorizing. Execution reruns backend Preflight, binds the request fingerprint to an immutable source snapshot, rejects drift/mismatch/warnings/blocked states, prevents duplicate dispatch, and publishes through atomic no-overwrite paths with runtime handoff receipts.

## Cross-repository flow

```text
Architect → Project Gate → CE → Project Gate → Builder
→ Project Gate → Responsive → Project Gate → Final Gate / Decision Kernel
```

Each specialist repository owns its schemas, validators, adapters, fixtures, and domain behavior. Project Gate owns deterministic orchestration, result envelopes, diagnostics, contract locks, publication safety, receipts, CLI/UI presentation, and selective CI boundary execution.

## Durable viewport runtime evidence

The Builder → Responsive runtime boundary uses a detached worktree at an exact pinned Builder commit. The official operational path must:

```text
execute the exact official producer tool
→ read the emitted artifact exactly once
→ bind repository, commit, tool, working directory, output ref, hash, subject and viewport
→ create an immutable exact-byte VerifiedArtifactSnapshot only after every predicate passes
→ derive receipt identity from snapshot metadata
→ remove and prune the temporary worktree
→ return durable bytes without returning a stale temporary path
```

Publication consumes `snapshot.exact_bytes` directly and verifies destination byte equality, SHA-256, and byte length. Parsed JSON is never reserialized to reconstruct the verified artifact.

The snapshot and exact-byte publication infrastructure are implemented. The pinned Builder owner still does not provide the required official viewport capture/export emitter, so real non-synthetic Builder → Responsive and Final Gate readiness remain `insufficient_evidence`.

See `docs/EVIDENCE_TRUTH_SPINE.md` for the exact runtime authority and cleanup rules.

## Setup

Python `>=3.11` is supported. `uv.lock` is committed for reproducible setup.

```bash
uv python install 3.11
uv sync --locked --extra dev --extra ui
uv run ev4-transition inspect
```

Fallback when `uv` is unavailable:

```bash
python -m pip install -e '.[dev,ui]'
```

## CLI

```bash
uv run ev4-transition validate fixtures/valid/architect-stage-bundle.v1.json
uv run ev4-transition validate fixtures/invalid/array-input.v1.json
uv run ev4-transition validate fixtures/insufficient-evidence/architect-stage-bundle.v1.json --format persian

uv run ev4-transition transition architect-to-ce input.json \
  --architect-repo ../EV4-Architect-Repo \
  --ce-repo ../EV4-Constructability-Engineer-Repo

uv run ev4-transition transition ce-to-builder input.json \
  --ce-repo ../EV4-Constructability-Engineer-Repo \
  --builder-repo ../EV4-Builder-Assistant-Repo

uv run ev4-transition transition builder-to-responsive input.json \
  --builder-repo ../EV4-Builder-Assistant-Repo \
  --responsive-repo ../EV4-Responsive-Architect

uv run ev4-transition transition final-evidence-gate input.json \
  --project-gate-repo . \
  --responsive-repo ../EV4-Responsive-Architect \
  --kernel-repo ../EV4-Decision-Kernel
```

Exit codes:

```text
0 = valid
1 = invalid
2 = insufficient_evidence
```

## Local UI

```bash
uv run python -m ev4_transition.ui.app
```

Optional entry point:

```bash
uv run ev4-project-gate-ui
```

The UI is Persian-first and local. It does not prove production readiness, browser correctness, responsive completion, accessibility completion, export validity, or real end-to-end compatibility unless the required owner evidence and validators execute successfully.

## Validation

Local core validation:

```bash
uv lock --check
uv sync --locked --extra dev --extra ui
uv run python -m compileall -q src tests
uv run pytest -vv
uv run python scripts/check-capability-truth.py
uv build --wheel
```

GitHub Actions uses one required workflow, `.github/workflows/validate.yml` (`Skeleton Health`):

- `scope`: exact Head and fail-safe changed-path classification;
- `core-quality`: full internal pytest once, CLI smokes, capability truth, wheel build, clean install, packaged UI construction once;
- `boundary-*`: only affected owner-boundary checks on ordinary PRs, all boundaries on `main`, Workflow changes, classifier changes, shared/unknown changes, or full dispatch;
- `quality-gate`: one final required result.

The reusable external contract verifier remains:

```text
.github/workflows/verify-vendored-common-contract.yml
```

It is consumed at immutable Project Gate SHAs by EV4 producer repositories and remains a separate public reusable Workflow contract.

See `docs/VALIDATION_STRATEGY.md` for the exact CI model and `docs/ROLE_BOUNDARY_MAP.md`, `docs/CONTRACT_INVENTORY.md`, and `docs/COMPATIBILITY_MAP.md` for active boundaries.
