from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from typing import Any

from ev4_transition.canonical_json import canonical_sha256, write_canonical_json

from .records import ToolExecutionOutcome
from .subprocess_runner import execute_official_tool
from .official_tools import _deterministic_env


def execute_responsive_input_boundary_validator(
    *,
    repo_root: str | Path,
    owner_repo: str,
    owner_commit: str,
    validator_path: str,
    responsive_input: dict[str, Any],
    timeout_seconds: float = 30,
    progress_sink: list[dict[str, Any]] | None = None,
) -> ToolExecutionOutcome:
    root = Path(repo_root).resolve()
    with tempfile.TemporaryDirectory(prefix="ev4-pg-responsive-input-") as td:
        payload_path = Path(td) / "builder-responsive-input.json"
        write_canonical_json(payload_path, responsive_input)
        return execute_official_tool(
            tool_kind="validator",
            owner_repo=owner_repo,
            owner_commit=owner_commit,
            tool_path=validator_path,
            command=[sys.executable, str(root / validator_path), str(payload_path)],
            working_directory=root,
            timeout_seconds=timeout_seconds,
            input_ref="builder-responsive-input.json",
            input_hash=canonical_sha256(responsive_input),
            parsed_result_ref="stdout:text",
            progress_sink=progress_sink,
            env=_deterministic_env(root),
        )


def execute_responsive_output_validator(
    *,
    repo_root: str | Path,
    owner_repo: str,
    owner_commit: str,
    validator_path: str,
    responsive_output: dict[str, Any],
    timeout_seconds: float = 30,
    progress_sink: list[dict[str, Any]] | None = None,
) -> ToolExecutionOutcome:
    root = Path(repo_root).resolve()
    with tempfile.TemporaryDirectory(prefix="ev4-pg-responsive-output-") as td:
        payload_path = Path(td) / "responsive-output.json"
        write_canonical_json(payload_path, responsive_output)
        return execute_official_tool(
            tool_kind="validator",
            owner_repo=owner_repo,
            owner_commit=owner_commit,
            tool_path=validator_path,
            command=[sys.executable, str(root / validator_path), str(payload_path)],
            working_directory=root,
            timeout_seconds=timeout_seconds,
            input_ref="responsive-output.json",
            input_hash=canonical_sha256(responsive_output),
            parsed_result_ref="stdout:text",
            progress_sink=progress_sink,
            env=_deterministic_env(root),
        )
