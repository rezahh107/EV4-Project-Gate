# Prompt 06 UI UXIS/DMDS Completion Handoff

## Branch

`project-gate-prompt-06-ui-uxis-dmds-completion`

## Inspected baseline

Initial inspected commit before edits: `5fcffd26149602bed715c5ee77e4d361d18a602e`.

## Scope completed

- Refactored normal operator-panel execution to build `GateRequest` and call `run_gate_request(...)` from the internal service layer.
- Exposed service choices: `validate_bundle`, `inspect_capabilities`, `architect_to_ce`, `ce_to_builder`, `builder_to_responsive`, and `final_gate`.
- Kept missing local checkout paths, GitHub URL paths, and missing evidence fail-closed through service diagnostics; no placeholder accepted state is produced.
- Added scoped Gradio CSS backed by semantic theme tokens, Persian UI font stack, code font stack, focus ring, RTL container behavior, and LTR technical isolation.
- Preserved Advanced/Evidence/Diagnostics as collapsed UI details, added safer report-write failure behavior, escaped serialized JSON in `report.html` to prevent local/report HTML injection, neutralized Markdown code-fence breakout in `report.md`, made artifact writes transactional, and logged defensive UI/report/finalization failures without exposing raw tracebacks in the primary UI.
- Updated CI prompt workflow to enforce UI and service tests along with UX/theme/typography/reporting checks, and to verify the exact checked-out source head for pull requests.

## Files changed

- `src/ev4_transition/ui/adapters.py`
- `src/ev4_transition/ui/app.py`
- `src/ev4_transition/ui/components.py`
- `src/ev4_transition/ui/state.py`
- `src/ev4_transition/presentation/theme_tokens.py`
- `src/ev4_transition/data/capability-status.v1.json`
- `tests/ui/test_operator_panel.py`
- `.github/workflows/prompt-06.yml`
- `docs/UI_OPERATOR_PANEL.md`
- `docs/UI_UX_TRACEABILITY.md`
- `docs/STANDARDS_TRACEABILITY.md`
- `docs/IMPLEMENTATION_STATUS.yaml`
- `docs/handoffs/PROMPT-06_UI_UXIS_DMDS_COMPLETION_HANDOFF.md`

## Tests run

- `python -m pip install -e '.[dev]'`
- `pytest tests/ui/test_operator_panel.py`
- `pytest tests/ui tests/service tests/theme_acceptance tests/typography_acceptance tests/ux_acceptance tests/reporting`
- `python scripts/check-capability-truth.py`
- `python scripts/check-workflow-permissions.py`
- `python scripts/check-github-action-pinning.py`
- `python -m pip install -e '.[dev,ui]'`
- `python - <<'PY' ... build_demo() ... PY`
- `pytest`

## Tests not run

- No long-running Gradio `launch()` server test was run.
- No browser/manual accessibility test was run; browser-level accessibility remains `insufficient_evidence`.
- No real non-synthetic EV4 handoff was executed.

## Coverage rules advanced

- UI/service route coverage: `fixture_tested` and CI-enforced in `prompt-06.yml` for adapter and service tests.
- Static DMDS token and CSS coverage: `ci_enforced` for token existence/non-inversion/focus/font assertions.
- Static TYPEKIT/RTL/LTR coverage: `ci_enforced` for helpers, CSS strings, and UI markup carriers.

## Coverage rules still gap

- Browser visual behavior: `prose_only` / `insufficient_evidence` until browser or manual evidence exists.
- Accessibility completion: `insufficient_evidence` without browser/manual QA evidence.
- Real Elementor validation, frontend correctness, responsive correctness, production readiness, and export validation: `insufficient_evidence`.

## New diagnostics

- `PG.UI.UNHANDLED_EXCEPTION`
- `PG.UI.REPORT_WRITE_FAILED`
- `PG.UI.CRITICAL_FINALIZATION_FAILURE`

## CLI/CI changes

No public CLI transition was added or renamed. `.github/workflows/prompt-06.yml` now runs `pytest tests/ui` and `pytest tests/service` and includes this branch name in push triggers.

## Design decisions

- Unhandled UI exceptions are logged with traceback for maintainers while the primary Persian UI remains sanitized. Finalization failures are caught by `PG.UI.CRITICAL_FINALIZATION_FAILURE` and return a minimal invalid UI output instead of crashing the panel.
- The UI adapter now delegates JSON parsing, repo-path validation, transition dispatch, capability inspection, and fail-closed behavior to `ev4_transition.service` instead of shelling out or duplicating transition logic. Packaged runtime capability truth now carries `user_interface.service_routing` and `browser_accessibility_evidence` so the UI inspector and active docs do not drift.
- Download files are written only if report artifacts can be written. A write failure returns an invalid UI result, logs the failure, removes partially written files for manual or temporary output directories, cleans up auto-created temporary directories, and produces no fake success download list. HTML report JSON is escaped with `html.escape(...)` before being embedded in `<pre>`, and Markdown report JSON neutralizes embedded triple-backtick fences without mutating `result.json`.
- Scoped CSS uses semantic `--ev4-*` variables and `prefers-color-scheme`; no persistence claim is made.

## Web sources used

None.

## Current remaining insufficient_evidence

- Real non-synthetic Architect→CE, CE→Builder, Builder→Responsive, and Final Evidence Gate handoffs remain insufficient evidence according to active capability truth.
- Browser-level accessibility and visual rendering remain insufficient evidence.
- Real Elementor artifact validation and export validation remain insufficient evidence.

## Next safe prompt/action

Run browser/manual accessibility QA against the local operator panel, capture evidence, and update traceability only for rules with actual evidence.

## Blockers

No local implementation blocker remains for internal service routing. Broader readiness claims are blocked by missing real owner evidence and missing browser/manual QA evidence.
