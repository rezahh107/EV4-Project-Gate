prompt_id: PROMPT-01
branch: project-gate-prompt-01-deterministic-core
summary: Project Gate-owned contracts and deterministic core hardening with Inspector follow-up fixes.
commit_groups:
  initial_prompt_01_foundation:
    range: a0c72f13a76f0546bb6081f299c83e75b7c6bf4b..7d5c751f6a7a095d4de97eb6bbbaa2402b2f9ffb
    note: Initial Prompt 01 implementation, compatibility fixes, and first CI handoff update.
  first_inspector_followup:
    - a011399a83e45c41c434a9f449dfae1c8a036c95 fix: enforce lock manifest structural constraints
    - e1275b82130bb6c088b8c86fd5a4c951dd8f5e34 tests: add fail-closed lock manifest negative tests
    - 6eadbb53e6a6c64817ff514198f642b61123464a docs: document strict lock manifest diagnostics
    - c5bee26bdd169658d40686e3be4a3269052b0496 docs: align prompt 01 coverage after inspector finding
    - 5ba2c7874657e52f81a010e42aa516dae99094d0 docs: record inspector lock validation fix
  second_inspector_followup:
    - f1cd68d50f4a2c17b1e0717c4ee5c80a9257ca4b schemas: enforce transition result status diagnostics correlation
    - b08ec25609daf72fb249566d9006daf766b96011 tests: make accepted result fixture evidence-bearing
    - 2625c4fe0cf04babdf46d4b8d7771bb370bc67e1 tests: add transition result status correlation negatives
    - 20893c7f9d24ecc430e44b53941b292aaf5b5fb2 fix: reject unknown lock manifest fields
    - 3083bd6bb894bb0ab10455f1a702027c8a2a042d tests: cover unknown lock manifest fields
    - 8c1e35a3755bc5dcc0a4cd0350271776cade01ba refactor: re-export canonical file sha256 helper
    - 518dac82417e4c1673ecc459bd8f29c28338c96e docs: add unknown lock field diagnostic
    - bdb2a239e897d1000c7b20de698ae83de924fab2 docs: document result status schema correlation
    - 804f277eeabdbf891eedd8a0d74b02967ce81720 docs: align status matrix with result schema
    - 760cb089e0e6006ece42c0845d34ee81e34128a4 docs: record inspector result-contract fixes
    - ded157caf279788b938cfa678c8cbbeb8bb5bd18 docs: record second inspector blocker fixes
  r2_inspector_followup:
    - fc6742e0b98728c4b4710ca837916758c855ccae schemas: close accepted evidence bypasses and legacy warning drift
    - 9286a5e95ee1ced546cf542b8f602e0132448dba tests: remove stale result status contract test for rewrite
    - 425eb6b0f7a3dd585a49f8357e3668921ed96f7d tests: cover accepted evidence bypasses and legacy warning contract
    - 2703a6755f81729b061efc8d6ccaec2d85df2fe3 docs: tighten accepted evidence model and legacy valid warning rule
    - 14310274d9809cc4f5c29291876940214f9412a4 docs: align valid warning compatibility in status matrix
    - 87a52efd30511289ca332f89a55c1b7472067c76 docs: record r2 accepted and legacy valid fixes
    - self_reference: docs: record r2 inspector blocker fixes; final commit SHA is reported in the final response.
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
  - tests/unit/test_prompt01_lock_manifest_strictness.py
  - tests/unit/test_prompt01_transition_result_status_contract.py
tests_run:
  - GitHub Actions run 28715773325: skeleton passed; python-core failed at Run Project Gate Python tests on pre-fix head b2342be6b7b7ecb35d90e79731848cfeab8ff4a0.
  - GitHub Actions run 28715844363: skeleton and python-core passed on code-bearing head decece3f6e87663cba565c51e91eb8b0775528b5.
  - GitHub Actions run 28716189498: skeleton and python-core passed on first Inspector follow-up head 5ba2c7874657e52f81a010e42aa516dae99094d0.
  - GitHub Actions run 28716744210: skeleton and python-core passed on second Inspector follow-up head ded157caf279788b938cfa678c8cbbeb8bb5bd18.
  - PR-Inspector R2 reported accepted bypasses for null source stage, empty provenance, and swapped hash scopes, plus valid-warning producer/schema drift against head ded157caf279788b938cfa678c8cbbeb8bb5bd18.
  - Final R2 GitHub Actions must run after this handoff commit; do not merge until it passes.
tests_passed:
  - Run 28716744210: skeleton succeeded.
  - Run 28716744210: python-core succeeded.
  - Run 28716744210: Run Project Gate Python tests succeeded.
  - Run 28716744210: Verify external contract lock hashes succeeded.
  - Run 28716744210: CLI smoke valid bundle succeeded.
  - Run 28716744210: CLI smoke invalid array succeeded.
  - Run 28716744210: CLI smoke Persian insufficient evidence succeeded.
  - Run 28716744210: Official Architect validator fixture suite succeeded.
  - Run 28716744210: Official CE validator fixture suite succeeded.
  - Run 28716744210: Generated Architect-to-CE transition smoke and CE binding succeeded.
