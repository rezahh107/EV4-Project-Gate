from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Severity = Literal["error", "warning", "info", "insufficient_evidence"]

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


def status_from_diagnostics(items: list[Diagnostic]) -> str:
    if any(item.severity == "error" for item in items):
        return "invalid"
    if any(item.severity == "insufficient_evidence" for item in items):
        return "insufficient_evidence"
    return "valid"


def persian_summary(status: str) -> str:
    return {
        "valid": "بسته معتبر است و شواهد لازم برای این بررسی وجود دارد.",
        "invalid": "بسته نامعتبر است و بدون حدس یا اصلاح خودکار رد شد.",
        "insufficient_evidence": "شواهد کافی نیست؛ وضعیت به‌صورت ساختاری ثبت شد و هیچ مقدار گمشده‌ای حدس زده نشد.",
    }.get(status, f"وضعیت: {status}")
