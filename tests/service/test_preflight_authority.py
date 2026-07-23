from __future__ import annotations

from ev4_transition.service.models import GateRequest
from ev4_transition.service.preflight import preflight_authorization_diagnostic
from ev4_transition.service.preflight_core import PreflightResult


def _result(status: str, fingerprint: str | None = "fp") -> PreflightResult:
    return PreflightResult(status, "architect_to_ce", [], status, fingerprint, {})  # type: ignore[arg-type]


def test_default_service_immediate_cannot_bypass_blocked_preflight():
    request = GateRequest(transition_choice="architect_to_ce", input_data={"stage": "architect"})
    diagnostic = preflight_authorization_diagnostic(request, _result("blocked", None))
    assert diagnostic is not None
    assert diagnostic.code == "PG.SERVICE.PREFLIGHT_NOT_READY"


def test_warning_preflight_cannot_authorize_operational_transition():
    request = GateRequest(transition_choice="architect_to_ce", input_data={"stage": "architect"})
    diagnostic = preflight_authorization_diagnostic(request, _result("warnings", None))
    assert diagnostic is not None
    assert diagnostic.code == "PG.SERVICE.PREFLIGHT_NOT_READY"


def test_external_token_requires_fingerprint():
    request = GateRequest(transition_choice="architect_to_ce", input_data={"stage": "architect"}, preflight_mode="external_token")
    diagnostic = preflight_authorization_diagnostic(request, _result("ready", "current"))
    assert diagnostic is not None
    assert diagnostic.code == "PG.SERVICE.PREFLIGHT_FINGERPRINT_REQUIRED"


def test_external_token_rejects_mismatched_fingerprint():
    request = GateRequest(transition_choice="architect_to_ce", input_data={"stage": "architect"}, preflight_mode="external_token", preflight_fingerprint="stale")
    diagnostic = preflight_authorization_diagnostic(request, _result("ready", "current"))
    assert diagnostic is not None
    assert diagnostic.code == "PG.SERVICE.PREFLIGHT_FINGERPRINT_STALE"


def test_ready_same_call_preflight_may_authorize_dispatch():
    request = GateRequest(transition_choice="architect_to_ce", input_data={"stage": "architect"})
    assert preflight_authorization_diagnostic(request, _result("ready", "current")) is None


def test_validation_only_path_may_run_diagnostically_with_warning():
    request = GateRequest(transition_choice="validate_bundle", input_data={"schema_version": "stage-evidence-bundle.v1"})
    assert preflight_authorization_diagnostic(request, PreflightResult("warnings", "validate_bundle", [], "warning", None, {})) is None
