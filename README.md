# EV4 Project Gate

Status: The deterministic Python foundation and the `ev4-architect-to-ce-transition@1.0.0`, `ev4-ce-to-builder-transition@1.0.0`, `ev4-builder-to-responsive-transition@1.0.0`, and `ev4-final-evidence-gate@1.0.0` orchestration baselines are implemented at their documented scopes. Only Architect → CE is exposed through the public CLI. Real non-synthetic handoff evidence remains insufficient, and the user interface is not implemented.

## Purpose

`EV4-Project-Gate` is the planned control center between the four EV4 specialist repositories:

```text
Architect → Project Gate → CE → Project Gate → Builder
→ Project Gate → Responsive → Project Gate → final evidence
```

Each specialist repository remains authoritative for its own schemas, validators, adapters, fixtures, and domain behavior. This repository coordinates cross-repository checks and package handoffs. It is not a canonical shared-schema owner or a fifth architecture authority.

## Implemented now

This repository contains the deterministic Python foundation:

```text
Stage Evidence Bundle JSON
→ Python envelope validation
→ structured diagnostics
→ canonical JSON and SHA-256 hashes
→ machine-readable result or Persian summary
```

Implemented components:

- Python package: `src/ev4_transition`
- CLI: `ev4-transition`
- Stage Evidence Bundle envelope schema: `schemas/stage-bundle/stage-bundle.v1.schema.json`
- Validation result schema: `schemas/transition-result/transition-result.v1.schema.json`
- Architect-to-CE transition result schema: `schemas/architect-to-ce-transition-result/architect-to-ce-transition-result.v1.schema.json`
- Synthetic valid, invalid, and insufficient-evidence fixtures
- Pytest coverage for deterministic hashes, malformed inputs, structured diagnostics, provenance preservation, lock enforcement, validator order, and result-schema enforcement
- GitHub Actions Python validation alongside the existing Node skeleton checks

Implemented transition:

```text
ev4-architect-to-ce-transition@1.0.0
```

It performs:

```text
Architect Stage Evidence Bundle
→ Project Gate envelope validation
→ source identity validation
→ expected external pin and file-byte hash verification
→ pinned Architect payload schema validation
→ official Architect semantic validation
→ deterministic Architect-to-CE mapping
→ pinned CE v1.1 intake schema validation
→ official CE semantic validation with explicit source-bundle binding
→ CE Stage Evidence Bundle
→ transition result schema validation
```

The transition executes the official Architect and CE validators in CLI/CI when pinned local checkouts are supplied.

## Authoritative pins for Architect → CE

```yaml
transition_id: ev4-architect-to-ce-transition@1.0.0
architect:
  repository: rezahh107/EV4-Architect-Repo
  commit: b0651668b97f682bb17f66840c8e8c503fd3935d
  schema: ev4-architect-stage-payload@1.0.0
ce:
  repository: rezahh107/EV4-Constructability-Engineer-Repo
  commit: 546680a2e2a309c0d7e0ddbfc017e9e194ece7cb
  intake_schema: ev4-ce-architect-stage-intake@1.1.0
  mapping_contract: ev4-architect-stage-to-ce-intake-mapping@1.1.0
verification_state: synthetic_fixture_only
real_elementor_validation: not_available
```

## Not implemented yet

The following remain intentionally out of scope:

- CE-to-Builder general public CLI exposure
- Builder-to-Responsive general public CLI exposure
- Final Evidence Gate general public CLI exposure
- real non-synthetic CE-to-Builder handoff verification
- real non-synthetic Builder-to-Responsive handoff verification
- real non-synthetic final evidence verification
- CE constructability execution
- implementation strategy selection
- Builder authorization
- real Elementor artifact validation
- UI/upload-download application
- legacy Node retirement

The CE-to-Builder, Builder-to-Responsive, and Final Evidence Gate orchestration baselines, result schemas, lock verification, runner integration, and scoped tests exist in the repository. `ev4-transition inspect` reports the layered status from `src/ev4_transition/data/capability-status.v1.json`.

