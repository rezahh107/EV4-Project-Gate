prompt_id: PROMPT-03
branch: project-gate-prompt-03-runner-boundary
handoff_status: updated_after_pr_inspector_red_review
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
    - this_commit: docs(handoff): record PR inspector red findings and fixes
files_changed:
  - .github/workflows/validate.yml
  - docs/BEHAVIORAL_RULE_COVERAGE.md
  - docs/RESULT_MODEL.md
  - docs/ROLE_BOUNDARY_MAP.md
  - docs/handoffs/PROMPT-03_HANDOFF.md
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
tests_run:
  - local synthetic-tree subset before Inspector red review: PYTHONPATH=src pytest -q -> 19 passed
  - GitHub Actions run 28719839833 on head 7998116340c29e0fc21889c83c90ce6faafbc816 inspected through GitHub tools -> failure
  - GitHub workflow jobs inspected for run 28719839833 -> skeleton success; python-core failure at Run Project Gate Python tests; runner-specific later steps skipped
  - attempted local git clone of live branch in ChatGPT container -> failed because github.com could not be resolved
tests_passed:
  - local synthetic-tree subset before Inspector red review: 19 passed
tests_failed:
  - GitHub Actions run 28719839833 on head 7998116340c29e0fc21889c83c90ce6faafbc816: python-core failed at Run Project Gate Python tests
tests_not_run:
  - full live repository clone/install after Inspector repair commits
  - python -m pip install -e '.[dev]' against repaired live branch
  - full live branch pytest after Inspector repair commits
  - python scripts/check-runner-boundary.py against repaired live branch
  - ev4-transition coverage validate docs/BEHAVIORAL_RULE_COVERAGE.md against repaired live branch
  - npm run status
  - npm run validate
  - GitHub Actions on repaired post-620ac6a head: pending/not yet evidenced at handoff update time
coverage_rules_advanced:
  - PG-BOUNDARY-001: static runner boundary scanner added; src/ev4_transition/validator_runner.py no longer imports/calls subprocess directly; CI step references added.
  - PG-VALIDATOR-001: official validator execution API added under src/ev4_transition/runners/; Architect/CE compatibility wrapper now passes pinned lock commits instead of unknown.
  - PG-ADAPTER-001: official adapter execution API added under src/ev4_transition/runners/; adapter command must now execute the declared adapter_path directly or through a trusted interpreter; mismatch fails closed.
  - PG-PROGRESS-001: sanitized runtime progress events added; token/env/stdout/stderr/private absolute path leakage is rejected; progress is excluded from canonical result hash.
  - PG-EVIDENCE-001: execution record carriers added for official tool execution evidence; stdout/stderr are recorded by SHA-256 hash only; successful official validator wrapper path no longer records unknown commit.
coverage_rules_still_gap:
  - PG-VALIDATOR-001 remains validator_backed in the machine-readable coverage ledger until behavioral coverage fixture-family binding supports runner tests and a repaired CI run passes.
  - PG-ADAPTER-001 remains validator_backed until PROMPT-04 adds real official CE→Builder adapter execution evidence and a repaired CI run passes.
  - PG-PROGRESS-001 remains validator_backed until repaired PR CI evidence exists and PROMPT-06 adds full Persian RTL/LTR report UX fixtures.
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
  - .github/workflows/validate.yml runs python scripts/check-runner-boundary.py.
  - .github/workflows/validate.yml runs pytest tests/runners.
  - .github/workflows/validate.yml runs pytest tests/progress.
  - .github/workflows/validate.yml runs pytest tests/boundary.
  - .github/workflows/validate.yml keeps existing behavioral coverage validator and fixture validation steps.
important_design_decisions:
  - Only src/ev4_transition/runners/ imports and calls subprocess for official specialist tools.
  - src/ev4_transition/validator_runner.py remains as compatibility wrapper for existing Architect→CE CLI behavior and delegates to runners.
  - src/ev4_transition/validator_runner.py now imports ARCHITECT_COMMIT and CE_COMMIT from external_lock instead of using UNKNOWN_COMMIT.
  - Adapter command binding is enforced before subprocess execution; adapter_path existence alone is not enough evidence.
  - Runner records store stdout_hash/stderr_hash, not raw stdout/stderr.
  - Timeouts, missing commands, missing validators/adapters, adapter command mismatches, and unparseable output are fail-closed and never accepted.
  - Fallback adapter use is invalid and emits PG.ADAPTER.FALLBACK_FORBIDDEN.
  - Progress events are runtime/UI artifacts and are deliberately excluded from canonical final result hashing.
  - Repo access is local-only and mockable in Phase 1; remote connector behavior remains outside deterministic core.
  - PROMPT-03 intentionally does not implement CE→Builder, Builder→Responsive, final gate, or specialist business logic.
web_sources_used: []
next_allowed_prompt: PROMPT-04 after a repaired current PR head CI is green and owner accepts/merges this PR; otherwise fix remaining PROMPT-03 CI/test failures first.
blocking_issues:
  - GitHub Actions run 28719839833 failed on old head 7998116340c29e0fc21889c83c90ce6faafbc816.
  - Full raw pytest traceback was truncated in available tool output; exact original failing assertion remains insufficient_evidence.
  - Repaired post-620ac6a head CI is not yet evidenced.
remaining_insufficient_evidence:
  - Current repaired PR/head CI result for PROMPT-03 additions and Inspector repairs.
  - Full live branch pytest result after Inspector repairs.
  - Static runner-boundary scanner result after Inspector repairs.
  - Real CE-to-Builder downstream rejection evidence.
  - Real Builder-to-Responsive downstream rejection evidence.
  - Official Builder adapter execution evidence.
  - Official Responsive validation evidence.
  - Final evidence gate policy, fixtures, and CI evidence.
inspector_red_findings:
  PRF-001:
    status: partially_addressed
    note: Failing CI was recorded honestly; repaired head CI still needs evidence.
  PRF-002:
    status: addressed_in_code
    note: UNKNOWN_COMMIT removed; Architect/CE validator wrapper uses ARCHITECT_COMMIT and CE_COMMIT from external_lock; tests added.
  PRF-003:
    status: addressed_in_code
    note: Adapter command must invoke declared adapter_path directly or through trusted interpreter; mismatch diagnostic and tests added.
  PRF-004:
    status: addressed_in_handoff
    note: Failed run 28719839833 and pending repaired-head CI are now recorded.
