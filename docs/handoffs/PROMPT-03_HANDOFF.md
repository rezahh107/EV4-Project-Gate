prompt_id: PROMPT-03
branch: project-gate-prompt-03-runner-boundary
commits:
  - 0d22d2962d690d2308accc832b4d493ce05f14d5: feat(runners): add official tool execution records
  - 73029e67afdb38a023e14a7ac23c8279da5480ca: feat(runners): map official tool failures deterministically
  - b885273020c819a50f7f8a1c5902738b12fdf87f: feat(progress): add sanitized progress events
  - af1cdf816bfc9b043f3f9418f1b4f2029c4742be: feat(progress): export progress sanitization API
  - 3b55a86c5992d5092616dc777d7afbe9a0130d8e: feat(runners): add subprocess runner boundary
  - e18dd82647c3e1da829f2f6c449c51e18393f223: feat(runners): add official validator and adapter helpers
  - c28f209765f2da9d98d1d113e539cc85808641df: feat(runners): export runner boundary API
  - f4433caae7ae30a65054133234fb2d06297edf47: feat(repo-access): add mockable repo access ports
  - b152446f5c63e713197e9642a0ff96c0d557c6c0: feat(repo-access): add local-only repo access
  - 5ad017ba8977cd16bee44c90942e522e654d51a0: docs(repo-access): reserve remote repo placeholder
  - a2283b4ad9d2b2999358ab81de4cd5c1af685b8a: feat(repo-access): export repo access API
  - c79827c55e938bb86672da24f955717d438d09db: refactor(runners): route validator execution through runner boundary
  - ad430869110449fa6cce73fb50e86d74b4cd9227: feat(boundary): add static runner boundary scanner
  - 3c50f0779d7bf52a406b6175a6b86ea7df3d3fc6: test(runners): cover fail-closed official tool execution
  - 6dd8c3f66d4e35ca59f62e976e1e3d0ef442f4ac: test(progress): cover sanitized progress events
  - d0e2cfb2c436dd914acfd389bcac3bcac3bc881a4c432: test(boundary): cover static runner boundary scanner
  - 328242924db1a26cdb512159b50618c5016a054c: ci(runners): run runner boundary and progress tests
  - cac368142f81b1411823878d57fddb8a032030de: docs(boundary): document runner execution boundary
  - de86c54cfe5156b3e2e8888c6dfe36085198311a: docs(result): document official tool execution records
  - de13fd28ef0335ac4b8180f6f1281ecc16735a46: docs(coverage): record runner boundary coverage state
  - handoff_creation_commit: reported by GitHub contents API in final response
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
tests_run:
  - local synthetic-tree subset in ChatGPT container: PYTHONPATH=src pytest -q -> 19 passed
  - live GitHub file fetch sanity check after branch update: docs/BEHAVIORAL_RULE_COVERAGE.md ref project-gate-prompt-03-runner-boundary returned PROMPT-03 content
tests_passed:
  - local synthetic-tree subset: 19 passed
  - static/source syntax indirectly covered in local synthetic subset for new modules and tests
tests_failed: []
tests_not_run:
  - full live repository clone/install: not run because container network could not resolve github.com
  - python -m pip install -e '.[dev]' against live branch
  - full live branch pytest
  - python scripts/check-runner-boundary.py against a live clone
  - ev4-transition coverage validate docs/BEHAVIORAL_RULE_COVERAGE.md against a live clone
  - npm run status
  - npm run validate
  - GitHub Actions current PR/head checks: pending until draft PR/checks run
coverage_rules_advanced:
  - PG-BOUNDARY-001: static runner boundary scanner added; src/ev4_transition/validator_runner.py no longer imports/calls subprocess directly; CI step references added.
  - PG-VALIDATOR-001: official validator execution API added under src/ev4_transition/runners/ with fail-closed mappings for missing, timeout, command not found, unparseable output, repair-needed, contract violation, and execution failure.
  - PG-ADAPTER-001: official adapter execution API added under src/ev4_transition/runners/ with missing/timeout fail-closed behavior and explicit fallback adapter rejection.
  - PG-PROGRESS-001: sanitized runtime progress events added; token/env/stdout/stderr/private absolute path leakage is rejected; progress is excluded from canonical result hash.
  - PG-EVIDENCE-001: execution record carriers added for official tool execution evidence; stdout/stderr are recorded by SHA-256 hash only.
coverage_rules_still_gap:
  - PG-VALIDATOR-001 remains validator_backed in the machine-readable coverage ledger until behavioral coverage fixture-family binding supports runner tests and CI evidence exists.
  - PG-ADAPTER-001 remains validator_backed until PROMPT-04 adds real official CE→Builder adapter execution evidence.
  - PG-PROGRESS-001 remains validator_backed until PR CI evidence exists and PROMPT-06 adds full Persian RTL/LTR report UX fixtures.
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
  - Runner records store stdout_hash/stderr_hash, not raw stdout/stderr.
  - Timeouts, missing commands, missing validators/adapters, and unparseable output are insufficient_evidence, never success.
  - Fallback adapter use is invalid and emits PG.ADAPTER.FALLBACK_FORBIDDEN.
  - Progress events are runtime/UI artifacts and are deliberately excluded from canonical final result hashing.
  - Repo access is local-only and mockable in Phase 1; remote connector behavior remains outside deterministic core.
  - PROMPT-03 intentionally does not implement CE→Builder, Builder→Responsive, final gate, or specialist business logic.
web_sources_used: []
next_allowed_prompt: PROMPT-04 after current PR head CI is green and owner accepts/merges this PR; otherwise fix PROMPT-03 CI/test failures first.
blocking_issues:
  - Full live-repo tests were not run locally because clone/install was unavailable in the container.
  - GitHub Actions evidence is pending until draft PR/checks run.
remaining_insufficient_evidence:
  - Current PR/head CI result for PROMPT-03 additions.
  - Real CE-to-Builder downstream rejection evidence.
  - Real Builder-to-Responsive downstream rejection evidence.
  - Official Builder adapter execution evidence.
  - Official Responsive validation evidence.
  - Final evidence gate policy, fixtures, and CI evidence.
