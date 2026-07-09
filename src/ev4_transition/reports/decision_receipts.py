from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

ReceiptStatus = Literal["success", "warning", "blocked"]

REQUIRED_KERNEL_DECISION_TRACE_FIELDS = (
    "decision_family",
    "decision_card_ref",
    "selected_option",
    "rejected_options",
    "evidence_refs",
    "evidence_state",
    "consumer_stage",
)
_STRING_TRACE_FIELDS = {"decision_family", "decision_card_ref", "selected_option", "evidence_state", "consumer_stage"}
_LIST_TRACE_FIELDS = {"rejected_options", "evidence_refs"}

SUCCESS_RECEIPT_FA = "✅ این Gate decision به decision card کرنل وصل است؛ Project Gate فقط lineage و evidence را اعتبارسنجی کرده و تصمیم جدیدی ایجاد نکرده است."
WARNING_RECEIPT_FA = "⚠️ این Gate item هنوز رسید معتبر کرنل ندارد؛ بدون machine-readable trace کامل نباید به‌عنوان gate-pass معتبر عبور کند."
BLOCKED_RECEIPT_FA = "⛔ Gate مسدود شد؛ decision lineage یا evidence کافی نیست و باید repair/reopen شود."

EXPLICIT_NON_CLAIMS = (
    "no_release_readiness_claim",
    "no_production_readiness_claim",
    "no_downstream_contract_enforcement_claim",
    "no_runtime_monitor_enforcement_claim",
    "no_project_gate_repair_authority_added",
)


@dataclass(frozen=True)
class KernelDecisionReceipt:
    status: ReceiptStatus
    message_fa: str
    trace_complete: bool
    missing_trace_fields: list[str]
    machine_trace_source: str | None
    presentation_layer_only: bool = True
    source_of_truth: str = "machine_readable_kernel_decision_trace"
    schema_version: str = "project-gate-kernel-decision-receipt.v1"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "message_fa": self.message_fa,
            "trace_complete": self.trace_complete,
            "missing_trace_fields": list(self.missing_trace_fields),
            "machine_trace_source": self.machine_trace_source,
            "presentation_layer_only": self.presentation_layer_only,
            "source_of_truth": self.source_of_truth,
            "explicit_non_claims": list(EXPLICIT_NON_CLAIMS),
        }


def build_kernel_decision_receipt(result: dict[str, Any] | Any) -> KernelDecisionReceipt:
    """Build a UX-safe receipt from an existing machine-readable result.

    The receipt is presentation-only. It never creates lineage, upgrades status,
    or converts user-facing prose into gate-pass evidence.
    """

    trace, trace_source = _find_machine_trace(result)
    missing = missing_kernel_decision_trace_fields(trace)
    trace_complete = trace is not None and not missing
    gate_status = str(result.get("status", "invalid")) if isinstance(result, dict) else "invalid"

    if gate_status == "accepted":
        if trace_complete:
            return KernelDecisionReceipt(
                status="success",
                message_fa=SUCCESS_RECEIPT_FA,
                trace_complete=True,
                missing_trace_fields=[],
                machine_trace_source=trace_source,
            )
        return KernelDecisionReceipt(
            status="warning",
            message_fa=WARNING_RECEIPT_FA,
            trace_complete=False,
            missing_trace_fields=missing,
            machine_trace_source=trace_source,
        )

    return KernelDecisionReceipt(
        status="blocked",
        message_fa=BLOCKED_RECEIPT_FA,
        trace_complete=trace_complete,
        missing_trace_fields=[] if trace_complete else missing,
        machine_trace_source=trace_source,
    )


def missing_kernel_decision_trace_fields(trace: Any) -> list[str]:
    if not isinstance(trace, dict):
        return list(REQUIRED_KERNEL_DECISION_TRACE_FIELDS)

    missing: list[str] = []
    for field in REQUIRED_KERNEL_DECISION_TRACE_FIELDS:
        value = trace.get(field)
        if field in _STRING_TRACE_FIELDS and not _valid_string(value):
            missing.append(field)
        elif field in _LIST_TRACE_FIELDS and not _valid_string_list(value):
            missing.append(field)
    return missing


def _find_machine_trace(result: Any) -> tuple[dict[str, Any] | None, str | None]:
    for path in (
        ("$.output.decision_lineage", ("output", "decision_lineage")),
        ("$.output.responsive_output.decision_lineage", ("output", "responsive_output", "decision_lineage")),
        ("$.responsive_output.decision_lineage", ("responsive_output", "decision_lineage")),
        ("$.decision_lineage", ("decision_lineage",)),
        ("$.engine_result.output.decision_lineage", ("engine_result", "output", "decision_lineage")),
    ):
        label, keys = path
        value = _get_path(result, keys)
        if isinstance(value, dict):
            return value, label
    return None, None


def _get_path(value: Any, keys: tuple[str, ...]) -> Any:
    current = value
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _valid_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _valid_string_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(_valid_string(item) for item in value)
