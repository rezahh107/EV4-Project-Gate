from __future__ import annotations

from html import escape
import json
import os
from pathlib import Path
from typing import Any

from ev4_transition.presentation.theme_tokens import THEME_TOKENS, css_custom_properties
from ev4_transition.service.preflight import run_preflight
from ev4_transition.runners.open_output_folder import open_directory

from .adapters import build_capability_rows, build_gate_request, run_operator_check
from .components import CAPABILITY_HEADERS, DIAGNOSTIC_HEADERS
from .operator_settings import default_settings, load_settings, reset_settings, save_settings, settings_path
from .preflight_components import preflight_result_html
from .source_preflight import classify_source_file
from .state import transition_choices

HEADER_WARNING_FA = (
    "این پنل مسیر authoritative Project Gate را اجرا می‌کند؛ موفقیت فقط پس از validatorهای رسمی و publication تأییدشده نمایش داده می‌شود."
)
HEADER_HELPER_FA = (
    "فایل اصلی JSON را بارگذاری کنید، مسیر تشخیص‌داده‌شده و checkoutهای local را بازبینی کنید، سپس Preflight و اجرا را انجام دهید. عملیات عادی به CLI نیاز ندارد."
)
PREFLIGHT_HELPER_FA = (
    "پیش‌بررسی، نوع artifact، acquisition mode و مسیرهای local را کنترل می‌کند. دکمه اجرا فقط پس از Preflight قابل استفاده است."
)


def operator_header_html() -> str:
    return f"""
<section lang="fa" dir="rtl" class="ev4-app ev4-rtl">
  <header class="ev4-header ev4-shell" aria-label="EV4 Project Gate local operator panel">
    <div class="ev4-header-kicker">Local Operator Panel</div>
    <div class="ev4-header-title-row">
      <h1 class="ev4-header-title"><bdi dir="ltr">EV4 Project Gate</bdi></h1>
      <span class="ev4-header-badge">authoritative gate runner</span>
    </div>
    <p class="ev4-header-subtitle">پنل محلی اجرای گذارهای کنترل‌شده</p>
    <p class="ev4-warning">⚠️ {HEADER_WARNING_FA}</p>
    <p class="ev4-helper">{HEADER_HELPER_FA}</p>
  </header>
</section>
"""


def operator_gradio_theme(gr: Any) -> Any:
    light = THEME_TOKENS["light"]
    dark = THEME_TOKENS["dark"]
    return gr.themes.Base(
        primary_hue="blue",
        secondary_hue="slate",
        neutral_hue="slate",
        spacing_size="md",
        radius_size="lg",
        text_size="md",
        font=["Vazirmatn", "Vazir", "IRANSansX", "Tahoma", "system-ui", "sans-serif"],
        font_mono=["Cascadia Code", "JetBrains Mono", "Consolas", "monospace"],
    ).set(
        body_background_fill=light["surface.base"],
        body_background_fill_dark=dark["surface.base"],
        body_text_color=light["text.primary"],
        body_text_color_dark=dark["text.primary"],
        block_background_fill=light["surface.raised"],
        block_background_fill_dark=dark["surface.raised"],
        block_border_color=light["border.default"],
        block_border_color_dark=dark["border.default"],
        input_background_fill=light["input.bg"],
        input_background_fill_dark=dark["input.bg"],
        input_border_color=light["input.border"],
        input_border_color_dark=dark["input.border"],
        button_primary_background_fill=light["button.primary.bg"],
        button_primary_background_fill_dark=dark["button.primary.bg"],
        button_primary_background_fill_hover=light["button.primary.hover.bg"],
        button_primary_background_fill_hover_dark=dark["button.primary.hover.bg"],
        button_primary_text_color=light["button.primary.text"],
        button_primary_text_color_dark=dark["button.primary.text"],
        button_secondary_background_fill=light["button.secondary.bg"],
        button_secondary_background_fill_dark=dark["button.secondary.bg"],
        button_secondary_text_color=light["button.secondary.text"],
        button_secondary_text_color_dark=dark["button.secondary.text"],
        code_background_fill=light["code.bg"],
        code_background_fill_dark=dark["code.bg"],
    )


