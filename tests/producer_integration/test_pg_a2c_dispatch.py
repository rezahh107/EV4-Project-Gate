from __future__ import annotations

import subprocess
from pathlib import Path

from ev4_transition.external_lock import ARCHITECT_COMMIT, CE_COMMIT
from ev4_transition.producer_integration.a2c_dispatch import _outcome_record
from ev4_transition.runners.records import TimeoutPolicy, ToolExecutionOutcome, build_validator_execution_record
from ev4_transition.runners.repository_identity import inspect_checkout


def _init_repo(path: Path, origin: str) -> str:
    subprocess.run(["git", "init"], cwd=path, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    subprocess.run(["git", "config", "user.name", "PG-A2C Test"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "pg-a2c@example.invalid"], cwd=path, check=True)
    subprocess.run(["git", "remote", "add", "origin", origin], cwd=path, check=True)
    (path / "README.md").write_text("test\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-m", "test"], cwd=path, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=path, text=True).strip()


def test_checkout_identity_accepts_exact_repository_and_commit(tmp_path: Path):
    commit = _init_repo(tmp_path, "https://github.com/rezahh107/EV4-Architect-Repo.git")
    result = inspect_checkout(
        tmp_path,
        expected_repository="rezahh107/EV4-Architect-Repo",
        expected_commit=commit,
    )
    assert result["status"] == "accepted"
    assert result["commit"] == commit


def test_checkout_identity_rejects_stale_commit_and_wrong_repository(tmp_path: Path):
    commit = _init_repo(tmp_path, "git@github.com:rezahh107/EV4-Architect-Repo.git")
    stale = inspect_checkout(
        tmp_path,
        expected_repository="rezahh107/EV4-Architect-Repo",
        expected_commit="0" * 40,
    )
    wrong = inspect_checkout(
        tmp_path,
        expected_repository="rezahh107/EV4-Constructability-Engineer-Repo",
        expected_commit=commit,
    )
    assert stale["status"] == "invalid"
    assert stale["diagnostics"][0]["code"] == "PG_REPOSITORY_COMMIT_MISMATCH"
    assert wrong["status"] == "invalid"
    assert wrong["diagnostics"][0]["code"] == "PG_REPOSITORY_IDENTITY_MISMATCH"


def test_receipt_validator_evidence_excludes_machine_specific_paths():
    record = build_validator_execution_record(
        owner_repo="rezahh107/EV4-Architect-Repo",
        owner_commit=ARCHITECT_COMMIT,
        validator_path="scripts/check-architect-stage-payload.py",
        command=["/tmp/random/python", "/tmp/random/validator.py", "--file", "/tmp/random/input.json"],
        working_directory="/tmp/random/architect",
        exit_code=0,
        stdout_hash="a" * 64,
        stderr_hash="b" * 64,
        started_by="project_gate",
        timeout_policy=TimeoutPolicy(seconds=30.0),
        parsed_result_ref="/tmp/random/result.json",
    )
    outcome = ToolExecutionOutcome(
        status="accepted",
        diagnostics=[],
        execution_record=record,
        stdout_hash="a" * 64,
        stderr_hash="b" * 64,
    )
    value = _outcome_record(outcome)
    assert value["status"] == "accepted"
    assert value["execution"]["owner_commit"] == ARCHITECT_COMMIT
    assert value["execution"]["validator_path"] == "scripts/check-architect-stage-payload.py"
    assert "command" not in value["execution"]
    assert "working_directory" not in value["execution"]
    assert "/tmp/random" not in str(value)


def test_a2c_current_pins_are_distinct_immutable_commits():
    assert len(ARCHITECT_COMMIT) == 40
    assert len(CE_COMMIT) == 40
    assert ARCHITECT_COMMIT != CE_COMMIT
