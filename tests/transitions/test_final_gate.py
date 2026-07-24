from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from jsonschema import Draft202012Validator

from ev4_transition.canonical_json import bytes_sha256, canonical_sha256
from ev4_transition.contract_source import LocalCheckoutContractSource
from ev4_transition.final_gate_authority import is_authoritative_final_gate_result
from ev4_transition.kernel_decision_dependencies import (
    EXPECTED_KERNEL_SEMANTIC_DEPENDENCIES,
    KERNEL_ACCEPTED_COMMIT,
    KERNEL_INTAKE_RESULT_SCHEMA_ID,
    KERNEL_INTAKE_SCHEMA_ID,
    KERNEL_LOCK_SCHEMA_VERSION,
    KERNEL_REPOSITORY,
)
from ev4_transition.kernel_decision_intake import KernelAuditExecution
from ev4_transition.transitions.final_gate import (
    EXPECTED_FINAL_GATE_DEPENDENCIES,
    GATE_ID,
    PG_REPO,
    RESPONSIVE_OUTPUT_SCHEMA,
    RESPONSIVE_REPO,
    FinalGateConfig,
    run_final_gate,
    verify_final_gate_lock,
)
from ev4_transition.viewport_runtime import OFFICIAL_RUNTIME_NOT_OBSERVED_REASON

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "fixtures/kernel-decision-intake/complete-layout-structure.synthetic.json"
ZERO_HASH = "0" * 64


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _json_file(path: Path, value: dict) -> str:
    _write(path, json.dumps(value, ensure_ascii=False, sort_keys=True))
    return bytes_sha256(path.read_bytes())


def _lineage() -> dict:
    return {
        "decision_family": "layout_structure",
        "decision_card_ref": "projection:test",
        "selected_option": "flexbox",
        "rejected_options": ["grid"],
        "evidence_refs": ["EV1"],
        "evidence_state": "validated",
        "consumer_stage": "final_evidence_gate",
    }


def _sanitize_runtime(value):
    if isinstance(value, dict):
        result = {}
        for key, child in value.items():
            if key in {"synthetic", "synthetic_only"}:
                result[key] = False
            else:
                result[key] = _sanitize_runtime(child)
        return result
    if isinstance(value, list):
        return [_sanitize_runtime(item) for item in value]
    if isinstance(value, str):
        text = value.replace("synthetic_fixture", "repo_path")
        text = text.replace("synthetic", "runtime")
        text = text.replace("fixtures/", "artifacts/")
        text = text.replace("fixture", "runtime")
        return text
    return value


def _raw_intake() -> dict:
    bundle = _sanitize_runtime(json.loads(BASE.read_text()))
    bundle["synthetic"] = False
    bundle["produced_by"]["ref"] = "runtime-head"
    bundle["provenance"] = {
        "source": "owner-runtime",
        "created_by": "owner-runtime",
    }
    bundle["evidence"][0]["kind"] = "report"
    bundle["evidence"][0]["source"] = {
        "type": "repo_path",
        "reference": "exports/project.json",
    }
    packet = bundle["payload"]["data"]["decision_packets"][0]
    for carrier in (packet["decision_record"], packet["resolver_input"]):
        carrier["evidence_refs"][0]["source_type"] = "project_export"
        carrier["evidence_refs"][0]["ref"] = "exports/project.json"
    return bundle


def _output(include_lineage: bool = True) -> dict:
    output = {
        "schema": RESPONSIVE_OUTPUT_SCHEMA,
        "source_packet_ref": "RESPONSIVE-PACKET-1",
        "responsive_tree_output": {"mode": "blocked"},
        "unresolved_unknowns": [],
    }
    if include_lineage:
        output["decision_lineage"] = _lineage()
    return output


def _pass(_: dict) -> KernelAuditExecution:
    return KernelAuditExecution(
        "completed",
        {
            "audit_status": "pass",
            "human_override_observed": False,
            "resolver_output": {
                "resolver_status": "auto_resolved",
                "rule_id": "resolver.rule.layout_structure.mvp.v0",
                "rule_version": "0.1.0",
            },
            "diagnostics": [],
        },
        {"exit_code": 0},
    )


