from __future__ import annotations

from ev4_transition.presentation.theme_tokens import css_custom_properties

from .adapters import build_capability_rows, run_operator_check
from .components import CAPABILITY_HEADERS, DIAGNOSTIC_HEADERS
from .state import transition_choices


HEADER_WARNING_FA = (
    "این ابزار فقط بررسی گیت را اجرا می‌کند؛ اثبات نهایی تولید، فرانت‌اند، "
    "Elementor واقعی یا صحت Responsive نیست."
)

HEADER_HELPER_FA = (
    "JSON را بارگذاری یا paste کن، transition مجاز را انتخاب کن، نتیجه فارسی و diagnostics را ببین، "
    "و خروجی‌های قابل دانلود را دریافت کن."
)


def operator_header_html() -> str:
    return f"""
<section lang="fa" dir="rtl" class="ev4-app ev4-rtl">
  <header class="ev4-header ev4-shell" aria-label="EV4 Project Gate local operator panel">
    <div class="ev4-header-kicker">Local Operator Panel</div>
    <div class="ev4-header-title-row">
      <h1 class="ev4-header-title"><bdi dir="ltr">EV4 Project Gate</bdi></h1>
      <span class="ev4-header-badge">gate runner</span>
    </div>
    <p class="ev4-header-subtitle">پنل محلی بررسی گذارها</p>
    <p class="ev4-warning">⚠️ {HEADER_WARNING_FA}</p>
    <p class="ev4-helper">{HEADER_HELPER_FA}</p>
  </header>
</section>
"""


