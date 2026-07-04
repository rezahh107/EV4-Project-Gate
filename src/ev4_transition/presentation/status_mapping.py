from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ProjectGateStatus = Literal["accepted", "repair_needed", "insufficient_evidence", "invalid"]
SemanticTone = Literal["success", "warning", "danger"]


@dataclass(frozen=True)
class StatusPresentation:
    status: ProjectGateStatus
    icon: str
    tone: SemanticTone
    persian_label: str
    exit_code: int


_STATUS_PRESENTATION: dict[ProjectGateStatus, StatusPresentation] = {
    "accepted": StatusPresentation("accepted", "✅", "success", "پذیرفته شد", 0),
    "repair_needed": StatusPresentation("repair_needed", "🛠️", "warning", "نیازمند اصلاح", 1),
    "insufficient_evidence": StatusPresentation("insufficient_evidence", "⚠️", "warning", "شواهد کافی نیست", 2),
    "invalid": StatusPresentation("invalid", "❌", "danger", "نامعتبر", 1),
}

_LEGACY_STATUS_ALIASES: dict[str, ProjectGateStatus] = {
    "valid": "accepted",
}


def normalize_status(status: str) -> ProjectGateStatus:
    """Normalize legacy validation aliases into the Project Gate status vocabulary."""

    candidate = _LEGACY_STATUS_ALIASES.get(status, status)
    if candidate not in _STATUS_PRESENTATION:
        raise ValueError(f"Unknown Project Gate status: {status}")
    return candidate  # type: ignore[return-value]


def presentation_for_status(status: str) -> StatusPresentation:
    return _STATUS_PRESENTATION[normalize_status(status)]


def exit_code_for_status(status: str) -> int:
    return presentation_for_status(status).exit_code
