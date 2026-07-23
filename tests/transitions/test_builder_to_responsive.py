from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from jsonschema import Draft202012Validator

from ev4_transition.canonical_json import bytes_sha256, canonical_sha256
from ev4_transition.contract_source import LocalCheckoutContractSource
from ev4_transition.transitions.builder_to_responsive import (
    BUILDER_REPO,
    EXPECTED_BUILDER_TO_RESPONSIVE_DEPENDENCIES,
    RESPONSIVE_INPUT_SCHEMA,
    RESPONSIVE_REPO,
    TRANSITION_ID,
    BuilderToResponsiveTransitionConfig,
    transition_builder_to_responsive,
    verify_builder_to_responsive_lock,
)

ROOT = Path(__file__).resolve().parents[2]


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _json_file(path: Path, value: dict) -> str:
    _write(path, json.dumps(value, ensure_ascii=False, sort_keys=True))
    return bytes_sha256(path.read_bytes())


def _schema(marker: str, schema_id: str | None = None) -> dict:
    properties = {"schema": {"type": "string"}}
    if schema_id:
        properties["schema"] = {"const": schema_id}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": ["schema"],
        "properties": properties,
        "additionalProperties": True,
        "marker": marker,
    }


def _repos(tmp_path: Path):
    builder = tmp_path / "builder"
    responsive = tmp_path / "responsive"
    for dep in EXPECTED_BUILDER_TO_RESPONSIVE_DEPENDENCIES.values():
        root = builder if dep.repository == BUILDER_REPO else responsive
        if dep.path.endswith(".mjs"):
            text = f"// {dep.identity_marker}\nconsole.log('validation passed');\n"
        elif dep.path.endswith(".py"):
            text = f"# {dep.identity_marker}\nprint('boundary ok')\n"
        elif dep.path.endswith(".json"):
            schema_id = dep.contract_or_schema_id if dep.role != "responsive_input_schema" else RESPONSIVE_INPUT_SCHEMA
            text = json.dumps(_schema(dep.identity_marker, schema_id))
        else:
            text = f"{dep.identity_marker}\n"
        _write(root / dep.path, text)
    source = LocalCheckoutContractSource({BUILDER_REPO: builder, RESPONSIVE_REPO: responsive})
    lock = {"schema_version": "builder-to-responsive-transition-lock.v1", "transition_id": TRANSITION_ID, "files": []}
    for dep in EXPECTED_BUILDER_TO_RESPONSIVE_DEPENDENCIES.values():
        root = builder if dep.repository == BUILDER_REPO else responsive
        content = (root / dep.path).read_bytes()
        lock["files"].append({
            "role": dep.role,
            "repository": dep.repository,
            "accepted_commit": dep.accepted_commit,
            "path": dep.path,
            "contract_or_schema_id": dep.contract_or_schema_id,
            "sha256_file_bytes": bytes_sha256(content),
        })
    return builder, responsive, source, lock


