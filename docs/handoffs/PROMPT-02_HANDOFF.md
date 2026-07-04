prompt_id: PROMPT-02
branch: project-gate-prompt-02-behavioral-coverage
commits:
  initial_prompt_02_range: 04331a3da62ef6c877a87dfb9e8ef065253b1d6b..c9133136972bbbeaad3abc8430706f5ca22111b9
  inspector_followup:
    - a09d27709b6bac74b404f01c4306f0f76269fa46 fix: resolve behavioral coverage evidence references
    - 9193bdb841d025182f06ad498b973a8aa5ecc6d7 schemas: add validator evidence schema
    - 815c51bfab99d7eedf40648907041641a113c7c0 ci: allow validator evidence schema
    - 1090432281ea720fe06ccda5cd4d7ae47999dc87 fixtures: require complete validator evidence for accepted result
    - 56594bb5ab289b4f9595366f7e2980b62e4cbb4b fixtures: require complete validator evidence for output success
    - 033dcf04df9a6c277a08b71df10d3b93f3a7024c fixtures: isolate synthetic-only accepted failure
    - f18209db8f8bbf118d176d3d3d8deddfe6f9abe7 fixtures: isolate output write failure success-status case
    - 7b3c4f1ba4e27c171b7c5df5bcf218ba90d62d37 fixtures: add failed validator evidence accepted invalid fixture
    - fdda3f465e406fc38afc2c0ceed10554b60bafab fixtures: add unknown validator evidence accepted invalid fixture
    - 3057e666df9a4c2b14faf997b27aa351f6ecb482 fixtures: add incomplete validator evidence accepted invalid fixture
    - 2dfb720e4ef83b2f5916934c4f4cdaeeddc1f6cc fixtures: add unpinned validator evidence accepted invalid fixture
    - 5016328280bf60dce1a576eb5e032d2abc72d563 fixtures: add validator hash mismatch accepted invalid fixture
    - e51736fb2f97f6f7934d6e2ea4cc23afcf5ea07f fixtures: add validator stage mismatch accepted invalid fixture
    - c6effe2bf2c781344e62120e50a64383f1e2d392 fixtures: add schema registry prefix collision invalid fixture
    - be7d43fe8dc0984099e3344df5a753b2a958f301 fixtures: bind coverage fixture to exact semantic validator
    - 7ffa81b5d17f4829865031d8f9a7d97f6da7a01f tests: cover resolved coverage evidence references
    - 7797a7986165b6bb4876c30c9e43678513c425b8 tests: cover validator evidence and schema registry bypasses
    - c9c82df0f8e74774c09fe31e542d6d1dc82985ee tests: cover unreadable and invalid coverage schema CLI failures
    - de7a85ae40df18f19175cc64b02be96e3421ef8c docs: record behavioral coverage inspector fixes
    - self_reference: docs: update PROMPT-02 handoff after inspector fixes; final commit SHA is reported in final response
files_changed:
  - .github/workflows/validate.yml
  - docs/BEHAVIORAL_RULE_COVERAGE.md
  - docs/handoffs/PROMPT-02_HANDOFF.md
  - schemas/behavioral-coverage/behavioral-coverage.v1.schema.json
  - schemas/validator-evidence/validator-evidence.v1.schema.json
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
  - tests/fixtures/result_envelope/invalid/accepted_with_failed_validator_evidence.json
  - tests/fixtures/result_envelope/invalid/accepted_with_unknown_validator_evidence.json
  - tests/fixtures/result_envelope/invalid/accepted_with_malformed_validator_evidence.json
  - tests/fixtures/result_envelope/invalid/accepted_with_unpinned_validator_evidence.json
  - tests/fixtures/result_envelope/invalid/accepted_with_validator_hash_mismatch.json
  - tests/fixtures/result_envelope/invalid/accepted_with_validator_stage_mismatch.json
  - tests/fixtures/result_envelope/invalid/synthetic_only_marked_as_real_evidence.json
  - tests/fixtures/result_envelope/invalid/output_write_failed_but_success.json
  - tests/fixtures/stage_bundle/valid/project_gate_owned_schema_only.json
  - tests/fixtures/stage_bundle/invalid/copied_specialist_schema_claimed_as_project_gate_owned.json
  - tests/fixtures/stage_bundle/invalid/project_gate_schema_prefix_collision_specialist_copy.json
tests_run:
  - local isolated generated-tree check before original PR: PYTHONPATH=src python scripts/validate-behavioral-rule-coverage.py docs/BEHAVIORAL_RULE_COVERAGE.md -> exit 0
  - local isolated generated-tree check before original PR: PYTHONPATH=src python -m ev4_transition.cli coverage validate docs/BEHAVIORAL_RULE_COVERAGE.md -> exit 0
  - local isolated generated-tree check before original PR: PYTHONPATH=src pytest -q tests/behavioral_coverage -> 17 passed
  - GitHub Actions run 28718131721 on head c9133136972bbbeaad3abc8430706f5ca22111b9: success, but Inspector found uncovered negative paths
  - PR Inspector v1.4.0 break attempts reproduced PRF-001 through PRF-004 against head c9133136972bbbeaad3abc8430706f5ca22111b9
  - GitHub Actions run 28718821873 on updated head de7a85ae40df18f19175cc64b02be96e3421ef8c: in_progress at handoff update time
tests_passed:
  - Original isolated generated-tree checks before PR #18 creation
  - GitHub Actions run 28718131721 on old head c9133136972bbbeaad3abc8430706f5ca22111b9
