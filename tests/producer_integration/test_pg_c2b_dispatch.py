from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from ev4_transition.canonical_json import canonical_sha256
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


def _transition_result(
    status: str = "accepted",
    *,
    lock: dict | None = None,
    execution_records: dict | None = None,
) -> dict:
    captured_lock = lock or {"schema_version": "ce-to-builder-transition-lock.v1", "files": []}
    return {
        "status": status,
        "diagnostics": [],
        "hashes": {
            "external_contract_lock": {
                "algorithm": "sha256",
                "canonicalization": "ev4-canonical-json-v1",
                "scope": "external_contract_lock",
                "value": canonical_sha256(captured_lock),
            }
        },
        "execution_records": execution_records or {"ce_validator": {"status": "accepted"}},
        "output": _builder_input() if status == "accepted" else None,
    }


def _identity(repository: str, commit: str) -> dict:
    return {"status": "accepted", "repository": repository, "commit": commit, "diagnostics": []}


def _validator_outcome(status: str = "accepted") -> SimpleNamespace:
    diagnostics = [] if status == "accepted" else [diagnostic("BUILDER_VALIDATION_FAILED", "error", "Builder validation failed.")]
    record = SimpleNamespace(
        tool_kind="validator",
        owner_repo=c2b_dispatch.BUILDER_REPO,
        owner_commit=c2b_dispatch.BUILDER_COMMIT,
        validator_path=c2b_dispatch.BUILDER_OUTPUT_VALIDATOR_PATH,
        adapter_path=None,
        input_ref=None,
        input_hash=None,
        output_ref=None,
        output_hash=None,
        parsed_result_ref="stdout:text",
        validator_after_adapter_ref=None,
        exit_code=0 if status == "accepted" else 1,
        timeout_policy=SimpleNamespace(seconds=30),
        failure_code=None if status == "accepted" else "BUILDER_VALIDATION_FAILED",
    )
    return SimpleNamespace(
        status=status,
        diagnostics=diagnostics,
        execution_record=record,
        stdout_hash="stdout-hash",
        stderr_hash="stderr-hash",
    )


def _configure_success(monkeypatch, *, execution_factory=None) -> None:
    def inspect(repo_root, *, expected_repository, expected_commit=None):
        commit = expected_commit or "project-gate-head"
        return _identity(expected_repository, commit)

    def transition(_bundle, *, schema_root, lock, ce_repo, builder_repo):
        records = execution_factory(Path(ce_repo), Path(builder_repo)) if execution_factory else None
        return _transition_result(lock=lock, execution_records=records)

    monkeypatch.setattr(c2b_dispatch, "inspect_checkout", inspect)
    monkeypatch.setattr(c2b_dispatch, "_transition_from_lock_snapshot", transition)
    monkeypatch.setattr(c2b_dispatch, "execute_builder_output_validator", lambda **kwargs: _validator_outcome())


def _run(
    tmp_path: Path,
    monkeypatch,
    *,
    output_name="builder-input.json",
    receipt_name="project-gate-c2b-receipt.json",
    create_lock=True,
):
    monkeypatch.chdir(tmp_path)
    artifact = _artifact()
    source = tmp_path / "ce-project-gate.json"
    lock = tmp_path / "c2b-lock.json"
    _write_json(source, artifact)
    if create_lock:
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
    assert receipt_payload["external_lock"]["canonical_sha256"] == result["transition_result"]["hashes"]["external_contract_lock"]["value"]
    assert "diagnostics" not in json.loads(output.read_text(encoding="utf-8"))


def _realistic_execution_records(ce_repo: Path, builder_repo: Path) -> dict:
    workspace = ce_repo.parent
    temp_root = workspace / "tmp" / "ev4-pg-ce-package-random-token"
    return {
        "ce_validator": {
            "tool_kind": "validator",
            "owner_repo": c2b_dispatch.CE_REPO,
            "owner_commit": c2b_dispatch.CE_COMMIT,
            "command": [
                str(workspace / "venv" / "bin" / "python"),
                "-m",
                "validator.engine",
                str(temp_root / "ce-builder-executable-package.json"),
                "--repo-root",
                str(ce_repo),
                "--mode",
                "package",
                "--json",
            ],
            "working_directory": str(ce_repo),
            "validator_path": "validator/engine.py",
            "exit_code": 0,
            "timeout_policy": {"seconds": 30, "kill_process_tree": False},
            "stdout_hash": "ce-stdout",
            "stderr_hash": "ce-stderr",
            "execution_record_hash": "workspace-dependent-hash",
        },
        "builder_adapter": {
            "tool_kind": "adapter",
            "owner_repo": c2b_dispatch.BUILDER_REPO,
            "owner_commit": c2b_dispatch.BUILDER_COMMIT,
            "command": [
                "node",
                str(builder_repo / "scripts" / "normalize-ce-builder-executable-package.mjs"),
                str(temp_root / "ce-builder-executable-package.json"),
            ],
            "command_or_entrypoint": [
                "node",
                str(builder_repo / "scripts" / "normalize-ce-builder-executable-package.mjs"),
                str(temp_root / "ce-builder-executable-package.json"),
            ],
            "working_directory": str(builder_repo),
            "adapter_path": "scripts/normalize-ce-builder-executable-package.mjs",
            "input_ref": "ce-builder-executable-package.json",
            "input_hash": "adapter-input-hash",
            "output_ref": "stdout:json",
            "output_hash": "adapter-output-hash",
            "validator_after_adapter_ref": "scripts/validate-package.mjs",
            "exit_code": 0,
            "timeout_policy": {"seconds": 30, "kill_process_tree": False},
            "stdout_hash": "adapter-stdout",
            "stderr_hash": "adapter-stderr",
            "execution_record_hash": "workspace-dependent-hash",
        },
    }


