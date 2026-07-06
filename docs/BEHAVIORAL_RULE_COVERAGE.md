# Behavioral Rule Coverage

Status: `PROMPT-07` closure audit confirms the coverage ledger is conservative. No rule is promoted to `ci_enforced` or `downstream_contract_enforced` in this cleanup. `PROMPT-06` report rules remain `validator_backed` until dedicated behavioral fixtures are added and bound through the behavioral coverage validator.

This ledger intentionally separates implementation and CI evidence from behavioral coverage status. A rule can have CI coverage and still remain below `ci_enforced` when the behavioral carrier/fixture/downstream contract required for that status is not present.

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

```json behavioral-coverage.v1
{
  "schema_version": "behavioral-coverage.v1",
  "generated_by": "PROMPT-07 closure audit and stale prose cleanup",
  "rules": [
    {
      "rule_id": "PG-BRC-001",
      "rule": "Behavioral coverage must be tracked honestly and must not overclaim enforcement status.",
      "risk": "High",
      "status": "fixture_tested",
      "target_status": "fixture_tested",
      "carriers": [
        "docs/BEHAVIORAL_RULE_COVERAGE.md",
        "schemas/behavioral-coverage/behavioral-coverage.v1.schema.json",
        "docs/STANDARDS_TRACEABILITY.md"
      ],
      "validators": [
        "src/ev4_transition/behavioral_coverage/validator.py::validate_coverage_document",
        "scripts/validate-behavioral-rule-coverage.py"
      ],
      "valid_fixtures": [
        "tests/fixtures/behavioral_coverage/valid/critical_rule_fixture_tested.json"
      ],
      "invalid_fixtures": [
        "tests/fixtures/behavioral_coverage/invalid/critical_rule_prose_only.json",
        "tests/fixtures/behavioral_coverage/invalid/critical_rule_schema_backed_without_followup.json"
      ],
      "ci_steps": [
        ".github/workflows/validate.yml / Behavioral coverage validator",
        ".github/workflows/prompt-06.yml / Behavioral coverage validator"
      ],
      "downstream_contracts": [],
      "downstream_rejection_fixtures": [],
      "documented_risk": "False behavioral coverage can make weak rules look enforced.",
      "next_enforcement_step": "Keep future status promotions evidence-backed and fixture-bound.",
      "notes": "PROMPT-07 keeps this at fixture_tested and does not inflate status."
    },
    {
      "rule_id": "PG-BOUNDARY-001",
      "rule": "Project Gate must remain a checkpoint and must not copy specialist schemas or implement specialist domain logic.",
      "risk": "Critical",
      "status": "validator_backed",
      "target_status": "validator_backed",
      "carriers": [
        "docs/ARCHITECTURE.md",
        "docs/ROLE_BOUNDARY_MAP.md",
        "src/ev4_transition/behavioral_coverage/validator.py"
      ],
      "validators": [
        "src/ev4_transition/behavioral_coverage/validator.py::validate_stage_bundle_semantics",
        "scripts/check-runner-boundary.py"
      ],
      "valid_fixtures": [],
      "invalid_fixtures": [],
      "ci_steps": [
        ".github/workflows/validate.yml / Verify no specialist canonical schema files exist",
        ".github/workflows/validate.yml / Static runner-boundary scanner"
      ],
      "downstream_contracts": [],
      "downstream_rejection_fixtures": [],
      "documented_risk": "Boundary drift would turn Project Gate into a fifth specialist engine.",
      "next_enforcement_step": "Add broader boundary fixtures before any fixture_tested promotion.",
      "notes": "The closure audit fixed stale prose but did not add specialist logic."
    },
    {
      "rule_id": "PG-SCHEMA-001",
      "rule": "Project Gate-owned schema claims must match the exact Project Gate schema registry and must not mask copied specialist schemas.",
      "risk": "Critical",
      "status": "validator_backed",
      "target_status": "validator_backed",
      "carriers": [
        "schemas/README.md",
        "src/ev4_transition/behavioral_coverage/validator.py",
        "docs/RESULT_MODEL.md"
      ],
      "validators": [
        "src/ev4_transition/behavioral_coverage/validator.py::validate_stage_bundle_semantics"
      ],
      "valid_fixtures": [],
      "invalid_fixtures": [],
      "ci_steps": [
        ".github/workflows/validate.yml / Verify no specialist canonical schema files exist",
        ".github/workflows/validate.yml / Behavioral fixture validation"
      ],
      "downstream_contracts": [],
      "downstream_rejection_fixtures": [],
      "documented_risk": "Schema ownership drift can create competing canonical contracts.",
      "next_enforcement_step": "Keep exact registry checks and add transition-specific ownership fixtures as needed.",
      "notes": "No downstream specialist schema is claimed as Project Gate-owned."
    },
    {
      "rule_id": "PG-EVIDENCE-001",
      "rule": "Accepted results require explicit evidence; synthetic, CI-only, or unresolved evidence must not unlock acceptance.",
      "risk": "Critical",
      "status": "validator_backed",
      "target_status": "validator_backed",
      "carriers": [
        "schemas/transition-result/transition-result.v1.schema.json",
        "docs/RESULT_MODEL.md",
        "docs/STATUS_DECISION_MATRIX.md"
      ],
      "validators": [
        "src/ev4_transition/behavioral_coverage/validator.py::validate_transition_result_semantics"
      ],
      "valid_fixtures": [],
      "invalid_fixtures": [],
      "ci_steps": [
        ".github/workflows/validate.yml / Prompt 01 unit tests",
        ".github/workflows/validate.yml / Behavioral fixture validation"
      ],
      "downstream_contracts": [],
      "downstream_rejection_fixtures": [],
      "documented_risk": "False acceptance can move an invalid EV4 handoff to the next specialist.",
      "next_enforcement_step": "Bind more transition-specific accepted-evidence failure fixtures before status promotion.",
      "notes": "Real non-synthetic Builder/Responsive/final evidence remains insufficient_evidence."
    },
    {
      "rule_id": "PG-SYNTH-001",
      "rule": "Synthetic fixtures must never be treated as real EV4 evidence.",
      "risk": "Critical",
      "status": "validator_backed",
      "target_status": "validator_backed",
      "carriers": [
        "docs/STATUS_DECISION_MATRIX.md",
        "src/ev4_transition/behavioral_coverage/validator.py"
      ],
      "validators": [
        "src/ev4_transition/behavioral_coverage/validator.py::validate_transition_result_semantics"
      ],
      "valid_fixtures": [],
      "invalid_fixtures": [],
      "ci_steps": [
        ".github/workflows/validate.yml / Behavioral fixture validation",
        ".github/workflows/validate.yml / Prompt-05 transition tests"
      ],
      "downstream_contracts": [],
      "downstream_rejection_fixtures": [],
      "documented_risk": "Synthetic evidence can create unsupported readiness claims.",
      "next_enforcement_step": "Add real-vs-synthetic transition fixture families before promotion.",
      "notes": "Prompt-04/05 owner fixtures prove integration, not real handoff evidence."
    },
    {
      "rule_id": "PG-ADAPTER-001",
      "rule": "Official adapters must execute only through runner infrastructure; fallback adapters are forbidden and missing/timeouts fail closed.",
      "risk": "Critical",
      "status": "validator_backed",
      "target_status": "validator_backed",
      "carriers": [
        "src/ev4_transition/runners/official_tools.py",
        "src/ev4_transition/runners/subprocess_runner.py",
        "src/ev4_transition/runners/failure_mapping.py"
      ],
      "validators": [
        "src/ev4_transition/runners/official_tools.py",
        "src/ev4_transition/runners/subprocess_runner.py"
      ],
      "valid_fixtures": [],
      "invalid_fixtures": [],
      "ci_steps": [
        ".github/workflows/validate.yml / Runner tests",
        ".github/workflows/validate.yml / CE-to-Builder live owner tool smoke"
      ],
      "downstream_contracts": [],
      "downstream_rejection_fixtures": [],
      "documented_risk": "Fallback adapter behavior can invent a next-stage package without owner evidence.",
      "next_enforcement_step": "Add runner behavioral fixtures for adapter failure modes before promotion.",
      "notes": "No fallback adapter is authorized."
    },
    {
      "rule_id": "PG-VALIDATOR-001",
      "rule": "Official validators must execute only through Project Gate runner infrastructure and fail closed when missing, timed out, unparseable, or failed.",
      "risk": "Critical",
      "status": "validator_backed",
      "target_status": "validator_backed",
      "carriers": [
        "src/ev4_transition/runners/official_tools.py",
        "src/ev4_transition/runners/responsive_tools.py",
        "src/ev4_transition/runners/subprocess_runner.py",
        "src/ev4_transition/runners/failure_mapping.py"
      ],
      "validators": [
        "src/ev4_transition/runners/official_tools.py",
        "src/ev4_transition/runners/responsive_tools.py",
        "src/ev4_transition/runners/subprocess_runner.py"
      ],
      "valid_fixtures": [],
      "invalid_fixtures": [],
      "ci_steps": [
        ".github/workflows/validate.yml / Runner tests",
        ".github/workflows/prompt-05.yml / Run pinned official Responsive validators"
      ],
      "downstream_contracts": [],
      "downstream_rejection_fixtures": [],
      "documented_risk": "Missing or failed validator execution must never be treated as acceptance.",
      "next_enforcement_step": "Add runner behavioral fixtures for validator failure modes before promotion.",
      "notes": "Owner validator execution is wired, but real EV4 evidence remains unavailable."
    },
    {
      "rule_id": "PG-HASH-001",
      "rule": "Canonical JSON and file-byte SHA-256 behavior must be deterministic and must not silently normalize Unicode or reorder arrays.",
      "risk": "Critical",
      "status": "validator_backed",
      "target_status": "validator_backed",
      "carriers": [
        "src/ev4_transition/core/canonical_json.py",
        "src/ev4_transition/canonical_json.py",
        "docs/ARCHITECTURE.md"
      ],
      "validators": [
        "tests/test_canonical_json.py"
      ],
      "valid_fixtures": [],
      "invalid_fixtures": [],
      "ci_steps": [
        ".github/workflows/validate.yml / CLI and bundle tests"
      ],
      "downstream_contracts": [],
      "downstream_rejection_fixtures": [],
      "documented_risk": "Non-deterministic hashes would make transition evidence non-reproducible.",
      "next_enforcement_step": "Keep canonical hash tests in CI and add transition-specific hash fixtures when needed.",
      "notes": "No hidden Unicode normalization is claimed or allowed."
    },
    {
      "rule_id": "PG-LOCK-001",
      "rule": "Lock manifests must pin exact repository, commit, path, identity marker, and file-byte SHA-256 and must fail closed on mismatch.",
      "risk": "Critical",
      "status": "validator_backed",
      "target_status": "validator_backed",
      "carriers": [
        "docs/LOCK_MANIFEST_POLICY.md",
        "contracts/locks/ce-to-builder-transition.v1.lock.json",
        "contracts/locks/builder-to-responsive-transition.v1.lock.json",
        "contracts/locks/final-gate.v1.lock.json"
      ],
      "validators": [
        "scripts/verify-ce-to-builder-lock.py",
        "scripts/compute-builder-to-responsive-lock.py",
        "scripts/compute-final-gate-lock.py"
      ],
      "valid_fixtures": [],
      "invalid_fixtures": [],
      "ci_steps": [
        ".github/workflows/validate.yml / CE-to-Builder lock verification",
        ".github/workflows/prompt-05.yml / Recompute and compare immutable locks"
      ],
      "downstream_contracts": [],
      "downstream_rejection_fixtures": [],
      "documented_risk": "Mutable refs or stale hashes can authorize the wrong owner boundary.",
      "next_enforcement_step": "Add dedicated lock-behavior fixtures before promotion.",
      "notes": "Lock behavior is implementation/CI-backed but not promoted to ci_enforced in this ledger."
    },
    {
      "rule_id": "PG-STATUS-001",
      "rule": "Status must use explicit accepted/repair_needed/insufficient_evidence/invalid semantics and Persian reports must use icon, text, and semantic tone rather than color alone.",
      "risk": "High",
      "status": "validator_backed",
      "target_status": "validator_backed",
      "carriers": [
        "docs/STATUS_DECISION_MATRIX.md",
        "src/ev4_transition/presentation/status_mapping.py",
        "src/ev4_transition/reports/renderers.py",
        "docs/REPORT_UX_CONTRACT.md"
      ],
      "validators": [
        "tests/ux_acceptance/test_report_status_ux.py"
      ],
      "valid_fixtures": [],
      "invalid_fixtures": [],
      "ci_steps": [
        ".github/workflows/prompt-06.yml / Report UX acceptance tests"
      ],
      "downstream_contracts": [],
      "downstream_rejection_fixtures": [],
      "documented_risk": "Color-only or ambiguous status can hide invalid or insufficient-evidence states.",
      "next_enforcement_step": "Add behavioral fixtures before any fixture_tested promotion.",
      "notes": "Legacy valid remains documented compatibility for older validation paths."
    },
    {
      "rule_id": "PG-OUTPUT-001",
      "rule": "Output writing must not report success or an available download unless the final path exists after an atomic write.",
      "risk": "High",
      "status": "validator_backed",
      "target_status": "validator_backed",
      "carriers": [
        "src/ev4_transition/io/atomic_writer.py",
        "docs/REPORT_UX_CONTRACT.md"
      ],
      "validators": [
        "tests/reporting/test_output_writer.py"
      ],
      "valid_fixtures": [],
      "invalid_fixtures": [],
      "ci_steps": [
        ".github/workflows/prompt-06.yml / Atomic writer tests",
        ".github/workflows/prompt-06.yml / Reporting tests"
      ],
      "downstream_contracts": [],
      "downstream_rejection_fixtures": [],
      "documented_risk": "A failed write displayed as success could lead the user to trust a missing or partial report.",
      "next_enforcement_step": "Add failure-mode behavioral fixtures before fixture_tested promotion.",
      "notes": "Atomic writer requires final path existence before success/download availability."
    },
    {
      "rule_id": "PG-UNICODE-001",
      "rule": "Persian reports must be RTL while technical identifiers stay LTR, isolated, monospace, and copyable.",
      "risk": "High",
      "status": "validator_backed",
      "target_status": "validator_backed",
      "carriers": [
        "src/ev4_transition/presentation/bidi.py",
        "src/ev4_transition/reports/renderers.py",
        "docs/REPORT_UX_CONTRACT.md"
      ],
      "validators": [
        "tests/typography_acceptance/test_persian_bidi_typography.py"
      ],
      "valid_fixtures": [],
      "invalid_fixtures": [],
      "ci_steps": [
        ".github/workflows/prompt-06.yml / Typography acceptance tests"
      ],
      "downstream_contracts": [],
      "downstream_rejection_fixtures": [],
      "documented_risk": "Mixed RTL/LTR output can corrupt copy-paste of paths, hashes, schema IDs, and diagnostic codes.",
      "next_enforcement_step": "Add representative Persian/LTR report fixtures before fixture_tested promotion.",
      "notes": "PROMPT-06 adds bdi/code rendering for Markdown/HTML and Unicode isolates for plain text."
    },
    {
      "rule_id": "PG-PROGRESS-001",
      "rule": "Progress events may be shown during long-running work but must not affect the canonical final result hash or leak sensitive runtime data.",
      "risk": "Medium",
      "status": "validator_backed",
      "target_status": "validator_backed",
      "carriers": [
        "src/ev4_transition/progress/events.py",
        "src/ev4_transition/reports/renderers.py",
        "docs/REPORT_UX_CONTRACT.md"
      ],
      "validators": [
        "tests/progress/test_progress_sanitization.py",
        "tests/reporting/test_report_rendering.py"
      ],
      "valid_fixtures": [],
      "invalid_fixtures": [],
      "ci_steps": [
        ".github/workflows/validate.yml / Progress tests",
        ".github/workflows/prompt-06.yml / Reporting tests"
      ],
      "downstream_contracts": [],
      "downstream_rejection_fixtures": [],
      "documented_risk": "UI progress state inside a final hash can make deterministic results unstable.",
      "next_enforcement_step": "Add progress-event fixtures before fixture_tested promotion.",
      "notes": "The report-only hash excludes progress event keys without mutating the source result."
    },
    {
      "rule_id": "PG-DOWNSTREAM-001",
      "rule": "Downstream rejection evidence is required before claiming downstream contract enforcement.",
      "risk": "Critical",
      "status": "fixture_tested",
      "target_status": "fixture_tested",
      "carriers": [
        "docs/BEHAVIORAL_RULE_COVERAGE.md",
        "src/ev4_transition/behavioral_coverage/validator.py"
      ],
      "validators": [
        "src/ev4_transition/behavioral_coverage/validator.py::validate_coverage_document"
      ],
      "valid_fixtures": [
        "tests/fixtures/behavioral_coverage/valid/critical_rule_fixture_tested.json"
      ],
      "invalid_fixtures": [
        "tests/fixtures/behavioral_coverage/invalid/downstream_contract_missing_for_claimed_enforcement.json"
      ],
      "ci_steps": [
        ".github/workflows/validate.yml / Behavioral coverage validator"
      ],
      "downstream_contracts": [],
      "downstream_rejection_fixtures": [],
      "documented_risk": "Future transitions must not claim downstream_contract_enforced without owner rejection evidence.",
      "next_enforcement_step": "Do not mark downstream_contract_enforced until owner rejection fixtures are pinned and proven.",
      "notes": "PROMPT-07 confirms no downstream_contract_enforced status is claimed."
    }
  ]
}
```

