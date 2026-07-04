# Behavioral Rule Coverage

Status: `PROMPT-02` Behavioral Rule Coverage hardening. This file now contains a machine-readable coverage ledger validated by `schemas/behavioral-coverage/behavioral-coverage.v1.schema.json` and `scripts/validate-behavioral-rule-coverage.py`.

Allowed statuses:

```text
prose_only
schema_backed
validator_backed
fixture_tested
ci_enforced
downstream_contract_enforced
```

## Machine-readable coverage ledger

The JSON block below is the validator source of truth for this document.

```json behavioral-coverage.v1
{
  "schema_version": "behavioral-coverage.v1",
  "generated_by": "PROMPT-02 behavioral coverage validator",
  "rules": [
    {
      "rule_id": "PG-BRC-001",
      "rule": "Behavioral coverage must be tracked honestly.",
      "risk": "High",
      "status": "fixture_tested",
      "target_status": "ci_enforced",
      "carriers": ["docs/BEHAVIORAL_RULE_COVERAGE.md", "schemas/behavioral-coverage/behavioral-coverage.v1.schema.json"],
      "validators": ["src/ev4_transition/behavioral_coverage/validator.py", "scripts/validate-behavioral-rule-coverage.py"],
      "valid_fixtures": ["tests/fixtures/behavioral_coverage/valid/critical_rule_fixture_tested.json"],
      "invalid_fixtures": ["tests/fixtures/behavioral_coverage/invalid/critical_rule_prose_only.json", "tests/fixtures/behavioral_coverage/invalid/critical_rule_schema_backed_without_followup.json"],
      "ci_steps": [".github/workflows/validate.yml / Behavioral coverage validator"],
      "downstream_contracts": [],
      "downstream_rejection_fixtures": [],
      "documented_risk": "False behavioral coverage lets prose-only Critical rules appear enforced.",
      "next_enforcement_step": "Promote to ci_enforced only after this PR workflow passes on the final head.",
      "notes": "Coverage validator is scoped to coverage honesty, not transition orchestration."
    },
    {
      "rule_id": "PG-EVIDENCE-001",
      "rule": "No accepted/final result without explicit evidence.",
      "risk": "Critical",
      "status": "fixture_tested",
      "target_status": "ci_enforced",
      "carriers": ["schemas/transition-result/transition-result.v1.schema.json", "src/ev4_transition/behavioral_coverage/validator.py"],
      "validators": ["validate_transition_result_semantics"],
      "valid_fixtures": ["tests/fixtures/result_envelope/valid/accepted_with_all_required_evidence_shape.json"],
      "invalid_fixtures": ["tests/fixtures/result_envelope/invalid/accepted_missing_validator_evidence.json"],
      "ci_steps": [".github/workflows/validate.yml / Run Project Gate Python tests"],
      "downstream_contracts": [],
      "downstream_rejection_fixtures": [],
      "documented_risk": "Accepted without official validator evidence creates false execution and false readiness claims.",
      "next_enforcement_step": "Promote after final PR CI passes; add transition-specific evidence acquisition in later prompts.",
      "notes": "Semantic fixture guard supplements the schema without changing normal Phase 1 transition validation."
    },
    {
      "rule_id": "PG-SYNTH-001",
      "rule": "Synthetic fixtures must not be treated as real EV4 evidence.",
      "risk": "Critical",
      "status": "fixture_tested",
      "target_status": "ci_enforced",
      "carriers": ["schemas/stage-bundle/stage-bundle.v1.schema.json", "src/ev4_transition/behavioral_coverage/validator.py"],
      "validators": ["validate_transition_result_semantics"],
      "valid_fixtures": ["tests/fixtures/result_envelope/valid/synthetic_fixture_labeled.json"],
      "invalid_fixtures": ["tests/fixtures/result_envelope/invalid/synthetic_only_marked_as_real_evidence.json"],
      "ci_steps": [".github/workflows/validate.yml / Run Project Gate Python tests"],
      "downstream_contracts": [],
      "downstream_rejection_fixtures": [],
      "documented_risk": "Synthetic-only fixtures can otherwise be mistaken for real EV4 transition evidence.",
      "next_enforcement_step": "Promote after CI; keep real evidence gates fail-closed in future transitions.",
      "notes": "A labeled synthetic fixture remains valid only when not accepted as real evidence."
    },
    {
      "rule_id": "PG-SCHEMA-001",
      "rule": "Project Gate must not copy specialist schemas as competing canonical contracts.",
      "risk": "Critical",
      "status": "fixture_tested",
      "target_status": "ci_enforced",
      "carriers": ["schemas/README.md", ".github/workflows/validate.yml", "src/ev4_transition/behavioral_coverage/validator.py"],
      "validators": ["schema allowlist in CI", "validate_stage_bundle_semantics"],
      "valid_fixtures": ["tests/fixtures/stage_bundle/valid/project_gate_owned_schema_only.json"],
      "invalid_fixtures": ["tests/fixtures/stage_bundle/invalid/copied_specialist_schema_claimed_as_project_gate_owned.json"],
      "ci_steps": [".github/workflows/validate.yml / Verify no specialist canonical schema files exist", ".github/workflows/validate.yml / Run Project Gate Python tests"],
      "downstream_contracts": [],
      "downstream_rejection_fixtures": [],
      "documented_risk": "Copied schemas produce contract drift and false canonical ownership.",
      "next_enforcement_step": "Promote after final PR CI passes; extend anti-drift scanner in PROMPT-03.",
      "notes": "This covers Project Gate-owned schema copy claims, not downstream specialist semantics."
    },
    {
      "rule_id": "PG-OUTPUT-001",
      "rule": "Machine-readable JSON and Persian summaries must be truthful.",
      "risk": "High",
      "status": "fixture_tested",
      "target_status": "ci_enforced",
      "carriers": ["src/ev4_transition/cli.py", "src/ev4_transition/behavioral_coverage/validator.py"],
      "validators": ["validate_transition_result_semantics"],
      "valid_fixtures": ["tests/fixtures/result_envelope/valid/output_write_success.json"],
      "invalid_fixtures": ["tests/fixtures/result_envelope/invalid/output_write_failed_but_success.json"],
      "ci_steps": [".github/workflows/validate.yml / Run Project Gate Python tests"],
      "downstream_contracts": [],
      "downstream_rejection_fixtures": [],
      "documented_risk": "A success status after output write failure gives the user an unusable artifact.",
      "next_enforcement_step": "Add full Persian RTL/LTR report fixtures in PROMPT-06.",
      "notes": "Prompt 02 only covers output-write truthfulness, not full UX/typography."
    },
    {
      "rule_id": "PG-BOUNDARY-001",
      "rule": "Project Gate must remain an orchestrator/checkpoint, not a specialist engine.",
      "risk": "Critical",
      "status": "fixture_tested",
      "target_status": "ci_enforced",
      "carriers": ["README.md", "AGENTS.md", "docs/ROLE_BOUNDARY_MAP.md", "src/ev4_transition/behavioral_coverage/validator.py"],
      "validators": ["validate_stage_bundle_semantics"],
      "valid_fixtures": ["tests/fixtures/stage_bundle/valid/project_gate_owned_schema_only.json"],
      "invalid_fixtures": ["tests/fixtures/stage_bundle/invalid/copied_specialist_schema_claimed_as_project_gate_owned.json"],
      "ci_steps": [".github/workflows/validate.yml / Verify no specialist canonical schema files exist", ".github/workflows/validate.yml / Run Project Gate Python tests"],
      "downstream_contracts": [],
      "downstream_rejection_fixtures": [],
      "documented_risk": "Boundary drift turns Project Gate into a fifth specialist engine.",
      "next_enforcement_step": "Add broader static runner/boundary scanner in PROMPT-03.",
      "notes": "Advanced at anti-drift/coverage level only; no CE/Builder/Responsive domain logic was added."
    },
    {
      "rule_id": "PG-DOWNSTREAM-001",
      "rule": "Downstream rejection evidence is required before claiming downstream compatibility.",
      "risk": "Critical",
      "status": "fixture_tested",
      "target_status": "downstream_contract_enforced",
      "carriers": ["docs/BEHAVIORAL_RULE_COVERAGE.md", "src/ev4_transition/behavioral_coverage/validator.py"],
      "validators": ["validate_coverage_document"],
      "valid_fixtures": ["tests/fixtures/behavioral_coverage/valid/critical_rule_fixture_tested.json"],
      "invalid_fixtures": ["tests/fixtures/behavioral_coverage/invalid/downstream_contract_missing_for_claimed_enforcement.json"],
      "ci_steps": [".github/workflows/validate.yml / Behavioral coverage validator"],
      "downstream_contracts": [],
      "downstream_rejection_fixtures": [],
      "documented_risk": "Future transitions must not claim downstream_contract_enforced without owner rejection evidence.",
      "next_enforcement_step": "PROMPT-04/05 must add real downstream contract and rejection evidence before changing this to downstream_contract_enforced.",
      "notes": "This is visibility/gap tracking and false-claim prevention; it is not downstream compatibility enforcement."
    }
  ]
}
```