def operator_panel_css() -> str:
    return (
        css_custom_properties()
        + """
        .gradio-container {
          color-scheme: light dark;
          background: var(--ev4-surface-base) !important;
          color: var(--ev4-text-primary) !important;
          font-family: var(--ev4-font-fa-ui);
          font-size: 16px;
          line-height: 1.7;
        }
        .ev4-app,
        .ev4-shell,
        .ev4-rtl,
        .ev4-rtl textarea,
        .ev4-rtl input {
          direction: rtl;
          text-align: right;
          font-family: var(--ev4-font-fa-ui);
          line-height: 1.75;
          letter-spacing: normal;
        }
        .ev4-shell {
          max-width: 1120px;
          margin: 0 auto 0.75rem;
        }
        .ev4-header {
          background: var(--ev4-surface-raised);
          border: 1px solid var(--ev4-border-subtle);
          border-radius: 18px;
          padding: 1.15rem 1.25rem;
          box-shadow: 0 14px 34px var(--ev4-shadow-raised);
        }
        .ev4-header-kicker {
          color: var(--ev4-text-secondary);
          direction: ltr;
          text-align: left;
          unicode-bidi: isolate;
          font-family: var(--ev4-font-code);
          font-size: 0.78rem;
          margin-bottom: 0.3rem;
        }
        .ev4-header-title-row {
          display: flex;
          flex-wrap: wrap;
          align-items: baseline;
          justify-content: space-between;
          gap: 0.65rem 1rem;
        }
        .ev4-header-title {
          color: var(--ev4-text-primary);
          font-size: clamp(1.45rem, 3vw, 2.15rem);
          line-height: 1.2;
          margin: 0;
          letter-spacing: normal;
        }
        .ev4-header-subtitle {
          color: var(--ev4-text-secondary);
          font-size: 1.02rem;
          margin: 0.35rem 0 0;
        }
        .ev4-header-badge {
          color: var(--ev4-accent-primary);
          background: var(--ev4-surface-overlay);
          border: 1px solid var(--ev4-border-subtle);
          border-radius: 999px;
          direction: ltr;
          unicode-bidi: isolate;
          font-family: var(--ev4-font-code);
          font-size: 0.78rem;
          padding: 0.18rem 0.55rem;
        }
        .ev4-warning {
          color: var(--ev4-status-warning-fg);
          background: var(--ev4-status-warning-bg);
          border: 1px solid var(--ev4-border-subtle);
          border-radius: 12px;
          margin: 0.9rem 0 0;
          padding: 0.6rem 0.75rem;
          font-weight: 600;
        }
        .ev4-helper {
          color: var(--ev4-text-secondary);
          margin: 0.7rem 0 0;
          font-size: 0.98rem;
        }
        .ev4-section,
        .ev4-dataframe,
        .ev4-download {
          background: var(--ev4-surface-raised);
          border: 1px solid var(--ev4-border-subtle);
          border-radius: 16px;
          padding: 0.75rem;
        }
        .ev4-section label,
        .ev4-download label,
        .ev4-dataframe label {
          color: var(--ev4-text-primary) !important;
          font-weight: 650;
          text-align: right;
        }
        .ev4-section textarea,
        .ev4-section input,
        .ev4-download input {
          background: var(--ev4-surface-overlay) !important;
          border-color: var(--ev4-border-default) !important;
          color: var(--ev4-text-primary) !important;
        }
        .ev4-helper-block {
          color: var(--ev4-text-secondary);
          margin: 0.25rem 0 0;
        }
        .ev4-ltr textarea,
        .ev4-ltr input,
        .ev4-ltr code,
        .ev4-ltr pre,
        .ev4-ltr .cm-editor,
        .ev4-ltr .cm-content,
        .ev4-ltr .cm-line,
        code,
        pre {
          direction: ltr;
          text-align: left;
          unicode-bidi: isolate;
          font-family: var(--ev4-font-code);
        }
        .ev4-code-preview,
        .ev4-code-preview pre,
        .ev4-code-preview code {
          background: var(--ev4-code-bg) !important;
        }
        .ev4-status-card section[role="status"],
        .ev4-status-content {
          border: 1px solid var(--ev4-border-default);
          border-radius: 16px;
          padding: 1rem 1.1rem;
          background: var(--ev4-surface-raised);
          color: var(--ev4-text-primary);
          line-height: 1.78;
        }
        .ev4-status-card code,
        .ev4-status-content code {
          background: var(--ev4-code-bg);
          border: 1px solid var(--ev4-border-subtle);
          border-radius: 6px;
          padding: 0.05rem 0.28rem;
        }
        .ev4-technical-table,
        .ev4-technical-table table {
          direction: rtl;
          text-align: right;
        }
        .ev4-technical-table code,
        .ev4-technical-table pre {
          direction: ltr;
          text-align: left;
          unicode-bidi: isolate;
        }
        .gradio-container :focus-visible,
        .ev4-app :focus-visible {
          outline: 3px solid var(--ev4-focus-ring) !important;
          outline-offset: 3px;
        }
        .gradio-container button.primary,
        .gradio-container button[variant="primary"] {
          background: var(--ev4-accent-primary) !important;
          border-color: var(--ev4-accent-primary) !important;
        }
        .gradio-container button.primary:hover,
        .gradio-container button[variant="primary"]:hover {
          background: var(--ev4-accent-hover) !important;
          border-color: var(--ev4-accent-hover) !important;
        }
        """
    )


