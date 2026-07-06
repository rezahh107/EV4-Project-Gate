from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import json
from html import escape
import logging
from pathlib import Path
import shutil
import tempfile
from typing import Any

from ev4_transition.canonical_json import canonical_dumps, load_json_file
from ev4_transition.service import GateRequest, RepoPaths, run_gate_request

from .components import capability_rows_from_payload, diagnostics_to_rows, status_summary_markdown
from .state import option_for_label


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CAPABILITY_STATUS_PATH = PACKAGE_ROOT / "data" / "capability-status.v1.json"
LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class UiRunOutput:
    result: dict[str, Any]
    status_markdown: str
    diagnostics_rows: list[list[str]]
    capability_rows: list[list[str]]
    json_preview: str
    download_paths: list[str]


@dataclass(frozen=True)
class ErrorState:
    code: str
    message_fa: str
    next_action_fa: str
    error_type: str

    def to_result(self, transition_choice: str) -> dict[str, Any]:
        return {
            "schema_version": "ev4-project-gate-ui-result.v1",
            "result_type": "ui_error_state",
            "transition_choice": transition_choice,
            "status": "invalid",
            "diagnostics": [
                {
                    "code": self.code,
                    "severity": "error",
                    "message": self.message_fa,
                    "path": "$",
                    "details": {"error_type": self.error_type, "next_action": self.next_action_fa},
                }
            ],
            "output": None,
        }


def run_operator_check(
    transition_label: str | None,
    pasted_json: str | None = None,
    uploaded_file: Any | None = None,
    project_gate_repo_path: str | None = None,
    architect_repo_path: str | None = None,
    ce_repo_path: str | None = None,
    builder_repo_path: str | None = None,
    responsive_repo_path: str | None = None,
    *,
    output_dir: str | Path | None = None,
) -> UiRunOutput:
    """Run the selected UI action through the internal Project Gate service API."""

    option = option_for_label(transition_label)
    choice = option.service_choice
    try:
        request = build_gate_request(
            transition_label,
            pasted_json=pasted_json,
            uploaded_file=uploaded_file,
            project_gate_repo_path=project_gate_repo_path,
            architect_repo_path=architect_repo_path,
            ce_repo_path=ce_repo_path,
            builder_repo_path=builder_repo_path,
            responsive_repo_path=responsive_repo_path,
        )
        response = run_gate_request(request)
        result = _result_from_response(response)
    except Exception as exc:  # Defensive UI boundary; primary view must not expose traceback.
        LOGGER.exception("Unhandled exception in UI operator check")
        result = ErrorState(
            code="PG.UI.UNHANDLED_EXCEPTION",
            message_fa="اجرای UI با خطای کنترل‌شده متوقف شد و traceback خام در نمای اصلی نمایش داده نشد.",
            next_action_fa="گزارش فنی را دانلود کن و خطای مسیر، JSON، یا وابستگی محلی را بررسی کن.",
            error_type=type(exc).__name__,
        ).to_result(choice)
    try:
        return _finalize(result, output_dir)
    except Exception as exc:  # Final UI rendering fallback; do not let report/capability failures crash the panel.
        LOGGER.exception("Critical failure while finalizing UI operator output")
        fallback = ErrorState(
            code="PG.UI.CRITICAL_FINALIZATION_FAILURE",
            message_fa="آماده‌سازی خروجی UI با خطای کنترل‌شده متوقف شد و traceback خام در نمای اصلی نمایش داده نشد.",
            next_action_fa="گزارش technical/log را بررسی کن و فایل capability یا مسیر خروجی را اصلاح کن.",
            error_type=type(exc).__name__,
        ).to_result(choice)
        return _minimal_output(fallback)


def build_gate_request(
    transition_label: str | None,
    *,
    pasted_json: str | None = None,
    uploaded_file: Any | None = None,
    project_gate_repo_path: str | None = None,
    architect_repo_path: str | None = None,
    ce_repo_path: str | None = None,
    builder_repo_path: str | None = None,
    responsive_repo_path: str | None = None,
) -> GateRequest:
    option = option_for_label(transition_label)
    input_text = pasted_json if pasted_json and pasted_json.strip() else None
    input_path = _uploaded_path(uploaded_file) if input_text is None else None
    return GateRequest(
        transition_choice=option.service_choice,  # type: ignore[arg-type]
        input_json_path=input_path,
        input_json_text=input_text,
        repo_paths=RepoPaths(
            project_gate_repo_path=_clean_path(project_gate_repo_path) or str(REPOSITORY_ROOT),
            architect_repo_path=_clean_path(architect_repo_path),
            ce_repo_path=_clean_path(ce_repo_path),
            builder_repo_path=_clean_path(builder_repo_path),
            responsive_repo_path=_clean_path(responsive_repo_path),
        ),
    )


