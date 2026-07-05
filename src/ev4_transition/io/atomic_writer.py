from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from ev4_transition.canonical_json import bytes_sha256, canonical_dumps

Validator = Callable[[Path], None]


class AtomicWriteError(OSError):
    """Raised when an atomic output write cannot be completed safely."""


@dataclass(frozen=True)
class AtomicWriteResult:
    final_path: Path
    success: bool
    final_path_exists: bool
    bytes_written: int
    sha256: str | None
    download_available: bool
    error: str | None = None


def atomic_write_bytes(final_path: str | Path, content: bytes, *, validate: Validator | None = None) -> AtomicWriteResult:
    """Write bytes through temp-file + flush/fsync + validate + atomic replace.

    Success is returned only after the final path exists. On failure an
    AtomicWriteError is raised and any temporary file is best-effort removed.
    """

    destination = Path(final_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, dir=destination.parent, prefix=f".{destination.name}.", suffix=".tmp") as handle:
            tmp_name = handle.name
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        tmp_path = Path(tmp_name)
        if validate is not None:
            validate(tmp_path)
        os.replace(tmp_path, destination)
        _fsync_directory_best_effort(destination.parent)
        if not destination.exists():
            raise AtomicWriteError(f"Atomic write finished but final path does not exist: {destination}")
        return AtomicWriteResult(
            final_path=destination,
            success=True,
            final_path_exists=True,
            bytes_written=len(content),
            sha256=bytes_sha256(content),
            download_available=True,
        )
    except Exception as exc:
        if tmp_name:
            try:
                Path(tmp_name).unlink(missing_ok=True)
            except OSError:
                pass
        if isinstance(exc, AtomicWriteError):
            raise
        raise AtomicWriteError(str(exc)) from exc


def atomic_write_text(final_path: str | Path, content: str, *, validate: Validator | None = None) -> AtomicWriteResult:
    return atomic_write_bytes(final_path, content.encode("utf-8"), validate=validate)


def atomic_write_canonical_json(final_path: str | Path, payload: object) -> AtomicWriteResult:
    content = canonical_dumps(payload) + "\n"

    def _validate_json(path: Path) -> None:
        import json

        json.loads(path.read_text(encoding="utf-8"))

    return atomic_write_text(final_path, content, validate=_validate_json)


def try_atomic_write_text(final_path: str | Path, content: str, *, validate: Validator | None = None) -> AtomicWriteResult:
    destination = Path(final_path)
    try:
        return atomic_write_text(destination, content, validate=validate)
    except AtomicWriteError as exc:
        return AtomicWriteResult(
            final_path=destination,
            success=False,
            final_path_exists=destination.exists(),
            bytes_written=0,
            sha256=None,
            download_available=False,
            error=str(exc),
        )


def _fsync_directory_best_effort(directory: Path) -> None:
    if os.name == "nt":
        return
    try:
        fd = _open_directory_fd(directory)
    except OSError:
        return
    try:
        os.fsync(fd)
    except OSError:
        pass
    finally:
        os.close(fd)


def _open_directory_fd(directory: Path) -> int:
    return os.open(directory, os.O_RDONLY)
