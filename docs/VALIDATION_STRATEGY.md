# Validation Strategy

## Objective

Project Gate validation must be complete, deterministic, fail-closed at real cross-repository boundaries, and non-duplicative inside a personal repository.

## Three layers

### 1. Personal operator runtime

```text
select input
→ one authoritative action
→ Preflight same request
→ execute same request
→ publish result
```

No CI receipt, historical ledger, source archive, persistent authorization token, or mandatory preview is part of normal operator use.

### 2. Cross-repository boundary validation

Every affected boundary retains:

- immutable source snapshot;
- canonical parsing and SHA-256 identity;
- input and output schema validation;
- semantic validation;
- relevant repository identity;
- pinned owner-contract byte verification;
- official owner validators/tooling;
- deterministic transition behavior;
- atomic no-overwrite publication;
- runtime handoff receipt and required post-write reread.

For a present EV4-PCVP carrier, the boundary additionally requires an exact read-only Decision Kernel checkout, locked execution-critical owner bytes, locked Node dependencies, official bundle/carrier execution, and explicit source Profile/Stage integration. Carrier absence remains dependency-free.

When an operator supplies `kernel_repo_path` for producer-emitted execution, that path is a dispatch-affecting optional request field. Authoritative Preflight forwards the same path into owner-backed inspection, request identity includes it in the fingerprint, and runtime reuses it for execution. Replacing the path after Preflight invalidates the fingerprint and requires a fresh Preflight. Omitting the path does not trigger Git, Node, npm, or Decision Kernel access when the carrier is absent.

### 3. Repository-change validation

`.github/workflows/validate.yml` is the single Project Gate quality Workflow.

```text
scope
→ python-core
→ affected boundaries
→ quality-gate
```

The Workflow name remains `Skeleton Health` for compatibility. Job IDs `skeleton` and `python-core` remain stable.

## Exact Head

Every job checks out and asserts the exact PR Head or `main` push SHA. `workflow_dispatch` may additionally require `expected_head_sha`.

GitHub logs and the Workflow summary are the evidence. CI does not upload source archives, tested-head text artifacts, JUnit evidence bundles, or repair-evidence packages.

## Core quality: once per Head

`python-core` always runs exactly once:

```bash
uv lock --check
uv sync --locked --extra dev --extra ui
uv run python -m compileall -q src tests
uv run pytest -vv
uv run ev4-transition validate fixtures/valid/architect-stage-bundle.v1.json
uv run ev4-transition validate fixtures/invalid/array-input.v1.json
uv run ev4-transition validate fixtures/insufficient-evidence/architect-stage-bundle.v1.json --format persian
uv run python scripts/check-capability-truth.py
uv build --wheel
```

The wheel is clean-installed outside the checkout. CI imports the CLI and native runners and constructs `build_demo()` without launching a server.

## Scope classifier

`scripts/classify-validation-scope.py` selects external boundaries only. It never reduces the full internal suite.

Fail-safe `run_all=true` applies to:

- `.github/workflows/**`;
- the classifier and its tests;
- `pyproject.toml`, `uv.lock`, and Python-version changes;
- shared service, canonical, CLI, runner, model, package, schema, or contract infrastructure;
- unknown paths;
- `push` to `main`;
- explicit full validation dispatch.

PCVP authority code, `contracts/locks/pcvp-v1.lock.json`, and PCVP contract tests select both `kernel_intake` and the applicable producer-integration coverage. Known non-authoritative docs-only changes run core quality but no external boundary matrix.

## Boundary matrix

The selected matrix can execute:

- `architect_to_ce`: pinned Architect/CE contracts, official validators, lock verification, transition smoke, positive/negative tests;
- `ce_to_builder`: pinned CE/Builder contracts, lock verification, owner-tool smoke, publication and lineage tests;
- `builder_to_responsive`: pinned Builder/Responsive contracts, lock reproduction, official Responsive validators, transition tests;
- `final_gate`: prior lock chain, Responsive evidence, result/receipt semantics, insufficient-evidence behavior;
- `kernel_intake`: a legacy Kernel checkout at `76a82e28543ff8f0babca11b7d7dccac96b92894` for MVK plus a separate PCVP authority checkout at `069a50fa243b01fa578a7c1bcb8864d9e796d34b`; locked dependency installation; official bundle/fixture/carrier execution; Profile mutations; bridge and intake tests;
- `producer_integration`: adoption registry, transition targets, exact producer artifact bytes, recorded validator existence, routing and dispatch tests.

Node setup is limited to `kernel_intake`, where official pinned owner toolchains require it. The unrelated legacy Kernel pin is never reused as PCVP authority.

## Final quality gate

`quality-gate` runs with `if: always()` and fails when:

- scope classification fails;
- core quality fails or is cancelled;
- selected boundary work fails, is cancelled, or is unexpectedly omitted;
- boundary work runs when the classifier explicitly selected none.

The summary records tested Head, core/package result, executed boundaries, not-applicable status, and final result.

## Reusable producer contract verifier

`.github/workflows/verify-vendored-common-contract.yml` remains a public reusable Workflow because external producer repositories call it at immutable Project Gate SHAs. Its contract is independent of the internal Project Gate validation topology.

## Removed non-correctness machinery

The active pipeline does not use:

- merged-PR auto-commits to `main`;
- post-merge Workflow redispatch;
- mutable Markdown merge ledgers;
- CI source/evidence archives;
- dedicated Action-pinning or Workflow-permission policy validators;
- global Node skeleton commands;
- prompt-specific duplicate full-suite Workflows;
- a duplicate implementation-status registry;
- a manually synchronized behavioral-rule coverage ledger.

Git, GitHub PR metadata, Workflow logs, executable tests, active contracts, and `src/ev4_transition/data/capability-status.v1.json` provide the required authority and reproducibility.