def _packet(builder: Path) -> dict:
    files = {
        "builder_output": ("evidence/builder-output.json", {"schema": "ev4-builder-context-package@1.0.0", "selected_candidate_id": "ARCH-FAM-C"}),
        "action_batch": ("evidence/action-batch.json", {"schema": "ev4-action-batch@1.0.0", "selected_candidate_id": "ARCH-FAM-C", "actions": []}),
        "execution_evidence": ("evidence/execution-evidence.json", {"schema": "ev4-real-elementor-execution-evidence@1.0.0", "selected_candidate_id": "ARCH-FAM-C", "builder_session_ref": "SESSION-1", "source_package_ref": "PACKAGE-1"}),
        "layout_check": ("evidence/layout-check.json", {"schema": "ev4-layout-check@0.1.0", "selected_candidate_id": "ARCH-FAM-C"}),
        "completion_gate": ("evidence/completion-gate.json", {"schema": "ev4-completion-gate@0.1.0", "selected_candidate_id": "ARCH-FAM-C", "source_package_ref": "PACKAGE-1", "layout_check_ref": "evidence/layout-check.json"}),
        "desktop": ("evidence/desktop.json", {"evidence_ref": "desktop-proof", "viewport": "desktop", "status": "confirmed"}),
        "tablet": ("evidence/tablet.json", {"evidence_ref": "tablet-proof", "viewport": "tablet", "status": "confirmed"}),
        "mobile": ("evidence/mobile.json", {"evidence_ref": "mobile-proof", "viewport": "mobile", "status": "confirmed"}),
    }
    bindings: dict[str, dict] = {}
    for slot, (ref, value) in files.items():
        digest = _json_file(builder / ref, value)
        subject = {
            "builder_output": ref,
            "action_batch": ref,
            "execution_evidence": ref,
            "layout_check": ref,
            "completion_gate": ref,
            "desktop": "desktop-proof",
            "tablet": "tablet-proof",
            "mobile": "mobile-proof",
        }[slot]
        bindings[slot] = {"artifact_ref": ref, "artifact_sha256": digest, "subject_ref": subject}
    responsive_input = {
        "schema": RESPONSIVE_INPUT_SCHEMA,
        "source_packet_ref": "PACKAGE-1",
        "project_gate_ref": {"gate_id": "PG-B2R-1", "gate_status": "verified", "gate_hash": "hash"},
        "selected_candidate_id": "ARCH-FAM-C",
        "builder_output_ref": {"output_id": "OUT-1", "artifact_ref": files["builder_output"][0], "artifact_hash": bindings["builder_output"]["artifact_sha256"]},
        "builder_evidence": {
            "action_batch_ref": files["action_batch"][0],
            "execution_evidence_ref": files["execution_evidence"][0],
            "layout_check_ref": files["layout_check"][0],
            "completion_gate_ref": files["completion_gate"][0],
        },
        "viewport_evidence": {
            "desktop": {"evidence_ref": "desktop-proof", "evidence_status": "provided"},
            "tablet": {"evidence_ref": "tablet-proof", "evidence_status": "provided"},
            "mobile": {"evidence_ref": "mobile-proof", "evidence_status": "provided"},
        },
        "responsive_intake_decision": {"intake_allowed": True, "reason": "verified", "claim_boundary": "input eligibility only; not responsive correctness evidence"},
        "forbidden_claims": [
            "production_ready", "release_ready", "pixel_perfect", "live_render_validated",
            "export_json_validated", "accessibility_passed", "responsive_correctness_validated",
            "ci_success_as_frontend_evidence",
        ],
    }
    return {
        "responsive_input": responsive_input,
        "evidence_subject": {
            "builder_session_ref": "SESSION-1",
            "source_package_ref": "PACKAGE-1",
            "action_set_digest": canonical_sha256(files["action_batch"][1]),
        },
        "evidence_bindings": bindings,
    }


def _config(lock: dict, builder: Path | None, responsive: Path | None) -> BuilderToResponsiveTransitionConfig:
    return BuilderToResponsiveTransitionConfig(ROOT / "schemas", lock, builder, responsive)


def _codes(result: dict) -> set[str]:
    return {item["code"] for item in result["diagnostics"]}


def _run(tmp_path: Path):
    builder, responsive, source, lock = _repos(tmp_path)
    packet = _packet(builder)
    return transition_builder_to_responsive(packet, source, _config(lock, builder, responsive)), packet, builder, responsive, source, lock


def test_source_bound_owner_validated_evidence_is_accepted(tmp_path: Path):
    result, _, _, _, _, _ = _run(tmp_path)
    assert result["status"] == "accepted", result
    assert result["accepted_requires"]["evidence_hashes_verified"] is True
    assert result["accepted_requires"]["owner_validators_passed"] is True
    assert result["accepted_requires"]["viewport_evidence_present"] is True
    assert all(result["evidence_resolutions"][name]["classification"] == "real_verified" for name in ("desktop", "tablet", "mobile"))


def test_reference_strings_without_bindings_are_insufficient(tmp_path: Path):
    builder, responsive, source, lock = _repos(tmp_path)
    packet = _packet(builder)
    packet.pop("evidence_bindings")
    result = transition_builder_to_responsive(packet, source, _config(lock, builder, responsive))
    assert result["status"] == "insufficient_evidence"
    assert "PG.B2R.EVIDENCE_BINDINGS_REQUIRED" in _codes(result)


def test_nonexistent_evidence_reference_is_rejected(tmp_path: Path):
    result, packet, builder, responsive, source, lock = _run(tmp_path / "base")
    assert result["status"] == "accepted"
    packet["evidence_bindings"]["layout_check"]["artifact_ref"] = "evidence/missing.json"
    result = transition_builder_to_responsive(packet, source, _config(lock, builder, responsive))
    assert result["status"] == "insufficient_evidence"
    assert "PG.EVIDENCE.FILE_MISSING" in _codes(result)


def test_wrong_evidence_hash_is_rejected(tmp_path: Path):
    _, packet, builder, responsive, source, lock = _run(tmp_path / "base")
    packet["evidence_bindings"]["execution_evidence"]["artifact_sha256"] = "a" * 64
    result = transition_builder_to_responsive(packet, source, _config(lock, builder, responsive))
    assert result["status"] == "invalid"
    assert "PG.EVIDENCE.HASH_MISMATCH" in _codes(result)


