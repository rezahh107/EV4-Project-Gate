# PROMPT-06 Operator Guidance Patch 2 Handoff

```yaml
prompt_id: PROMPT-06
patch_id: operator-guidance-diagnostic-help-patch-2
branch: ux/operator-guidance-diagnostic-help-patch-2
base_branch: main
base_head_sha: 5a1cebcbf1c0b769690eb594a41d3e57590449b9
pull_request: pending_at_handoff_write
commits_before_handoff_write:
  - c3820e8d0c1d7cb5a84fce348430dc839359fc39
  - e7e433fdae6394efa9c5680d3c925dc8858442dd
  - 392efca50c9f3f9318d92fc11918b14db16ca95f
  - 9eb0d717622d24091422f645f4574e83563dc671
  - d7485868424d81f03a2544e357eb7a23b84840f9
  - f78bffdc58416acf52a030bbb11f7710f4df11ec
  - 95b1c95c0c6d6e4bab9e8ae7595c56e457270019
  - 27ef636d548f1bc4c8c30e54895a8875fe4a5d0d
  - f905a230a1e084cb93b034af5e3bbb255c55a56f
  - 2042ea71431ba666f6b700e1a90554b2eb133ef7
files_changed:
  - src/ev4_transition/data/operator-guidance.v1.json
  - src/ev4_transition/service/guidance.py
  - src/ev4_transition/service/__init__.py
  - src/ev4_transition/ui/adapters.py
  - src/ev4_transition/ui/components.py
  - pyproject.toml
  - tests/service/test_operator_guidance.py
  - docs/OPERATOR_GUIDE.md
  - docs/DIAGNOSTIC_GUIDE.md
  - docs/UI_OPERATOR_PANEL.md
  - docs/handoffs/PROMPT-06_OPERATOR_GUIDANCE_PATCH_2_HANDOFF.md
tests_run:
  - python -m py_compile /tmp/ev4patch/src/ev4_transition/service/guidance.py
  - python -m py_compile /tmp/ev4patch/src/ev4_transition/service/__init__.py
  - python -m py_compile /tmp/ev4patch/src/ev4_transition/ui/components.py
  - python -m py_compile /tmp/ev4patch/src/ev4_transition/ui/adapters.py
  - python -m py_compile /tmp/ev4patch/tests/service/test_operator_guidance.py
  - python -m json.tool /tmp/ev4patch/src/ev4_transition/data/operator-guidance.v1.json
tests_not_run:
  - python -m pytest -q
  - uv run pytest tests/service/test_operator_guidance.py tests/ui/test_operator_panel.py
  - UI launch smoke test in a browser
reason_tests_not_run:
  - live repository clone was unavailable in this environment because github.com DNS resolution failed
  - GitHub connector can write/read repository files but does not provide a Python test runner
coverage_rules_advanced:
  - PG-UNICODE-001: guidance/status main panel keeps Persian RTL and technical identifiers LTR via existing presentation helpers
  - PG-OUTPUT-001: output:null is classified and explained as no downstream package produced when applicable
  - PG-STATUS-001: guidance keeps accepted/repair_needed/insufficient_evidence/invalid semantically distinct
  - PG-UX-GUIDANCE-001: new code-backed guidance registry and service tests cover common operator failures
coverage_rules_still_gap:
  - no browser accessibility completion claim
  - no frontend/Elementor/responsive correctness claim
  - no downstream_contract_enforced claim
  - full pytest and CI remain pending until PR checks run
new_diagnostics:
  - PG.UI.PREFLIGHT_RESULT_JSON_USED_AS_SOURCE
  - PG.UI.PREFLIGHT_WRONG_STAGE_FOR_TRANSITION
cli_changes:
  - none
ci_changes:
  - none
important_design_decisions:
  - guidance registry is JSON-backed and deterministic, separate from transition decisions
  - guidance service summarizes result dictionaries without mutating engine results
  - UI preflight catches result.json-as-source and wrong-stage mistakes before calling the service transition path
  - existing raw diagnostics table remains available
  - repair prompt is generated only for known repairable Architect schema failures and includes paths/messages only
  - report.md and report.html now include operational guidance, grouped diagnostics, repair prompt when available, and raw JSON in LTR code/pre blocks
web_sources_used:
  - none
next_allowed_prompt:
  - PR review / CI repair for this Patch 2 branch
blockers:
  - full local pytest could not be run in this environment
remaining_insufficient_evidence:
  - real non-synthetic CE-to-Builder evidence
  - real Builder execution evidence bundle
  - real Responsive input/output evidence bundle
  - browser accessibility and screenshot QA evidence
  - production/readiness/frontend/Elementor correctness evidence
```
