from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import json
import logging
from pathlib import Path
from typing import Any

from ev4_transition.canonical_json import canonical_dumps, load_json_file
from ev4_transition.presentation.rtl import bdi_ltr, escape_html, ltr_code_block
from ev4_transition.service import GateRequest, RepoPaths, ServiceDiagnostic, run_gate_request, run_preflight
from ev4_transition.service.guidance import build_operator_guidance

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
    kernel_repo_path: str | None = None,
    *,
    acquisition_mode: str = "pinned_owner_file_computation",
    output_dir: str | Path | None = None,
    output_path: str | Path | None = None,
    receipt_path: str | Path | None = None,
    preflight_fingerprint: str | None = None,
) -> UiRunOutput:
    """Run the selected UI action through the authoritative Project Gate service."""

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
            kernel_repo_path=kernel_repo_path,
            acquisition_mode=acquisition_mode,
            output_dir=output_dir,
            output_path=output_path,
            receipt_path=receipt_path,
            preflight_fingerprint=preflight_fingerprint,
        )
        response = run_gate_request(request)
        result = _result_from_response(response)
        result["ui_acquisition_mode"] = acquisition_mode
    except Exception as exc:  # Defensive UI boundary; primary view must not expose traceback.
        LOGGER.exception("Unhandled exception in UI operator check")
        result = ErrorState(
            code="PG.UI.UNHANDLED_EXCEPTION",
            message_fa="اجرای UI با خطای کنترل‌شده متوقف شد و traceback خام در نمای اصلی نمایش داده نشد.",
            next_action_fa="گزارش فنی را دانلود کن و correlation ID یا خطای مسیر و وابستگی محلی را بررسی کن.",
            error_type=type(exc).__name__,
        ).to_result(choice)
    try:
        return _finalize(result)
    except Exception as exc:  # Final rendering containment.
        LOGGER.exception("Critical failure while finalizing UI operator output")
        fallback = ErrorState(
            code="PG.UI.CRITICAL_FINALIZATION_FAILURE",
            message_fa="آماده‌سازی خروجی UI با خطای کنترل‌شده متوقف شد و traceback خام در نمای اصلی نمایش داده نشد.",
            next_action_fa="گزارش technical/log را بررسی کن و مسیر خروجی را اصلاح کن.",
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
    kernel_repo_path: str | None = None,
    acquisition_mode: str = "pinned_owner_file_computation",
    output_dir: str | Path | None = None,
    output_path: str | Path | None = None,
    receipt_path: str | Path | None = None,
    preflight_fingerprint: str | None = None,
    schema_root: str = "schemas",
    lock_path: str | None = None,
    timeout_seconds: float = 30,
    require_real_evidence: bool = True,
) -> GateRequest:
    option = option_for_label(transition_label)
    input_text = pasted_json if pasted_json and pasted_json.strip() else None
    input_path = _uploaded_path(uploaded_file)
    if acquisition_mode != "producer_emitted_gate_artifact" and input_text is not None:
        input_path = None
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
            kernel_repo_path=_clean_path(kernel_repo_path),
        ),
        acquisition_mode=acquisition_mode,  # type: ignore[arg-type]
        output_dir=_clean_path(str(output_dir)) if output_dir is not None else None,
        output_path=_clean_path(str(output_path)) if output_path is not None else None,
        receipt_path=_clean_path(str(receipt_path)) if receipt_path is not None else None,
        schema_root=schema_root,
        lock_path=_clean_path(lock_path),
        timeout_seconds=timeout_seconds,
        require_real_evidence=require_real_evidence,
        preflight_fingerprint=preflight_fingerprint,
        preflight_mode="external_token",
    )


def load_capability_payload(path: str | Path = CAPABILITY_STATUS_PATH) -> dict[str, Any]:
    payload = load_json_file(path)
    if not isinstance(payload, dict):
        raise ValueError("capability-status.v1.json must contain a JSON object")
    return payload


def build_capability_rows(path: str | Path = CAPABILITY_STATUS_PATH) -> list[list[str]]:
    return capability_rows_from_payload(load_capability_payload(path))



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
        known = {(item.get("code"), item.get("path")) for item in diagnostics if isinstance(item, dict)}
        diagnostics.extend(
            deepcopy(item)
            for item in engine_result["diagnostics"]
            if isinstance(item, dict) and (item.get("code"), item.get("path")) not in known
        )
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
        "published_download_paths": list(payload.get("download_paths") or []),
        "attempt_directory": payload.get("attempt_directory"),
        "publication_state": payload.get("publication_state"),
        "published_artifacts": list(payload.get("published_artifacts") or []),
        "report_bundle": payload.get("report_bundle", {}),
        "output": engine_result.get("output") if isinstance(engine_result, dict) else None,
    }



