from __future__ import annotations

import errno
import json
import os
import stat
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ev4_transition.canonical_json import bytes_sha256, canonical_dumps
from ev4_transition.verified_artifact import VerifiedArtifactSnapshot


class PublicationError(OSError):
    def __init__(self, code: str, message: str, **details: Any) -> None:
        self.code = code
        normalized = dict(details)
        if "path" in normalized:
            normalized["artifact_path"] = normalized.pop("path")
        self.details = normalized
        super().__init__(message)


@dataclass(frozen=True)
class StagedJson:
    temporary_path: Path
    final_path: Path
    content: bytes = field(repr=False)
    sha256: str
    verify_json: bool = True


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
        raise PublicationError(
            "PG_A2C_OUTPUT_PATH_COLLISION",
            "CE input and receipt paths must be different.",
        )
    if output == source or receipt == source:
        raise PublicationError(
            "PG_A2C_SOURCE_OUTPUT_COLLISION",
            "The source export path must not be reused as an output path.",
        )
    return output, receipt


def stage_canonical_json(final_path: str | Path, payload: Any) -> StagedJson:
    content = (canonical_dumps(payload) + "\n").encode("utf-8")
    return stage_exact_bytes(final_path, content, verify_json=True)


def stage_exact_text(final_path: str | Path, content: str) -> StagedJson:
    return stage_exact_bytes(final_path, content.encode("utf-8"), verify_json=False)


def stage_exact_bytes(
    final_path: str | Path,
    content: bytes,
    *,
    verify_json: bool = False,
) -> StagedJson:
    destination = Path(final_path)
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
    _verify_exact_bytes(temporary, content, verify_json=verify_json)
    return StagedJson(temporary, destination, content, bytes_sha256(content), verify_json)


def stage_verified_artifact_snapshot(
    final_path: str | Path,
    snapshot: VerifiedArtifactSnapshot,
) -> StagedJson:
    """Stage the exact verified bytes without reconstructing parsed JSON."""

    snapshot.validate_integrity()
    staged = stage_exact_bytes(final_path, snapshot.exact_bytes, verify_json=True)
    if staged.sha256 != snapshot.sha256:
        discard_staged_json(staged)
        raise PublicationError(
            "PG.RUNTIME.SNAPSHOT_STAGING_HASH_MISMATCH",
            "Staged bytes differ from the verified artifact snapshot hash.",
            path=str(final_path),
            expected=snapshot.sha256,
            actual=staged.sha256,
        )
    if len(staged.content) != snapshot.byte_length:
        discard_staged_json(staged)
        raise PublicationError(
            "PG.RUNTIME.SNAPSHOT_STAGING_LENGTH_MISMATCH",
            "Staged length differs from the verified artifact snapshot.",
            path=str(final_path),
            expected=snapshot.byte_length,
            actual=len(staged.content),
        )
    return staged


def verify_published_artifact_snapshot(
    destination: str | Path,
    snapshot: VerifiedArtifactSnapshot,
) -> dict[str, Any]:
    """Reread one published artifact and require exact snapshot byte identity."""

    snapshot.validate_integrity()
    path = Path(destination)
    observed = path.read_bytes()
    if observed != snapshot.exact_bytes:
        raise PublicationError(
            "PG.RUNTIME.SNAPSHOT_POST_WRITE_BYTES_MISMATCH",
            "Published bytes differ from the verified artifact snapshot.",
            path=str(path),
        )
    observed_hash = bytes_sha256(observed)
    if observed_hash != snapshot.sha256:
        raise PublicationError(
            "PG.RUNTIME.SNAPSHOT_POST_WRITE_HASH_MISMATCH",
            "Published SHA-256 differs from the verified artifact snapshot.",
            path=str(path),
            expected=snapshot.sha256,
            actual=observed_hash,
        )
    if len(observed) != snapshot.byte_length:
        raise PublicationError(
            "PG.RUNTIME.SNAPSHOT_POST_WRITE_LENGTH_MISMATCH",
            "Published byte length differs from the verified artifact snapshot.",
            path=str(path),
            expected=snapshot.byte_length,
            actual=len(observed),
        )
    return snapshot.metadata()


