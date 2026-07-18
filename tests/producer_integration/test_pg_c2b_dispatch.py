from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from ev4_transition.diagnostics import diagnostic
from ev4_transition.io.secure_snapshot import SnapshotError, capture_json_snapshot
from ev4_transition.producer_integration import c2b_dispatch


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


def _artifact() -> dict:
    return {
        "export_id": "ce-export-1",
        "producer": {
            "repository": c2b_dispatch.CE_REPO,
            "commit_sha": c2b_dispatch.CE_COMMIT,
        },
        "handoff": {"allowed": True, "target": "builder-intake"},
        "final_stage_bundle": {
            "schema_version": "stage-evidence-bundle.v1",
            "bundle_id": "ce-bundle-1",
            "synthetic": False,
            "payload": {"data": {"builder_executable_package": {"schema": "ev4-builder-executable-package@1.0.0"}}},
        },
    }


def _builder_input() -> dict:
    return {
        "schema": c2b_dispatch.BUILDER_CONTEXT_SCHEMA,
        "input_authorization": {"decision": "approved"},
        "source_payload_ledger": [
            {
                "payload_name": "CE Builder Executable Package",
                "schema": "ev4-builder-executable-package@1.0.0",
                "status": "executable_ready",
                "source_ref": "ce-package-1",
            }
        ],
    }


def _transition_result(status: str = "accepted") -> dict:
    return {
        "status": status,
        "diagnostics": [],
        "execution_records": {"ce_validator": {"status": "accepted"}},
        "output": _builder_input() if status == "accepted" else None,
    }


def _identity(repository: str, commit: str) -> dict:
    return {"status": "accepted", "repository": repository, "commit": commit, "diagnostics": []}


def _validator_outcome(status: str = "accepted") -> SimpleNamespace:
    diagnostics = [] if status == "accepted" else [diagnostic("BUILDER_VALIDATION_FAILED", "error", "Builder validation failed.")]
    record = SimpleNamespace(
        owner_repo=c2b_dispatch.BUILDER_REPO,
        owner_commit=c2b_dispatch.BUILDER_COMMIT,
        validator_path=c2b_dispatch.BUILDER_OUTPUT_VALIDATOR_PATH,
        exit_code=0 if status == "accepted" else 1,
        timeout_policy=SimpleNamespace(seconds=30),
    )
    return SimpleNamespace(
        status=status,
        diagnostics=diagnostics,
        execution_record=record,
        stdout_hash="stdout-hash",
        stderr_hash="stderr-hash",
    )


def _configure_success(monkeypatch) -> None:
    def inspect(repo_root, *, expected_repository, expected_commit=None):
        commit = expected_commit or "project-gate-head"
        return _identity(expected_repository, commit)

    monkeypatch.setattr(c2b_dispatch, "inspect_checkout", inspect)
    monkeypatch.setattr(c2b_dispatch, "transition_from_local_paths", lambda *args, **kwargs: _transition_result())
    monkeypatch.setattr(c2b_dispatch, "execute_builder_output_validator", lambda **kwargs: _validator_outcome())


def _run(tmp_path: Path, monkeypatch, *, output_name="builder-input.json", receipt_name="project-gate-c2b-receipt.json"):
    monkeypatch.chdir(tmp_path)
    artifact = _artifact()
    source = tmp_path / "ce-project-gate.json"
    lock = tmp_path / "c2b-lock.json"
    _write_json(source, artifact)
    _write_json(lock, {"schema_version": "ce-to-builder-transition-lock.v1", "files": []})
    snapshot = capture_json_snapshot(source)
    return c2b_dispatch.dispatch_ce_export(
        artifact,
        {"status": "accepted", "resolved_transition": "ce-to-builder", "handoff_allowed": False, "diagnostics": []},
        snapshot=snapshot,
        schema_root=tmp_path / "schemas",
        lock_path=lock,
        ce_repo=tmp_path / "ce",
        builder_repo=tmp_path / "builder",
        project_gate_repo=tmp_path / "project-gate",
        output_path=output_name,
        receipt_path=receipt_name,
    )


