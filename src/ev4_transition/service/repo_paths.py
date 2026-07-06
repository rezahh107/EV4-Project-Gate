from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from .models import RepoPaths, ServiceDiagnostic


_REQUIRED_PATHS: dict[str, tuple[str, ...]] = {
    "validate_bundle": (),
    "inspect_capabilities": (),
    "architect_to_ce": ("architect_repo_path", "ce_repo_path"),
    "ce_to_builder": ("ce_repo_path", "builder_repo_path"),
    "builder_to_responsive": ("builder_repo_path", "responsive_repo_path"),
    "final_gate": ("project_gate_repo_path", "responsive_repo_path"),
}


def required_path_fields(transition_choice: str) -> tuple[str, ...]:
    return _REQUIRED_PATHS.get(transition_choice, ())


def validate_repo_paths(repo_paths: RepoPaths, transition_choice: str) -> list[ServiceDiagnostic]:
    diagnostics: list[ServiceDiagnostic] = []
    for field_name in required_path_fields(transition_choice):
        value = getattr(repo_paths, field_name)
        diagnostics.extend(_validate_single_required_path(field_name, value))
    return diagnostics


def _validate_single_required_path(field_name: str, value: str | None) -> list[ServiceDiagnostic]:
    path_expr = f"$.repo_paths.{field_name}"
    if value is None or not str(value).strip():
        return [
            ServiceDiagnostic(
                "PG.SERVICE.REPO_PATH_MISSING",
                "insufficient_evidence",
                _missing_message(field_name),
                path_expr,
                {"field": field_name},
            )
        ]
    if _looks_like_url(value):
        return [
            ServiceDiagnostic(
                "PG.SERVICE.REPO_PATH_NOT_LOCAL",
                "insufficient_evidence",
                "A local filesystem checkout path is required; GitHub URLs are not local repo paths.",
                path_expr,
                {"field": field_name, "observed": value},
            )
        ]
    try:
        path = Path(value).expanduser()
        exists = path.exists()
        is_directory = path.is_dir() if exists else False
    except (OSError, ValueError) as exc:
        return [
            ServiceDiagnostic(
                "PG.SERVICE.REPO_PATH_INACCESSIBLE",
                "insufficient_evidence",
                "Required local repository checkout path is invalid or inaccessible.",
                path_expr,
                {"field": field_name, "path": value, "error_type": type(exc).__name__},
            )
        ]
    if not exists:
        return [
            ServiceDiagnostic(
                "PG.SERVICE.REPO_PATH_DOES_NOT_EXIST",
                "insufficient_evidence",
                "Required local repository checkout path does not exist.",
                path_expr,
                {"field": field_name, "path": value},
            )
        ]
    if not is_directory:
        return [
            ServiceDiagnostic(
                "PG.SERVICE.REPO_PATH_NOT_DIRECTORY",
                "insufficient_evidence",
                "Required local repository checkout path must be a directory.",
                path_expr,
                {"field": field_name, "path": value},
            )
        ]
    return []


def resolve_project_gate_path(repo_paths: RepoPaths) -> Path:
    value = repo_paths.project_gate_repo_path or "."
    return Path(value).expanduser()


def resolve_relative_to_project_gate(repo_paths: RepoPaths, candidate: str) -> Path:
    path = Path(candidate).expanduser()
    if path.is_absolute():
        return path
    return resolve_project_gate_path(repo_paths) / path


def _looks_like_url(value: str) -> bool:
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    if parsed.scheme and parsed.netloc:
        return True
    lowered = value.lower()
    return lowered.startswith(("github.com/", "www.github.com/", "git@github.com:"))


def _missing_message(field_name: str) -> str:
    labels = {
        "architect_repo_path": "Architect local checkout path is required for this transition.",
        "ce_repo_path": "CE local checkout path is required for this transition.",
        "builder_repo_path": "Builder local checkout path is required for this transition.",
        "responsive_repo_path": "Responsive local checkout path is required for this transition.",
        "project_gate_repo_path": "Project Gate local checkout path is required for this gate.",
    }
    return labels.get(field_name, "Required local repository checkout path is missing.")
