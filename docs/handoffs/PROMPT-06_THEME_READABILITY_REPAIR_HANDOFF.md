# PROMPT-06 Theme Readability Repair Handoff

```yaml
patch_id: PROMPT-06-THEME-READABILITY-REPAIR
branch: project-gate-prompt-06-theme-readability
base_branch: main
base_commit: f038a8ca893438dcd793897092c7a36b06e586e2
pull_request: 45
current_head_after_review_repair: a2441b679d946d8f46342592fdd38acb6a0fb857
scope:
  - repair operator panel Light/Dark/System readability
  - align EV4 semantic tokens with Gradio theme variables
  - improve Settings modal, disabled state, input, upload, radio, accordion, footer, and button readability
  - add token-level WCAG contrast regression tests
  - repair PR Inspector review findings PRF-001, PRF-002, PRF-003 and low-risk PRF-004
out_of_scope:
  - transition logic changes
  - schema/validator/specialist adapter changes
  - Project Gate status semantics changes
  - canonical JSON semantics changes
  - hashing changes
  - production/frontend/Elementor/Responsive readiness claims
files_changed:
  - src/ev4_transition/presentation/theme_tokens.py
  - src/ev4_transition/ui/app.py
  - tests/theme_acceptance/test_theme_tokens.py
  - tests/theme_acceptance/test_operator_panel_theme_tokens.py
  - tests/theme_acceptance/test_operator_panel_theme_contract.py
  - tests/theme_acceptance/test_theme_contrast.py
  - tests/ui/test_operator_panel_theme_repair.py
  - docs/VISUAL_THEME_CONTRACT.md
  - docs/OPERATOR_PANEL_UX_CONTRACT.md
  - docs/OPERATOR_PANEL_MANUAL_QA.md
  - docs/handoffs/PROMPT-06_THEME_READABILITY_REPAIR_HANDOFF.md
commits_created:
  - 0b05f5bd95f47fbc4246ddc36366f9309b2fd192
  - 9699713f5ac62ac9e3f1c2561d2144155b8eff1e
  - 3e48ccf42e5bea58004f80fe68654d5ecee23888
  - fe40c19a58b98c0aab10eb740df1d5e5a1f5b8e5
  - c59de66ded33f5015257d9081dd5decf9571b275
  - fb42c4fe39c43253f447f07a16e3b12c66da2220
  - 10450d011c5bca763f96d72be7433d96e2010734
  - 893b2db3f2e2eb096bf27904fa4a86e99200eaaf
  - 959486643eb520275f9594d48e96bfd92e470b43
  - 245d6ee6fdfff76a05191693c04db14c4c26705d
  - c59924f8815170fb519aff9ec7dd58536c549a82
  - a3a76e0b21edec6e6f5b9e6d49e2d4097d9b627e
  - df51c0b49768d3aa9965b0c0f77d4692fbef6557
  - 314bba2ca2c64440376f869cbf183ad7fca8001b
  - 5cbcfb416c936fba3e7cb6da553b3ecec3472453
  - a2441b679d946d8f46342592fdd38acb6a0fb857
review_repair_findings_addressed:
  PRF-001:
    status: patched
    repair: added explicit primary hover foreground/background tokens and CSS, including dark-mode hover text using a dark token-compatible foreground
    tests: added primary hover contrast pairs for light and dark
  PRF-002:
    status: patched
    repair: lowered system dark fallback selector specificity and kept explicit light selectors after fallback
    tests: added selector contract test that old high-specificity fallback is absent and explicit light selectors follow fallback
  PRF-003:
    status: patched
    repair: restored canonical json_preview as the fourth Gradio callback output through operator_run_outputs
    tests: added UI test proving callback output slot 4 is a string json_preview, not raw result dict
  PRF-004:
    status: patched
    repair: added explicit secondary hover CSS and tokens
    tests: added CSS presence test for secondary hover styling
tests_run:
  - GitHub Actions on head 245d6ee6fdfff76a05191693c04db14c4c26705d: Prompt 06 Report UX, UI Runtime Smoke, Prompt 05 Builder Responsive Final Gate, Skeleton Health all success
  - GitHub Actions on head a2441b679d946d8f46342592fdd38acb6a0fb857: Prompt 06 Report UX, UI Runtime Smoke, Prompt 05 Builder Responsive Final Gate, Skeleton Health all success
tests_not_run:
  - local full repository pytest from the connector container; container DNS could not resolve github.com for clone
  - browser launch / screenshot QA from this connector environment
  - computed-style Settings modal verification from browser devtools
coverage_rules_advanced:
  - PG-THEME-001: expanded from token presence/non-inversion to component token coverage for dialog/input/button/disabled/selection/state/hover colors
  - PG-THEME-CONTRAST-001: added token-level contrast ratio tests for text, UI boundary/focus, button base/hover, disabled, and status pairs
  - PG-GRADIO-THEME-001: added Gradio theme variable mapping to EV4 semantic tokens
  - PG-THEME-RESOLUTION-001: added explicit light/dark selector support and reduced system-dark fallback specificity so explicit light can win
  - PG-UI-PREVIEW-001: added callback helper/test to keep result.json preview as canonical JSON text, not raw dict
coverage_rules_still_gap:
  - Browser/computed-style QA is still manual, not CI-enforced
  - Settings modal readability is statically repaired through Gradio theme mapping and scoped CSS, but screenshot evidence remains pending
  - Accessibility completion remains insufficient_evidence until real browser keyboard/focus and screenshot QA are recorded
new_diagnostics:
  - none
cli_or_ci_changes:
  - none
important_design_decisions:
  - Kept all color values centralized in theme_tokens.py rather than scattered across components
  - Added explicit hover text/background tokens instead of relying on accent hover plus inherited button text
  - Lowered the system-dark fallback selector instead of removing System Mode support
  - Restored json_preview in the Gradio callback without changing result.json artifact serialization or canonical JSON semantics
  - Did not change Project Gate validation logic, transition execution, schemas, canonical JSON behavior, hashing, status mapping, or specialist boundaries
web_sources_used:
  - W3C WCAG 2.2 Contrast Minimum and Non-text Contrast
  - Official Gradio theming guide and custom CSS guidance
next_allowed_prompt: PR #45 manual browser screenshot QA, then merge review if screenshots are acceptable, then PROMPT-07 closure audit
blockers:
  - manual browser screenshot QA pending for Light/Dark/System and Settings modal
remaining_insufficient_evidence:
  - production readiness
  - real Elementor validation
  - frontend correctness
  - responsive correctness
  - accessibility completion
  - browser screenshot QA
  - computed-style Settings modal verification
```
