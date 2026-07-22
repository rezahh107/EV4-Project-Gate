from __future__ import annotations

import os
import json
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
import tempfile
from typing import Any
from urllib.parse import urlparse

_PATH_ERRORS = (OSError, ValueError, RuntimeError)
_DEFAULT_OUTPUT_ROOT = Path("outputs") / "runs"
_REPORT_FILENAMES = ("result.json", "report.md", "report.html")


@dataclass(frozen=True)
class AttemptPaths:
    output_root: Path
    execution_directory: Path
    result: Path
    report_markdown: Path
    report_html: Path

    def report_paths(self) -> tuple[Path, ...]:
        return (self.result, self.report_markdown, self.report_html)


@dataclass(frozen=True)
class PublicationPaths(AttemptPaths):
    downstream_artifact: Path
    receipt: Path

    def all_paths(self) -> tuple[Path, ...]:
        return (
            self.downstream_artifact,
            self.receipt,
            self.result,
            self.report_markdown,
            self.report_html,
        )


class PublicationPathError(ValueError):
    def __init__(self, diagnostic: dict[str, Any]) -> None:
        super().__init__(str(diagnostic.get("message", "Publication path validation failed.")))
        self.diagnostic = diagnostic


def looks_like_url(value: str) -> bool:
    lowered = value.lower()
    if lowered.startswith(("git@", "github.com/", "www.github.com/")):
        return True
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    return bool(parsed.scheme and parsed.netloc)


def is_absolute_path_for_platform(value: str, platform: str | None = None) -> bool:
    platform_name = os.name if platform is None else platform
    if platform_name == "nt":
        return PureWindowsPath(value).is_absolute()
    return Path(value).is_absolute()


def validate_repository_checkout(
    field: str,
    value: str | Path | None,
    *,
    workspace: str | Path | None = None,
) -> tuple[Path | None, list[dict[str, Any]]]:
    path_expr = f"$.repository_paths.{field}"
    if value is None or not str(value).strip():
        return None, [
            _diag(
                "PG_INT_REPOSITORY_PATH_REQUIRED",
                "insufficient_evidence",
                path_expr,
                "A required local repository checkout path is missing.",
                field=field,
            )
        ]
    raw = str(value).strip()
    if looks_like_url(raw):
        return None, [
            _diag(
                "PG_INT_GITHUB_URL_REJECTED",
                "error",
                path_expr,
                "A local checkout directory is required; repository URLs are not accepted.",
                field=field,
            )
        ]
    try:
        base = Path.cwd() if workspace is None else Path(workspace)
        candidate = Path(raw).expanduser()
        if not candidate.is_absolute():
            candidate = base / candidate
        candidate = candidate.resolve(strict=False)
        if not candidate.exists():
            return None, [
                _diag(
                    "PG_INT_REPOSITORY_PATH_NOT_FOUND",
                    "insufficient_evidence",
                    path_expr,
                    "The required local repository checkout does not exist.",
                    field=field,
                    observed_path=str(candidate),
                )
            ]
        if not candidate.is_dir():
            return None, [
                _diag(
                    "PG_INT_REPOSITORY_PATH_UNSAFE",
                    "error",
                    path_expr,
                    "The required local repository checkout path is not a directory.",
                    field=field,
                    observed_path=str(candidate),
                )
            ]
        candidate.stat()
        next(candidate.iterdir(), None)
    except _PATH_ERRORS as exc:
        return None, [
            _diag(
                "PG_INT_REPOSITORY_PATH_UNSAFE",
                "error",
                path_expr,
                "The required local repository checkout path is invalid or inaccessible.",
                field=field,
                error_type=type(exc).__name__,
            )
        ]
    return candidate, []


