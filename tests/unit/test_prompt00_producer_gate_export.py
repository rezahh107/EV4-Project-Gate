from __future__ import annotations

from pathlib import Path

from ev4_transition.producer_gate_export import ProducerGateExportValidator

from .prompt00_fixture_factory import invalid_export_case, load_json, valid_export_case

ROOT = Path(__file__).resolve().parents[2]


def codes(result: dict) -> set[str]:
    return {item["code"] for item in result["diagnostics"]}


def test_valid_fixture_recipes_pass() -> None:
    validator = ProducerGateExportValidator(ROOT)
    recipes = load_json("tests/fixtures/producer_gate_export/valid/cases.json")
    assert recipes["synthetic"] is True
    for case in recipes["cases"]:
        result = validator.validate(valid_export_case(case["name"]))
        assert result["status"] == "valid", (case["name"], result)


def test_invalid_fixture_recipes_emit_expected_diagnostics() -> None:
    validator = ProducerGateExportValidator(ROOT)
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
    validator = ProducerGateExportValidator(ROOT)
    artifact = invalid_export_case("handoff_allowed_with_blocker")
    assert validator.validate(artifact) == validator.validate(artifact)
