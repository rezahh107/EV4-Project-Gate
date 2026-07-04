from __future__ import annotations

import math
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from ev4_transition.canonical_json import CanonicalJsonError, canonical_dumps, canonical_sha256, file_sha256, load_json_file
from ev4_transition.diagnostics import diagnostic, project_gate_status_from_diagnostics, sort_diagnostics
from ev4_transition.locks.manifest import validate_lock_manifest
from ev4_transition.presentation.status_mapping import exit_code_for_status, presentation_for_status

ROOT = Path(__file__).resolve().parents[2]


def schema(path: str) -> dict:
    return load_json_file(ROOT / path)


def fixture(path: str) -> dict:
    return load_json_file(ROOT / path)


def assert_schema_valid(schema_path: str, fixture_path: str) -> None:
    validator = Draft202012Validator(schema(schema_path))
    errors = sorted(validator.iter_errors(fixture(fixture_path)), key=lambda err: (list(err.path), err.message))
    assert errors == []


def assert_schema_invalid(schema_path: str, fixture_path: str) -> None:
    validator = Draft202012Validator(schema(schema_path))
    errors = sorted(validator.iter_errors(fixture(fixture_path)), key=lambda err: (list(err.path), err.message))
    assert errors


def test_canonical_json_is_stable():
    value = {"b": 2, "a": {"d": 4, "c": 3}}
    assert canonical_sha256(value) == canonical_sha256(value)


def test_canonical_json_rejects_nan():
    with pytest.raises(CanonicalJsonError):
        canonical_dumps({"bad": float("nan")})


def test_canonical_json_rejects_infinity():
    for bad in (float("inf"), -math.inf):
        with pytest.raises(CanonicalJsonError):
            canonical_dumps({"bad": bad})


def test_canonical_json_sorts_object_keys():
    assert canonical_dumps({"b": 2, "a": 1}) == '{"a":1,"b":2}'


def test_canonical_json_does_not_reorder_arrays():
    assert canonical_dumps({"items": [3, 2, 1]}) == '{"items":[3,2,1]}'


def test_canonical_json_preserves_unicode_strings_as_input():
    assert canonical_dumps({"text": "سلام EV4"}) == '{"text":"سلام EV4"}'


def test_canonical_json_does_not_apply_hidden_unicode_normalization():
    composed = "é"
    decomposed = "e\u0301"
    assert composed != decomposed
    assert canonical_dumps({"text": composed}) != canonical_dumps({"text": decomposed})
    assert canonical_sha256({"text": composed}) != canonical_sha256({"text": decomposed})


def test_sha256_file_bytes_detects_byte_change(tmp_path: Path):
    first = tmp_path / "first.bin"
    second = tmp_path / "second.bin"
    first.write_bytes(b"ev4\n")
    second.write_bytes(b"ev4\r\n")
    assert file_sha256(first) != file_sha256(second)


def test_file_byte_hash_mismatch_is_invalid(tmp_path: Path):
    path = tmp_path / "artifact.txt"
    path.write_bytes(b"original")
    expected = file_sha256(path)
    path.write_bytes(b"changed")
    assert file_sha256(path) != expected


def test_missing_lock_schema_version_is_invalid():
    diagnostics = validate_lock_manifest({"transition_id": "demo", "files": []})
    assert any(item.code == "PG_LOCK_SCHEMA_VERSION_MISSING" for item in diagnostics)


def test_unknown_lock_schema_version_is_invalid():
    diagnostics = validate_lock_manifest({"schema_version": "unknown.v1", "transition_id": "demo", "files": []})
    assert any(item.code == "PG_LOCK_SCHEMA_VERSION_UNKNOWN" for item in diagnostics)


def test_diagnostics_have_deterministic_order():
    unordered = [
        diagnostic("ZZZ", "info", "later", "$.b"),
        diagnostic("AAA", "error", "first", "$.a"),
        diagnostic("BBB", "warning", "middle", "$.a"),
    ]
    ordered = sort_diagnostics(unordered)
    assert [item.code for item in ordered] == ["AAA", "BBB", "ZZZ"]


def test_no_implicit_timestamp_in_core():
    result = canonical_dumps({"status": "accepted"})
    assert "created_at" not in result
    assert "updated_at" not in result


def test_insufficient_evidence_visual_tone_is_warning():
    presentation = presentation_for_status("insufficient_evidence")
    assert presentation.icon == "⚠️"
    assert presentation.tone == "warning"
    assert presentation.exit_code == 2


def test_status_model_maps_warning_to_repair_needed():
    status = project_gate_status_from_diagnostics([diagnostic("WARN", "warning", "repairable", "$")])
    assert status == "repair_needed"
    assert exit_code_for_status(status) == 1


def test_stage_bundle_schema_valid_fixture_passes():
    assert_schema_valid(
        "schemas/stage-bundle/stage-bundle.v1.schema.json",
        "tests/fixtures/stage_bundle/valid/minimal-stage-bundle.v1.json",
    )


def test_stage_bundle_missing_synthetic_label_fails_when_synthetic():
    assert_schema_invalid(
        "schemas/stage-bundle/stage-bundle.v1.schema.json",
        "tests/fixtures/stage_bundle/invalid/missing-synthetic-label.v1.json",
    )


def test_result_schema_valid_fixture_passes():
    assert_schema_valid(
        "schemas/transition-result/transition-result.v1.schema.json",
        "tests/fixtures/result_envelope/valid/accepted-stage-validation.v1.json",
    )


def test_result_schema_invalid_fixture_fails():
    assert_schema_invalid(
        "schemas/transition-result/transition-result.v1.schema.json",
        "tests/fixtures/result_envelope/invalid/missing-status.v1.json",
    )
