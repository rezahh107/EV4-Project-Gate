# Standards Traceability

Status: `PROMPT-06` traceability for report UX, Persian RTL/LTR typography, theme tokens, and output writing.

| requirement | source standard | implementation location | tests/manual checks |
|---|---|---|---|
| `status_not_color_only` | `UXIS v1.2`, `DMDS v2.1` | `src/ev4_transition/presentation/status_mapping.py`, `src/ev4_transition/reports/renderers.py` | `tests/ux_acceptance/test_report_status_ux.py::test_status_color_is_not_only_signal` |
| `focus_visible` | `UXIS v1.2`, `DMDS v2.1` | `src/ev4_transition/presentation/theme_tokens.py` | `tests/theme_acceptance/test_theme_tokens.py::test_focus_token_exists_for_light_and_dark_if_themed_report_exists` |
| `persian_rtl_ltr_isolation` | `UXIS v1.2`, `TYPEKIT v1.1`, `DMDS v2.1` | `src/ev4_transition/presentation/bidi.py`, `src/ev4_transition/reports/renderers.py` | `tests/typography_acceptance/test_persian_bidi_typography.py` |
| `no_success_download_on_write_failure` | `UXIS v1.2`, Project Gate lightweight safety | `src/ev4_transition/io/atomic_writer.py` | `tests/reporting/test_output_writer.py::test_no_success_download_when_output_write_failed` |
| `dark_mode_not_simple_inversion` | `DMDS v2.1` | `src/ev4_transition/presentation/theme_tokens.py` | `tests/theme_acceptance/test_theme_tokens.py::test_dark_theme_is_not_simple_inversion` |
| `technical_text_copyable` | `TYPEKIT v1.1`, `DMDS v2.1` | `src/ev4_transition/presentation/bidi.py`, `src/ev4_transition/reports/renderers.py` | `tests/typography_acceptance/test_persian_bidi_typography.py::test_code_paths_hashes_are_copyable` |
| `insufficient_evidence_warning_tone` | `UXIS v1.2`, Project Gate hard rules | `src/ev4_transition/presentation/status_mapping.py`, `src/ev4_transition/reports/renderers.py` | `tests/ux_acceptance/test_report_status_ux.py::test_insufficient_evidence_uses_warning` |
| `report_does_not_mutate_result` | Project Gate deterministic boundary | `src/ev4_transition/reports/renderers.py` | `tests/reporting/test_report_rendering.py::test_report_rendering_does_not_mutate_result` |
| `personal_project_lightweight_security` | Project Gate personal-use security posture | `src/ev4_transition/io/atomic_writer.py`, `docs/REPORT_UX_CONTRACT.md` | atomic writer tests and manual review of no enterprise UI/security overhead |

## Source notes

- `UXIS v1.2` is used for workflow, status meaning, error recovery, file flow, Persian/RTL behavior, and no-success-output-after-write-failure rules.
- `DMDS v2.1` is used for semantic status tokens, explicit light/dark tokens, focus ring, and dark-mode non-inversion.
- `TYPEKIT v1.1` is used for Persian-friendly UI font stack and LTR/copyable technical fragments.

## Implementation boundary

This traceability does not claim a production UI, accessibility completion, real frontend correctness, or release readiness. It only binds report-generation behavior and output-writing safety to tests and documentation.
