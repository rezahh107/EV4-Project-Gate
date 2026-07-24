from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from typing import Any

from ev4_transition.architect_to_ce import TransitionValidatorHooks, transition_from_local_paths as architect_to_ce_from_local_paths
from ev4_transition.bundle_validator import BundleValidator, ResultValidationError
from ev4_transition.io.secure_snapshot import SnapshotError, obtain_json_snapshot
from ev4_transition.producer_integration.path_environment import (
    AttemptPaths,
    PublicationPathError,
    PublicationPaths,
    prepare_attempt_paths,
    prepare_publication_paths,
)
from ev4_transition.transitions.builder_to_responsive import transition_from_local_paths as builder_to_responsive_from_local_paths
from ev4_transition.transitions.ce_to_builder import transition_from_local_paths as ce_to_builder_from_local_paths
from ev4_transition.transitions.final_gate import final_gate_from_local_paths
from ev4_transition.validator_runner import run_architect_validator, run_ce_validator

from .capabilities import get_capabilities
from .json_input import parse_json_input
from .models import GateRequest, GateResponse, ServiceDiagnostic
from .preflight import preflight_authorization_diagnostic, run_preflight
from .producer_handoff import ProducerHandoffRequest, run_producer_handoff_request
from .repo_paths import resolve_relative_to_project_gate, validate_repo_paths
from .report_publication import publish_report_bundle, verified_existing_paths
from .reports import build_report_bundle
from .transition_contracts import all_service_choices, contract_for_service, lock_path_for_service, producer_transition_for_service

_STATUSES = {"accepted", "invalid", "insufficient_evidence", "repair_needed"}


def run_gate_request(request: GateRequest) -> GateResponse:
    """Execute one preflight-bound authoritative lifecycle for GUI and CLI."""

    choice = str(request.transition_choice)
    if choice not in all_service_choices():
        return _response(choice, "invalid", None, [_diag("PG.SERVICE.TRANSITION_UNKNOWN", "error", "Unsupported transition choice.", "$.transition_choice")])
    if choice == "inspect_capabilities":
        capabilities = get_capabilities()
        result = {"schema_version": "project-gate-service-result.v1", "result_type": "capability_inspection", "status": "accepted", "capabilities": deepcopy(capabilities)}
        return _response(choice, "accepted", result, [], capabilities_snapshot=capabilities)

    request = _bind_runtime_snapshot(request)
    preflight = run_preflight(request)
    authorization_failure = preflight_authorization_diagnostic(request, preflight)
    attempt, publication_paths, allocation_failure = _prepare_attempt(request)
    if allocation_failure is not None:
        response = _response(choice, "invalid", None, [allocation_failure])
        return _finalize_response(response, attempt)
    if authorization_failure is not None:
        response = _response(choice, _status_from_diags([authorization_failure]), None, [authorization_failure])
        return _finalize_response(response, attempt)

    if request.acquisition_mode == "producer_emitted_gate_artifact":
        response = _run_producer_emitted_request(request, publication_paths)
        return _finalize_response(response, attempt)

    parsed = parse_json_input(input_json_path=request.input_json_path, input_json_text=request.input_json_text, input_data=request.input_data)
    if parsed.diagnostics:
        return _finalize_response(_response(choice, "invalid", None, parsed.diagnostics), attempt)
    path_diagnostics = validate_repo_paths(request.repo_paths, choice)
    if path_diagnostics:
        return _finalize_response(_response(choice, _status_from_diags(path_diagnostics), None, path_diagnostics), attempt)

    try:
        result = _execute(choice, request, parsed.value)
    except ResultValidationError as exc:
        response = _response(choice, "invalid", None, [_diag("PG.SERVICE.RESULT_SCHEMA_VALIDATION_FAILED", "error", "Engine result schema validation failed.", "$", error=str(exc))])
    except OSError as exc:
        response = _response(choice, "insufficient_evidence", None, [_diag("PG.SERVICE.LOCAL_FILE_ACCESS_FAILED", "insufficient_evidence", "Required local file could not be read.", "$", error_type=type(exc).__name__, error=str(exc))])
    except Exception as exc:
        response = _response(choice, "invalid", None, [_diag("PG.SERVICE.ENGINE_EXECUTION_FAILED", "error", "Project Gate engine execution failed.", "$", error_type=type(exc).__name__, error=str(exc))])
    else:
        response = _response(choice, _status_from_engine(result), result, [])
    return _finalize_response(response, attempt)


