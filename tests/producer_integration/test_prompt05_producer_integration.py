from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

from ev4_transition import cli as cli_module
from ev4_transition.producer_integration import intake as intake_module
from ev4_transition.producer_integration.join_preflight import validate_join_evidence_packet
from ev4_transition.producer_integration.registry import validate_adoption_registry, git_blob_sha256
from ev4_transition.producer_integration.intake import intake_producer_export, transition_producer_export


def load(path: str):
    return json.loads(Path(path).read_text())


def test_join_packet_preflight_passes_repaired_packet():
    result = validate_join_evidence_packet("docs/evidence/JOIN_EVIDENCE_PACKET_v1.json")
    assert result["status"] == "passed"
    assert result["prompt_5_execution_allowed"] is True


def test_registry_is_valid_and_uses_merged_runtime_pins():
    result = validate_adoption_registry()
    assert result["status"] == "valid", result
    reg = load("contracts/producer-adoption/ev4-producer-adoption-set.v1.json")
    for producer in reg["producers"]:
        assert producer["runtime_pin"]["merged_commit_sha"] != producer["pr_head_sha"]


def test_git_blob_unavailable_is_insufficient_not_mismatch(tmp_path):
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, stdout=subprocess.PIPE)
    result = git_blob_sha256(tmp_path, "0123456789abcdef0123456789abcdef01234567", "missing.txt")
    assert result["status"] == "insufficient_evidence"
    assert result["diagnostic"]["code"] == "PG-P05-EXACT-BLOB-UNAVAILABLE"


def test_valid_producer_emitted_intakes_do_not_mutate():
    for stage in ["architect", "ce", "builder", "responsive"]:
        artifact = load(f"fixtures/producer-emitted/valid/{stage}-export.v1.json")
        before = copy.deepcopy(artifact)
        result = intake_producer_export(artifact)
        assert artifact == before
        assert result["status"] == "accepted", result
        assert result["acquisition_mode"] == "producer_emitted_gate_artifact"


def test_all_transition_targets_resolve_at_intake_boundary():
    cases = {"architect": "architect-to-ce", "ce": "ce-to-builder", "builder": "builder-to-responsive", "responsive": "final-evidence-gate"}
    for stage, transition in cases.items():
        result = intake_producer_export(load(f"fixtures/producer-emitted/valid/{stage}-export.v1.json"), transition_name=transition)
        assert result["status"] == "accepted", result
        assert result["resolved_transition"] == transition


def test_architect_dispatch_without_immutable_runtime_evidence_fails_closed():
    result = transition_producer_export(
        "architect-to-ce",
        load("fixtures/producer-emitted/valid/architect-export.v1.json"),
    )
    assert result["status"] == "insufficient_evidence"
    assert result["handoff_allowed"] is False
    assert result["producer_validation"]["official_validator_status"] == "not_run"
    assert any(d["code"] == "PG_A2C_RUNTIME_EVIDENCE_REQUIRED" for d in result["diagnostics"])


def test_c2b_dispatch_without_immutable_runtime_evidence_fails_closed():
    result = transition_producer_export(
        "ce-to-builder",
        load("fixtures/producer-emitted/valid/ce-export.v1.json"),
    )
    assert result["status"] == "insufficient_evidence"
    assert result["handoff_allowed"] is False
    assert result["downstream_artifact"]["status"] == "not_published"
    assert any(d["code"] == "PG_C2B_RUNTIME_EVIDENCE_REQUIRED" for d in result["diagnostics"])


def _configure_direct_dispatch(monkeypatch, resolved_transition: str):
    monkeypatch.setattr(intake_module, "validate_join_evidence_packet", lambda _path: {"status": "passed", "prompt_5_execution_allowed": True, "diagnostics": []})
    monkeypatch.setattr(
        intake_module,
        "intake_producer_export",
        lambda *args, **kwargs: {
            "status": "accepted",
            "resolved_transition": resolved_transition,
            "diagnostics": [],
            "handoff_allowed": False,
        },
    )
    monkeypatch.setattr(intake_module, "_operational_truth_failure", lambda *args, **kwargs: None)


