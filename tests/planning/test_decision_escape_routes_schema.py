from __future__ import annotations

import copy
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from ev4_transition.canonical_json import load_json_file

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "planning/decision-escape-routes.schema.json"
STATE_PATH = ROOT / "planning/DECISION_ESCAPE_ROUTES.yml"


def _validator() -> Draft202012Validator:
    schema = load_json_file(SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _state() -> dict:
    return yaml.safe_load(STATE_PATH.read_text(encoding="utf-8"))


def _errors(payload: dict):
    return sorted(_validator().iter_errors(payload), key=lambda error: (list(error.path), error.message))


def test_wave_0_decision_escape_routes_state_validates_with_empty_records() -> None:
    assert _errors(_state()) == []


def test_wave_0_decision_escape_routes_rejects_empty_record_object() -> None:
    payload = copy.deepcopy(_state())
    payload["records"] = [{}]

    assert _errors(payload)


def test_wave_0_decision_escape_routes_rejects_authored_resolved_record() -> None:
    payload = copy.deepcopy(_state())
    payload["records"] = [{"resolved": False}]

    assert _errors(payload)


def test_wave_0_decision_escape_routes_rejects_authored_production_ready_record() -> None:
    payload = copy.deepcopy(_state())
    payload["records"] = [{"production_ready": False}]

    assert _errors(payload)