def _fail(_: dict) -> KernelAuditExecution:
    return KernelAuditExecution(
        "completed",
        {
            "audit_status": "fail",
            "human_override_observed": False,
            "resolver_output": {"resolver_status": "auto_resolved"},
            "diagnostics": [
                {
                    "code": "L2_SELECTED_OPTION_RESOLVER_MISMATCH",
                    "severity": "error",
                    "source": "semantic",
                    "path": "decision_record.selected_option",
                    "message": "runtime",
                }
            ],
        },
        {"exit_code": 0},
    )


def _repos(tmp_path: Path):
    pg = tmp_path / "pg"
    responsive = tmp_path / "responsive"
    kernel = tmp_path / "kernel"
    for dep in EXPECTED_FINAL_GATE_DEPENDENCIES.values():
        root = pg if dep.repository == PG_REPO else responsive
        if dep.path.endswith(".py"):
            text = f"# {dep.identity_marker}\nprint('responsive ok')\n"
        elif dep.path.endswith(".json") and "responsive-output" in dep.path:
            text = json.dumps(
                {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "id": dep.contract_or_schema_id,
                    "marker": dep.identity_marker,
                    "type": "object",
                    "required": ["schema"],
                    "properties": {"schema": {"const": RESPONSIVE_OUTPUT_SCHEMA}},
                    "additionalProperties": True,
                }
            )
        elif dep.path.endswith(".json"):
            text = json.dumps(
                {
                    "id": dep.contract_or_schema_id,
                    "marker": dep.identity_marker,
                }
            )
        else:
            text = f"{dep.identity_marker}\n"
        _write(root / dep.path, text)
    final_lock = {
        "schema_version": "final-gate-lock.v1",
        "gate_id": GATE_ID,
        "files": [],
    }
    for dep in EXPECTED_FINAL_GATE_DEPENDENCIES.values():
        root = pg if dep.repository == PG_REPO else responsive
        final_lock["files"].append(
            {
                "role": dep.role,
                "repository": dep.repository,
                "accepted_commit": dep.accepted_commit,
                "path": dep.path,
                "contract_or_schema_id": dep.contract_or_schema_id,
                "sha256_file_bytes": bytes_sha256((root / dep.path).read_bytes()),
            }
        )

    texts = {
        "decision_record_schema": json.dumps(
            {"$id": "https://ev4.local/schemas/decision-record.v2.schema.json"}
        ),
        "p0_decision_matrices": json.dumps(
            {
                "matrix_registry_id": "p0-decision-matrices.v0",
                "matrices": [{"decision_family_id": "layout_structure"}],
            }
        ),
        "resolver_rule_registry": json.dumps(
            {
                "registry_id": "resolver-rule-registry.v0",
                "active_rules": [{"decision_family_id": "layout_structure"}],
            }
        ),
        "layout_structure_rule": json.dumps(
            {
                "contract_id": "resolver.contract.layout_structure.mvp.v0",
                "rule_id": "resolver.rule.layout_structure.mvp.v0",
                "rule_version": "0.1.0",
            }
        ),
        "resolver_implementation": "export function resolveDecision() {}\n",
        "l2_decision_correctness_audit": "export function auditDecisionRecord() {}\n",
    }
    files = []
    for role, dep in EXPECTED_KERNEL_SEMANTIC_DEPENDENCIES.items():
        _write(kernel / dep.path, texts[role])
        files.append(
            {
                "role": role,
                "repository": dep.repository,
                "accepted_commit": dep.accepted_commit,
                "path": dep.path,
                "contract_or_schema_id": dep.contract_or_schema_id,
                "sha256_file_bytes": bytes_sha256((kernel / dep.path).read_bytes()),
            }
        )
    kernel_lock = {
        "schema_version": KERNEL_LOCK_SCHEMA_VERSION,
        "intake_schema_id": KERNEL_INTAKE_SCHEMA_ID,
        "kernel_pin": {
            "repository": KERNEL_REPOSITORY,
            "accepted_commit": KERNEL_ACCEPTED_COMMIT,
        },
        "files": sorted(files, key=lambda item: item["role"]),
    }
    source = LocalCheckoutContractSource(
        {
            PG_REPO: pg,
            RESPONSIVE_REPO: responsive,
            KERNEL_REPOSITORY: kernel,
        }
    )
    return pg, responsive, kernel, source, final_lock, kernel_lock