def test_direct_c2b_dispatch_uses_c2b_defaults_when_paths_omitted(monkeypatch):
    captured = {}
    _configure_direct_dispatch(monkeypatch, "ce-to-builder")

    from ev4_transition.producer_integration import c2b_dispatch

    def capture_dispatch(*args, **kwargs):
        captured.update(kwargs)
        return {"status": "accepted", "diagnostics": [], "handoff_allowed": True}

    monkeypatch.setattr(c2b_dispatch, "dispatch_ce_export", capture_dispatch)
    result = transition_producer_export(
        "ce-to-builder",
        {},
        snapshot=object(),
        ce_repo="ce-repo",
        builder_repo="builder-repo",
    )
    assert result["status"] == "accepted"
    assert captured["lock_path"] == "contracts/locks/ce-to-builder-transition.v1.lock.json"
    assert captured["output_path"] == "builder-input.json"
    assert captured["receipt_path"] == "project-gate-c2b-receipt.json"


def test_direct_c2b_dispatch_preserves_explicit_custom_paths(monkeypatch):
    captured = {}
    _configure_direct_dispatch(monkeypatch, "ce-to-builder")

    from ev4_transition.producer_integration import c2b_dispatch

    def capture_dispatch(*args, **kwargs):
        captured.update(kwargs)
        return {"status": "accepted", "diagnostics": [], "handoff_allowed": True}

    monkeypatch.setattr(c2b_dispatch, "dispatch_ce_export", capture_dispatch)
    transition_producer_export(
        "ce-to-builder",
        {},
        snapshot=object(),
        ce_repo="ce-repo",
        builder_repo="builder-repo",
        lock_path="custom-lock.json",
        output_path="custom-builder.json",
        receipt_path="custom-receipt.json",
    )
    assert captured["lock_path"] == "custom-lock.json"
    assert captured["output_path"] == "custom-builder.json"
    assert captured["receipt_path"] == "custom-receipt.json"


def test_direct_a2c_dispatch_preserves_a2c_defaults(monkeypatch):
    captured = {}
    _configure_direct_dispatch(monkeypatch, "architect-to-ce")

    from ev4_transition.producer_integration import a2c_dispatch

    def capture_dispatch(*args, **kwargs):
        captured.update(kwargs)
        return {"status": "accepted", "diagnostics": [], "handoff_allowed": True}

    monkeypatch.setattr(a2c_dispatch, "dispatch_architect_export", capture_dispatch)
    transition_producer_export(
        "architect-to-ce",
        {},
        snapshot=object(),
        architect_repo="architect-repo",
        ce_repo="ce-repo",
    )
    assert captured["lock_path"] == "contracts/locks/architect-to-ce-transition.v1.lock.json"
    assert captured["output_path"] == "ce-input.json"
    assert captured["receipt_path"] == "project-gate-a2c-receipt.json"


def test_cli_producer_emitted_c2b_routes_through_shared_service(tmp_path, monkeypatch):
    captured = {}
    ce_repo = tmp_path / "ce"
    builder_repo = tmp_path / "builder"
    ce_repo.mkdir()
    builder_repo.mkdir()
    source = tmp_path / "ce-project-gate.json"
    source.write_text("{}", encoding="utf-8")

    class Response:
        def to_dict(self):
            return {
                "status": "accepted",
                "transition_choice": "ce_to_builder",
                "engine_result": {"status": "accepted", "diagnostics": [], "handoff_allowed": True},
                "service_diagnostics": [],
            }

    def fake_run_gate_request(request):
        captured["request"] = request
        return Response()

    monkeypatch.setattr(cli_module, "run_preflight", lambda request: SimpleNamespace(status="ready", request_fingerprint="token"))
    monkeypatch.setattr(cli_module, "run_gate_request", fake_run_gate_request)
    monkeypatch.setattr(cli_module, "_emit", lambda payload, fmt: None)

    exit_code = cli_module.main(
        [
            "transition",
            "ce-to-builder",
            str(source),
            "--acquisition-mode",
            "producer_emitted_gate_artifact",
            "--project-gate-repo",
            str(Path(__file__).resolve().parents[2]),
            "--ce-repo",
            str(ce_repo),
            "--builder-repo",
            str(builder_repo),
        ]
    )
    assert exit_code == 0
    request = captured["request"]
    assert request.transition_choice == "ce_to_builder"
    assert request.acquisition_mode == "producer_emitted_gate_artifact"
    assert request.input_json_path == str(source)
    assert request.repo_paths.ce_repo_path == str(ce_repo)
    assert request.repo_paths.builder_repo_path == str(builder_repo)


