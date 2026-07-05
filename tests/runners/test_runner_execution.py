from __future__ import annotations

import sys
from pathlib import Path

from ev4_transition.runners import execute_official_tool


def _script(tmp_path: Path, name: str, body: str) -> Path:
    path = tmp_path / name
    path.write_text(body, encoding="utf-8")
    return path


def _run(tmp_path: Path, *, tool_kind="validator", tool_path="tool.py", command=None, timeout_seconds=5):
    command = command or [sys.executable, str(tmp_path / tool_path)]
    return execute_official_tool(
        tool_kind=tool_kind,
        owner_repo="owner/repo",
        owner_commit="a" * 40,
        tool_path=tool_path,
        command=command,
        working_directory=tmp_path,
        timeout_seconds=timeout_seconds,
        parsed_result_ref="stdout:json" if tool_kind == "validator" else None,
        input_ref="input.json" if tool_kind == "adapter" else None,
        input_hash="b" * 64 if tool_kind == "adapter" else None,
        validator_after_adapter_ref="validator-after-adapter" if tool_kind == "adapter" else None,
    )


def test_missing_validator_maps_to_insufficient_evidence(tmp_path: Path) -> None:
    outcome = _run(tmp_path, tool_path="missing.py")
    assert outcome.status == "insufficient_evidence"
    assert outcome.diagnostics[0].code == "PG.VALIDATOR.MISSING"


def test_missing_adapter_maps_to_insufficient_evidence(tmp_path: Path) -> None:
    outcome = _run(tmp_path, tool_kind="adapter", tool_path="missing_adapter.py", command=[sys.executable, str(tmp_path / "missing_adapter.py")])
    assert outcome.status == "insufficient_evidence"
    assert outcome.diagnostics[0].code == "PG.ADAPTER.MISSING"


def test_validator_timeout_maps_to_insufficient_evidence(tmp_path: Path) -> None:
    _script(tmp_path, "tool.py", "import time\ntime.sleep(2)\n")
    outcome = _run(tmp_path, timeout_seconds=0.05)
    assert outcome.status == "insufficient_evidence"
    assert outcome.diagnostics[0].code == "PG.VALIDATOR.TIMEOUT"


def test_adapter_timeout_maps_to_insufficient_evidence(tmp_path: Path) -> None:
    _script(tmp_path, "adapter.py", "import time\ntime.sleep(2)\n")
    outcome = _run(tmp_path, tool_kind="adapter", tool_path="adapter.py", command=[sys.executable, str(tmp_path / "adapter.py")], timeout_seconds=0.05)
    assert outcome.status == "insufficient_evidence"
    assert outcome.diagnostics[0].code == "PG.ADAPTER.TIMEOUT"


def test_command_not_found_maps_to_insufficient_evidence(tmp_path: Path) -> None:
    _script(tmp_path, "tool.py", "print('{}')\n")
    outcome = _run(tmp_path, command=["definitely-not-found-ev4-runner"])
    assert outcome.status == "insufficient_evidence"
    assert outcome.diagnostics[0].code == "PG.RUNNER.COMMAND_NOT_FOUND"


def test_unparseable_output_maps_to_insufficient_evidence(tmp_path: Path) -> None:
    _script(tmp_path, "tool.py", "print('not-json')\n")
    outcome = _run(tmp_path)
    assert outcome.status == "insufficient_evidence"
    assert outcome.diagnostics[0].code == "PG.RUNNER.UNPARSEABLE_OUTPUT"


def test_nonzero_exit_with_structured_repair_maps_to_repair_needed(tmp_path: Path) -> None:
    _script(tmp_path, "tool.py", "import json, sys\nprint(json.dumps({'status':'repair_needed','diagnostics':[{'severity':'warning','code':'REPAIR'}]}))\nsys.exit(1)\n")
    outcome = _run(tmp_path)
    assert outcome.status == "repair_needed"
    assert outcome.diagnostics[0].code == "PG.VALIDATOR.REPAIR_NEEDED"


def test_nonzero_exit_with_contract_violation_maps_to_invalid(tmp_path: Path) -> None:
    _script(tmp_path, "tool.py", "import json, sys\nprint(json.dumps({'status':'invalid','diagnostics':[{'severity':'error','code':'contract_violation'}]}))\nsys.exit(1)\n")
    outcome = _run(tmp_path)
    assert outcome.status == "invalid"
    assert outcome.diagnostics[0].code == "PG.VALIDATOR.CONTRACT_VIOLATION"


def test_fallback_adapter_used_fails(tmp_path: Path) -> None:
    _script(tmp_path, "fallback_adapter.py", "print('{}')\n")
    outcome = _run(tmp_path, tool_kind="adapter", tool_path="fallback_adapter.py", command=[sys.executable, str(tmp_path / "fallback_adapter.py")])
    assert outcome.status == "invalid"
    assert outcome.diagnostics[0].code == "PG.ADAPTER.FALLBACK_FORBIDDEN"


def test_adapter_command_must_invoke_declared_adapter_path(tmp_path: Path) -> None:
    _script(tmp_path, "official_adapter.py", "import json\nprint(json.dumps({'status':'valid'}))\n")
    _script(tmp_path, "other.py", "import json\nprint(json.dumps({'status':'valid'}))\n")
    outcome = _run(tmp_path, tool_kind="adapter", tool_path="official_adapter.py", command=[sys.executable, str(tmp_path / "other.py")])
    assert outcome.status == "invalid"
    assert outcome.diagnostics[0].code == "PG.ADAPTER.COMMAND_PATH_MISMATCH"


def test_adapter_command_accepts_declared_adapter_as_interpreter_script(tmp_path: Path) -> None:
    _script(tmp_path, "official_adapter.py", "import json\nprint(json.dumps({'status':'valid'}))\n")
    outcome = _run(tmp_path, tool_kind="adapter", tool_path="official_adapter.py", command=[sys.executable, str(tmp_path / "official_adapter.py")])
    assert outcome.status == "accepted"
    assert outcome.execution_record.to_dict()["adapter_path"] == "official_adapter.py"


def test_execution_record_has_minimum_semantic_children(tmp_path: Path) -> None:
    _script(tmp_path, "tool.py", "import json\nprint(json.dumps({'status':'valid'}))\n")
    outcome = _run(tmp_path)
    record = outcome.execution_record.to_dict()
    for key in ["owner_repo", "owner_commit", "validator_path", "command", "working_directory", "exit_code", "stdout_hash", "stderr_hash", "execution_record_hash", "started_by", "timeout_policy", "parsed_result_ref"]:
        assert key in record


def test_stdout_and_stderr_hashes_are_stable(tmp_path: Path) -> None:
    _script(tmp_path, "tool.py", "import json, sys\nprint(json.dumps({'status':'valid'}))\nprint('warn', file=sys.stderr)\n")
    first = _run(tmp_path)
    second = _run(tmp_path)
    assert first.stdout_hash == second.stdout_hash
    assert first.stderr_hash == second.stderr_hash
