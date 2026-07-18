from __future__ import annotations
import copy, json, subprocess, sys
from pathlib import Path

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
    cases = {"architect":"architect-to-ce","ce":"ce-to-builder","builder":"builder-to-responsive","responsive":"final-evidence-gate"}
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


def test_direct_c2b_dispatch_selects_c2b_lock_default(monkeypatch):
    captured = {}

    monkeypatch.setattr(intake_module, "validate_join_evidence_packet", lambda _path: {"status": "passed", "prompt_5_execution_allowed": True, "diagnostics": []})
    monkeypatch.setattr(intake_module, "intake_producer_export", lambda *args, **kwargs: {"status": "accepted", "resolved_transition": "ce-to-builder", "diagnostics": [], "handoff_allowed": False})

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
