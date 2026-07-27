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

## Dormant EV4-PCVP boundary compatibility

Producer Gate Export intake is additive and dual-read for the optional
`continuation_assurance` carrier from `EV4-PCVP@1.0.0`. Legacy exports without
the carrier remain accepted. Present carriers are checked against exact,
non-authoritative schema bytes pinned from `EV4-Decision-Kernel`, followed by
bounded mechanical reference, Authorization-coverage, scope, status and derived
projection checks. A validated carrier is surfaced losslessly in the intake
result; malformed or unsupported carriers fail closed.

This does not enable Producer emission, specialist downstream propagation,
adoption, strictness, an official PASS, or activation. Those remain separate,
dependency-ordered work.

## Builder → Responsive runtime truth

Three different implementation states must not be conflated:

```text
implemented runtime primitives
≠ production Builder → Responsive runtime integration
≠ available official Builder viewport emitter
```

Project Gate implements and regression-tests the following reusable primitives:

- detached worktree execution at an exact pinned owner commit;
- exact repository, commit, tool, working-directory, output-reference and output-hash binding;
- one-read emitted-artifact handling;
- immutable `VerifiedArtifactSnapshot` creation after all verification predicates pass;
- metadata-only runtime receipt derivation;
- cleanup-failure revocation;
- exact-byte staging, post-write byte/hash/length verification and grouped rollback.

The intended operational lifecycle is:

```text
execute_pinned_viewport_capture
→ execute the exact official producer tool
→ read the emitted artifact exactly once
→ verify exact runtime bindings
→ create VerifiedArtifactSnapshot
→ derive metadata-only receipt
→ clean the temporary worktree
→ pass the observed verified result into B2R evidence resolution
→ publish snapshot.exact_bytes and receipt through grouped publication
→ carry applicable verified runtime evidence into Final Gate
```

This lifecycle is not yet wired into the production `transition_builder_to_responsive` path. That transition currently resolves viewport evidence without supplying an observed `runtime_run` and exact expected runtime tool, so file-only viewport evidence remains non-authoritative. Applicable Final Gate evidence resolution likewise does not yet consume the observed verified runtime result, snapshot and receipt.

The pinned Builder owner also does not provide the required official viewport capture/export emitter. Adding that emitter alone would not complete the root handoff; Project Gate integration and Final Gate propagation would still be required.

Consequently:

```yaml
runtime_primitives: implemented
production_b2r_runtime_integration: not_implemented
official_builder_viewport_emitter: missing_in_pinned_builder_owner
real_non_synthetic_handoff: insufficient_evidence
root_operational_handoff_complete: false
```

Remaining work, in order:

1. implement the official Builder viewport capture/export emitter;
2. pin its exact Builder commit, tool path and contract;
3. wire Project Gate to call `execute_pinned_viewport_capture` in the production B2R flow;
4. pass the exact observed runtime result through evidence resolution;
5. consume and publish the verified snapshot and receipt;
6. verify applicable Final Gate integration;
7. run exact-Head CI and obtain a fresh independent PR Inspector review.

None of these implementation states proves responsive correctness, frontend correctness, accessibility completion, export validity, release readiness or production readiness.

See `docs/EVIDENCE_TRUTH_SPINE.md` for the implemented primitive contracts and fail-closed runtime rules.

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

The UI is Persian-first and local. It does not prove production readiness, browser correctness, responsive completion, accessibility completion, export validity, or real end-to-end compatibility unless the required owner evidence, observed official runtime execution, integration paths and validators execute successfully.

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
