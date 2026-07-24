from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from ev4_transition.canonical_json import canonical_sha256
from ev4_transition.producer_gate_export import ProducerGateExportValidator

from .prompt00_fixture_factory import invalid_export_case, load_json, producer_export, valid_export_case

ROOT = Path(__file__).resolve().parents[2]


def codes(result: dict) -> set[str]:
    return {item["code"] for item in result["diagnostics"]}


def test_valid_fixture_recipes_pass_contract_validation() -> None:
    validator = ProducerGateExportValidator(ROOT, operational=False)
    recipes = load_json("tests/fixtures/producer_gate_export/valid/cases.json")
    assert recipes["synthetic"] is True
    for case in recipes["cases"]:
        result = validator.validate(valid_export_case(case["name"]))
        assert result["status"] == "valid", (case["name"], result)


def test_invalid_fixture_recipes_emit_expected_diagnostics() -> None:
    validator = ProducerGateExportValidator(ROOT, operational=False)
    recipes = load_json("tests/fixtures/producer_gate_export/invalid/cases.json")
    assert recipes["synthetic"] is True
    for case in recipes["cases"]:
        result = validator.validate(invalid_export_case(case["name"]))
        assert result["status"] == "invalid", case["name"]
        assert case["expected_code"] in codes(result), (case["name"], result)


def test_stage_bundle_is_a_strict_reference_not_a_duplicate_contract() -> None:
    schema = load_json("contracts/common/producer-gate-export.v1.schema.json")
    final_bundle = schema["properties"]["final_stage_bundle"]
    assert final_bundle == {"$ref": "https://ev4.local/schemas/stage-bundle/stage-bundle.v1.schema.json"}
    for field in ("payload_schema", "produced_by", "evidence_status", "payload", "evidence", "provenance", "synthetic", "missing_evidence"):
        assert field not in schema["properties"]


def test_validator_result_is_deterministic() -> None:
    validator = ProducerGateExportValidator(ROOT, operational=False)
    artifact = invalid_export_case("handoff_allowed_with_blocker")
    assert validator.validate(artifact) == validator.validate(artifact)


def _operational_export(*, synthetic: bool = False) -> dict:
    artifact = deepcopy(producer_export())
    final = artifact["final_stage_bundle"]
    final["synthetic"] = synthetic
    final["provenance"] = {"source": "owner-runtime", "created_by": "owner-runtime"}
    final["evidence"][0]["kind"] = "report"
    final["evidence"][0]["description"] = "Owner runtime report."
    final["evidence"][0]["source"] = {"type": "repo_path", "reference": "artifacts/architect-final.json"}
    final["bundle_id"] = "architect-runtime-bundle"
    if synthetic:
        final["provenance"]["source"] = "synthetic-fixture"
    stage = artifact["stage_manifest"][-1]
    stage["output"] = {
        "present": True,
        "artifact_ref": "final_stage_bundle",
        "artifact_hash": {
            "algorithm": "sha256",
            "scope": "canonical_json",
            "value": canonical_sha256(final),
        },
    }
    # The artifact contract remains v1.0.0 even though the implementation result
    # reports a newer internal validator version.
    artifact["validation"]["validator_version"] = "1.0.0"
    return artifact


def test_operational_synthetic_handoff_is_rejected() -> None:
    result = ProducerGateExportValidator(ROOT).validate(_operational_export(synthetic=True))
    assert result["status"] == "invalid"
    assert "PG_EXPORT_SYNTHETIC_HANDOFF_FORBIDDEN" in codes(result)


def test_operational_placeholder_final_hash_is_rejected() -> None:
    artifact = _operational_export()
    artifact["stage_manifest"][-1]["output"]["artifact_hash"]["value"] = "a" * 64
    result = ProducerGateExportValidator(ROOT).validate(artifact)
    assert result["status"] == "invalid"
    assert "PG_EXPORT_FINAL_HASH_MISMATCH" in codes(result)


def test_operational_exact_embedded_hash_is_accepted() -> None:
    result = ProducerGateExportValidator(ROOT).validate(_operational_export())
    assert result["status"] == "valid", result