def operator_panel_css() -> str:
    return css_custom_properties() + """
    .gradio-container { color-scheme: light dark; background: var(--ev4-surface-base) !important; color: var(--ev4-text-primary) !important; font-family: var(--ev4-font-fa-ui); font-size: 16px; line-height: 1.7; }
    .ev4-app, .ev4-shell, .ev4-rtl, .ev4-rtl textarea, .ev4-rtl input { direction: rtl; text-align: right; font-family: var(--ev4-font-fa-ui); line-height: 1.75; letter-spacing: normal; }
    .ev4-shell { max-width: 1120px; margin: 0 auto 0.75rem; }
    .ev4-header, .ev4-section, .ev4-dataframe, .ev4-download, .ev4-status-content, .ev4-preflight-result { background: var(--ev4-surface-raised); border: 1px solid var(--ev4-border-default); border-radius: 16px; padding: 0.75rem; box-shadow: 0 14px 34px var(--ev4-shadow-raised); }
    .ev4-header { padding: 1.15rem 1.25rem; }
    body.dark .ev4-header, .dark .ev4-header, :root[data-theme="dark"] .ev4-header { background: linear-gradient(145deg, var(--ev4-surface-raised), var(--ev4-surface-overlay)) !important; color: var(--ev4-text-primary) !important; border-color: var(--ev4-border-default) !important; }
    @media (prefers-color-scheme: dark) { body:not(.light) .ev4-header { background: linear-gradient(145deg, var(--ev4-surface-raised), var(--ev4-surface-overlay)) !important; color: var(--ev4-text-primary) !important; } }
    .ev4-header-title-row { display: flex; flex-wrap: wrap; align-items: baseline; justify-content: space-between; gap: .65rem 1rem; }
    .ev4-header-title { margin: 0; color: var(--ev4-text-primary); }
    .ev4-header-kicker, .ev4-header-subtitle, .ev4-helper { color: var(--ev4-text-secondary); }
    .ev4-header-badge { color: var(--ev4-info); background: var(--ev4-info-bg); border-radius: 999px; padding: .18rem .55rem; }
    .ev4-warning { color: var(--ev4-status-warning-fg); background: var(--ev4-status-warning-bg); border-radius: 12px; padding: .6rem .75rem; font-weight: 650; }
    .ev4-ltr textarea, .ev4-ltr input, .ev4-ltr code, .ev4-ltr pre, code, pre { direction: ltr; text-align: left; unicode-bidi: isolate; font-family: var(--ev4-font-code); }
    .gradio-container input[type="radio"] { appearance: none; -webkit-appearance: none; inline-size: 1.1rem; block-size: 1.1rem; border: 2px solid var(--ev4-control-indicator-border) !important; border-radius: 999px; background: var(--ev4-control-indicator-bg) !important; }
    .gradio-container input[type="radio"]:checked { border-color: var(--ev4-control-indicator-checked-bg) !important; background: radial-gradient(circle, var(--ev4-control-indicator-checked-dot) 34%, transparent 36%), var(--ev4-control-indicator-checked-bg) !important; }
    .gradio-container input[type="radio"]:focus-visible { outline: 3px solid var(--ev4-control-indicator-focus-ring) !important; outline-offset: 3px; }
    .gradio-container button.primary, .gradio-container button[variant="primary"] { background: var(--ev4-button-primary-bg) !important; color: var(--ev4-button-primary-text) !important; font-weight: 700; }
    .gradio-container button.primary:hover, .gradio-container button[variant="primary"]:hover { background: var(--ev4-button-primary-hover-bg) !important; color: var(--ev4-button-primary-hover-text) !important; }
    .gradio-container button:not(.primary):not([variant="primary"]) { background: var(--ev4-button-secondary-bg) !important; color: var(--ev4-button-secondary-text) !important; }
    .gradio-container button:not(.primary):not([variant="primary"]):hover { background: var(--ev4-button-secondary-hover-bg) !important; color: var(--ev4-button-secondary-hover-text) !important; }
    .gradio-container :disabled, .gradio-container [aria-disabled="true"] { background: var(--ev4-disabled-bg) !important; color: var(--ev4-disabled-text) !important; cursor: not-allowed; opacity: 1 !important; }
    .ev4-classification { border-inline-start: 5px solid var(--ev4-info); }
    """


def operator_run_outputs(output: Any) -> tuple[Any, Any, Any, str, Any]:
    return output.status_markdown, output.diagnostics_rows, output.capability_rows, output.json_preview, output.download_paths


