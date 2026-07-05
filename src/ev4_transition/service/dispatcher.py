from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from ev4_transition.architect_to_ce import TransitionValidatorHooks, transition_from_local_paths as architect_to_ce_from_local_paths
from ev4_transition.bundle_validator import BundleValidator, ResultValidationError
from ev4_transition.transitions.builder_to_responsive import transition_from_local_paths as builder_to_responsive_from_local_paths
from ev4_transition.transitions.ce_to_builder import transition_from_local_paths as ce_to_builder_from_local_paths
from ev4_transition.transitions.final_gate import final_gate_from_local_paths
from ev4_transition.validator_runner import run_architect_validator, run_ce_validator

from .capabilities import get_capabilities
from .json_input import parse_json_input
from .models import GateRequest, GateResponse, ServiceDiagnostic
from .repo_paths import resolve_relative_to_project_gate, validate_repo_paths
from .reports import build_report_bundle

_ALLOWED = {"validate_bundle", "inspect_capabilities", "architect_to_ce", "ce_to_builder", "builder_to_responsive", "final_gate"}
_STATUSES = {"accepted", "invalid", "insufficient_evidence", "repair_needed"}
_LOCKS = {
    "architect_to_ce": "contracts/locks/architect-to-ce-transition.v1.lock.json",
    "ce_to_builder": "contracts/locks/ce-to-builder-transition.v1.lock.json",
    "builder_to_responsive": "contracts/locks/builder-to-responsive-transition.v1.lock.json",
    "final_gate": "contracts/locks/final-gate.v1.lock.json",
}


def run_gate_request(request: GateRequest) -> GateResponse:
    choice = str(request.transition_choice)
    if choice not in _ALLOWED:
        return _response(choice, "invalid", None, [_diag("PG.SERVICE.TRANSITION_UNKNOWN", "error", "Unsupported transition choice.", "$.transition_choice")])
    if choice == "inspect_capabilities":
        capabilities = get_capabilities()
        result = {"schema_version": "project-gate-service-result.v1", "result_type": "capability_inspection", "status": "accepted", "capabilities": deepcopy(capabilities)}
        return _response(choice, "accepted", result, [], capabilities_snapshot=capabilities)

    parsed = parse_json_input(input_json_path=request.input_json_path, input_json_text=request.input_json_text, input_data=request.input_data)
    if parsed.diagnostics:
        return _response(choice, "invalid", None, parsed.diagnostics)
    path_diagnostics = validate_repo_paths(request.repo_paths, choice)
    if path_diagnostics:
        return _response(choice, _status_from_diags(path_diagnostics), None, path_diagnostics)

    try:
        result = _execute(choice, request, parsed.value)
    except ResultValidationError as exc:
        return _response(choice, "invalid", None, [_diag("PG.SERVICE.RESULT_SCHEMA_VALIDATION_FAILED", "error", "Engine result schema validation failed.", "$", error=str(exc))])
    except OSError as exc:
        return _response(choice, "insufficient_evidence", None, [_diag("PG.SERVICE.LOCAL_FILE_ACCESS_FAILED", "insufficient_evidence", "Required local file could not be read.", "$", error_type=type(exc).__name__, error=str(exc))])
    except Exception as exc:
        return _response(choice, "invalid", None, [_diag("PG.SERVICE.ENGINE_EXECUTION_FAILED", "error", "Project Gate engine execution failed.", "$", error_type=type(exc).__name__, error=str(exc))])
    return _response(choice, _status_from_engine(result), result, [])


def _execute(choice: str, request: GateRequest, payload: Any) -> dict[str, Any]:
    if choice == "validate_bundle":
        return BundleValidator(_schema_root(request)).validate_bundle(payload, required_evidence_ids=list(request.required_evidence_ids))
    repos = request.repo_paths
    if choice == "architect_to_ce":
        hooks = TransitionValidatorHooks(
            architect=lambda value: run_architect_validator(str(repos.architect_repo_path), value),
            ce=lambda value, source_bundle: run_ce_validator(str(repos.ce_repo_path), value, source_bundle),
        )
        return architect_to_ce_from_local_paths(payload, _schema_root(request), _lock_path(request, choice), str(repos.architect_repo_path), str(repos.ce_repo_path), validator_hooks=hooks)
    if choice == "ce_to_builder":
        return ce_to_builder_from_local_paths(payload, _schema_root(request), _lock_path(request, choice), str(repos.ce_repo_path), str(repos.builder_repo_path), timeout_seconds=request.timeout_seconds, require_real_evidence=request.require_real_evidence)
    if choice == "builder_to_responsive":
        return builder_to_responsive_from_local_paths(payload, _schema_root(request), _lock_path(request, choice), str(repos.builder_repo_path), str(repos.responsive_repo_path), timeout_seconds=request.timeout_seconds, require_real_evidence=request.require_real_evidence)
    if choice == "final_gate":
        return final_gate_from_local_paths(payload, _schema_root(request), _lock_path(request, choice), str(repos.project_gate_repo_path), str(repos.responsive_repo_path), timeout_seconds=request.timeout_seconds, require_real_evidence=request.require_real_evidence)
    raise AssertionError(choice)


