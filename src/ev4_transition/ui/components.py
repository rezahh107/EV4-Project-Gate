from __future__ import annotations

from html import escape
from typing import Any

from ev4_transition.presentation.bidi import html_code_ltr, isolate_ltr_text, markdown_code_ltr
from ev4_transition.presentation.status_mapping import presentation_for_status
from ev4_transition.service.guidance import OperatorGuidance, build_operator_guidance

from .state import STATUS_MEANINGS_FA, STATUS_NEXT_ACTION_FA, normalize_ui_status


DIAGNOSTIC_HEADERS = ["code", "severity", "path", "message", "owner/repo", "next action"]
CAPABILITY_HEADERS = ["بخش", "orchestration", "CLI", "evidence", "UI status", "توضیح"]


def ltr_token(value: object) -> str:
    """Return a copyable LTR-isolated token for tables and plain-text cells."""

    if value is None:
        return ""
    return isolate_ltr_text(str(value))


def status_summary_markdown(result: dict[str, Any]) -> str:
    status = normalize_ui_status(result.get("status", "invalid"))
    presentation = presentation_for_status(status)
    meaning = STATUS_MEANINGS_FA[status]
    next_action = STATUS_NEXT_ACTION_FA[status]
    original_status = str(result.get("status", status))
    guidance = build_operator_guidance(result)
    status_meta = (
        f'<span class="ev4-status-meta"><span dir="ltr">status:</span> {markdown_code_ltr(status)} '
        f'· <span dir="ltr">semantic tone:</span> {markdown_code_ltr(presentation.tone)}'
    )
    if original_status != status:
        status_meta += f' · <span dir="ltr">engine status:</span> {markdown_code_ltr(original_status)}'
    status_meta += "</span>"

    return "\n".join(
        [
            '<section lang="fa" dir="rtl" role="status" aria-live="polite" class="ev4-status-content">',
            "<h3>نتیجه بررسی</h3>",
            f'<p class="ev4-status-title">{presentation.icon} <strong>وضعیت: {escape(presentation.persian_label)}</strong></p>',
            f"<p>{status_meta}</p>",
            f"<p><strong>معنی:</strong> {escape(meaning)}</p>",
            f"<p><strong>اقدام بعدی:</strong> {escape(next_action)}</p>",
            _guidance_html(guidance),
            (
                "<p><strong>هشدار محدوده:</strong> این ابزار فقط بررسی Project Gate را اجرا می‌کند؛ "
                "اثبات نهایی تولید، فرانت‌اند، Elementor واقعی یا صحت Responsive نیست.</p>"
            ),
            "</section>",
        ]
    )


def diagnostics_to_rows(diagnostics: Any) -> list[list[str]]:
    if not isinstance(diagnostics, list):
        return []

    rows: list[list[str]] = []
    for item in diagnostics:
        if not isinstance(item, dict):
            continue
        details = item.get("details")
        details_map = details if isinstance(details, dict) else {}
        owner_repo = (
            details_map.get("owner_repo")
            or details_map.get("owner_repository")
            or details_map.get("repository")
            or details_map.get("repo")
            or details_map.get("owner")
            or ""
        )
        next_action = details_map.get("next_action") or details_map.get("repair_action") or ""
        rows.append(
            [
                ltr_token(item.get("code", "UNKNOWN_DIAGNOSTIC")),
                ltr_token(item.get("severity", "unknown")),
                ltr_token(item.get("path", "$")),
                str(item.get("message", "")),
                ltr_token(owner_repo) if owner_repo else "",
                str(next_action),
            ]
        )
    return rows


