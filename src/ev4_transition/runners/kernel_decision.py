from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from ev4_transition.canonical_json import write_canonical_json
from ev4_transition.diagnostics import diagnostic
from ev4_transition.kernel_decision_dependencies import KERNEL_ACCEPTED_COMMIT, KERNEL_REPOSITORY
from ev4_transition.kernel_decision_intake import KernelAuditExecution

from .subprocess_runner import execute_official_tool

BRIDGE_SCHEMA_VERSION = "project-gate-kernel-l2-bridge.v1"
BRIDGE_PATH = "scripts/kernel-decision-intake-bridge.mjs"


def execute_kernel_l2_audit(packet: dict[str, Any], *, kernel_repo_root: str | Path, project_gate_repo_root: str | Path, timeout_seconds: float = 30) -> KernelAuditExecution:
    kernel_root = Path(kernel_repo_root).resolve()
    project_gate_root = Path(project_gate_repo_root).resolve()
    bridge = project_gate_root / BRIDGE_PATH
    if not kernel_root.exists() or not bridge.exists():
        return KernelAuditExecution("unavailable", None, diagnostics=(diagnostic("PG.KERNEL_INTAKE.KERNEL_EXECUTION_UNAVAILABLE", "insufficient_evidence", "Pinned Kernel checkout or Project Gate bridge is unavailable.", "$"),))
    bridge_input = {"decision_record": packet.get("decision_record"), "resolver_input": packet.get("resolver_input"), "audit_context": packet.get("audit_context")}
    with TemporaryDirectory(prefix="ev4-kroad-011-") as temp_dir:
        input_path = Path(temp_dir) / "kernel-audit-input.json"
        write_canonical_json(input_path, bridge_input)
        outcome = execute_official_tool(tool_kind="validator", owner_repo=KERNEL_REPOSITORY, owner_commit=KERNEL_ACCEPTED_COMMIT, tool_path=bridge, command=["node", str(bridge), "--kernel-repo", str(kernel_root), "--input", str(input_path)], working_directory=project_gate_root, timeout_seconds=timeout_seconds, started_by="ev4-project-gate-kroad-011", parsed_result_ref="stdout:json")
    record = {"tool_kind": "validator", "owner_repo": outcome.execution_record.owner_repo, "owner_commit": outcome.execution_record.owner_commit, "bridge_path": BRIDGE_PATH, "exit_code": outcome.execution_record.exit_code, "stdout_hash": outcome.execution_record.stdout_hash, "stderr_hash": outcome.execution_record.stderr_hash, "failure_code": outcome.execution_record.failure_code}
    if outcome.execution_record.exit_code != 0:
        return KernelAuditExecution("unavailable", None, execution_record=record, diagnostics=(diagnostic("PG.KERNEL_INTAKE.KERNEL_EXECUTION_UNAVAILABLE", "insufficient_evidence", "Pinned Kernel bridge exited non-zero; semantic failure was not inferred from the process exit.", "$", exit_code=outcome.execution_record.exit_code, failure_code=outcome.execution_record.failure_code),))
    parsed = outcome.parsed_result
    if not isinstance(parsed, dict) or parsed.get("bridge_schema_version") != BRIDGE_SCHEMA_VERSION or parsed.get("execution_status") != "completed" or not isinstance(parsed.get("kernel_audit"), dict):
        return KernelAuditExecution("malformed", None, execution_record=record)
    return KernelAuditExecution("completed", parsed["kernel_audit"], execution_record=record)