def _input(
    responsive: Path,
    *,
    include_raw: bool = True,
    include_lineage: bool = True,
) -> dict:
    output = _output(include_lineage)
    output_ref = "evidence/responsive-output.json"
    bindings = {
        "responsive_output": {
            "artifact_ref": output_ref,
            "artifact_sha256": _json_file(responsive / output_ref, output),
            "subject_ref": "RESPONSIVE-PACKET-1",
        }
    }
    viewport_refs = {}
    for name in ("desktop", "tablet", "mobile"):
        ref = f"{name}-proof"
        viewport_refs[name] = ref
        path = f"evidence/{name}.json"
        bindings[name] = {
            "artifact_ref": path,
            "artifact_sha256": _json_file(
                responsive / path,
                {
                    "evidence_ref": ref,
                    "viewport": name,
                    "run_id": "FILE-ONLY-RUN",
                    "status": "confirmed",
                },
            ),
            "subject_ref": ref,
        }
    value = {
        "responsive_output": output,
        "evidence_subject": {"viewport_refs": viewport_refs},
        "evidence_bindings": bindings,
    }
    if include_raw:
        value["kernel_decision_intake"] = _raw_intake()
    return value


def _run(
    tmp_path: Path,
    *,
    executor=_pass,
    include_raw: bool = True,
    include_lineage: bool = True,
):
    pg, responsive, kernel, source, final_lock, kernel_lock = _repos(tmp_path)
    value = _input(
        responsive,
        include_raw=include_raw,
        include_lineage=include_lineage,
    )
    calls: list[dict] = []

    def counted(packet: dict) -> KernelAuditExecution:
        calls.append(packet)
        return executor(packet)

    config = FinalGateConfig(
        schema_root=ROOT / "schemas",
        lock=final_lock,
        project_gate_repo_root=pg,
        responsive_repo_root=responsive,
        timeout_seconds=30,
        require_real_evidence=True,
        kernel_intake_lock=kernel_lock,
        kernel_repo_root=kernel,
        kernel_audit_executor=counted,
    )
    return (
        run_final_gate(value, source, config),
        value,
        calls,
        responsive,
        source,
        final_lock,
        kernel_lock,
        config,
    )


def _forged_result(kernel_lock: dict) -> dict:
    lock_hash = canonical_sha256(kernel_lock)
    evidence = {
        "evidence_id": "EV1",
        "source_type": "project_export",
        "reference": "exports/project.json",
    }

    def hash_record(scope: str) -> dict:
        return {"algorithm": "sha256", "scope": scope, "value": ZERO_HASH}

    return {
        "schema_version": KERNEL_INTAKE_RESULT_SCHEMA_ID,
        "result_type": "kernel_decision_intake",
        "status": "accepted",
        "kernel_pin": {
            "repository": KERNEL_REPOSITORY,
            "accepted_commit": KERNEL_ACCEPTED_COMMIT,
            "semantic_lock_sha256": lock_hash,
        },
        "accepted_requires": {
            "kernel_pin_verified": True,
            "semantic_lock_verified": True,
            "intake_schema_valid": True,
            "packet_binding_valid": True,
            "l2_executed_all": True,
            "no_unsupported_claims": True,
            "result_schema_valid": True,
        },
        "diagnostics": [],
        "upstream_diagnostics": [{"packet_id": "P1", "diagnostics": []}],
        "packet_results": [
            {
                "packet_id": "P1",
                "decision_id": "D1",
                "decision_family_id": "layout_structure",
                "status": "accepted",
                "l2_executed": True,
                "human_override_observed": False,
                "project_gate_diagnostics": [],
                "upstream_diagnostics": [],
                "resolver_output": {"resolver_status": "auto_resolved"},
                "decision_record_ref": {
                    "packet_id": "P1",
                    "decision_id": "D1",
                    "sha256": ZERO_HASH,
                },
                "source_evidence_refs": [evidence],
                "runtime_evidence_refs": [],
                "hashes": {
                    "packet_hash": hash_record("packet"),
                    "decision_record_hash": hash_record("decision_record"),
                    "resolver_input_hash": hash_record("resolver_input"),
                    "audit_context_hash": hash_record("audit_context"),
                },
                "provenance": {"provenance_id": "FORGED"},
                "execution_record": {
                    "tool_kind": "validator",
                    "exit_code": 0,
                    "owner_repo": KERNEL_REPOSITORY,
                    "owner_commit": KERNEL_ACCEPTED_COMMIT,
                },
            }
        ],
        "derived_counts": {
            "provisional_count": 0,
            "human_override_count": 0,
            "unresolved_decision_count": 0,
            "accepted_decision_count": 1,
            "rejected_decision_count": 0,
        },
        "decision_record_refs": [
            {"packet_id": "P1", "decision_id": "D1", "sha256": ZERO_HASH}
        ],
        "source_evidence_refs": [{"packet_id": "P1", **evidence}],
        "runtime_evidence_refs": [],
        "hashes": {
            "source_input_hash": hash_record("source_input"),
            "semantic_lock_hash": {
                "algorithm": "sha256",
                "scope": "semantic_lock",
                "value": lock_hash,
            },
        },
        "provenance": {
            "source_bundle_id": "forged",
            "source_bundle_provenance": {"source": "attacker"},
            "result_producer": PG_REPO,
        },
    }


