prompt_id: PROMPT-02
branch: project-gate-prompt-02-behavioral-coverage
commits:
  - 04331a3da62ef6c877a87dfb9e8ef065253b1d6b schemas: add behavioral coverage schema
  - 6b946c0de2d3f84c26c29ed58d9e68e5ccf87b52 code: add behavioral coverage package exports
  - 643d3493c1ec8d2dddcba4d5a48029bb54c02527 code: add behavioral coverage validator
  - 478432f2e30a4b7bb4ec50f9ab3be829b2146f56 tools: add behavioral coverage validator script
  - dafd4bc84b45bbe4b113731dea6420843c90af59 cli: add behavioral coverage inspect and validate commands
  - dbfcd5319ed5984f827d6198b63784f88fc79cbb fixtures: add valid behavioral coverage fixture
  - 564954fdda73f2ca3a937f3b35ff10c816f09f6f fixtures: add critical prose-only invalid coverage fixture
  - 3bb5d93fe1b6ecb34ced24394fedc580310e0c37 fixtures: add critical schema-backed no-followup invalid fixture
  - 47feb4e795bd1d0bf30af3210a34b56f1005a175 fixtures: add downstream enforcement missing-contract invalid fixture
  - f747bc93e95f6c7769bcd03b3f5c1bfe96bbafbb fixtures: add valid accepted result envelope evidence shape
  - 6855ea41affcbf109b43649b817dbc3936cabf74 fixtures: add labeled synthetic result envelope fixture
  - 8839f7c619c55ab8bb8d4d9e31f369e7b54e66fa fixtures: add output write success result fixture
  - 879598a6601d99a29eb55a574e4e0d881372c766 fixtures: add accepted missing validator evidence invalid fixture
  - fab3b6391d06641d1b12807836f383ccf21b316d fixtures: add synthetic-only accepted invalid fixture
  - f8ca10a2a66ac00e6fb0f5122a9474a65b76a1f7 fixtures: add output-write failed success-status invalid fixture
  - 15386bdba56555b1c9c6eaaa3670c5b52613f039 fixtures: add Project Gate-owned stage bundle fixture
  - 8f85229fb50b420b39235478d251f438a30b158f fixtures: add copied specialist schema ownership invalid fixture
  - 4ae515ce2262f881feb67520be8856971a6edc76 tests: add behavioral coverage validator tests
  - 0430f08691564f80b2667f1f3735c79428aa3b3b tests: add behavioral semantic fixture tests
  - 2621e96037effc93f9ae132d2ff2655f7052dd1d tests: add behavioral coverage CLI tests
  - ffae252fd7c83a7dee642810168427bc2d8644d7 ci: run behavioral coverage validation and fixtures
  - d9169cb56a7698525a0dff77f5d744100b22f42c docs: update behavioral rule coverage with validated ledger
  - self_reference: docs: create PROMPT-02 handoff; final commit SHA is reported in the final response
files_changed:
  - .github/workflows/validate.yml
  - docs/BEHAVIORAL_RULE_COVERAGE.md
  - docs/handoffs/PROMPT-02_HANDOFF.md
  - schemas/behavioral-coverage/behavioral-coverage.v1.schema.json
  - scripts/validate-behavioral-rule-coverage.py
  - src/ev4_transition/behavioral_coverage/__init__.py
  - src/ev4_transition/behavioral_coverage/validator.py
  - src/ev4_transition/cli.py
  - tests/behavioral_coverage/test_behavioral_coverage_validator.py
  - tests/behavioral_coverage/test_behavioral_semantic_fixtures.py
  - tests/behavioral_coverage/test_coverage_cli.py
  - tests/fixtures/behavioral_coverage/valid/critical_rule_fixture_tested.json
  - tests/fixtures/behavioral_coverage/invalid/critical_rule_prose_only.json
  - tests/fixtures/behavioral_coverage/invalid/critical_rule_schema_backed_without_followup.json
  - tests/fixtures/behavioral_coverage/invalid/downstream_contract_missing_for_claimed_enforcement.json
  - tests/fixtures/result_envelope/valid/accepted_with_all_required_evidence_shape.json
  - tests/fixtures/result_envelope/valid/synthetic_fixture_labeled.json
  - tests/fixtures/result_envelope/valid/output_write_success.json
  - tests/fixtures/result_envelope/invalid/accepted_missing_validator_evidence.json
  - tests/fixtures/result_envelope/invalid/synthetic_only_marked_as_real_evidence.json
  - tests/fixtures/result_envelope/invalid/output_write_failed_but_success.json
  - tests/fixtures/stage_bundle/valid/project_gate_owned_schema_only.json
  - tests/fixtures/stage_bundle/invalid/copied_specialist_schema_claimed_as_project_gate_owned.json
tests_run:
  - local isolated generated-tree check: PYTHONPATH=src python scripts/validate-behavioral-rule-coverage.py docs/BEHAVIORAL_RULE_COVERAGE.md -> exit 0
  - local isolated generated-tree check: PYTHONPATH=src python -m ev4_transition.cli coverage validate docs/BEHAVIORAL_RULE_COVERAGE.md -> exit 0
  - local isolated generated-tree check: PYTHONPATH=src pytest -q tests/behavioral_coverage -> 17 passed
  - GitHub Actions workflow configured but final branch CI result is pending until PR/push workflow completes
tests_passed:
  - isolated generated-tree behavioral coverage script check
  - isolated generated-tree behavioral coverage CLI check
  - isolated generated-tree behavioral coverage pytest suite: 17 passed
