prompt_id: PROMPT-04
branch: project-gate-prompt-04-ce-to-builder
pull_request: 20
base_branch: main
base_sha: 10e665cdec74ba5508042fa774a3934b16387192
latest_code_head_sha_before_handoff_refresh: 796b3552c779d901a7452af573e3df4002c6d76c
pr_state_after_continuation: open_draft_unmerged

review_input:
  authoritative_review: PR_Inspector_v1_5_0_RED_DO_NOT_MERGE
  blocking_findings_addressed_partially:
    - PRF-001_CI_schema_allowlist: workflow_allowlist_updated_for_project_gate_owned_ce_to_builder_result_schema_and_skeleton_job_now_passes
    - PRF-002_lock_hashes_zero: not_fully_fixed_exact_hashes_still_pending
    - PRF-003_builder_pins_paths: builder_commit_and_paths_re_pinned_to_owner_commit_with_gate_registry_artifacts_but_lock_verification_not_reached_due_pytest_failure
    - PRF-004_ci_integration: CE_to_Builder_pytest_lock_verification_and_live_owner_tool_smoke_steps_added_but_pytest_currently_fails

commits_initial_slice:
  - 0af2e48feddff904fef3aaffbd078afbf682d1c9 feat(c2b): add transition package exports
  - 378c55a890e08dac5636fb4a6f556c13340ae5ce feat(c2b): add official CE and Builder runner helpers
  - 89167d2721bbf4f3a11612eec72218acb69270f4 feat(c2b): export official tool runner helpers
  - 067d6194693d5fb74d4527f5af306ad762c96327 feat(c2b): map owner gate and output validator failures
  - 89d6c39a3523f19af72e0c5ef203322eecad30c1 feat(c2b): support text validators and adapter output hashes
  - 99e9017a24e2498338d415f3fc3f66d5eceed019 feat(c2b): implement CE to Builder transition orchestration
  - ddee20754aa87562eb8369a408bdc14a21df4b22 feat(c2b): add CE to Builder transition result schema
  - 24868ab441fae40975ba6cecf16d92b1dd5f5091 chore(c2b): add fail-closed CE to Builder lock baseline
  - 4ef6d9f2141e927ac10cda7e66e30368fafe34a6 test(c2b): add CE to Builder transition fixture matrix tests
  - 70a5a8e2a45988198beb59a3193c6c074c66e9e5 test(c2b): add CE to Builder fixture matrix README
  - 2117c5b1e6f9a4c3a5f1374f53474c7940e44fbc test(c2b): add positive synthetic fixture label
  - 43d72d97cb951c1511bd05922e7f8b0878556502 test(c2b): add fallback adapter negative fixture label
  - 70fbe1bc47f3ec33dc21ea3230a3b6fd4995a6a2 test(c2b): add synthetic evidence insufficient fixture label
  - 9390ecab00cb47e71b9cff84e647f53ba5d562b8 docs(c2b): add PROMPT-04 handoff

commits_continuation:
  - 9df610a6fa2b22072e02abde05c080cd4e28229c feat(c2b): add live CE to Builder lock verifier
  - d975d3a422087bd8236f77552ffe124805341e79 feat(c2b): add live owner tool smoke script
  - e9eb27efcfa75a9d86c17e380d4ac191538fc56a fix(c2b): correct Builder pins and CE valid fixture path
  - 2cee92f5b99aa8c7d14c344ec163123c292a2a0a test: raw newline content support
  - cc7ff5dde503a4035ad653eb8d0abe052dc2bea5 chore: delete probe file
  - ff93ddefb4ae20c9d1a76129827a007990a2b13c fix(c2b): align transition pins with Builder owner gate commit
  - a239309e7ed0940593945382b80a7cb75feb5fe4 ci(c2b): wire CE to Builder checks and schema allowlist
  - 2348d1592bd4ae82d09db08c0556eed8a0978eca docs(c2b): update transition boundary map
  - b1a0af96c87ae4132065d98b4a0af06a3af55b05 docs(c2b): update implementation status
  - 454c04317306ac570d0bf814b9173d662ed725de docs(c2b): update behavioral coverage ledger
  - 1a87ce8b9de26ab7d99c5c08b2b5a9d5d7479561 docs(c2b): register CE to Builder diagnostics
  - a49b2fdb4c6613676bd7c3412bcfb9f98d7b1db5 docs(c2b): update PROMPT-04 handoff after Inspector follow-up
  - 3876b237a6f16b90f08aafc006faf1ab2ed0c8d8 test(c2b): align synthetic repos with corrected owner pins
  - 796b3552c779d901a7452af573e3df4002c6d76c test(c2b): make bundle fixture schema valid
  - THIS_COMMIT docs(c2b): refresh PROMPT-04 handoff with latest CI failure evidence

