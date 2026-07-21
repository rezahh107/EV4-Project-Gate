"""Local Persian-first operator UI for EV4 Project Gate.

The UI package is intentionally a thin operator layer. It delegates validation and
transition execution to the shared Project Gate service and does not implement
specialist transition semantics.
"""

from importlib import import_module

__all__ = []


def _install_operator_compatibility_contract() -> None:
    """Preserve the published Prompt-06 visual/text contract after runtime repair."""

    app = import_module(".app", __name__)
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


_install_operator_compatibility_contract()
