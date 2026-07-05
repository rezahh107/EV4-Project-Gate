from __future__ import annotations

from copy import deepcopy
from typing import Any

from ev4_transition.reports import canonical_result_hash_for_report, render_json_result, render_markdown_report, render_optional_html_report, render_plain_summary

from .models import ReportBundle


def build_report_bundle(result: dict[str, Any]) -> ReportBundle:
    """Build UI-downloadable report strings without mutating the engine result."""

    snapshot = deepcopy(result)
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
        canonical_json=render_json_result(snapshot),
        persian_plain_summary=render_plain_summary(snapshot),
        markdown_report=markdown_report,
        html_report=html_report,
        result_hash=result_hash,
    )
