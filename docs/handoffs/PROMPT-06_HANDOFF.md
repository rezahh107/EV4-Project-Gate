# PROMPT-06 Handoff

## Patch 3 — Local Repository Preflight Setup Assistant

```yaml
patch_id: PROMPT-06-UI-PATCH-3
branch: ux/local-repo-preflight-setup-assistant-patch-3
pull_request: 37
base_branch: main
base_head_sha: 7a8d7ea7b3e199bd8e1d4cd7b0c5a5e690fa9397
files_changed:
  - src/ev4_transition/service/preflight.py
  - src/ev4_transition/service/__init__.py
  - src/ev4_transition/ui/preflight_components.py
  - src/ev4_transition/ui/app.py
  - tests/service/test_preflight.py
  - tests/ui/test_preflight_rendering.py
  - docs/LOCAL_REPOSITORY_PREFLIGHT.md
  - docs/OPERATOR_GUIDE.md
  - docs/handoffs/PROMPT-06_HANDOFF.md
tests_run:
  - local syntax check on generated patch files before repository write: python -m py_compile <generated Python files>
tests_not_run:
  - python -m pytest -q
  - targeted UI/service pytest in a live checkout
  - browser launch / screenshot QA
ci_status_at_handoff_update:
  - Skeleton Health: in_progress
  - Prompt 05 Builder Responsive Final Gate: in_progress
  - Prompt 06 Report UX: in_progress
  - UI Runtime Smoke: in_progress
coverage_rules_advanced:
  - PG-UNICODE-001: added UI rendering test for RTL Persian preflight checklist and LTR technical identifiers.
  - PG-OUTPUT-001: added validation-only warning for validate_bundle so users do not expect downstream output.
  - PG-PREFLIGHT-001: added service tests for required path selection, local path classification, pinned file existence, wrong input file type, and irrelevant path handling.
coverage_rules_still_gap:
  - Preflight is fixture-tested at service/UI unit level after CI passes; it is not downstream_contract_enforced.
  - Browser accessibility and screenshot QA remain insufficient_evidence.
new_diagnostics:
  - no deterministic engine diagnostics changed.
  - Preflight uses internal PreflightCheck ids and classifications, not transition result status semantics.
cli_or_ci_changes:
  - none
important_design_decisions:
  - Preflight is a separate read-only service layer, not part of run_gate_request decision semantics.
  - The main Project Gate run button remains available and still calls run_operator_check.
  - Preflight checks existence of pinned files from lock manifests but deliberately does not verify hashes or schema identity.
  - GitHub Desktop guidance is shown for missing pinned files.
  - Non-required paths are marked not_required_for_selected_transition and do not block Preflight.
  - Technical identifiers are rendered as LTR code fragments inside RTL Persian UI.
web_sources_used:
  - none
repository_sources_inspected:
  - src/ev4_transition/ui/app.py
  - src/ev4_transition/ui/adapters.py
  - src/ev4_transition/ui/components.py
  - src/ev4_transition/ui/state.py
  - src/ev4_transition/service/repo_paths.py
  - src/ev4_transition/service/dispatcher.py
  - src/ev4_transition/service/guidance.py
  - src/ev4_transition/data/operator-guidance.v1.json
  - src/ev4_transition/external_lock.py
  - contracts/locks/*.lock.json
  - docs/UI_SERVICE_CONTRACT.md
  - docs/OPERATOR_GUIDE.md
  - tests/ui/test_operator_panel.py
  - tests/ui/test_operator_panel_visual_polish.py
next_allowed_prompt: PROMPT-06 UI patch review or PROMPT-07 closure audit after CI evidence
blockers:
  - full pytest and browser launch not executed in this environment
remaining_insufficient_evidence:
  - real Elementor/frontend/responsive/production readiness
  - browser screenshot review
  - accessibility completion evidence
  - real non-synthetic downstream evidence for later transition claims
```

## Scope note

This patch intentionally does not change Project Gate transition logic, schema rules, canonical JSON, hashing, official specialist validators, owner contracts, or transition status mapping.

Earlier Prompt-06 and UI Patch 1/2 details remain available in repository history before this handoff rewrite.