files_changed:
  - .github/workflows/validate.yml
  - contracts/locks/ce-to-builder-transition.v1.lock.json
  - docs/BEHAVIORAL_RULE_COVERAGE.md
  - docs/DIAGNOSTIC_CODES.md
  - docs/IMPLEMENTATION_STATUS.yaml
  - docs/TRANSITION_BOUNDARY_MAP.md
  - docs/handoffs/PROMPT-04_HANDOFF.md
  - schemas/ce-to-builder-transition-result/ce-to-builder-transition-result.v1.schema.json
  - scripts/ce-to-builder-smoke.py
  - scripts/verify-ce-to-builder-lock.py
  - src/ev4_transition/runners/__init__.py
  - src/ev4_transition/runners/failure_mapping.py
  - src/ev4_transition/runners/official_tools.py
  - src/ev4_transition/runners/subprocess_runner.py
  - src/ev4_transition/transitions/__init__.py
  - src/ev4_transition/transitions/ce_to_builder.py
  - tests/fixture_matrix/ce_to_builder/README.md
  - tests/fixture_matrix/ce_to_builder/valid/synthetic-ce-package-label.json
  - tests/fixture_matrix/ce_to_builder/invalid/synthetic-fallback-adapter-forbidden.json
  - tests/fixture_matrix/ce_to_builder/insufficient-evidence/synthetic-only-not-real-evidence.json
  - tests/transitions/test_ce_to_builder.py

tests_run_by_assistant_local:
  - local py_compile on drafted Python files before GitHub write in initial slice
  - local py_compile on continuation draft scripts/modules in /mnt/data
  - local YAML parse of drafted workflow/status files in /mnt/data
tests_passed_by_assistant_local:
  - py_compile_drafted_python_files
  - yaml_parse_drafted_workflow_and_status
tests_failed_by_assistant_local: []

github_actions_evidence:
  latest_completed_run_checked:
    code_head_sha: 796b3552c779d901a7452af573e3df4002c6d76c
    run_id: 28738791107
    workflow: Skeleton Health
    skeleton_job: success
    schema_allowlist_step: success
    python_core_job: failure
    successful_python_core_steps_before_failure:
      - Checkout Project Gate
      - Checkout Architect pinned contract repo
      - Checkout CE pinned contract repo
      - Checkout CE pinned CE-to-Builder repo
      - Checkout Builder pinned CE-to-Builder repo
      - Setup Python
      - Setup Node
      - Install package
      - CLI and bundle tests
      - A2C valid transition smoke
      - A2C mapping and order tests
      - A2C fail-closed hook tests
      - A2C source commit preservation test
      - A2C insufficient evidence test
      - A2C lock enforcement test
      - A2C repeat run determinism test
      - A2C nonfinite edge test
      - Architect-to-CE CLI transition tests
      - Prompt 01 unit tests
      - Static runner-boundary scanner
      - Runner tests
    failing_step: CE-to-Builder transition pytest
    skipped_after_failure:
      - Progress tests
      - Runner boundary tests
      - Behavioral coverage validator
      - Behavioral fixture validation
      - Verify external contract lock hashes
      - CE-to-Builder lock verification
      - CE-to-Builder live owner tool smoke
      - CLI smoke valid bundle
      - CLI smoke invalid array
      - CLI smoke Persian insufficient evidence
      - Official Architect validator fixture suite
      - Official CE validator fixture suite
      - Generated Architect-to-CE transition smoke and CE binding
    failure_detail_limit: job_log_output_available_to_chat_was_truncated_before_pytest_traceback

tests_not_run_or_not_proven:
  - pytest tests/transitions/test_ce_to_builder.py passing result
  - python scripts/verify-ce-to-builder-lock.py passing result with exact lock hashes
  - python scripts/ce-to-builder-smoke.py passing result with pinned live owner checkouts
  - full GitHub Actions success on latest PR head

coverage_rules_advanced:
  - PG-C2B-001: validator_backed lock verification carrier and CI step added; not ci_enforced while exact hashes are placeholders and CI step is skipped by earlier pytest failure
  - PG-C2B-002: validator_backed official CE validator Builder gate Builder adapter Builder output validator sequence carrier added; not ci_enforced until pytest and live owner smoke pass
  - PG-EVIDENCE-001: CE-to-Builder accepted_requires result schema and transition result validation included; not ci_enforced until CI passes
  - PG-SYNTH-001: synthetic evidence remains explicitly non-real evidence; live owner smoke is labeled synthetic integration evidence
  - PG-SCHEMA-001: CE-to-Builder result schema is explicitly treated as Project Gate-owned result envelope and schema allowlist now passes
coverage_rules_still_gap:
  - PG-C2B-001 needs exact file-byte SHA-256 values and passing CI lock verification
  - PG-C2B-002 needs passing CE-to-Builder pytest and live owner tool smoke on pinned checkouts
  - PG-DOWNSTREAM-001 remains below downstream_contract_enforced

