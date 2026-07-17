from __future__ import annotations

import errno
import json
import os
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ev4_transition.canonical_json import bytes_sha256, canonical_dumps


class PublicationError(OSError):
    def __init__(self, code: str, message: str, **details: Any) -> None:
        self.code = code
        self.details = details
        super().__init__(message)


@dataclass(frozen=True)
class StagedJson:
    temporary_path: Path
    final_path: Path
    content: bytes
    sha256: str


def resolve_publication_paths(
    *,
    source_path: str | Path,
    output_path: str | Path,
    receipt_path: str | Path,
    base_directory: str | Path | None = None,
) -> tuple[Path, Path]:
    base = Path(base_directory or Path.cwd()).resolve()
    source = Path(source_path).resolve(strict=True)
    output = _safe_destination(output_path, base)
    receipt = _safe_destination(receipt_path, base)
    if output == receipt:
        raise PublicationError("PG_A2C_OUTPUT_PATH_COLLISION", "CE input and receipt paths must be different.")
    if output == source or receipt == source:
        raise PublicationError("PG_A2C_SOURCE_OUTPUT_COLLISION", "The source export path must not be reused as an output path.")
    return output, receipt


def stage_canonical_json(final_path: str | Path, payload: Any) -> StagedJson:
    destination = Path(final_path)
    content = (canonical_dumps(payload) + "\n").encode("utf-8")
    handle = tempfile.NamedTemporaryFile(
        mode="wb",
        delete=False,
        dir=destination.parent,
        prefix=f".{destination.name}.",
        suffix=".tmp",
    )
    temporary = Path(handle.name)
    try:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    except Exception:
        handle.close()
        temporary.unlink(missing_ok=True)
        raise
    finally:
        if not handle.closed:
            handle.close()
    _verify_exact_json_bytes(temporary, content)
    return StagedJson(temporary, destination, content, bytes_sha256(content))


def publish_staged_json(staged: StagedJson) -> dict[str, Any]:
    destination = staged.final_path
    _assert_destination_unused(destination)
    try:
        os.link(staged.temporary_path, destination, follow_symlinks=False)
    except FileExistsError as exc:
        raise PublicationError("PG_A2C_OUTPUT_CREATED_CONCURRENTLY", "An output target was created concurrently; overwrite is forbidden.", path=str(destination)) from exc
    except OSError as exc:
        code = "PG_A2C_ATOMIC_PUBLICATION_UNAVAILABLE"
        if exc.errno == errno.EEXIST:
            code = "PG_A2C_OUTPUT_CREATED_CONCURRENTLY"
        raise PublicationError(code, "Atomic no-overwrite publication failed.", path=str(destination), error_type=type(exc).__name__, errno=exc.errno) from exc
    try:
        _fsync_directory(destination.parent)
        _verify_exact_json_bytes(destination, staged.content)
    except Exception as exc:
        raise PublicationError(
            "PG_A2C_POST_WRITE_VALIDATION_FAILED",
            "Published artifact bytes failed post-write verification.",
            path=str(destination),
            persisted=True,
            error_type=type(exc).__name__,
        ) from exc
    finally:
        try:
            staged.temporary_path.unlink(missing_ok=True)
        except OSError:
            pass
    return {
        "path": str(destination),
        "state": "published_verified",
        "sha256_file_bytes": staged.sha256,
        "bytes": len(staged.content),
    }


def discard_staged_json(staged: StagedJson | None) -> None:
    if staged is None:
        return
    try:
        staged.temporary_path.unlink(missing_ok=True)
    except OSError as exc:
        raise PublicationError(
            "PG_A2C_STAGING_CLEANUP_FAILED",
            "A staged temporary artifact could not be removed.",
            path=str(staged.temporary_path),
            error_type=type(exc).__name__,
        ) from exc


def _safe_destination(raw_path: str | Path, base: Path) -> Path:
    raw = Path(raw_path)
    if any(part == ".." for part in raw.parts):
        raise PublicationError("PG_A2C_PATH_TRAVERSAL_FORBIDDEN", "Output paths must not contain parent traversal segments.", path=str(raw))
    candidate = raw if raw.is_absolute() else base / raw
    _assert_destination_unused(candidate)
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(base)
    except ValueError as exc:
        raise PublicationError("PG_A2C_OUTPUT_OUTSIDE_WORKSPACE", "Output paths must remain inside the current workspace.", path=str(raw)) from exc
    parent = resolved.parent
    if not parent.exists() or not parent.is_dir():
        raise PublicationError("PG_A2C_OUTPUT_PARENT_INVALID", "The output parent directory must already exist.", path=str(parent))
    _assert_no_symlink_component(parent, base)
    _assert_destination_unused(resolved)
    return resolved


def _assert_no_symlink_component(path: Path, base: Path) -> None:
    current = base
    if stat.S_ISLNK(base.lstat().st_mode):
        raise PublicationError("PG_A2C_OUTPUT_PARENT_SYMLINK_FORBIDDEN", "The workspace root must not be a symbolic link.", path=str(base))
    for part in path.relative_to(base).parts:
        current = current / part
        if stat.S_ISLNK(current.lstat().st_mode):
            raise PublicationError("PG_A2C_OUTPUT_PARENT_SYMLINK_FORBIDDEN", "Output parent directories must not be symbolic links.", path=str(current))


def _assert_destination_unused(path: Path) -> None:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return
    if stat.S_ISDIR(info.st_mode):
        raise PublicationError("PG_A2C_OUTPUT_IS_DIRECTORY", "An output path refers to a directory.", path=str(path))
    if stat.S_ISLNK(info.st_mode):
        raise PublicationError("PG_A2C_OUTPUT_SYMLINK_FORBIDDEN", "An output path must not be a symbolic link.", path=str(path))
    raise PublicationError("PG_A2C_OUTPUT_EXISTS", "An output file already exists; overwrite is forbidden.", path=str(path))


def _verify_exact_json_bytes(path: Path, expected: bytes) -> None:
    observed = path.read_bytes()
    if observed != expected:
        raise PublicationError("PG_A2C_PUBLISHED_BYTES_MISMATCH", "Artifact bytes differ from the staged canonical bytes.", path=str(path))
    json.loads(observed.decode("utf-8"), parse_constant=_reject_json_constant)


def _reject_json_constant(value: str) -> Any:
    raise ValueError(f"Non-finite JSON constant is forbidden: {value}")


def _fsync_directory(directory: Path) -> None:
    if os.name == "nt":
        return
    fd = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