tests_failed: []
tests_not_run:
  - local full repository python -m pip install -e '.[dev]'
  - local full repository pytest
  - local full repository ev4-transition coverage validate docs/BEHAVIORAL_RULE_COVERAGE.md
  - local full repository python scripts/validate-behavioral-rule-coverage.py docs/BEHAVIORAL_RULE_COVERAGE.md
  - local npm run status
  - local npm run validate
  - final GitHub Actions result on branch/PR head
coverage_rules_advanced:
  - PG-BRC-001: behavioral coverage schema, validator, fixtures, CLI, and CI step added.
  - PG-EVIDENCE-001: accepted_missing_validator_evidence invalid fixture added and semantic guard added.
  - PG-SYNTH-001: synthetic_only_marked_as_real_evidence invalid fixture added and semantic guard added.
  - PG-SCHEMA-001: Project Gate-owned schema copy anti-drift fixture added.
  - PG-OUTPUT-001: output_write_failed_but_success invalid fixture added and semantic guard added.
  - PG-BOUNDARY-001: advanced at anti-drift/schema-ownership coverage level only.
  - PG-DOWNSTREAM-001: advanced as false-claim visibility/gap tracking; downstream_contract_enforced still not claimed.
coverage_rules_still_gap:
  - PG-ADAPTER-001: runner/official adapter boundary enforcement is deferred to PROMPT-03.
  - PG-DOWNSTREAM-001: real downstream contract and rejection evidence for CE-to-Builder/Builder-to-Responsive remain insufficient_evidence.
  - PG-PROGRESS-001: handoff/report no-false-progress linter not implemented.
  - PG-OUTPUT-001: full Persian RTL/LTR UX report fixtures deferred to PROMPT-06.
  - PG-STATUS-001: legacy valid compatibility still exists in current A2C/stage-bundle paths.
new_diagnostics:
  - PG_BRC_SCHEMA_INVALID
  - PG_BRC_RULE_NOT_OBJECT
  - PG_BRC_RULE_ID_MUST_BE_STABLE
  - PG_BRC_RULE_ID_MUST_NOT_BE_REUSED
  - PG_BRC_RISK_MUST_BE_KNOWN
  - PG_BRC_STATUS_MUST_BE_KNOWN
  - PG_BRC_CRITICAL_MUST_NOT_BE_PROSE_ONLY
  - PG_BRC_CRITICAL_SCHEMA_BACKED_REQUIRES_FOLLOWUP
  - PG_BRC_HIGH_PROSE_ONLY_REQUIRES_DOCUMENTED_RISK
  - PG_BRC_INVALID_FIXTURE_REQUIRED_FOR_CRITICAL_TARGET
  - PG_BRC_CI_STEP_REQUIRED_BEFORE_CI_ENFORCED
  - PG_BRC_DOWNSTREAM_CONTRACT_REQUIRED_BEFORE_DOWNSTREAM_ENFORCED
  - PG_BRC_NO_CLAIMED_ENFORCEMENT_WITHOUT_CARRIER
  - PG_BRC_NO_CLAIMED_ENFORCEMENT_WITHOUT_VALIDATOR
  - PG_BRC_NO_CLAIMED_ENFORCEMENT_WITHOUT_FIXTURE
  - PG_BRC_NO_CLAIMED_DOWNSTREAM_ENFORCEMENT_WITHOUT_REJECTION_FIXTURE
  - PG_BRC_SOURCE_UNPARSEABLE
  - PG_EVIDENCE_ACCEPTED_MISSING_VALIDATOR_EVIDENCE
  - PG_SYNTH_SYNTHETIC_ONLY_MARKED_ACCEPTED
  - PG_OUTPUT_WRITE_FAILED_BUT_SUCCESS_STATUS
  - PG_BOUNDARY_COPIED_SPECIALIST_SCHEMA_CLAIMED_AS_PROJECT_GATE_OWNED
new_or_changed_cli:
  - ev4-transition coverage inspect
  - ev4-transition coverage validate
  - coverage validate exit 0 when thresholds met
  - coverage validate exit 1 when thresholds fail
  - coverage validate exit 2 when source missing or unparseable
new_or_changed_ci:
  - .github/workflows/validate.yml schema allowlist includes schemas/behavioral-coverage/behavioral-coverage.v1.schema.json
  - .github/workflows/validate.yml runs python scripts/validate-behavioral-rule-coverage.py docs/BEHAVIORAL_RULE_COVERAGE.md
  - .github/workflows/validate.yml runs ev4-transition coverage validate docs/BEHAVIORAL_RULE_COVERAGE.md
  - .github/workflows/validate.yml runs pytest tests/behavioral_coverage
important_design_decisions:
  - Behavioral coverage validation is separate from normal transition validation in Phase 1 and does not block ordinary user transition validation unless explicitly run.
  - The coverage validator accepts JSON fixtures and extracts a behavioral-coverage.v1 JSON code block from docs/BEHAVIORAL_RULE_COVERAGE.md.
  - Result/stage semantic guards are behavioral anti-false-claim checks; they do not add CE constructability logic, Builder runtime logic, or Responsive repair logic.
  - PG-DOWNSTREAM-001 is not marked downstream_contract_enforced; it is fixture_tested only for false downstream enforcement claim prevention.
  - No specialist schema was copied into schemas/; only Project Gate behavioral coverage schema was added.
web_sources_used: []
next_allowed_prompt: PROMPT-03
blocking_issues:
  - final GitHub Actions result on the Prompt 02 branch/PR is not yet recorded in this handoff
  - local full repository tests were not run in a repository checkout by this assistant
remaining_insufficient_evidence:
  - final GitHub Actions result on project-gate-prompt-02-behavioral-coverage
  - real CE-to-Builder downstream rejection evidence
  - real Builder-to-Responsive downstream rejection evidence
  - official Builder adapter execution evidence
  - official Responsive validation evidence
  - final evidence gate policy, fixtures, and CI evidence
