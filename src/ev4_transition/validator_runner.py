from __future__ import annotations

from pathlib import Path
from typing import Any

from .diagnostics import Diagnostic, diagnostic
from .evidence_truth import synthetic_indicators
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


def run_ce_validator(
    repo_root: str | Path,
    payload: dict[str, Any],
    source_bundle: dict[str, Any],
    *,
    operational: bool = True,
) -> list[Diagnostic]:
    """Run the official CE validator and enforce operational evidence authority.

    ``operational=False`` is restricted to explicit fixture/contract validation. It
    still runs the official owner validator, but it cannot be used by service,
    CLI, producer dispatch, or publication paths to authorize a handoff.
    """

    diagnostics = diagnostics_from_outcome(execute_ce_validator(repo_root, payload, source_bundle))
    indicators = synthetic_indicators(source_bundle)
    if operational and indicators:
        diagnostics.append(
            diagnostic(
                "PG_A2C_SYNTHETIC_OPERATIONAL_HANDOFF_FORBIDDEN",
                "insufficient_evidence",
                "Runtime-derived synthetic evidence cannot authorize an operational Architect-to-CE handoff.",
                "$",
                classification="synthetic",
                synthetic_indicators=indicators,
            )
        )
    return diagnostics
