from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import ServiceDiagnostic


class _NonFiniteJsonConstant(ValueError):
    def __init__(self, constant: str) -> None:
        self.constant = constant
        super().__init__(f"Non-finite JSON constant is not allowed: {constant}")


@dataclass(frozen=True)
class ParsedJsonInput:
    value: Any
    diagnostics: list[ServiceDiagnostic]
    source: str


def parse_json_input(
    *,
    input_json_path: str | None = None,
    input_json_text: str | None = None,
    input_data: Any = None,
) -> ParsedJsonInput:
    """Parse UI-provided JSON without mutating caller-owned objects."""

    provided = [
        name
        for name, value in (
            ("file_path", input_json_path),
            ("json_text", input_json_text),
            ("dict", input_data),
        )
        if value is not None
    ]
    if not provided:
        return ParsedJsonInput(
            None,
            [
                ServiceDiagnostic(
                    "PG.SERVICE.JSON_INPUT_MISSING",
                    "error",
                    "A JSON file, pasted JSON text, or parsed JSON object is required for this check.",
                    "$",
                )
            ],
            "missing",
        )
    if len(provided) > 1:
        return ParsedJsonInput(
            None,
            [
                ServiceDiagnostic(
                    "PG.SERVICE.JSON_INPUT_AMBIGUOUS",
                    "error",
                    "Provide only one JSON input source: file path, pasted JSON text, or parsed object.",
                    "$",
                    {"sources": provided},
                )
            ],
            "missing",
        )

    if input_data is not None:
        return ParsedJsonInput(deepcopy(input_data), [], "dict")

    if input_json_text is not None:
        return _parse_json_text(input_json_text, "json_text")

    assert input_json_path is not None
    try:
        text = Path(input_json_path).read_text(encoding="utf-8")
    except (OSError, ValueError) as exc:
        return ParsedJsonInput(
            None,
            [
                ServiceDiagnostic(
                    "PG.SERVICE.FILE_READ_ERROR",
                    "error",
                    "JSON input file could not be read.",
                    "$.input_json_path",
                    {"error_type": type(exc).__name__, "path": input_json_path},
                )
            ],
            "file_path",
        )
    return _parse_json_text(text, "file_path", input_json_path=input_json_path)


def _parse_json_text(text: str, source: str, *, input_json_path: str | None = None) -> ParsedJsonInput:
    try:
        return ParsedJsonInput(json.loads(text, parse_constant=_reject_non_finite_constant), [], source)
    except _NonFiniteJsonConstant as exc:
        details: dict[str, Any] = {"constant": exc.constant}
        if input_json_path is not None:
            details["path"] = input_json_path
        return ParsedJsonInput(
            None,
            [
                ServiceDiagnostic(
                    "PG.SERVICE.NON_FINITE_JSON_CONSTANT",
                    "error",
                    "JSON input must not contain NaN, Infinity, or -Infinity.",
                    "$",
                    details,
                )
            ],
            source,
        )
    except json.JSONDecodeError as exc:
        details: dict[str, Any] = {"line": exc.lineno, "column": exc.colno}
        if input_json_path is not None:
            details["path"] = input_json_path
        return ParsedJsonInput(
            None,
            [
                ServiceDiagnostic(
                    "PG.SERVICE.MALFORMED_JSON",
                    "error",
                    "JSON input is not valid JSON.",
                    "$",
                    details,
                )
            ],
            source,
        )


def _reject_non_finite_constant(constant: str) -> None:
    raise _NonFiniteJsonConstant(constant)