def _ui_preflight_diagnostics(request: GateRequest) -> list[ServiceDiagnostic]:
    """Compatibility view of authoritative preflight diagnostics; never grants readiness."""

    result = run_preflight(request)
    diagnostics: list[ServiceDiagnostic] = []
    for check in result.checks:
        if check.status != "error":
            continue
        diagnostics.append(
            ServiceDiagnostic(
                check.id,
                "error",
                check.message_fa,
                "$.preflight",
                {
                    "technical_detail": check.technical_detail,
                    "classification": check.classification,
                },
            )
        )
    return diagnostics


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
    guidance = build_operator_guidance(result)
    safe_json = _neutralize_markdown_fences(canonical_dumps(result))
    raw_diagnostics = _neutralize_markdown_fences(json.dumps(result.get("diagnostics", []), ensure_ascii=False, indent=2))
    lines = [
        "# گزارش Project Gate Operator Panel",
        "",
        f"status: `{result.get('status', 'invalid')}`",
        "",
        "## راهنمای عملیاتی",
        "",
        f"- خلاصه: {guidance.headline_fa}",
        f"- کجا متوقف شد؟ {guidance.where_stopped_fa}",
        f"- مشکل فعلی چیست؟ {guidance.current_problem_fa}",
        f"- آیا خروجی مرحله بعد ساخته شد؟ {guidance.output_state_fa}",
        f"- safe_to_continue: `{str(guidance.safe_to_continue).lower()}`",
        "",
        "### چه چیزی درست پیش رفت؟",
    ]
    lines.extend(f"- {item}" for item in guidance.passed_steps_fa)
    lines.extend(["", "### اقدام بعدی دقیق"])
    lines.extend(f"{index}. {action}" for index, action in enumerate(guidance.next_actions_fa, start=1))
    lines.extend(["", "## Preflight summary", "", "- Preflight result and authoritative diagnostics are included below.", "", "## Raw diagnostics", "", "```json", raw_diagnostics, "```", "", "## Raw JSON result", "", "```json", safe_json, "```", ""])
    return "\n".join(lines)


def _neutralize_markdown_fences(value: str) -> str:
    return value.replace("```", "``\u200b`")


def _html_report(result: dict[str, Any]) -> str:
    escaped_json = json.dumps(result, ensure_ascii=False, indent=2)
    escaped_diagnostics = json.dumps(result.get("diagnostics", []), ensure_ascii=False, indent=2)
    guidance = build_operator_guidance(result)
    identifiers = []
    for item in result.get("diagnostics", []):
        if isinstance(item, dict):
            identifiers.append(
                f'<li>{bdi_ltr(item.get("code", "UNKNOWN_DIAGNOSTIC"))} — {bdi_ltr(item.get("path", "$"))}</li>'
            )
    identifier_html = "".join(identifiers) or "<li>diagnostic ثبت نشده است.</li>"
    return (
        '<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><title>Project Gate Report</title></head><body>'
        '<main lang="fa" dir="rtl"><h1>گزارش Project Gate Operator Panel</h1>'
        f'<p><strong>status:</strong> {bdi_ltr(result.get("status", "invalid"))}</p>'
        '<h2>راهنمای عملیاتی</h2>'
        f'<p>{escape_html(guidance.headline_fa)}</p>'
        '<h2>Preflight summary</h2>'
        '<p>Preflight result and authoritative diagnostics are included in this report.</p>'
        '<h2>Diagnostic identifiers</h2>'
        f'<ul>{identifier_html}</ul>'
        '<h2>Raw diagnostics</h2>'
        f'{ltr_code_block(escaped_diagnostics)}'
        '<h2>Raw JSON result</h2>'
        f'{ltr_code_block(escaped_json)}'
        '</main></body></html>'
    )


def _finalize(result: dict[str, Any]) -> UiRunOutput:
    downloads = [str(path) for path in result.get("published_download_paths", []) if _existing_file(path)]
    capability_payload = result.get("capabilities_snapshot") if isinstance(result.get("capabilities_snapshot"), dict) else load_capability_payload()
    return UiRunOutput(
        result=result,
        status_markdown=status_summary_markdown(result),
        diagnostics_rows=diagnostics_to_rows(result.get("diagnostics", [])),
        capability_rows=capability_rows_from_payload(capability_payload),
        json_preview=canonical_dumps(result),
        download_paths=downloads,
    )


def _existing_file(value: Any) -> bool:
    if not isinstance(value, (str, Path)) or not str(value).strip():
        return False
    try:
        return Path(value).is_file()
    except (OSError, ValueError, RuntimeError):
        return False
