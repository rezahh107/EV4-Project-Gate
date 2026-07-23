from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

import ev4_transition.service.dispatcher as dispatcher
from ev4_transition.io.secure_snapshot import SnapshotError, capture_json_snapshot, validate_json_snapshot
from ev4_transition.service import GateRequest, RepoPaths, repository_path_matrix, run_gate_request
from ev4_transition.service.preflight_core import PreflightResult
from ev4_transition.service.transition_contracts import contract_for_service

ROOT = Path(__file__).resolve().parents[2]


def _authorize_unit_dispatch(monkeypatch) -> None:
    def ready(request: GateRequest) -> PreflightResult:
        return PreflightResult(
            "ready",
            str(request.transition_choice),
            [],
            "ready",
            "unit-test-fingerprint",
            {},
        )

    monkeypatch.setattr(dispatcher, "run_preflight", ready)


def test_repository_path_matrix_has_complete_final_gate_contract() -> None:
    contract = contract_for_service("final_gate")
    assert contract.required_repo_fields == (
        "project_gate_repo_path",
        "responsive_repo_path",
        "kernel_repo_path",
    )
    row = next(item for item in repository_path_matrix() if item["service_choice"] == "final_gate")
    assert row["required_repo_fields"] == contract.required_repo_fields
    assert contract_for_service("architect_to_ce").producer_required_repo_fields == (
        "project_gate_repo_path", "architect_repo_path", "ce_repo_path"
    )


def test_snapshot_and_file_requests_use_same_producer_service_authority(monkeypatch, tmp_path: Path) -> None:
    source = tmp_path / "source.json"
    source.write_text('{"schema_version":"producer-gate-export.v1"}', encoding="utf-8")
    snapshot = capture_json_snapshot(source)
    observed = []

    def fake_run(request):
        observed.append(request)
        return SimpleNamespace(
            status="invalid",
            resolved_transition=None,
            routing={},
            diagnostics=[],
            engine_result={"status": "invalid", "diagnostics": []},
            artifact_metadata={},
            download_paths=[],
            user_message_fa="invalid",
            next_action_fa="inspect",
        )

    _authorize_unit_dispatch(monkeypatch)
    monkeypatch.setattr(dispatcher, "run_producer_handoff_request", fake_run)
    base = dict(
        transition_choice="architect_to_ce",
        acquisition_mode="producer_emitted_gate_artifact",
        repo_paths=RepoPaths(project_gate_repo_path=str(ROOT), architect_repo_path=str(tmp_path), ce_repo_path=str(tmp_path)),
    )
    run_gate_request(GateRequest(input_json_path=str(source), **base))
    run_gate_request(GateRequest(input_json_path=str(source), input_snapshot=snapshot, **base))

    assert len(observed) == 2
    assert observed[0].source_snapshot is not None
    assert observed[1].source_snapshot is snapshot
    assert observed[0].source_snapshot.sha256_file_bytes == observed[1].source_snapshot.sha256_file_bytes
    assert observed[0].repo_paths == observed[1].repo_paths
    assert observed[0].source_path == observed[1].source_path == str(source)


def test_supplied_snapshot_rejects_changed_source_before_routing(tmp_path: Path) -> None:
    source = tmp_path / "source.json"
    source.write_text('{"schema_version":"producer-gate-export.v1"}', encoding="utf-8")
    snapshot = capture_json_snapshot(source)
    source.write_text('{"schema_version":"producer-gate-export.v1","changed":true}', encoding="utf-8")

    response = run_gate_request(
        GateRequest(
            transition_choice="architect_to_ce",
            acquisition_mode="producer_emitted_gate_artifact",
            input_json_path=str(source),
            input_snapshot=snapshot,
            repo_paths=RepoPaths(project_gate_repo_path=str(ROOT), architect_repo_path=str(tmp_path), ce_repo_path=str(tmp_path)),
        )
    )

    assert response.status == "invalid"
    assert any(item["code"] in {"PG_A2C_INPUT_REPLACED_BEFORE_PUBLICATION", "PG_A2C_INPUT_MUTATED_BEFORE_PUBLICATION"} for item in response.service_diagnostics)


def test_supplied_snapshot_digest_cannot_be_forged(tmp_path: Path) -> None:
    source = tmp_path / "source.json"
    source.write_text('{"schema_version":"producer-gate-export.v1"}', encoding="utf-8")
    snapshot = capture_json_snapshot(source)
    forged = replace(snapshot, sha256_file_bytes="0" * 64)

    with pytest.raises(SnapshotError, match="digest") as captured:
        validate_json_snapshot(forged, expected_source_path=source)
    assert captured.value.code == "PG_A2C_INPUT_SNAPSHOT_HASH_MISMATCH"


def test_wrong_project_gate_path_is_not_bypassed_by_supplied_snapshot(tmp_path: Path) -> None:
    source = tmp_path / "source.json"
    source.write_text('{"schema_version":"producer-gate-export.v1"}', encoding="utf-8")
    snapshot = capture_json_snapshot(source)
    wrong = tmp_path / "wrong-project-gate"
    wrong.mkdir()

    response = run_gate_request(
        GateRequest(
            transition_choice="architect_to_ce",
            acquisition_mode="producer_emitted_gate_artifact",
            input_json_path=str(source),
            input_snapshot=snapshot,
            repo_paths=RepoPaths(project_gate_repo_path=str(wrong), architect_repo_path=str(tmp_path), ce_repo_path=str(tmp_path)),
        )
    )

    assert response.status == "invalid"
    assert any(item["code"] == "PG_INT_PROJECT_GATE_FILES_UNAVAILABLE" for item in response.service_diagnostics)


def test_service_package_contains_no_snapshot_specific_dispatch_shortcut() -> None:
    for relative in ("src/ev4_transition/service/__init__.py", "src/ev4_transition/service/dispatcher.py"):
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert "transition_producer_export" not in text
        assert "_dispatcher._run_producer_emitted_request =" not in text