def capability_rows_from_payload(payload: dict[str, Any]) -> list[list[str]]:
    capabilities = payload.get("capabilities", {})
    if not isinstance(capabilities, dict):
        capabilities = {}

    architect = capabilities.get("architect_to_ce", {}) if isinstance(capabilities.get("architect_to_ce"), dict) else {}
    ce_to_builder = capabilities.get("ce_to_builder", {}) if isinstance(capabilities.get("ce_to_builder"), dict) else {}
    builder_to_responsive = (
        capabilities.get("builder_to_responsive", {}) if isinstance(capabilities.get("builder_to_responsive"), dict) else {}
    )
    final_gate = capabilities.get("final_evidence_gate", {}) if isinstance(capabilities.get("final_evidence_gate"), dict) else {}
    ui = capabilities.get("user_interface", {}) if isinstance(capabilities.get("user_interface"), dict) else {}

    return [
        [
            "Architect → CE",
            ltr_token(architect.get("orchestration_baseline", "unknown")),
            ltr_token(architect.get("cli_exposure", "unknown")),
            ltr_token(architect.get("real_non_synthetic_handoff", "unknown")),
            ltr_token("wired in UI when local Architect and CE paths are supplied"),
            "اجرای واقعی فقط با مسیرهای local checkout انجام می‌شود.",
        ],
        [
            "CE → Builder",
            ltr_token(ce_to_builder.get("orchestration_baseline", "unknown")),
            ltr_token(ce_to_builder.get("cli_exposure", "unknown")),
            ltr_token(ce_to_builder.get("real_non_synthetic_handoff", "unknown")),
            ltr_token("wired through internal service; guarded/fail-closed"),
            "در UI از مسیر service اجرا می‌شود و در نبود شواهد/checkout معتبر fail-closed می‌ماند.",
        ],
        [
            "Builder → Responsive",
            ltr_token(builder_to_responsive.get("orchestration_baseline", "unknown")),
            ltr_token(builder_to_responsive.get("cli_exposure", "unknown")),
            ltr_token(builder_to_responsive.get("real_non_synthetic_handoff", "unknown")),
            ltr_token("wired through internal service; guarded/fail-closed"),
            "در UI از مسیر service اجرا می‌شود و بدون owner evidence معتبر accepted نمی‌شود.",
        ],
        [
            "Final Evidence Gate",
            ltr_token(final_gate.get("orchestration_baseline", "unknown")),
            ltr_token(final_gate.get("cli_exposure", "unknown")),
            ltr_token(final_gate.get("real_non_synthetic_evidence", "unknown")),
            ltr_token("wired through internal service; guarded/fail-closed"),
            "در UI از مسیر service اجرا می‌شود و بدون evidence نهایی معتبر accepted نمی‌شود.",
        ],
        [
            "UI",
            ltr_token(ui.get("service_routing", "unknown")),
            ltr_token("not a public CLI transition"),
            ltr_token(ui.get("browser_accessibility_evidence", ui.get("status", "unknown"))),
            ltr_token(ui.get("status", "unknown")),
            "این ردیف وضعیت runtime capability truth پنل محلی را نشان می‌دهد؛ browser accessibility بدون QA واقعی insufficient_evidence می‌ماند.",
        ],
    ]


def _guidance_html(guidance: OperatorGuidance) -> str:
    passed = "".join(f"<li>✓ {escape(item)}</li>" for item in guidance.passed_steps_fa)
    actions = "".join(f"<li>{escape(item)}</li>" for item in guidance.next_actions_fa)
    groups = _diagnostic_groups_html(guidance)
    repair = _repair_prompt_html(guidance)
    safe_label = "بله" if guidance.safe_to_continue else "خیر"
    return "\n".join(
        [
            '<div class="ev4-guidance" lang="fa" dir="rtl">',
            "<h3>راهنمای عملیاتی</h3>",
            f"<p><strong>خلاصه:</strong> {escape(guidance.headline_fa)}</p>",
            f"<p><strong>کجا متوقف شد؟</strong> {escape(guidance.where_stopped_fa)}</p>",
            "<p><strong>چه چیزی درست پیش رفت؟</strong></p>",
            f"<ul>{passed}</ul>",
            f"<p><strong>مشکل فعلی چیست؟</strong> {escape(guidance.current_problem_fa)}</p>",
            "<p><strong>اقدام بعدی دقیق:</strong></p>",
            f"<ol>{actions}</ol>",
            f"<p><strong>آیا خروجی مرحله بعد ساخته شد؟</strong> {escape(guidance.output_state_fa)}</p>",
            f"<p><strong>ادامه دادن امن است؟</strong> {escape(safe_label)}</p>",
            groups,
            repair,
            "</div>",
        ]
    )


def _diagnostic_groups_html(guidance: OperatorGuidance) -> str:
    if not guidance.diagnostic_groups:
        return "<p><strong>گروه‌بندی diagnostics:</strong> diagnostic ثبت نشده است.</p>"
    rows = []
    for group in guidance.diagnostic_groups:
        messages = "".join(f"<li>{escape(message)}</li>" for message in group.top_messages if message)
        rows.append(
            "<li>"
            f"<strong>{escape(group.title_fa)}</strong> — count: {html_code_ltr(group.count)}"
            f"<ul>{messages}</ul>"
            f"<p><strong>اقدام گروه:</strong> {escape(group.next_action_fa)}</p>"
            "</li>"
        )
    return "<details class=\"ev4-guidance-details\"><summary>گروه‌بندی diagnostics</summary><ul>" + "".join(rows) + "</ul></details>"


def _repair_prompt_html(guidance: OperatorGuidance) -> str:
    if not guidance.repair_prompt_fa_or_en:
        return ""
    prompt = escape(guidance.repair_prompt_fa_or_en)
    return (
        '<details class="ev4-guidance-details ev4-repair-prompt">'
        '<summary>Repair prompt / پرامپت اصلاح</summary>'
        f'<pre dir="ltr"><code>{prompt}</code></pre>'
        '</details>'
    )
