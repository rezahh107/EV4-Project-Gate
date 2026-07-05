prompt_id: PROMPT-03
branch: project-gate-prompt-03-runner-boundary
handoff_status: updated_after_pr_inspector_repairs_and_green_ci
commits:
  initial_prompt_03_range:
    - 0d22d2962d690d2308accc832b4d493ce05f14d5
    - 7998116340c29e0fc21889c83c90ce6faafbc816
  inspector_red_repair_commits:
    - 2c47d29c0b7f3b63ffde1470a0a7db30a9de4392: fix(runners): fail closed on adapter command mismatch
    - 7541ee37dd3aca8a4358580a450c3d0c4e91b72b: fix(runners): bind adapter command to declared path
    - 68b51ebebaee5b236ca71d048bfb1834c06fa4ee: fix(runners): pin official validator records to lock commits
    - 4c304178fdabe70de0744f4a7a5a55feb97b6010: test(runners): cover adapter command path binding
    - e7705bf411b56f68dc2d333ed0f168293eec359c: test(runners): assert official validator commit pinning
    - 620ac6a1ac12900692facdf5e7ccc5a6c9686253: docs(result): record adapter command binding failure
    - 9ae2b7f03e6883c4f71f5e27e2733a95334531f5: docs(handoff): record PR inspector red findings and fixes
  ci_diagnosis_and_schema_repair_commits:
    - ce12e00d626500435a915b265b4d86b55f6b6b81: ci(runners): split core and runner test steps
    - b79d6136ec9c1c0f255b49ae523abc85f926e8ea: ci(core): isolate core test groups
    - ec7f00dad264a20a2b59ab9c49f1ec7e1566fefc: ci(a2c): split transition and CLI tests
    - cdb6098520ed74b191aeda24db8c250c401e8ddd: ci(a2c): isolate pure transition failures
    - 2ed71c8f1b57e379f5c3e298136dc07c9f56931c: ci(a2c): isolate evidence determinism failures
    - feaadd324d53bdf03f423c194dd210bd45ace23a: fix(schemas): allow dotted Project Gate diagnostic codes
    - 7501cf11321a5feb6eb0867604f45a843e282165: fix(schemas): allow dotted A2C diagnostic codes
    - d1fc846c4efdfd28ce71bec6bb72739fa22e8c3e: fix(schemas): allow dotted transition-result diagnostic codes
    - 8fb551caee6608114b967c1da6402b6b8ce1b778: test(schemas): accept dotted Project Gate diagnostic codes
    - 7e98aded80ce42450ddabdb30128a9f92bc26ba1: docs(coverage): align CI step references after workflow split
  final_handoff_update:
    - this_commit: docs(handoff): record final prompt 03 green CI
files_changed:
  - .github/workflows/validate.yml
  - docs/BEHAVIORAL_RULE_COVERAGE.md
  - docs/RESULT_MODEL.md
  - docs/ROLE_BOUNDARY_MAP.md
  - docs/handoffs/PROMPT-03_HANDOFF.md
  - schemas/architect-to-ce-transition-result/architect-to-ce-transition-result.v1.schema.json
  - schemas/diagnostic/diagnostic.v1.schema.json
  - schemas/transition-result/transition-result.v1.schema.json
  - scripts/check-runner-boundary.py
  - src/ev4_transition/progress/__init__.py
  - src/ev4_transition/progress/events.py
  - src/ev4_transition/repo_access/__init__.py
  - src/ev4_transition/repo_access/local_repo.py
  - src/ev4_transition/repo_access/ports.py
  - src/ev4_transition/repo_access/remote_repo_future.py
  - src/ev4_transition/runners/__init__.py
  - src/ev4_transition/runners/failure_mapping.py
  - src/ev4_transition/runners/official_tools.py
  - src/ev4_transition/runners/records.py
  - src/ev4_transition/runners/subprocess_runner.py
  - src/ev4_transition/validator_runner.py
  - tests/boundary/test_runner_boundary_static.py
  - tests/progress/test_progress_sanitization.py
  - tests/runners/test_runner_execution.py
  - tests/runners/test_validator_runner_pinning.py
  - tests/unit/test_prompt01_transition_result_status_contract.py
