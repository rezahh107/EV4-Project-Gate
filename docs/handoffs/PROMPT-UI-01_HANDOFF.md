# PROMPT-UI-01 Handoff — Local Operator Panel

```yaml
prompt: UI operator panel prompt 1 of 3
repair_prompts:
  - UI operator panel repair
  - UI runtime smoke evidence repair
branch: ui/operator-panel
pull_request: 28
base_branch: main
reviewed_head_before_runtime_smoke: 84221ea0c5fa2decfa5cb3462e84d2ed15e1f679
status: ui_runtime_smoke_added_pending_current_head_ci
metadata_mode: historical_handoff_snapshot
live_status_source: GitHub PR checks for the current PR head
service_integration_status: pending
```

## Branch

- `ui/operator-panel`

## Pull request

- PR: `#28` — `Add local Project Gate operator UI`
- Base: `main`
- Head: `ui/operator-panel`

## Metadata note

This handoff is a historical implementation and repair snapshot. It must not be treated as the live CI oracle after later documentation-only or smoke-evidence commits. Read the current PR head and GitHub Actions checks for live merge evidence.

## Commits

- Branch was `17` commits ahead of `main` before the first UI repair.
- First repair commits added focused changes for dependency scope, UI input guard rails, docs, and tests.
- Runtime smoke repair added a focused GitHub Actions workflow to install the optional `ui` extra and construct the Gradio app without launching a server.
- Latest commit SHAs and final CI conclusions must be read from PR `#28` checks for the current head.

## Files changed

- `.github/workflows/validate.yml`
- `.github/workflows/ui-runtime-smoke.yml`
- `src/ev4_transition/ui/__init__.py`
- `src/ev4_transition/ui/app.py`
- `src/ev4_transition/ui/state.py`
- `src/ev4_transition/ui/adapters.py`
- `src/ev4_transition/ui/components.py`
- `tests/ui/test_operator_panel.py`
- `docs/UI_OPERATOR_PANEL.md`
- `docs/UI_UX_TRACEABILITY.md`
- `docs/handoffs/PROMPT-UI-01_HANDOFF.md`
- `pyproject.toml`
- `README.md`
- `AGENTS.md`
- `docs/IMPLEMENTATION_STATUS.yaml`
- `src/ev4_transition/data/capability-status.v1.json`

## Scope implemented

- Added local Gradio operator panel composition in `src/ev4_transition/ui/app.py`.
- Added UI-safe adapter boundary in `src/ev4_transition/ui/adapters.py`.
- Added Persian status summary, diagnostics rows, capability rows, and LTR-isolation helpers.
- Added JSON upload/paste support with malformed JSON fail-closed behavior.
- Added local path guards for repository checkout paths.
- Added read-only capability inspector.
- Added downloadable `result.json`, `report.md`, and `report.html` generation through existing report renderers.
- Added tests for UI helper/adapter behavior.
- Added CI execution for `pytest tests/ui` in `Skeleton Health`.
- Added CI runtime smoke for optional `.[dev,ui]` install and `build_demo()` construction without calling `launch()`.

## Repair changes

- Removed `gradio>=4,<6` from mandatory `[project].dependencies`.
- Kept `gradio>=4,<6` under `[project.optional-dependencies].ui`.
- Kept `ev4-project-gate-ui` entry point; `src/ev4_transition/ui/app.py` fails clearly if `gradio` is missing.
- Updated UI install docs to use `python -m pip install -e '.[dev,ui]'`.
- Added fail-closed `UI_INPUT_INVALID_TYPE` for JSON values that are valid JSON but not objects.
- Added fail-closed `UI_PROJECT_GATE_SCHEMA_ROOT_INVALID` when the Project Gate root lacks the expected `schemas/stage-bundle/stage-bundle.v1.schema.json` file.
- Made `ltr_token(...)` return `""` for `None` and stringify non-string values before LTR isolation.
- Expanded `tests/ui/test_operator_panel.py` for the repair cases.
- Added `.github/workflows/ui-runtime-smoke.yml` to prove optional Gradio install/build evidence in CI.

## Not changed

- Transition engine semantics.
- Official specialist validators/adapters.
- Lock manifests.
- Specialist schemas.
- Transition result schemas.
- CE constructability logic.
- Builder runtime logic.
- Responsive repair logic.
- Public CLI transition exposure.
- Service-layer files from PR `#29`.
- Browser automation, visual QA, accessibility QA, export validation, frontend correctness, production readiness, or real Elementor validation claims.

## Capability truth change rationale

`src/ev4_transition/data/capability-status.v1.json`, `docs/IMPLEMENTATION_STATUS.yaml`, `README.md`, and `AGENTS.md` were updated in the original UI prompt because the active capability source previously said `user_interface.status: not_implemented`. The value is limited to `implemented_initial_operator_panel` and does not claim service-layer wiring for all transitions.

## Coverage rules advanced

