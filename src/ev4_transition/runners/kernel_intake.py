from __future__ import annotations

import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ev4_transition.canonical_json import bytes_sha256, write_canonical_json


@dataclass(frozen=True)
class KernelAuditExecution:
    execution_status: str
    result: dict[str, Any] | None
    exit_code: int | None
    stdout_sha256: str
    stderr_sha256: str
    failure_code: str | None = None


def execute_kernel_l2_audit(
    *,
    kernel_repo_root: str | Path,
    bridge_path: str | Path,
    packet: dict[str, Any],
    timeout_seconds: float = 30,
) -> KernelAuditExecution:
    root = Path(kernel_repo_root).resolve()
    bridge = Path(bridge_path).resolve()
    if not root.exists():
        return _failure("PG.KERNEL.CHECKOUT_UNAVAILABLE")
    if not bridge.exists():
        return _failure("PG.KERNEL.BRIDGE_UNAVAILABLE")

    with tempfile.TemporaryDirectory(prefix="ev4-pg-kernel-intake-") as td:
        input_path = Path(td) / "packet.json"
        write_canonical_json(
            input_path,
            {
                "decision_record": packet.get("decision_record"),
                "resolver_input": packet.get("resolver_input"),
                "audit_context": packet.get("audit_context", {}),
            },
        )
        env = {"PATH": os.environ.get("PATH", ""), "HOME": os.environ.get("HOME", ""), "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"}
        try:
            completed = subprocess.run(
                ["node", str(bridge), str(root), str(input_path)],
                cwd=root,
                capture_output=True,
                text=False,
                check=False,
                timeout=timeout_seconds,
                env=env,
            )
        except FileNotFoundError:
            return _failure("PG.KERNEL.NODE_UNAVAILABLE")
        except subprocess.TimeoutExpired as exc:
            return KernelAuditExecution("execution_failure", None, None, bytes_sha256(_partial(exc.stdout)), bytes_sha256(_partial(exc.stderr)), "PG.KERNEL.EXECUTION_TIMEOUT")

    stdout = completed.stdout or b""
    stderr = completed.stderr or b""
    stdout_hash = bytes_sha256(stdout)
    stderr_hash = bytes_sha256(stderr)
    if completed.returncode != 0:
        return KernelAuditExecution("execution_failure", None, completed.returncode, stdout_hash, stderr_hash, "PG.KERNEL.EXECUTION_FAILED")
    try:
        envelope = json.loads(stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return KernelAuditExecution("malformed_output", None, completed.returncode, stdout_hash, stderr_hash, "PG.KERNEL.OUTPUT_MALFORMED")
    if not isinstance(envelope, dict) or envelope.get("bridge_status") != "ok" or not isinstance(envelope.get("result"), dict):
        return KernelAuditExecution("malformed_output", None, completed.returncode, stdout_hash, stderr_hash, "PG.KERNEL.OUTPUT_UNKNOWN")
    result = envelope["result"]
    if result.get("audit_status") not in {"pass", "fail", "unsupported"} or not isinstance(result.get("diagnostics"), list):
        return KernelAuditExecution("malformed_output", None, completed.returncode, stdout_hash, stderr_hash, "PG.KERNEL.OUTPUT_UNKNOWN")
    return KernelAuditExecution("executed", result, completed.returncode, stdout_hash, stderr_hash)


def _failure(code: str) -> KernelAuditExecution:
    empty = bytes_sha256(b"")
    return KernelAuditExecution("execution_failure", None, None, empty, empty, code)


def _partial(value: bytes | str | None) -> bytes:
    if value is None:
        return b""
    return value if isinstance(value, bytes) else value.encode("utf-8", errors="replace")
