from __future__ import annotations

from .capabilities import get_capabilities
from .dispatcher import run_gate_request
from .guidance import OperatorGuidance, build_operator_guidance, classify_output_state, load_guidance_registry
from .models import GateRequest, GateResponse, RepoPaths, ReportBundle, ServiceDiagnostic
from .preflight_core import PreflightCheck, PreflightResult, run_preflight
from .producer_handoff import (
    ProducerHandoffRequest,
    ProducerHandoffResponse,
    inspect_producer_handoff_request,
    run_producer_handoff_request,
)
from .reports import build_report_bundle
from .transition_contracts import (
    TransitionContract,
    cli_transition_names,
    contract_for_service,
    repository_path_matrix,
    service_choice_for_cli,
)

__all__ = [
    "GateRequest",
    "GateResponse",
    "OperatorGuidance",
    "PreflightCheck",
    "PreflightResult",
    "ProducerHandoffRequest",
    "ProducerHandoffResponse",
    "RepoPaths",
    "ReportBundle",
    "ServiceDiagnostic",
    "TransitionContract",
    "build_operator_guidance",
    "build_report_bundle",
    "classify_output_state",
    "cli_transition_names",
    "contract_for_service",
    "get_capabilities",
    "inspect_producer_handoff_request",
    "load_guidance_registry",
    "repository_path_matrix",
    "run_gate_request",
    "run_preflight",
    "run_producer_handoff_request",
    "service_choice_for_cli",
]