def validate_project_gate_root(
    value: str | Path | None,
    *,
    required_files: tuple[str, ...],
    workspace: str | Path | None = None,
) -> tuple[Path | None, list[dict[str, Any]]]:
    raw = str(value or ".").strip()
    if looks_like_url(raw):
        return None, [
            _diag(
                "PG_INT_PROJECT_GATE_REPO_INVALID",
                "error",
                "$.project_gate_repo",
                "The Project Gate repository root must be a local directory.",
                project_gate_repo=raw,
                error_type="UrlPath",
            )
        ]
    try:
        base = Path.cwd() if workspace is None else Path(workspace)
        root = Path(raw).expanduser()
        if not root.is_absolute():
            root = base / root
        root = root.resolve(strict=False)
    except _PATH_ERRORS as exc:
        return None, [
            _diag(
                "PG_INT_PATH_EXPANSION_FAILED",
                "error",
                "$.project_gate_repo",
                "The Project Gate repository path could not be expanded safely.",
                project_gate_repo=raw,
                error_type=type(exc).__name__,
            )
        ]
    try:
        if not root.exists() or not root.is_dir():
            raise NotADirectoryError(str(root))
        root.stat()
        next(root.iterdir(), None)
    except _PATH_ERRORS as exc:
        return None, [
            _diag(
                "PG_INT_PROJECT_GATE_REPO_INVALID",
                "error",
                "$.project_gate_repo",
                "The Project Gate repository root does not exist, is not a directory, or is inaccessible.",
                project_gate_repo=str(root),
                error_type=type(exc).__name__,
            )
        ]
    for relative in required_files:
        candidate = root / relative
        try:
            if not candidate.is_file():
                raise FileNotFoundError(relative)
            json.loads(candidate.read_text(encoding="utf-8"), parse_constant=_reject_json_constant)
        except Exception as exc:
            return None, [
                _diag(
                    "PG_INT_PROJECT_GATE_FILES_UNAVAILABLE",
                    "error",
                    "$.project_gate_repo.routing_files",
                    "A required Project Gate file is missing, unreadable, or malformed.",
                    file=relative,
                    error_type=type(exc).__name__,
                    project_gate_repo=str(root),
                )
            ]
    return root, []


def validate_publication_root(
    value: str | Path | None,
    *,
    create: bool,
    workspace: str | Path | None = None,
) -> tuple[Path | None, dict[str, Any] | None]:
    raw = str(value).strip() if value is not None and str(value).strip() else str(_DEFAULT_OUTPUT_ROOT)
    if looks_like_url(raw):
        return None, _diag(
            "PG_INT_OUTPUT_DIRECTORY_URL_REJECTED",
            "error",
            "$.output_dir",
            "The output root must be a local filesystem directory, not a URL.",
            output_dir=raw,
        )
    if os.name != "nt" and PureWindowsPath(raw).is_absolute():
        return None, _diag(
            "PG_INT_OUTPUT_DIRECTORY_PLATFORM_MISMATCH",
            "error",
            "$.output_dir",
            "A Windows absolute output path can only be validated on Windows.",
            output_dir=raw,
            current_platform=os.name,
        )
    try:
        base = Path.cwd() if workspace is None else Path(workspace)
        root = Path(raw).expanduser()
        if not root.is_absolute():
            root = base / root
        root = root.resolve(strict=False)
        if root.exists() and not root.is_dir():
            raise NotADirectoryError(str(root))
        parent = _nearest_existing_parent(root)
        if not parent.is_dir():
            raise NotADirectoryError(str(parent))
        parent.stat()
        next(parent.iterdir(), None)
        if not os.access(parent, os.W_OK | os.X_OK):
            raise PermissionError(str(parent))
        if create:
            root.mkdir(parents=True, exist_ok=True)
            if not root.is_dir():
                raise NotADirectoryError(str(root))
            if not os.access(root, os.W_OK | os.X_OK):
                raise PermissionError(str(root))
    except _PATH_ERRORS as exc:
        return None, _diag(
            "PG_INT_OUTPUT_DIRECTORY_UNAVAILABLE",
            "error",
            "$.output_dir",
            "The selected output root is not a usable local directory.",
            output_dir=raw,
            error_type=type(exc).__name__,
        )
    return root, None


