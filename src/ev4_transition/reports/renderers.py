from __future__ import annotations

from copy import deepcopy
import json
from html import escape
from typing import Any

from ev4_transition.canonical_json import canonical_dumps, canonical_sha256
from ev4_transition.presentation.bidi import RTL_MARK, isolate_ltr_text, markdown_code_ltr
from ev4_transition.presentation.status_mapping import presentation_for_status
from ev4_transition.reports.decision_receipts import build_kernel_decision_receipt

_PROGRESS_KEYS_EXCLUDED_FROM_REPORT_HASH = {"progress_events", "progress_event", "ui_progress_events"}
_TECHNICAL_KEY_PARTS = (
    "path",
    "schema",
    "hash",
    "sha",
    "code",
    "id",
    "repository",
    "repo",
    "ref",
    "commit",
    "command",
    "json",
    "yaml",
    "diagnostic",
)
_STATUS_EXPLANATIONS = {
    "accepted": "این بسته معتبر است و برای همین بررسی پذیرفته شد، چون شواهد لازم به‌صورت صریح وجود دارد.",
    "repair_needed": "بسته قابل فهم است، اما چند مورد قابل اصلاح دارد و نباید به مرحله بعدی به‌عنوان نتیجه نهایی عبور کند.",
    "insufficient_evidence": "شواهد برای تصمیم امن کافی نیست. این وضعیت هشدار/مسدودکننده است، نه اطلاع عادی.",
    "invalid": "بسته نامعتبر است و بدون حدس، نرمال‌سازی پنهان یا اصلاح خودکار رد شد.",
}
_NEXT_ACTIONS = {
    "accepted": "خروجی را فقط در همان محدوده شواهد ثبت‌شده استفاده کن؛ این پذیرش، اثبات production/readiness عمومی نیست.",
    "repair_needed": "Diagnostics را اصلاح کن و بسته را دوباره از همان ورودی رسمی بساز.",
    "insufficient_evidence": "شواهد گمشده را از owner repository یا validator رسمی تهیه کن و دوباره Gate را اجرا کن.",
    "invalid": "ساختار، schema identity، مسیرها، hashها و diagnosticهای خطادار را اصلاح کن و دوباره اجرا کن.",
}


def canonical_result_hash_for_report(result: dict[str, Any]) -> str:
    """Hash the final result for report use without UI/progress-only events."""

    return canonical_sha256(_without_progress_events(result))


def render_json_result(result: dict[str, Any]) -> str:
    """Render machine-readable JSON without mutating the source result."""

    return canonical_dumps(deepcopy(result)) + "\n"


def render_plain_summary(result: dict[str, Any], *, title: str = "گزارش Project Gate") -> str:
    snapshot = deepcopy(result)
    status = str(snapshot.get("status", "invalid"))
    presentation = presentation_for_status(status)
    diagnostics = _diagnostics(snapshot)
    receipt = build_kernel_decision_receipt(snapshot)
    lines = [
        f"{RTL_MARK}{title}",
        f"{presentation.icon} {presentation.persian_label} — tone: {isolate_ltr_text(presentation.tone)} — status: {isolate_ltr_text(status)}",
        _STATUS_EXPLANATIONS[presentation.status],
        f"رسید Kernel decision: {receipt.message_fa}",
        f"اقدام بعدی: {_NEXT_ACTIONS[presentation.status]}",
        f"خلاصه diagnostics: {len(diagnostics)} مورد",
        "جزئیات پیشرفته / Evidence / Diagnostics:",
    ]
    if diagnostics:
        for diagnostic in diagnostics:
            code = isolate_ltr_text(diagnostic.get("code", "UNKNOWN_DIAGNOSTIC"))
            severity = isolate_ltr_text(diagnostic.get("severity", "unknown"))
            path = isolate_ltr_text(diagnostic.get("path", "$"))
            lines.append(f"- {code} / severity={severity} / path={path}: {diagnostic.get('message', '')}")
    else:
        lines.append("- diagnostic ثبت نشده است.")
    return "\n".join(lines) + "\n"


