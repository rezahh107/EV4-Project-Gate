# UI/UX Traceability — Operator Panel Prompt 1

## Scope boundary

| Rule | Carrier |
|---|---|
| Persian-first interface | `src/ev4_transition/ui/app.py` labels and Markdown |
| RTL Persian text | Gradio Markdown sections with `lang="fa" dir="rtl"` and CSS class `ev4-rtl` |
| LTR technical tokens | `src/ev4_transition/ui/components.py::ltr_token` |
| Status icon + text | `src/ev4_transition/ui/components.py::status_summary_markdown` |
| No color-only status | Status includes icon, Persian label, raw status, and semantic tone text |
| Progressive disclosure | Gradio accordions for input, diagnostics, capabilities, JSON preview |
| No fake progress | No progress bar, no timer, no optimistic execution text |
| No hidden result mutation | `render_download_artifacts` deep-copies result before rendering |
| Malformed JSON fail-closed | `run_operator_check` returns `MALFORMED_JSON` and does not call engine |
| Unwired transitions fail-safe | `UI_TRANSITION_NOT_WIRED` with `insufficient_evidence` |
| Capability inspector read-only | `load_capability_payload` reads `capability-status.v1.json`; tests compare file before/after |

## Test evidence carriers

| Test | Rule |
|---|---|
| `test_malformed_json_returns_safe_ui_error` | malformed JSON safe error |
| `test_status_mapping_for_project_gate_statuses` | accepted / invalid / insufficient_evidence / repair_needed mapping |
| `test_diagnostics_rendering_preserves_code_severity_and_path` | diagnostic table preserves code/severity/path |
| `test_ltr_isolation_helper_wraps_technical_tokens` | LTR isolation |
| `test_capability_inspector_reads_without_mutating_source_file` | read-only capability inspector |
| `test_unavailable_transition_is_marked_and_does_not_fake_execution` | unavailable transition does not fake execution |
| `test_report_and_result_rendering_does_not_mutate_original_result` | report/result rendering immutability |

## Known gaps

- CE → Builder, Builder → Responsive, and Final Evidence Gate are intentionally not wired in this prompt.
- No claim is made about real non-synthetic handoff evidence.
- No claim is made about production readiness, frontend correctness, real Elementor validation, responsive correctness, accessibility completion, or export validation.
- UI visual accessibility was not proven by browser automation in this prompt.