def load_capability_payload(path: str | Path = CAPABILITY_STATUS_PATH) -> dict[str, Any]:
    payload = load_json_file(path)
    if not isinstance(payload, dict):
        raise ValueError("capability-status.v1.json must contain a JSON object")
    return payload


def build_capability_rows(path: str | Path = CAPABILITY_STATUS_PATH) -> list[list[str]]:
    return capability_rows_from_payload(load_capability_payload(path))


def render_download_artifacts(result: dict[str, Any], output_dir: str | Path | None = None) -> list[str]:
    directory = Path(output_dir) if output_dir is not None else Path(tempfile.mkdtemp(prefix="ev4_project_gate_ui_"))
    written_paths: list[Path] = []
    try:
        directory.mkdir(parents=True, exist_ok=True)
        files = {
            "result.json": canonical_dumps(deepcopy(result)),
            "report.md": _markdown_report(result),
            "report.html": _html_report(result),
        }
        paths: list[str] = []
        for name, content in files.items():
            path = directory / name
            path.write_text(content, encoding="utf-8")
            written_paths.append(path)
            paths.append(str(path))
        return paths
    except OSError as exc:
        LOGGER.error("Failed to render download artifacts: %s", exc)
        for path in written_paths:
            path.unlink(missing_ok=True)
        if output_dir is None:
            shutil.rmtree(directory, ignore_errors=True)
        return []


def _minimal_output(result: dict[str, Any]) -> UiRunOutput:
    return UiRunOutput(
        result=result,
        status_markdown=status_summary_markdown(result),
        diagnostics_rows=diagnostics_to_rows(result.get("diagnostics", [])),
        capability_rows=[],
        json_preview=canonical_dumps(result),
        download_paths=[],
    )


def _result_from_response(response: Any) -> dict[str, Any]:
    payload = response.to_dict()
    diagnostics = list(payload.get("service_diagnostics") or [])
    engine_result = payload.get("engine_result")
    if isinstance(engine_result, dict) and isinstance(engine_result.get("diagnostics"), list):
        diagnostics.extend(deepcopy(engine_result["diagnostics"]))
    return {
        "schema_version": "ev4-project-gate-ui-result.v1",
        "result_type": "service_response",
        "transition_choice": payload.get("transition_choice"),
        "status": payload.get("status", "invalid"),
        "user_message_fa": payload.get("user_message_fa", ""),
        "next_action_fa": payload.get("next_action_fa", ""),
        "diagnostics": diagnostics,
        "engine_result": engine_result,
        "capabilities_snapshot": payload.get("capabilities_snapshot"),
        "download_filenames": payload.get("download_filenames", {}),
        "report_bundle": payload.get("report_bundle", {}),
        "output": engine_result.get("output") if isinstance(engine_result, dict) else None,
    }


def _uploaded_path(uploaded_file: Any | None) -> str | None:
    if uploaded_file is None:
        return None
    if isinstance(uploaded_file, str):
        return uploaded_file
    name = getattr(uploaded_file, "name", None)
    return str(name) if name else None


def _clean_path(value: str | None) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _markdown_report(result: dict[str, Any]) -> str:
    safe_json = _neutralize_markdown_fences(canonical_dumps(result))
    return "\n".join(["# گزارش Project Gate Operator Panel", "", f"status: `{result.get('status', 'invalid')}`", "", "```json", safe_json, "```", ""])


def _neutralize_markdown_fences(value: str) -> str:
    return value.replace("```", "``\u200b`")


def _html_report(result: dict[str, Any]) -> str:
    escaped_json = escape(json.dumps(result, ensure_ascii=False, indent=2))
    return (
        '<!doctype html><html lang="fa" dir="rtl">'
        '<meta charset="utf-8"><title>Project Gate Report</title>'
        f'<pre dir="ltr">{escaped_json}</pre></html>'
    )


def _finalize(result: dict[str, Any], output_dir: str | Path | None) -> UiRunOutput:
    downloads = render_download_artifacts(result, output_dir)
    if not downloads:
        result = deepcopy(result)
        result.setdefault("diagnostics", []).append(
            {
                "code": "PG.UI.REPORT_WRITE_FAILED",
                "severity": "error",
                "message": "نوشتن فایل‌های گزارش انجام نشد؛ لینک دانلود موفق نمایش داده نمی‌شود.",
                "path": "$.downloads",
                "details": {"next_action": "مجوز نوشتن output directory را بررسی کن."},
            }
        )
        result["status"] = "invalid"
    capability_payload = result.get("capabilities_snapshot") if isinstance(result.get("capabilities_snapshot"), dict) else load_capability_payload()
    return UiRunOutput(
        result=result,
        status_markdown=status_summary_markdown(result),
        diagnostics_rows=diagnostics_to_rows(result.get("diagnostics", [])),
        capability_rows=capability_rows_from_payload(capability_payload),
        json_preview=canonical_dumps(result),
        download_paths=downloads,
    )
