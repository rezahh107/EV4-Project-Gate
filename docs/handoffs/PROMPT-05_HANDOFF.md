# Prompt 5 Handoff — Producer-emitted runtime integration

branch: project-gate-prompt-05-producer-integration-join

## Summary

Prompt 5 implemented the explicit `producer_emitted_gate_artifact` Project Gate path while preserving the legacy `pinned_owner_file_computation` path. The implementation is bounded to Project Gate-owned registries, exact-byte verification helpers, shared intake, CLI/UI routing, CI wiring, fixtures, diagnostics, and tests.

## Files changed

- `.github/workflows/prompt-05-producer-integration.yml`
- `contracts/producer-adoption/ev4-producer-adoption-set.v1.json`
- `contracts/transition-targets/ev4-transition-targets.v1.json`
- `schemas/producer-adoption/producer-adoption-set.v1.schema.json`
- `schemas/transition-targets/transition-targets.v1.schema.json`
- `src/ev4_transition/producer_integration/*`
- `src/ev4_transition/cli.py`
- `src/ev4_transition/ui/app.py`
- `src/ev4_transition/ui/adapters.py`
- `src/ev4_transition/data/capability-status.v1.json`
- `fixtures/producer-emitted/**`
- `tests/producer_integration/test_prompt05_producer_integration.py`
- `docs/adr/ADR-0008-producer-emitted-runtime-integration.md`
- `docs/handoffs/PROMPT-05_HANDOFF.md`

## Tests run

- `uv sync --locked --extra dev --extra ui`
- `uv run pytest -q tests/producer_integration/test_prompt05_producer_integration.py`
- `uv run pytest -q`
- `uv run python scripts/check-capability-truth.py`
- `uv run python scripts/check-workflow-permissions.py`
- `uv run python scripts/check-github-action-pinning.py`
- `uv run python scripts/validate-behavioral-rule-coverage.py`
- `uv run ev4-transition validate fixtures/valid/architect-stage-bundle.v1.json`
- `uv run ev4-transition validate fixtures/invalid/array-input.v1.json` returned exit 1 as expected for invalid input.
- `uv run ev4-transition validate fixtures/insufficient-evidence/architect-stage-bundle.v1.json --format persian` returned exit 2 as expected for insufficient evidence.
- `npm run status`
- `npm run validate`

## Tests not run at handoff creation time

Remote GitHub Actions re-run on the repaired PR head was not observed in this local environment.

## Coverage rules advanced

- Join Evidence Packet preflight: fixture-tested by the repaired packet and enforced in the producer-emitted transition runtime before accepted results are returned.
- Producer adoption registry: validator-backed and fixture-tested by Prompt 5 tests, including malformed-registry fail-closed cases.
- Exact Git blob unavailable behavior: fixture-tested with a local empty git repository.
- Producer-emitted intake: fixture-tested across all four stages.
- Explicit acquisition mode, no fallback, and no evidence mixing: fixture-tested.

## Rules still gap

- Official Producer validators are wired for immutable-SHA CI presence checks, but full owner-tool execution remains dependent on Producer repository environments.
- Real non-synthetic cross-repository E2E remains `insufficient_evidence`.

## New diagnostics

`PG-P05-JOIN-EVIDENCE-NOT-READY`, `PG-P05-PRODUCER-REGISTRY-INVALID`, `PG-P05-MOVING-REF-FORBIDDEN`, `PG-P05-PR-HEAD-AS-RUNTIME-PIN`, `PG-P05-EXACT-BLOB-UNAVAILABLE`, `PG-P05-EXACT-BLOB-HASH-MISMATCH`, `PG-P05-PRODUCER-FILE-MISSING`, `PG-P05-VENDORED-CONTRACT-MISMATCH`, `PG-P05-ACQUISITION-MODE-MISSING`, `PG-P05-ACQUISITION-MODE-MISMATCH`, `PG-P05-SILENT-FALLBACK-FORBIDDEN`, `PG-P05-EVIDENCE-MIXING-FORBIDDEN`, `PG-P05-PRODUCER-ARTIFACT-MUTATED`, `PG-P05-HANDOFF-TARGET-INVALID`, `PG-P05-PRODUCER-VALIDATOR-FAILED`, `PG-P05-DOWNSTREAM-FABRICATION-FORBIDDEN`, `PG-P05-REAL-E2E-EVIDENCE-MISSING`.

## CLI/CI/UI changes

- CLI: `ev4-transition transition ... --acquisition-mode producer_emitted_gate_artifact` selects the explicit Producer-emitted path.
- UI: local operator panel exposes acquisition-mode selection and includes selected mode in machine-readable results.
- CI: `.github/workflows/prompt-05-producer-integration.yml` checks out Producer repositories only by immutable merged SHAs with `persist-credentials: false` and verifies validator paths recorded in the adoption registry.

## Important design decisions

- Join Evidence Packet preflight is enforced before producer-emitted transition acceptance.
- No auto-detection and no automatic fallback between acquisition modes.
- Runtime pins use merged commits; PR heads are retained only as CI provenance.
- Project Gate validates orchestration boundaries and does not copy Producer semantics.
- Downstream artifacts are not fabricated.

## Web sources used

None.

## Next allowed prompt

Human review and merge decision for Prompt 5 PR; a later prompt may deepen official owner-tool execution evidence.

## Blockers

Review blockers repaired locally: Join Evidence Packet runtime enforcement, schema allowlist governance, registry malformed-input fail-closed behavior, and adoption-registry-based producer validator path checks.

## Remaining insufficient_evidence

- Real non-synthetic cross-repository E2E chain.
- Production readiness.
- Exact PR-head CI observation for the repaired PR head until remote CI is observed.

## No-false-execution notes

Synthetic fixtures prove validator and routing behavior only. They do not prove real Elementor correctness, responsive correctness, frontend correctness, accessibility completion, export validation, or production readiness.
