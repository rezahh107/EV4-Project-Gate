from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from .canonical_json import canonical_sha256
from .diagnostics import Diagnostic, diagnostic, sort_diagnostics
from .pcvp_owner import (
    ARCHITECTURE_LOCK_ID,
    BUNDLE_ROOT,
    CANONICAL_COMMIT,
    CANONICAL_REPOSITORY,
    POLICY_ID,
    POLICY_VERSION,
    PROFILE_BINDINGS,
    SOURCE_STAGE_BY_PRODUCER,
    VALIDATOR_PATH,
    OwnerAuthority,
    expected_authority_paths,
    load_profile,
    profile_integration_diagnostics,
    run_owner_bridge,
    verify_owner_authority,
)


def inspect_optional_pcvp_carrier(
    artifact: Any,
    repository_root: str | Path = ".",
    *,
    decision_kernel_repo: str | Path | None = None,
    downstream_stage: str | None = None,
) -> tuple[dict[str, Any], list[Diagnostic]]:
    """Evaluate an optional carrier through the exact Decision Kernel authority."""
    if not isinstance(artifact, dict) or "continuation_assurance" not in artifact:
        return _projection("legacy_absent"), []
    document = {"continuation_assurance": copy.deepcopy(artifact.get("continuation_assurance"))}
    diagnostics, source_stage = _source_stage_diagnostics(artifact, document)
    if downstream_stage is None:
        diagnostics.append(diagnostic("PG_PCVP_DOWNSTREAM_STAGE_UNRESOLVED", "error", "The downstream Stage was not derived from the resolved handoff transition.", "$.handoff.target", validator_layer="INTEGRATION"))
    if any(item.severity == "error" for item in diagnostics):
        return _projection("invalid"), sort_diagnostics(_deduplicate(diagnostics))
    authority, authority_diags = verify_owner_authority(Path(repository_root), decision_kernel_repo, source_stage)
    diagnostics.extend(authority_diags)
    if authority is None:
        return _projection("insufficient_evidence"), sort_diagnostics(_deduplicate(diagnostics))
    response, execution_diags = run_owner_bridge(authority, document)
    diagnostics.extend(execution_diags)
    if response is None:
        return _projection("insufficient_evidence"), sort_diagnostics(_deduplicate(diagnostics))
    bundle = response.get("bundle")
    if not isinstance(bundle, dict) or bundle.get("result") != "PASS":
        diagnostics.append(diagnostic("PG_PCVP_OWNER_BUNDLE_REJECTED", "error", "The official owner bundle validator did not return PASS.", "$.continuation_assurance", owner_bundle=copy.deepcopy(bundle), validator_layer="OWNER_BUNDLE"))
        return _projection("invalid"), sort_diagnostics(_deduplicate(diagnostics))
    owner_result = response.get("carrier")
    if not isinstance(owner_result, dict):
        diagnostics.append(diagnostic("PG_PCVP_OWNER_RESPONSE_INVALID", "insufficient_evidence", "The owner bridge did not return a carrier result.", "$.continuation_assurance"))
        return _projection("insufficient_evidence"), sort_diagnostics(_deduplicate(diagnostics))
    if owner_result.get("accepted") is not True or owner_result.get("observed_layer") != "ACCEPT":
        diagnostics.extend(_owner_rejection_diagnostics(owner_result))
        return _projection("invalid"), sort_diagnostics(_deduplicate(diagnostics))
    profile, profile_diags = load_profile(authority)
    diagnostics.extend(profile_diags)
    if profile is None:
        status = "invalid" if any(item.severity == "error" for item in diagnostics) else "insufficient_evidence"
        return _projection(status), sort_diagnostics(_deduplicate(diagnostics))
    diagnostics.extend(profile_integration_diagnostics(profile, authority.profile_binding, document, source_stage=source_stage, downstream_stage=downstream_stage))
    ordered = sort_diagnostics(_deduplicate(diagnostics))
    if any(item.severity == "error" for item in ordered):
        return _projection("invalid"), ordered
    if any(item.severity == "insufficient_evidence" for item in ordered):
        return _projection("insufficient_evidence"), ordered
    continuation = document["continuation_assurance"]
    return _projection(
        "validated",
        policy_id=continuation.get("policy_id"),
        policy_version=continuation.get("policy_version"),
        source_stage=continuation.get("source_stage"),
        downstream_stage=downstream_stage,
        profile_id=profile.get("profile_id"),
        owner_observed_layer=owner_result.get("observed_layer"),
        owner_bundle_fixtures=copy.deepcopy(bundle.get("fixtures")),
        canonical_hash=canonical_sha256(document),
        carrier=document,
    ), ordered