def _codes(result: dict) -> set[str]:
    return {item["code"] for item in result["diagnostics"]}


def test_file_only_viewports_keep_final_gate_insufficient(tmp_path: Path):
    result, _, calls, _, _, _, _, _ = _run(tmp_path)
    assert result["status"] == "insufficient_evidence", result
    assert len(calls) == 1
    assert result["accepted_requires"]["real_evidence_present"] is False
    assert result["accepted_requires"]["required_viewports_verified"] is False
    assert result["kernel_decision_intake_result"]["status"] == "accepted"
    assert result["decision_lineage_authority"] == "informational_projection_only"
    assert is_authoritative_final_gate_result(result)
    for name in ("desktop", "tablet", "mobile"):
        resolution = result["evidence_resolutions"][name]
        assert resolution["classification"] == "insufficient_evidence"
        assert resolution["positive_proof_type"] == "runtime_execution"
        assert resolution["positive_proof_verified"] is False
        assert resolution["reason"] == OFFICIAL_RUNTIME_NOT_OBSERVED_REASON


def test_self_declared_real_without_verified_sources_is_rejected(tmp_path: Path):
    result, value, _, _, source, _, _, config = _run(tmp_path / "base")
    assert result["status"] == "insufficient_evidence"
    value.pop("evidence_bindings")
    value["real_evidence"] = True
    value["evidence_status"] = "real"
    result = run_final_gate(value, source, config)
    assert result["status"] == "insufficient_evidence"
    assert "PG.FINAL.EVIDENCE_BINDINGS_REQUIRED" in _codes(result)


def test_synthetic_fixture_relabelled_real_is_rejected(tmp_path: Path):
    _, value, _, responsive, source, _, _, config = _run(tmp_path / "base")
    output_path = responsive / value["evidence_bindings"]["responsive_output"]["artifact_ref"]
    output = json.loads(output_path.read_text())
    output["provenance"] = {"source": "synthetic_fixture"}
    value["responsive_output"] = output
    value["real_evidence"] = True
    value["evidence_status"] = "real"
    value["synthetic"] = False
    value["evidence_bindings"]["responsive_output"]["artifact_sha256"] = _json_file(output_path, output)
    result = run_final_gate(value, source, config)
    assert result["status"] == "insufficient_evidence"
    assert (
        "PG.EVIDENCE.SYNTHETIC_DERIVED" in _codes(result)
        or "PG.FINAL.SYNTHETIC_ONLY_EVIDENCE" in _codes(result)
    )


def test_wrong_responsive_output_hash_is_rejected(tmp_path: Path):
    _, value, _, _, source, _, _, config = _run(tmp_path / "base")
    value["evidence_bindings"]["responsive_output"]["artifact_sha256"] = "a" * 64
    result = run_final_gate(value, source, config)
    assert result["status"] == "invalid"
    assert "PG.EVIDENCE.HASH_MISMATCH" in _codes(result)


def test_incomplete_viewport_evidence_is_rejected(tmp_path: Path):
    _, value, _, _, source, _, _, config = _run(tmp_path / "base")
    value["evidence_bindings"].pop("mobile")
    result = run_final_gate(value, source, config)
    assert result["status"] == "insufficient_evidence"
    assert "PG.FINAL.EVIDENCE_BINDING_MISSING" in _codes(result)


