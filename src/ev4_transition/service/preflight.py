from __future__ import annotations

import ast
from dataclasses import replace
from typing import Any

from ev4_transition.io.secure_snapshot import SnapshotError

from .environment_preflight import validate_gate_request_environment
from .models import GateRequest, ServiceDiagnostic
from .preflight_core import (
    PreflightCheck,
    PreflightCheckStatus,
    PreflightResult,
    PreflightResultStatus,
    run_preflight as _run_core_preflight,
)
from .request_identity import build_gate_request_identity


def run_preflight(request: GateRequest) -> PreflightResult:
    """Run the single authoritative, read-only preflight for every adapter."""

    result = (
        validate_gate_request_environment(request)
        if request.acquisition_mode == "producer_emitted_gate_artifact"
        else _run_core_preflight(request)
    )
    try:
        identity = build_gate_request_identity(request)
    except SnapshotError as exc:
        return _blocked_identity_result(result, exc.code, str(exc), exc.details)
    except (OSError, ValueError, TypeError) as exc:
        return _blocked_identity_result(
            result,
            "PG.SERVICE.PREFLIGHT_IDENTITY_FAILED",
            "The exact request identity could not be computed during preflight.",
            {"error_type": type(exc).__name__},
        )
    return replace(
        result,
        request_fingerprint=identity.fingerprint if result.status == "ready" else None,
        source_identity=dict(identity.source_identity),
    )


def preflight_authorization_diagnostic(
    request: GateRequest,
    result: PreflightResult,
) -> ServiceDiagnostic | None:
    """Fail closed unless current preflight authorizes the exact request.

    ``service_immediate`` remains only as a compatibility name for the same-call
    Preflight → dispatch path. It no longer suppresses non-ready Preflight.
    ``validate_bundle`` is validation-only and may run diagnostically with warnings;
    it cannot publish an operational handoff.
    """

    if result.status != "ready":
        if str(request.transition_choice) == "validate_bundle" and result.status == "warnings":
            return None
        return _diagnostic_from_blocked_preflight(result)
    if request.preflight_mode == "service_immediate":
        return None
    supplied = request.preflight_fingerprint
    if not supplied:
        return ServiceDiagnostic(
            "PG.SERVICE.PREFLIGHT_FINGERPRINT_REQUIRED",
            "error",
            "Execution requires the fingerprint produced by authoritative preflight.",
            "$.preflight_fingerprint",
        )
    if supplied != result.request_fingerprint:
        return ServiceDiagnostic(
            "PG.SERVICE.PREFLIGHT_FINGERPRINT_STALE",
            "error",
            "The current request differs from the request that passed preflight.",
            "$.preflight_fingerprint",
            {
                "supplied_fingerprint": supplied,
                "current_fingerprint": result.request_fingerprint,
            },
        )
    return None


def _diagnostic_from_blocked_preflight(result: PreflightResult) -> ServiceDiagnostic:
    identity_check = next(
        (item for item in result.checks if item.status == "error" and item.id == "request.identity.blocked"),
        None,
    )
    identity_code = _extract_preflight_code(identity_check) if identity_check is not None else None
    identity_is_snapshot_authority = bool(identity_code and identity_code.startswith(("PG_A2C_INPUT_", "PG_C2B_INPUT_")))
    check = identity_check if identity_is_snapshot_authority else next(
        (item for item in result.checks if item.status == "error" and item.id != "request.identity.blocked"),
        identity_check,
    )
    code = "PG.SERVICE.PREFLIGHT_NOT_READY"
    path = "$.preflight"
    message = "Authoritative preflight is not ready for the current request."
    if check is not None:
        extracted = _extract_preflight_code(check)
        if extracted:
            code = extracted
            message = check.message_fa
        if check.id.startswith("json.source"):
            path = "$.input"
        elif check.id.startswith("path.") or check.id.startswith("environment."):
            path = "$.repo_paths"
        elif check.id == "request.identity.blocked":
            path = "$.request_identity"
    severity = "insufficient_evidence" if code in {
        "PG.SERVICE.REPO_PATH_NOT_LOCAL",
        "PG.SERVICE.REPO_PATH_INACCESSIBLE",
        "PG.SERVICE.REPO_PATH_MISSING",
    } else "error"
    details: dict[str, Any] = {
        "preflight_status": result.status,
        "request_fingerprint": result.request_fingerprint,
    }
    identity_details = _extract_identity_details(identity_check)
    if identity_details:
        details.update(identity_details)
    if check is not None:
        details.update(
            {
                "preflight_check_id": check.id,
                "preflight_classification": check.classification,
                "technical_detail": check.technical_detail,
            }
        )
    return ServiceDiagnostic(code, severity, message, path, details)


def _extract_preflight_code(check: PreflightCheck | None) -> str | None:
    if check is None:
        return None
    if check.id == "json.source.invalid_or_missing" and isinstance(check.technical_detail, str) and check.technical_detail.startswith("PG.SERVICE."):
        return check.technical_detail
    if check.id == "json.source.not_object":
        return "PG.SERVICE.JSON_NOT_OBJECT"
    if check.id.startswith("path.") and check.id.endswith(".github_url"):
        return "PG.SERVICE.REPO_PATH_NOT_LOCAL"
    if check.id.startswith("path.") and check.id.endswith(".inaccessible"):
        return "PG.SERVICE.REPO_PATH_INACCESSIBLE"
    if check.id.startswith("path.") and check.id.endswith(".missing"):
        return "PG.SERVICE.REPO_PATH_MISSING"
    if check.id.startswith("environment."):
        candidate = check.id.rsplit(".", 1)[-1]
        if candidate.startswith("PG_"):
            return candidate
    detail = check.technical_detail
    if isinstance(detail, str) and detail.startswith("code="):
        candidate = detail.removeprefix("code=").split(";", 1)[0].strip()
        if candidate.startswith("PG"):
            return candidate
    return None


def _extract_identity_details(check: PreflightCheck | None) -> dict[str, Any]:
    if check is None or not isinstance(check.technical_detail, str):
        return {}
    marker = "; details="
    if marker not in check.technical_detail:
        return {}
    raw = check.technical_detail.split(marker, 1)[1]
    try:
        parsed = ast.literal_eval(raw)
    except (SyntaxError, ValueError):
        return {}
    return dict(parsed) if isinstance(parsed, dict) else {}


def _blocked_identity_result(
    result: PreflightResult,
    code: str,
    message: str,
    details: dict[str, Any],
) -> PreflightResult:
    check = PreflightCheck(
        "request.identity.blocked",
        "هویت دقیق درخواست",
        "error",
        message,
        f"code={code}; details={details}",
        "ورودی source و مسیرهای درخواست را اصلاح کن و Preflight را دوباره اجرا کن.",
        "request_identity_failed",
    )
    return replace(
        result,
        status="blocked",
        checks=[*result.checks, check],
        summary_fa="Preflight مسدود است؛ هویت دقیق درخواست قابل تأیید نیست.",
        request_fingerprint=None,
    )


__all__ = [
    "PreflightCheck",
    "PreflightCheckStatus",
    "PreflightResult",
    "PreflightResultStatus",
    "preflight_authorization_diagnostic",
    "run_preflight",
    "validate_gate_request_environment",
]
