from __future__ import annotations

from .environment_preflight import validate_gate_request_environment
from .models import GateRequest
from .preflight_core import (
    PreflightCheck,
    PreflightCheckStatus,
    PreflightResult,
    PreflightResultStatus,
    run_preflight as _run_core_preflight,
)


def run_preflight(request: GateRequest) -> PreflightResult:
    if request.acquisition_mode == "producer_emitted_gate_artifact":
        return validate_gate_request_environment(request)
    return _run_core_preflight(request)


__all__ = [
    "PreflightCheck",
    "PreflightCheckStatus",
    "PreflightResult",
    "PreflightResultStatus",
    "run_preflight",
    "validate_gate_request_environment",
]
