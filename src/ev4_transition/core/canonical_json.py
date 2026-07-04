from __future__ import annotations

from pathlib import Path

from ..canonical_json import (
    CANONICAL_JSON_VERSION,
    CanonicalJsonError,
    bytes_sha256,
    canonical_bytes,
    canonical_dumps,
    canonical_sha256,
    load_json_file,
    write_canonical_json,
)


def file_sha256(path: str | Path) -> str:
    """Compute SHA-256 over exact file bytes without text decoding or normalization."""

    return bytes_sha256(Path(path).read_bytes())


__all__ = [
    "CANONICAL_JSON_VERSION",
    "CanonicalJsonError",
    "bytes_sha256",
    "canonical_bytes",
    "canonical_dumps",
    "canonical_sha256",
    "file_sha256",
    "load_json_file",
    "write_canonical_json",
]
