prompt_id: PROMPT-01
branch: project-gate-prompt-01-deterministic-core
commits:
  - a0c72f13a76f0546bb6081f299c83e75b7c6bf4b core: align diagnostics with project gate statuses
  - cbaae6a04a94d6dab8b3d6ef75723a27d7045f3b presentation: add status mapping package
  - e5e999a61a7e5ea795c8e07760beddfa2b0db1f5 presentation: implement project gate status mapping
  - 601e1e077bd947a985faff722d73e4c5165202d6 cli: use project gate status exit mapping
  - b6f7446eb26ba915aa19ec911c618e30d0bc47ea core: preserve legacy validation status compatibility
  - 240ced70e8d5aaae9723df4faa1efaeb9981e49a core: expose deterministic foundation namespace
  - 05dfe643e89ec66ff1988c8b379c19c460687b27 core: add canonical json compatibility module
  - e27d94ec18eba08b13f49560217c9e192330c677 stage-bundle: add package namespace
  - e018bc319c7805053d18465b002e4efe7439b013 stage-bundle: add validator compatibility module
  - 199e9fc22fdcbfa6c7960be4aaed6527af94901e locks: add lock namespace
  - 9d81ff27ce3c632d19730328172309c8a8dc4f78 locks: add project gate lock manifest validator
  - 26a41c7c4547141e4d72a4367d1b497681e261f0 core: add explicit file-byte sha256 helper
  - a5c9b91c9de169081705e31f3c90d76ee9f957c2 schemas: add diagnostic schema v1
  - b8bd56fbb28bfbf3e363cb731f580ca05308311e schemas: add lock manifest schema v1
  - 19add6391f306a40b506fb4247b83feb4d69aa43 schemas: harden transition result status model
  - 7f45abf151224b565c0e2365ce1c4dde40085710 tests: add prompt 01 valid stage bundle fixture
  - c3f7e2dc77f3028f19ec69d3f9478f9bfa38de08 tests: add prompt 01 invalid stage bundle fixture
  - 24d79e078b7e4c23b2c8bd8b470c2229f79c7360 tests: add prompt 01 valid result envelope fixture
  - d8562e92ed668dc806e92dab4323a356cc256e4a tests: add prompt 01 invalid result envelope fixture
  - 17a705ed9186d11f819714071cff0d44d143c72e tests: add prompt 01 deterministic core coverage
  - c2c8720a04da82706e20695a895ac1fd4698a06f ci: allow project gate prompt 01 schemas
  - 8db1116f3dfaa69147be8776fde20c72c26b1722 docs: update project gate schema inventory
  - 3ba5121af7532d070a2b60baa7840133cffdaeff docs: add project gate result model
  - 93bbb55bb6f42a84d6bc7078588ff93c1ebaabcb docs: add status decision matrix
  - a360e271e9ce9eed6bf7686d1c3cb9777d77f569 docs: add diagnostic code registry baseline
  - 855e613435e6e41bda78788c7833f3834aa7bbc2 docs: add lock manifest policy
  - de6b31489087bb49cd11b4eb7f14f54e03c4e91a docs: update architecture for prompt 01 core foundation
  - d89353bd5c854c7cc0a69e8227054038dae896e5 docs: update role boundary for prompt 01 contracts
  - 08de4a715a91d206c0d885b85a58eea140129b6f docs: update behavioral coverage for prompt 01
  - b2342be6b7b7ecb35d90e79731848cfeab8ff4a0 docs: add prompt 01 handoff
  - b11db5606038dbbb1f276b0397658c15b09e5155 fix: preserve legacy valid Persian wording
  - self_reference: docs: refresh prompt 01 handoff after ci feedback; exact commit SHA is reported in final response.
files_changed:
  - .github/workflows/validate.yml
  - docs/ARCHITECTURE.md
  - docs/BEHAVIORAL_RULE_COVERAGE.md
  - docs/DIAGNOSTIC_CODES.md
  - docs/LOCK_MANIFEST_POLICY.md
  - docs/RESULT_MODEL.md
  - docs/ROLE_BOUNDARY_MAP.md
  - docs/STATUS_DECISION_MATRIX.md
  - docs/handoffs/PROMPT-01_HANDOFF.md
  - schemas/README.md
  - schemas/diagnostic/diagnostic.v1.schema.json
  - schemas/lock-manifest/lock-manifest.v1.schema.json
  - schemas/transition-result/transition-result.v1.schema.json
  - src/ev4_transition/canonical_json.py
  - src/ev4_transition/cli.py
  - src/ev4_transition/core/__init__.py
  - src/ev4_transition/core/canonical_json.py
  - src/ev4_transition/diagnostics.py
  - src/ev4_transition/locks/__init__.py
  - src/ev4_transition/locks/manifest.py
  - src/ev4_transition/presentation/__init__.py
  - src/ev4_transition/presentation/status_mapping.py
  - src/ev4_transition/stage_bundle/__init__.py
  - src/ev4_transition/stage_bundle/validator.py
  - tests/fixtures/result_envelope/invalid/missing-status.v1.json
  - tests/fixtures/result_envelope/valid/accepted-stage-validation.v1.json
  - tests/fixtures/stage_bundle/invalid/missing-synthetic-label.v1.json
  - tests/fixtures/stage_bundle/valid/minimal-stage-bundle.v1.json
  - tests/unit/test_prompt01_deterministic_core.py
