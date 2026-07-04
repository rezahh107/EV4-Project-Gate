from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

CANONICAL_JSON_VERSION = "ev4-canonical-json.v1"


class CanonicalJsonError(ValueError):
    """Raised when a value cannot be represented as deterministic JSON."""


def _reject_non_finite(value: Any, path: str = "$") -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise CanonicalJsonError(f"Non-finite float is not allowed at {path}.")
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str):
                raise CanonicalJsonError(f"JSON object key must be a string at {path}.")
            _reject_non_finite(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_non_finite(child, f"{path}[{index}]")


def canonical_dumps(value: Any) -> str:
    """Serialize JSON-compatible data using EV4 canonical JSON v1.

    Behavior:
    - UTF-8 text, returned as Python str before byte encoding.
    - deterministic lexicographic key ordering.
    - compact separators with no insignificant whitespace.
    - non-ASCII characters preserved, not escaped.
    - NaN and infinity rejected.
    - no Unicode normalization is applied before serialization.
    """

    _reject_non_finite(value)
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise CanonicalJsonError(str(exc)) from exc


def canonical_bytes(value: Any) -> bytes:
    return canonical_dumps(value).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def bytes_sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def file_sha256(path: str | Path) -> str:
    """Compute SHA-256 over exact file bytes without decoding or normalization."""

    return bytes_sha256(Path(path).read_bytes())


def load_json_file(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_canonical_json(path: str | Path, value: Any) -> None:
    Path(path).write_text(canonical_dumps(value) + "\n", encoding="utf-8")
