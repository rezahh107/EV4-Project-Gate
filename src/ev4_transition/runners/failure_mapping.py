from __future__ import annotations

from typing import Any, Literal

from ev4_transition.diagnostics import Diagnostic, diagnostic

ToolKind = Literal["validator", "adapter"]
RunStatus = Literal["accepted", "repair_needed", "insufficient_evidence", "invalid"]


def missing_tool(tool_kind: ToolKind, path: str) -> tuple[RunStatus, Diagnostic]:
    if tool_kind == "validator":
        return "insufficient_evidence", diagnostic("PG.VALIDATOR.MISSING", "insufficient_evidence", "Official validator is missing; Project Gate cannot treat this as success.", "$", validator_path=path)
    return "insufficient_evidence", diagnostic("PG.ADAPTER.MISSING", "insufficient_evidence", "Official adapter is missing; Project Gate cannot treat this as success.", "$", adapter_path=path)


def timeout(tool_kind: ToolKind, seconds: float) -> tuple[RunStatus, Diagnostic]:
    code = "PG.VALIDATOR.TIMEOUT" if tool_kind == "validator" else "PG.ADAPTER.TIMEOUT"
    return "insufficient_evidence", diagnostic(code, "insufficient_evidence", "Official tool timed out; timeouts are never success.", "$", timeout_seconds=seconds)


def command_not_found(command: list[str]) -> tuple[RunStatus, Diagnostic]:
    return "insufficient_evidence", diagnostic("PG.RUNNER.COMMAND_NOT_FOUND", "insufficient_evidence", "Command executable was not found; execution evidence is unavailable.", "$", command=command[:1])


def unparseable_output() -> tuple[RunStatus, Diagnostic]:
    return "insufficient_evidence", diagnostic("PG.RUNNER.UNPARSEABLE_OUTPUT", "insufficient_evidence", "Official tool output was not parseable JSON; Project Gate cannot infer success.", "$")


def execution_failed(exit_code: int | None) -> tuple[RunStatus, Diagnostic]:
    return "insufficient_evidence", diagnostic("PG.RUNNER.EXECUTION_FAILED", "insufficient_evidence", "Official tool execution failed without a structured Project Gate result.", "$", exit_code=exit_code)


def fallback_adapter_forbidden(adapter_path: str, command: list[str]) -> tuple[RunStatus, Diagnostic]:
    return "invalid", diagnostic("PG.ADAPTER.FALLBACK_FORBIDDEN", "error", "Fallback adapter execution is forbidden in Project Gate runner infrastructure.", "$", adapter_path=adapter_path, command=command)


def adapter_command_mismatch(adapter_path: str, command: list[str]) -> tuple[RunStatus, Diagnostic]:
    return "invalid", diagnostic("PG.ADAPTER.COMMAND_PATH_MISMATCH", "error", "Adapter command must execute the declared official adapter path.", "$", adapter_path=adapter_path, command=command)


def text_success() -> tuple[RunStatus, list[Diagnostic]]:
    return "accepted", []


def text_failure(tool_kind: ToolKind, exit_code: int | None) -> tuple[RunStatus, Diagnostic]:
    if tool_kind == "validator":
        return "invalid", diagnostic("PG.VALIDATOR.CONTRACT_VIOLATION", "error", "Official text-output validator exited non-zero; Project Gate treats this as a blocking owner validation failure.", "$", exit_code=exit_code)
    return "invalid", diagnostic("PG.ADAPTER.EXECUTION_FAILED", "error", "Official text-output adapter exited non-zero.", "$", exit_code=exit_code)


def map_structured_nonzero(tool_kind: ToolKind, parsed: dict[str, Any], exit_code: int) -> tuple[RunStatus, Diagnostic]:
    status = parsed.get("status")
    diagnostics = parsed.get("diagnostics") if isinstance(parsed.get("diagnostics"), list) else []
    codes = {item.get("code") for item in diagnostics if isinstance(item, dict)}
    severities = {item.get("severity") for item in diagnostics if isinstance(item, dict)}
    if parsed.get("passed") is False or parsed.get("result") == "fail" or parsed.get("blocking") is True:
        if tool_kind == "validator":
            return "invalid", diagnostic("PG.VALIDATOR.CONTRACT_VIOLATION", "error", "Official validator returned a structured blocking failure.", "$", exit_code=exit_code, validator_status=status or parsed.get("result"), validator_diagnostic_codes=sorted(code for code in codes if isinstance(code, str)))
        return "invalid", diagnostic("PG.ADAPTER.EXECUTION_FAILED", "error", "Official adapter returned a structured blocking failure.", "$", exit_code=exit_code)
    if tool_kind == "validator" and (status == "repair_needed" or "warning" in severities):
        return "repair_needed", diagnostic("PG.VALIDATOR.REPAIR_NEEDED", "warning", "Official validator returned a structured repair-needed result.", "$", exit_code=exit_code, validator_status=status, validator_diagnostic_codes=sorted(code for code in codes if isinstance(code, str)))
    if tool_kind == "validator" and (status == "invalid" or "error" in severities or "contract_violation" in codes or "PG.VALIDATOR.CONTRACT_VIOLATION" in codes):
        return "invalid", diagnostic("PG.VALIDATOR.CONTRACT_VIOLATION", "error", "Official validator returned a structured contract violation.", "$", exit_code=exit_code, validator_status=status, validator_diagnostic_codes=sorted(code for code in codes if isinstance(code, str)))
    return execution_failed(exit_code)


def map_zero_exit(parsed: dict[str, Any]) -> tuple[RunStatus, list[Diagnostic]]:
    status = parsed.get("status")
    if status in {"accepted", "valid"} or parsed.get("passed") is True or parsed.get("result") == "pass":
        return "accepted", []
    if parsed.get("schema") == "ev4-builder-context-package@1.0.0":
        return "accepted", []
    if status == "repair_needed":
        return "repair_needed", [diagnostic("PG.VALIDATOR.REPAIR_NEEDED", "warning", "Official tool returned repair_needed.", "$")]
    if status == "insufficient_evidence":
        return "insufficient_evidence", [diagnostic("PG.RUNNER.EXECUTION_FAILED", "insufficient_evidence", "Official tool returned insufficient_evidence.", "$")]
    if status == "invalid" or parsed.get("passed") is False or parsed.get("result") == "fail":
        return "invalid", [diagnostic("PG.VALIDATOR.CONTRACT_VIOLATION", "error", "Official tool returned invalid.", "$")]
    return "insufficient_evidence", [diagnostic("PG.RUNNER.UNPARSEABLE_OUTPUT", "insufficient_evidence", "Official tool JSON omitted a recognized status.", "$")]
