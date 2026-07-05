from __future__ import annotations

from html import escape

LTR_ISOLATE_START = "\u2066"
ISOLATE_END = "\u2069"
RTL_MARK = "\u200f"


def isolate_ltr_text(value: object) -> str:
    """Return a copyable plain-text LTR-isolated technical fragment."""

    return f"{LTR_ISOLATE_START}{str(value)}{ISOLATE_END}"


def markdown_code_ltr(value: object) -> str:
    """Return copyable Markdown/HTML for LTR technical identifiers inside RTL text."""

    return f'<bdi dir="ltr"><code>{escape(str(value), quote=False)}</code></bdi>'


def html_code_ltr(value: object) -> str:
    return markdown_code_ltr(value)
