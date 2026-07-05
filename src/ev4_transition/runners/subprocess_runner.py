from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Literal

from ev4_transition.canonical_json import bytes_sha256, file_sha256
from ev4_transition.progress import ProgressEvent, emit_progress_event

from .failure_mapping import adapter_command_mismatch, command_not_found, execution_failed, fallback_adapter_forbidden, map_structured_nonzero, map_zero_exit, missing_tool, text_failure, text_success, timeout, unparseable_output
from .records import TimeoutPolicy, ToolExecutionOutcome, build_adapter_execution_record, build_validator_execution_record, repo_relative

ToolKind = Literal["validator", "adapter"]
EMPTY_SHA256 = bytes_sha256(b"")
TRUSTED_INTERPRETER_NAMES = {"python", "python3", "node"}


def execute_official_tool(
    *,
    tool_kind: ToolKind,
    owner_repo: str,
    owner_commit: str,
    tool_path: str | Path,
    command: list[str],
    working_directory: str | Path,
    timeout_seconds: float = 30,
    started_by: str = "ev4-project-gate-runner",
    input_ref: str | None = None,
    input_hash: str | None = None,
    output_ref: str | None = None,
    output_path: str | Path | None = None,
    parsed_result_ref: str | None = None,
    validator_after_adapter_ref: str | None = None,
    progress_sink: list[dict[str, Any]] | None = None,
    env: dict[str, str] | None = None,
) -> ToolExecutionOutcome:
    """Run an official validator/adapter and return a sanitized evidence record.

    This module is the only Project Gate boundary allowed to import and use subprocess.
    Raw stdout/stderr are never returned; only their SHA-256 hashes are stored.
    """

    root = Path(working_directory).resolve()
    resolved_tool = Path(tool_path)
    if not resolved_tool.is_absolute():
        resolved_tool = root / resolved_tool
    tool_path_ref = repo_relative(resolved_tool, root)
    timeout_policy = TimeoutPolicy(seconds=timeout_seconds)

    if tool_kind == "adapter" and _looks_like_fallback_adapter(tool_path_ref, command):
        status, diag = fallback_adapter_forbidden(tool_path_ref, command)
        record = _record(
            tool_kind=tool_kind,
            owner_repo=owner_repo,
            owner_commit=owner_commit,
            tool_path_ref=tool_path_ref,
            command=command,
            working_directory=root.name,
            exit_code=None,
            stdout_hash=EMPTY_SHA256,
            stderr_hash=EMPTY_SHA256,
            started_by=started_by,
            timeout_policy=timeout_policy,
            parsed_result_ref=parsed_result_ref,
            input_ref=input_ref,
            input_hash=input_hash,
            output_ref=output_ref,
            output_hash=None,
            validator_after_adapter_ref=validator_after_adapter_ref,
            failure_code=diag.code,
        )
        return ToolExecutionOutcome(status, [diag], record, None, EMPTY_SHA256, EMPTY_SHA256)

    if not resolved_tool.exists():
        status, diag = missing_tool(tool_kind, tool_path_ref)
        record = _record(
            tool_kind=tool_kind,
            owner_repo=owner_repo,
            owner_commit=owner_commit,
            tool_path_ref=tool_path_ref,
            command=command,
            working_directory=root.name,
            exit_code=None,
            stdout_hash=EMPTY_SHA256,
            stderr_hash=EMPTY_SHA256,
            started_by=started_by,
            timeout_policy=timeout_policy,
            parsed_result_ref=parsed_result_ref,
            input_ref=input_ref,
            input_hash=input_hash,
            output_ref=output_ref,
            output_hash=None,
            validator_after_adapter_ref=validator_after_adapter_ref,
            failure_code=diag.code,
        )
        return ToolExecutionOutcome(status, [diag], record, None, EMPTY_SHA256, EMPTY_SHA256)

    if tool_kind == "adapter" and not _command_invokes_declared_tool(command, resolved_tool):
        status, diag = adapter_command_mismatch(tool_path_ref, command)
        record = _record(
            tool_kind=tool_kind,
            owner_repo=owner_repo,
            owner_commit=owner_commit,
            tool_path_ref=tool_path_ref,
            command=command,
            working_directory=root.name,
            exit_code=None,
            stdout_hash=EMPTY_SHA256,
            stderr_hash=EMPTY_SHA256,
            started_by=started_by,
            timeout_policy=timeout_policy,
            parsed_result_ref=parsed_result_ref,
            input_ref=input_ref,
            input_hash=input_hash,
            output_ref=output_ref,
            output_hash=None,
            validator_after_adapter_ref=validator_after_adapter_ref,
            failure_code=diag.code,
        )
        return ToolExecutionOutcome(status, [diag], record, None, EMPTY_SHA256, EMPTY_SHA256)

    emit_progress_event(progress_sink, ProgressEvent("official_tool_started", f"Running official {tool_kind}.", "running", repo_path=tool_path_ref), repo_root=root)
    try:
        completed = subprocess.run(command, cwd=root, text=False, capture_output=True, check=False, timeout=timeout_seconds, env=env)
        stdout = completed.stdout or b""
        stderr = completed.stderr or b""
        exit_code = completed.returncode
    except FileNotFoundError:
        status, diag = command_not_found(command)
        record = _record(
            tool_kind=tool_kind,
            owner_repo=owner_repo,
            owner_commit=owner_commit,
            tool_path_ref=tool_path_ref,
            command=command,
            working_directory=root.name,
            exit_code=None,
            stdout_hash=EMPTY_SHA256,
            stderr_hash=EMPTY_SHA256,
            started_by=started_by,
            timeout_policy=timeout_policy,
            parsed_result_ref=parsed_result_ref,
            input_ref=input_ref,
            input_hash=input_hash,
            output_ref=output_ref,
            output_hash=None,
            validator_after_adapter_ref=validator_after_adapter_ref,
            failure_code=diag.code,
        )
        return ToolExecutionOutcome(status, [diag], record, None, EMPTY_SHA256, EMPTY_SHA256)
    except subprocess.TimeoutExpired as exc:
        stdout = _partial_bytes(exc.stdout)
        stderr = _partial_bytes(exc.stderr)
        stdout_hash = bytes_sha256(stdout)
        stderr_hash = bytes_sha256(stderr)
        status, diag = timeout(tool_kind, timeout_seconds)
        record = _record(
            tool_kind=tool_kind,
            owner_repo=owner_repo,
            owner_commit=owner_commit,
            tool_path_ref=tool_path_ref,
            command=command,
            working_directory=root.name,
            exit_code=None,
            stdout_hash=stdout_hash,
            stderr_hash=stderr_hash,
            started_by=started_by,
            timeout_policy=timeout_policy,
            parsed_result_ref=parsed_result_ref,
            input_ref=input_ref,
            input_hash=input_hash,
            output_ref=output_ref,
            output_hash=None,
            validator_after_adapter_ref=validator_after_adapter_ref,
            failure_code=diag.code,
        )
        return ToolExecutionOutcome(status, [diag], record, None, stdout_hash, stderr_hash)

    stdout_hash = bytes_sha256(stdout)
    stderr_hash = bytes_sha256(stderr)
    parsed = None if parsed_result_ref == "stdout:text" else _parse_json(stdout)
    output_hash = file_sha256(output_path) if output_path is not None and Path(output_path).exists() else (stdout_hash if output_ref and output_ref.startswith("stdout:") else None)
    if parsed_result_ref == "stdout:text":
        if exit_code == 0:
            status, diagnostics = text_success()
        else:
            status, diag = text_failure(tool_kind, exit_code)
            diagnostics = [diag]
    elif parsed is None:
        status, diag = unparseable_output()
        diagnostics = [diag]
    elif exit_code == 0:
        status, diagnostics = map_zero_exit(parsed)
    else:
        status, diag = map_structured_nonzero(tool_kind, parsed, exit_code)
        diagnostics = [diag]
    failure_code = diagnostics[0].code if diagnostics and status != "accepted" else None
    record = _record(
        tool_kind=tool_kind,
        owner_repo=owner_repo,
        owner_commit=owner_commit,
        tool_path_ref=tool_path_ref,
        command=command,
        working_directory=root.name,
        exit_code=exit_code,
        stdout_hash=stdout_hash,
        stderr_hash=stderr_hash,
        started_by=started_by,
        timeout_policy=timeout_policy,
        parsed_result_ref=parsed_result_ref,
        input_ref=input_ref,
        input_hash=input_hash,
        output_ref=output_ref,
        output_hash=output_hash,
        validator_after_adapter_ref=validator_after_adapter_ref,
        failure_code=failure_code,
    )
    if parsed_result_ref != "stdout:text" and parsed is None and exit_code != 0:
        status2, diag2 = execution_failed(exit_code)
        status, diagnostics = status2, [diag2]
        record = _record(
            tool_kind=tool_kind,
            owner_repo=owner_repo,
            owner_commit=owner_commit,
            tool_path_ref=tool_path_ref,
            command=command,
            working_directory=root.name,
            exit_code=exit_code,
            stdout_hash=stdout_hash,
            stderr_hash=stderr_hash,
            started_by=started_by,
            timeout_policy=timeout_policy,
            parsed_result_ref=parsed_result_ref,
            input_ref=input_ref,
            input_hash=input_hash,
            output_ref=output_ref,
            output_hash=output_hash,
            validator_after_adapter_ref=validator_after_adapter_ref,
            failure_code=diag2.code,
        )
    emit_progress_event(progress_sink, ProgressEvent("official_tool_finished", f"Official {tool_kind} finished.", status, repo_path=tool_path_ref, details={"exit_code": exit_code}), repo_root=root)
    return ToolExecutionOutcome(status, diagnostics, record, parsed, stdout_hash, stderr_hash)


