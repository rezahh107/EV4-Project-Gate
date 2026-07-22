from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import ev4_transition.service.environment_preflight as environment_preflight
from ev4_transition.service.models import GateRequest, RepoPaths


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_normal_producer_preflight_succeeds_without_retired_join_packet(monkeypatch, tmp_path: Path) -> None:
    project_gate = tmp_path / "project-gate"
    _write_json(project_gate / "contracts/producer-adoption/ev4-producer-adoption-set.v1.json", {})
    _write_json(project_gate / "contracts/transition-targets/ev4-transition-targets.v1.json", {})
    _write_json(project_gate / "contracts/locks/architect-to-ce-transition.v1.lock.json", {})
    assert not (project_gate / "docs/evidence/JOIN_EVIDENCE_PACKET_v1.json").exists()

    architect = tmp_path / "architect"
    ce = tmp_path / "ce"
    architect.mkdir()
    ce.mkdir()
    source = tmp_path / "producer.json"
    _write_json(source, {})

    monkeypatch.setattr(
        environment_preflight,
        "inspect_producer_handoff_request",
        lambda *args, **kwargs: SimpleNamespace(
            status="accepted",
            resolved_transition="architect-to-ce",
            diagnostics=[],
        ),
    )

    request = GateRequest(
        transition_choice="architect_to_ce",
        acquisition_mode="producer_emitted_gate_artifact",
        input_json_path=str(source),
        repo_paths=RepoPaths(
            project_gate_repo_path=str(project_gate),
            architect_repo_path=str(architect),
            ce_repo_path=str(ce),
        ),
        output_dir=str(tmp_path),
    )
    result = environment_preflight.validate_gate_request_environment(request)
    assert result.status == "ready"
    assert "docs/evidence/JOIN_EVIDENCE_PACKET_v1.json" not in environment_preflight._ROUTING_FILES
