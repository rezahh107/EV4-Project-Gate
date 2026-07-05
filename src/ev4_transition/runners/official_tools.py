from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Literal

from ev4_transition.canonical_json import canonical_sha256, write_canonical_json
from ev4_transition.diagnostics import Diagnostic

from .records import ToolExecutionOutcome
from .subprocess_runner import execute_official_tool

ToolKind = Literal["validator", "adapter"]


def execute_validator(
    *,
    repo_root: str | Path,
    owner_repo: str,
    owner_commit: str,
    validator_path: str,
    payload: dict[str, Any],
    source_bundle: dict[str, Any] | None = None,
    timeout_seconds: float = 30,
    progress_sink: list[dict[str, Any]] | None = None,
) -> ToolExecutionOutcome:
    root = Path(repo_root).resolve()
    with tempfile.TemporaryDirectory(prefix="ev4-pg-validator-") as td:
        temp_root = Path(td)
        payload_path = temp_root / "payload.json"
        write_canonical_json(payload_path, payload)
        command = [sys.executable, str(root / validator_path), "--repo-root", str(root), "--file", str(payload_path), "--format", "json"]
        if source_bundle is not None:
            source_bundle_path = temp_root / "source-bundle.json"
            write_canonical_json(source_bundle_path, source_bundle)
            command.extend(["--source-bundle", str(source_bundle_path)])
        return execute_official_tool(
            tool_kind="validator",
            owner_repo=owner_repo,
            owner_commit=owner_commit,
            tool_path=validator_path,
            command=command,
            working_directory=root,
            timeout_seconds=timeout_seconds,
            input_ref="payload.json",
            input_hash=canonical_sha256(payload),
            parsed_result_ref="stdout:json",
            progress_sink=progress_sink,
            env=_deterministic_env(),
        )


def execute_adapter(
    *,
    repo_root: str | Path,
    owner_repo: str,
    owner_commit: str,
    adapter_path: str,
    command: list[str],
    input_ref: str,
    input_hash: str,
    output_ref: str | None = None,
    output_path: str | Path | None = None,
    validator_after_adapter_ref: str | None = None,
    timeout_seconds: float = 30,
    progress_sink: list[dict[str, Any]] | None = None,
) -> ToolExecutionOutcome:
    return execute_official_tool(
        tool_kind="adapter",
        owner_repo=owner_repo,
        owner_commit=owner_commit,
        tool_path=adapter_path,
        command=command,
        working_directory=repo_root,
        timeout_seconds=timeout_seconds,
        input_ref=input_ref,
        input_hash=input_hash,
        output_ref=output_ref,
        output_path=output_path,
        validator_after_adapter_ref=validator_after_adapter_ref,
        progress_sink=progress_sink,
        env=_deterministic_env(),
    )


def diagnostics_from_outcome(outcome: ToolExecutionOutcome) -> list[Diagnostic]:
    return outcome.diagnostics


def _deterministic_env() -> dict[str, str]:
    allowed = {"PATH", "PYTHONPATH", "HOME"}
    env = {key: value for key, value in os.environ.items() if key in allowed}
    env.update({"LC_ALL": "C.UTF-8", "LANG": "C.UTF-8", "PYTHONHASHSEED": "0"})
    return env
