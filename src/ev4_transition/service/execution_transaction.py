from __future__ import annotations

from dataclasses import dataclass, replace

from .dispatcher import run_gate_request
from .models import GateRequest, GateResponse
from .preflight import PreflightResult, run_preflight


@dataclass(frozen=True)
class PreparedAuthoritativeGateTransaction:
    """Read-only preflight result bound to one immutable logical request."""

    request: GateRequest
    preflight: PreflightResult
    authorized_request: GateRequest | None

    @property
    def authorization_ready(self) -> bool:
        return self.authorized_request is not None


@dataclass(frozen=True)
class AuthoritativeGateTransactionResult:
    """Result of the unified authoritative preflight-and-run lifecycle."""

    prepared: PreparedAuthoritativeGateTransaction
    response: GateResponse | None

    @property
    def dispatch_started(self) -> bool:
        return self.response is not None

    @property
    def preflight(self) -> PreflightResult:
        return self.prepared.preflight


def prepare_authoritative_gate_transaction(request: GateRequest) -> PreparedAuthoritativeGateTransaction:
    """Run authoritative preflight and bind its fingerprint to the same request data.

    This function never dispatches. It always forces the external-token contract so
    callers cannot accidentally use ``service_immediate`` to bypass request-bound
    fingerprint enforcement.
    """

    base_request = replace(
        request,
        preflight_mode="external_token",
        preflight_fingerprint=None,
    )
    preflight = run_preflight(base_request)
    fingerprint = preflight.request_fingerprint
    authorized_request = None
    if preflight.status == "ready" and fingerprint:
        authorized_request = replace(base_request, preflight_fingerprint=fingerprint)
    return PreparedAuthoritativeGateTransaction(
        request=base_request,
        preflight=preflight,
        authorized_request=authorized_request,
    )


def execute_authoritative_gate_transaction(
    prepared: PreparedAuthoritativeGateTransaction,
) -> AuthoritativeGateTransactionResult:
    """Execute a prepared transaction only when authoritative preflight authorized it."""

    if prepared.authorized_request is None:
        return AuthoritativeGateTransactionResult(prepared=prepared, response=None)
    return AuthoritativeGateTransactionResult(
        prepared=prepared,
        response=run_gate_request(prepared.authorized_request),
    )


def run_authoritative_preflight_and_gate(request: GateRequest) -> AuthoritativeGateTransactionResult:
    """Run one fail-closed Preflight → fingerprint → backend execution transaction."""

    return execute_authoritative_gate_transaction(
        prepare_authoritative_gate_transaction(request)
    )