def build_demo():
    try:
        import gradio as gr
    except ImportError as exc:  # pragma: no cover - exercised only without optional UI dependency.
        raise RuntimeError(
            "Gradio is required for the local operator panel. Install the package with UI dependencies, "
            "for example: python -m pip install -e '.[ui]'"
        ) from exc

    with gr.Blocks(
        title="EV4 Project Gate Local Operator Panel",
        css=operator_panel_css(),
    ) as demo:
        gr.Markdown(operator_header_html())

        with gr.Group(elem_classes=["ev4-section", "ev4-transition-section"]):
            with gr.Row():
                transition = gr.Radio(
                    choices=transition_choices(),
                    value=transition_choices()[0],
                    label="انتخاب بررسی / Transition",
                )
                run_button = gr.Button("اجرای بررسی Project Gate", variant="primary")

        with gr.Accordion("ورودی JSON", open=True, elem_classes=["ev4-section", "ev4-json-section"]):
            json_file = gr.File(label="بارگذاری فایل JSON / Upload JSON", file_types=[".json"], type="filepath")
            json_text = gr.Textbox(
                label="چسباندن متن JSON / Paste JSON",
                lines=12,
                elem_classes=["ev4-ltr"],
                placeholder='{"schema_version": "..."}',
            )

        with gr.Accordion("مسیر پوشه‌های local repository — نه GitHub URL", open=False, elem_classes=["ev4-section"]):
            project_gate_path = gr.Textbox(
                label="مسیر Project Gate repo / Project Gate path",
                placeholder="/path/to/EV4-Project-Gate",
                elem_classes=["ev4-ltr"],
            )
            architect_path = gr.Textbox(
                label="مسیر Architect repo / Architect path",
                placeholder="/path/to/EV4-Architect-Repo",
                elem_classes=["ev4-ltr"],
            )
            ce_path = gr.Textbox(
                label="مسیر CE repo / CE path",
                placeholder="/path/to/EV4-Constructability-Engineer-Repo",
                elem_classes=["ev4-ltr"],
            )
            builder_path = gr.Textbox(
                label="مسیر Builder repo / Builder path",
                placeholder="/path/to/EV4-Builder-Assistant-Repo",
                elem_classes=["ev4-ltr"],
            )
            responsive_path = gr.Textbox(
                label="مسیر Responsive repo / Responsive path",
                placeholder="/path/to/EV4-Responsive-Architect",
                elem_classes=["ev4-ltr"],
            )
            gr.Markdown(
                '<div lang="fa" dir="rtl" class="ev4-rtl ev4-helper-block">این مسیرها باید پوشه‌های local checkout باشند، نه URL گیت‌هاب.</div>'
            )

        with gr.Accordion("خلاصه نتیجه", open=True, elem_classes=["ev4-section"]):
            status_summary = gr.Markdown(elem_classes=["ev4-rtl", "ev4-status-card"], elem_id="ev4-status-live")

        with gr.Accordion("جزئیات پیشرفته / Diagnostics", open=False, elem_classes=["ev4-section"]):
            diagnostics = gr.Dataframe(
                headers=DIAGNOSTIC_HEADERS,
                datatype=["str", "str", "str", "str", "str", "str"],
                label="Diagnostics",
                interactive=False,
                elem_classes=["ev4-dataframe", "ev4-technical-table"],
            )

        with gr.Accordion("وضعیت قابلیت‌ها / Capabilities", open=False, elem_classes=["ev4-section"]):
            capabilities = gr.Dataframe(
                value=build_capability_rows(),
                headers=CAPABILITY_HEADERS,
                datatype=["str", "str", "str", "str", "str", "str"],
                label="Capabilities",
                interactive=False,
                elem_classes=["ev4-dataframe", "ev4-technical-table"],
            )

        with gr.Accordion("پیش‌نمایش JSON / result.json", open=False, elem_classes=["ev4-section"]):
            json_preview = gr.Code(language="json", label="result.json", elem_classes=["ev4-ltr", "ev4-code-preview"])

        downloads = gr.File(
            label="دانلود خروجی‌ها / result.json, report.md, report.html",
            file_count="multiple",
            elem_classes=["ev4-download", "ev4-ltr"],
        )

        def _run(
            selected_transition,
            pasted,
            uploaded,
            project_gate,
            architect,
            ce,
            builder,
            responsive,
        ):
            output = run_operator_check(
                selected_transition,
                pasted_json=pasted,
                uploaded_file=uploaded,
                project_gate_repo_path=project_gate,
                architect_repo_path=architect,
                ce_repo_path=ce,
                builder_repo_path=builder,
                responsive_repo_path=responsive,
            )
            return (
                output.status_markdown,
                output.diagnostics_rows,
                output.capability_rows,
                output.json_preview,
                output.download_paths,
            )

        run_event = run_button.click(
            lambda: "⏳ در حال پردازش…",
            outputs=[status_summary],
            queue=False,
        ).then(
            _run,
            inputs=[transition, json_text, json_file, project_gate_path, architect_path, ce_path, builder_path, responsive_path],
            outputs=[status_summary, diagnostics, capabilities, json_preview, downloads],
        )

    return demo


def main() -> None:
    build_demo().launch()


if __name__ == "__main__":
    main()
