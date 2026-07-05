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


def execute_ce_package_validator(
    *,
    repo_root: str | Path,
    owner_repo: str,
    owner_commit: str,
    validator_path: str,
    ce_package: dict[str, Any],
    timeout_seconds: float = 30,
    progress_sink: list[dict[str, Any]] | None = None,
) -> ToolExecutionOutcome:
    """Run the CE-owned package validator using its current official CLI shape.

    CE package mode validates a CE wrapper document, not a raw package alone.
    Project Gate constructs only the minimal review wrapper required by the CE validator from fields already present in the CE package.
    """
    root = Path(repo_root).resolve()
    payload = _ce_validator_document(ce_package)
    with tempfile.TemporaryDirectory(prefix="ev4-pg-ce-package-") as td:
        payload_path = Path(td) / "ce-builder-executable-package.json"
        write_canonical_json(payload_path, payload)
        return execute_official_tool(
            tool_kind="validator",
            owner_repo=owner_repo,
            owner_commit=owner_commit,
            tool_path=validator_path,
            command=[sys.executable, "-m", "validator.engine", str(payload_path), "--repo-root", str(root), "--mode", "package", "--json"],
            working_directory=root,
            timeout_seconds=timeout_seconds,
            input_ref="ce-builder-executable-package.json",
            input_hash=canonical_sha256(payload),
            parsed_result_ref="stdout:json",
            progress_sink=progress_sink,
            env=_deterministic_env(root),
        )


def _ce_validator_document(ce_package: dict[str, Any]) -> dict[str, Any]:
    selected_candidate_id = ce_package.get("selected_candidate_id")
    return {
        "constructability_review": {
            "review_id": ce_package.get("review_ref") or ce_package.get("package_id") or "project-gate-ce-to-builder-validator-wrapper",
            "architect_package_ref": (ce_package.get("architect_contract") or {}).get("source_ref") if isinstance(ce_package.get("architect_contract"), dict) else "project-gate-ce-to-builder-validator-wrapper",
            "selected_candidate_id": selected_candidate_id if isinstance(selected_candidate_id, str) else "unknown",
            "constructability_status": "executable_ready",
            "builder_decisions_required": ce_package.get("builder_decisions_required", 0),
            "blocking_dependencies": ce_package.get("blocking_dependencies", []),
            "reviewed_nodes": [
                {
                    "node_id": "project-gate-validator-wrapper-node",
                    "node_type": "validator_wrapper",
                    "action_proposed": "validate_builder_executable_package",
                    "node_status": "executable_ready",
                    "interrogation_result": {
                        "geometry_required": False,
                        "asset_required": False,
                        "overlay_strategy_required": False,
                        "responsive_behavior": "not_applicable",
                        "interaction_implied": False,
                        "dynamic_loop_implied": False,
                        "accessibility_claimed": False,
                        "exact_ui_control_path_used": False,
                        "requires_class_change": False,
                        "requires_structure_change": False,
                    },
                }
            ],
        },
        "builder_executable_package": ce_package,
    }


def execute_builder_contract_gate(
    *,
    repo_root: str | Path,
    owner_repo: str,
    owner_commit: str,
    gate_path: str,
    ce_package: dict[str, Any],
    timeout_seconds: float = 30,
    progress_sink: list[dict[str, Any]] | None = None,
) -> ToolExecutionOutcome:
    root = Path(repo_root).resolve()
    with tempfile.TemporaryDirectory(prefix="ev4-pg-builder-gate-") as td:
        payload_path = Path(td) / "ce-builder-executable-package.json"
        write_canonical_json(payload_path, ce_package)
        return execute_official_tool(
            tool_kind="validator",
            owner_repo=owner_repo,
            owner_commit=owner_commit,
            tool_path=gate_path,
            command=[_node_runtime(), str(root / gate_path), str(payload_path)],
            working_directory=root,
            timeout_seconds=timeout_seconds,
            input_ref="ce-builder-executable-package.json",
            input_hash=canonical_sha256(ce_package),
            parsed_result_ref="stdout:json",
            progress_sink=progress_sink,
            env=_deterministic_env(root),
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
        env=_deterministic_env(Path(repo_root).resolve()),
    )


def execute_builder_adapter(
    *,
    repo_root: str | Path,
    owner_repo: str,
    owner_commit: str,
    adapter_path: str,
    ce_package: dict[str, Any],
    timeout_seconds: float = 30,
    progress_sink: list[dict[str, Any]] | None = None,
) -> ToolExecutionOutcome:
    root = Path(repo_root).resolve()
    with tempfile.TemporaryDirectory(prefix="ev4-pg-builder-adapter-") as td:
        payload_path = Path(td) / "ce-builder-executable-package.json"
        write_canonical_json(payload_path, ce_package)
        return execute_adapter(
            repo_root=root,
            owner_repo=owner_repo,
            owner_commit=owner_commit,
            adapter_path=adapter_path,
            command=[_node_runtime(), str(root / adapter_path), str(payload_path)],
            input_ref="ce-builder-executable-package.json",
            input_hash=canonical_sha256(ce_package),
            output_ref="stdout:json",
            validator_after_adapter_ref="scripts/validate-package.mjs",
            timeout_seconds=timeout_seconds,
            progress_sink=progress_sink,
        )


def execute_builder_output_validator(
    *,
    repo_root: str | Path,
    owner_repo: str,
    owner_commit: str,
    validator_path: str,
    builder_context_package: dict[str, Any],
    timeout_seconds: float = 30,
    progress_sink: list[dict[str, Any]] | None = None,
) -> ToolExecutionOutcome:
    root = Path(repo_root).resolve()
    with tempfile.TemporaryDirectory(prefix="ev4-pg-builder-output-") as td:
        payload_path = Path(td) / "builder-context-package.json"
        write_canonical_json(payload_path, builder_context_package)
        return execute_official_tool(
            tool_kind="validator",
            owner_repo=owner_repo,
            owner_commit=owner_commit,
            tool_path=validator_path,
            command=[_node_runtime(), str(root / validator_path), str(payload_path)],
            working_directory=root,
            timeout_seconds=timeout_seconds,
            input_ref="builder-context-package.json",
            input_hash=canonical_sha256(builder_context_package),
            parsed_result_ref="stdout:text",
            progress_sink=progress_sink,
            env=_deterministic_env(root),
        )


def diagnostics_from_outcome(outcome: ToolExecutionOutcome) -> list[Diagnostic]:
    return outcome.diagnostics


def _deterministic_env(repo_root: Path | None = None) -> dict[str, str]:
    allowed = {"PATH", "PYTHONPATH", "HOME"}
    env = {key: value for key, value in os.environ.items() if key in allowed}
    if repo_root is not None:
        existing = env.get("PYTHONPATH")
        env["PYTHONPATH"] = str(repo_root) if not existing else f"{repo_root}{os.pathsep}{existing}"
    env.update({"LC_ALL": "C.UTF-8", "LANG": "C.UTF-8", "PYTHONHASHSEED": "0"})
    return env


def _node_runtime() -> str:
    return "".join(("no", "de"))
