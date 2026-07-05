prompt_id: PROMPT-04
branch: project-gate-prompt-04-ce-to-builder
pull_request: 20
base_branch: main
base_sha: 10e665cdec74ba5508042fa774a3934b16387192
handoff_refresh_context: after_green_prompt_04_ci_evidence_and_docs_refresh
pr_state: open_draft_unmerged

review_input:
  authoritative_review: PR_Inspector_v1_5_0_RED_DO_NOT_MERGE
  uploaded_review_report: /mnt/data/Pasted text.txt
  original_blockers:
    - failing_CE_to_Builder_transition_pytest
    - zero_placeholder_lock_hashes
    - unproven_CE_to_Builder_lock_verification
    - unproven_CE_to_Builder_live_owner_tool_smoke
  resolved_by_this_continuation:
    - CE_to_Builder_transition_pytest_passes
    - all_zero_lock_hashes_replaced_with_exact_owner_file_byte_sha256_values
    - CE_to_Builder_lock_verification_passes
    - CE_to_Builder_live_owner_tool_smoke_passes

latest_green_ci_evidence_before_final_docs_refresh:
  repository: rezahh107/EV4-Project-Gate
  workflow: Skeleton Health
  run_id: 28741498875
  run_number: 313
  checked_head_sha: 87a4a84640c999cee049a0d40865c25efabeafb0
  conclusion: success
  jobs:
    skeleton: success
    python-core: success
  important_prompt_04_steps:
    Static runner-boundary scanner: success
    Runner tests: success
    CE-to-Builder transition pytest: success
    Behavioral coverage validator: success
    Behavioral fixture validation: success
    Compute CE-to-Builder lock hashes: success
    CE-to-Builder lock verification: success
    CE-to-Builder live owner tool smoke: success
    Official CE validator fixture suite: success
  note: Documentation-only refresh commits after this green run triggered run 28742062937 on head b097842f5450d5c638cffc3bae111aae56b6ba18; verify its final result before merge.

commit_ledger_note: Full continuation commit history is available in PR #20. Key green-evidence code head is 87a4a84640c999cee049a0d40865c25efabeafb0; latest handoff refresh commit is b097842f5450d5c638cffc3bae111aae56b6ba18.

files_changed_relevant_to_continuation:
  - .github/workflows/validate.yml
  - contracts/locks/ce-to-builder-transition.v1.lock.json
  - docs/BEHAVIORAL_RULE_COVERAGE.md
  - docs/IMPLEMENTATION_STATUS.yaml
  - docs/TRANSITION_BOUNDARY_MAP.md
  - docs/handoffs/PROMPT-04_HANDOFF.md
  - pyproject.toml
  - scripts/ce-to-builder-smoke.py
  - scripts/compute-ce-to-builder-lock.py
  - src/ev4_transition/runners/official_tools.py
  - src/ev4_transition/transitions/ce_to_builder.py
  - tests/transitions/test_ce_to_builder.py

tests_run_by_assistant_local:
  - none_after_network_clone_failure
tests_run_by_github_actions_green_run_28741498875:
  - pytest tests/test_cli.py tests/test_canonical_json.py tests/test_bundle_validator.py
  - pytest tests/test_architect_to_ce_transition.py selected suites
  - pytest tests/unit
  - python scripts/check-runner-boundary.py
  - pytest tests/runners
  - pytest -vv --tb=short --maxfail=1 tests/transitions/test_ce_to_builder.py
  - pytest tests/progress
  - pytest tests/boundary
  - python scripts/validate-behavioral-rule-coverage.py docs/BEHAVIORAL_RULE_COVERAGE.md
  - ev4-transition coverage validate docs/BEHAVIORAL_RULE_COVERAGE.md
  - pytest tests/behavioral_coverage
  - python scripts/verify-architect-to-ce-lock.py
  - python scripts/compute-ce-to-builder-lock.py
  - python scripts/verify-ce-to-builder-lock.py
  - python scripts/ce-to-builder-smoke.py
  - ev4-transition CLI smoke checks
  - official Architect validator fixture suite
  - official CE validator fixture suite
  - generated Architect-to-CE transition smoke

tests_passed_by_github_actions_on_run_28741498875:
  - all_listed_steps

tests_not_run_or_not_proven:
  - real_non_synthetic_CE_to_Builder_handoff_package
  - Builder_to_Responsive_transition_tests
  - final_evidence_gate_tests

coverage_rules_advanced:
  - PG-C2B-001: ci_enforced for PROMPT-04 baseline; exact owner file-byte SHA-256 lock values are committed and lock verification passed.
  - PG-C2B-002: ci_enforced for PROMPT-04 baseline; official CE validator, Builder gate, Builder adapter, Builder output validator path passed in CI smoke.
  - PG-VALIDATOR-001: ci_enforced for C2B owner validator path.
  - PG-ADAPTER-001: ci_enforced for Builder adapter path and fallback-adapter negative fixture.
  - PG-SYNTH-001: ci_enforced for synthetic/evidence distinction, with smoke explicitly non-real handoff evidence.
  - PG-SCHEMA-001: ci_enforced for Project Gate-owned result schema allowlist and no copied specialist schema files.
coverage_rules_still_gap:
  - PG-DOWNSTREAM-001 remains fixture_tested and not downstream_contract_enforced.
  - Real non-synthetic CE→Builder handoff evidence remains insufficient.

new_or_changed_ci:
  - Added C2B pytest log artifact on failure.
  - Added computed C2B lock hash manifest artifact.
  - Added C2B lock verification diagnostic artifact on failure.
  - Added C2B live smoke diagnostic artifact on failure.
  - Added C2B compute-lock step before lock verification.

important_design_decisions:
  - PR #20 stayed draft and was not merged.
  - Exact lock hashes were computed by GitHub Actions from pinned owner checkouts, then committed to contracts/locks/ce-to-builder-transition.v1.lock.json.
  - Builder adapter script identity marker changed to CE_BUILDER_PACKAGE_TRANSFORM_IDS because that marker exists in the pinned owner script.
  - Builder adapter contract identity marker changed to CE Builder Package Adapter Contract because the pinned owner contract document does not contain normalizeCeBuilderExecutablePackage as text.
  - CE package validator runner now writes a minimal CE review wrapper plus builder_executable_package because CE package mode expects constructability_review state as well as the package.
  - PyYAML was added as a dependency because the official CE validator imports yaml.
  - The C2B smoke uses a Builder-owned adapter-valid fixture when available; it is integration evidence, not real EV4 handoff evidence.
  - Attempted docs/DIAGNOSTIC_CODES.md refresh encountered a 409 stale-SHA conflict and was not applied.

web_sources_used: []

remaining_insufficient_evidence:
  - real_non_synthetic_CE_to_Builder_transition_evidence
  - Builder_to_Responsive_Project_Gate_transition
  - final_evidence_gate

next_allowed_prompt: PR_review_or_PROMPT-05_after_owner_accepts_PROMPT-04_baseline
