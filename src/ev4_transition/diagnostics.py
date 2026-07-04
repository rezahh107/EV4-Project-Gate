from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Severity = Literal["error", "warning", "info", "insufficient_evidence"]
ValidationStatus = Literal["valid", "invalid", "insufficient_evidence"]
ProjectGateStatus = Literal["accepted", "repair_needed", "insufficient_evidence", "invalid"]

_SEVERITY_ORDER: dict[str, int] = {
    "error": 0,
    "insufficient_evidence": 1,
    "warning": 2,
    "info": 3,
}


@dataclass(frozen=True)
class Diagnostic:
    code: str
    severity: Severity
    message: str
    path: str = "$"
    details: dict[str, Any] = field(default_factory=dict)

    def sort_key(self) -> tuple[Any, ...]:
        return (
            self.path,
            _SEVERITY_ORDER[self.severity],
            self.code,
            self.message,
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "path": self.path,
        }
        if self.details:
            data["details"] = self.details
        return data


def diagnostic(code: str, severity: Severity, message: str, path: str = "$", **details: Any) -> Diagnostic:
    return Diagnostic(code=code, severity=severity, message=message, path=path, details=details)


def sort_diagnostics(items: list[Diagnostic]) -> list[Diagnostic]:
    return sorted(items, key=lambda item: item.sort_key())


def status_from_diagnostics(items: list[Diagnostic]) -> ValidationStatus:
    """Return the legacy validation-result status used by current validators."""

    if any(item.severity == "error" for item in items):
        return "invalid"
    if any(item.severity == "insufficient_evidence" for item in items):
        return "insufficient_evidence"
    return "valid"


def project_gate_status_from_diagnostics(items: list[Diagnostic]) -> ProjectGateStatus:
    """Map diagnostics into the target Project Gate transition status vocabulary."""

    if any(item.severity == "error" for item in items):
        return "invalid"
    if any(item.severity == "insufficient_evidence" for item in items):
        return "insufficient_evidence"
    if any(item.severity == "warning" for item in items):
        return "repair_needed"
    return "accepted"


def persian_summary(status: str) -> str:
    return {
        "accepted": "✅ پذیرفته شد — بسته معتبر است و شواهد لازم برای این بررسی وجود دارد.",
        "valid": "✅ پذیرفته شد — بسته معتبر است و وضعیت legacy `valid` به‌عنوان معادل `accepted` نمایش داده شد.",
        "repair_needed": "🛠️ نیازمند اصلاح — بسته قابل فهم است، اما هشدارهای قابل اصلاح دارد.",
        "invalid": "❌ نامعتبر — بسته بدون حدس یا اصلاح خودکار رد شد.",
        "insufficient_evidence": "⚠️ شواهد کافی نیست — وضعیت به‌صورت ساختاری ثبت شد و هیچ مقدار گمشده‌ای حدس زده نشد.",
    }.get(status, f"وضعیت: {status}")
