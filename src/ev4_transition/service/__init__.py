from __future__ import annotations

from .capabilities import get_capabilities
from .dispatcher import run_gate_request
from .execution_transaction import (
    AuthoritativeGateTransactionResult,
    PreparedAuthoritativeGateTransaction,
    execute_authoritative_gate_transaction,
    prepare_authoritative_gate_transaction,
    run_authoritative_preflight_and_gate,
)
from .guidance import OperatorGuidance, build_operator_guidance, classify_output_state, load_guidance_registry
from .models import GateRequest, GateResponse, RepoPaths, ReportBundle, ServiceDiagnostic
from .preflight import PreflightCheck, PreflightResult, run_preflight
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
    effective_repository_fields,
    repository_path_matrix,
    service_choice_for_cli,
)

__all__ = [
    "AuthoritativeGateTransactionResult",
    "GateRequest",
    "GateResponse",
    "OperatorGuidance",
    "PreflightCheck",
    "PreflightResult",
    "PreparedAuthoritativeGateTransaction",
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
    "effective_repository_fields",
    "execute_authoritative_gate_transaction",
    "get_capabilities",
    "inspect_producer_handoff_request",
    "load_guidance_registry",
    "prepare_authoritative_gate_transaction",
    "repository_path_matrix",
    "run_authoritative_preflight_and_gate",
    "run_gate_request",
    "run_preflight",
    "run_producer_handoff_request",
    "service_choice_for_cli",
]
