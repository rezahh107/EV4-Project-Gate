from __future__ import annotations

from pathlib import Path
from typing import Any

from .diagnostics import Diagnostic
from .external_lock import ARCHITECT_REPO, ARCHITECT_RUNTIME_COMMIT, CE_COMMIT, CE_REPO
from .runners import diagnostics_from_outcome, execute_validator
from .runners.records import ToolExecutionOutcome


def execute_architect_validator(
    repo_root: str | Path,
    payload: dict[str, Any],
    *,
    progress_sink: list[dict[str, Any]] | None = None,
) -> ToolExecutionOutcome:
    return execute_validator(
        repo_root=repo_root,
        owner_repo=ARCHITECT_REPO,
        owner_commit=ARCHITECT_RUNTIME_COMMIT,
        validator_path="scripts/check-architect-stage-payload.py",
        payload=payload,
        progress_sink=progress_sink,
    )


def run_architect_validator(repo_root: str | Path, payload: dict[str, Any]) -> list[Diagnostic]:
    return diagnostics_from_outcome(execute_architect_validator(repo_root, payload))


def execute_ce_validator(
    repo_root: str | Path,
    payload: dict[str, Any],
    source_bundle: dict[str, Any],
    *,
    progress_sink: list[dict[str, Any]] | None = None,
) -> ToolExecutionOutcome:
    return execute_validator(
        repo_root=repo_root,
        owner_repo=CE_REPO,
        owner_commit=CE_COMMIT,
        validator_path="scripts/validate-ce-architect-stage-intake.py",
        payload=payload,
        source_bundle=source_bundle,
        progress_sink=progress_sink,
    )


def run_ce_validator(repo_root: str | Path, payload: dict[str, Any], source_bundle: dict[str, Any]) -> list[Diagnostic]:
    return diagnostics_from_outcome(execute_ce_validator(repo_root, payload, source_bundle))