def publish_staged_json(staged: StagedJson) -> dict[str, Any]:
    destination = staged.final_path
    _assert_destination_unused(destination)
    try:
        os.link(staged.temporary_path, destination, follow_symlinks=False)
    except FileExistsError as exc:
        raise PublicationError(
            "PG_A2C_OUTPUT_CREATED_CONCURRENTLY",
            "An output target was created concurrently; overwrite is forbidden.",
            path=str(destination),
        ) from exc
    except OSError as exc:
        code = "PG_A2C_ATOMIC_PUBLICATION_UNAVAILABLE"
        if exc.errno == errno.EEXIST:
            code = "PG_A2C_OUTPUT_CREATED_CONCURRENTLY"
        raise PublicationError(
            code,
            "Atomic no-overwrite publication failed.",
            path=str(destination),
            error_type=type(exc).__name__,
            errno=exc.errno,
        ) from exc
    try:
        _fsync_directory(destination.parent)
        _verify_exact_bytes(
            destination,
            staged.content,
            verify_json=staged.verify_json,
        )
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


def publish_staged_group(staged_items: list[StagedJson]) -> list[dict[str, Any]]:
    """Commit a staged group or roll back every linked final artifact.

    Records are returned only after every final path is linked, directory state
    is synced, every final byte sequence is verified, and every temporary file
    is removed. Preflight destination failures also clean every staged file.
    """

    if not staged_items:
        return []

    published: list[Path] = []
    try:
        destinations = [item.final_path for item in staged_items]
        if len(set(destinations)) != len(destinations):
            raise PublicationError(
                "PG.REPORT.PUBLICATION_PATH_COLLISION",
                "Report artifact destinations must be distinct.",
            )
        for destination in destinations:
            _assert_destination_unused(destination)

        for staged in staged_items:
            try:
                os.link(
                    staged.temporary_path,
                    staged.final_path,
                    follow_symlinks=False,
                )
            except FileExistsError as exc:
                raise PublicationError(
                    "PG.REPORT.OUTPUT_CREATED_CONCURRENTLY",
                    "A report destination was created concurrently; overwrite is forbidden.",
                    path=str(staged.final_path),
                ) from exc
            except OSError as exc:
                raise PublicationError(
                    "PG.REPORT.ATOMIC_PUBLICATION_UNAVAILABLE",
                    "Atomic no-overwrite report publication failed.",
                    path=str(staged.final_path),
                    error_type=type(exc).__name__,
                    errno=exc.errno,
                ) from exc
            published.append(staged.final_path)

        for directory in sorted(
            {path.parent for path in published}, key=lambda item: str(item)
        ):
            _fsync_directory(directory)
        for staged in staged_items:
            _verify_exact_bytes(
                staged.final_path,
                staged.content,
                verify_json=staged.verify_json,
            )

        cleanup_errors = _cleanup_temporaries(staged_items)
        if cleanup_errors:
            raise PublicationError(
                "PG.REPORT.STAGING_CLEANUP_FAILED",
                "The publication group was linked but staged temporary files could not be removed.",
                cleanup_errors=cleanup_errors,
            )
    except Exception as exc:
        failure = _as_group_publication_error(exc)
        rollback_errors = _rollback_published(published)
        fsync_errors = _fsync_rollback_directories(published)
        cleanup_errors = _cleanup_temporaries(staged_items)
        persisted_paths = [str(path) for path in published if _lexists(path)]
        persisted_temporary_paths = [
            str(item.temporary_path)
            for item in staged_items
            if _lexists(item.temporary_path)
        ]
        failure.details.update(
            {
                "rollback_errors": rollback_errors,
                "rollback_fsync_errors": fsync_errors,
                "cleanup_errors": cleanup_errors,
                "persisted_paths": persisted_paths,
                "persisted_temporary_paths": persisted_temporary_paths,
                "rollback_complete": not persisted_paths
                and not persisted_temporary_paths,
            }
        )
        raise failure from exc

    return [
        {
            "artifact_name": staged.final_path.name,
            "path": str(staged.final_path),
            "state": "published_verified",
            "sha256_file_bytes": staged.sha256,
            "bytes": len(staged.content),
            "verification": "exact_bytes_verified",
        }
        for staged in staged_items
    ]


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


