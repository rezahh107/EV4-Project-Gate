from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import ev4_transition.service.json_input as service_json_input
import ev4_transition.service.repo_paths as service_repo_paths
import ev4_transition.service.reports as service_reports
from ev4_transition.service import GateRequest, RepoPaths, build_report_bundle, run_gate_request
from ev4_transition.service import dispatcher
from ev4_transition.service.capabilities import _CAPABILITY_STATUS_PATH, get_capabilities


def _repo_paths(tmp_path: Path) -> RepoPaths:
    architect = tmp_path / "architect"
    ce = tmp_path / "ce"
    builder = tmp_path / "builder"
    responsive = tmp_path / "responsive"
    project_gate = tmp_path / "project-gate"
    kernel = tmp_path / "kernel"
    for path in (architect, ce, builder, responsive, project_gate, kernel):
        path.mkdir()
    return RepoPaths(
        project_gate_repo_path=str(project_gate),
        architect_repo_path=str(architect),
        ce_repo_path=str(ce),
        builder_repo_path=str(builder),
        responsive_repo_path=str(responsive),
        kernel_repo_path=str(kernel),
    )


def _engine_result(status: str = "accepted") -> dict:
    return {"status": status, "diagnostics": [], "output": {"ok": True}}


def test_malformed_json_returns_invalid_without_crash():
    response = run_gate_request(GateRequest(transition_choice="validate_bundle", input_json_text="{"))

    assert response.status == "invalid"
    assert response.service_diagnostics[0]["code"] == "PG.SERVICE.MALFORMED_JSON"
    assert response.engine_result is None


def test_non_finite_pasted_json_constant_is_rejected():
    response = run_gate_request(GateRequest(transition_choice="validate_bundle", input_json_text='{"value": NaN}'))

    assert response.status == "invalid"
    assert response.service_diagnostics[0]["code"] == "PG.SERVICE.NON_FINITE_JSON_CONSTANT"
    assert response.service_diagnostics[0]["details"]["constant"] == "NaN"


def test_non_finite_file_json_constant_is_rejected(tmp_path: Path):
    source = tmp_path / "bundle.json"
    source.write_text('{"value": -Infinity}', encoding="utf-8")

    response = run_gate_request(GateRequest(transition_choice="validate_bundle", input_json_path=str(source)))

    assert response.status == "invalid"
    assert response.service_diagnostics[0]["code"] == "PG.SERVICE.NON_FINITE_JSON_CONSTANT"
    assert response.service_diagnostics[0]["details"]["constant"] == "-Infinity"


def test_missing_json_input_returns_invalid():
    response = run_gate_request(GateRequest(transition_choice="validate_bundle"))

    assert response.status == "invalid"
    assert response.service_diagnostics[0]["code"] == "PG.SERVICE.JSON_INPUT_MISSING"


def test_invalid_input_file_path_returns_structured_invalid_result(monkeypatch):
    def raise_value_error(self, encoding=None):
        raise ValueError("invalid path")

    monkeypatch.setattr(service_json_input.Path, "read_text", raise_value_error)

    response = run_gate_request(GateRequest(transition_choice="validate_bundle", input_json_path="invalid-path.json"))

    assert response.status == "invalid"
    assert response.service_diagnostics[0]["code"] == "PG.SERVICE.FILE_READ_ERROR"


def test_github_url_repo_path_is_rejected_as_local_path(tmp_path: Path):
    builder = tmp_path / "builder"
    builder.mkdir()
    response = run_gate_request(
        GateRequest(
            transition_choice="ce_to_builder",
            input_data={"schema": "ev4-builder-executable-package@1.0.0"},
            repo_paths=RepoPaths(
                ce_repo_path="https://github.com/rezahh107/EV4-Constructability-Engineer-Repo",
                builder_repo_path=str(builder),
            ),
        )
    )

    assert response.status == "insufficient_evidence"
    assert response.service_diagnostics[0]["code"] == "PG.SERVICE.REPO_PATH_NOT_LOCAL"