def prepare_attempt_paths(
    output_root: str | Path | None,
    *,
    workspace: str | Path | None = None,
) -> AttemptPaths:
    root, diagnostic = validate_publication_root(output_root, create=True, workspace=workspace)
    if diagnostic is not None or root is None:
        raise PublicationPathError(diagnostic or _diag(
            "PG_INT_OUTPUT_DIRECTORY_UNAVAILABLE",
            "error",
            "$.output_dir",
            "The selected output root is unavailable.",
        ))
    try:
        execution = Path(tempfile.mkdtemp(prefix="run-", dir=root)).resolve(strict=True)
        paths = AttemptPaths(
            output_root=root,
            execution_directory=execution,
            result=_safe_child(execution, _REPORT_FILENAMES[0], "$.result_path"),
            report_markdown=_safe_child(execution, _REPORT_FILENAMES[1], "$.report_markdown_path"),
            report_html=_safe_child(execution, _REPORT_FILENAMES[2], "$.report_html_path"),
        )
    except _PATH_ERRORS as exc:
        raise PublicationPathError(
            _diag(
                "PG_INT_OUTPUT_DIRECTORY_UNAVAILABLE",
                "error",
                "$.output_dir",
                "A collision-safe execution directory could not be created under the selected output root.",
                output_dir=str(root),
                error_type=type(exc).__name__,
            )
        ) from exc
    _assert_attempt_children(paths.execution_directory, paths.report_paths())
    return paths


def prepare_publication_paths(
    output_root: str | Path | None,
    *,
    output_filename: str,
    receipt_filename: str,
    output_path: str | Path | None = None,
    receipt_path: str | Path | None = None,
    workspace: str | Path | None = None,
    attempt_paths: AttemptPaths | None = None,
) -> PublicationPaths:
    _require_route_owned_filename(output_path, output_filename, "$.output_path")
    _require_route_owned_filename(receipt_path, receipt_filename, "$.receipt_path")
    attempt = attempt_paths or prepare_attempt_paths(output_root, workspace=workspace)
    paths = PublicationPaths(
        output_root=attempt.output_root,
        execution_directory=attempt.execution_directory,
        result=attempt.result,
        report_markdown=attempt.report_markdown,
        report_html=attempt.report_html,
        downstream_artifact=_safe_child(attempt.execution_directory, output_filename, "$.output_path"),
        receipt=_safe_child(attempt.execution_directory, receipt_filename, "$.receipt_path"),
    )
    _assert_attempt_children(paths.execution_directory, paths.all_paths())
    return paths


def _assert_attempt_children(execution: Path, candidates: tuple[Path, ...]) -> None:
    for candidate in candidates:
        try:
            candidate.relative_to(execution)
        except ValueError as exc:
            raise PublicationPathError(
                _diag(
                    "PG_INT_PUBLICATION_PATH_ESCAPE",
                    "error",
                    "$.output_dir",
                    "A derived publication path escaped the execution directory.",
                    execution_directory=str(execution),
                    derived_path=str(candidate),
                )
            ) from exc


def _require_route_owned_filename(value: str | Path | None, expected: str, path_expr: str) -> None:
    if value is None or not str(value).strip():
        return
    raw = str(value).strip()
    path = Path(raw)
    if path.is_absolute() or len(path.parts) != 1 or path.name != expected:
        raise PublicationPathError(
            _diag(
                "PG_INT_ADVANCED_PUBLICATION_PATH_UNSUPPORTED",
                "error",
                path_expr,
                "Explicit publication paths must use the route-owned filename and may not select another directory.",
                expected_filename=expected,
                observed_value=raw,
            )
        )


def _safe_child(root: Path, filename: str, path_expr: str) -> Path:
    candidate = Path(filename)
    if candidate.is_absolute() or len(candidate.parts) != 1 or candidate.name in {"", ".", ".."}:
        raise PublicationPathError(
            _diag(
                "PG_INT_PUBLICATION_PATH_ESCAPE",
                "error",
                path_expr,
                "A publication filename must be a simple child filename.",
                observed_value=filename,
            )
        )
    return root / candidate.name


def _nearest_existing_parent(path: Path) -> Path:
    candidate = path
    while not candidate.exists() and candidate != candidate.parent:
        candidate = candidate.parent
    return candidate


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"Non-standard JSON constant is forbidden: {value}")


def _diag(code: str, severity: str, path: str, message: str, **details: Any) -> dict[str, Any]:
    return {
        "code": code,
        "severity": severity,
        "path": path,
        "message": message,
        "details": details,
    }
