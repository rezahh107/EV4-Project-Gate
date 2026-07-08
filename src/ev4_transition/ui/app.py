from __future__ import annotations

from typing import Any

from ev4_transition.presentation.theme_tokens import THEME_TOKENS, css_custom_properties
from ev4_transition.service.preflight import run_preflight

from .adapters import build_capability_rows, build_gate_request, run_operator_check
from .components import CAPABILITY_HEADERS, DIAGNOSTIC_HEADERS
from .preflight_components import preflight_result_html
from .state import transition_choices


HEADER_WARNING_FA = (
    "این ابزار فقط بررسی گیت را اجرا می‌کند؛ اثبات نهایی تولید، فرانت‌اند، "
    "Elementor واقعی یا صحت Responsive نیست."
)

HEADER_HELPER_FA = (
    "JSON را بارگذاری یا paste کن، transition مجاز را انتخاب کن، نتیجه فارسی و diagnostics را ببین، "
    "و خروجی‌های قابل دانلود را دریافت کن."
)

PREFLIGHT_HELPER_FA = (
    "قبل از اجرای اصلی، مسیرهای local checkout، فایل‌های pin‌شده و شکل کلی JSON را بررسی کن. "
    "این بررسی repositoryها را تغییر نمی‌دهد و جایگزین اجرای واقعی Gate نیست."
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


def operator_gradio_theme(gr: Any) -> Any:
    """Return a Gradio theme mapped to the EV4 semantic token palette.

    Gradio owns its Settings modal and internal component variables. Mapping those
    variables here keeps Gradio light/dark rendering aligned with the EV4 custom
    properties instead of relying only on broad CSS overrides.
    """

    light = THEME_TOKENS["light"]
    dark = THEME_TOKENS["dark"]
    return gr.themes.Base(
        primary_hue="blue",
        secondary_hue="slate",
        neutral_hue="slate",
        spacing_size="md",
        radius_size="lg",
        text_size="md",
        font=["Vazirmatn", "Vazir", "IRANSansX", "IranSansXV", "Tahoma", "system-ui", "sans-serif"],
        font_mono=["Cascadia Code", "JetBrains Mono", "Fira Code", "Consolas", "monospace"],
    ).set(
        body_background_fill=light["surface.base"],
        body_background_fill_dark=dark["surface.base"],
        body_text_color=light["text.primary"],
        body_text_color_dark=dark["text.primary"],
        body_text_color_subdued=light["text.secondary"],
        body_text_color_subdued_dark=dark["text.secondary"],
        background_fill_primary=light["surface.raised"],
        background_fill_primary_dark=dark["surface.raised"],
        background_fill_secondary=light["surface.overlay"],
        background_fill_secondary_dark=dark["surface.overlay"],
        block_background_fill=light["surface.raised"],
        block_background_fill_dark=dark["surface.raised"],
        block_border_color=light["border.default"],
        block_border_color_dark=dark["border.default"],
        block_label_background_fill=light["surface.overlay"],
        block_label_background_fill_dark=dark["surface.overlay"],
        block_label_border_color=light["border.default"],
        block_label_border_color_dark=dark["border.default"],
        block_label_text_color=light["text.primary"],
        block_label_text_color_dark=dark["text.primary"],
        block_title_text_color=light["text.primary"],
        block_title_text_color_dark=dark["text.primary"],
        panel_background_fill=light["surface.dialog"],
        panel_background_fill_dark=dark["surface.dialog"],
        panel_border_color=light["border.default"],
        panel_border_color_dark=dark["border.default"],
        accordion_text_color=light["text.primary"],
        accordion_text_color_dark=dark["text.primary"],
        input_background_fill=light["input.bg"],
        input_background_fill_dark=dark["input.bg"],
        input_background_fill_focus=light["input.bg"],
        input_background_fill_focus_dark=dark["input.bg"],
        input_background_fill_hover=light["input.bg"],
        input_background_fill_hover_dark=dark["input.bg"],
        input_border_color=light["input.border"],
        input_border_color_dark=dark["input.border"],
        input_border_color_focus=light["focus.ring"],
        input_border_color_focus_dark=dark["focus.ring"],
        input_border_color_hover=light["border.strong"],
        input_border_color_hover_dark=dark["border.strong"],
        input_placeholder_color=light["text.muted"],
        input_placeholder_color_dark=dark["text.muted"],
        button_primary_background_fill=light["button.primary.bg"],
        button_primary_background_fill_dark=dark["button.primary.bg"],
        button_primary_background_fill_hover=light["button.primary.hover.bg"],
        button_primary_background_fill_hover_dark=dark["button.primary.hover.bg"],
        button_primary_border_color=light["button.primary.bg"],
        button_primary_border_color_dark=dark["button.primary.bg"],
        button_primary_border_color_hover=light["button.primary.hover.bg"],
        button_primary_border_color_hover_dark=dark["button.primary.hover.bg"],
        button_primary_text_color=light["button.primary.text"],
        button_primary_text_color_dark=dark["button.primary.text"],
        button_primary_text_color_hover=light["button.primary.hover.text"],
        button_primary_text_color_hover_dark=dark["button.primary.hover.text"],
        button_secondary_background_fill=light["button.secondary.bg"],
        button_secondary_background_fill_dark=dark["button.secondary.bg"],
        button_secondary_background_fill_hover=light["button.secondary.hover.bg"],
        button_secondary_background_fill_hover_dark=dark["button.secondary.hover.bg"],
        button_secondary_border_color=light["border.default"],
        button_secondary_border_color_dark=dark["border.default"],
        button_secondary_border_color_hover=light["border.strong"],
        button_secondary_border_color_hover_dark=dark["border.strong"],
        button_secondary_text_color=light["button.secondary.text"],
        button_secondary_text_color_dark=dark["button.secondary.text"],
        button_secondary_text_color_hover=light["button.secondary.hover.text"],
        button_secondary_text_color_hover_dark=dark["button.secondary.hover.text"],
        checkbox_label_background_fill=light["button.secondary.bg"],
        checkbox_label_background_fill_dark=dark["button.secondary.bg"],
        checkbox_label_background_fill_hover=light["button.secondary.hover.bg"],
        checkbox_label_background_fill_hover_dark=dark["button.secondary.hover.bg"],
        checkbox_label_background_fill_selected=light["info.bg"],
        checkbox_label_background_fill_selected_dark=dark["info.bg"],
        checkbox_label_border_color=light["border.default"],
        checkbox_label_border_color_dark=dark["border.default"],
        checkbox_label_border_color_hover=light["border.strong"],
        checkbox_label_border_color_hover_dark=dark["border.strong"],
        checkbox_label_border_color_selected=light["focus.ring"],
        checkbox_label_border_color_selected_dark=dark["focus.ring"],
        checkbox_label_text_color=light["text.primary"],
        checkbox_label_text_color_dark=dark["text.primary"],
        checkbox_label_text_color_selected=light["text.primary"],
        checkbox_label_text_color_selected_dark=dark["text.primary"],
        checkbox_border_color=light["input.border"],
        checkbox_border_color_dark=dark["input.border"],
        checkbox_border_color_focus=light["focus.ring"],
        checkbox_border_color_focus_dark=dark["focus.ring"],
        checkbox_border_color_selected=light["focus.ring"],
        checkbox_border_color_selected_dark=dark["focus.ring"],
        table_text_color=light["text.primary"],
        table_text_color_dark=dark["text.primary"],
        table_border_color=light["border.default"],
        table_border_color_dark=dark["border.default"],
        code_background_fill=light["code.bg"],
        code_background_fill_dark=dark["code.bg"],
        loader_color=light["accent.primary"],
        loader_color_dark=dark["accent.primary"],
        slider_color=light["accent.primary"],
        slider_color_dark=dark["accent.primary"],
        border_color_primary=light["border.default"],
        border_color_primary_dark=dark["border.default"],
        border_color_accent=light["focus.ring"],
        border_color_accent_dark=dark["focus.ring"],
        color_accent=light["accent.primary"],
        color_accent_soft=light["info.bg"],
        color_accent_soft_dark=dark["info.bg"],
    )


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
        .ev4-shell { max-width: 1120px; margin: 0 auto 0.75rem; }
        .ev4-header,
        .ev4-section,
        .ev4-dataframe,
        .ev4-download,
        .ev4-status-content,
        .ev4-preflight-result {
          background: var(--ev4-surface-raised);
          border: 1px solid var(--ev4-border-default);
          border-radius: 16px;
          padding: 0.75rem;
          box-shadow: 0 14px 34px var(--ev4-shadow-raised);
        }
        .ev4-header { padding: 1.15rem 1.25rem; }
        .ev4-header-kicker,
        .ev4-header-badge,
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
        .ev4-header-kicker { color: var(--ev4-text-secondary); font-size: 0.78rem; margin-bottom: 0.3rem; }
        .ev4-header-title-row { display: flex; flex-wrap: wrap; align-items: baseline; justify-content: space-between; gap: 0.65rem 1rem; }
        .ev4-header-title { color: var(--ev4-text-primary); font-size: clamp(1.45rem, 3vw, 2.15rem); line-height: 1.2; margin: 0; letter-spacing: normal; }
        .ev4-header-subtitle { color: var(--ev4-text-secondary); font-size: 1.02rem; margin: 0.35rem 0 0; }
        .ev4-header-badge { color: var(--ev4-info); background: var(--ev4-info-bg); border-radius: 999px; font-size: 0.78rem; padding: 0.18rem 0.55rem; }
        .ev4-warning { color: var(--ev4-status-warning-fg); background: var(--ev4-status-warning-bg); border: 1px solid var(--ev4-border-default); border-radius: 12px; margin: 0.9rem 0 0; padding: 0.6rem 0.75rem; font-weight: 650; }
        .ev4-helper,
        .ev4-helper-block { color: var(--ev4-text-secondary); margin: 0.7rem 0 0; font-size: 0.98rem; }
        .ev4-section label,
        .ev4-download label,
        .ev4-dataframe label,
        .gradio-container label,
        .gradio-container [data-testid="block-label"],
        .gradio-container .block-label,
        .gradio-container .label-wrap,
        .gradio-container .prose,
        .gradio-container .prose * { color: var(--ev4-text-primary) !important; font-weight: 650; text-align: right; opacity: 1 !important; }
        .gradio-container .secondary-text,
        .gradio-container .svelte-1gfkn6j,
        .gradio-container .wrap .meta-text { color: var(--ev4-text-secondary) !important; opacity: 1 !important; }
        .ev4-section textarea,
        .ev4-section input,
        .ev4-download input,
        .gradio-container textarea,
        .gradio-container input,
        .gradio-container [role="textbox"] {
          background: var(--ev4-input-bg) !important;
          border-color: var(--ev4-input-border) !important;
          color: var(--ev4-input-text) !important;
          opacity: 1 !important;
        }
        .gradio-container textarea::placeholder,
        .gradio-container input::placeholder { color: var(--ev4-text-muted) !important; opacity: 1 !important; }
        .gradio-container input[type="radio"],
        .gradio-container input[type="checkbox"] { accent-color: var(--ev4-accent-primary); }
        .gradio-container [role="radiogroup"] label,
        .gradio-container [role="checkbox"] label { color: var(--ev4-text-primary) !important; opacity: 1 !important; }
        .gradio-container details,
        .gradio-container summary,
        .gradio-container .accordion,
        .gradio-container .accordion > .label-wrap,
        .gradio-container .accordion button {
          background: var(--ev4-surface-raised) !important;
          color: var(--ev4-text-primary) !important;
          border-color: var(--ev4-border-default) !important;
          opacity: 1 !important;
        }
        .gradio-container .file-preview,
        .gradio-container .upload,
        .gradio-container [data-testid="file"],
        .gradio-container [data-testid="file-upload"] {
          background: var(--ev4-input-bg) !important;
          color: var(--ev4-text-primary) !important;
          border-color: var(--ev4-input-border) !important;
          opacity: 1 !important;
        }
        .gradio-container [role="dialog"],
        .gradio-container dialog,
        .gradio-container .modal {
          background: var(--ev4-surface-dialog) !important;
          color: var(--ev4-text-primary) !important;
          border: 1px solid var(--ev4-border-default) !important;
          opacity: 1 !important;
        }
        .gradio-container [role="dialog"] *,
        .gradio-container dialog *,
        .gradio-container .modal * { color: inherit; opacity: 1; }
        .gradio-container :disabled,
        .gradio-container [aria-disabled="true"],
        .gradio-container .disabled {
          background: var(--ev4-disabled-bg) !important;
          color: var(--ev4-disabled-text) !important;
          border-color: var(--ev4-border-default) !important;
          opacity: 1 !important;
          cursor: not-allowed;
        }
        .ev4-code-preview,
        .ev4-code-preview pre,
        .ev4-code-preview code { background: var(--ev4-code-bg) !important; color: var(--ev4-text-primary) !important; }
        .ev4-status-card section[role="status"],
        .ev4-status-content,
        .ev4-preflight-result { border-color: var(--ev4-border-default); padding: 1rem 1.1rem; line-height: 1.78; }
        .ev4-status-card code,
        .ev4-status-content code,
        .ev4-preflight-result code { background: var(--ev4-code-bg); border: 1px solid var(--ev4-border-default); border-radius: 6px; padding: 0.05rem 0.28rem; }
        .ev4-preflight-list { list-style: none; margin: 0.75rem 0 0; padding: 0; }
        .ev4-preflight-list li { border-top: 1px solid var(--ev4-border-subtle); padding: 0.55rem 0; }
        .ev4-preflight-icon { display: inline-block; min-width: 1.5rem; text-align: center; }
        .ev4-preflight-error { color: var(--ev4-status-danger-fg); }
        .ev4-preflight-warning { color: var(--ev4-status-warning-fg); }
        .ev4-preflight-ok { color: var(--ev4-status-success-fg); }
        .ev4-technical-table,
        .ev4-technical-table table { direction: rtl; text-align: right; }
        .ev4-technical-table code,
        .ev4-technical-table pre { direction: ltr; text-align: left; unicode-bidi: isolate; }
        .gradio-container :focus-visible,
        .ev4-app :focus-visible { outline: 3px solid var(--ev4-focus-ring) !important; outline-offset: 3px; box-shadow: 0 0 0 2px var(--ev4-surface-base) !important; }
        .gradio-container ::selection,
        .ev4-app ::selection { background: var(--ev4-selection-bg); }
        .gradio-container button.primary,
        .gradio-container button[variant="primary"] { background: var(--ev4-button-primary-bg) !important; border-color: var(--ev4-button-primary-bg) !important; color: var(--ev4-button-primary-text) !important; font-weight: 700; }
        .gradio-container button.primary:hover,
        .gradio-container button[variant="primary"]:hover { background: var(--ev4-button-primary-hover-bg) !important; border-color: var(--ev4-button-primary-hover-bg) !important; color: var(--ev4-button-primary-hover-text) !important; }
        .gradio-container button:not(.primary):not([variant="primary"]) { background: var(--ev4-button-secondary-bg) !important; border-color: var(--ev4-border-default) !important; color: var(--ev4-button-secondary-text) !important; }
        .gradio-container button:not(.primary):not([variant="primary"]):hover { background: var(--ev4-button-secondary-hover-bg) !important; border-color: var(--ev4-border-strong) !important; color: var(--ev4-button-secondary-hover-text) !important; }
        .gradio-container footer,
        .gradio-container footer * { color: var(--ev4-text-muted) !important; opacity: 1 !important; }
        """
    )


def operator_run_outputs(output: Any) -> tuple[Any, Any, Any, str, Any]:
    """Return Gradio callback outputs without replacing JSON preview text with a dict."""

    return output.status_markdown, output.diagnostics_rows, output.capability_rows, output.json_preview, output.download_paths


def build_demo():
    try:
        import gradio as gr
    except ImportError as exc:  # pragma: no cover - exercised only without optional UI dependency.
        raise RuntimeError(
            "Gradio is required for the local operator panel. Install the package with UI dependencies, "
            "for example: python -m pip install -e '.[ui]'"
        ) from exc

    with gr.Blocks(title="EV4 Project Gate Local Operator Panel", theme=operator_gradio_theme(gr), css=operator_panel_css()) as demo:
        gr.HTML(operator_header_html())

        with gr.Group(elem_classes=["ev4-section", "ev4-transition-section"]):
            with gr.Row():
                transition = gr.Radio(choices=transition_choices(), value=transition_choices()[0], label="انتخاب بررسی / Transition")
                acquisition_mode = gr.Radio(choices=["pinned_owner_file_computation", "producer_emitted_gate_artifact"], value="pinned_owner_file_computation", label="Acquisition mode / روش دریافت شواهد")
                run_button = gr.Button("اجرای بررسی Project Gate", variant="primary")

        with gr.Accordion("ورودی JSON", open=True, elem_classes=["ev4-section", "ev4-json-section"]):
            json_file = gr.File(label="بارگذاری فایل JSON / Upload JSON", file_types=[".json"], type="filepath")
            json_text = gr.Textbox(label="چسباندن متن JSON / Paste JSON", lines=12, elem_classes=["ev4-ltr"], placeholder='{"schema_version": "..."}')

        with gr.Accordion("مسیر پوشه‌های local repository — نه GitHub URL", open=False, elem_classes=["ev4-section"]):
            project_gate_path = gr.Textbox(label="مسیر Project Gate repo / Project Gate path", placeholder="/path/to/EV4-Project-Gate", elem_classes=["ev4-ltr"])
            architect_path = gr.Textbox(label="مسیر Architect repo / Architect path", placeholder="/path/to/EV4-Architect-Repo", elem_classes=["ev4-ltr"])
            ce_path = gr.Textbox(label="مسیر CE repo / CE path", placeholder="/path/to/EV4-Constructability-Engineer-Repo", elem_classes=["ev4-ltr"])
            builder_path = gr.Textbox(label="مسیر Builder repo / Builder path", placeholder="/path/to/EV4-Builder-Assistant-Repo", elem_classes=["ev4-ltr"])
            responsive_path = gr.Textbox(label="مسیر Responsive repo / Responsive path", placeholder="/path/to/EV4-Responsive-Architect", elem_classes=["ev4-ltr"])
            gr.Markdown('<div lang="fa" dir="rtl" class="ev4-rtl ev4-helper-block">این مسیرها باید پوشه‌های local checkout باشند، نه URL گیت‌هاب.</div>')

        with gr.Accordion("بررسی آماده‌سازی مسیرها / Preflight", open=True, elem_classes=["ev4-section", "ev4-preflight-section"]):
            gr.Markdown(f'<div lang="fa" dir="rtl" class="ev4-rtl ev4-helper-block">{PREFLIGHT_HELPER_FA}</div>')
            preflight_button = gr.Button("بررسی مسیرها و ورودی‌ها")
            preflight_summary = gr.HTML(elem_classes=["ev4-rtl", "ev4-preflight-card"], elem_id="ev4-preflight-live")

        with gr.Accordion("خلاصه نتیجه", open=True, elem_classes=["ev4-section"]):
            status_summary = gr.HTML(elem_classes=["ev4-rtl", "ev4-status-card"], elem_id="ev4-status-live")

        with gr.Accordion("جزئیات پیشرفته / Diagnostics", open=False, elem_classes=["ev4-section"]):
            diagnostics = gr.Dataframe(headers=DIAGNOSTIC_HEADERS, datatype=["str", "str", "str", "str", "str", "str"], label="Diagnostics", interactive=False, elem_classes=["ev4-dataframe", "ev4-technical-table"])

        with gr.Accordion("وضعیت قابلیت‌ها / Capabilities", open=False, elem_classes=["ev4-section"]):
            capabilities = gr.Dataframe(value=build_capability_rows(), headers=CAPABILITY_HEADERS, datatype=["str", "str", "str", "str", "str", "str"], label="Capabilities", interactive=False, elem_classes=["ev4-dataframe", "ev4-technical-table"])

        with gr.Accordion("پیش‌نمایش JSON / result.json", open=False, elem_classes=["ev4-section"]):
            json_preview = gr.Code(language="json", label="result.json", elem_classes=["ev4-ltr", "ev4-code-preview"])

        downloads = gr.File(label="دانلود خروجی‌ها / result.json, report.md, report.html", file_count="multiple", elem_classes=["ev4-download", "ev4-ltr"])

        def _preflight(selected_transition, pasted, uploaded, project_gate, architect, ce, builder, responsive):
            request = build_gate_request(
                selected_transition,
                pasted_json=pasted,
                uploaded_file=uploaded,
                project_gate_repo_path=project_gate,
                architect_repo_path=architect,
                ce_repo_path=ce,
                builder_repo_path=builder,
                responsive_repo_path=responsive,
            )
            return preflight_result_html(run_preflight(request))

        def _run(selected_transition, selected_acquisition_mode, pasted, uploaded, project_gate, architect, ce, builder, responsive):
            output = run_operator_check(
                selected_transition,
                pasted_json=pasted,
                uploaded_file=uploaded,
                project_gate_repo_path=project_gate,
                architect_repo_path=architect,
                ce_repo_path=ce,
                builder_repo_path=builder,
                responsive_repo_path=responsive,
                acquisition_mode=selected_acquisition_mode,
            )
            return operator_run_outputs(output)

        preflight_button.click(lambda: "⏳ در حال بررسی آماده‌سازی…", outputs=[preflight_summary], queue=False).then(
            _preflight,
            inputs=[transition, json_text, json_file, project_gate_path, architect_path, ce_path, builder_path, responsive_path],
            outputs=[preflight_summary],
        )

        run_button.click(lambda: "⏳ در حال پردازش…", outputs=[status_summary], queue=False).then(
            _run,
            inputs=[transition, acquisition_mode, json_text, json_file, project_gate_path, architect_path, ce_path, builder_path, responsive_path],
            outputs=[status_summary, diagnostics, capabilities, json_preview, downloads],
        )

    return demo


def main() -> None:
    build_demo().launch()


if __name__ == "__main__":
    main()
