# PROMPT-02 Service Layer Handoff

```yaml
prompt_id: PROMPT-02-service-layer
branch: feature/gate-service-api
status: repaired_and_ci_verified
head_before_repair: 994d1c0b628d6da61073e5f866d7cecbfaaeab13
head_after_repair_before_handoff_update: 210fdb077a84ded03d606cfd58e9a7bb5f5e0c07
scope: internal_python_service_api_for_future_operator_ui
```

## Branch

```text
feature/gate-service-api
```

Created from `main` through the GitHub connector. No direct commit to `main` was made.

## Commits

Initial service-layer commits on this branch:

```text
45b2136f96d4920c7701e1c471e801ebdab35d40 Add Project Gate service package exports
cabbb643fbf8f579c9b263e6879806e566ba65c2 Add Project Gate service models
b6c7acd767bc890bb844efacda7bbda7274dbddd Add service JSON input parsing
2388bf2ff4587b94be71c018f5d4f18319568976 Add local repo path validation for service
3029cd7daaf332d57d2aa1b165f14db9d4319ba1 Add read-only service capability loader
1ac36d907fe0068dafb0480dcbe21ce51eef028d Add service report bundle builder
fe3ba2344817a7a9bc06b32710ec032a7df77f44 Add service dispatcher for direct Python gate calls
860d8c436f256091e9895d8af0286a278a544e18 Add service layer tests
656c8ac312b1a6a99c1150062e9126d562d697fe Document Project Gate service layer
60a04a9adfdaf4c614e65c7cff18199ddf6d77dd Document UI service integration contract
994d1c0b628d6da61073e5f866d7cecbfaaeab13 Add service layer handoff
```

Repair commits:

```text
da69cd4119b19a2f9bde555f64042a393c17423b Fail closed service report rendering
a028b50b8c546a114478162da5951bd1aa0a3580 Harden service JSON input parsing
7c00f53c2c5337a631ef9699672a0d1be2487cc3 Fail closed service repo path validation
3a7e1e9608ebda48e6ef56b30748d05db66dadbd Add service robustness regression tests
e8825fa61705e97401af0810242c33657045f191 Run service tests in CI
210fdb077a84ded03d606cfd58e9a7bb5f5e0c07 Stabilize service robustness tests
```

## Files changed

```text
.github/workflows/validate.yml
docs/SERVICE_LAYER.md
docs/UI_SERVICE_CONTRACT.md
docs/handoffs/PROMPT-02_SERVICE_LAYER_HANDOFF.md
src/ev4_transition/service/__init__.py
src/ev4_transition/service/models.py
src/ev4_transition/service/json_input.py
src/ev4_transition/service/repo_paths.py
src/ev4_transition/service/capabilities.py
src/ev4_transition/service/dispatcher.py
src/ev4_transition/service/reports.py
tests/service/test_service_layer.py
```

## Tests run

GitHub Actions for head `210fdb077a84ded03d606cfd58e9a7bb5f5e0c07`:

```text
Skeleton Health run 28781438379: success
Prompt 05 Builder Responsive Final Gate run 28781438404: success
Prompt 06 Report UX run 28781438466: success
```

Important verified `Skeleton Health` jobs/steps:

```text
skeleton job: success
python-core job: success
Service layer tests: success
CLI and bundle tests: success
A2C transition tests: success
Runner tests: success
CE-to-Builder transition pytest: success
Prompt-05 transition tests: success
Behavioral coverage validator: success
Behavioral fixture validation: success
CE-to-Builder lock verification: success
CE-to-Builder live owner tool smoke: success
CLI smoke tests: success
Official Architect validator fixture suite: success
Official CE validator fixture suite: success
Generated Architect-to-CE transition smoke and CE binding: success
```

## Tests not run locally

The requested local commands were not run in this ChatGPT container because direct repository network access was unavailable:

```text
python -m pip install -e '.[dev]'
pytest tests/service
pytest
python scripts/check-capability-truth.py
python scripts/check-workflow-permissions.py
npm run status
npm run validate
```

Evidence: `git ls-remote https://github.com/rezahh107/EV4-Project-Gate.git HEAD` failed with DNS resolution error for `github.com`.