tests_run:
  - GitHub Actions run 28715773325: skeleton job passed; python-core failed at Run Project Gate Python tests on pre-fix head b2342be6b7b7ecb35d90e79731848cfeab8ff4a0.
  - GitHub Actions run 28715821162: started after fix commit b11db5606038dbbb1f276b0397658c15b09e5155; final result not recorded in this handoff because a handoff refresh commit follows it.
tests_passed:
  - GitHub Actions run 28715773325: skeleton job succeeded.
tests_failed:
  - GitHub Actions run 28715773325: python-core failed at Run Project Gate Python tests.
tests_not_run:
  - local python -m pip install -e '.[dev]'
  - local pytest
  - local ev4-transition validate fixtures/valid/architect-stage-bundle.v1.json
  - local ev4-transition validate fixtures/invalid/array-input.v1.json
  - local ev4-transition validate fixtures/insufficient-evidence/architect-stage-bundle.v1.json --format persian
  - local python scripts/verify-architect-to-ce-lock.py --architect-repo ../EV4-Architect-Repo --ce-repo ../EV4-Constructability-Engineer-Repo
  - local python scripts/transition-smoke.py --architect-repo ../EV4-Architect-Repo --ce-repo ../EV4-Constructability-Engineer-Repo
  - local npm run status
  - local npm run validate
coverage_rules_advanced:
  - PG-HASH-001: explicit file-byte SHA-256 helper and deterministic canonical JSON regression tests added.
  - PG-LOCK-001: lock manifest schema and structural lock manifest validator added.
  - PG-STATUS-001: target status mapping added for icon, semantic tone, Persian label, and exit code; legacy valid compatibility preserved.
  - PG-UNICODE-001: explicit composed/decomposed Unicode no-normalization regression test added.
  - PG-EVIDENCE-001: result model and status matrix carriers added; full future transition accepted-gate enforcement remains incomplete.
  - PG-SYNTH-001: Stage Bundle synthetic-label negative fixture added.
coverage_rules_still_gap:
  - PG-EVIDENCE-001: no full accepted-without-evidence future-transition validator yet.
  - PG-STATUS-001: existing Stage Bundle and A2C paths still emit legacy valid; target status mapping exists but direct target emission is not universal.
  - PG-BRC-001: no behavioral coverage schema/validator/fixtures/CI yet.
  - PG-PROGRESS-001: no automated no-false-progress handoff validator yet.
  - PG-ADAPTER-001: CE-to-Builder and Builder-to-Responsive adapter orchestration not implemented.
  - PG-DOWNSTREAM-001: downstream rejection evidence not orchestrated for CE-to-Builder or Builder-to-Responsive.
new_diagnostics:
  - PG_LOCK_SCHEMA_VERSION_MISSING
  - PG_LOCK_SCHEMA_VERSION_UNKNOWN
  - PG_LOCK_FILES_NOT_ARRAY
  - PG_LOCK_ENTRY_NOT_OBJECT
  - PG_LOCK_ROLE_INVALID
  - PG_LOCK_ROLE_DUPLICATE
  - PG_LOCK_FIELD_INVALID
  - PG_LOCK_HASH_NOT_LOWERCASE
new_or_changed_cli:
  - ev4-transition exit-code mapping now uses src/ev4_transition/presentation/status_mapping.py.
  - no new CLI command added.
new_or_changed_ci:
  - .github/workflows/validate.yml schema allowlist updated for schemas/diagnostic/diagnostic.v1.schema.json and schemas/lock-manifest/lock-manifest.v1.schema.json.
important_design_decisions:
  - Preserved existing stage-bundle.v1 schema instead of replacing it.
  - Added Project Gate-owned diagnostic and lock manifest schemas only; no specialist schema was copied.
  - Preserved legacy valid status compatibility in current Stage Bundle and A2C implementation to avoid a broad breaking change during Prompt 01.
  - Added target accepted/repair_needed/insufficient_evidence/invalid presentation mapping and docs so future transition prompts can migrate deliberately.
  - Kept progress/runtime state out of canonical JSON helpers; no implicit timestamp helper was added.
  - Kept Unicode strings unnormalized; added regression test to distinguish composed and decomposed forms.
  - A large direct rewrite of src/ev4_transition/architect_to_ce.py was attempted but blocked by the GitHub write safety layer; no commit occurred from that blocked call, and the final design avoided the broad rewrite.
  - After CI feedback, legacy Persian valid wording was restored to include بسته معتبر while keeping the new accepted mapping.
web_sources_used: []
next_allowed_prompt: PROMPT-02
blocking_issues:
  - Local tests were not run by the assistant because the container could not resolve github.com and no local repository checkout was available.
  - Latest post-fix GitHub Actions result must be checked before merge.
  - Existing Architect-to-CE result schema still uses legacy valid/invalid/insufficient_evidence vocabulary; full migration to target transition statuses is deferred to future scoped work.
remaining_insufficient_evidence:
  - latest post-fix Prompt 01 GitHub Actions result
  - real Elementor artifact validation
  - real cross-repository validation beyond synthetic fixtures
  - CE-to-Builder Project Gate lock manifest and transition result contract
  - Builder-to-Responsive formal Builder export or explicit Project Gate transport contract
  - Responsive Builder input validation against real verified Builder evidence
  - downstream rejection evidence for real invalid handoffs
  - final evidence gate policy, fixtures, and CI evidence
