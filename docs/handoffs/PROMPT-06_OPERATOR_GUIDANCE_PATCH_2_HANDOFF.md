# PROMPT-06 Operator Guidance Patch 2 Handoff

```yaml
prompt_id: PROMPT-06
patch_id: operator-guidance-diagnostic-help-patch-2
branch: ux/operator-guidance-diagnostic-help-patch-2
base_branch: main
base_head_sha: 5a1cebcbf1c0b769690eb594a41d3e57590449b9
pull_request: 36
latest_head_sha_before_handoff_update: 4281c5178c538c7f411c0daf048e7e2d89445403
commits_before_handoff_update:
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
  - 3e353c20327f2170f2cb066ae5d1071f0d9f4d26
  - d1f84e3d847dd76d44c50c920581dda6bc98048c
  - 26e8502707cd2fecd7de68c4b2ba2df07a887ab5
  - cf4628749c04e53a0e813965309b15c15f085200
  - 027557c9702a4060ee3a3aed0dfec52286c2b168
  - 4d667ad6652223fd21aa8d840daa63a07f663bd3
  - 4281c5178c538c7f411c0daf048e7e2d89445403
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
  - python compile() syntax check on drafted review-suggestion patch files:
      - src/ev4_transition/service/guidance.py
      - src/ev4_transition/ui/components.py
      - tests/service/test_operator_guidance.py
  - GitHub Actions on d1f84e3d847dd76d44c50c920581dda6bc98048c: UI Runtime Smoke
  - GitHub Actions on d1f84e3d847dd76d44c50c920581dda6bc98048c: Prompt 05 Builder Responsive Final Gate
  - GitHub Actions on d1f84e3d847dd76d44c50c920581dda6bc98048c: Prompt 06 Report UX
  - GitHub Actions on d1f84e3d847dd76d44c50c920581dda6bc98048c: Skeleton Health
tests_passed:
  - UI Runtime Smoke run 28818684598: success
  - Prompt 05 Builder Responsive Final Gate run 28818684473: success
  - Prompt 06 Report UX run 28818684461: success
  - Skeleton Health run 28818684610: success
ci_repair:
  blocking_review_status_before_repair: RED_DO_NOT_MERGE
  failing_reviewed_head: 3e353c20327f2170f2cb066ae5d1071f0d9f4d26
  blocking_failure: Service layer tests failed in Prompt 06 Report UX and Skeleton Health
  repair_commit: d1f84e3d847dd76d44c50c920581dda6bc98048c
  repair_summary: Added explicit checkout wording to PG_A2C_EXTERNAL_FILE_READ_FAILED guidance so service guidance tests match the user-facing action contract.
review_suggestion_patch:
  patch_head_before_handoff: 4281c5178c538c7f411c0daf048e7e2d89445403
  commits:
    - cf4628749c04e53a0e813965309b15c15f085200
    - 027557c9702a4060ee3a3aed0dfec52286c2b168
    - 4d667ad6652223fd21aa8d840daa63a07f663bd3
    - 4281c5178c538c7f411c0daf048e7e2d89445403
  accepted_suggestions:
    - Added valid to success guidance status dictionaries.
    - Rendered diagnostic group count through html_code_ltr inside HTML details/list markup.
    - Fixed pip editable fallback command to pip install -e ".[dev,ui]".
    - Replaced double registry lookup in repair prompt selection with one lookup per diagnostic.
  tests_added:
    - test_valid_status_without_primary_diagnostic_uses_success_guidance_not_invalid_fallback
    - test_status_summary_group_count_uses_html_code_not_literal_markdown_backticks
tests_not_run:
  - full local python -m pytest -q in this assistant environment
  - UI launch smoke test in a browser
reason_tests_not_run:
  - live repository clone was unavailable in this environment because github.com DNS resolution failed
  - browser screenshot/interactive Gradio launch was not available through the GitHub connector
coverage_rules_advanced:
  - PG-UNICODE-001: guidance/status main panel keeps Persian RTL and technical identifiers LTR via existing presentation helpers
  - PG-OUTPUT-001: output:null is classified and explained as no downstream package produced when applicable
  - PG-STATUS-001: guidance keeps accepted/valid/repair_needed/insufficient_evidence/invalid semantically distinct
  - PG-UX-GUIDANCE-001: new code-backed guidance registry and service tests cover common operator failures
coverage_rules_still_gap:
  - no browser accessibility completion claim
  - no frontend/Elementor/responsive correctness claim
  - no downstream_contract_enforced claim
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
  - CI repair changed only guidance wording, not transition behavior or status semantics
  - review-suggestion patch changes presentation/guidance only and does not change transition behavior, schema identity, hashes, validators, adapters, or status mapping semantics
web_sources_used:
  - none
next_allowed_prompt:
  - PR Inspector re-review on latest head
  - Merge only after owner review and current-head CI remains green
blockers:
  - current-head GitHub Actions must complete after this handoff-update commit
remaining_insufficient_evidence:
  - real non-synthetic CE-to-Builder evidence
  - real Builder execution evidence bundle
  - real Responsive input/output evidence bundle
  - browser accessibility and screenshot QA evidence
  - production/readiness/frontend/Elementor correctness evidence
```
