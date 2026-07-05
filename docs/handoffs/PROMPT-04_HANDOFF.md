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
  note: Documentation-only refresh commits after this green run may trigger newer runs; verify latest PR head before merge.

commits_added_after_initial_prompt_04_handoff:
  - 43e1f042e2ae8e0783571ab23524da56a16a37fc ci(c2b): preserve failing pytest log artifact
  - f56edbcea31b3f56d4dccd07b141c1b8f6481403 test(c2b): include CE validator identity marker
  - 304d4dc2cd9a7374f073aeffe5b9a137db7456c2 test(c2b): include Builder adapter identity marker
  - dc92297f6bc1c1d3ea4c230fb02f1384ef435a75 feat(c2b): add lock hash computation helper
  - 081553ab4aa8eb8498bfa0e547b7d8d8194a5856 ci(c2b): upload computed lock hash manifest
  - 64ce2ca47e19e814dba95c926ad451046689a99d fix(c2b): replace lock placeholders with computed owner hashes
  - 3c8c279a87c6b745006672e906782a776fc9d85b fix(c2b): align Builder adapter script identity marker
  - b93dbd371c1fc11816229b5104803a8d1a626f88 test(c2b): align adapter fixture marker with owner script
  - 1ececa659bfe40c4e5234d409085c0a5852ee9c7 fix(c2b): restore transition helper functions
  - 19119fba20f70365a4c3ac90f7f2f5108bf9f54f ci(c2b): preserve lock verification diagnostics
  - 1022c5affaf042316e5301e3e5894dedb5b8a5fb fix(c2b): align adapter contract identity marker
  - 43ccc6fc01086fd46daa985ca7d0179f6b6f39c4 test(c2b): align adapter contract fixture marker
  - 7c3e6a54b8f89d1d366d65c75d0db42ec990acc2 fix(c2b): unwrap Builder owner smoke fixture
  - 5c2f1c8b9f632fdc363834941fe5c4ad16054e24 fix(c2b): use Builder-owned smoke fixture when available
  - f258fdd22dd774adc6ef7149ac755fb8b3cfa6a3 ci(c2b): preserve live smoke diagnostics
  - 5a3bf436dfa12e7dc2bd49094634089a7668bc78 fix(c2b): wrap CE package validator input in CE review document
  - 87a4a84640c999cee049a0d40865c25efabeafb0 fix(c2b): add PyYAML for official CE validator execution
  - f58c8c0e4e61c1dc6fa59d3d4ad724f38fcfa4db docs(c2b): mark PROMPT-04 baseline CI evidenced
  - 1c2aa49a9dd6739d56a18a7a313c6b5ac6ed561e docs(c2b): update boundary map after green CI
  - 99512a2b8b7fddff1adaf44b3d8cee569fbf282a docs(c2b): promote green C2B coverage to ci_enforced
  - 96d27ebcbc24e42b4e4789f89086f3e51c995e86 docs(c2b): refresh PROMPT-04 handoff after green CI
  - 08f470b32d0b1db4a48c2268a8394ea5ccd4581f docs(c2b): clarify latest green CI reference
  - bfc2e92df6fd2129f9c5d8447d9902a3cd3e653a docs(c2b): refresh PROMPT-04 handoff latest green reference
  - 9d38f6cc2994060521feb4fc03eb5ea79940bb33 docs(c2b): record diagnostic docs conflict in handoff
  - 3b913881df9990338eb1c83a9953d6259134d029 docs(c2b): remove unresolved placeholder from handoff
  - 139c5b3f767e17b6587d1b272530e438c0ed7962 docs(c2b): finalize PROMPT-04 handoff commit ledger
  - 604fbfcae42e823ad4128907f58ef74aeff3b2bb docs(c2b): record final handoff commit ledger

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