## PROMPT-07 closure audit notes

- No Critical rule is left as `prose_only` or shallow `schema_backed` in this ledger.
- No rule is marked `downstream_contract_enforced`.
- `PG-DOWNSTREAM-001` is only `fixture_tested` for preventing false downstream-enforcement claims; it is not real downstream rejection evidence.
- `PG-STATUS-001`, `PG-OUTPUT-001`, `PG-PROGRESS-001`, and `PG-UNICODE-001` remain `validator_backed` because their dedicated behavioral fixture families are not yet bound through the behavioral coverage validator.
- Transition decision logic, fail-closed status behavior, and `insufficient_evidence` semantics are unchanged.

## Prompt 0 Common Contract Foundation Coverage

| rule_id | concept | risk | prose_source | schema_carrier | validator_rule | valid_fixture | invalid_fixture | CI_step | downstream_contract | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PG-P00-001 | Stage Evidence Bundle remains canonical for single-stage evidence | competing envelope | AGENTS.md Hard Boundaries | `schemas/stage-bundle/stage-bundle.v1.schema.json` | strict `$ref` from Producer Gate Export | `producer_gate_export/valid/cases.json` | `competing_single_stage_envelope_identity` | `pytest tests/unit/test_prompt00_producer_gate_export.py` | Producer adoption pending | fixture_tested |
| PG-P00-002 | No competing single-stage envelope | authority drift | ADR-0002 | `contracts/common/producer-gate-export.v1.schema.json` | `PG_EXPORT_SCHEMA_INVALID` | `complete` | `competing_single_stage_envelope_identity` | `pytest tests/unit/test_prompt00_producer_gate_export.py` | not downstream_contract_enforced | fixture_tested |
| PG-P00-003 | Run-level contract composes existing Stage Bundle | schema duplication | ADR-0002 | `final_stage_bundle` `$ref` | schema reference test | `complete` | schema reference assertion | `pytest tests/unit/test_prompt00_producer_gate_export.py` | Producer-owned payloads remain Producer-owned | schema_backed |
| PG-P00-004 | Legacy pinned path remains available | transition regression | AGENTS.md | existing lock manifests | unchanged existing tests | existing transition fixtures | existing transition tests | `pytest` | existing pinned-owner-file path | ci_enforced |
| PG-P00-005 | Silent fallback forbidden | hidden acquisition downgrade | Common vendoring docs | `acquisition_mode.silent_fallback_allowed` | `PG_EXPORT_SILENT_FALLBACK_FORBIDDEN` | `complete` | `silent_fallback_allowed` | `pytest tests/unit/test_prompt00_producer_gate_export.py` | not downstream_contract_enforced | fixture_tested |
| PG-P00-006 | Canonical common contract has one owner | owner drift | Common vendoring docs | `common-contract-lock.v1` | `PG_COMMON_LOCK_OWNER_DRIFT` | `exact-lock` | `contract_owner_drift` | `pytest tests/unit/test_prompt00_common_contract_lock.py` | not downstream_contract_enforced | fixture_tested |
| PG-P00-007 | Vendored copies byte-identical to immutable pin | semantic mismatch hidden | Common vendoring docs | `common-contract-lock.v1` | `PG_COMMON_CONTRACT_BYTE_MISMATCH` | `exact-lock` | `byte_mismatch_semantically_equal` | `pytest tests/unit/test_prompt00_common_contract_lock.py` | Producer adoption pending | fixture_tested |
| PG-P00-008 | Moving branch refs forbidden in locks | non-reproducible verification | Common vendoring docs | `canonical.commit_sha` | `PG_COMMON_LOCK_MOVING_REF_FORBIDDEN` | `exact-lock` | `canonical_ref_main` | `pytest tests/unit/test_prompt00_common_contract_lock.py` | not downstream_contract_enforced | fixture_tested |
| PG-P00-009 | Producer adoption not claimed from Project Gate-only tests | overclaim | AGENTS.md Evidence States | status docs | status truth checks | active status | N/A | `python scripts/check-capability-truth.py` | Producer CI pending | schema_backed |
| PG-P00-010 | Downstream enforcement not claimed before Producer CI adoption | overclaim | AGENTS.md Pull Requests | status docs | status truth checks | active status | N/A | `python scripts/check-capability-truth.py` | not downstream_contract_enforced | schema_backed |
| PG-P00-011 | User summary cannot replace machine artifact | loss of evidence | UX boundary | `producer-gate-export.v1` | required machine fields | `complete` | `missing_pipeline_id` | `pytest tests/unit/test_prompt00_producer_gate_export.py` | Producer adoption pending | fixture_tested |
| PG-P00-012 | Legacy retirement requires separate ADR and PR | accidental removal | AGENTS.md Hard Boundaries | docs only | existing path preserved | existing tests | N/A | `pytest` | legacy path retained | ci_enforced |
