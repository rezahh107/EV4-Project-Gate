from __future__ import annotations

from pathlib import Path

from jsonschema import Draft202012Validator

from ev4_transition.behavioral_coverage import validate_stage_bundle_semantics, validate_transition_result_semantics
from ev4_transition.canonical_json import load_json_file

ROOT = Path(__file__).resolve().parents[2]
RESULT_SCHEMA = Draft202012Validator(load_json_file(ROOT / "schemas/transition-result/transition-result.v1.schema.json"))
STAGE_SCHEMA = Draft202012Validator(load_json_file(ROOT / "schemas/stage-bundle/stage-bundle.v1.schema.json"))


def codes(diagnostics):
    return {diagnostic.code for diagnostic in diagnostics}


def result_fixture(path: str):
    return load_json_file(ROOT / "tests/fixtures/result_envelope" / path)


def stage_fixture(path: str):
    return load_json_file(ROOT / "tests/fixtures/stage_bundle" / path)


def assert_schema_valid(schema, payload):
    assert list(schema.iter_errors(payload)) == []


def test_accepted_missing_evidence_fails():
    payload = result_fixture("invalid/accepted_missing_validator_evidence.json")
    assert_schema_valid(RESULT_SCHEMA, payload)
    assert "PG_EVIDENCE_ACCEPTED_MISSING_VALIDATOR_EVIDENCE" in codes(validate_transition_result_semantics(payload))


def test_synthetic_only_marked_accepted_fails():
    payload = result_fixture("invalid/synthetic_only_marked_as_real_evidence.json")
    assert_schema_valid(RESULT_SCHEMA, payload)
    assert "PG_SYNTH_SYNTHETIC_ONLY_MARKED_ACCEPTED" in codes(validate_transition_result_semantics(payload))


def test_output_write_failed_but_success_fails():
    payload = result_fixture("invalid/output_write_failed_but_success.json")
    assert_schema_valid(RESULT_SCHEMA, payload)
    assert "PG_OUTPUT_WRITE_FAILED_BUT_SUCCESS_STATUS" in codes(validate_transition_result_semantics(payload))


def test_valid_result_envelope_fixtures_pass_semantic_checks():
    for name in (
        "valid/accepted_with_all_required_evidence_shape.json",
        "valid/synthetic_fixture_labeled.json",
        "valid/output_write_success.json",
    ):
        payload = result_fixture(name)
        assert_schema_valid(RESULT_SCHEMA, payload)
        assert validate_transition_result_semantics(payload) == []


def test_copied_specialist_schema_fails():
    payload = stage_fixture("invalid/copied_specialist_schema_claimed_as_project_gate_owned.json")
    assert_schema_valid(STAGE_SCHEMA, payload)
    assert "PG_BOUNDARY_COPIED_SPECIALIST_SCHEMA_CLAIMED_AS_PROJECT_GATE_OWNED" in codes(validate_stage_bundle_semantics(payload))


def test_project_gate_owned_schema_only_passes():
    payload = stage_fixture("valid/project_gate_owned_schema_only.json")
    assert_schema_valid(STAGE_SCHEMA, payload)
    assert validate_stage_bundle_semantics(payload) == []