## Coverage table

| Rule ID | Risk | Current status | Coverage meaning | Next enforcement step |
|---|---|---|---|---|
| `PG-BRC-001` | `High` | `fixture_tested` | Coverage validator/schema/fixtures now exist. | Promote to `ci_enforced` only after this PR workflow passes on the final head. |
| `PG-EVIDENCE-001` | `Critical` | `fixture_tested` | `accepted` without explicit validator evidence fails semantic fixture validation. | Add transition-specific evidence acquisition in later prompts. |
| `PG-SYNTH-001` | `Critical` | `fixture_tested` | Synthetic-only accepted-as-real evidence fails semantic fixture validation. | Keep future real evidence gates fail-closed. |
| `PG-SCHEMA-001` | `Critical` | `fixture_tested` | Copied specialist schema ownership claims fail semantic fixture validation. | Extend scanner in `PROMPT-03`. |
| `PG-OUTPUT-001` | `High` | `fixture_tested` | Output-write failure paired with success status fails. | Add full Persian report UX fixtures in `PROMPT-06`. |
| `PG-BOUNDARY-001` | `Critical` | `fixture_tested` | Boundary anti-drift is covered at schema-ownership level. | Add broader runner/boundary scanner in `PROMPT-03`. |
| `PG-DOWNSTREAM-001` | `Critical` | `fixture_tested` | False downstream enforcement claims fail without downstream contract/rejection fixture. | Real downstream enforcement remains deferred to `PROMPT-04/05`. |

