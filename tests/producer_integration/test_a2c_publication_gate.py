from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from ev4_transition.producer_integration import a2c_dispatch


def _accepted_outcome(owner: str, commit: str, validator: str):
    record = SimpleNamespace(
        owner_repo=owner,
        owner_commit=commit,
        validator_path=validator,
        exit_code=0,
        timeout_policy=SimpleNamespace(seconds=30),
        to_dict=lambda: {
            "owner_repo": owner,
            "owner_commit": commit,
            "validator_path": validator,
            "exit_code": 0,
        },
    )
    return SimpleNamespace(
        status="accepted",
        diagnostics=[],
        execution_record=record,
        stdout_hash="1" * 64,
        stderr_hash="2" * 64,
    )


def _configure_authorized_transition(monkeypatch):
    monkeypatch.setattr(
        a2c_dispatch,
        "inspect_checkout",
        lambda *_args, expected_repository=None, expected_commit=None, **_kwargs: {
            "status": "accepted",
            "repository": expected_repository,
            "commit": expected_commit or "project-gate-head",
            "diagnostics": [],
        },
    )
    monkeypatch.setattr(
        a2c_dispatch,
        "execute_architect_validator",
        lambda *_args, **_kwargs: _accepted_outcome(
            a2c_dispatch.ARCHITECT_REPO,
            a2c_dispatch.ARCHITECT_COMMIT,
            "architect-validator",
        ),
    )
    monkeypatch.setattr(
        a2c_dispatch,
        "execute_ce_validator",
        lambda *_args, **_kwargs: _accepted_outcome(
            a2c_dispatch.CE_REPO,
            a2c_dispatch.CE_COMMIT,
            "ce-validator",
        ),
    )

    def transition(*_args, validator_hooks, **_kwargs):
        validator_hooks.architect({})
        validator_hooks.ce({}, {})
        return {
            "status": "accepted",
            "diagnostics": [],
            "output": {
                "payload": {
                    "data": {
                        "schema_id": "ev4-ce-intake@1.1.0",
                        "intake_status": "complete",
                    }
                }
            },
        }

    monkeypatch.setattr(a2c_dispatch, "transition_from_local_paths", transition)


def _call(tmp_path: Path, *, handoff_allowed: bool):
    source = tmp_path / "architect-project-gate.json"
    source.write_text("{}", encoding="utf-8")
    return a2c_dispatch.dispatch_architect_export(
        {
            "final_stage_bundle": {"bundle_id": "A2C-1"},
            "handoff": {"allowed": handoff_allowed},
        },
        {"status": "accepted", "diagnostics": []},
        snapshot=SimpleNamespace(
            path=source,
            sha256_file_bytes="0" * 64,
        ),
        schema_root=tmp_path / "schemas",
        lock_path=tmp_path / "lock.json",
        architect_repo=tmp_path / "architect",
        ce_repo=tmp_path / "ce",
        project_gate_repo=tmp_path / "project-gate",
        output_path=tmp_path / "ce-input.json",
        receipt_path=tmp_path / "project-gate-a2c-receipt.json",
    )


def test_handoff_denied_returns_before_any_publication_work(tmp_path: Path, monkeypatch):
    _configure_authorized_transition(monkeypatch)

    def forbidden(*_args, **_kwargs):
        raise AssertionError("publication work must not run")

    monkeypatch.setattr(a2c_dispatch, "resolve_publication_paths", forbidden)
    monkeypatch.setattr(a2c_dispatch, "load_lock", forbidden)
    monkeypatch.setattr(a2c_dispatch, "stage_canonical_json", forbidden)
    monkeypatch.setattr(a2c_dispatch, "publish_staged_group", forbidden)

    result = _call(tmp_path, handoff_allowed=False)

    assert result["status"] == "insufficient_evidence"
    assert result["publication_allowed"] is False
    assert result["handoff_allowed"] is False
    assert result["downstream_artifact"] == {"status": "not_published"}
    assert result["receipt"] == {"status": "not_generated"}
    assert result["publication"]["ce_input"]["state"] == "not_published"
    assert result["publication"]["receipt"]["state"] == "not_generated"
    assert not (tmp_path / "ce-input.json").exists()
    assert not (tmp_path / "project-gate-a2c-receipt.json").exists()