def build_demo():
    try:
        import gradio as gr
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Gradio is required. Install with: python -m pip install -e '.[ui]'") from exc

    settings = load_settings()
    with gr.Blocks(title="EV4 Project Gate Local Operator Panel", theme=operator_gradio_theme(gr), css=operator_panel_css()) as demo:
        gr.HTML(operator_header_html())

        with gr.Group(elem_classes=["ev4-section"]):
            source_file = gr.File(label="فایل اصلی JSON / Original JSON file", file_types=[".json"], type="filepath")
            source_classification = gr.HTML('<section class="ev4-status-content ev4-classification" lang="fa" dir="rtl">فایل را انتخاب کنید تا نوع artifact و مسیر سازگار آشکارا تشخیص داده شود.</section>')
            with gr.Row():
                transition = gr.Radio(choices=transition_choices(), value=settings["default_transition"], label="Transition / مسیر")
                acquisition_mode = gr.Radio(
                    choices=["pinned_owner_file_computation", "producer_emitted_gate_artifact"],
                    value=settings["default_acquisition_mode"],
                    label="Acquisition mode / روش دریافت",
                )
            json_text = gr.Textbox(label="Paste JSON — فقط برای pinned_owner_file_computation", lines=5, elem_classes=["ev4-ltr"])

        with gr.Accordion("مسیرهای local repository و خروجی", open=True, elem_classes=["ev4-section"]):
            project_gate_path, project_gate_browse = _path_row(gr, "Project Gate repository", settings["project_gate_repo_path"])
            architect_path, architect_browse = _path_row(gr, "Architect repository", settings["architect_repo_path"])
            ce_path, ce_browse = _path_row(gr, "Constructability Engineer repository", settings["ce_repo_path"])
            builder_path, builder_browse = _path_row(gr, "Builder repository", settings["builder_repo_path"])
            responsive_path, responsive_browse = _path_row(gr, "Responsive repository", settings["responsive_repo_path"])
            output_dir, output_browse = _path_row(gr, "Default output directory", settings["default_output_directory"])
            with gr.Row():
                save_button = gr.Button("ذخیره مسیرها در تنظیمات محلی")
                reset_button = gr.Button("Reset to defaults")
            settings_status = gr.Markdown(f"تنظیمات محلی: `{settings_path()}`")

        with gr.Accordion("Preflight", open=True, elem_classes=["ev4-section"]):
            gr.Markdown(PREFLIGHT_HELPER_FA)
            preflight_button = gr.Button("بررسی نوع فایل و مسیرها")
            preflight_summary = gr.HTML()

        run_button = gr.Button("اجرای authoritative Project Gate", variant="primary", interactive=False)
        with gr.Accordion("خلاصه نتیجه", open=True, elem_classes=["ev4-section"]):
            status_summary = gr.HTML()
        with gr.Accordion("Diagnostics", open=True, elem_classes=["ev4-section"]):
            diagnostics = gr.Dataframe(headers=DIAGNOSTIC_HEADERS, datatype=["str"] * 6, interactive=False)
        with gr.Accordion("Capabilities", open=False, elem_classes=["ev4-section"]):
            capabilities = gr.Dataframe(value=build_capability_rows(), headers=CAPABILITY_HEADERS, datatype=["str"] * 6, interactive=False)
        with gr.Accordion("Structured result", open=False, elem_classes=["ev4-section"]):
            json_preview = gr.Code(language="json", label="result.json")
        downloads = gr.File(label="ce-input / receipt / reports", file_count="multiple")
        with gr.Row():
            open_folder_button = gr.Button("Open output folder", interactive=False)
            open_folder_status = gr.Markdown()

        def _classify(source, project_gate):
            payload = classify_source_file(source, project_gate)
            message = escape(str(payload.get("message_fa", "")))
            schema = escape(str(payload.get("source_schema") or "unknown"))
            html = f'<section class="ev4-status-content ev4-classification" lang="fa" dir="rtl"><p>{message}</p><p><b>schema:</b> <bdi dir="ltr">{schema}</bdi></p></section>'
            selected_transition = payload.get("selected_transition") or transition_choices()[0]
            selected_mode = payload.get("selected_acquisition_mode") or "pinned_owner_file_computation"
            return html, gr.update(value=selected_transition), gr.update(value=selected_mode), gr.update(interactive=False)

        def _preflight(selected_transition, selected_mode, pasted, uploaded, project_gate, architect, ce, builder, responsive, output):
            classification = classify_source_file(uploaded, project_gate) if uploaded else None
            if selected_mode == "producer_emitted_gate_artifact":
                ready = bool(
                    classification
                    and classification.get("status") == "source_classified"
                    and classification.get("selected_transition") == selected_transition
                    and not (pasted and pasted.strip())
                    and all(str(value or "").strip() for value in (project_gate, architect, ce, output))
                )
                summary = classification.get("message_fa", "") if classification else "فایل اصلی Producer Gate Export لازم است."
                if pasted and pasted.strip():
                    summary = "PG.UI.PRODUCER_SOURCE_FILE_REQUIRED — در حالت producer-emitted متن paste‌شده مجاز نیست."
                return f'<section class="ev4-preflight-result" lang="fa" dir="rtl"><p>{escape(summary)}</p><p>ready: <bdi dir="ltr">{str(ready).lower()}</bdi></p></section>', gr.update(interactive=ready)
            request = build_gate_request(
                selected_transition,
                pasted_json=pasted,
                uploaded_file=uploaded,
                project_gate_repo_path=project_gate,
                architect_repo_path=architect,
                ce_repo_path=ce,
                builder_repo_path=builder,
                responsive_repo_path=responsive,
                acquisition_mode=selected_mode,
                output_dir=output,
            )
            result = run_preflight(request)
            ready = result.status == "ready"
            return preflight_result_html(result), gr.update(interactive=ready)

        def _run(selected_transition, selected_mode, pasted, uploaded, project_gate, architect, ce, builder, responsive, output):
            result = run_operator_check(
                selected_transition,
                pasted_json=pasted,
                uploaded_file=uploaded,
                project_gate_repo_path=project_gate,
                architect_repo_path=architect,
                ce_repo_path=ce,
                builder_repo_path=builder,
                responsive_repo_path=responsive,
                acquisition_mode=selected_mode,
                output_dir=output,
            )
            open_enabled = bool(result.download_paths and Path(result.download_paths[0]).parent.is_dir())
            return (*operator_run_outputs(result), gr.update(interactive=open_enabled))

        source_file.change(_classify, inputs=[source_file, project_gate_path], outputs=[source_classification, transition, acquisition_mode, run_button])
        project_gate_path.change(_classify, inputs=[source_file, project_gate_path], outputs=[source_classification, transition, acquisition_mode, run_button])
        preflight_button.click(
            _preflight,
            inputs=[transition, acquisition_mode, json_text, source_file, project_gate_path, architect_path, ce_path, builder_path, responsive_path, output_dir],
            outputs=[preflight_summary, run_button],
        )
        run_button.click(
            _run,
            inputs=[transition, acquisition_mode, json_text, source_file, project_gate_path, architect_path, ce_path, builder_path, responsive_path, output_dir],
            outputs=[status_summary, diagnostics, capabilities, json_preview, downloads, open_folder_button],
        )

        for button, textbox in (
            (project_gate_browse, project_gate_path),
            (architect_browse, architect_path),
            (ce_browse, ce_path),
            (builder_browse, builder_path),
            (responsive_browse, responsive_path),
            (output_browse, output_dir),
        ):
            button.click(browse_directory, inputs=[textbox], outputs=[textbox])

        save_button.click(
            _save_settings_callback,
            inputs=[project_gate_path, architect_path, ce_path, builder_path, responsive_path, output_dir, transition, acquisition_mode],
            outputs=[settings_status],
        )
        reset_button.click(
            _reset_settings_callback,
            outputs=[project_gate_path, architect_path, ce_path, builder_path, responsive_path, output_dir, transition, acquisition_mode, settings_status, run_button],
        )
        open_folder_button.click(open_output_folder, inputs=[json_preview], outputs=[open_folder_status])

    return demo