def _record(**kwargs: Any):
    tool_kind = kwargs.pop("tool_kind")
    tool_path_ref = kwargs.pop("tool_path_ref")
    if tool_kind == "validator":
        allowed = {
            "owner_repo", "owner_commit", "command", "working_directory", "exit_code",
            "stdout_hash", "stderr_hash", "started_by", "timeout_policy",
            "parsed_result_ref", "failure_code",
        }
        data = {key: value for key, value in kwargs.items() if key in allowed}
        return build_validator_execution_record(validator_path=tool_path_ref, **data)
    allowed = {
        "owner_repo", "owner_commit", "command", "working_directory", "exit_code",
        "stdout_hash", "stderr_hash", "started_by", "timeout_policy",
        "input_ref", "input_hash", "output_ref", "output_hash",
        "validator_after_adapter_ref", "failure_code",
    }
    data = {key: value for key, value in kwargs.items() if key in allowed}
    return build_adapter_execution_record(adapter_path=tool_path_ref, command_or_entrypoint=data["command"], **data)


def _parse_json(stdout: bytes) -> dict[str, Any] | None:
    try:
        value = json.loads(stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _partial_bytes(value: bytes | str | None) -> bytes:
    if value is None:
        return b""
    if isinstance(value, bytes):
        return value
    return value.encode("utf-8", errors="replace")


def _looks_like_fallback_adapter(adapter_path: str, command: list[str]) -> bool:
    text = " ".join([adapter_path, *command]).lower()
    return "fallback" in text


def _command_invokes_declared_tool(command: list[str], resolved_tool: Path) -> bool:
    if not command:
        return False
    expected = resolved_tool.resolve()
    if _same_path(command[0], expected):
        return True
    executable = Path(command[0]).name.lower()
    if executable in TRUSTED_INTERPRETER_NAMES or executable.startswith("python"):
        return len(command) >= 2 and _same_path(command[1], expected)
    return False


def _same_path(value: str, expected: Path) -> bool:
    try:
        return Path(value).resolve() == expected
    except OSError:
        return False
