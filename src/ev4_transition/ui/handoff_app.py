from __future__ import annotations

from html import escape
from typing import Any

from ev4_transition.canonical_json import canonical_dumps
from ev4_transition.service.models import RepoPaths
from ev4_transition.service.producer_handoff import (
    ProducerHandoffRequest,
    inspect_producer_handoff_request,
    run_producer_handoff_request,
)

from .app import operator_gradio_theme, operator_panel_css
from .components import DIAGNOSTIC_HEADERS, diagnostics_to_rows, status_summary_markdown


HEADER_FA = "یک Producer Gate Export را انتخاب کنید؛ Project Gate مسیر Architect→CE یا CE→Builder را از قرارداد معتبر تشخیص می‌دهد."


def inspect_uploaded_route(source_path: str | None, project_gate_repo: str | None = None) -> dict[str, Any]:
    if not source_path:
        return {
            "status": "invalid",
            "resolved_transition": None,
            "routing": {"required_repository_roles": []},
            "user_message_fa": "ابتدا یک فایل Producer Gate Export انتخاب کنید.",
        }
    return inspect_producer_handoff_request(
        source_path,
        project_gate_repo_path=project_gate_repo or ".",
    ).to_dict()


def route_summary_html(payload: dict[str, Any]) -> str:
    routing = payload.get("routing") if isinstance(payload.get("routing"), dict) else {}
    status = escape(str(payload.get("status", "invalid")))
    source = escape(str(routing.get("producer_stage") or "unknown"))
    target = escape(str(routing.get("target_stage") or "unknown"))
    transition = escape(str(payload.get("resolved_transition") or "not_resolved"))
    message = escape(str(payload.get("user_message_fa") or ""))
    return (
        '<section lang="fa" dir="rtl" role="status" class="ev4-status-content">'
        "<h3>مسیر تشخیص‌داده‌شده</h3>"
        f"<p>{message}</p>"
        f'<p><strong>status:</strong> <bdi dir="ltr">{status}</bdi></p>'
        f'<p><strong>source:</strong> <bdi dir="ltr">{source}</bdi> '
        f'→ <strong>target:</strong> <bdi dir="ltr">{target}</bdi></p>'
        f'<p><strong>transition:</strong> <bdi dir="ltr">{transition}</bdi></p>'
        "</section>"
    )


def run_uploaded_handoff(
    source_path: str | None,
    project_gate_repo: str | None,
    architect_repo: str | None,
    ce_repo: str | None,
    builder_repo: str | None,
    output_dir: str | None,
) -> tuple[str, list[list[str]], str, list[str]]:
    if not source_path:
        payload = {
            "status": "invalid",
            "diagnostics": [
                {
                    "code": "PG.UI.PRODUCER_EXPORT_REQUIRED",
                    "severity": "error",
                    "path": "$.source_path",
                    "message": "Producer Gate Export file is required.",
                }
            ],
        }
        return status_summary_markdown(payload), diagnostics_to_rows(payload["diagnostics"]), canonical_dumps(payload), []

    response = run_producer_handoff_request(
        ProducerHandoffRequest(
            source_path=source_path,
            repo_paths=RepoPaths(
                project_gate_repo_path=(project_gate_repo or ".").strip() or ".",
                architect_repo_path=_clean(architect_repo),
                ce_repo_path=_clean(ce_repo),
                builder_repo_path=_clean(builder_repo),
            ),
            output_dir=_clean(output_dir),
        )
    )
    payload = response.to_dict()
    engine = payload["engine_result"]
    return (
        status_summary_markdown(engine),
        diagnostics_to_rows(payload.get("diagnostics", [])),
        canonical_dumps(payload),
        list(payload.get("download_paths", [])),
    )


def build_demo():
    try:
        import gradio as gr
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Gradio is required. Install with: uv sync --extra ui") from exc

    with gr.Blocks(
        title="EV4 Project Gate Unified Producer Handoff",
        theme=operator_gradio_theme(gr),
        css=operator_panel_css(),
    ) as demo:
        gr.HTML(
            '<section lang="fa" dir="rtl" class="ev4-header ev4-shell">'
            '<div class="ev4-header-kicker">S-003 / PG-INT</div>'
            '<h1 class="ev4-header-title"><bdi dir="ltr">EV4 Project Gate</bdi> — Unified Producer Handoff</h1>'
            f'<p class="ev4-helper">{escape(HEADER_FA)}</p>'
            '<p class="ev4-warning">این ابزار CE یا Builder را اجرا نمی‌کند؛ فقط خروجی مستقل مرحله بعد و receipt را می‌سازد.</p>'
            "</section>"
        )

        with gr.Group(elem_classes=["ev4-section"]):
            source = gr.File(
                label="Producer Gate Export JSON",
                file_types=[".json"],
                type="filepath",
            )
            project_gate = gr.Textbox(
                label="مسیر local Project Gate",
                value=".",
                elem_classes=["ev4-ltr"],
            )
            route = gr.HTML(
                '<section lang="fa" dir="rtl" class="ev4-status-content">فایل را انتخاب کنید تا مسیر معتبر تشخیص داده شود.</section>'
            )

        with gr.Accordion("مسیرهای local repository موردنیاز", open=True, elem_classes=["ev4-section"]):
            architect = gr.Textbox(
                label="Architect checkout",
                visible=False,
                elem_classes=["ev4-ltr"],
            )
            ce = gr.Textbox(
                label="CE checkout",
                visible=False,
                elem_classes=["ev4-ltr"],
            )
            builder = gr.Textbox(
                label="Builder checkout",
                visible=False,
                elem_classes=["ev4-ltr"],
            )
            output_dir = gr.Textbox(
                label="Output directory — اختیاری",
                placeholder="خالی بگذارید تا پوشه موقت امن داخل workspace ساخته شود",
                elem_classes=["ev4-ltr"],
            )

        run_button = gr.Button("اجرای handoff معتبر", variant="primary")
        status = gr.HTML(elem_classes=["ev4-status-card"])
        diagnostics = gr.Dataframe(
            headers=DIAGNOSTIC_HEADERS,
            datatype=["str", "str", "str", "str", "str", "str"],
            interactive=False,
            label="Diagnostics",
            elem_classes=["ev4-dataframe", "ev4-technical-table"],
        )
        with gr.Accordion("جزئیات فنی", open=False):
            preview = gr.Code(language="json", label="Structured service result")
        downloads = gr.File(
            label="خروجی مستقل مرحله بعد و Project Gate receipt",
            file_count="multiple",
        )

        def _inspect(source_path, project_gate_path):
            payload = inspect_uploaded_route(source_path, project_gate_path)
            routing = payload.get("routing") if isinstance(payload.get("routing"), dict) else {}
            roles = set(routing.get("required_repository_roles") or [])
            return (
                route_summary_html(payload),
                gr.update(visible="architect" in roles),
                gr.update(visible="ce" in roles),
                gr.update(visible="builder" in roles),
            )

        source.change(
            _inspect,
            inputs=[source, project_gate],
            outputs=[route, architect, ce, builder],
        )
        project_gate.change(
            _inspect,
            inputs=[source, project_gate],
            outputs=[route, architect, ce, builder],
        )
        run_button.click(
            run_uploaded_handoff,
            inputs=[source, project_gate, architect, ce, builder, output_dir],
            outputs=[status, diagnostics, preview, downloads],
        )

    return demo


def _clean(value: str | None) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def main() -> None:
    build_demo().launch()


if __name__ == "__main__":
    main()
