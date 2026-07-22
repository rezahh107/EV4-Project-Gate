from __future__ import annotations

from dataclasses import replace
import inspect
from pathlib import Path

import pytest

import ev4_transition.service.dispatcher as dispatcher
import ev4_transition.ui.app as ui_app
from ev4_transition.service import run_gate_request, run_preflight
from ev4_transition.service.request_identity import build_gate_request_identity
from ev4_transition.ui.adapters import build_gate_request, run_operator_check
from ev4_transition.ui.app import invalidate_preflight_state, run_authoritative_preflight
from ev4_transition.ui.source_preflight import classify_source_file

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "fixtures/producer-emitted/valid/architect-export.v1.json"


def _paths(tmp_path: Path) -> tuple[Path, Path, Path]:
    architect = tmp_path / "architect"
    ce = tmp_path / "ce"
    output = tmp_path / "outputs"
    architect.mkdir()
    ce.mkdir()
    return architect, ce, output


def _request(tmp_path: Path):
    architect, ce, output = _paths(tmp_path)
    return build_gate_request(
        "Architect → CE",
        uploaded_file=str(SOURCE),
        acquisition_mode="producer_emitted_gate_artifact",
        project_gate_repo_path=str(ROOT),
        architect_repo_path=str(architect),
        ce_repo_path=str(ce),
        output_dir=str(output),
    )


@pytest.mark.parametrize(
    "kind",
    ["missing_architect", "url_architect", "file_ce", "file_output"],
)
def test_producer_invalid_environment_never_becomes_ready(tmp_path: Path, kind: str):
    architect, ce, output = _paths(tmp_path)
    if kind == "missing_architect":
        architect = tmp_path / "does-not-exist"
    elif kind == "url_architect":
        architect = Path("https://github.com/rezahh107/EV4-Architect-Repo")
    elif kind == "file_ce":
        ce = tmp_path / "ce-file"
        ce.write_text("not a checkout", encoding="utf-8")
    elif kind == "file_output":
        output.write_text("not a directory", encoding="utf-8")

    result, token = run_authoritative_preflight(
        "Architect → CE",
        "producer_emitted_gate_artifact",
        None,
        str(SOURCE),
        str(ROOT),
        str(architect),
        str(ce),
        None,
        None,
        None,
        str(output),
    )

    assert result.status == "blocked"
    assert token is None


def test_classification_never_grants_readiness_with_invalid_repositories(tmp_path: Path):
    classified = classify_source_file(str(SOURCE), str(ROOT))
    assert classified["status"] == "source_classified"

    result, token = run_authoritative_preflight(
        classified["selected_transition"],
        classified["selected_acquisition_mode"],
        None,
        str(SOURCE),
        str(ROOT),
        str(tmp_path / "missing-architect"),
        str(tmp_path / "missing-ce"),
        None,
        None,
        None,
        str(tmp_path / "outputs"),
    )
    assert result.status == "blocked"
    assert token is None


def test_effective_dispatch_mutations_change_request_fingerprint_and_irrelevant_paths_do_not(tmp_path: Path):
    request = _request(tmp_path)
    baseline = build_gate_request_identity(request).fingerprint
    alternate_source = tmp_path / "alternate.json"
    alternate_source.write_bytes(SOURCE.read_bytes())

    effective_mutations = [
        replace(request, transition_choice="ce_to_builder"),
        replace(request, acquisition_mode="pinned_owner_file_computation"),
        replace(request, input_json_path=str(alternate_source)),
        replace(request, repo_paths=replace(request.repo_paths, project_gate_repo_path=str(tmp_path))),
        replace(request, repo_paths=replace(request.repo_paths, architect_repo_path=str(tmp_path / "other-a"))),
        replace(request, repo_paths=replace(request.repo_paths, ce_repo_path=str(tmp_path / "other-ce"))),
        replace(request, output_dir=str(tmp_path / "other-output")),
        replace(request, schema_root="other-schemas"),
        replace(request, lock_path="other-lock.json"),
        replace(request, output_path="ce-input.json"),
        replace(request, receipt_path="project-gate-a2c-receipt.json"),
        replace(request, timeout_seconds=31),
        replace(request, require_real_evidence=False),
    ]
    for mutated in effective_mutations:
        assert build_gate_request_identity(mutated).fingerprint != baseline

    irrelevant_mutations = [
        replace(request, repo_paths=replace(request.repo_paths, builder_repo_path=str(tmp_path / "builder"))),
        replace(request, repo_paths=replace(request.repo_paths, responsive_repo_path=str(tmp_path / "responsive"))),
        replace(request, repo_paths=replace(request.repo_paths, kernel_repo_path=str(tmp_path / "kernel"))),
    ]
    for mutated in irrelevant_mutations:
        assert build_gate_request_identity(mutated).fingerprint == baseline