def test_invalid_repo_path_returns_insufficient_evidence(monkeypatch):
    def raise_os_error(self):
        raise OSError("permission denied")

    monkeypatch.setattr(service_repo_paths.Path, "exists", raise_os_error)

    response = run_gate_request(
        GateRequest(
            transition_choice="ce_to_builder",
            input_data={"schema": "ev4-builder-executable-package@1.0.0"},
            repo_paths=RepoPaths(ce_repo_path="/local/ce", builder_repo_path="/local/builder"),
        )
    )

    assert response.status == "insufficient_evidence"
    assert response.service_diagnostics[0]["code"] == "PG.SERVICE.REPO_PATH_INACCESSIBLE"


def test_missing_required_repo_path_returns_insufficient_evidence(tmp_path: Path):
    builder = tmp_path / "builder"
    builder.mkdir()
    response = run_gate_request(
        GateRequest(
            transition_choice="ce_to_builder",
            input_data={"schema": "ev4-builder-executable-package@1.0.0"},
            repo_paths=RepoPaths(builder_repo_path=str(builder)),
        )
    )

    assert response.status == "insufficient_evidence"
    assert response.service_diagnostics[0]["code"] == "PG.SERVICE.REPO_PATH_MISSING"


def test_validate_bundle_uses_bundle_validator_and_returns_existing_status(monkeypatch):
    calls = {}

    class FakeBundleValidator:
        def __init__(self, schema_root):
            calls["schema_root"] = schema_root

        def validate_bundle(self, payload, required_evidence_ids=None):
            calls["payload"] = payload
            calls["required_evidence_ids"] = required_evidence_ids
            return _engine_result("repair_needed")

    monkeypatch.setattr(dispatcher, "BundleValidator", FakeBundleValidator)

    payload = {"schema_version": "stage-evidence-bundle.v1"}
    response = run_gate_request(
        GateRequest(
            transition_choice="validate_bundle",
            input_data=payload,
            required_evidence_ids=["architecture_handoff"],
        )
    )

    assert calls["payload"] == payload
    assert calls["payload"] is not payload
    assert calls["required_evidence_ids"] == ["architecture_handoff"]
    assert response.status == "repair_needed"
    assert response.engine_result["status"] == "repair_needed"


def test_inspect_capabilities_returns_truth_and_does_not_mutate_file():
    before = _CAPABILITY_STATUS_PATH.read_text(encoding="utf-8")

    response = run_gate_request(GateRequest(transition_choice="inspect_capabilities"))
    capabilities = get_capabilities()
    capabilities["capabilities"]["user_interface"]["status"] = "mutated-in-test"

    after = _CAPABILITY_STATUS_PATH.read_text(encoding="utf-8")
    assert response.status == "accepted"
    assert response.engine_result["capabilities"]["schema_version"] == "ev4-project-gate-capability-status.v1"
    assert before == after
    assert get_capabilities()["capabilities"]["user_interface"]["status"] != "mutated-in-test"


def test_architect_to_ce_service_path_calls_existing_engine_boundary(monkeypatch, tmp_path: Path):
    paths = _repo_paths(tmp_path)
    calls = {}

    def fake(payload, schema_root, lock_path, architect_repo, ce_repo, validator_hooks=None):
        calls.update(payload=payload, architect_repo=architect_repo, ce_repo=ce_repo, validator_hooks=validator_hooks)
        return _engine_result("insufficient_evidence")

    monkeypatch.setattr(dispatcher, "architect_to_ce_from_local_paths", fake)
    response = run_gate_request(GateRequest(transition_choice="architect_to_ce", input_data={"stage": "architect"}, repo_paths=paths))

    assert response.status == "insufficient_evidence"
    assert calls["architect_repo"] == paths.architect_repo_path
    assert calls["ce_repo"] == paths.ce_repo_path
    assert calls["validator_hooks"] is not None


def test_ce_to_builder_service_path_calls_existing_transition_function(monkeypatch, tmp_path: Path):
    paths = _repo_paths(tmp_path)
    calls = {}

    def fake(payload, schema_root, lock_path, ce_repo, builder_repo, **kwargs):
        calls.update(payload=payload, ce_repo=ce_repo, builder_repo=builder_repo, kwargs=kwargs)
        return _engine_result("insufficient_evidence")

    monkeypatch.setattr(dispatcher, "ce_to_builder_from_local_paths", fake)
    response = run_gate_request(GateRequest(transition_choice="ce_to_builder", input_data={"schema": "ce"}, repo_paths=paths))

    assert response.status == "insufficient_evidence"
    assert calls["ce_repo"] == paths.ce_repo_path
    assert calls["builder_repo"] == paths.builder_repo_path
    assert calls["kwargs"]["require_real_evidence"] is True