def _bind_runtime_snapshot(request: GateRequest) -> GateRequest:
    """Capture producer source once for runtime, token comparison, and final revalidation."""

    if request.acquisition_mode != "producer_emitted_gate_artifact":
        return request
    try:
        snapshot = obtain_json_snapshot(
            source_path=request.input_json_path,
            snapshot=request.input_snapshot,
        )
    except (SnapshotError, OSError, ValueError, TypeError):
        return request
    return replace(request, input_snapshot=snapshot)


def _prepare_attempt(
    request: GateRequest,
) -> tuple[AttemptPaths | None, PublicationPaths | None, ServiceDiagnostic | None]:
    if request.output_dir is None and request.preflight_mode == "service_immediate":
        return None, None, None
    try:
        attempt = prepare_attempt_paths(request.output_dir)
        contract = contract_for_service(str(request.transition_choice))
        publication_paths = None
        if request.acquisition_mode == "producer_emitted_gate_artifact":
            if not contract.downstream_filename or not contract.receipt_filename:
                raise PublicationPathError(
                    {
                        "code": "PG_INT_PUBLICATION_ROUTE_UNAVAILABLE",
                        "severity": "error",
                        "path": "$.transition_choice",
                        "message": "The selected producer transition has no publication route.",
                        "details": {"transition_choice": str(request.transition_choice)},
                    }
                )
            publication_paths = prepare_publication_paths(
                request.output_dir,
                output_filename=contract.downstream_filename,
                receipt_filename=contract.receipt_filename,
                output_path=request.output_path,
                receipt_path=request.receipt_path,
                attempt_paths=attempt,
            )
        return attempt, publication_paths, None
    except PublicationPathError as exc:
        return None, None, _diagnostic_from_dict(exc.diagnostic)


def _run_producer_emitted_request(
    request: GateRequest,
    publication_paths: PublicationPaths | None,
) -> GateResponse:
    choice = str(request.transition_choice)
    expected = producer_transition_for_service(choice)
    if expected is None:
        return _response(
            choice,
            "invalid",
            None,
            [_diag("PG.UI.SOURCE_SCHEMA_TRANSITION_MISMATCH", "error", "Producer-emitted execution is not compatible with the selected transition.", "$.transition_choice", selected_transition=choice)],
        )
    if request.input_json_text is not None or request.input_data is not None:
        return _response(
            choice,
            "invalid",
            None,
            [_diag("PG.UI.PRODUCER_SOURCE_FILE_REQUIRED", "error", "در حالت producer_emitted_gate_artifact باید فایل اصلی Producer Gate Export را بارگذاری کنید؛ متن paste‌شده هویت فایل پایدار ندارد.", "$.input_json_path", acquisition_mode=request.acquisition_mode)],
        )
    if request.input_snapshot is None and not request.input_json_path:
        return _response(
            choice,
            "invalid",
            None,
            [_diag("PG.UI.PRODUCER_SOURCE_FILE_REQUIRED", "error", "در حالت producer_emitted_gate_artifact باید فایل اصلی Producer Gate Export را بارگذاری کنید.", "$.input_json_path", acquisition_mode=request.acquisition_mode)],
        )

    response = run_producer_handoff_request(
        ProducerHandoffRequest(
            source_path=request.input_json_path,
            source_snapshot=request.input_snapshot,
            repo_paths=request.repo_paths,
            output_dir=request.output_dir,
            output_path=request.output_path,
            receipt_path=request.receipt_path,
            schema_root=request.schema_root,
            lock_path=request.lock_path,
            publication_paths=publication_paths,
        )
    )
    if response.resolved_transition and response.resolved_transition != expected:
        diagnostic = _diag(
            "PG.UI.SOURCE_SCHEMA_TRANSITION_MISMATCH",
            "error",
            "The validated Producer Gate Export resolves to a different transition than the operator selection.",
            "$.transition_choice",
            selected_transition=choice,
            resolved_transition=response.resolved_transition,
        )
        return _response(choice, "invalid", response.engine_result, [diagnostic])

    diagnostics = [_diagnostic_from_dict(item) for item in response.diagnostics]
    return _response(
        choice,
        response.status,
        response.engine_result,
        diagnostics,
        download_paths=response.download_paths,
        user_message_fa=response.user_message_fa,
        next_action_fa=response.next_action_fa,
    )