## Rules advanced by PROMPT-02

```yaml
advanced:
  - PG-BRC-001: schema, validator, fixtures, CLI, and CI step configured.
  - PG-EVIDENCE-001: accepted-without-validator-evidence semantic fixture now fails.
  - PG-SYNTH-001: synthetic-only evidence marked accepted now fails.
  - PG-SCHEMA-001: copied specialist schema claimed as Project Gate-owned now fails at semantic fixture level.
  - PG-OUTPUT-001: output write failure paired with success status now fails.
  - PG-BOUNDARY-001: anti-drift coverage fixture added for schema ownership claims.
  - PG-DOWNSTREAM-001: false downstream_contract_enforced claims now fail unless downstream contract and rejection fixture exist.
not_advanced_to_full_enforcement:
  - no CE-to-Builder transition orchestration added
  - no Builder-to-Responsive transition orchestration added
  - no specialist validator/adapter calls added beyond existing A2C baseline
  - no downstream_contract_enforced claim added for future transitions
  - ci_enforced status for Prompt 02 additions requires final PR workflow evidence
```

## Critical / High gaps

```yaml
critical:
  - PG-ADAPTER-001 still needs PROMPT-03 runner/adapter boundary enforcement.
  - PG-DOWNSTREAM-001 is fixture_tested for false-claim prevention only; real downstream compatibility remains insufficient_evidence until PROMPT-04/05.
  - PG-STATUS-001 still has legacy valid compatibility in existing A2C/stage-bundle paths.
high:
  - PG-PROGRESS-001 still lacks a handoff/report linter.
  - PG-OUTPUT-001 still lacks full Persian RTL/LTR report-contract fixtures; PROMPT-02 only covers output-write truthfulness.
```

## Enforcement honesty note

`fixture_tested` means the behavioral claim has a validator plus valid/invalid fixture coverage. It does not mean downstream owner compatibility unless the status is explicitly `downstream_contract_enforced` and the ledger includes downstream contracts plus downstream rejection fixtures.
