# AGENTS.md

## Scope

These instructions apply to the entire repository unless a closer nested `AGENTS.md` or `AGENTS.override.md` provides more specific guidance.

## Repository Role

`EV4-Project-Gate` is the planned cross-repository workflow and compatibility control center for:

```text
EV4-Architect-Repo
EV4-Constructability-Engineer-Repo
EV4-Builder-Assistant-Repo
EV4-Responsive-Architect
```

The specialist repositories remain authoritative for their own schemas, validators, adapters, fixtures, and domain behavior.

This repository owns cross-repository verification orchestration, gate configuration, report and evidence formats, package container formats, the user-facing stage state, Project Gate CI, the deterministic Python foundation for Stage Evidence Bundle validation, `ev4-architect-to-ce-transition@1.0.0`, the narrow CE→Builder, Builder→Responsive, and Final Evidence Gate orchestration baselines documented by the active capability source, and the initial local operator UI shell.

## Current Status

```yaml
capabilities:
  architect_to_ce:
    cli_exposure: implemented
    orchestration_baseline: implemented
    real_non_synthetic_handoff: insufficient_evidence
    verification_state: synthetic_fixture_only
  builder_to_responsive:
    cli_exposure: guarded
    official_responsive_validator_integration: implemented
    orchestration_baseline: implemented
    owner_contract_lock: computed_from_pinned_owner_file_bytes
    real_non_synthetic_handoff: insufficient_evidence
    verification_state: verified_by_exact_head_ci
  ce_to_builder:
    cli_exposure: guarded
    orchestration_baseline: implemented
    owner_fixture_integration: verified
    real_non_synthetic_handoff: insufficient_evidence
  final_evidence_gate:
    cli_exposure: guarded
    official_responsive_validator_integration: implemented
    orchestration_baseline: implemented
    prior_lock_chain: pinned_to_immutable_project_gate_commit
    real_non_synthetic_evidence: insufficient_evidence
    verification_state: verified_by_exact_head_ci
  user_interface:
    browser_accessibility_evidence: insufficient_evidence
    service_routing: implemented_prompt_06_fail_closed
    status: implemented_initial_operator_panel
  producer_emitted_gate_artifact:
    common_contract: implemented
    reusable_verifier: implemented
    producer_adoption: implemented
    project_gate_runtime_integration: implemented_prompt_05_explicit_mode
    downstream_producer_ci_enforcement: implemented_immutable_sha_workflow
    real_non_synthetic_handoff: insufficient_evidence
public_cli_transitions:
  - architect-to-ce
  - ce-to-builder
  - builder-to-responsive
  - final-evidence-gate
python_deterministic_core: implemented_initial_v1
stage_bundle_validation: implemented_initial_v1
canonical_schema_owner: false
runtime_dependency_of_specialist_repos: false
node_skeleton: preserved_temporarily
```

Describe every capability only with the layered status above. Do not describe CE→Builder, Builder→Responsive, or Final Evidence Gate as general public CLI workflows or as verified real non-synthetic handoffs. Do not describe real Elementor artifact validation, production readiness, frontend correctness, responsive correctness, accessibility completion, export validation, or UI transition wiring beyond the initial local operator panel as implemented.

## Read First

1. `src/ev4_transition/data/capability-status.v1.json`
2. `docs/IMPLEMENTATION_STATUS.yaml`
3. `README.md`
4. `docs/ROLE_BOUNDARY_MAP.md`
5. `docs/CONTRACT_INVENTORY.md`
6. `docs/COMPATIBILITY_MAP.md`
7. `docs/VALIDATION_STRATEGY.md`
8. `contracts/locks/architect-to-ce-transition.v1.lock.json`
9. `contracts/locks/ce-to-builder-transition.v1.lock.json`
10. Project Gate-owned schemas under `schemas/`
11. `src/ev4_transition/*`
12. `tests/*`
13. the exact producer and consumer contracts in the owning repositories when reviewing transition changes

`docs/EV4_SHARED_CONTRACTS_STATUS.md` is a historical pre-Project-Gate merge ledger, not the active capability authority. Older documents about canonical promotion or the previous shared-contract skeleton are historical when they conflict with the capability source, `docs/IMPLEMENTATION_STATUS.yaml`, README, or this file.

## Planned Workflow

```text
Architect output
→ Gate
→ CE output
→ Gate
→ Builder output and build evidence
→ Gate
→ Responsive output and viewport evidence
→ final Gate
```

Each gate eventually produces either:

- an accepted next-stage package built only from validated evidence; or
- a repair package based on confirmed diagnostics.

Repair ownership remains unresolved unless contracts and evidence establish it.

## Architect → CE Transition Boundary

`ev4-architect-to-ce-transition@1.0.0` may orchestrate only:

```text
Architect Stage Evidence Bundle
→ Project Gate envelope validation
→ source identity validation
→ expected pin and file-byte hash verification
→ pinned Architect payload schema validation
→ official Architect semantic validation
→ deterministic projection using CE-owned v1.1 mapping contract
→ pinned CE v1.1 intake schema validation
→ official CE semantic validation with explicit source-bundle binding
→ CE Stage Evidence Bundle
```

It must not create CE constructability findings, proof-state conclusions, implementation strategy, Elementor feasibility conclusions, Builder authorization, Builder readiness, responsive completion, or production readiness.

The lock manifest records pinned external contract bytes. It is Project Gate orchestration metadata, not a competing canonical schema. The lock manifest must be checked against Project Gate-owned expected dependency configuration; it must not authenticate its own repository, commit, path, role, or identity values.

## CE → Builder Transition Boundary

`ev4-ce-to-builder-transition@1.0.0` is an implemented orchestration baseline. It may verify pinned CE/Builder owner files, run official tools through `src/ev4_transition/runners/`, and emit a Project Gate-owned result envelope. It must not implement CE constructability logic or Builder adapter behavior internally.

The baseline is exposed only as a guarded fail-closed CLI transition, not as functional readiness or a general verified handoff workflow. Owner-fixture integration is verified by PR #20 workflow evidence. Real non-synthetic handoff evidence remains `insufficient_evidence`.

## Hard Boundaries

Do not:

- copy specialist schemas into this repository as competing canonical contracts;
- invent missing fields, identifiers, units, breakpoints, values, relationships, or evidence;
- auto-repair specialist outputs;
- select a winning schema or architectural authority;
- silently normalize undocumented differences;
- mark a stage accepted without executed evidence;
- hide known incompatibilities because a decision record exists;
- claim real EV4 transition compatibility from synthetic or owner fixtures;
- remove or disable the legacy Node skeleton until a dedicated retirement PR proves parity.

When a conclusion cannot be established, use:

```yaml
status: insufficient_evidence
missing_evidence: explicit
repair_owner: unresolved
```

## Python Implementation Rules

- Preserve public contracts unless a breaking change is explicitly approved.
- Isolate repository/network access behind mockable interfaces.
- Use stable ordering and versioned canonical JSON.
- Use SHA-256 over canonical UTF-8 content or explicit file bytes.
- Reject NaN and infinities.
- Do not inject live timestamps in deterministic core logic.
- If timestamps are accepted, require explicit RFC3339 UTC input.
- Use deterministic diagnostic codes, ordering, and paths.
- Validate every emitted validation-result object against its schema.
- Do not append diagnostics, hashes, status, provenance, or output after final transition-result schema validation.
- Add stable fixtures and tests for every implemented rule.
- Label synthetic fixtures as synthetic.
- Do not implement future transition features unless explicitly requested.

## Validation

Current checks include:

```bash
python -m pip install -e '.[dev]'
pytest
python scripts/check-capability-truth.py
python scripts/check-workflow-permissions.py
ev4-transition validate fixtures/valid/architect-stage-bundle.v1.json
ev4-transition validate fixtures/invalid/array-input.v1.json
ev4-transition validate fixtures/insufficient-evidence/architect-stage-bundle.v1.json --format persian
python scripts/check-github-action-pinning.py
npm run status
npm run validate
```

Architect-to-CE transition checks require pinned local checkouts:

```bash
python scripts/verify-architect-to-ce-lock.py \
  --architect-repo path/to/EV4-Architect-Repo \
  --ce-repo path/to/EV4-Constructability-Engineer-Repo

ev4-transition transition architect-to-ce path/to/architect-stage-bundle.json \
  --architect-repo path/to/EV4-Architect-Repo \
  --ce-repo path/to/EV4-Constructability-Engineer-Repo
```

The GitHub workflow must keep both the existing skeleton health checks and the Python checks until Node retirement is handled in a later PR.

## User Experience Boundary

The normal user is non-technical. The primary interaction is upload, check, understand, and download through the local operator UI.

User-facing summaries are Persian and must clearly distinguish accepted, repair-needed, and insufficient-evidence states. Meaning must not depend on color alone. Technical identifiers and evidence remain available as optional details.

## Evidence States

Use explicit states:

```text
observed
exported
validated
resolved
derived
proposed
unverified
insufficient_evidence
```

Every factual compatibility conclusion must trace to explicit input, pinned repository refs, exact paths, official validators/adapters, fixtures, deterministic rule results, or retained execution evidence.

## Pull Requests

A PR must state:

- required change versus optional recommendation;
- repositories and contract boundaries affected;
- compatibility and versioning impact;
- tests and checks actually executed;
- fixtures or reports added or changed;
- remaining unverified behavior or missing evidence.

Avoid unrelated refactoring and never claim validation without executed evidence.
