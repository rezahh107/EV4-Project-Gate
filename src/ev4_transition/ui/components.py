from __future__ import annotations

from html import escape
from typing import Any

from ev4_transition.presentation.bidi import isolate_ltr_text, markdown_code_ltr
from ev4_transition.presentation.status_mapping import presentation_for_status

from .state import STATUS_MEANINGS_FA, STATUS_NEXT_ACTION_FA, normalize_ui_status


DIAGNOSTIC_HEADERS = ["code", "severity", "path", "message", "owner/repo", "next action"]
CAPABILITY_HEADERS = ["بخش", "orchestration", "CLI", "evidence", "UI status", "توضیح"]


def ltr_token(value: object) -> str:
    """Return a copyable LTR-isolated token for tables and plain-text cells."""

    return isolate_ltr_text(value)


def status_summary_markdown(result: dict[str, Any]) -> str:
    status = normalize_ui_status(result.get("status", "invalid"))
    presentation = presentation_for_status(status)
    meaning = STATUS_MEANINGS_FA[status]
    next_action = STATUS_NEXT_ACTION_FA[status]
    original_status = str(result.get("status", status))
    status_line = f"/ status: {markdown_code_ltr(status)} / semantic tone: {markdown_code_ltr(presentation.tone)}"
    if original_status != status:
        status_line += f" / engine status: {markdown_code_ltr(original_status)}"

    return "\n".join(
        [
            '<section lang="fa" dir="rtl">',
            "### نتیجه بررسی",
            f"<p>{presentation.icon} <strong>وضعیت: {escape(presentation.persian_label)}</strong> {status_line}</p>",
            f"<p><strong>معنی:</strong> {escape(meaning)}</p>",
            f"<p><strong>اقدام بعدی:</strong> {escape(next_action)}</p>",
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
            ltr_token("UI wiring pending"),
            "در این Prompt اجرا نمی‌شود و fake execution ندارد.",
        ],
        [
            "Builder → Responsive",
            ltr_token(builder_to_responsive.get("orchestration_baseline", "unknown")),
            ltr_token(builder_to_responsive.get("cli_exposure", "unknown")),
            ltr_token(builder_to_responsive.get("real_non_synthetic_handoff", "unknown")),
            ltr_token("UI wiring pending"),
            "نیازمند اتصال service layer در Prompt 2 است.",
        ],
        [
            "Final Evidence Gate",
            ltr_token(final_gate.get("orchestration_baseline", "unknown")),
            ltr_token(final_gate.get("cli_exposure", "unknown")),
            ltr_token(final_gate.get("real_non_synthetic_evidence", "unknown")),
            ltr_token("UI wiring pending"),
            "فقط وضعیت capability خوانده می‌شود؛ transition اجرا نمی‌شود.",
        ],
        [
            "UI",
            ltr_token("this panel"),
            ltr_token("not a public CLI transition"),
            ltr_token(ui.get("status", "unknown")),
            ltr_token("local operator panel"),
            "این ردیف فقط وضعیت پنل محلی را توضیح می‌دهد و capability inspector در زمان اجرا فایل را تغییر نمی‌دهد.",
        ],
    ]