def test_stale_token_blocks_before_transition_dispatch(monkeypatch, tmp_path: Path):
    request = _request(tmp_path)
    preflight = run_preflight(request)
    assert preflight.status == "ready"
    called = {"dispatch": False}

    def forbidden_dispatch(*args, **kwargs):
        called["dispatch"] = True
        raise AssertionError("transition dispatch must not run")

    monkeypatch.setattr(dispatcher, "run_producer_handoff_request", forbidden_dispatch)
    mutated = replace(
        request,
        repo_paths=replace(request.repo_paths, architect_repo_path=str(tmp_path / "changed")),
        preflight_fingerprint=preflight.request_fingerprint,
    )
    response = run_gate_request(mutated)

    assert response.status == "invalid"
    assert response.service_diagnostics[0]["code"] in {
        "PG.SERVICE.PREFLIGHT_NOT_READY",
        "PG.SERVICE.PREFLIGHT_FINGERPRINT_STALE",
    }
    assert called["dispatch"] is False


def test_direct_ui_execution_without_token_fails_before_dispatch(monkeypatch, tmp_path: Path):
    request = _request(tmp_path)
    called = {"dispatch": False}

    def forbidden_dispatch(*args, **kwargs):
        called["dispatch"] = True
        raise AssertionError("transition dispatch must not run")

    monkeypatch.setattr(dispatcher, "run_producer_handoff_request", forbidden_dispatch)
    output = run_operator_check(
        "Architect → CE",
        uploaded_file=request.input_json_path,
        acquisition_mode=request.acquisition_mode,
        project_gate_repo_path=request.repo_paths.project_gate_repo_path,
        architect_repo_path=request.repo_paths.architect_repo_path,
        ce_repo_path=request.repo_paths.ce_repo_path,
        output_dir=request.output_dir,
    )
    assert output.result["status"] == "invalid"
    assert output.result["diagnostics"][0]["code"] == "PG.SERVICE.PREFLIGHT_FINGERPRINT_REQUIRED"
    assert called["dispatch"] is False


def test_runtime_repeats_preflight_and_binds_single_snapshot(monkeypatch, tmp_path: Path):
    request = _request(tmp_path)
    preflight = run_preflight(request)
    observed = {}

    def capture(request):
        observed["snapshot"] = request.source_snapshot
        return type("R", (), {
            "status": "invalid",
            "resolved_transition": "architect-to-ce",
            "routing": {},
            "diagnostics": [],
            "engine_result": {"status": "invalid", "diagnostics": [], "handoff_allowed": False},
            "artifact_metadata": {},
            "download_paths": [],
            "user_message_fa": "invalid",
            "next_action_fa": "stop",
        })()

    monkeypatch.setattr(dispatcher, "run_producer_handoff_request", capture)
    response = run_gate_request(replace(request, preflight_fingerprint=preflight.request_fingerprint))
    assert response.status == "invalid"
    assert observed["snapshot"] is not None
    assert observed["snapshot"].sha256_file_bytes == preflight.source_identity["sha256"]


def test_ui_invalidation_clears_token_attempt_and_run_state():
    token, run_update, _html, attempt, open_update = invalidate_preflight_state()
    assert token is None
    assert run_update == {"interactive": False}
    assert attempt is None
    assert open_update == {"interactive": False}


def test_source_bytes_changed_after_ready_blocks_before_dispatch(monkeypatch, tmp_path: Path):
    source = tmp_path / "architect-export.json"
    source.write_bytes(SOURCE.read_bytes())
    architect, ce, output = _paths(tmp_path)
    request = build_gate_request(
        "Architect → CE",
        uploaded_file=str(source),
        acquisition_mode="producer_emitted_gate_artifact",
        project_gate_repo_path=str(ROOT),
        architect_repo_path=str(architect),
        ce_repo_path=str(ce),
        output_dir=str(output),
    )
    preflight = run_preflight(request)
    assert preflight.status == "ready"
    source.write_bytes(source.read_bytes() + b"\n")
    called = {"dispatch": False}

    def forbidden_dispatch(*args, **kwargs):
        called["dispatch"] = True
        raise AssertionError("transition dispatch must not run")

    monkeypatch.setattr(dispatcher, "run_producer_handoff_request", forbidden_dispatch)
    response = run_gate_request(replace(request, preflight_fingerprint=preflight.request_fingerprint))

    assert response.status == "invalid"
    assert response.service_diagnostics[0]["code"] == "PG.SERVICE.PREFLIGHT_FINGERPRINT_STALE"
    assert called["dispatch"] is False


def test_all_authority_bearing_gui_controls_have_immediate_invalidation_wiring():
    demo = ui_app.build_demo()
    config = demo.get_config_file()
    components = config["components"]
    dependencies = config["dependencies"]

    by_label = {
        component.get("props", {}).get("label"): component["id"]
        for component in components
        if component.get("props", {}).get("label")
    }
    changed_targets = {
        target
        for dependency in dependencies
        for target in dependency.get("targets", [])
        if target[1] == "change"
    }
    expected_labels = {
        "فایل اصلی JSON / Original JSON file",
        "Transition / مسیر",
        "Acquisition mode / روش دریافت",
        "Paste JSON — فقط برای pinned_owner_file_computation",
        "Project Gate repository",
        "Architect repository",
        "Constructability Engineer repository",
        "Builder repository",
        "Responsive repository",
        "Decision Kernel repository",
        "Default output directory",
    }
    assert expected_labels <= set(by_label)
    for label in expected_labels:
        assert (by_label[label], "change") in changed_targets, label
