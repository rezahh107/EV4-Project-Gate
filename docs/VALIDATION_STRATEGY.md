# EV4 Validation Strategy

This document defines validation strategy for EV4 Project Gate. Layered capability status is authoritative in `src/ev4_transition/data/capability-status.v1.json` and mirrored in `docs/IMPLEMENTATION_STATUS.yaml`.

## Capability state

```yaml
architect_to_ce:
  orchestration_baseline: implemented
  cli_exposure: implemented
  verification_state: synthetic_fixture_only
ce_to_builder:
  orchestration_baseline: implemented
  cli_exposure: guarded
  owner_fixture_integration: verified
  real_non_synthetic_handoff: insufficient_evidence
builder_to_responsive:
  orchestration_baseline: implemented
  cli_exposure: guarded
  official_responsive_validator_integration: implemented
  verification_state: verified_by_exact_head_ci
  real_non_synthetic_handoff: insufficient_evidence
final_evidence_gate:
  orchestration_baseline: implemented
  cli_exposure: guarded
  official_responsive_validator_integration: implemented
  verification_state: verified_by_exact_head_ci
  real_non_synthetic_evidence: insufficient_evidence
```

## Foundation validation

Current Python checks validate:

- canonical JSON v1 behavior;
- stable SHA-256 over canonical UTF-8 JSON;
- NaN and infinity rejection;
- structured diagnostics and deterministic ordering;
- malformed JSON values without crashes;
- Stage Evidence Bundle envelope structure;
- explicit `insufficient_evidence`;
- provenance preservation;
- validation-result and transition-result schema enforcement;
- runner-boundary enforcement;
- behavioral coverage declarations;
- layered capability-truth reporting.

Current commands:

```bash
uv lock --check
uv sync --locked --extra dev --extra ui
uv run pytest
uv run ev4-transition validate fixtures/valid/architect-stage-bundle.v1.json
uv run ev4-transition validate fixtures/invalid/array-input.v1.json
uv run ev4-transition validate fixtures/insufficient-evidence/architect-stage-bundle.v1.json --format persian
uv run python scripts/check-github-action-pinning.py
npm run status
npm run validate
```

The Node skeleton remains temporarily required until a dedicated parity-proof change retires it.

## Architect → CE validation

Active transition:

```text
ev4-architect-to-ce-transition@1.0.0
```

It validates the source bundle, source identity, pinned external file bytes, Architect payload schema and official validator, deterministic CE-owned mapping, CE intake schema and official validator, source binding, target bundle, and Project Gate result schema.

Pinned repositories:

```text
rezahh107/EV4-Architect-Repo@b0651668b97f682bb17f66840c8e8c503fd3935d
rezahh107/EV4-Constructability-Engineer-Repo@546680a2e2a309c0d7e0ddbfc017e9e194ece7cb
```

Verification remains `synthetic_fixture_only`; no real non-synthetic Architect→CE handoff is claimed.

## CE → Builder validation

Implemented orchestration baseline:

```text
ev4-ce-to-builder-transition@1.0.0
```

The baseline validates or executes, in order:

- CE Stage Evidence Bundle or CE package identity;
- exact CE and Builder owner repository, commit, path, identity marker, and file-byte SHA-256 pins;
- official CE package validator;
- official Builder CE→Builder Contract Gate;
- official Builder adapter;
- Builder-owned context schema;
- official Builder output validator;
- Project Gate CE→Builder result schema.

Project Gate calls owner tools through `src/ev4_transition/runners/`; it does not duplicate CE or Builder domain logic.

Evidence state:

```yaml
owner_fixture_integration:
  status: verified
  pull_request: 20
  head_sha: 42bfa484481c585f589d86c40424660c70b038a0
  workflow_run_id: 28744810186
real_non_synthetic_handoff:
  status: insufficient_evidence
public_cli_exposure:
  status: guarded
```

The owner-fixture smoke is integration evidence only. It is not real non-synthetic handoff evidence and does not prove a real non-synthetic handoff; the public `ce-to-builder` CLI entry remains guarded and fail-closed.

## Builder → Responsive baseline

Builder→Responsive has an implemented guarded orchestration baseline with official Responsive validator integration. It remains fail-closed for real handoff claims until Builder-owned output/evidence artifacts and Responsive-owned input requirements are explicit, pinned, and validated; real non-synthetic handoff evidence is `insufficient_evidence`.

## Local schemas

Project Gate owns envelope/result/diagnostic/lock/coverage schemas only. It must not copy specialist-domain schemas as competing canonical contracts.

## Producer and consumer validation

A cross-repository compatibility claim requires producer-side evidence and consumer-side acceptance/rejection evidence. Synthetic or owner fixtures must retain their labels and cannot be promoted into real handoff evidence.

## CI requirements

CI must prove the package installs, applicable unit and CLI tests pass, positive and negative fixtures behave as expected, official owner tools execute through the runner boundary, external locks match exact pinned bytes, behavioral coverage declarations validate, active documentation matches capability truth, and every external GitHub Action in every workflow is pinned according to repository policy.

The exact automatic post-merge `main` head `dca39ed177d5660d96df04a05fff0a0314c6c339` had no visible workflow run during the audit; its CI state remains `insufficient_evidence` until direct evidence exists.

## Dependency boundary

Existing EV4 repositories should not import from this repository until an explicit ADR, migration plan, validation evidence, compatibility policy, and rollback guidance are approved.

### Prompt 0 common-contract foundation note

Stage Bundle v1 remains the canonical single-stage evidence envelope. Producer Gate Export v1 is a Project Gate-owned run-level complement that composes Stage Bundle v1 through `final_stage_bundle`; it is not a replacement Stage Bundle and does not define Producer-specific payload schemas or exact Producer stage sequences. The common-contract lock is Project Gate-owned and requires exact file-byte equality to a pinned immutable Project Gate commit; semantic JSON equality is not sufficient. Producer adoption, Project Gate runtime integration, and downstream Producer CI enforcement remain pending/not implemented, and real non-synthetic handoff evidence remains `insufficient_evidence`. The canonical Producer pin is pending merge for PR #39; future Producer callers must pin the reusable workflow by immutable Project Gate commit SHA, not `@main`.
