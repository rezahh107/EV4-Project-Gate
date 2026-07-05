# Behavioral Rule Coverage

Status: `PROMPT-03` Runner Boundary and Official Tool Execution infrastructure. This file contains a machine-readable coverage ledger validated by `schemas/behavioral-coverage/behavioral-coverage.v1.schema.json` and `scripts/validate-behavioral-rule-coverage.py`.

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
  "generated_by": "PROMPT-03 runner boundary infrastructure with split CI references",
  "rules": [
    {
      "rule_id": "PG-BRC-001",
      "rule": "Behavioral coverage must be tracked honestly.",
      "risk": "High",
      "status": "fixture_tested",
      "target_status": "ci_enforced",
      "carriers": ["docs/BEHAVIORAL_RULE_COVERAGE.md", "schemas/behavioral-coverage/behavioral-coverage.v1.schema.json"],
      "validators": ["src/ev4_transition/behavioral_coverage/validator.py::validate_coverage_document", "scripts/validate-behavioral-rule-coverage.py"],
      "valid_fixtures": ["tests/fixtures/behavioral_coverage/valid/critical_rule_fixture_tested.json"],
      "invalid_fixtures": ["tests/fixtures/behavioral_coverage/invalid/critical_rule_prose_only.json", "tests/fixtures/behavioral_coverage/invalid/critical_rule_schema_backed_without_followup.json"],
      "ci_steps": [".github/workflows/validate.yml / Behavioral coverage validator"],
      "downstream_contracts": [],
      "downstream_rejection_fixtures": [],
      "documented_risk": "False behavioral coverage can make weak rules look enforced.",
      "next_enforcement_step": "Promote to ci_enforced only after the current PR head workflow passes.",
      "notes": "Coverage validator resolves references and emits deterministic evidence_records. PROMPT-03 does not promote CI status without CI evidence."
    },
    {
      "rule_id": "PG-EVIDENCE-001",
      "rule": "No accepted/final result without explicit evidence, including official tool execution records where applicable.",
      "risk": "Critical",
      "status": "fixture_tested",
      "target_status": "ci_enforced",
      "carriers": ["schemas/transition-result/transition-result.v1.schema.json", "schemas/validator-evidence/validator-evidence.v1.schema.json", "schemas/diagnostic/diagnostic.v1.schema.json", "src/ev4_transition/behavioral_coverage/validator.py", "src/ev4_transition/runners/records.py", "docs/RESULT_MODEL.md"],
      "validators": ["src/ev4_transition/behavioral_coverage/validator.py::validate_transition_result_semantics"],
      "valid_fixtures": ["tests/fixtures/result_envelope/valid/accepted_with_all_required_evidence_shape.json"],
      "invalid_fixtures": ["tests/fixtures/result_envelope/invalid/accepted_missing_validator_evidence.json", "tests/fixtures/result_envelope/invalid/accepted_with_failed_validator_evidence.json", "tests/fixtures/result_envelope/invalid/accepted_with_unknown_validator_evidence.json", "tests/fixtures/result_envelope/invalid/accepted_with_malformed_validator_evidence.json", "tests/fixtures/result_envelope/invalid/accepted_with_unpinned_validator_evidence.json", "tests/fixtures/result_envelope/invalid/accepted_with_validator_hash_mismatch.json", "tests/fixtures/result_envelope/invalid/accepted_with_validator_stage_mismatch.json"],
      "ci_steps": [".github/workflows/validate.yml / Behavioral fixture validation", ".github/workflows/validate.yml / Prompt 01 unit tests", ".github/workflows/validate.yml / Runner tests"],
      "downstream_contracts": [],
      "downstream_rejection_fixtures": [],
      "documented_risk": "Accepted with failed, unknown, unpinned, or mismatched validator evidence is a false readiness claim.",
      "next_enforcement_step": "Promote after current PR CI passes; add real transition evidence acquisition in later prompts.",
      "notes": "PROMPT-03 adds execution-record carriers and dotted Project Gate diagnostic-code compatibility for official tool evidence."
    },
    {
      "rule_id": "PG-SYNTH-001",
      "rule": "Synthetic fixtures must not be treated as real EV4 evidence.",
      "risk": "Critical",
      "status": "fixture_tested",
      "target_status": "ci_enforced",
      "carriers": ["schemas/stage-bundle/stage-bundle.v1.schema.json", "src/ev4_transition/behavioral_coverage/validator.py"],
      "validators": ["src/ev4_transition/behavioral_coverage/validator.py::validate_transition_result_semantics"],
      "valid_fixtures": ["tests/fixtures/result_envelope/valid/synthetic_fixture_labeled.json"],
      "invalid_fixtures": ["tests/fixtures/result_envelope/invalid/synthetic_only_marked_as_real_evidence.json"],
      "ci_steps": [".github/workflows/validate.yml / Behavioral fixture validation"],
      "downstream_contracts": [],
      "downstream_rejection_fixtures": [],
      "documented_risk": "Synthetic-only fixtures can otherwise be mistaken for real EV4 transition evidence.",
      "next_enforcement_step": "Keep future real evidence gates fail-closed.",
      "notes": "PROMPT-03 does not change synthetic evidence semantics."
    },
    {
      "rule_id": "PG-SCHEMA-001",
      "rule": "Project Gate must not copy specialist schemas as competing canonical contracts.",
      "risk": "Critical",
      "status": "fixture_tested",
      "target_status": "ci_enforced",
      "carriers": ["schemas/README.md", ".github/workflows/validate.yml", "src/ev4_transition/behavioral_coverage/validator.py"],
      "validators": ["src/ev4_transition/behavioral_coverage/validator.py::validate_stage_bundle_semantics"],
      "valid_fixtures": ["tests/fixtures/stage_bundle/valid/project_gate_owned_schema_only.json"],
      "invalid_fixtures": ["tests/fixtures/stage_bundle/invalid/copied_specialist_schema_claimed_as_project_gate_owned.json", "tests/fixtures/stage_bundle/invalid/project_gate_schema_prefix_collision_specialist_copy.json"],
      "ci_steps": [".github/workflows/validate.yml / Verify no specialist canonical schema files exist", ".github/workflows/validate.yml / Behavioral fixture validation"],
      "downstream_contracts": [],
      "downstream_rejection_fixtures": [],
      "documented_risk": "Copied schemas produce contract drift and false canonical ownership.",
      "next_enforcement_step": "Keep exact registry and anti-drift scanner; do not copy specialist schemas during transition prompts.",
      "notes": "PROMPT-03 adds runner infrastructure only, not specialist schemas."
    },
    {
      "rule_id": "PG-OUTPUT-001",
      "rule": "Machine-readable JSON and Persian summaries must be truthful.",
      "risk": "High",
      "status": "fixture_tested",
      "target_status": "ci_enforced",
      "carriers": ["src/ev4_transition/cli.py", "src/ev4_transition/behavioral_coverage/validator.py"],
      "validators": ["src/ev4_transition/behavioral_coverage/validator.py::validate_transition_result_semantics"],
      "valid_fixtures": ["tests/fixtures/result_envelope/valid/output_write_success.json"],
      "invalid_fixtures": ["tests/fixtures/result_envelope/invalid/output_write_failed_but_success.json"],
      "ci_steps": [".github/workflows/validate.yml / Behavioral fixture validation", ".github/workflows/validate.yml / CLI and bundle tests"],
      "downstream_contracts": [],
      "downstream_rejection_fixtures": [],
      "documented_risk": "A success status after output write failure gives the user an unusable artifact.",
      "next_enforcement_step": "Add full Persian RTL/LTR report fixtures in PROMPT-06.",
      "notes": "Prompt 03 adds progress sanitization, but not full Persian report UX fixtures."
    },
    {
      "rule_id": "PG-BOUNDARY-001",
      "rule": "Project Gate must remain an orchestrator/checkpoint, not a specialist engine; only runners may execute official specialist tools.",
      "risk": "Critical",
      "status": "fixture_tested",
      "target_status": "ci_enforced",
      "carriers": ["README.md", "AGENTS.md", "docs/ROLE_BOUNDARY_MAP.md", "src/ev4_transition/behavioral_coverage/validator.py", "scripts/check-runner-boundary.py", "src/ev4_transition/runners/subprocess_runner.py"],
      "validators": ["src/ev4_transition/behavioral_coverage/validator.py::validate_stage_bundle_semantics", "scripts/check-runner-boundary.py::scan_runner_boundary"],
      "valid_fixtures": ["tests/fixtures/stage_bundle/valid/project_gate_owned_schema_only.json"],
      "invalid_fixtures": ["tests/fixtures/stage_bundle/invalid/copied_specialist_schema_claimed_as_project_gate_owned.json", "tests/fixtures/stage_bundle/invalid/project_gate_schema_prefix_collision_specialist_copy.json"],
      "ci_steps": [".github/workflows/validate.yml / Verify no specialist canonical schema files exist", ".github/workflows/validate.yml / Static runner-boundary scanner", ".github/workflows/validate.yml / Runner boundary tests"],
      "downstream_contracts": [],
      "downstream_rejection_fixtures": [],
      "documented_risk": "Boundary drift turns Project Gate into a fifth specialist engine or hides unsafe execution.",
      "next_enforcement_step": "Promote to ci_enforced only after current PR CI passes and static scanner evidence is available.",
      "notes": "PROMPT-03 adds static scanner and tests for subprocess/os.system boundary."
    },
    {
      "rule_id": "PG-DOWNSTREAM-001",
      "rule": "Downstream rejection evidence is required before claiming downstream compatibility.",
      "risk": "Critical",
      "status": "fixture_tested",
      "target_status": "downstream_contract_enforced",
      "carriers": ["docs/BEHAVIORAL_RULE_COVERAGE.md", "src/ev4_transition/behavioral_coverage/validator.py"],
      "validators": ["src/ev4_transition/behavioral_coverage/validator.py::validate_coverage_document"],
      "valid_fixtures": ["tests/fixtures/behavioral_coverage/valid/critical_rule_fixture_tested.json"],
      "invalid_fixtures": ["tests/fixtures/behavioral_coverage/invalid/downstream_contract_missing_for_claimed_enforcement.json"],
      "ci_steps": [".github/workflows/validate.yml / Behavioral coverage validator"],
      "downstream_contracts": [],
      "downstream_rejection_fixtures": [],
      "documented_risk": "Future transitions must not claim downstream_contract_enforced without owner rejection evidence.",
      "next_enforcement_step": "PROMPT-04/05 must add real downstream contract and rejection evidence before changing this to downstream_contract_enforced.",
      "notes": "PROMPT-03 does not implement downstream transition logic."
    },
    {
      "rule_id": "PG-VALIDATOR-001",
      "rule": "Official validators must execute only through Project Gate runner infrastructure and fail closed when missing, timed out, unparseable, or structurally failed.",
      "risk": "Critical",
      "status": "validator_backed",
      "target_status": "validator_backed",
      "carriers": ["src/ev4_transition/runners/official_tools.py", "src/ev4_transition/runners/subprocess_runner.py", "src/ev4_transition/runners/failure_mapping.py", "src/ev4_transition/validator_runner.py", "docs/RESULT_MODEL.md"],
      "validators": ["src/ev4_transition/runners/official_tools.py::execute_validator", "src/ev4_transition/runners/subprocess_runner.py::execute_official_tool"],
      "valid_fixtures": [],
      "invalid_fixtures": [],
      "ci_steps": [".github/workflows/validate.yml / Runner tests"],
      "downstream_contracts": [],
      "downstream_rejection_fixtures": [],
      "documented_risk": "Missing or failed validator execution must never be treated as acceptance.",
      "next_enforcement_step": "Promote only after behavioral coverage validator supports runner test fixture families and current PR CI passes.",
      "notes": "Pytest runner tests are added in tests/runners, but ledger status remains validator_backed until fixture binding rules are extended."
    },
    {
      "rule_id": "PG-ADAPTER-001",
      "rule": "Official adapters must execute only through runner infrastructure; fallback adapters are forbidden and missing/timeouts fail closed.",
      "risk": "Critical",
      "status": "validator_backed",
      "target_status": "validator_backed",
      "carriers": ["src/ev4_transition/runners/official_tools.py", "src/ev4_transition/runners/subprocess_runner.py", "src/ev4_transition/runners/failure_mapping.py", "docs/RESULT_MODEL.md"],
      "validators": ["src/ev4_transition/runners/official_tools.py::execute_adapter", "src/ev4_transition/runners/subprocess_runner.py::execute_official_tool"],
      "valid_fixtures": [],
      "invalid_fixtures": [],
      "ci_steps": [".github/workflows/validate.yml / Runner tests"],
      "downstream_contracts": [],
      "downstream_rejection_fixtures": [],
      "documented_risk": "Fallback or missing adapter behavior can invent a next-stage package without owner evidence.",
      "next_enforcement_step": "Promote only after real CE→Builder adapter execution evidence is added in PROMPT-04 and current PR CI passes.",
      "notes": "PROMPT-03 provides infrastructure and fail-closed mapping only; it does not implement CE→Builder adapter behavior."
    },
    {
      "rule_id": "PG-PROGRESS-001",
      "rule": "Progress events must be sanitized runtime/UI artifacts and must not affect canonical final result hashes.",
      "risk": "High",
      "status": "validator_backed",
      "target_status": "validator_backed",
      "carriers": ["src/ev4_transition/progress/events.py", "docs/RESULT_MODEL.md"],
      "validators": ["src/ev4_transition/progress/events.py::sanitize_progress_event", "src/ev4_transition/progress/events.py::canonical_result_hash_without_progress"],
      "valid_fixtures": [],
      "invalid_fixtures": [],
      "ci_steps": [".github/workflows/validate.yml / Progress tests"],
      "downstream_contracts": [],
      "downstream_rejection_fixtures": [],
      "documented_risk": "Progress messages can leak secrets or make runtime state look canonical.",
      "next_enforcement_step": "Promote only after current PR CI passes and future report UX fixtures are added in PROMPT-06.",
      "notes": "Progress tests cover token/env rejection, relative paths, and hash exclusion."
    }
  ]
}
```

## Coverage table

| Rule ID | Risk | Current status | Coverage meaning | Next enforcement step |
|---|---|---|---|---|
| `PG-BRC-001` | `High` | `fixture_tested` | Coverage references remain schema/validator/fixture checked. | Promote to `ci_enforced` only after current PR CI evidence. |
| `PG-EVIDENCE-001` | `Critical` | `fixture_tested` | Accepted result validator evidence semantics remain fixture-tested; execution record carriers added. | Add real transition execution evidence in later prompts. |
| `PG-BOUNDARY-001` | `Critical` | `fixture_tested` | Static runner boundary scanner and CI step references added. | Promote to `ci_enforced` only after current PR CI evidence. |
| `PG-VALIDATOR-001` | `Critical` | `validator_backed` | Official validator execution is centralized in runner API and fail-closed mapping is implemented. | Extend coverage fixture binding before claiming `fixture_tested`. |
| `PG-ADAPTER-001` | `Critical` | `validator_backed` | Official adapter execution API and fallback-adapter rejection are implemented. | Add real owner adapter execution in `PROMPT-04`. |
| `PG-PROGRESS-001` | `High` | `validator_backed` | Progress sanitization and canonical hash exclusion are implemented. | Promote after CI evidence and report UX fixtures. |
| `PG-DOWNSTREAM-001` | `Critical` | `fixture_tested` | False downstream enforcement claims still fail; no real downstream enforcement claimed. | `PROMPT-04/05` must add real downstream evidence before promotion. |

## Critical / High gaps

```yaml
critical:
  - PG-VALIDATOR-001, PG-ADAPTER-001, and PG-PROGRESS-001 have pytest coverage, but the machine-readable coverage ledger keeps them at validator_backed until the behavioral coverage validator supports those test fixture families.
  - PG-DOWNSTREAM-001 remains fixture_tested for false-claim prevention only; real downstream compatibility remains insufficient_evidence until PROMPT-04/05.
  - PG-STATUS-001 still has legacy valid compatibility in existing A2C/stage-bundle paths.
high:
  - PG-OUTPUT-001 still lacks full Persian RTL/LTR report-contract fixtures; PROMPT-03 only covers progress sanitization.
```

## Enforcement honesty note

`validator_backed` means a carrier and validator/API exist. It does not mean CI has passed or that downstream owner compatibility is enforced. `ci_enforced` is not claimed for `PROMPT-03` additions until GitHub Actions evidence exists for the current PR head.
