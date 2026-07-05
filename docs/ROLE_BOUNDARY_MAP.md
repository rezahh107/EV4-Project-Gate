# EV4 Role Boundary Map

Status: Architect→CE, CE→Builder, Builder→Responsive, and Final Evidence Gate orchestration baselines are implemented. Only Architect→CE has public CLI exposure. Real non-synthetic EV4 handoff/evidence remains `insufficient_evidence` for transition readiness beyond the synthetic or pinned-owner integration proofs.

## Authority rule

Specialist repositories remain authoritative for their schemas, validators, adapters, fixtures, and domain behavior. Project Gate may pin, hash, call, validate, report, and package handoffs. It must not replace specialist logic.

| Repository | Role | Owns | Must Not Own | Allowed Outputs | Blocked Outputs | Downstream Consumer | Current Authority Status |
|---|---|---|---|---|---|---|---|
| `rezahh107/EV4-Architect-Repo` | Architect | Architecture decisions; selected candidate identity; approved structure model; class intent; forbidden work; Architect Stage Payload `ev4-architect-stage-payload@1.0.0`; Architect semantic validator and fixtures | Constructability proof; Builder runtime authorization; Builder execution; Responsive correctness; production readiness | Architect Stage Payload; architecture handoff evidence; CE-intake source data | Builder-ready runtime package; CE proof; Responsive completion; real Elementor validation | Project Gate, then CE | repo-local authoritative for Architect-owned design/handoff concepts |
| `rezahh107/EV4-Constructability-Engineer-Repo` | Constructability Engineer | Constructability review; implementation-strategy proof; canonical Architect-facing CE intake `ev4-ce-architect-stage-intake@1.1.0`; CE-owned mapping `ev4-architect-stage-to-ce-intake-mapping@1.1.0`; Builder Executable Package producer semantics | Architect redesign; Builder runtime execution; Builder adapter projection; Responsive repair; production readiness | CE intake validation; CE review output; Builder Executable Package when evidence-gated | Builder runtime output; Builder compact `node:model` carriers in CE source output; production-ready claims | Project Gate, then Builder | repo-local authoritative for CE review/gating and executable handoff issuance |
| `rezahh107/EV4-Builder-Assistant-Repo` | Builder | Runtime intake validation; `ev4-builder-context-package@1.0.0`; CE→Builder Contract Gate; CE→Builder adapter; Builder action batch, layout check, completion gate, and real Elementor execution evidence validators | Architecture decisions; CE strategy proof; Responsive conclusions; production readiness; invention of missing Golden Reference / Build Intent Brief / Spatial Lexicon | Normalized Builder runtime intake; execution/build evidence; Builder-side validation decisions | Architect-only package treated as Builder-ready; CE review-only package treated as runtime-ready; Responsive correctness claims | Project Gate, then Responsive | repo-local authoritative for Builder runtime intake, execution behavior, and Builder-owned evidence surfaces |
| `rezahh107/EV4-Responsive-Architect` | Responsive Architect | Responsive input eligibility; `ev4-builder-responsive-input@0.1.0`; responsive output `ev4-responsive-output@0.3.0`; viewport evidence gates; Responsive repair semantics; responsive handoff export family | Original architecture selection; CE constructability proof; Builder execution; mobile/tablet inference from desktop-only evidence; final readiness without evidence | Responsive input eligibility decisions; responsive output; viewport-scoped evidence; repair outputs when authorized | Raw screenshot as baseline authority; frontend/export/accessibility/production claims without evidence | Project Gate final gate | repo-local authoritative for responsive adaptation, viewport evidence, and Responsive-owned output concepts |
| `rezahh107/EV4-Project-Gate` | Project Gate | Stage Evidence Bundle envelope; transition/result schemas; diagnostic schema; lock manifest schema; deterministic canonical JSON and SHA-256; pinned external contract verification; Architect→CE orchestration; CE→Builder orchestration baseline; Builder→Responsive orchestration baseline; Final Evidence Gate orchestration baseline; official validator/adapter execution through `src/ev4_transition/runners/`; diagnostics; Persian summaries; report rendering; atomic output writing; behavioral coverage ledger | Specialist schemas as canonical copies; CE constructability logic; Builder runtime logic; Responsive repair logic; evidence invention; silent normalization; accepted/final claims without evidence; subprocess execution outside `src/ev4_transition/runners/` | Validation results; transition results; pinned/hash reports; next-stage packages only when owner contracts/evidence validate; repair/insufficient-evidence diagnostics; Persian reports | Specialist logic; copied owner schemas; synthetic or owner fixtures described as real evidence; production readiness claims | User and next specialist repository | Project Gate-owned orchestration authority only |

## Boundary invariants

```yaml
project_gate:
  may:
    - validate_envelopes
    - verify_schema_identity
    - pin_refs_commits_paths
    - compute_sha256_hashes
    - call_official_validators
    - call_official_adapters
    - produce_diagnostics
    - emit_json_results
    - write_persian_summaries
  must_not:
    - copy_specialist_schemas_as_canonical_truth
    - implement_CE_constructability_logic
    - implement_Builder_runtime_logic
    - implement_Responsive_repair_logic
    - invent_evidence
    - silently_normalize_specialist_outputs
    - emit_accepted_without_explicit_evidence
```