tests_run:
  - local synthetic-tree subset before Inspector red review: PYTHONPATH=src pytest -q -> 19 passed
  - GitHub Actions run 28719839833 on head 7998116340c29e0fc21889c83c90ce6faafbc816 inspected through GitHub tools -> failure
  - GitHub Actions run 28734225063 on head 9ae2b7f03e6883c4f71f5e27e2733a95334531f5 inspected -> failure at Run Project Gate Python tests
  - GitHub Actions run 28734309621 on head ce12e00d626500435a915b265b4d86b55f6b6b81 inspected -> failure at Core and transition tests
  - GitHub Actions run 28734348973 on head b79d6136ec9c1c0f255b49ae523abc85f926e8ea inspected -> failure at Architect-to-CE transition tests
  - GitHub Actions run 28734392071 on head ec7f00dad264a20a2b59ab9c49f1ec7e1566fefc inspected -> failure at Architect-to-CE pure transition tests
  - GitHub Actions run 28734419506 on head cdb6098520ed74b191aeda24db8c250c401e8ddd inspected -> failure at A2C evidence and determinism tests
  - GitHub Actions run 28734451375 on head 2ed71c8f1b57e379f5c3e298136dc07c9f56931c inspected -> failure at A2C insufficient evidence test
  - GitHub Actions run 28734559052 on head 8fb551caee6608114b967c1da6402b6b8ce1b778 inspected -> behavioral coverage validator failed after Python/A2C/runner checks passed
  - GitHub Actions run 28734606213 on head 7e98aded80ce42450ddabdb30128a9f92bc26ba1 inspected -> success
  - attempted local git clone of live branch in ChatGPT container -> failed because github.com could not be resolved
tests_passed:
  - local synthetic-tree subset before Inspector red review: 19 passed
  - GitHub Actions run 28734606213 / Skeleton Health / skeleton job: success
  - GitHub Actions run 28734606213 / Skeleton Health / python-core job: success
  - GitHub Actions run 28734606213 successful python-core steps:
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
      - Progress tests
      - Runner boundary tests
      - Behavioral coverage validator
      - Behavioral fixture validation
      - Verify external contract lock hashes
      - CLI smoke valid bundle
      - CLI smoke invalid array
      - CLI smoke Persian insufficient evidence
      - Official Architect validator fixture suite
      - Official CE validator fixture suite
      - Generated Architect-to-CE transition smoke and CE binding
tests_failed:
  - GitHub Actions run 28719839833 on old head 7998116340c29e0fc21889c83c90ce6faafbc816: python-core failed at Run Project Gate Python tests
  - GitHub Actions run 28734225063 on intermediate head 9ae2b7f03e6883c4f71f5e27e2733a95334531f5: python-core failed at Run Project Gate Python tests
  - GitHub Actions run 28734309621 on intermediate head ce12e00d626500435a915b265b4d86b55f6b6b81: python-core failed at Core and transition tests
  - GitHub Actions run 28734348973 on intermediate head b79d6136ec9c1c0f255b49ae523abc85f926e8ea: python-core failed at Architect-to-CE transition tests
  - GitHub Actions run 28734392071 on intermediate head ec7f00dad264a20a2b59ab9c49f1ec7e1566fefc: python-core failed at Architect-to-CE pure transition tests
  - GitHub Actions run 28734419506 on intermediate head cdb6098520ed74b191aeda24db8c250c401e8ddd: python-core failed at A2C evidence and determinism tests
  - GitHub Actions run 28734451375 on intermediate head 2ed71c8f1b57e379f5c3e298136dc07c9f56931c: python-core failed at A2C insufficient evidence test
  - GitHub Actions run 28734559052 on intermediate head 8fb551caee6608114b967c1da6402b6b8ce1b778: python-core failed at Behavioral coverage validator
tests_not_run:
  - full local repository clone/install after repairs, because ChatGPT container DNS could not resolve github.com
  - local full branch pytest after repairs, for the same network reason
coverage_rules_advanced:
  - PG-BOUNDARY-001: static runner boundary scanner added; src/ev4_transition/validator_runner.py no longer imports/calls subprocess directly; CI step references pass on run 28734606213.
  - PG-VALIDATOR-001: official validator execution API added under src/ev4_transition/runners/; Architect/CE compatibility wrapper now passes pinned lock commits instead of unknown; runner tests pass on run 28734606213.
  - PG-ADAPTER-001: official adapter execution API added under src/ev4_transition/runners/; adapter command must now execute the declared adapter_path directly or through a trusted interpreter; mismatch fails closed; runner tests pass on run 28734606213.
  - PG-PROGRESS-001: sanitized runtime progress events added; token/env/stdout/stderr/private absolute path leakage is rejected; progress is excluded from canonical result hash; progress tests pass on run 28734606213.
  - PG-EVIDENCE-001: execution record carriers added for official tool execution evidence; stdout/stderr are recorded by SHA-256 hash only; successful official validator wrapper path no longer records unknown commit; dotted Project Gate diagnostic codes are schema-compatible.
coverage_rules_still_gap:
  - PG-VALIDATOR-001 remains validator_backed in the machine-readable coverage ledger until behavioral coverage fixture-family binding supports runner tests as fixtures.
  - PG-ADAPTER-001 remains validator_backed until PROMPT-04 adds real official CE→Builder adapter execution evidence.
  - PG-PROGRESS-001 remains validator_backed until PROMPT-06 adds full Persian RTL/LTR report UX fixtures.
  - PG-DOWNSTREAM-001 remains fixture_tested for false downstream-enforcement claim prevention only; real downstream contracts remain insufficient_evidence.
  - PG-STATUS-001 legacy valid compatibility still exists in existing Stage Bundle/A2C paths.