tests_failed:
  - PRF-001: fake ci_enforced evidence references were accepted on old head c9133136972bbbeaad3abc8430706f5ca22111b9
  - PRF-002: failed validator evidence was accepted on old head c9133136972bbbeaad3abc8430706f5ca22111b9
  - PRF-003: schema ownership prefix collision was accepted on old head c9133136972bbbeaad3abc8430706f5ca22111b9
  - PRF-004: unreadable/invalid schema path could bypass structured CLI exit behavior on old head c9133136972bbbeaad3abc8430706f5ca22111b9
tests_not_run:
  - local full repository python -m pip install -e '.[dev]'
  - local full repository pytest after Inspector fixes
  - local full repository ev4-transition coverage validate docs/BEHAVIORAL_RULE_COVERAGE.md after Inspector fixes
  - local npm run status
  - local npm run validate
  - final GitHub Actions result on updated head after Inspector fixes
coverage_rules_advanced:
  - PG-BRC-001: now resolves repository-relative carriers, validators, fixtures, and CI step references and emits deterministic evidence_records.
  - PG-EVIDENCE-001: accepted result now requires validator-evidence.v1 records with status=passed, pinning, stage match, hash match, and result digest.
  - PG-SYNTH-001: synthetic_only_marked_as_real_evidence fixture now isolates synthetic guard with otherwise complete validator evidence.
  - PG-SCHEMA-001: Project Gate-owned schema check moved from prefix matching to exact schema registry; prefix collision fixture added.
  - PG-OUTPUT-001: output write failure with success status remains fixture-tested with complete validator evidence shape.
  - PG-BOUNDARY-001: schema ownership anti-drift now covers explicit copied schema and prefix-collision cases.
  - PG-DOWNSTREAM-001: false downstream_contract_enforced claim prevention remains fixture-tested; downstream_contract_enforced is still not claimed.
coverage_rules_still_gap:
  - PG-ADAPTER-001: runner/official adapter boundary enforcement is deferred to PROMPT-03.
  - PG-DOWNSTREAM-001: real downstream contract and rejection evidence for CE-to-Builder/Builder-to-Responsive remain insufficient_evidence.
  - PG-PROGRESS-001: handoff/report no-false-progress linter not implemented.
  - PG-OUTPUT-001: full Persian RTL/LTR UX report fixtures deferred to PROMPT-06.
  - PG-STATUS-001: legacy valid compatibility still exists in current A2C/stage-bundle paths.
new_diagnostics:
  - PG_BRC_CARRIER_REFERENCE_INVALID
  - PG_BRC_VALIDATOR_REFERENCE_INVALID
  - PG_BRC_VALIDATOR_SYMBOL_NOT_FOUND
  - PG_BRC_FIXTURE_REFERENCE_INVALID
  - PG_BRC_FIXTURE_NOT_BOUND_TO_VALIDATOR
  - PG_BRC_CI_STEP_REFERENCE_INVALID
  - PG_BRC_CI_JOB_REFERENCE_INVALID
  - PG_BRC_DOWNSTREAM_CONTRACT_REFERENCE_INVALID
  - PG_BRC_DOWNSTREAM_REJECTION_FIXTURE_REFERENCE_INVALID
  - PG_EVIDENCE_VALIDATOR_EVIDENCE_MALFORMED
  - PG_EVIDENCE_VALIDATOR_STATUS_NOT_PASSED
  - PG_EVIDENCE_VALIDATOR_UNPINNED
  - PG_EVIDENCE_VALIDATOR_STAGE_MISMATCH
  - PG_EVIDENCE_VALIDATOR_SCOPE_MISMATCH
  - PG_EVIDENCE_VALIDATOR_HASH_MISMATCH
  - PG_EVIDENCE_VALIDATOR_RESULT_DIGEST_INVALID
  - PG_SCHEMA_REGISTRY_PATH_MISSING
new_or_changed_cli:
  - ev4-transition coverage validate now returns exit 2 for unreadable or invalid schema paths via CoverageSourceError.
  - coverage reports now include deterministic evidence_records for resolved carriers, validators, fixtures, and CI steps.
new_or_changed_ci:
  - .github/workflows/validate.yml schema allowlist includes schemas/validator-evidence/validator-evidence.v1.schema.json.
important_design_decisions:
  - Evidence reference resolution is repository-relative and rejects external, absolute, missing, and traversal-like references.
  - Validator references use file or file::symbol form; unresolved module strings are rejected.
  - Workflow step evidence is resolved from the actual YAML step name.
  - Fixture-to-validator binding is deterministic by validator family and fixture directory.
  - Exact Project Gate schema registry replaced prefix matching for Project Gate-owned schema claims.
  - validator-evidence.v1 is Project Gate-owned evidence metadata; it is not a copied specialist schema.
  - ci_enforced was not promoted after the Inspector fix because updated-head CI was still pending.
web_sources_used: []
next_allowed_prompt: PROMPT-03 after PR #18 Inspector follow-up is green and reviewed
blocking_issues:
  - updated-head GitHub Actions run 28718821873 is still in_progress at handoff update time
  - PR #18 should not be merged until updated-head CI succeeds and the Inspector blockers are rechecked
remaining_insufficient_evidence:
  - final GitHub Actions result on updated head after Inspector fixes
  - PR Inspector recheck after updated-head CI
  - real CE-to-Builder downstream rejection evidence
  - real Builder-to-Responsive downstream rejection evidence
  - official Builder adapter execution evidence
  - official Responsive validation evidence
  - final evidence gate policy, fixtures, and CI evidence
