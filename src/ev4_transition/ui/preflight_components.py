from __future__ import annotations

from html import escape

from ev4_transition.presentation.bidi import html_code_ltr
from ev4_transition.service.preflight import PreflightCheck, PreflightResult


def preflight_result_html(result: PreflightResult) -> str:
    """Render a read-only preflight result as an RTL Persian checklist."""

    items = "".join(_check_html(check) for check in result.checks)
    return "\n".join(
        [
            '<section lang="fa" dir="rtl" role="status" aria-live="polite" class="ev4-preflight-result">',
            "<h3>بررسی آماده‌سازی مسیرها / Preflight</h3>",
            f"<p><strong>وضعیت آماده‌سازی:</strong> {escape(result.summary_fa)}</p>",
            f'<p><span dir="ltr">preflight_status:</span> {html_code_ltr(result.status)} · <span dir="ltr">transition:</span> {html_code_ltr(result.transition_choice)}</p>',
            "<p class=\"ev4-helper-block\">Preflight اجرای کامل Project Gate نیست و repositoryها یا JSON را تغییر نمی‌دهد.</p>",
            f'<ul class="ev4-preflight-list">{items}</ul>',
            "</section>",
        ]
    )


def _check_html(check: PreflightCheck) -> str:
    icon = {"ok": "✓", "warning": "⚠️", "error": "❌", "not_required": "↷", "unknown": "؟"}.get(check.status, "؟")
    css_class = f"ev4-preflight-{escape(str(check.status))}"
    detail = f"<div><strong>جزئیات فنی:</strong> {html_code_ltr(check.technical_detail)}</div>" if check.technical_detail else ""
    classification = f"<div><strong>classification:</strong> {html_code_ltr(check.classification)}</div>" if check.classification else ""
    action = f"<div><strong>اقدام پیشنهادی:</strong> {escape(check.next_action_fa)}</div>" if check.next_action_fa else ""
    return (
        f'<li class="{css_class}">'
        f'<span class="ev4-preflight-icon">{icon}</span> '
        f'<strong>{escape(check.label_fa)}</strong>: {escape(check.message_fa)}'
        f"{detail}{classification}{action}</li>"
    )