## Coverage rules advanced

```yaml
service_json_input:
  status: ci_enforced
  notes: malformed JSON, missing JSON, file read ValueError, and non-finite JSON constants are covered by tests/service and CI.
service_repo_paths:
  status: ci_enforced
  notes: missing required paths, GitHub URL rejection, and inaccessible path exceptions are covered by tests/service and CI.
service_dispatcher:
  status: ci_enforced
  notes: transition dispatch boundaries are monkeypatched to prove direct Python calls without CLI dependency.
service_reports:
  status: ci_enforced
  notes: renderer exception fallback and result immutability are covered by tests/service and CI.
service_ci:
  status: ci_enforced
  notes: .github/workflows/validate.yml now runs pytest tests/service.
```

## Rules still gap

```yaml
real_external_repo_execution:
  status: insufficient_evidence
  reason: no real non-synthetic owner handoff evidence was supplied for this service-layer PR.
operator_ui_integration:
  status: prose_only
  reason: Prompt 1 owns UI implementation.
personal_packaging_examples:
  status: prose_only
  reason: Prompt 3 owns packaging, examples, run scripts, and demo workflow.
```

## New diagnostics

```text
PG.SERVICE.JSON_INPUT_MISSING
PG.SERVICE.JSON_INPUT_AMBIGUOUS
PG.SERVICE.MALFORMED_JSON
PG.SERVICE.NON_FINITE_JSON_CONSTANT
PG.SERVICE.FILE_READ_ERROR
PG.SERVICE.REPO_PATH_MISSING
PG.SERVICE.REPO_PATH_NOT_LOCAL
PG.SERVICE.REPO_PATH_DOES_NOT_EXIST
PG.SERVICE.REPO_PATH_NOT_DIRECTORY
PG.SERVICE.REPO_PATH_INACCESSIBLE
PG.SERVICE.TRANSITION_UNKNOWN
PG.SERVICE.RESULT_SCHEMA_VALIDATION_FAILED
PG.SERVICE.LOCAL_FILE_ACCESS_FAILED
PG.SERVICE.ENGINE_EXECUTION_FAILED
PG.SERVICE.REPORT_JSON_RENDER_FAILED
```

## CLI / CI changes

```yaml
public_cli_changes: none
ci_changes:
  - .github/workflows/validate.yml adds Service layer tests step: pytest tests/service
```

No new public CLI transitions were exposed.

## Review comments repaired

```yaml
reports_py_fail_closed_rendering: repaired
repo_paths_exception_safe_path_checks: repaired
json_input_value_error_file_read: repaired
non_finite_json_constants: repaired
```

## Important design decisions

- Plain Python service API; no FastAPI, database, login, or cloud dependency.
- The UI calls `run_gate_request(...)` directly.
- `validate_bundle` uses `BundleValidator` directly.
- Transition choices call existing Python boundaries directly, not the public CLI.
- Missing local owner checkouts return `insufficient_evidence` before engine execution.
- JSON file/text input rejects `NaN`, `Infinity`, and `-Infinity` with a structured invalid diagnostic.
- JSON input is deep-copied and not mutated.
- Report generation deep-copies the engine result and now fails closed for renderer exceptions.
- Service status maps legacy `valid` to service-level `accepted`, while preserving the original engine result unchanged.

## Web sources used

```yaml
web_sources_used: []
```

No web research was needed; live repository files, PR comments, CI output, and uploaded Project rules were sufficient.

## Next allowed prompt

```text
Prompt 1: UI/operator panel may call this service API after PR review/merge.
Prompt 3: packaging/examples/run scripts/demo workflow may add local launch wrappers after this service API is merged or rebased.
```

## Blockers

```yaml
merge_blockers_known_from_current_branch: []
```

## Remaining insufficient_evidence

- real non-synthetic CE-to-Builder transition evidence
- real Builder execution evidence bundle
- real Responsive input/output evidence bundle
- accessibility/export/frontend correctness evidence
- downstream owner rejection evidence
- real UI/operator panel integration evidence
- personal-use packaging/demo evidence