def _schema_root(request: GateRequest) -> Path:
    return resolve_relative_to_project_gate(request.repo_paths, request.schema_root)


def _lock_path(request: GateRequest, choice: str) -> Path:
    return resolve_relative_to_project_gate(request.repo_paths, request.lock_path or _LOCKS[choice])


def _response(choice: str, status: str, engine_result: dict[str, Any] | None, diagnostics: list[ServiceDiagnostic], *, capabilities_snapshot: dict[str, Any] | None = None) -> GateResponse:
    status = _normalize_status(status)
    service_diagnostics = [item.to_dict() for item in diagnostics]
    report_source = deepcopy(engine_result) if engine_result is not None else {"schema_version": "project-gate-service-result.v1", "result_type": "service_layer_failure", "transition_choice": choice, "status": status, "diagnostics": service_diagnostics, "output": None}
    return GateResponse(
        status=status,
        transition_choice=choice,
        engine_result=deepcopy(engine_result),
        service_diagnostics=deepcopy(service_diagnostics),
        capabilities_snapshot=deepcopy(capabilities_snapshot) if capabilities_snapshot is not None else _safe_capabilities(),
        report_bundle=build_report_bundle(report_source),
        download_filenames=_download_filenames(choice),
        user_message_fa=_user_message(status),
        next_action_fa=_next_action(status),
    )


def _diag(code: str, severity: str, message: str, path: str, **details: Any) -> ServiceDiagnostic:
    return ServiceDiagnostic(code, severity, message, path, details)  # type: ignore[arg-type]


def _safe_capabilities() -> dict[str, Any] | None:
    try:
        return get_capabilities()
    except Exception:
        return None


def _status_from_engine(result: dict[str, Any]) -> str:
    return _normalize_status(str(result.get("status", "invalid")))


def _status_from_diags(diagnostics: list[ServiceDiagnostic]) -> str:
    severities = {item.severity for item in diagnostics}
    if "error" in severities:
        return "invalid"
    if "insufficient_evidence" in severities:
        return "insufficient_evidence"
    if "warning" in severities:
        return "repair_needed"
    return "accepted"


def _normalize_status(status: str) -> str:
    if status == "valid":
        return "accepted"
    return status if status in _STATUSES else "invalid"


def _download_filenames(choice: str) -> dict[str, str]:
    prefix = f"project-gate-{choice.replace('_', '-')}"
    return {"json": f"{prefix}-result.json", "summary_txt": f"{prefix}-summary.fa.txt", "markdown": f"{prefix}-report.fa.md", "html": f"{prefix}-report.fa.html"}


def _user_message(status: str) -> str:
    return {"accepted": "✅ بررسی پذیرفته شد؛ فقط در محدوده همین Gate.", "repair_needed": "🛠️ بسته نیازمند اصلاح است.", "insufficient_evidence": "⚠️ شواهد کافی نیست.", "invalid": "❌ ورودی یا اجرای Gate نامعتبر است."}.get(status, "❌ وضعیت نامشخص است.")


def _next_action(status: str) -> str:
    return {"accepted": "خروجی JSON و گزارش فارسی را ذخیره کن.", "repair_needed": "diagnostics را اصلاح کن و دوباره اجرا کن.", "insufficient_evidence": "local checkout، evidence، lock، یا validator رسمی گمشده را فراهم کن.", "invalid": "JSON، انتخاب transition، مسیرها، schema identity، یا خطای گزارش‌شده را اصلاح کن."}.get(status, "diagnostics را بررسی کن.")