def test_invalid_modes_and_targets_fail_closed():
    expected = {
        "missing-acquisition-mode": "PG-P05-ACQUISITION-MODE-MISSING",
        "evidence-mixing": "PG-P05-EVIDENCE-MIXING-FORBIDDEN",
        "silent-fallback": "PG-P05-SILENT-FALLBACK-FORBIDDEN",
        "unknown-target": "PG-P05-HANDOFF-TARGET-INVALID",
        "wrong-repository": "PG-P05-PRODUCER-REGISTRY-INVALID",
        "pr-head-runtime-pin": "PG-P05-PRODUCER-REGISTRY-INVALID",
    }
    for name, code in expected.items():
        result = intake_producer_export(load(f"fixtures/producer-emitted/invalid/{name}.v1.json"))
        assert result["status"] == "invalid"
        assert any(d["code"] == code for d in result["diagnostics"]), result


def test_cli_producer_mode_requires_exact_owner_checkouts():
    proc = subprocess.run([sys.executable, "-m", "ev4_transition.cli", "transition", "architect-to-ce", "fixtures/producer-emitted/valid/architect-export.v1.json", "--acquisition-mode", "producer_emitted_gate_artifact"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert proc.returncode == 2, proc.stderr + proc.stdout
    payload = json.loads(proc.stdout)
    assert payload["status"] == "insufficient_evidence"
    assert any(d["code"] == "CLI_LOCAL_PATH_REQUIRED" for d in payload["diagnostics"])


def write_json(path: Path, payload):
    path.write_text(json.dumps(payload, sort_keys=True))


def test_transition_runtime_enforces_join_packet_preflight(tmp_path):
    packet = tmp_path / "not-ready.json"
    write_json(packet, {"prompt_5_ready": False, "blocking_insufficient_evidence": ["x"], "ready_decision": "blocked"})
    result = transition_producer_export(
        "architect-to-ce",
        load("fixtures/producer-emitted/valid/architect-export.v1.json"),
        join_packet_path=packet,
    )
    assert result["status"] == "invalid"
    assert any(d["code"] == "PG-P05-JOIN-EVIDENCE-NOT-READY" for d in result["diagnostics"])
    assert result["join_evidence_preflight"]["prompt_5_execution_allowed"] is False


def test_adoption_registry_malformed_inputs_return_invalid_without_traceback(tmp_path):
    cases = [
        ["not", "object"],
        {"schema_id": "ev4-producer-adoption-set.v1", "prompt_0": {}, "producers": ["bad"]},
        {"schema_id": "ev4-producer-adoption-set.v1", "prompt_0": {}, "producers": [{"stage": "architect", "runtime_pin": [], "artifacts": ["bad"]}]},
        {"schema_id": "ev4-producer-adoption-set.v1", "prompt_0": {}, "producers": [{"stage": "architect", "runtime_pin": {}, "artifacts": [{"role": 7}]}]},
    ]
    for index, payload in enumerate(cases):
        path = tmp_path / f"registry-{index}.json"
        write_json(path, payload)
        result = validate_adoption_registry(path)
        assert result["status"] == "invalid"
        assert result["diagnostics"]
        assert all(d["code"] == "PG-P05-PRODUCER-REGISTRY-INVALID" for d in result["diagnostics"] if d["path"] != "$.producers[0].runtime_pin.merged_commit_sha")
