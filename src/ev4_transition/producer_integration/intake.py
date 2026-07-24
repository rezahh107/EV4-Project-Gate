from __future__ import annotations

from pathlib import Path
from typing import Any

from . import intake_runtime as _runtime
from .join_preflight import validate_join_evidence_packet

TRANSITIONS = _runtime.TRANSITIONS
load_transition_targets = _runtime.load_transition_targets
intake_producer_export = _runtime.intake_producer_export
_operational_truth_failure = _runtime._operational_truth_failure


def transition_producer_export(
    transition_name: str,
    artifact: Any,
    *,
    join_packet_path: str | Path | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Preserve the historical monkeypatch seam while using lean runtime logic."""

    _runtime.intake_producer_export = intake_producer_export
    _runtime.validate_join_evidence_packet = validate_join_evidence_packet
    _runtime._operational_truth_failure = _operational_truth_failure
    return _runtime.transition_producer_export(
        transition_name,
        artifact,
        join_packet_path=join_packet_path,
        **kwargs,
    )


__all__ = [
    "TRANSITIONS",
    "intake_producer_export",
    "load_transition_targets",
    "transition_producer_export",
    "validate_join_evidence_packet",
]