def test_authorized_handoff_uses_one_grouped_publication(tmp_path: Path, monkeypatch):
    _configure_authorized_transition(monkeypatch)
    output = tmp_path / "ce-input.json"
    receipt = tmp_path / "project-gate-a2c-receipt.json"
    staged: list[SimpleNamespace] = []
    grouped_calls: list[list[SimpleNamespace]] = []

    monkeypatch.setattr(
        a2c_dispatch,
        "resolve_publication_paths",
        lambda **_kwargs: (output, receipt),
    )
    monkeypatch.setattr(a2c_dispatch, "load_lock", lambda *_args: {})
    monkeypatch.setattr(
        a2c_dispatch,
        "_build_receipt",
        lambda **_kwargs: {"receipt_id": "A2C-RECEIPT-1"},
    )

    def stage(path: Path, payload: dict):
        item = SimpleNamespace(
            final_path=path,
            temporary_path=path.with_name(f".{path.name}.tmp"),
            payload=payload,
        )
        staged.append(item)
        return item

    def publish_group(items):
        grouped_calls.append(list(items))
        return [
            {
                "path": str(item.final_path),
                "state": "published_verified",
                "sha256_file_bytes": "f" * 64,
            }
            for item in items
        ]

    monkeypatch.setattr(a2c_dispatch, "stage_canonical_json", stage)
    monkeypatch.setattr(a2c_dispatch, "verify_snapshot_unchanged", lambda *_args: None)
    monkeypatch.setattr(a2c_dispatch, "publish_staged_group", publish_group)

    result = _call(tmp_path, handoff_allowed=True)

    assert result["status"] == "accepted"
    assert result["publication_allowed"] is True
    assert result["handoff_allowed"] is True
    assert result["downstream_artifact"]["status"] == "published_verified"
    assert result["receipt"]["status"] == "published_verified"
    assert [item.final_path for item in staged] == [output, receipt]
    assert grouped_calls == [staged]


def test_group_failure_returns_invalid_without_published_artifacts(tmp_path: Path, monkeypatch):
    _configure_authorized_transition(monkeypatch)
    output = tmp_path / "ce-input.json"
    receipt = tmp_path / "project-gate-a2c-receipt.json"

    monkeypatch.setattr(
        a2c_dispatch,
        "resolve_publication_paths",
        lambda **_kwargs: (output, receipt),
    )
    monkeypatch.setattr(a2c_dispatch, "load_lock", lambda *_args: {})
    monkeypatch.setattr(
        a2c_dispatch,
        "_build_receipt",
        lambda **_kwargs: {"receipt_id": "A2C-RECEIPT-1"},
    )

    def stage(path: Path, payload: dict):
        temporary = path.with_name(f".{path.name}.tmp")
        temporary.write_text("staged", encoding="utf-8")
        return SimpleNamespace(
            final_path=path,
            temporary_path=temporary,
            payload=payload,
        )

    def fail_group(_items):
        raise a2c_dispatch.PublicationError(
            "PG.REPORT.OUTPUT_CREATED_CONCURRENTLY",
            "forced grouped publication failure",
            rollback_complete=True,
            persisted_paths=[],
            persisted_temporary_paths=[],
        )

    monkeypatch.setattr(a2c_dispatch, "stage_canonical_json", stage)
    monkeypatch.setattr(a2c_dispatch, "verify_snapshot_unchanged", lambda *_args: None)
    monkeypatch.setattr(a2c_dispatch, "publish_staged_group", fail_group)

    result = _call(tmp_path, handoff_allowed=True)

    assert result["status"] == "invalid"
    assert result["publication_allowed"] is False
    assert result["handoff_allowed"] is False
    assert result["downstream_artifact"] == {"status": "not_published"}
    assert result["receipt"] == {"status": "not_generated"}
    assert not output.exists()
    assert not receipt.exists()
    assert not list(tmp_path.glob(".*.tmp"))
    assert any(
        item["code"] == "PG.REPORT.OUTPUT_CREATED_CONCURRENTLY"
        for item in result["diagnostics"]
    )