| Rule | Status |
|---|---|
| malformed JSON safe error | ci_enforced |
| non-object JSON safe error | ci_enforced |
| missing Project Gate schemas root safe error | ci_enforced |
| status mapping for accepted/invalid/insufficient_evidence/repair_needed | ci_enforced |
| diagnostics preserve code/severity/path | ci_enforced |
| LTR isolation and None-safe technical tokens | ci_enforced |
| capability inspector read-only | ci_enforced |
| unavailable transitions do not fake execution or return accepted | ci_enforced |
| report/result rendering does not mutate result object | ci_enforced |
| Gradio remains optional UI extra | ci_enforced |
| optional `.[dev,ui]` install and Gradio `build_demo()` construction | ci_pending_for_current_head |

## Coverage rules still gap

| Rule | Gap |
|---|---|
| browser-level UI accessibility | not validated by browser automation |
| browser visual behavior | not validated by browser automation or manual visual run in this prompt |
| `python -m ev4_transition.ui.app` long-running launch | not executed because smoke must not launch a server |
| CE→Builder UI execution | pending service-layer integration after PR #29 path is intentionally adopted |
| Builder→Responsive UI execution | pending service-layer integration after PR #29 path is intentionally adopted |
| Final Evidence Gate UI execution | pending service-layer integration after PR #29 path is intentionally adopted |
| packaging/user run polish | pending Prompt 3 |

## New diagnostics

- `MALFORMED_JSON`
- `UI_INPUT_REQUIRED`
- `UI_INPUT_INVALID_TYPE`
- `UI_TRANSITION_NOT_WIRED`
- `UI_PROJECT_GATE_SCHEMA_ROOT_INVALID`
- `UI_LOCAL_PATH_REQUIRED`
- `UI_LOCAL_PATH_NOT_URL`
- `UI_LOCAL_PATH_NOT_FOUND`
- `LOCAL_PATH_READ_ERROR`
- `TRANSITION_RESULT_SCHEMA_VALIDATION_FAILED`

## CLI / CI changes

- Added optional local UI entry point: `ev4-project-gate-ui`.
- Did not expose new public Project Gate transition commands.
- Added `Operator UI adapter tests` step to `.github/workflows/validate.yml` because otherwise the new UI tests would not be CI-enforced.
- Added `UI Runtime Smoke` workflow that runs:
  - `python -m pip install -e '.[dev,ui]'`
  - imports `build_demo()` from `ev4_transition.ui.app`
  - constructs the demo object
  - asserts it has `launch`
  - does not call `launch()`

## Tests run

GitHub Actions before runtime smoke repair, PR `#28`, head `84221ea0c5fa2decfa5cb3462e84d2ed15e1f679`:

- `Skeleton Health` run `28780835147`: success.
- `Prompt 05 Builder Responsive Final Gate` run `28780835158`: success.
- `Prompt 06 Report UX` run `28780835247`: success.

Local/container attempt from the original UI prompt:

```bash
git clone --branch ui/operator-panel --single-branch https://github.com/rezahh107/EV4-Project-Gate.git /tmp/EV4-Project-Gate-ui
```

Result: failed because the execution container could not resolve `github.com`.

Runtime smoke validation for the current head must be read from the `UI Runtime Smoke` GitHub Actions workflow after this handoff update.

## Tests not run

- Browser-driven Gradio UI testing was not run.
- Manual visual inspection of the live UI was not performed.
- Optional UI launch command `python -m ev4_transition.ui.app` was not executed because it would start a long-running Gradio server.
- Local `python -m pip install -e '.[dev,ui]'` was not executed in this ChatGPT container.

## Important design decisions

- UI event handlers delegate to `ui.adapters` and do not contain transition business logic.
- The UI uses direct Python calls rather than subprocess CLI calls.
- Only `Validate Stage Evidence Bundle`, `Architect → CE`, and `Inspect Capabilities` are wired.
- CE→Builder, Builder→Responsive, and Final Evidence Gate remain `insufficient_evidence` / not wired in this repair.
- PR `#29` was inspected only for service contract compatibility context; no service files were modified here.
- Reports reuse `src/ev4_transition/reports/` renderers.
- Result objects are deep-copied before report rendering.
- Runtime smoke evidence intentionally proves install/import/build only, not visual/browser/accessibility readiness.

## Web sources used

- None. The implementation followed live repository files, the PR review report, PR checks, and uploaded Project rules.

## Next allowed prompt

- Service-layer adoption/integration after PR `#29` is intentionally available to this branch, or Prompt 3 packaging/run-script work after this PR is merged.

## Blockers

- Current-head CI must complete for `UI Runtime Smoke` before this PR can be considered re-review ready.
- No merge to `main`; PR remains open.

## Remaining insufficient_evidence

- real non-synthetic CE→Builder handoff evidence
- real Builder execution evidence bundle
- real Responsive input/output evidence bundle
- accessibility/export/frontend correctness evidence
- downstream owner rejection evidence for downstream-contract-enforced claims