def _finalize_response(response: GateResponse, attempt: AttemptPaths | None) -> GateResponse:
    if attempt is None:
        return response
    state, metadata, report_paths, diagnostic = publish_report_bundle(attempt, response.report_bundle)
    diagnostics = list(response.service_diagnostics)
    status = response.status
    if diagnostic is not None:
        diagnostics.append(diagnostic)
        status = "invalid"
    downloads = verified_existing_paths([*response.download_paths, *report_paths])
    return replace(
        response,
        status=status,  # type: ignore[arg-type]
        service_diagnostics=diagnostics,
        download_paths=downloads,
        attempt_directory=str(attempt.execution_directory),
        publication_state=state,
        published_artifacts=metadata,
    )


def _diagnostic_from_dict(item: dict[str, Any]) -> ServiceDiagnostic:
    severity = str(item.get("severity", "error"))
    if severity not in {"error", "warning", "info", "insufficient_evidence"}:
        severity = "error"
    return ServiceDiagnostic(
        str(item.get("code", "PG.SERVICE.UNKNOWN_DIAGNOSTIC")),
        severity,  # type: ignore[arg-type]
        str(item.get("message", "")),
        str(item.get("path", "$")),
        deepcopy(item.get("details")) if isinstance(item.get("details"), dict) else {},
    )


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
        return final_gate_from_local_paths(payload, _schema_root(request), _lock_path(request, choice), str(repos.project_gate_repo_path), str(repos.responsive_repo_path), kernel_repo=str(repos.kernel_repo_path), timeout_seconds=request.timeout_seconds, require_real_evidence=request.require_real_evidence)
    raise AssertionError(choice)


def _schema_root(request: GateRequest) -> Path:
    return resolve_relative_to_project_gate(request.repo_paths, request.schema_root)


def _lock_path(request: GateRequest, choice: str) -> Path:
    return resolve_relative_to_project_gate(request.repo_paths, request.lock_path or lock_path_for_service(choice))


def _response(
    choice: str,
    status: str,
    engine_result: dict[str, Any] | None,
    diagnostics: list[ServiceDiagnostic],
    *,
    capabilities_snapshot: dict[str, Any] | None = None,
    download_paths: list[str] | None = None,
    user_message_fa: str | None = None,
    next_action_fa: str | None = None,
) -> GateResponse:
    status = _normalize_status(status)
    service_diagnostics = [item.to_dict() for item in diagnostics]
    report_source = deepcopy(engine_result) if engine_result is not None else {"schema_version": "project-gate-service-result.v1", "result_type": "service_layer_failure", "transition_choice": choice, "status": status, "diagnostics": service_diagnostics, "output": None}
    report_bundle = build_report_bundle(report_source)
    if report_bundle.render_diagnostics:
        status = "invalid"
        service_diagnostics.extend(deepcopy(report_bundle.render_diagnostics))
    return GateResponse(
        status=status,  # type: ignore[arg-type]
        transition_choice=choice,
        engine_result=deepcopy(engine_result),
        service_diagnostics=deepcopy(service_diagnostics),
        capabilities_snapshot=deepcopy(capabilities_snapshot) if capabilities_snapshot is not None else _safe_capabilities(),
        report_bundle=report_bundle,
        download_filenames=_download_filenames(choice),
        download_paths=list(download_paths or []),
        user_message_fa=user_message_fa or _user_message(status),
        next_action_fa=next_action_fa or _next_action(status),
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
