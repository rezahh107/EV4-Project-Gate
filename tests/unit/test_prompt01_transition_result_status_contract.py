from __future__ import annotations

from pathlib import Path

from jsonschema import Draft202012Validator

from ev4_transition.canonical_json import load_json_file
from ev4_transition.diagnostics import diagnostic as make_diagnostic, status_from_diagnostics

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = Draft202012Validator(load_json_file(ROOT / "schemas/transition-result/transition-result.v1.schema.json"))


def diagnostic(severity: str) -> dict:
    return {"code": f"TEST_{severity.upper()}", "severity": severity, "message": f"test {severity}", "path": "$"}


def hash_record(scope: str) -> dict:
    return {"algorithm": "sha256", "canonicalization": "ev4-canonical-json.v1", "scope": scope, "value": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"}


def base_result(status: str, diagnostics: list[dict] | None = None) -> dict:
    return {
        "schema_version": "transition-result.v1",
        "result_type": "stage_bundle_validation",
        "status": status,
        "source_stage": "architect",
        "diagnostics": diagnostics or [],
        "hashes": {"source_bundle_hash": hash_record("source_bundle"), "canonical_payload_hash": hash_record("payload")},
        "provenance": {"source_provenance": {"kind": "synthetic_fixture"}, "produced_by": {"tool": "ev4-transition"}},
        "output": None,
    }


def assert_valid(payload: dict) -> None:
    assert list(SCHEMA.iter_errors(payload)) == []


def assert_invalid(payload: dict) -> None:
    assert list(SCHEMA.iter_errors(payload))


def test_accepted_allows_empty_or_info_diagnostics_with_explicit_evidence():
    assert_valid(base_result("accepted"))
    assert_valid(base_result("accepted", [diagnostic("info")]))


def test_accepted_rejects_blocking_diagnostics():
    for severity in ("error", "warning", "insufficient_evidence"):
        assert_invalid(base_result("accepted", [diagnostic(severity)]))


def test_accepted_rejects_missing_explicit_hash_or_provenance_evidence():
    for path in (("hashes", "source_bundle_hash"), ("hashes", "canonical_payload_hash"), ("provenance", "source_provenance"), ("provenance", "produced_by")):
        payload = base_result("accepted")
        payload[path[0]][path[1]] = None
        assert_invalid(payload)


def test_accepted_rejects_empty_provenance_objects():
    payload = base_result("accepted")
    payload["provenance"]["source_provenance"] = {}
    assert_invalid(payload)
    payload = base_result("accepted")
    payload["provenance"]["produced_by"] = {}
    assert_invalid(payload)


def test_accepted_rejects_swapped_hash_scopes():
    payload = base_result("accepted")
    payload["hashes"]["source_bundle_hash"]["scope"] = "payload"
    assert_invalid(payload)
    payload = base_result("accepted")
    payload["hashes"]["canonical_payload_hash"]["scope"] = "source_bundle"
    assert_invalid(payload)


def test_accepted_rejects_null_source_stage():
    payload = base_result("accepted")
    payload["source_stage"] = None
    assert_invalid(payload)


def test_repair_needed_requires_warning_and_rejects_blocking_diagnostics():
    assert_valid(base_result("repair_needed", [diagnostic("warning")]))
    assert_valid(base_result("repair_needed", [diagnostic("info"), diagnostic("warning")]))
    assert_invalid(base_result("repair_needed", []))
    assert_invalid(base_result("repair_needed", [diagnostic("info")]))
    assert_invalid(base_result("repair_needed", [diagnostic("warning"), diagnostic("error")]))
    assert_invalid(base_result("repair_needed", [diagnostic("warning"), diagnostic("insufficient_evidence")]))


def test_insufficient_evidence_requires_matching_diagnostic_and_rejects_error():
    assert_valid(base_result("insufficient_evidence", [diagnostic("insufficient_evidence")]))
    assert_valid(base_result("insufficient_evidence", [diagnostic("info"), diagnostic("insufficient_evidence")]))
    assert_invalid(base_result("insufficient_evidence", []))
    assert_invalid(base_result("insufficient_evidence", [diagnostic("warning")]))
    assert_invalid(base_result("insufficient_evidence", [diagnostic("insufficient_evidence"), diagnostic("error")]))


def test_invalid_requires_error_diagnostic():
    assert_valid(base_result("invalid", [diagnostic("error")]))
    assert_invalid(base_result("invalid", []))
    assert_invalid(base_result("invalid", [diagnostic("warning")]))
    assert_invalid(base_result("invalid", [diagnostic("insufficient_evidence")]))


def test_legacy_valid_preserves_warning_compatibility():
    assert_valid(base_result("valid"))
    assert_valid(base_result("valid", [diagnostic("info")]))
    assert_valid(base_result("valid", [diagnostic("warning")]))
    assert_invalid(base_result("valid", [diagnostic("error")]))
    assert_invalid(base_result("valid", [diagnostic("insufficient_evidence")]))


def test_legacy_warning_status_output_validates_against_schema():
    diagnostics = [make_diagnostic("LEGACY_WARNING", "warning", "legacy warning", "$")]
    status = status_from_diagnostics(diagnostics)
    assert status == "valid"
    assert_valid(base_result(status, [diagnostic("warning")]))
