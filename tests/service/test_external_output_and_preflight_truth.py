from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import ev4_transition.producer_integration.facade as facade
import ev4_transition.service.environment_preflight as environment_preflight
import ev4_transition.service.preflight_core as preflight_core
from ev4_transition.io.safe_publication import publish_staged_json, stage_canonical_json
from ev4_transition.service.dispatcher import run_gate_request
from ev4_transition.service.models import GateRequest, RepoPaths
from ev4_transition.service.preflight import run_preflight
from ev4_transition.ui.adapters import run_operator_check

ROOT = Path(__file__).resolve().parents[2]


def _accepted_intake(transition: str = "architect-to-ce") -> dict:
    return {
        "schema_version": "producer-emitted-transition-result.v1",
        "status": "accepted",
        "producer": {"stage": "architect", "repository": "rezahh107/EV4-Architect-Repo"},
        "resolved_transition": transition,
        "handoff_allowed": False,
        "diagnostics": [],
    }


def _publishing_transition(*args, **kwargs) -> dict:
    output = Path(kwargs["output_path"])
    receipt = Path(kwargs["receipt_path"])
    output_publication = publish_staged_json(stage_canonical_json(output, {"schema_id": "ce-input.v1", "intake_status": "complete"}))
    receipt_publication = publish_staged_json(stage_canonical_json(receipt, {"schema_version": "project-gate-a2c-receipt.v1"}))
    return {
        "schema_version": "producer-emitted-transition-result.v1",
        "status": "accepted",
        "resolved_transition": "architect-to-ce",
        "handoff_allowed": True,
        "diagnostics": [],
        "publication": {"ce_input": output_publication, "receipt": receipt_publication},
        "downstream_artifact": {"status": "published_verified", "path": str(output)},
        "receipt": {"status": "published_verified", "path": str(receipt)},
    }


def _source(tmp_path: Path) -> Path:
    source = tmp_path / "architect-project-gate.json"
    source.write_text(json.dumps({"schema_version": "producer-gate-export.v1", "handoff": {"target": "ce-intake"}}), encoding="utf-8")
    return source


def _repo_with_required_files(tmp_path: Path, field: str) -> Path:
    repo = tmp_path / field
    repo.mkdir()
    paths = preflight_core._required_files_by_field(RepoPaths(project_gate_repo_path=str(ROOT)), "architect_to_ce").get(field, ())
    for relative in paths:
        target = repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("{}\n", encoding="utf-8")
    return repo


def _accepted_inspection(*args, **kwargs):
    return SimpleNamespace(status="accepted", resolved_transition="architect-to-ce", diagnostics=[])


def test_real_gui_service_path_publishes_five_files_under_external_sibling_root(monkeypatch, tmp_path: Path) -> None:
    project_gate = tmp_path / "EV4 Shared Contracts"
    project_gate.symlink_to(ROOT, target_is_directory=True)
    output_root = tmp_path / "EV4 Project Gate Outputs"
    architect = tmp_path / "architect"
    ce = tmp_path / "ce"
    architect.mkdir()
    ce.mkdir()
    source = _source(tmp_path)
    monkeypatch.chdir(project_gate)
    monkeypatch.setattr(facade, "intake_producer_export", lambda *args, **kwargs: _accepted_intake())
    monkeypatch.setattr(facade, "transition_producer_export", _publishing_transition)

    result = run_operator_check(
        "Architect → CE",
        uploaded_file=str(source),
        project_gate_repo_path=str(project_gate),
        architect_repo_path=str(architect),
        ce_repo_path=str(ce),
        acquisition_mode="producer_emitted_gate_artifact",
        output_dir=str(output_root),
    )

    assert result.result["status"] == "accepted"
    assert len(result.download_paths) == 5
    parents = {Path(path).parent for path in result.download_paths}
    assert len(parents) == 1
    execution = next(iter(parents))
    assert execution.parent == output_root.resolve()
    assert {Path(path).name for path in result.download_paths} == {
        "ce-input.json",
        "project-gate-a2c-receipt.json",
        "result.json",
        "report.md",
        "report.html",
    }