def render_markdown_report(result: dict[str, Any], *, title: str = "گزارش Project Gate", theme: str = "light") -> str:
    snapshot = deepcopy(result)
    status = str(snapshot.get("status", "invalid"))
    presentation = presentation_for_status(status)
    diagnostics = _diagnostics(snapshot)
    technical_refs = _technical_references(snapshot)
    result_hash = canonical_result_hash_for_report(snapshot)
    receipt = build_kernel_decision_receipt(snapshot)
    status_token = f"status.{presentation.status}"
    parts = [
        f'<section lang="fa" dir="rtl" class="ev4-report ev4-theme-{escape(theme)}">',
        f"\n# {escape(title)}",
        "",
        "## وضعیت",
        f'<p class="status status--{presentation.tone}" data-status="{presentation.status}" data-tone="{presentation.tone}" data-token="{status_token}">',
        f"{presentation.icon} <strong>{escape(presentation.persian_label)}</strong> — semantic tone: {markdown_code_ltr(presentation.tone)} — status: {markdown_code_ltr(status)}",
        "</p>",
        "",
        "## توضیح فارسی",
        escape(_STATUS_EXPLANATIONS[presentation.status]),
        "",
        "## رسید Kernel decision",
        escape(receipt.message_fa),
        "",
        "## اقدام بعدی",
        escape(_NEXT_ACTIONS[presentation.status]),
        "",
        "## خلاصه Diagnostics",
        f"تعداد diagnosticها: {markdown_code_ltr(len(diagnostics))}",
        "",
        "## جزئیات پیشرفته / Evidence / Diagnostics",
        f"Canonical report hash بدون progress events: {markdown_code_ltr(result_hash)}",
        "",
    ]
    if diagnostics:
        parts.append("### Diagnostics")
        for diagnostic in diagnostics:
            parts.append(
                "- "
                f"code: {markdown_code_ltr(diagnostic.get('code', 'UNKNOWN_DIAGNOSTIC'))} — "
                f"severity: {markdown_code_ltr(diagnostic.get('severity', 'unknown'))} — "
                f"path: {markdown_code_ltr(diagnostic.get('path', '$'))} — "
                f"message: {_neutralize_markdown_fences(escape(str(diagnostic.get('message', ''))))}"
            )
    else:
        parts.append("### Diagnostics\n- diagnostic ثبت نشده است.")
    parts.extend(["", "### Technical references"])
    if technical_refs:
        for key_path, value in technical_refs[:60]:
            parts.append(f"- {markdown_code_ltr(key_path)}: {markdown_code_ltr(value)}")
    else:
        parts.append("- reference فنی قابل استخراجی ثبت نشده است.")
    raw_diagnostics = _neutralize_markdown_fences(json.dumps(diagnostics, ensure_ascii=False, indent=2))
    raw_result = _neutralize_markdown_fences(canonical_dumps(snapshot))
    parts.extend([
        "",
        "## Preflight summary",
        "Preflight authoritative و diagnostics این اجرا در نتیجه ثبت شده‌اند.",
        "",
        "## Raw diagnostics",
        "```json",
        raw_diagnostics,
        "```",
        "",
        "## Raw JSON result",
        "```json",
        raw_result,
        "```",
        "</section>",
    ])
    return "\n".join(parts) + "\n"


def render_optional_html_report(result: dict[str, Any], *, title: str = "گزارش Project Gate", theme: str = "light") -> str:
    snapshot = deepcopy(result)
    diagnostics = _diagnostics(snapshot)
    diagnostic_items = "".join(
        "<li>"
        f'<bdi dir="ltr"><code>{escape(str(item.get("code", "UNKNOWN_DIAGNOSTIC")))}</code></bdi> — '
        f'<bdi dir="ltr"><code>{escape(str(item.get("path", "$")))}</code></bdi>'
        "</li>"
        for item in diagnostics
    ) or "<li>diagnostic ثبت نشده است.</li>"
    raw_diagnostics = escape(json.dumps(diagnostics, ensure_ascii=False, indent=2))
    raw_result = escape(canonical_dumps(snapshot))
    return "\n".join(
        [
            '<!doctype html>',
            '<html lang="fa" dir="rtl">',
            '<head><meta charset="utf-8"><title>' + escape(title) + "</title></head>",
            '<body>',
            f'<main class="ev4-report ev4-theme-{escape(theme)}" lang="fa" dir="rtl">',
            f'<h1>{escape(title)}</h1>',
            '<h2>راهنمای عملیاتی</h2>',
            f'<p>{escape(_STATUS_EXPLANATIONS[presentation_for_status(str(snapshot.get("status", "invalid"))).status])}</p>',
            '<h2>Preflight summary</h2>',
            '<p>Preflight authoritative و diagnostics این اجرا در نتیجه ثبت شده‌اند.</p>',
            '<h2>Diagnostic identifiers</h2>',
            f'<ul>{diagnostic_items}</ul>',
            '<h2>Raw diagnostics</h2>',
            f'<pre dir="ltr"><code>{raw_diagnostics}</code></pre>',
            '<h2>Raw JSON result</h2>',
            f'<pre dir="ltr"><code>{raw_result}</code></pre>',
            '</main>',
            '</body>',
            '</html>',
            '',
        ]
    )



def _neutralize_markdown_fences(value: str) -> str:
    return value.replace("```", "``\u200b`")

def _diagnostics(result: dict[str, Any]) -> list[dict[str, Any]]:
    diagnostics = result.get("diagnostics", [])
    if not isinstance(diagnostics, list):
        return []
    return [item for item in diagnostics if isinstance(item, dict)]


def _without_progress_events(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _without_progress_events(child)
            for key, child in value.items()
            if key not in _PROGRESS_KEYS_EXCLUDED_FROM_REPORT_HASH
        }
    if isinstance(value, list):
        return [_without_progress_events(child) for child in value]
    return deepcopy(value)


def _technical_references(value: Any, path: str = "$", results: list[tuple[str, str]] | None = None) -> list[tuple[str, str]]:
    if results is None:
        results = []
    if len(results) >= 80:
        return results
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if isinstance(child, str) and _is_technical_key(key):
                results.append((child_path, child))
            elif isinstance(child, (int, float)) and _is_technical_key(key):
                results.append((child_path, str(child)))
            _technical_references(child, child_path, results)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _technical_references(child, f"{path}[{index}]", results)
    return results


def _is_technical_key(key: str) -> bool:
    lower = key.lower()
    return any(part in lower for part in _TECHNICAL_KEY_PARTS)