def test_realistic_execution_records_produce_deterministic_path_free_receipts(tmp_path: Path, monkeypatch):
    _configure_success(monkeypatch, execution_factory=_realistic_execution_records)
    first = tmp_path / "first-workspace"
    second = tmp_path / "second-workspace"
    first.mkdir()
    second.mkdir()
    _run(first, monkeypatch)
    _run(second, monkeypatch)

    first_bytes = (first / "project-gate-c2b-receipt.json").read_bytes()
    second_bytes = (second / "project-gate-c2b-receipt.json").read_bytes()
    assert first_bytes == second_bytes
    first_payload = json.loads(first_bytes)
    second_payload = json.loads(second_bytes)
    assert first_payload["receipt_id"] == second_payload["receipt_id"]
    text = first_bytes.decode("utf-8")
    assert str(first) not in text
    assert str(second) not in text
    assert "ev4-pg-ce-package-random-token" not in text
    assert "working_directory" not in text
    assert "command" not in text


def test_output_receipt_collision_fails_closed_without_publication(tmp_path: Path, monkeypatch):
    _configure_success(monkeypatch)
    result = _run(tmp_path, monkeypatch, output_name="same.json", receipt_name="same.json")
    assert result["status"] == "invalid"
    assert result["handoff_allowed"] is False
    assert result["failure_class"] == "publication_failed"
    assert not (tmp_path / "same.json").exists()


def test_blocked_transition_writes_neither_output_nor_receipt(tmp_path: Path, monkeypatch):
    _configure_success(monkeypatch)
    monkeypatch.setattr(
        c2b_dispatch,
        "_transition_from_lock_snapshot",
        lambda _bundle, *, schema_root, lock, ce_repo, builder_repo: _transition_result("insufficient_evidence", lock=lock),
    )
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
    original_verify = c2b_dispatch.verify_snapshot_unchanged
    source_checks = 0

    def verify(snapshot):
        nonlocal source_checks
        if snapshot.path.name == "ce-project-gate.json":
            source_checks += 1
            if source_checks == 2:
                raise SnapshotError("PG_A2C_INPUT_MUTATED_BEFORE_PUBLICATION", "source changed")
        return original_verify(snapshot)

    monkeypatch.setattr(c2b_dispatch, "verify_snapshot_unchanged", verify)
    result = _run(tmp_path, monkeypatch)
    assert result["status"] == "invalid"
    assert result["failure_class"] == "publication_failed"
    assert (tmp_path / "builder-input.json").exists()
    assert not (tmp_path / "project-gate-c2b-receipt.json").exists()
    assert any(item["code"] == "PG_C2B_INPUT_MUTATED_BEFORE_PUBLICATION" for item in result["diagnostics"])


def test_lock_mutation_after_transition_fails_closed_with_truthful_partial_publication(tmp_path: Path, monkeypatch):
    _configure_success(monkeypatch)

    def mutate_after_transition(_bundle, *, schema_root, lock, ce_repo, builder_repo):
        result = _transition_result(lock=lock)
        _write_json(
            tmp_path / "c2b-lock.json",
            {"schema_version": "ce-to-builder-transition-lock.v1", "files": [], "replacement": True},
        )
        return result

    monkeypatch.setattr(c2b_dispatch, "_transition_from_lock_snapshot", mutate_after_transition)
    result = _run(tmp_path, monkeypatch)
    assert result["status"] != "accepted"
    assert result["handoff_allowed"] is False
    assert result["failure_class"] == "publication_failed"
    assert (tmp_path / "builder-input.json").exists()
    assert result["publication"]["builder_input"]["state"] == "published_verified"
    assert not (tmp_path / "project-gate-c2b-receipt.json").exists()
    assert result["publication"]["receipt"]["state"] == "not_published"
    assert any(item["code"] == "PG_C2B_LOCK_MUTATED_BEFORE_RECEIPT" for item in result["diagnostics"])


def test_transition_lock_identity_mismatch_fails_before_publication(tmp_path: Path, monkeypatch):
    _configure_success(monkeypatch)

    def mismatched(_bundle, *, schema_root, lock, ce_repo, builder_repo):
        return _transition_result(lock={"schema_version": "different-lock", "files": []})

    monkeypatch.setattr(c2b_dispatch, "_transition_from_lock_snapshot", mismatched)
    result = _run(tmp_path, monkeypatch)
    assert result["status"] == "invalid"
    assert result["failure_class"] == "lock_verification_failed"
    assert not (tmp_path / "builder-input.json").exists()
    assert not (tmp_path / "project-gate-c2b-receipt.json").exists()
    assert any(item["code"] == "PG_C2B_LOCK_IDENTITY_MISMATCH" for item in result["diagnostics"])


def test_missing_or_unreadable_lock_returns_structured_invalid(tmp_path: Path, monkeypatch):
    _configure_success(monkeypatch)
    result = _run(tmp_path, monkeypatch, create_lock=False)
    assert result["status"] == "invalid"
    assert result["handoff_allowed"] is False
    assert result["downstream_artifact"]["status"] == "not_published"
    assert any(item["code"] == "PG_C2B_LOCK_READ_FAILED" for item in result["diagnostics"])
    assert not (tmp_path / "builder-input.json").exists()
    assert not (tmp_path / "project-gate-c2b-receipt.json").exists()