new_diagnostics:
  - PG.C2B.LOCK_NOT_OBJECT
  - PG.C2B.LOCK_VERSION_MISMATCH
  - PG.C2B.LOCK_TRANSITION_ID_MISMATCH
  - PG.C2B.LOCK_FILES_NOT_ARRAY
  - PG.C2B.LOCK_ENTRY_NOT_OBJECT
  - PG.C2B.LOCK_ROLE_UNEXPECTED
  - PG.C2B.LOCK_ROLE_DUPLICATE
  - PG.C2B.LOCK_ROLE_MISSING
  - PG.C2B.LOCK_REPOSITORY_MISMATCH
  - PG.C2B.LOCK_COMMIT_MISMATCH
  - PG.C2B.LOCK_PATH_MISMATCH
  - PG.C2B.LOCK_IDENTITY_MISMATCH
  - PG.C2B.OWNER_FILE_READ_FAILED
  - PG.C2B.EXTERNAL_HASH_MISMATCH
  - PG.C2B.EXTERNAL_IDENTITY_MISMATCH
  - PG.C2B.INPUT_NOT_OBJECT
  - PG.C2B.CE_PACKAGE_MISSING
  - PG.C2B.CE_PACKAGE_NOT_OBJECT
  - PG.C2B.CE_PACKAGE_SCHEMA_MISMATCH
  - PG.C2B.SYNTHETIC_ONLY_EVIDENCE
  - PG.C2B.ADAPTER_OUTPUT_UNPARSEABLE
  - PG.C2B.BUILDER_SCHEMA_UNAVAILABLE
  - PG.C2B.BUILDER_SCHEMA_VALIDATION_FAILED
  - PG.C2B.FORBIDDEN_CLAIM
  - PG.C2B.ACCEPTED_REQUIRES_MISSING
  - PG.ADAPTER.EXECUTION_FAILED

new_or_changed_cli:
  - none; CE-to-Builder remains Python API plus CI scripts in this slice
new_or_changed_ci:
  - added project-gate-prompt-04-ce-to-builder push trigger
  - allowed schemas/ce-to-builder-transition-result/ce-to-builder-transition-result.v1.schema.json as Project Gate-owned result schema
  - added pinned CE checkout for PROMPT-04
  - added pinned Builder checkout for PROMPT-04
  - added Setup Node to python-core job
  - added CE-to-Builder transition pytest step
  - added CE-to-Builder lock verification step
  - added CE-to-Builder live owner tool smoke step

important_design_decisions:
  - PR #20 was converted back to draft after PR Inspector reported draft mismatch.
  - Builder dependency pins were re-pinned from 4d9445fe76e3f8a15a179735ad82c9aadec0991b to 69a2c61edf6d06b4418ad770fcefbfdffcf275d6 because that commit contains the Builder gate doc, gate script, adapter contract/script, registry JSON, and output validator paths.
  - CE valid fixture path was corrected to tests/role-alignment/valid/executable_visual_reference_package.json because it carries builder_executable_package with schema ev4-builder-executable-package@1.0.0.
  - CE owner role-alignment wrapper input is accepted by the Project Gate extractor only as a wrapper; Project Gate still validates the inner CE-owned builder_executable_package identity.
  - Forbidden claim detection now recursively treats production_ready, builder_runtime_authorized, and production_ready_allowed=true as blocking.
  - The lock remains fail-closed with placeholder hashes until exact file-byte SHA-256 values are available from CI/local owner checkouts.
  - A temporary newline probe file was created and deleted; it is not present in the final compare diff.
  - CE-to-Builder pytest remains the current CI blocker; exact assertion traceback is unknown because the available job-log output was truncated before the pytest failure details.

web_sources_used: []

blocking_issues:
  - CE-to-Builder transition pytest fails in GitHub Actions on code head 796b3552c779d901a7452af573e3df4002c6d76c.
  - Exact live owner file-byte SHA-256 values must replace all-zero placeholders in contracts/locks/ce-to-builder-transition.v1.lock.json.
  - CE-to-Builder lock verification must pass with pinned CE and Builder checkouts after hashes are replaced.
  - CE-to-Builder live owner tool smoke must pass and remain labeled as synthetic integration evidence, not real handoff evidence.
  - PR must remain draft until blockers are resolved.

remaining_insufficient_evidence:
  - exact_file_byte_sha256_values_for_contracts/locks/ce-to-builder-transition.v1.lock.json
  - passing_GitHub_Actions_result_for_PR_20_latest_head
  - passing_CE-to-Builder_transition_pytest_result
  - passing_CE-to-Builder_lock_verification_with_pinned_CE_and_Builder_checkouts
  - passing_CE-to-Builder_live_owner_tool_smoke
  - real_non_synthetic_CE_to_Builder_transition_evidence

next_allowed_prompt: continue_PROMPT-04_debug_CE_to_Builder_pytest_then_replace_lock_hashes_and_recheck_PR_20