new_diagnostics:
  - PG.VALIDATOR.TIMEOUT
  - PG.ADAPTER.TIMEOUT
  - PG.RUNNER.COMMAND_NOT_FOUND
  - PG.VALIDATOR.MISSING
  - PG.ADAPTER.MISSING
  - PG.VALIDATOR.REPAIR_NEEDED
  - PG.VALIDATOR.CONTRACT_VIOLATION
  - PG.RUNNER.UNPARSEABLE_OUTPUT
  - PG.RUNNER.EXECUTION_FAILED
  - PG.ADAPTER.FALLBACK_FORBIDDEN
  - PG.ADAPTER.COMMAND_PATH_MISMATCH
  - PG.RUNNER_BOUNDARY.BANNED_IMPORT
  - PG.RUNNER_BOUNDARY.OS_SYSTEM
  - PG.RUNNER_BOUNDARY.SHELL_TRUE
  - PG.RUNNER_BOUNDARY.IMPORTLIB_SPECIALIST
  - PG.RUNNER_BOUNDARY.DIRECT_RUNTIME_COMMAND
  - PG.RUNNER_BOUNDARY.SYNTAX_ERROR
new_or_changed_cli:
  - scripts/check-runner-boundary.py added as repository script; no ev4-transition CLI subcommand added in PROMPT-03.
new_or_changed_ci:
  - .github/workflows/validate.yml splits broad pytest into named core/A2C/runner/progress/boundary/coverage steps.
  - .github/workflows/validate.yml runs python scripts/check-runner-boundary.py.
  - .github/workflows/validate.yml runs pytest tests/runners.
  - .github/workflows/validate.yml runs pytest tests/progress.
  - .github/workflows/validate.yml runs pytest tests/boundary.
  - .github/workflows/validate.yml keeps behavioral coverage validator, behavioral fixtures, lock hash, CLI smoke, official validator fixture suite, and transition smoke steps.
important_design_decisions:
  - Only src/ev4_transition/runners/ imports and calls subprocess for official specialist tools.
  - src/ev4_transition/validator_runner.py remains as compatibility wrapper for existing Architect→CE CLI behavior and delegates to runners.
  - src/ev4_transition/validator_runner.py now imports ARCHITECT_COMMIT and CE_COMMIT from external_lock instead of using UNKNOWN_COMMIT.
  - Adapter command binding is enforced before subprocess execution; adapter_path existence alone is not enough evidence.
  - Dotted Project Gate runner diagnostic codes are allowed in Project Gate diagnostic/result schemas because PROMPT-03 diagnostics use the PG.<AREA>.<CODE> namespace.
  - Runner records store stdout_hash/stderr_hash, not raw stdout/stderr.
  - Timeouts, missing commands, missing validators/adapters, adapter command mismatches, and unparseable output are fail-closed and never accepted.
  - Fallback adapter use is invalid and emits PG.ADAPTER.FALLBACK_FORBIDDEN.
  - Progress events are runtime/UI artifacts and are deliberately excluded from canonical final result hashing.
  - Repo access is local-only and mockable in Phase 1; remote connector behavior remains outside deterministic core.
  - PROMPT-03 intentionally does not implement CE→Builder, Builder→Responsive, final gate, or specialist business logic.
web_sources_used: []
next_allowed_prompt: PROMPT-04 only after owner accepts/merges PR #19; do not start PROMPT-04 from an unmerged branch.
blocking_issues:
  - PR #19 remains draft and unmerged at this handoff update.
  - Local full-clone validation was unavailable in ChatGPT container, but GitHub Actions run 28734606213 passed on the branch head before this handoff-only update.
remaining_insufficient_evidence:
  - CI result for this final handoff-only commit, if GitHub Actions reruns after the handoff update.
  - Real CE-to-Builder downstream rejection evidence.
  - Real Builder-to-Responsive downstream rejection evidence.
  - Official Builder adapter execution evidence.
  - Official Responsive validation evidence.
  - Final evidence gate policy, fixtures, and CI evidence.
inspector_red_findings:
  PRF-001:
    status: addressed_with_green_ci
    note: Initial failing CI was fixed; GitHub Actions run 28734606213 succeeded on head 7e98aded80ce42450ddabdb30128a9f92bc26ba1.
  PRF-002:
    status: addressed_in_code_and_ci
    note: UNKNOWN_COMMIT removed; Architect/CE validator wrapper uses ARCHITECT_COMMIT and CE_COMMIT from external_lock; validator pinning tests passed in run 28734606213.
  PRF-003:
    status: addressed_in_code_and_ci
    note: Adapter command must invoke declared adapter_path directly or through trusted interpreter; mismatch diagnostic and runner tests passed in run 28734606213.
  PRF-004:
    status: addressed_in_handoff
    note: Failed intermediate runs and final green run 28734606213 are now recorded.