def _rollback_published(published: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in reversed(published):
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            errors.append(f"{path}:{type(exc).__name__}:{exc}")
    return errors


def _cleanup_temporaries(staged_items: list[StagedJson]) -> list[str]:
    errors: list[str] = []
    for staged in staged_items:
        try:
            staged.temporary_path.unlink(missing_ok=True)
        except OSError as exc:
            errors.append(f"{staged.temporary_path}:{type(exc).__name__}:{exc}")
    return errors


def _fsync_rollback_directories(published: list[Path]) -> list[str]:
    errors: list[str] = []
    for directory in sorted(
        {path.parent for path in published}, key=lambda item: str(item)
    ):
        try:
            _fsync_directory(directory)
        except OSError as exc:
            errors.append(f"{directory}:{type(exc).__name__}:{exc}")
    return errors


def _as_group_publication_error(exc: Exception) -> PublicationError:
    if isinstance(exc, PublicationError):
        return exc
    return PublicationError(
        "PG.REPORT.POST_WRITE_VALIDATION_FAILED",
        "The publication group failed verification and was rolled back.",
        error_type=type(exc).__name__,
    )


def _lexists(path: Path) -> bool:
    try:
        path.lstat()
    except FileNotFoundError:
        return False
    except OSError:
        return True
    return True


def _safe_destination(raw_path: str | Path, base: Path) -> Path:
    raw = Path(raw_path)
    if any(part == ".." for part in raw.parts):
        raise PublicationError(
            "PG_A2C_PATH_TRAVERSAL_FORBIDDEN",
            "Output paths must not contain parent traversal segments.",
            path=str(raw),
        )
    candidate = raw if raw.is_absolute() else base / raw
    _assert_destination_unused(candidate)
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(base)
    except ValueError as exc:
        raise PublicationError(
            "PG_A2C_OUTPUT_OUTSIDE_WORKSPACE",
            "Output paths must remain inside the current workspace.",
            path=str(raw),
        ) from exc
    parent = resolved.parent
    if not parent.exists() or not parent.is_dir():
        raise PublicationError(
            "PG_A2C_OUTPUT_PARENT_INVALID",
            "The output parent directory must already exist.",
            path=str(parent),
        )
    _assert_no_symlink_component(parent, base)
    _assert_destination_unused(resolved)
    return resolved


def _assert_no_symlink_component(path: Path, base: Path) -> None:
    current = base
    if stat.S_ISLNK(base.lstat().st_mode):
        raise PublicationError(
            "PG_A2C_OUTPUT_PARENT_SYMLINK_FORBIDDEN",
            "The workspace root must not be a symbolic link.",
            path=str(base),
        )
    for part in path.relative_to(base).parts:
        current = current / part
        if stat.S_ISLNK(current.lstat().st_mode):
            raise PublicationError(
                "PG_A2C_OUTPUT_PARENT_SYMLINK_FORBIDDEN",
                "Output parent directories must not be symbolic links.",
                path=str(current),
            )


def _assert_destination_unused(path: Path) -> None:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return
    if stat.S_ISDIR(info.st_mode):
        raise PublicationError(
            "PG_A2C_OUTPUT_IS_DIRECTORY",
            "An output path refers to a directory.",
            path=str(path),
        )
    if stat.S_ISLNK(info.st_mode):
        raise PublicationError(
            "PG_A2C_OUTPUT_SYMLINK_FORBIDDEN",
            "An output path must not be a symbolic link.",
            path=str(path),
        )
    raise PublicationError(
        "PG_A2C_OUTPUT_EXISTS",
        "An output file already exists; overwrite is forbidden.",
        path=str(path),
    )


def _verify_exact_json_bytes(path: Path, expected: bytes) -> None:
    _verify_exact_bytes(path, expected, verify_json=True)


def _verify_exact_bytes(path: Path, expected: bytes, *, verify_json: bool) -> None:
    observed = path.read_bytes()
    if observed != expected:
        raise PublicationError(
            "PG_A2C_PUBLISHED_BYTES_MISMATCH",
            "Artifact bytes differ from the staged bytes.",
            path=str(path),
        )
    if verify_json:
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
