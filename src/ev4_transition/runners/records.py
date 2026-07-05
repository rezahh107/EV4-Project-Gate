from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from ev4_transition.canonical_json import canonical_sha256
from ev4_transition.diagnostics import Diagnostic

ToolKind = Literal["validator", "adapter"]
RunStatus = Literal["accepted", "repair_needed", "insufficient_evidence", "invalid"]


@dataclass(frozen=True)
class TimeoutPolicy:
    seconds: float
    kill_process_tree: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {"seconds": self.seconds, "kill_process_tree": self.kill_process_tree}


@dataclass(frozen=True)
class ExecutionRecord:
    tool_kind: ToolKind
    owner_repo: str
    owner_commit: str
    command: list[str]
    working_directory: str
    exit_code: int | None
    stdout_hash: str
    stderr_hash: str
    started_by: str
    timeout_policy: TimeoutPolicy
    validator_path: str | None = None
    adapter_path: str | None = None
    parsed_result_ref: str | None = None
    command_or_entrypoint: list[str] | str | None = None
    input_ref: str | None = None
    input_hash: str | None = None
    output_ref: str | None = None
    output_hash: str | None = None
    validator_after_adapter_ref: str | None = None
    failure_code: str | None = None

    def to_dict_without_hash(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "tool_kind": self.tool_kind,
            "owner_repo": self.owner_repo,
            "owner_commit": self.owner_commit,
            "command": list(self.command),
            "working_directory": self.working_directory,
            "exit_code": self.exit_code,
            "stdout_hash": self.stdout_hash,
            "stderr_hash": self.stderr_hash,
            "started_by": self.started_by,
            "timeout_policy": self.timeout_policy.to_dict(),
        }
        if self.tool_kind == "validator":
            payload.update({"validator_path": self.validator_path, "parsed_result_ref": self.parsed_result_ref})
        else:
            payload.update({
                "adapter_path": self.adapter_path,
                "command_or_entrypoint": self.command_or_entrypoint if self.command_or_entrypoint is not None else list(self.command),
                "input_ref": self.input_ref,
                "input_hash": self.input_hash,
                "output_ref": self.output_ref,
                "output_hash": self.output_hash,
                "validator_after_adapter_ref": self.validator_after_adapter_ref,
            })
        if self.failure_code:
            payload["failure_code"] = self.failure_code
        return payload

    def to_dict(self) -> dict[str, Any]:
        payload = self.to_dict_without_hash()
        payload["execution_record_hash"] = canonical_sha256(payload)
        return payload

    @property
    def execution_record_hash(self) -> str:
        return self.to_dict()["execution_record_hash"]


@dataclass(frozen=True)
class ToolExecutionOutcome:
    status: RunStatus
    diagnostics: list[Diagnostic]
    execution_record: ExecutionRecord
    parsed_result: dict[str, Any] | None = None
    stdout_hash: str = ""
    stderr_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "diagnostics": [item.to_dict() for item in self.diagnostics],
            "execution_record": self.execution_record.to_dict(),
            "parsed_result": self.parsed_result,
            "stdout_hash": self.stdout_hash,
            "stderr_hash": self.stderr_hash,
        }


def repo_relative(path: str | Path, repo_root: str | Path) -> str:
    candidate = Path(path).resolve()
    root = Path(repo_root).resolve()
    try:
        return candidate.relative_to(root).as_posix()
    except ValueError:
        return candidate.name


def build_validator_execution_record(
    *,
    owner_repo: str,
    owner_commit: str,
    validator_path: str,
    command: list[str],
    working_directory: str,
    exit_code: int | None,
    stdout_hash: str,
    stderr_hash: str,
    started_by: str,
    timeout_policy: TimeoutPolicy,
    parsed_result_ref: str | None,
    failure_code: str | None = None,
) -> ExecutionRecord:
    return ExecutionRecord(
        tool_kind="validator",
        owner_repo=owner_repo,
        owner_commit=owner_commit,
        validator_path=validator_path,
        command=command,
        working_directory=working_directory,
        exit_code=exit_code,
        stdout_hash=stdout_hash,
        stderr_hash=stderr_hash,
        started_by=started_by,
        timeout_policy=timeout_policy,
        parsed_result_ref=parsed_result_ref,
        failure_code=failure_code,
    )


def build_adapter_execution_record(
    *,
    owner_repo: str,
    owner_commit: str,
    adapter_path: str,
    command_or_entrypoint: list[str] | str,
    command: list[str],
    working_directory: str,
    exit_code: int | None,
    stdout_hash: str,
    stderr_hash: str,
    started_by: str,
    timeout_policy: TimeoutPolicy,
    input_ref: str | None,
    input_hash: str | None,
    output_ref: str | None,
    output_hash: str | None,
    validator_after_adapter_ref: str | None,
    failure_code: str | None = None,
) -> ExecutionRecord:
    return ExecutionRecord(
        tool_kind="adapter",
        owner_repo=owner_repo,
        owner_commit=owner_commit,
        adapter_path=adapter_path,
        command_or_entrypoint=command_or_entrypoint,
        command=command,
        working_directory=working_directory,
        exit_code=exit_code,
        stdout_hash=stdout_hash,
        stderr_hash=stderr_hash,
        started_by=started_by,
        timeout_policy=timeout_policy,
        input_ref=input_ref,
        input_hash=input_hash,
        output_ref=output_ref,
        output_hash=output_hash,
        validator_after_adapter_ref=validator_after_adapter_ref,
        failure_code=failure_code,
    )