## Project Gate-owned deterministic infrastructure

```text
schemas/diagnostic/diagnostic.v1.schema.json
schemas/lock-manifest/lock-manifest.v1.schema.json
src/ev4_transition/core/
src/ev4_transition/stage_bundle/
src/ev4_transition/locks/
src/ev4_transition/presentation/status_mapping.py
src/ev4_transition/runners/
src/ev4_transition/reports/
src/ev4_transition/io/atomic_writer.py
```

Only `src/ev4_transition/runners/` may execute subprocesses for official specialist validators or adapters.

```yaml
runner_boundary:
  allowed_inside:
    - src/ev4_transition/runners/subprocess_runner.py imports and calls subprocess
    - src/ev4_transition/runners/official_tools.py builds official validator/adapter commands
    - src/ev4_transition/runners/responsive_tools.py builds official Responsive validator commands
    - src/ev4_transition/runners/records.py creates execution records
    - src/ev4_transition/runners/failure_mapping.py maps failures to deterministic Project Gate statuses
  forbidden_outside:
    - subprocess imports or calls
    - os.system
    - shell=true
    - importlib-based dynamic specialist imports
    - direct Python/Node command execution for specialist tools
  scanner:
    - scripts/check-runner-boundary.py
```

`src/ev4_transition/validator_runner.py` remains a compatibility wrapper for the Architect→CE CLI path and delegates execution to the runner boundary.

## CE → Builder boundary

```yaml
transition_id: ev4-ce-to-builder-transition@1.0.0
orchestration_baseline: implemented
cli_exposure: not_implemented
owner_fixture_integration: verified
real_non_synthetic_handoff: insufficient_evidence
```

Project Gate may verify the CE/Builder lock, run official tools, validate the Builder-owned output schema, and emit a Project Gate result. It must not duplicate the CE validator, Builder contract gate, Builder adapter, or Builder output rules.

## Builder → Responsive boundary

```yaml
transition_id: ev4-builder-to-responsive-transition@1.0.0
orchestration_baseline: implemented
cli_exposure: not_implemented
official_responsive_validator_integration: implemented
real_non_synthetic_handoff: insufficient_evidence
```

Project Gate may verify the Builder/Responsive lock, preserve Builder evidence references as transport metadata, validate Responsive-owned intake, run official Responsive input validators, and emit a Project Gate result. It must not invent Builder execution evidence or Responsive repair semantics.

## Final Evidence Gate boundary

```yaml
gate_id: ev4-final-evidence-gate@1.0.0
orchestration_baseline: implemented
cli_exposure: not_implemented
official_responsive_validator_integration: implemented
real_non_synthetic_evidence: insufficient_evidence
```

Project Gate may verify the immutable prior lock chain, validate Responsive-owned final output, run official Responsive output validators, and reject unsupported readiness/correctness claims. It must not claim release readiness, production readiness, accessibility completion, export validation, or frontend correctness without explicit owner evidence.

## Current implementation summary

```yaml
implemented:
  - Project Gate deterministic core
  - Stage Evidence Bundle validation
  - structured diagnostics
  - canonical JSON and SHA-256
  - Project Gate diagnostic and lock carrier schemas
  - status presentation mapping
  - Architect-to-CE transition orchestration and public CLI path
  - CE-to-Builder orchestration baseline
  - owner-fixture CE-to-Builder integration
  - Builder-to-Responsive orchestration baseline
  - Final Evidence Gate orchestration baseline
  - runner boundary for official validator/adapter subprocess execution
  - local-only mockable repo access abstraction
  - sanitized runtime progress events
  - static runner-boundary scanner
  - Persian report rendering and atomic report writing
not_implemented:
  - CE-to-Builder public CLI exposure
  - Builder-to-Responsive public CLI exposure
  - Final Evidence Gate public CLI exposure
  - real non-synthetic CE-to-Builder handoff verification
  - real non-synthetic Builder execution evidence verification
  - real non-synthetic Responsive input/output evidence verification
  - UI/upload-download application
  - real Elementor artifact validation
```

## Known evidence gaps

```yaml
- id: STATUS-MODEL-LEGACY-VALID
  description: Current Stage Bundle validation and Architect→CE paths retain legacy valid status compatibility while newer transition results use accepted/repair_needed/insufficient_evidence/invalid.
  action: preserve compatibility unless a breaking status migration is explicitly approved.
- id: REAL-EV4-EVIDENCE-GAP
  description: Prompt-04 and Prompt-05 verify orchestration, locks, fixtures, and pinned owner validators, but not a real non-synthetic EV4 Builder/Responsive evidence chain.
  action: keep real handoff/final readiness at insufficient_evidence until owner evidence bundles exist and pass.
```
