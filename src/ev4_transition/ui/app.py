from __future__ import annotations

from typing import Any

from ev4_transition.runners.open_output_folder import open_directory

from .adapters import build_capability_rows
from .app_callbacks import build_operator_callbacks
from .app_support import (
    HEADER_HELPER_FA,
    HEADER_WARNING_FA,
    PREFLIGHT_HELPER_FA,
    _path_row,
    _reset_settings_callback,
    _save_settings_callback,
    browse_directory,
    invalidate_preflight_state,
    open_output_folder as _open_output_folder,
    operator_gradio_theme,
    operator_header_html,
    operator_panel_css,
    operator_run_outputs,
    repository_field_affects_request,
    run_authoritative_preflight,
    workflow_state_html,
)
from .components import CAPABILITY_HEADERS, DIAGNOSTIC_HEADERS
from .operator_settings import load_settings, settings_path
from .state import initial_workflow_state, transition_choices

__all__ = [
    "HEADER_HELPER_FA",
    "HEADER_WARNING_FA",
    "PREFLIGHT_HELPER_FA",
    "browse_directory",
    "build_demo",
    "invalidate_preflight_state",
    "main",
    "open_directory",
    "open_output_folder",
    "operator_gradio_theme",
    "operator_header_html",
    "operator_panel_css",
    "operator_run_outputs",
    "repository_field_affects_request",
    "run_authoritative_preflight",
    "workflow_state_html",
]


def open_output_folder(attempt_directory: str | None) -> str:
    """Compatibility facade preserving the established open-directory patch seam."""

    return _open_output_folder(attempt_directory, opener=open_directory)


def build_demo():
    try:
        import gradio as gr
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Gradio is required. Install with: python -m pip install -e '.[ui]'") from exc

    settings = load_settings()
    initial_state = initial_workflow_state()
    with gr.Blocks(title="EV4 Project Gate Local Operator Panel", theme=operator_gradio_theme(gr), css=operator_panel_css()) as demo:
        gr.HTML(operator_header_html())
        workflow_state = gr.State(initial_state)
        prepared_operation = gr.State(None)
        executed_operation = gr.State(None)
        verified_attempt_directory = gr.State(None)

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
            kernel_path, kernel_browse = _path_row(gr, "Decision Kernel repository", settings["kernel_repo_path"])
            output_dir, output_browse = _path_row(gr, "Default output directory", settings["default_output_directory"])
            with gr.Row():
                save_button = gr.Button("ذخیره مسیرها در تنظیمات محلی")
                reset_button = gr.Button("Reset to defaults")
            settings_status = gr.Markdown(f"تنظیمات محلی: `{settings_path()}`")

        workflow_status = gr.HTML(workflow_state_html(initial_state))
        with gr.Accordion("Preflight diagnostic preview", open=True, elem_classes=["ev4-section"]):
            gr.Markdown(PREFLIGHT_HELPER_FA)
            preflight_button = gr.Button("فقط نمایش Authoritative Preflight")
            preflight_summary = gr.HTML()

        run_button = gr.Button("بررسی و اجرای Authoritative Project Gate", variant="primary", interactive=True)
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

        callbacks = build_operator_callbacks(gr)

        source_file.change(
            callbacks.classify_source,
            inputs=[source_file, project_gate_path, workflow_state],
            outputs=[
                source_classification, transition, acquisition_mode, workflow_state, workflow_status,
                preflight_summary, prepared_operation, executed_operation, verified_attempt_directory,
                open_folder_button, run_button,
            ],
        )
        project_gate_path.change(
            callbacks.classify_project_gate,
            inputs=[source_file, project_gate_path, transition, acquisition_mode, workflow_state],
            outputs=[
                source_classification, workflow_state, workflow_status, preflight_summary,
                prepared_operation, executed_operation, verified_attempt_directory,
                open_folder_button, run_button,
            ],
        )

        for authority_input, field_name in (
            (transition, "transition_choice"),
            (acquisition_mode, "acquisition_mode"),
            (json_text, "source"),
            (architect_path, "architect_repo_path"),
            (ce_path, "ce_repo_path"),
            (builder_path, "builder_repo_path"),
            (responsive_path, "responsive_repo_path"),
            (kernel_path, "kernel_repo_path"),
            (output_dir, "output_dir"),
        ):
            authority_input.change(
                lambda state, selected_transition, selected_mode, field=field_name: callbacks.invalidate(state, selected_transition, selected_mode, field),
                inputs=[workflow_state, transition, acquisition_mode],
                outputs=[
                    workflow_state, workflow_status, preflight_summary, prepared_operation,
                    executed_operation, verified_attempt_directory, open_folder_button,
                ],
            )

        preflight_button.click(
            callbacks.preview,
            inputs=[
                transition, acquisition_mode, json_text, source_file, project_gate_path,
                architect_path, ce_path, builder_path, responsive_path, kernel_path, output_dir,
                workflow_state,
            ],
            outputs=[preflight_summary, diagnostics, workflow_state, workflow_status],
        )

        run_event = run_button.click(
            callbacks.begin,
            inputs=[workflow_state],
            outputs=[workflow_state, workflow_status, run_button, preflight_button, prepared_operation, executed_operation],
        )
        prepare_event = run_event.then(
            callbacks.prepare,
            inputs=[
                transition, acquisition_mode, json_text, source_file, project_gate_path,
                architect_path, ce_path, builder_path, responsive_path, kernel_path, output_dir,
                workflow_state,
            ],
            outputs=[prepared_operation, workflow_state, workflow_status, preflight_summary, diagnostics],
        )
        execute_event = prepare_event.then(
            callbacks.execute,
            inputs=[prepared_operation, workflow_state],
            outputs=[executed_operation, workflow_state, workflow_status],
        )
        execute_event.then(
            callbacks.finalize,
            inputs=[executed_operation, workflow_state],
            outputs=[
                status_summary, diagnostics, capabilities, json_preview, downloads,
                open_folder_button, verified_attempt_directory, workflow_state,
                workflow_status, run_button, preflight_button,
            ],
        )

        for button, textbox in (
            (project_gate_browse, project_gate_path),
            (architect_browse, architect_path),
            (ce_browse, ce_path),
            (builder_browse, builder_path),
            (responsive_browse, responsive_path),
            (kernel_browse, kernel_path),
            (output_browse, output_dir),
        ):
            button.click(browse_directory, inputs=[textbox], outputs=[textbox])

        save_button.click(
            _save_settings_callback,
            inputs=[project_gate_path, architect_path, ce_path, builder_path, responsive_path, kernel_path, output_dir, transition, acquisition_mode],
            outputs=[settings_status],
        )
        reset_button.click(
            _reset_settings_callback,
            inputs=[workflow_state],
            outputs=[
                project_gate_path, architect_path, ce_path, builder_path, responsive_path,
                kernel_path, output_dir, transition, acquisition_mode, settings_status,
                workflow_state, workflow_status, preflight_summary, prepared_operation,
                executed_operation, verified_attempt_directory, open_folder_button, run_button,
            ],
        )
        open_folder_button.click(open_output_folder, inputs=[verified_attempt_directory], outputs=[open_folder_status])

    return demo




def main() -> None:
    build_demo().launch()


if __name__ == "__main__":
    main()