def test_publishes_standalone_builder_input_and_separate_receipt(tmp_path: Path, monkeypatch):
    _configure_success(monkeypatch)
    result = _run(tmp_path, monkeypatch)
    output = tmp_path / "builder-input.json"
    receipt = tmp_path / "project-gate-c2b-receipt.json"

    assert result["status"] == "accepted"
    assert result["handoff_allowed"] is True
    assert output.exists() and receipt.exists()
    assert json.loads(output.read_text(encoding="utf-8"))["schema"] == c2b_dispatch.BUILDER_CONTEXT_SCHEMA
    receipt_payload = json.loads(receipt.read_text(encoding="utf-8"))
    assert receipt_payload["schema_version"] == c2b_dispatch.RECEIPT_SCHEMA_ID
    assert "diagnostics" not in json.loads(output.read_text(encoding="utf-8"))


def test_same_inputs_produce_same_output_and_receipt_bytes(tmp_path: Path, monkeypatch):
    _configure_success(monkeypatch)
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    _run(first, monkeypatch)
    _run(second, monkeypatch)

    assert (first / "builder-input.json").read_bytes() == (second / "builder-input.json").read_bytes()
    assert (first / "project-gate-c2b-receipt.json").read_bytes() == (second / "project-gate-c2b-receipt.json").read_bytes()


def test_output_receipt_collision_fails_closed_without_publication(tmp_path: Path, monkeypatch):
    _configure_success(monkeypatch)
    result = _run(tmp_path, monkeypatch, output_name="same.json", receipt_name="same.json")
    assert result["status"] == "invalid"
    assert result["handoff_allowed"] is False
    assert result["failure_class"] == "publication_failed"
    assert not (tmp_path / "same.json").exists()


def test_blocked_transition_writes_neither_output_nor_receipt(tmp_path: Path, monkeypatch):
    _configure_success(monkeypatch)
    monkeypatch.setattr(c2b_dispatch, "transition_from_local_paths", lambda *args, **kwargs: _transition_result("insufficient_evidence"))
    result = _run(tmp_path, monkeypatch)
    assert result["status"] == "insufficient_evidence"
    assert result["handoff_allowed"] is False
    assert not (tmp_path / "builder-input.json").exists()
    assert not (tmp_path / "project-gate-c2b-receipt.json").exists()


def test_post_write_owner_validator_failure_records_partial_publication(tmp_path: Path, monkeypatch):
    _configure_success(monkeypatch)
    monkeypatch.setattr(c2b_dispatch, "execute_builder_output_validator", lambda **kwargs: _validator_outcome("invalid"))
    result = _run(tmp_path, monkeypatch)
    assert result["status"] == "invalid"
    assert result["handoff_allowed"] is False
    assert result["failure_class"] == "owner_tool_failed"
    assert (tmp_path / "builder-input.json").exists()
    assert not (tmp_path / "project-gate-c2b-receipt.json").exists()


def test_source_mutation_before_receipt_records_partial_publication(tmp_path: Path, monkeypatch):
    _configure_success(monkeypatch)
    calls = 0

    def verify(_snapshot):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise SnapshotError("PG_A2C_INPUT_MUTATED_BEFORE_PUBLICATION", "source changed")

    monkeypatch.setattr(c2b_dispatch, "verify_snapshot_unchanged", verify)
    result = _run(tmp_path, monkeypatch)
    assert result["status"] == "invalid"
    assert result["failure_class"] == "publication_failed"
    assert (tmp_path / "builder-input.json").exists()
    assert not (tmp_path / "project-gate-c2b-receipt.json").exists()
    assert any(item["code"] == "PG_C2B_INPUT_MUTATED_BEFORE_PUBLICATION" for item in result["diagnostics"])
