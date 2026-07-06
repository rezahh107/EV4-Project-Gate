from __future__ import annotations

from html import escape as _escape

LTR_ISOLATE_START = "\u2066"
ISOLATE_END = "\u2069"
RTL_MARK = "\u200f"


def escape_html(value: object) -> str:
    """Escape text for HTML output without changing directionality."""

    return _escape(str(value), quote=True)


def isolate_ltr_text(value: object) -> str:
    """Return a copyable plain-text LTR-isolated technical fragment."""

    return f"{LTR_ISOLATE_START}{str(value)}{ISOLATE_END}"


def bdi_ltr(value: object) -> str:
    """Return an HTML LTR-isolated code token for technical identifiers."""

    return f'<bdi dir="ltr"><code>{escape_html(value)}</code></bdi>'


def rtl_text(value: object) -> str:
    """Return escaped Persian/RTL text wrapped in an RTL span."""

    return f'<span lang="fa" dir="rtl">{escape_html(value)}</span>'


def ltr_code_block(value: object) -> str:
    """Return an escaped LTR code block for JSON, paths, commands, or raw diagnostics."""

    return f'<pre dir="ltr"><code>{escape_html(value)}</code></pre>'


def markdown_code_ltr(value: object) -> str:
    """Backward-compatible alias for LTR-isolated inline code in Markdown/HTML."""

    return bdi_ltr(value)


def html_code_ltr(value: object) -> str:
    """Backward-compatible alias for LTR-isolated inline code in HTML."""

    return bdi_ltr(value)
