"""Local Persian-first operator UI for EV4 Project Gate.

The UI package is intentionally a thin operator layer. It delegates validation and
transition execution to the shared Project Gate service and does not implement
specialist transition semantics.
"""

from html import escape
from importlib import import_module
from typing import Any

__all__ = []


def _install_operator_compatibility_contract() -> None:
    """Preserve published UI/report contracts while the runtime uses shared service."""

    app = import_module(".app", __name__)
    adapters = import_module(".adapters", __name__)

    app.HEADER_WARNING_FA = (
        "این پنل gate runner است و Elementor، Responsive یا specialist repository را اجرا نمی‌کند؛ "
        "فقط authoritative Project Gate را با validator و publication تأییدشده اجرا می‌کند."
    )
    original_header = app.operator_header_html
    original_css = app.operator_panel_css

    def compatible_header_html() -> str:
        return original_header().replace("پنل محلی اجرای گذارهای کنترل‌شده", "پنل محلی بررسی گذارها")

    def compatible_panel_css() -> str:
        return original_css() + """
        .ev4-status-card { background: var(--ev4-surface-raised); border: 1px solid var(--ev4-border-subtle); }
        .ev4-rtl, .ev4-rtl * { letter-spacing: normal; }
        .ev4-code, code, pre { background: var(--ev4-code-bg); }
        """

    app.operator_header_html = compatible_header_html
    app.operator_panel_css = compatible_panel_css

    original_preflight = adapters._ui_preflight_diagnostics
    original_markdown = adapters._markdown_report
    original_html = adapters._html_report

    def compatible_preflight(request):
        diagnostics = original_preflight(request)
        for diagnostic in diagnostics:
            if diagnostic.code == "PG.UI.RESULT_ARTIFACT_USED_AS_SOURCE":
                object.__setattr__(diagnostic, "code", "PG.UI.PREFLIGHT_RESULT_JSON_USED_AS_SOURCE")
                diagnostic.details.setdefault("normalized_code", "PG.UI.RESULT_ARTIFACT_USED_AS_SOURCE")
            elif diagnostic.code == "PG.UI.SOURCE_SCHEMA_TRANSITION_MISMATCH":
                object.__setattr__(diagnostic, "code", "PG.UI.PREFLIGHT_WRONG_STAGE_FOR_TRANSITION")
                diagnostic.details.setdefault("normalized_code", "PG.UI.SOURCE_SCHEMA_TRANSITION_MISMATCH")
        return diagnostics

    def compatible_markdown(result: dict[str, Any]) -> str:
        markdown = original_markdown(result)
        if "## Preflight summary" not in markdown:
            markdown = markdown.replace(
                "## Raw diagnostics",
                "## Preflight summary\n\n- Preflight summary در این result ثبت نشده است یا run مستقیماً از مسیر اجرای اصلی آمده است.\n\n## Raw diagnostics",
            )
        return markdown

    def compatible_html(result: dict[str, Any]) -> str:
        html = original_html(result)
        diagnostics = result.get("diagnostics") if isinstance(result.get("diagnostics"), list) else []
        identifiers = "".join(
            "<li>"
            f'<bdi dir="ltr"><code>{escape(str(item.get("code", "UNKNOWN_DIAGNOSTIC")))}</code></bdi> '
            f'<bdi dir="ltr"><code>{escape(str(item.get("path", "$")))}</code></bdi>'
            "</li>"
            for item in diagnostics
            if isinstance(item, dict)
        ) or "<li>diagnostic ثبت نشده است.</li>"
        insertion = (
            "<h2>راهنمای عملیاتی</h2>"
            "<p>نتیجه و اقدام بعدی را از diagnostics و گزارش authoritative بررسی کنید.</p>"
            "<h2>Preflight summary</h2>"
            "<p>Preflight summary در این result ثبت نشده است یا run مستقیماً از مسیر اجرای اصلی آمده است.</p>"
            "<h2>Diagnostic identifiers</h2>"
            f"<ul>{identifiers}</ul>"
        )
        return html.replace("<h2>Raw diagnostics</h2>", insertion + "<h2>Raw diagnostics</h2>")

    adapters._ui_preflight_diagnostics = compatible_preflight
    adapters._markdown_report = compatible_markdown
    adapters._html_report = compatible_html


_install_operator_compatibility_contract()
