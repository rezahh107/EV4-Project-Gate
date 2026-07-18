from __future__ import annotations

import hashlib
import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class SnapshotError(OSError):
    def __init__(self, code: str, message: str, *, status: str = "invalid", **details: Any) -> None:
        self.code = code
        self.status = status
        self.details = details
        super().__init__(message)


@dataclass(frozen=True)
class JsonInputSnapshot:
    path: Path
    content: bytes
    sha256_file_bytes: str
    value: dict[str, Any]
    device: int
    inode: int
    size: int
    mtime_ns: int


def capture_json_snapshot(path: str | Path) -> JsonInputSnapshot:
    """Capture one stable, read-only JSON input and reject observable replacement races."""

    source = Path(path)
    try:
        initial_lstat = source.lstat()
    except OSError as exc:
        raise SnapshotError(
            "PG_A2C_INPUT_READ_FAILED",
            "The producer export could not be inspected.",
            status="insufficient_evidence",
            error_type=type(exc).__name__,
        ) from exc
    if stat.S_ISLNK(initial_lstat.st_mode):
        raise SnapshotError("PG_A2C_INPUT_SYMLINK_FORBIDDEN", "The producer export path must not be a symbolic link.")
    if not stat.S_ISREG(initial_lstat.st_mode):
        raise SnapshotError("PG_A2C_INPUT_NOT_REGULAR_FILE", "The producer export must be a regular file.")

    flags = os.O_RDONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(source, flags)
    except OSError as exc:
        raise SnapshotError(
            "PG_A2C_INPUT_OPEN_FAILED",
            "The producer export could not be opened without following links.",
            status="insufficient_evidence",
            error_type=type(exc).__name__,
        ) from exc

    try:
        before = os.fstat(fd)
        content = _read_all(fd)
        after = os.fstat(fd)
    finally:
        os.close(fd)

    if _identity(before) != _identity(after) or len(content) != after.st_size:
        raise SnapshotError("PG_A2C_INPUT_MUTATED_DURING_READ", "The producer export changed while it was being captured.")
    try:
        final_lstat = source.lstat()
    except OSError as exc:
        raise SnapshotError(
            "PG_A2C_INPUT_REPLACED_AFTER_READ",
            "The producer export path disappeared after capture.",
            error_type=type(exc).__name__,
        ) from exc
    if stat.S_ISLNK(final_lstat.st_mode) or _identity(final_lstat) != _identity(after):
        raise SnapshotError("PG_A2C_INPUT_REPLACED_AFTER_READ", "The producer export path was replaced during capture.")

    second = _read_path_without_following(source)
    if second != content:
        raise SnapshotError("PG_A2C_INPUT_REPEATED_READ_MISMATCH", "Repeated reads of the producer export returned different bytes.")

    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SnapshotError("PG_A2C_INPUT_NOT_UTF8", "The producer export is not valid UTF-8.") from exc
    try:
        value = json.loads(text, parse_constant=_reject_json_constant)
    except (json.JSONDecodeError, ValueError) as exc:
        details: dict[str, Any] = {"error_type": type(exc).__name__}
        if isinstance(exc, json.JSONDecodeError):
            details.update({"line": exc.lineno, "column": exc.colno})
        raise SnapshotError("MALFORMED_JSON", "The producer export is not valid strict JSON.", **details) from exc
    if not isinstance(value, dict):
        raise SnapshotError("PG_EXPORT_SCHEMA_INVALID", "The producer export root must be a JSON object.")

    resolved = source.resolve(strict=True)
    return JsonInputSnapshot(
        path=resolved,
        content=content,
        sha256_file_bytes=hashlib.sha256(content).hexdigest(),
        value=value,
        device=after.st_dev,
        inode=after.st_ino,
        size=after.st_size,
        mtime_ns=after.st_mtime_ns,
    )


def verify_snapshot_unchanged(snapshot: JsonInputSnapshot) -> None:
    """Reject path replacement or byte mutation before publication."""

    try:
        current_lstat = snapshot.path.lstat()
    except OSError as exc:
        raise SnapshotError(
            "PG_A2C_INPUT_REPLACED_BEFORE_PUBLICATION",
            "The producer export path is unavailable before publication.",
            error_type=type(exc).__name__,
        ) from exc
    if stat.S_ISLNK(current_lstat.st_mode):
        raise SnapshotError("PG_A2C_INPUT_SYMLINK_RETARGETED", "The producer export path became a symbolic link.")
    if _identity(current_lstat) != (snapshot.device, snapshot.inode, snapshot.size, snapshot.mtime_ns):
        raise SnapshotError("PG_A2C_INPUT_REPLACED_BEFORE_PUBLICATION", "The producer export identity changed before publication.")
    current = _read_path_without_following(snapshot.path)
    if current != snapshot.content:
        raise SnapshotError("PG_A2C_INPUT_MUTATED_BEFORE_PUBLICATION", "The producer export bytes changed before publication.")


def _read_path_without_following(path: Path) -> bytes:
    flags = os.O_RDONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise SnapshotError("PG_A2C_INPUT_REOPEN_FAILED", "The producer export could not be reopened safely.", error_type=type(exc).__name__) from exc
    try:
        return _read_all(fd)
    finally:
        os.close(fd)


def _read_all(fd: int) -> bytes:
    chunks: list[bytes] = []
    while True:
        chunk = os.read(fd, 1024 * 1024)
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)


def _identity(info: os.stat_result) -> tuple[int, int, int, int]:
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns


def _reject_json_constant(value: str) -> Any:
    raise ValueError(f"Non-finite JSON constant is forbidden: {value}")