def test_producer_preflight_truth_and_runtime_revalidation(monkeypatch, tmp_path: Path) -> None:
    source = _source(tmp_path)
    architect = _repo_with_required_files(tmp_path, "architect_repo_path")
    ce = _repo_with_required_files(tmp_path, "ce_repo_path")
    output_root = tmp_path / "external" / "outputs"
    request = GateRequest(
        transition_choice="architect_to_ce",
        acquisition_mode="producer_emitted_gate_artifact",
        input_json_path=str(source),
        repo_paths=RepoPaths(
            project_gate_repo_path=str(ROOT),
            architect_repo_path=str(architect),
            ce_repo_path=str(ce),
        ),
        output_dir=str(output_root),
    )
    monkeypatch.setattr(environment_preflight, "inspect_producer_handoff_request", _accepted_inspection)

    ready = run_preflight(request)
    assert ready.status == "ready"
    assert not output_root.exists()

    for child in sorted(ce.rglob("*"), reverse=True):
        if child.is_file():
            child.unlink()
        elif child.is_dir():
            child.rmdir()
    ce.rmdir()
    changed = run_preflight(request)
    assert changed.status == "blocked"

    monkeypatch.setattr(facade, "intake_producer_export", lambda *args, **kwargs: _accepted_intake())
    runtime = run_gate_request(request)
    assert runtime.status == "insufficient_evidence"
    assert not output_root.exists()


@pytest.mark.parametrize(
    "field,value_factory",
    [
        ("project_gate_repo_path", lambda tmp: str(tmp / "missing-pg")),
        ("architect_repo_path", lambda tmp: str(tmp / "missing-architect")),
        ("ce_repo_path", lambda tmp: str(tmp / "missing-ce")),
        ("architect_repo_path", lambda tmp: "https://github.com/rezahh107/EV4-Architect-Repo"),
    ],
)
def test_producer_preflight_blocks_missing_or_url_repository_paths(monkeypatch, tmp_path: Path, field: str, value_factory) -> None:
    source = _source(tmp_path)
    architect = _repo_with_required_files(tmp_path, "architect_repo_path")
    ce = _repo_with_required_files(tmp_path, "ce_repo_path")
    values = {
        "project_gate_repo_path": str(ROOT),
        "architect_repo_path": str(architect),
        "ce_repo_path": str(ce),
    }
    values[field] = value_factory(tmp_path)
    monkeypatch.setattr(environment_preflight, "inspect_producer_handoff_request", _accepted_inspection)
    request = GateRequest(
        transition_choice="architect_to_ce",
        acquisition_mode="producer_emitted_gate_artifact",
        input_json_path=str(source),
        repo_paths=RepoPaths(**values),
        output_dir=str(tmp_path / "outputs"),
    )
    assert run_preflight(request).status == "blocked"


def test_producer_preflight_blocks_regular_file_repo_and_output(monkeypatch, tmp_path: Path) -> None:
    source = _source(tmp_path)
    architect = _repo_with_required_files(tmp_path, "architect_repo_path")
    ce = _repo_with_required_files(tmp_path, "ce_repo_path")
    file_path = tmp_path / "regular-file"
    file_path.write_text("x", encoding="utf-8")
    monkeypatch.setattr(environment_preflight, "inspect_producer_handoff_request", _accepted_inspection)

    repo_request = GateRequest(
        transition_choice="architect_to_ce",
        acquisition_mode="producer_emitted_gate_artifact",
        input_json_path=str(source),
        repo_paths=RepoPaths(project_gate_repo_path=str(ROOT), architect_repo_path=str(file_path), ce_repo_path=str(ce)),
        output_dir=str(tmp_path / "outputs"),
    )
    assert run_preflight(repo_request).status == "blocked"

    output_request = GateRequest(
        transition_choice="architect_to_ce",
        acquisition_mode="producer_emitted_gate_artifact",
        input_json_path=str(source),
        repo_paths=RepoPaths(project_gate_repo_path=str(ROOT), architect_repo_path=str(architect), ce_repo_path=str(ce)),
        output_dir=str(file_path),
    )
    assert run_preflight(output_request).status == "blocked"


def test_cli_output_dir_is_the_selected_publication_root(monkeypatch, tmp_path: Path) -> None:
    import ev4_transition.cli as cli

    captured: dict = {}

    class Response:
        status = "accepted"

        def to_dict(self):
            return {
                "status": "accepted",
                "engine_result": {"status": "accepted", "handoff_allowed": True},
                "service_diagnostics": [],
            }

    monkeypatch.setattr(cli, "_transition_preflight", lambda *args, **kwargs: None)

    def fake_run(request):
        captured["request"] = request
        return Response()

    monkeypatch.setattr(cli, "run_gate_request", fake_run)
    exit_code = cli.main([
        "transition",
        "architect-to-ce",
        "producer.json",
        "--acquisition-mode",
        "producer_emitted_gate_artifact",
        "--project-gate-repo",
        str(tmp_path),
        "--architect-repo",
        str(tmp_path),
        "--ce-repo",
        str(tmp_path),
        "--output-dir",
        str(tmp_path / "external-output"),
    ])
    assert exit_code == 0
    assert captured["request"].output_dir == str(tmp_path / "external-output")
    assert captured["request"].output_path is None
    assert captured["request"].receipt_path is None