def _path_row(gr: Any, label: str, value: str):
    with gr.Row():
        textbox = gr.Textbox(label=label, value=value, elem_classes=["ev4-ltr"], scale=8)
        button = gr.Button("Browse…", scale=1)
    return textbox, button


def browse_directory(current: str | None) -> str:
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        selected = filedialog.askdirectory(initialdir=current if current and Path(current).is_dir() else None)
        root.destroy()
        return selected or (current or "")
    except Exception:
        return current or ""


def _save_settings_callback(project_gate, architect, ce, builder, responsive, output, transition, mode):
    path = save_settings(
        {
            "project_gate_repo_path": project_gate,
            "architect_repo_path": architect,
            "ce_repo_path": ce,
            "builder_repo_path": builder,
            "responsive_repo_path": responsive,
            "default_output_directory": output,
            "default_transition": transition,
            "default_acquisition_mode": mode,
        }
    )
    return f"✅ تنظیمات محلی ذخیره شد: `{path}`"


def _reset_settings_callback():
    value = reset_settings()
    return (
        value["project_gate_repo_path"],
        value["architect_repo_path"],
        value["ce_repo_path"],
        value["builder_repo_path"],
        value["responsive_repo_path"],
        value["default_output_directory"],
        value["default_transition"],
        value["default_acquisition_mode"],
        "تنظیمات به defaults بازگردانده شد.",
        {"interactive": False},
    )


def open_output_folder(result_json: str | None) -> str:
    try:
        payload = json.loads(result_json or "{}")
        paths = payload.get("published_download_paths") or []
        if not paths:
            return "پوشه خروجی معتبر هنوز ایجاد نشده است."
        directory = Path(paths[0]).resolve().parent
        if not directory.is_dir():
            return "پوشه خروجی معتبر وجود ندارد."
        open_directory(directory)
        return f"پوشه باز شد: `{directory}`"
    except Exception as exc:
        return f"باز کردن پوشه ممکن نشد: `{type(exc).__name__}`"


def main() -> None:
    build_demo().launch()


if __name__ == "__main__":
    main()
