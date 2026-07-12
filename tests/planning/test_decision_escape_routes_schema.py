from __future__ import annotations

import ast
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


def _assert_local_python_symbol_exists(record_id: str, reference: str) -> None:
    path_text, separator, symbol = reference.partition("::")
    assert separator and path_text and symbol, (
        f"{record_id}: validator_rule must use '<repo-path>::<top-level-symbol>', got {reference!r}"
    )
    path = ROOT / path_text
    assert path.is_file(), f"{record_id}: carrier file does not exist: {path_text}"
    try:
        module = ast.parse(path.read_text(encoding="utf-8"), filename=path_text)
    except SyntaxError as exc:
        raise AssertionError(f"{record_id}: carrier file is not valid Python: {path_text}: {exc}") from exc
    top_level_symbols = {
        node.name
        for node in module.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }
    assert symbol in top_level_symbols, (
        f"{record_id}: carrier symbol does not exist: {path_text}::{symbol}; "
        f"available top-level symbols: {sorted(top_level_symbols)}"
    )


def test_wave_0_decision_escape_routes_state_validates_with_empty_records() -> None:
    assert _errors(_state()) == []


def test_decision_escape_route_local_python_carriers_exist_without_importing_modules() -> None:
    for record in _state()["records"]:
        _assert_local_python_symbol_exists(record["escape_route_id"], record["carriers"]["validator_rule"])


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


def _first_record_payload() -> dict:
    payload = copy.deepcopy(_state())
    assert payload["records"]
    return payload


def test_decision_escape_routes_rejects_missing_core_carrier_key() -> None:
    payload = _first_record_payload()
    payload["records"][0]["carriers"].pop("validator_diagnostic")

    assert _errors(payload)


def test_decision_escape_routes_rejects_downstream_status_without_downstream_contract() -> None:
    payload = _first_record_payload()
    payload["records"][0]["status"]["enforcement_status"] = "downstream_contract_enforced"
    payload["records"][0]["carriers"].pop("downstream_contract", None)

    assert _errors(payload)


def test_decision_escape_routes_rejects_authored_release_ready_record() -> None:
    payload = _first_record_payload()
    payload["records"][0]["release_ready"] = False

    assert _errors(payload)