def _source_stage_diagnostics(artifact: dict[str, Any], document: dict[str, Any]) -> tuple[list[Diagnostic], str | None]:
    producer = artifact.get("producer") if isinstance(artifact.get("producer"), dict) else {}
    expected = SOURCE_STAGE_BY_PRODUCER.get(producer.get("stage"))
    continuation = document.get("continuation_assurance")
    observed = continuation.get("source_stage") if isinstance(continuation, dict) else None
    diagnostics: list[Diagnostic] = []
    if expected is None:
        diagnostics.append(diagnostic("PG_PCVP_SOURCE_STAGE_UNSUPPORTED", "error", "The Producer stage has no PCVP Profile binding.", "$.producer.stage", actual=producer.get("stage"), validator_layer="INTEGRATION"))
        return diagnostics, None
    if observed != expected:
        diagnostics.append(diagnostic("PG_PCVP_SOURCE_STAGE_MISMATCH", "error", "source_stage does not match the Producer stage.", "$.continuation_assurance.source_stage", expected=expected, actual=observed, validator_layer="INTEGRATION"))
    return diagnostics, expected


def _owner_rejection_diagnostics(owner_result: dict[str, Any]) -> list[Diagnostic]:
    layer = owner_result.get("observed_layer")
    owner_diags = owner_result.get("diagnostics")
    result: list[Diagnostic] = []
    if isinstance(owner_diags, list):
        for item in owner_diags:
            if not isinstance(item, dict):
                continue
            owner_code = item.get("code")
            code = f"PG_{owner_code}" if isinstance(owner_code, str) and owner_code.startswith("PCVP_") else "PG_PCVP_OWNER_REJECTED"
            result.append(diagnostic(code, "error", "The official Decision Kernel validator rejected the carrier.", "$.continuation_assurance", owner_observed_layer=layer, owner_diagnostic=copy.deepcopy(item), validator_layer="OWNER_VALIDATOR"))
    if not result:
        result.append(diagnostic("PG_PCVP_OWNER_REJECTED", "error", "The official Decision Kernel validator rejected the carrier.", "$.continuation_assurance", owner_observed_layer=layer, validator_layer="OWNER_VALIDATOR"))
    if layer == "JSON_SCHEMA":
        result.append(diagnostic("PG_PCVP_CARRIER_SCHEMA_INVALID", "error", "The owner validator rejected the carrier at JSON Schema.", "$.continuation_assurance", owner_observed_layer=layer, validator_layer="OWNER_VALIDATOR"))
    return result


def _projection(status: str, **values: Any) -> dict[str, Any]:
    result: dict[str, Any] = {
        "status": status,
        "compatibility_mode": "DUAL_READ",
        "canonical_owner": CANONICAL_REPOSITORY,
        "canonical_commit": CANONICAL_COMMIT,
        "architecture_lock_id": ARCHITECTURE_LOCK_ID,
        "adoption_status": "not_yet_adopted",
        "activation_effect": "NONE",
    }
    if status == "validated":
        result.update(copy.deepcopy(values))
        result["canonical_sha256"] = result.pop("canonical_hash")
    return result


def _deduplicate(items: list[Diagnostic]) -> list[Diagnostic]:
    seen: set[tuple[str, str, str]] = set()
    result: list[Diagnostic] = []
    for item in items:
        key = (item.code, item.path, item.message)
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


# Stable compatibility aliases used by repository contract tests.
_expected_authority_paths = expected_authority_paths
_verify_owner_authority = verify_owner_authority
_run_owner_bridge = run_owner_bridge
_load_profile = load_profile
_profile_integration_diagnostics = profile_integration_diagnostics

__all__ = [
    "ARCHITECTURE_LOCK_ID",
    "BUNDLE_ROOT",
    "CANONICAL_COMMIT",
    "CANONICAL_REPOSITORY",
    "POLICY_ID",
    "POLICY_VERSION",
    "PROFILE_BINDINGS",
    "VALIDATOR_PATH",
    "OwnerAuthority",
    "inspect_optional_pcvp_carrier",
]
