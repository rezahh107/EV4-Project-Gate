from __future__ import annotations

import re
from pathlib import Path, PurePosixPath, PureWindowsPath

_WINDOWS_DRIVE = re.compile(r"^[A-Za-z]:")


class RepoPathError(ValueError):
    def __init__(self, code: str, raw_ref: object, message: str):
        super().__init__(message)
        self.code = code
        self.raw_ref = raw_ref


def normalize_repo_relative_ref(raw: str, *, allow_root: bool = False) -> str:
    """Return one canonical POSIX repository-relative reference.

    Invalid references are rejected rather than rewritten into a different
    identity. The only directory-root spelling accepted is ``.`` when
    ``allow_root`` is true.
    """

    if not isinstance(raw, str) or not raw:
        raise RepoPathError("PG.RUNTIME.REF_REQUIRED", raw, "Repository-relative reference is required.")
    if raw != raw.strip() or "\x00" in raw:
        raise RepoPathError("PG.RUNTIME.REF_INVALID", raw, "Repository-relative reference contains invalid characters.")
    if raw == ".":
        if allow_root:
            return raw
        raise RepoPathError("PG.RUNTIME.REF_ROOT_FORBIDDEN", raw, "Repository root is not a valid file reference.")
    if "\\" in raw or _WINDOWS_DRIVE.match(raw) or PureWindowsPath(raw).drive:
        raise RepoPathError("PG.RUNTIME.REF_WINDOWS_PATH_FORBIDDEN", raw, "References must use POSIX '/' separators and cannot be drive-qualified.")
    if raw.startswith("/") or PurePosixPath(raw).is_absolute():
        raise RepoPathError("PG.RUNTIME.REF_ABSOLUTE_FORBIDDEN", raw, "Absolute repository references are forbidden.")
    if raw.endswith("/") or "//" in raw:
        raise RepoPathError("PG.RUNTIME.REF_NON_CANONICAL", raw, "Repository reference is not canonical.")

    path = PurePosixPath(raw)
    if any(part in {"", ".", ".."} for part in path.parts):
        raise RepoPathError("PG.RUNTIME.REF_TRAVERSAL_FORBIDDEN", raw, "Repository reference cannot contain '.' or '..' components.")
    normalized = path.as_posix()
    if normalized != raw:
        raise RepoPathError("PG.RUNTIME.REF_NON_CANONICAL", raw, "Repository reference would change during normalization.")
    return normalized


def resolve_repo_relative_file(root: str | Path, ref: str) -> Path:
    return _resolve(root, ref, expected="file")


def resolve_repo_relative_directory(root: str | Path, ref: str) -> Path:
    return _resolve(root, ref, expected="directory", allow_root=True)


def repo_relative_ref(path: str | Path, root: str | Path, *, require_exists: bool = True) -> str:
    resolved_root = Path(root).resolve(strict=True)
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = resolved_root / candidate
    _reject_symlink_components(resolved_root, candidate, allow_missing=not require_exists)
    resolved = candidate.resolve(strict=require_exists)
    try:
        relative = resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise RepoPathError("PG.RUNTIME.REF_OUTSIDE_REPOSITORY", str(path), "Path is outside the repository root.") from exc
    raw = relative.as_posix() if relative.parts else "."
    return normalize_repo_relative_ref(raw, allow_root=True)


def _resolve(root: str | Path, ref: str, *, expected: str, allow_root: bool = False) -> Path:
    normalized = normalize_repo_relative_ref(ref, allow_root=allow_root)
    resolved_root = Path(root).resolve(strict=True)
    candidate = resolved_root if normalized == "." else resolved_root.joinpath(*PurePosixPath(normalized).parts)
    _reject_symlink_components(resolved_root, candidate, allow_missing=False)
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(resolved_root)
    except FileNotFoundError as exc:
        raise RepoPathError("PG.RUNTIME.REF_MISSING", ref, "Repository reference does not exist.") from exc
    except (OSError, RuntimeError, ValueError) as exc:
        raise RepoPathError("PG.RUNTIME.REF_OUTSIDE_REPOSITORY", ref, "Repository reference cannot be resolved safely inside the repository.") from exc

    if expected == "file" and (not resolved.is_file() or resolved.is_symlink()):
        raise RepoPathError("PG.RUNTIME.REF_FILE_REQUIRED", ref, "Repository reference must identify a regular non-symlink file.")
    if expected == "directory" and (not resolved.is_dir() or resolved.is_symlink()):
        raise RepoPathError("PG.RUNTIME.REF_DIRECTORY_REQUIRED", ref, "Repository reference must identify a non-symlink directory.")
    return resolved


def _reject_symlink_components(root: Path, candidate: Path, *, allow_missing: bool) -> None:
    try:
        relative = candidate.relative_to(root)
    except ValueError as exc:
        raise RepoPathError("PG.RUNTIME.REF_OUTSIDE_REPOSITORY", str(candidate), "Path is outside the repository root.") from exc

    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise RepoPathError("PG.RUNTIME.REF_SYMLINK_FORBIDDEN", str(candidate), "Symlink components are forbidden for runtime references.")
        if not current.exists():
            if allow_missing:
                return
            raise RepoPathError("PG.RUNTIME.REF_MISSING", str(candidate), "Repository reference does not exist.")