Do not claim real EV4 end-to-end compatibility from synthetic transition fixtures, owner-fixture integration, or pinned-owner validator execution.

## CLI

```bash
python -m pip install -e '.[dev]'
ev4-transition validate fixtures/valid/architect-stage-bundle.v1.json
ev4-transition validate fixtures/insufficient-evidence/architect-stage-bundle.v1.json --format persian
ev4-transition transition architect-to-ce path/to/architect-stage-bundle.json \
  --architect-repo ../EV4-Architect-Repo \
  --ce-repo ../EV4-Constructability-Engineer-Repo \
  --format json
ev4-transition inspect
```

Exit codes:

```text
0 = valid
1 = invalid
2 = insufficient_evidence
```

## Stage Evidence Bundle

The common envelope requires:

- explicit stage identity
- explicit payload schema identity
- producer repository/ref
- structured evidence items
- declared SHA-256 artifact hash records
- provenance
- explicit synthetic fixture labeling

The envelope validates transport and evidence structure. It does not validate stage-owned specialist semantics.

## Hash scope

This foundation uses versioned canonical JSON behavior:

```yaml
canonicalization: ev4-canonical-json.v1
key_ordering: deterministic_lexicographic
encoding: utf8
serialization: compact_json
nan_and_infinity: rejected
```

Transition hash records cover source bundle, source payload, target payload, target bundle, and external contract lock.

No implicit current timestamp is generated by the deterministic core.

## `insufficient_evidence`

`insufficient_evidence` is a first-class status. It means the bundle is parseable and structurally understood, but the evidence is not enough for a safe next step.

The validator must not invent missing evidence, silently fill important fields, or repair specialist outputs.

## Evidence Policy

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

Compatibility is checked through pinned official contracts, validators, and synthetic cross-repository fixtures. Synthetic fixtures remain clearly identified as synthetic and must not be described as real Elementor artifact validation.

## Repository Responsibilities

```text
EV4-Architect-Repo
  architecture decisions and architecture handoff

EV4-Constructability-Engineer-Repo
  constructability and implementation-strategy proof

EV4-Builder-Assistant-Repo
  interactive Elementor execution and build evidence

EV4-Responsive-Architect
  post-build responsive validation and repair

EV4-Project-Gate
  deterministic envelope validation, diagnostics, provenance, hashes, external pin verification, and package orchestration
```

## Personal local use

Personal-use setup and controlled demo docs:

- `docs/LOCAL_SETUP_GUIDE.md`
- `docs/PERSONAL_USE_GUIDE.md`
- `docs/E2E_DEMO_WORKFLOW.md`

Local launcher scripts:

```bash
python scripts/run-project-gate-ui.py
python scripts/run-project-gate-demo.py
```

Windows helpers:

```text
scripts/run-project-gate-ui.ps1
scripts/run-project-gate-ui.bat
```

Notes:

- UI/operator panel support requires the Prompt 1 UI branch/merge.
- Internal service/API integration requires the Prompt 2 service branch/merge.
- The controlled demo uses synthetic fixtures only and does not claim production readiness, real Elementor validation, frontend correctness, responsive correctness, accessibility completion, export validation, or real end-to-end readiness.
- Generated local outputs belong under `outputs/runs/<timestamp-or-run-id>/` and should not be committed.

## Validation

Python checks:

```bash
python -m pip install -e '.[dev]'
pytest
python scripts/check-capability-truth.py
python scripts/check-workflow-permissions.py
ev4-transition validate fixtures/valid/architect-stage-bundle.v1.json
ev4-transition validate fixtures/invalid/array-input.v1.json
ev4-transition validate fixtures/insufficient-evidence/architect-stage-bundle.v1.json --format persian
python scripts/verify-architect-to-ce-lock.py \
  --architect-repo ../EV4-Architect-Repo \
  --ce-repo ../EV4-Constructability-Engineer-Repo
python scripts/transition-smoke.py \
  --architect-repo ../EV4-Architect-Repo \
  --ce-repo ../EV4-Constructability-Engineer-Repo
```

Existing Node skeleton checks remain available temporarily:

```bash
npm run status
npm run validate
```
