from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import ev4_transition.cli as cli
from ev4_transition.ui.adapters import build_gate_request


def test_gui_and_cli_construct_equivalent_shared_requests(monkeypatch, tmp_path: Path, capsys) -> None:
    source = tmp_path / "architect-project-gate.json"
    source.write_text("{}", encoding="utf-8")
    project_gate = tmp_path / "project-gate"
    architect = tmp_path / "architect"
    ce = tmp_path / "ce"
    for path in (project_gate, architect, ce):
        path.mkdir()

    gui_request = build_gate_request(
        "Architect → CE",
        uploaded_file=str(source),
        acquisition_mode="producer_emitted_gate_artifact",
        project_gate_repo_path=str(project_gate),
        architect_repo_path=str(architect),
        ce_repo_path=str(ce),
    )
    observed = {}

    class Response:
        def to_dict(self):
            return {
                "status": "invalid",
                "transition_choice": "architect_to_ce",
                "engine_result": {"status": "invalid", "diagnostics": []},
                "service_diagnostics": [],
            }

    def fake_run(request):
        observed["request"] = request
        return Response()

    monkeypatch.setattr(cli, "run_preflight", lambda request: SimpleNamespace(status="ready", request_fingerprint="token"))
    monkeypatch.setattr(cli, "run_gate_request", fake_run)
    cli.main(
        [
            "transition",
            "architect-to-ce",
            str(source),
            "--acquisition-mode",
            "producer_emitted_gate_artifact",
            "--project-gate-repo",
            str(project_gate),
            "--architect-repo",
            str(architect),
            "--ce-repo",
            str(ce),
        ]
    )
    capsys.readouterr()
    cli_request = observed["request"]

    assert cli_request.transition_choice == gui_request.transition_choice
    assert cli_request.input_json_path == gui_request.input_json_path
    assert cli_request.acquisition_mode == gui_request.acquisition_mode
    assert cli_request.repo_paths == gui_request.repo_paths
