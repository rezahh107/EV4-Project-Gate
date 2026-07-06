from __future__ import annotations

from .adapters import build_capability_rows, run_operator_check
from .components import CAPABILITY_HEADERS, DIAGNOSTIC_HEADERS
from .state import transition_choices


HEADER_WARNING_FA = (
    "این ابزار فقط بررسی گیت را اجرا می‌کند؛ اثبات نهایی تولید، فرانت‌اند، "
    "Elementor واقعی یا صحت Responsive نیست."
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
        css="""
        .ev4-rtl, .ev4-rtl textarea { direction: rtl; text-align: right; }
        .ev4-ltr, .ev4-ltr textarea, .ev4-ltr code, .ev4-ltr pre { direction: ltr; text-align: left; unicode-bidi: isolate; }
        """,
    ) as demo:
        gr.Markdown(
            f"""
<div lang="fa" dir="rtl" class="ev4-rtl">

# EV4 Project Gate Local Operator Panel

**هشدار:** {HEADER_WARNING_FA}

این پنل محلی است و برای کاربر غیر CLI ساخته شده است: JSON را بارگذاری یا paste کن، transition مجاز را انتخاب کن، نتیجه فارسی و diagnostics را ببین، و خروجی‌ها را دانلود کن.

</div>
"""
        )

        with gr.Row():
            transition = gr.Radio(
                choices=transition_choices(),
                value=transition_choices()[0],
                label="Transition selector / انتخاب بررسی",
            )
            run_button = gr.Button("اجرای بررسی Project Gate", variant="primary")

        with gr.Accordion("ورودی JSON", open=True):
            json_file = gr.File(label="Upload JSON file / بارگذاری فایل JSON", file_types=[".json"], type="filepath")
            json_text = gr.Textbox(
                label="Paste JSON text / چسباندن JSON",
                lines=12,
                elem_classes=["ev4-ltr"],
                placeholder='{"schema_version": "..."}',
            )

        with gr.Accordion("مسیرهای local repository — GitHub URL وارد نکن", open=False):
            project_gate_path = gr.Textbox(label="Project Gate repo path", placeholder="/path/to/EV4-Project-Gate")
            architect_path = gr.Textbox(label="Architect repo path", placeholder="/path/to/EV4-Architect-Repo")
            ce_path = gr.Textbox(label="CE repo path", placeholder="/path/to/EV4-Constructability-Engineer-Repo")
            builder_path = gr.Textbox(label="Builder repo path", placeholder="/path/to/EV4-Builder-Assistant-Repo")
            responsive_path = gr.Textbox(label="Responsive repo path", placeholder="/path/to/EV4-Responsive-Architect")
            gr.Markdown(
                '<div lang="fa" dir="rtl" class="ev4-rtl">این مسیرها باید پوشه‌های local checkout باشند، نه URL گیت‌هاب.</div>'
            )

        with gr.Accordion("خلاصه نتیجه", open=True):
            status_summary = gr.Markdown(elem_classes=["ev4-rtl"])

        with gr.Accordion("Diagnostics / جزئیات پیشرفته", open=False):
            diagnostics = gr.Dataframe(
                headers=DIAGNOSTIC_HEADERS,
                datatype=["str", "str", "str", "str", "str", "str"],
                label="Diagnostics",
                interactive=False,
            )

        with gr.Accordion("Capabilities / وضعیت قابلیت‌ها", open=False):
            capabilities = gr.Dataframe(
                value=build_capability_rows(),
                headers=CAPABILITY_HEADERS,
                datatype=["str", "str", "str", "str", "str", "str"],
                label="Capabilities",
                interactive=False,
            )

        with gr.Accordion("JSON preview / پیش‌نمایش خروجی", open=False):
            json_preview = gr.Code(language="json", label="result.json")

        downloads = gr.File(label="Download result.json / report.md / report.html", file_count="multiple")

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

        run_button.click(
            _run,
            inputs=[transition, json_text, json_file, project_gate_path, architect_path, ce_path, builder_path, responsive_path],
            outputs=[status_summary, diagnostics, capabilities, json_preview, downloads],
        )

    return demo


def main() -> None:
    build_demo().launch()


if __name__ == "__main__":
    main()
