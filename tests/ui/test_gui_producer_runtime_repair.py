from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import ev4_transition.service.dispatcher as dispatcher
import ev4_transition.ui.source_preflight as source_preflight
from ev4_transition.service.models import GateRequest, RepoPaths
from ev4_transition.ui.adapters import build_gate_request, run_operator_check
from ev4_transition.ui.app import operator_panel_css
from ev4_transition.ui.operator_settings import default_settings, load_settings, reset_settings, save_settings
from ev4_transition.ui.source_preflight import classify_source_file


def test_no_parsed_json_payload_access_remains():
    import inspect
    import ev4_transition.ui.adapters as adapters

    assert "parsed.payload" not in inspect.getsource(adapters)


def test_producer_mode_requires_original_file(tmp_path: Path):
    output = run_operator_check(
        "Architect → CE",
        pasted_json='{"schema_version":"producer-gate-export.v1"}',
        acquisition_mode="producer_emitted_gate_artifact",
        output_dir=tmp_path,
    )

    assert output.result["status"] == "invalid"
    assert output.result["diagnostics"][0]["code"] == "PG.UI.PRODUCER_SOURCE_FILE_REQUIRED"
    assert "فایل اصلی" in output.result["diagnostics"][0]["message"]


def test_gui_builds_complete_producer_request(tmp_path: Path):
    source = tmp_path / "architect-project-gate.json"
    source.write_text('{"schema_version":"producer-gate-export.v1"}', encoding="utf-8")
    request = build_gate_request(
        "Architect → CE",
        uploaded_file=str(source),
        acquisition_mode="producer_emitted_gate_artifact",
        project_gate_repo_path=r"E:\GitHub\EV4 Shared Contracts",
        architect_repo_path=r"E:\GitHub\EV4-Architect-Repo",
        ce_repo_path=r"E:\GitHub\EV4 Constructability Engineer Repo",
        builder_repo_path=r"E:\GitHub\Builder Assistant",
        responsive_repo_path=r"E:\GitHub\EV4 Responsive Architect",
        output_dir=r"E:\GitHub\EV4 Project Gate Outputs",
    )

    assert request.input_json_path == str(source)
    assert request.acquisition_mode == "producer_emitted_gate_artifact"
    assert request.repo_paths.project_gate_repo_path.endswith("EV4 Shared Contracts")
    assert request.repo_paths.ce_repo_path.endswith("EV4 Constructability Engineer Repo")
    assert request.output_dir.endswith("EV4 Project Gate Outputs")


def test_shared_service_dispatches_producer_request(monkeypatch, tmp_path: Path):
    source = tmp_path / "producer.json"
    source.write_text('{"schema_version":"producer-gate-export.v1"}', encoding="utf-8")
    captured = {}

    def fake_run(request):
        captured["request"] = request
        return SimpleNamespace(
            status="accepted",
            resolved_transition="architect-to-ce",
            routing={},
            diagnostics=[],
            engine_result={"status": "accepted", "handoff_allowed": True, "diagnostics": []},
            artifact_metadata={},
            download_paths=[],
            user_message_fa="accepted",
            next_action_fa="done",
        )

    monkeypatch.setattr(dispatcher, "run_producer_handoff_request", fake_run)
    response = dispatcher.run_gate_request(
        GateRequest(
            transition_choice="architect_to_ce",
            acquisition_mode="producer_emitted_gate_artifact",
            input_json_path=str(source),
            repo_paths=RepoPaths(project_gate_repo_path=str(tmp_path), architect_repo_path=str(tmp_path), ce_repo_path=str(tmp_path)),
        )
    )

    assert response.status == "accepted"
    assert captured["request"].source_path == str(source)
    assert captured["request"].repo_paths.ce_repo_path == str(tmp_path)


def test_source_classification_visibly_selects_a2c(monkeypatch, tmp_path: Path):
    source = tmp_path / "architect-project-gate.json"
    source.write_text('{"schema_version":"producer-gate-export.v1"}', encoding="utf-8")

    monkeypatch.setattr(
        source_preflight,
        "inspect_producer_handoff_request",
        lambda *args, **kwargs: SimpleNamespace(
            to_dict=lambda: {
                "status": "accepted",
                "resolved_transition": "architect-to-ce",
                "routing": {"producer_stage": "architect", "target_stage": "ce"},
                "diagnostics": [],
            }
        ),
    )
    result = classify_source_file(str(source), str(tmp_path))

    assert result["status"] == "source_classified"
    assert result["source_schema"] == "producer-gate-export.v1"
    assert result["selected_transition"] == "Architect → CE"
    assert result["selected_acquisition_mode"] == "producer_emitted_gate_artifact"
    assert "Producer Gate Export شناسایی شد" in result["message_fa"]


def test_result_artifact_is_rejected_as_source(tmp_path: Path):
    source = tmp_path / "result.json"
    source.write_text(json.dumps({"schema_version": "ev4-project-gate-ui-result.v1"}), encoding="utf-8")

    result = classify_source_file(str(source), str(tmp_path))

    assert result["status"] == "invalid"
    assert result["diagnostics"][0]["code"] == "PG.UI.RESULT_ARTIFACT_USED_AS_SOURCE"


def test_operator_settings_round_trip_and_reset(monkeypatch, tmp_path: Path):
    path = tmp_path / "operator-settings.json"
    defaults = default_settings()
    defaults["project_gate_repo_path"] = r"E:\GitHub\EV4 Shared Contracts"
    defaults["default_output_directory"] = r"E:\GitHub\EV4 Project Gate Outputs"

    save_settings(defaults, path)
    loaded = load_settings(path)
    reset = reset_settings(path)

    assert loaded["project_gate_repo_path"] == r"E:\GitHub\EV4 Shared Contracts"
    assert loaded["default_acquisition_mode"] == "producer_emitted_gate_artifact"
    assert not path.exists()
    assert reset == default_settings()


def test_operator_panel_includes_gui_first_controls():
    css = operator_panel_css()

    assert "input[type=\"radio\"]" in css
    assert "--ev4-button-primary-hover-bg" in css
    assert "body.dark .ev4-header" in css
