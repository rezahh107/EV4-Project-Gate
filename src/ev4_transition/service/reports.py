from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

from ev4_transition.reports import canonical_result_hash_for_report, render_json_result, render_markdown_report, render_optional_html_report, render_plain_summary

from .models import ReportBundle


def build_report_bundle(result: dict[str, Any]) -> ReportBundle:
    """Build UI-downloadable report strings without mutating the engine result."""

    snapshot = deepcopy(result)
    render_diagnostics: list[dict[str, Any]] = []
    try:
        canonical_json = render_json_result(snapshot)
    except Exception as exc:
        diagnostic = _report_failure_diagnostic("PG.SERVICE.REPORT_JSON_RENDER_FAILED", exc)
        render_diagnostics.append(diagnostic)
        canonical_json = _fallback_canonical_json(diagnostic)
    try:
        persian_plain_summary = render_plain_summary(snapshot)
    except Exception as exc:
        persian_plain_summary = _fallback_persian_summary(exc)
    try:
        markdown_report = render_markdown_report(snapshot)
    except Exception:
        markdown_report = None
    try:
        html_report = render_optional_html_report(snapshot)
    except Exception:
        html_report = None
    try:
        result_hash = canonical_result_hash_for_report(snapshot)
    except Exception:
        result_hash = None
    return ReportBundle(
        canonical_json=canonical_json,
        persian_plain_summary=persian_plain_summary,
        markdown_report=markdown_report,
        html_report=html_report,
        result_hash=result_hash,
        render_diagnostics=render_diagnostics,
    )


def _report_failure_diagnostic(code: str, exc: Exception) -> dict[str, Any]:
    return {
        "code": code,
        "severity": "error",
        "message": "Report JSON rendering failed; fallback report emitted without mutating engine result.",
        "path": "$.report_bundle.canonical_json",
        "details": {"error_type": type(exc).__name__},
    }


def _fallback_canonical_json(diagnostic: dict[str, Any]) -> str:
    payload = {
        "schema_version": "project-gate-service-report-fallback.v1",
        "status": "invalid",
        "diagnostics": [deepcopy(diagnostic)],
        "output": None,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"


def _fallback_persian_summary(exc: Exception) -> str:
    return (
        "\u200f❌ نامعتبر — tone: danger — status: invalid\n"
        "تولید خلاصه فارسی گزارش شکست خورد؛ Service Layer به‌جای crash کردن، fallback امن تولید کرد.\n"
        f"جزئیات فنی: error_type={type(exc).__name__}\n"
    )