def test_desktop_evidence_cannot_satisfy_tablet_claim(tmp_path: Path):
    _, value, _, _, source, _, _, config = _run(tmp_path / "base")
    value["evidence_bindings"]["tablet"] = deepcopy(value["evidence_bindings"]["desktop"])
    value["evidence_bindings"]["tablet"]["subject_ref"] = "tablet-proof"
    result = run_final_gate(value, source, config)
    assert result["status"] == "invalid"
    assert (
        "PG.EVIDENCE.CLAIM_VIEWPORT_MISMATCH" in _codes(result)
        or "PG.FINAL.VIEWPORT_EVIDENCE_MISMATCH" in _codes(result)
    )


def test_raw_kernel_intake_remains_mandatory(tmp_path: Path):
    result, _, calls, _, _, _, _, _ = _run(tmp_path, include_raw=False)
    assert calls == []
    assert result["status"] == "invalid"
    assert "PG.FINAL.KERNEL_INTAKE_REQUIRED" in _codes(result)


def test_precomputed_result_without_raw_intake_cannot_authenticate(tmp_path: Path):
    _, value, calls, _, source, _, kernel_lock, config = _run(
        tmp_path / "base",
        include_raw=False,
    )
    assert calls == []
    value["kernel_decision_intake_result"] = _forged_result(kernel_lock)
    result = run_final_gate(value, source, config)
    assert result["status"] == "invalid"
    assert "PG.FINAL.KERNEL_INTAKE_REQUIRED" in _codes(result)


def test_precomputed_kernel_result_drift_remains_rejected(tmp_path: Path):
    first, value, calls, _, source, _, _, config = _run(tmp_path / "base")
    assert len(calls) == 1
    supplied = deepcopy(first["kernel_decision_intake_result"])
    supplied["derived_counts"] = {
        **supplied["derived_counts"],
        "accepted_decision_count": 99,
    }
    value["kernel_decision_intake_result"] = supplied
    result = run_final_gate(value, source, config)
    assert "PG.FINAL.KERNEL_INTAKE_PROJECTION_MISMATCH" in _codes(result)


def test_nonaccepted_kernel_execution_is_rejected(tmp_path: Path):
    result, _, calls, _, _, _, _, _ = _run(tmp_path, executor=_fail)
    assert len(calls) == 1
    assert result["status"] == "invalid"
    assert "PG.FINAL.KERNEL_INTAKE_NOT_ACCEPTED" in _codes(result)


def test_lineage_is_optional_informational_projection(tmp_path: Path):
    result, _, calls, _, _, _, _, _ = _run(tmp_path, include_lineage=False)
    assert len(calls) == 1
    assert result["status"] == "insufficient_evidence", result
    assert result["decision_lineage_authority"] == "informational_projection_only"


def test_lineage_projection_drift_is_rejected(tmp_path: Path):
    _, value, _, _, source, _, _, config = _run(tmp_path / "base")
    value["decision_lineage"] = {**_lineage(), "selected_option": "grid"}
    result = run_final_gate(value, source, config)
    assert "PG.FINAL.DECISION_LINEAGE_DRIFT" in _codes(result)


def test_forbidden_claim_is_rejected(tmp_path: Path):
    _, value, _, _, source, _, _, config = _run(tmp_path / "base")
    value["claim"] = "production_ready"
    result = run_final_gate(value, source, config)
    assert result["status"] == "invalid"
    assert "PG.FINAL.FORBIDDEN_CLAIM" in _codes(result)


def test_final_gate_lock_detects_hash_mismatch(tmp_path: Path):
    _, _, _, source, final_lock, _ = _repos(tmp_path)
    final_lock["files"][0]["sha256_file_bytes"] = "0" * 64
    assert any(
        item.code == "PG.FINAL.EXTERNAL_HASH_MISMATCH"
        for item in verify_final_gate_lock(final_lock, source)
    )


def test_completed_result_is_schema_valid(tmp_path: Path):
    result, _, _, _, _, _, _, _ = _run(tmp_path)
    schema = json.loads(
        (ROOT / "schemas/final-gate-result/final-gate-result.v1.schema.json").read_text()
    )
    Draft202012Validator(schema).validate(result)
