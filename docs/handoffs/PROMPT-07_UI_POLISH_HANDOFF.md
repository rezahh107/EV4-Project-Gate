# PROMPT-07 UI Polish Handoff

## Scope

Focused visual polish patch for `rezahh107/EV4-Project-Gate` local Gradio operator panel after the merged theme/readability repair.

This patch does not change transition logic, schemas, specialist adapters, canonical JSON, hashing, evidence status semantics, or readiness claims.

## Branch

```text
project-gate-prompt-07-ui-polish
```

## Base commit

```text
b56e8048a71f075e568d4f77d36f737f40c002ba
```

Base evidence: latest inspected `main` commit from GitHub commit search: `Add LLM implementation prompt plan`.

## Head commit

```text
79d7a9aae56d1985713d87bf66f51f357cda11e8
```

Note: this is the implementation/docs head immediately before this handoff file was added. The GitHub commit that adds this handoff becomes the branch head after write; the final exact PR head must be checked from PR metadata before merge.

## PR number

```text
pending_pr_creation
```

## Files changed

```text
src/ev4_transition/presentation/theme_tokens.py
docs/OPERATOR_PANEL_MANUAL_QA.md
docs/OPERATOR_PANEL_UX_CONTRACT.md
docs/VISUAL_THEME_CONTRACT.md
src/ev4_transition/ui/app.py
tests/theme_acceptance/test_operator_panel_theme_contract.py
tests/theme_acceptance/test_operator_panel_theme_tokens.py
tests/theme_acceptance/test_theme_contrast.py
tests/ui/test_operator_panel_css.py
docs/handoffs/PROMPT-07_UI_POLISH_HANDOFF.md
```

## Commits created

```text
00249c6099cae3517aa59bea4ec2368cbe34f9b1 Add control indicator theme tokens
4b0c7d840b62b6a783ae6046070b6180a492328f Polish operator panel radio indicators and dark header
4a09fdc4438b50f982053d775f6c7006bae23796 Test control indicator theme token exports
1136cce77491ab6a08fe0a39336cf878a8f4b245 Add operator panel CSS polish regression tests
b4b0a35c9370c88e523777c9a6deb6ca133d444a Cover control indicator contrast pairs
df6c9852099dfce6f3d85314d4b18220723aeab5 Assert final theme contract exports control indicator vars
8a821ef7b413089d14a06d470c81e6cd424b0841 Document control indicator and dark header theme contract
9ebdc6ab56e063888e97e06699f88a53eb18c159 Document operator panel UI polish requirements
79d7a9aae56d1985713d87bf66f51f357cda11e8 Update manual QA checklist for UI polish
```

## Visual issues fixed

- Added semantic control indicator tokens for Light and Dark themes.
- Exported `--ev4-control-indicator-*` CSS variables.
- Replaced radio-only reliance on browser default `accent-color` with scoped explicit radio indicator CSS under `.gradio-container`.
- Added visible unselected, selected, hover, and focus-visible radio states.
- Added explicit dark header selectors for `body.dark`, `.dark`, `:root[data-theme="dark"]`, and system dark fallback.
- Kept Light Mode header clean and token-backed.

## Design decisions

- Used Project Gate semantic token architecture rather than copying `EV4-Workbook-Jinja` palette or UI identity.
- Transferred only the principles of shell-level theme coherence, layered dark surfaces, visible controls, restrained accents, focus visibility, and readable Persian line-height.
- Kept the patch CSS-scoped to `.gradio-container` or `.ev4-header` rather than modifying service or transition behavior.
- Kept dark radio checked dot dark-on-bright for measurable UI contrast.

## Reference repo files inspected

```text
rezahh107/EV4-Workbook-Jinja:templates/base.html.j2
rezahh107/EV4-Workbook-Jinja:templates/partials/head.html.j2
rezahh107/EV4-Workbook-Jinja:static/assets/css/workbook.css
```

Transferable findings:

- `html[data-theme="..."]` provides shell-level theme control.
- Dark mode uses layered non-white surfaces rather than isolated light cards.
- Form controls use visibly sized `input[type="checkbox"]` / `input[type="radio"]` and accent treatment.
- `:focus-visible` has a strong explicit outline.
- Persian UI font stack and generous line-height improve readability.

Non-transferable:

- Workbook gold/teal identity and educational workbook layout were not copied.

## Tests run

```text
not_run
```

Reason: GitHub connector write access was available, but local sandbox clone failed with DNS resolution error:

```text
fatal: unable to access 'https://github.com/rezahh107/EV4-Project-Gate.git/': Could not resolve host: github.com
```

## Tests not run

```text
uv sync --extra dev --extra ui
uv run pytest tests/theme_acceptance tests/ui
uv run pytest
uv run python -m ev4_transition.ui.app
```

## Added or updated test coverage

- Theme token contract: control indicator tokens exist in Light and Dark.
- CSS export: `--ev4-control-indicator-*` variables are exported.
- CSS behavior: radio selectors, `:checked`, `:focus-visible`, checked dot/background variables are present.
- Dark header anti-regression: explicit dark header selectors are present.
- Contrast token coverage: radio border/background, checked dot/background, and focus ring/surface token pairs are included.

## Visual QA status

```yaml
browser_visual_qa: not_run
screenshot_qa: not_run
status: insufficient_evidence
```

Browser launch and screenshot QA were not available in this execution environment.

## Remaining insufficient_evidence

```yaml
remaining_insufficient_evidence:
  - browser_visual_qa_not_run
  - local_pytest_not_run
  - ci_status_pending_until_pr_workflow_runs_are_checked
  - computed_style_browser_validation_not_run
```

## Next allowed action

Open PR from `project-gate-prompt-07-ui-polish` to `main`, then check GitHub Actions on the exact PR head. After CI, run manual browser QA for Light, Dark, System, Settings modal, radio selected/unselected/focus states, result.json preview, upload area, and accordion headers.