def test_builder_to_responsive_service_path_calls_existing_transition_function(monkeypatch, tmp_path: Path):
    paths = _repo_paths(tmp_path)
    calls = {}

    def fake(payload, schema_root, lock_path, builder_repo, responsive_repo, **kwargs):
        calls.update(payload=payload, builder_repo=builder_repo, responsive_repo=responsive_repo, kwargs=kwargs)
        return _engine_result("repair_needed")

    monkeypatch.setattr(dispatcher, "builder_to_responsive_from_local_paths", fake)
    response = run_gate_request(GateRequest(transition_choice="builder_to_responsive", input_data={"responsive_input": {}}, repo_paths=paths))

    assert response.status == "repair_needed"
    assert calls["builder_repo"] == paths.builder_repo_path
    assert calls["responsive_repo"] == paths.responsive_repo_path


def test_final_gate_service_path_calls_existing_gate_function(monkeypatch, tmp_path: Path):
    paths = _repo_paths(tmp_path)
    calls = {}

    def fake(payload, schema_root, lock_path, project_gate_repo, responsive_repo, **kwargs):
        calls.update(payload=payload, project_gate_repo=project_gate_repo, responsive_repo=responsive_repo, kwargs=kwargs)
        return _engine_result("insufficient_evidence")

    monkeypatch.setattr(dispatcher, "final_gate_from_local_paths", fake)
    response = run_gate_request(GateRequest(transition_choice="final_gate", input_data={"responsive_output": {}}, repo_paths=paths))

    assert response.status == "insufficient_evidence"
    assert calls["project_gate_repo"] == paths.project_gate_repo_path
    assert calls["responsive_repo"] == paths.responsive_repo_path
    assert calls["kwargs"]["kernel_repo"] == paths.kernel_repo_path


def test_report_renderer_exceptions_do_not_crash_service(monkeypatch):
    def explode(_result):
        raise RuntimeError("renderer failed")

    monkeypatch.setattr(service_reports, "render_json_result", explode)
    monkeypatch.setattr(service_reports, "render_plain_summary", explode)

    bundle = build_report_bundle({"status": "not-a-real-status", "diagnostics": []})

    parsed = json.loads(bundle.canonical_json)
    assert parsed["status"] == "invalid"
    assert parsed["diagnostics"][0]["code"] == "PG.SERVICE.REPORT_JSON_RENDER_FAILED"
    assert "fallback امن" in bundle.persian_plain_summary


def test_report_bundle_generation_does_not_mutate_original_result():
    result = {
        "status": "accepted",
        "diagnostics": [],
        "progress_events": [{"step": "ui-only"}],
        "hashes": {"result_hash": "abc"},
    }
    original = deepcopy(result)

    bundle = build_report_bundle(result)

    assert result == original
    assert "accepted" in bundle.canonical_json
    assert bundle.markdown_report is not None
    assert bundle.html_report is not None


def test_service_report_generation_does_not_mutate_engine_result(monkeypatch):
    engine_result = _engine_result("accepted")
    original = deepcopy(engine_result)

    class FakeBundleValidator:
        def __init__(self, schema_root):
            self.schema_root = schema_root

        def validate_bundle(self, payload, required_evidence_ids=None):
            return engine_result

    monkeypatch.setattr(dispatcher, "BundleValidator", FakeBundleValidator)

    response = run_gate_request(GateRequest(transition_choice="validate_bundle", input_data={"schema_version": "stage-evidence-bundle.v1"}))

    assert response.engine_result == original
    assert engine_result == original


def test_report_hash_ignores_progress_only_ui_events():
    first = {"status": "accepted", "diagnostics": [], "progress_events": [{"step": 1}]}
    second = {"status": "accepted", "diagnostics": [], "progress_events": [{"step": 2}]}

    assert build_report_bundle(first).result_hash == build_report_bundle(second).result_hash


def test_unavailable_or_misconfigured_transition_does_not_return_accepted():
    response = run_gate_request(GateRequest(transition_choice="not_a_gate", input_data={}))  # type: ignore[arg-type]

    assert response.status == "invalid"
    assert response.engine_result is None
    assert response.service_diagnostics[0]["code"] == "PG.SERVICE.TRANSITION_UNKNOWN"
