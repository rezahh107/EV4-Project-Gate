from __future__ import annotations

from pathlib import Path

from ev4_transition.behavioral_coverage import validate_coverage_document, validate_coverage_source
from ev4_transition.canonical_json import load_json_file

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "schemas/behavioral-coverage/behavioral-coverage.v1.schema.json"
FIXTURES = ROOT / "tests/fixtures/behavioral_coverage"


def diagnostic_codes(report):
    return {diagnostic.code for diagnostic in report.diagnostics}


def load_fixture(name: str):
    return load_json_file(FIXTURES / name)


def test_critical_rule_cannot_remain_prose_only():
    report = validate_coverage_source(FIXTURES / "invalid/critical_rule_prose_only.json", SCHEMA)
    assert report.status == "thresholds_failed"
    assert "PG_BRC_CRITICAL_MUST_NOT_BE_PROSE_ONLY" in diagnostic_codes(report)


def test_critical_rule_cannot_remain_schema_backed_without_followup():
    report = validate_coverage_source(FIXTURES / "invalid/critical_rule_schema_backed_without_followup.json", SCHEMA)
    assert report.status == "thresholds_failed"
    assert "PG_BRC_CRITICAL_SCHEMA_BACKED_REQUIRES_FOLLOWUP" in diagnostic_codes(report)


def test_high_rule_prose_only_requires_documented_risk():
    document = load_fixture("valid/critical_rule_fixture_tested.json")
    rule = document["rules"][0]
    rule["rule_id"] = "PG-PROGRESS-001"
    rule["risk"] = "High"
    rule["status"] = "prose_only"
    rule["target_status"] = "validator_backed"
    rule["validators"] = []
    rule["valid_fixtures"] = []
    rule["invalid_fixtures"] = []
    rule.pop("documented_risk", None)
    report = validate_coverage_document(document, "<memory>", SCHEMA)
    assert "PG_BRC_HIGH_PROSE_ONLY_REQUIRES_DOCUMENTED_RISK" in diagnostic_codes(report)


def test_invalid_fixture_required_for_critical_rule():
    document = load_fixture("valid/critical_rule_fixture_tested.json")
    document["rules"][0]["invalid_fixtures"] = []
    report = validate_coverage_document(document, "<memory>", SCHEMA)
    assert "PG_BRC_INVALID_FIXTURE_REQUIRED_FOR_CRITICAL_TARGET" in diagnostic_codes(report)


def test_ci_step_required_before_ci_enforced():
    document = load_fixture("valid/critical_rule_fixture_tested.json")
    document["rules"][0]["status"] = "ci_enforced"
    document["rules"][0]["target_status"] = "ci_enforced"
    document["rules"][0]["ci_steps"] = []
    report = validate_coverage_document(document, "<memory>", SCHEMA)
    assert "PG_BRC_CI_STEP_REQUIRED_BEFORE_CI_ENFORCED" in diagnostic_codes(report)


def test_downstream_contract_required_before_downstream_contract_enforced():
    report = validate_coverage_source(FIXTURES / "invalid/downstream_contract_missing_for_claimed_enforcement.json", SCHEMA)
    codes = diagnostic_codes(report)
    assert "PG_BRC_DOWNSTREAM_CONTRACT_REQUIRED_BEFORE_DOWNSTREAM_ENFORCED" in codes
    assert "PG_BRC_NO_CLAIMED_DOWNSTREAM_ENFORCEMENT_WITHOUT_REJECTION_FIXTURE" in codes


def test_coverage_cli_valid_fixture_thresholds_met():
    report = validate_coverage_source(FIXTURES / "valid/critical_rule_fixture_tested.json", SCHEMA)
    assert report.status == "thresholds_met"
    assert report.rule_count == 1
