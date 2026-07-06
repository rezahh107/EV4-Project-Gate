# PROMPT-06 Handoff

## Patch 4 — Final Operator Panel UX Hardening

```yaml
patch_id: PROMPT-06-UI-PATCH-4
branch: ux/operator-panel-final-hardening-patch-4
pull_request: 38
base_branch: main
base_context:
  patch_3_pr: 37
  patch_3_status: merged
files_changed:
  - src/ev4_transition/presentation/rtl.py
  - src/ev4_transition/presentation/bidi.py
  - src/ev4_transition/presentation/__init__.py
  - src/ev4_transition/presentation/theme_tokens.py
  - src/ev4_transition/ui/preflight_components.py
  - src/ev4_transition/ui/adapters.py
  - tests/service/test_operator_panel_final_guidance.py
  - tests/presentation/test_rtl_contract.py
  - tests/theme_acceptance/test_operator_panel_theme_contract.py
  - tests/ui/test_preflight_final_contract.py
  - docs/OPERATOR_PANEL_UX_CONTRACT.md
  - docs/OPERATOR_PANEL_MANUAL_QA.md
  - docs/PERSIAN_RTL_UI_CONTRACT.md
  - docs/VISUAL_THEME_CONTRACT.md
  - docs/DIAGNOSTIC_GUIDE.md
  - docs/UI_SERVICE_CONTRACT.md
  - docs/handoffs/PROMPT-06_HANDOFF.md
commits_created_before_this_handoff:
  - 769e035b2949ae603a5bb21d7121ee1939181e79
  - 3a4a225048f603739f62ef7350a74d2611011a8e
  - 2dee7b2a689952652b2cbd6a6add238eaf1770e9
  - 218a97c536fb994cad1ca8be8bfce8da8a32f51b
  - 13dc2cfde30d9df3ed6787bec80369b555a667a0
  - 45f6e86ecec2b8bd4677aa0547eb899916bf0832
  - 1701e32266bf4753dcbc48bddd37fc44f774d8cb
  - 0271e8a64a541f05b6d9bfec02bc7503708627b7
  - f69b24f988dea4e712fa7e5d277d4112c91f4f79
  - 039efaaa01815d287eb49c53dec99a8628fe2036
  - 2c7d13ed9dc8dfe5b941433b52b5e1c1a850339f
  - 96147e3555a80c2b9fa73c043017c36c5ae56ca8
  - 2f4136c63f077e72c48c665440bc109ec37f19af
  - d3afe21f1ebbd87ee7bd1cb3d8bc2d5d2f30e4ad
  - ff20741386e9288e0b35163e796897a43bc39999
  - 16868ef971e4e95c1da117ed6053da720d074e1d
  - 5d283368f70bd174525ced673694d88932a977d0
tests_run:
  - local syntax check in sandbox on generated Python patch files: python -m py_compile /mnt/data/patch4/*.py
tests_not_run:
  - python -m pytest -q
  - python -m pytest -q tests/ui tests/service tests/presentation
  - browser launch / screenshot QA
  - GitHub Actions CI result for this branch at handoff time
coverage_rules_advanced:
  - PG-UNICODE-001: added centralized RTL helper contract tests and report/preflight LTR isolation tests.
  - PG-OUTPUT-001: added final output-state regression tests for validation-only, output null, and CE output produced language.
  - PG-GUIDANCE-001: added required diagnostic guidance coverage test for known operator diagnostics.
  - PG-REPORT-001: strengthened report artifact expectations for operational guidance, grouped diagnostics, raw diagnostics, and raw JSON LTR code blocks.
  - PG-THEME-001: added final theme token contract tests for semantic tokens, status icon/label/tone, focus ring, code background, and non-inversion dark mode.
coverage_rules_still_gap:
  - Browser visual QA remains manual, not screenshot-test enforced.
  - Accessibility completion remains insufficient_evidence; keyboard/focus sanity is documented for manual QA only.
  - Real Elementor/frontend/responsive readiness remains out of scope and insufficient_evidence.
new_diagnostics:
  - none; no transition diagnostic semantics changed.
cli_or_ci_changes:
  - none.
important_design_decisions:
  - Created src/ev4_transition/presentation/rtl.py as the small shared presentation helper module.
  - Kept src/ev4_transition/presentation/bidi.py as a compatibility wrapper to avoid breaking existing imports.
  - Hardened UI report artifacts without changing run_gate_request, transition execution, schema validation, canonical JSON, hash behavior, or status mapping.
  - Added docs/OPERATOR_PANEL_UX_CONTRACT.md as the final UX SSOT for the local operator panel.
  - Added docs/OPERATOR_PANEL_MANUAL_QA.md for final human QA before personal local operation.
web_sources_used:
  - none.
repository_sources_inspected:
  - README.md
  - src/ev4_transition/ui/app.py
  - src/ev4_transition/ui/adapters.py
  - src/ev4_transition/ui/components.py
  - src/ev4_transition/ui/state.py
  - src/ev4_transition/service/dispatcher.py
  - src/ev4_transition/service/repo_paths.py
  - src/ev4_transition/service/guidance.py
  - src/ev4_transition/service/preflight.py
  - src/ev4_transition/service/preflight_core.py
  - src/ev4_transition/presentation/theme_tokens.py
  - src/ev4_transition/presentation/bidi.py
  - src/ev4_transition/data/operator-guidance.v1.json
  - contracts/locks/architect-to-ce-transition.v1.lock.json
  - docs/UI_OPERATOR_PANEL.md
  - docs/UI_SERVICE_CONTRACT.md
  - docs/OPERATOR_GUIDE.md
  - docs/DIAGNOSTIC_GUIDE.md
  - docs/LOCAL_REPOSITORY_PREFLIGHT.md
  - tests/service/test_operator_guidance.py
  - tests/service/test_preflight.py
  - tests/ui/test_preflight_rendering.py
  - tests/theme_acceptance/test_operator_panel_theme_tokens.py
next_allowed_prompt: PROMPT-06 patch review after PR CI evidence, then PROMPT-07 closure audit
blockers:
  - full pytest and browser launch were not executed from this connector environment.
  - CI status must be checked on PR 38 before merge.
remaining_insufficient_evidence:
  - production readiness
  - real Elementor validation
  - frontend correctness
  - responsive correctness
  - accessibility completion
  - browser screenshot QA
  - real non-synthetic downstream evidence for later transition claims
```

## Scope note

Patch 4 intentionally does not change Project Gate validation logic, transition behavior, schema rules, canonical JSON behavior, hashing, status mapping, official specialist validators, specialist repository contracts, or owner adapter semantics.