tests_failed:
  - Run 28715773325: python-core failed before fix commit b11db5606038dbbb1f276b0397658c15b09e5155.
  - First Inspector PRF-001: validate_lock_manifest was weaker than schema/policy on reviewed head 7d5c751f6a7a095d4de97eb6bbbaa2402b2f9ffb.
  - Second Inspector PRF-001: transition-result.v1 accepted contradictory accepted/error/no-evidence combinations on reviewed head 5ba2c7874657e52f81a010e42aa516dae99094d0.
  - Second Inspector PRF-002: validate_lock_manifest accepted unknown top-level and file-entry fields on reviewed head 5ba2c7874657e52f81a010e42aa516dae99094d0.
  - R2 Inspector PRF-001: accepted still permitted null source stage, empty provenance objects, and swapped hash scopes on reviewed head ded157caf279788b938cfa678c8cbbeb8bb5bd18.
  - R2 Inspector PRF-002: legacy producer returns valid for warnings while schema rejected valid+warning on reviewed head ded157caf279788b938cfa678c8cbbeb8bb5bd18.
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
  - PG-HASH-001: explicit file-byte SHA-256 helper and deterministic canonical JSON regression tests added; compatibility namespace now re-exports the canonical helper.
  - PG-LOCK-001: lock manifest schema, strict structural lock manifest validator, schema allowlist checks, and fail-closed negative tests added.
  - PG-STATUS-001: target status mapping, result schema status/diagnostic correlation, contradiction tests, and legacy valid-warning compatibility test added.
  - PG-UNICODE-001: explicit composed/decomposed Unicode no-normalization regression test added.
  - PG-EVIDENCE-001: accepted result carrier now requires concrete source_stage, property-specific hash scopes, source_provenance.kind, produced_by.tool, and no blocking diagnostic.
  - PG-SYNTH-001: Stage Bundle synthetic-label negative fixture added.
coverage_rules_still_gap:
  - PG-STATUS-001: existing Stage Bundle and A2C paths still emit legacy valid; target status mapping exists but direct target emission is not universal.
  - PG-BRC-001: no behavioral coverage schema/validator/fixtures/CI yet.
  - PG-PROGRESS-001: no automated no-false-progress handoff validator yet.
  - PG-ADAPTER-001: CE-to-Builder and Builder-to-Responsive adapter orchestration not implemented.
  - PG-DOWNSTREAM-001: downstream rejection evidence not orchestrated for CE-to-Builder or Builder-to-Responsive.
new_diagnostics:
  - PG_LOCK_SCHEMA_VERSION_MISSING
  - PG_LOCK_SCHEMA_VERSION_UNKNOWN
  - PG_LOCK_TRANSITION_ID_INVALID
  - PG_LOCK_FILES_NOT_ARRAY
  - PG_LOCK_FILES_EMPTY
  - PG_LOCK_ENTRY_NOT_OBJECT
  - PG_LOCK_ROLE_INVALID
  - PG_LOCK_ROLE_DUPLICATE
  - PG_LOCK_FIELD_INVALID
  - PG_LOCK_UNKNOWN_FIELD
  - PG_LOCK_REPOSITORY_INVALID
  - PG_LOCK_COMMIT_INVALID
  - PG_LOCK_HASH_INVALID
  - PG_LOCK_SIZE_BYTES_INVALID
new_or_changed_cli:
  - ev4-transition exit-code mapping uses src/ev4_transition/presentation/status_mapping.py.
  - no new CLI command added.
new_or_changed_ci:
  - .github/workflows/validate.yml schema allowlist updated for schemas/diagnostic/diagnostic.v1.schema.json and schemas/lock-manifest/lock-manifest.v1.schema.json.
important_design_decisions:
  - Preserved existing stage-bundle.v1 schema instead of replacing it.
  - Added Project Gate-owned diagnostic and lock manifest schemas only; no specialist schema was copied.
  - Preserved legacy valid status compatibility in current Stage Bundle and A2C implementation; warning-only legacy results remain schema-valid in Prompt 01.
  - Enforced accepted/repair_needed/insufficient_evidence/invalid status correlation in transition-result.v1 while keeping legacy valid explicitly separate.
  - Tightened accepted carrier evidence without adding CE/Builder/Responsive specialist semantics.
  - Kept progress/runtime state out of canonical JSON helpers; no implicit timestamp helper was added.
  - Kept Unicode strings unnormalized; added regression test to distinguish composed and decomposed forms.
  - Kept lock manifest validation structural; file-byte verification against repositories remains in transition-specific code.
  - Replaced duplicate compatibility file_sha256 implementation with canonical re-export.
web_sources_used: []
next_allowed_prompt: PROMPT-02
blocking_issues:
  - Local tests were not run by the assistant because the container could not resolve github.com and no local repository checkout was available.
  - Existing Architect-to-CE result schema still uses legacy valid/invalid/insufficient_evidence vocabulary; full migration to target transition statuses is deferred to future scoped work.
  - Final R2 GitHub Actions must pass before merge.
remaining_insufficient_evidence:
  - final R2 GitHub Actions result
  - real Elementor artifact validation
  - real cross-repository validation beyond synthetic fixtures
  - CE-to-Builder Project Gate lock manifest and transition result contract
  - Builder-to-Responsive formal Builder export or explicit Project Gate transport contract
  - Responsive Builder input validation against real verified Builder evidence
  - downstream rejection evidence for real invalid handoffs
  - final evidence gate policy, fixtures, and CI evidence