def test_source_mutation_after_hash_is_rejected(tmp_path: Path):
    _, packet, builder, responsive, source, lock = _run(tmp_path / "base")
    (builder / "evidence/action-batch.json").write_text(json.dumps({"schema": "ev4-action-batch@1.0.0", "selected_candidate_id": "ARCH-FAM-C", "actions": ["mutated"]}), encoding="utf-8")
    result = transition_builder_to_responsive(packet, source, _config(lock, builder, responsive))
    assert "PG.EVIDENCE.HASH_MISMATCH" in _codes(result)


def test_synthetic_builder_evidence_is_rejected(tmp_path: Path):
    _, packet, builder, responsive, source, lock = _run(tmp_path / "base")
    value = json.loads((builder / "evidence/execution-evidence.json").read_text())
    value["provenance"] = {"source": "synthetic_fixture"}
    digest = _json_file(builder / "evidence/execution-evidence.json", value)
    packet["evidence_bindings"]["execution_evidence"]["artifact_sha256"] = digest
    result = transition_builder_to_responsive(packet, source, _config(lock, builder, responsive))
    assert result["status"] == "insufficient_evidence"
    assert "PG.EVIDENCE.SYNTHETIC_DERIVED" in _codes(result)


def test_self_declared_real_evidence_is_insufficient(tmp_path: Path):
    builder, responsive, source, lock = _repos(tmp_path)
    packet = _packet(builder)
    packet.pop("evidence_bindings")
    packet["real_evidence"] = True
    result = transition_builder_to_responsive(packet, source, _config(lock, builder, responsive))
    assert result["status"] == "insufficient_evidence"


def test_wrong_session_binding_is_rejected(tmp_path: Path):
    _, packet, builder, responsive, source, lock = _run(tmp_path / "base")
    packet["evidence_subject"]["builder_session_ref"] = "SESSION-OTHER"
    result = transition_builder_to_responsive(packet, source, _config(lock, builder, responsive))
    assert "PG.B2R.BINDING_SESSION_MISMATCH" in _codes(result)


def test_wrong_package_binding_is_rejected(tmp_path: Path):
    _, packet, builder, responsive, source, lock = _run(tmp_path / "base")
    packet["evidence_subject"]["source_package_ref"] = "PACKAGE-OTHER"
    result = transition_builder_to_responsive(packet, source, _config(lock, builder, responsive))
    assert "PG.B2R.BINDING_PACKAGE_MISMATCH" in _codes(result)


def test_wrong_action_set_digest_is_rejected(tmp_path: Path):
    _, packet, builder, responsive, source, lock = _run(tmp_path / "base")
    packet["evidence_subject"]["action_set_digest"] = "0" * 64
    result = transition_builder_to_responsive(packet, source, _config(lock, builder, responsive))
    assert "PG.B2R.BINDING_ACTION_SET_MISMATCH" in _codes(result)


def test_desktop_evidence_cannot_satisfy_tablet_claim(tmp_path: Path):
    _, packet, builder, responsive, source, lock = _run(tmp_path / "base")
    packet["evidence_bindings"]["tablet"] = deepcopy(packet["evidence_bindings"]["desktop"])
    packet["evidence_bindings"]["tablet"]["subject_ref"] = "tablet-proof"
    result = transition_builder_to_responsive(packet, source, _config(lock, builder, responsive))
    assert "PG.EVIDENCE.CLAIM_VIEWPORT_MISMATCH" in _codes(result) or "PG.B2R.BINDING_VIEWPORT_MISMATCH" in _codes(result)


def test_missing_mobile_viewport_binding_is_rejected(tmp_path: Path):
    _, packet, builder, responsive, source, lock = _run(tmp_path / "base")
    packet["evidence_bindings"].pop("mobile")
    result = transition_builder_to_responsive(packet, source, _config(lock, builder, responsive))
    assert result["status"] == "insufficient_evidence"
    assert "PG.B2R.EVIDENCE_BINDING_MISSING" in _codes(result)


def test_forbidden_claim_is_invalid(tmp_path: Path):
    _, packet, builder, responsive, source, lock = _run(tmp_path / "base")
    packet["claim"] = "production_ready"
    result = transition_builder_to_responsive(packet, source, _config(lock, builder, responsive))
    assert result["status"] == "invalid"
    assert "PG.B2R.FORBIDDEN_CLAIM" in _codes(result)


def test_lock_verification_detects_hash_mismatch(tmp_path: Path):
    builder, responsive, source, lock = _repos(tmp_path)
    lock["files"][0]["sha256_file_bytes"] = "0" * 64
    assert any(item.code == "PG.B2R.EXTERNAL_HASH_MISMATCH" for item in verify_builder_to_responsive_lock(lock, source))


def test_result_schema_validated(tmp_path: Path):
    result, _, _, _, _, _ = _run(tmp_path)
    schema = json.loads((ROOT / "schemas/builder-to-responsive-transition-result/builder-to-responsive-transition-result.v1.schema.json").read_text())
    Draft202012Validator(schema).validate(result)
