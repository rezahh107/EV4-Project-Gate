from __future__ import annotations

from pathlib import Path
from typing import Any

from ev4_transition.producer_integration.intake import transition_producer_export

from . import dispatcher as _dispatcher
from .capabilities import get_capabilities
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

_original_producer_dispatch = _dispatcher._run_producer_emitted_request


def _producer_dispatch_with_adapter_snapshot(request: GateRequest) -> GateResponse:
    """Use an adapter-captured immutable snapshot without moving orchestration into the adapter."""

    snapshot = request.input_snapshot
    if snapshot is None:
        return _original_producer_dispatch(request)
    choice = str(request.transition_choice)
    transition_name = {"architect_to_ce": "architect-to-ce", "ce_to_builder": "ce-to-builder"}.get(choice)
    if transition_name is None:
        return _original_producer_dispatch(request)

    repos = request.repo_paths
    defaults = {
        "architect-to-ce": ("contracts/locks/architect-to-ce-transition.v1.lock.json", "ce-input.json", "project-gate-a2c-receipt.json"),
        "ce-to-builder": ("contracts/locks/ce-to-builder-transition.v1.lock.json", "builder-input.json", "project-gate-c2b-receipt.json"),
    }
    default_lock, default_output, default_receipt = defaults[transition_name]
    output_path = request.output_path or default_output
    receipt_path = request.receipt_path or default_receipt
    if request.output_dir:
        root = Path(request.output_dir)
        output_path = str(root / Path(output_path).name)
        receipt_path = str(root / Path(receipt_path).name)

    result = transition_producer_export(
        transition_name,
        snapshot.value,
        snapshot=snapshot,
        architect_repo=repos.architect_repo_path,
        ce_repo=repos.ce_repo_path,
        builder_repo=repos.builder_repo_path,
        schema_root=request.schema_root,
        lock_path=request.lock_path or default_lock,
        output_path=output_path,
        receipt_path=receipt_path,
    )
    diagnostics = [
        _dispatcher._diagnostic_from_dict(item)
        for item in result.get("diagnostics", [])
        if isinstance(item, dict)
    ]
    paths: list[str] = []
    for key in ("downstream_artifact", "receipt"):
        item = result.get(key)
        if isinstance(item, dict) and isinstance(item.get("path"), str):
            paths.append(item["path"])
    return _dispatcher._response(
        choice,
        str(result.get("status", "invalid")),
        result,
        diagnostics,
        download_paths=paths,
    )


_dispatcher._run_producer_emitted_request = _producer_dispatch_with_adapter_snapshot
run_gate_request = _dispatcher.run_gate_request

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
    "build_operator_guidance",
    "build_report_bundle",
    "classify_output_state",
    "get_capabilities",
    "inspect_producer_handoff_request",
    "load_guidance_registry",
    "run_gate_request",
    "run_preflight",
    "run_producer_handoff_request",
]
