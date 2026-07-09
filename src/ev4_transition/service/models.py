from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

ProjectGateServiceStatus = Literal["accepted", "invalid", "insufficient_evidence", "repair_needed"]
TransitionChoice = Literal[
    "validate_bundle",
    "inspect_capabilities",
    "architect_to_ce",
    "ce_to_builder",
    "builder_to_responsive",
    "final_gate",
]
InputSource = Literal["file_path", "json_text", "dict", "missing"]


@dataclass(frozen=True)
class ServiceDiagnostic:
    code: str
    severity: Literal["error", "warning", "info", "insufficient_evidence"]
    message: str
    path: str = "$"
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "path": self.path,
        }
        if self.details:
            payload["details"] = deepcopy(self.details)
        return payload


@dataclass(frozen=True)
class RepoPaths:
    project_gate_repo_path: str | None = "."
    architect_repo_path: str | None = None
    ce_repo_path: str | None = None
    builder_repo_path: str | None = None
    responsive_repo_path: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return asdict(self)


@dataclass(frozen=True)
class GateRequest:
    transition_choice: TransitionChoice
    input_json_path: str | None = None
    input_json_text: str | None = None
    input_data: dict[str, Any] | list[Any] | str | int | float | bool | None = None
    repo_paths: RepoPaths = field(default_factory=RepoPaths)
    schema_root: str = "schemas"
    lock_path: str | None = None
    required_evidence_ids: list[str] = field(default_factory=list)
    timeout_seconds: float = 30
    require_real_evidence: bool = True


@dataclass(frozen=True)
class ReportBundle:
    canonical_json: str
    persian_plain_summary: str
    markdown_report: str | None
    html_report: str | None
    result_hash: str | None = None
    decision_receipt: dict[str, Any] = field(default_factory=dict)
    render_diagnostics: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GateResponse:
    status: ProjectGateServiceStatus
    transition_choice: str
    engine_result: dict[str, Any] | None
    service_diagnostics: list[dict[str, Any]]
    capabilities_snapshot: dict[str, Any] | None
    report_bundle: ReportBundle
    download_filenames: dict[str, str]
    user_message_fa: str
    next_action_fa: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "transition_choice": self.transition_choice,
            "engine_result": deepcopy(self.engine_result),
            "service_diagnostics": deepcopy(self.service_diagnostics),
            "capabilities_snapshot": deepcopy(self.capabilities_snapshot),
            "report_bundle": self.report_bundle.to_dict(),
            "download_filenames": dict(self.download_filenames),
            "user_message_fa": self.user_message_fa,
            "next_action_fa": self.next_action_fa,
        }
