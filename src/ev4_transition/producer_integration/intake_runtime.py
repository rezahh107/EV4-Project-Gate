from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from ev4_transition.canonical_json import canonical_dumps, load_json_file
from ev4_transition.io.secure_snapshot import JsonInputSnapshot
from ev4_transition.producer_gate_export import ProducerGateExportValidator

from .join_preflight import validate_join_evidence_packet
from .operational_export import OperationalProducerGateExportValidator
from .registry import validate_adoption_registry

TRANSITIONS = {
    "ce-intake": "architect-to-ce",
    "builder-intake": "ce-to-builder",
    "responsive-intake": "builder-to-responsive",
    "final-evidence-gate": "final-evidence-gate",
}

_TRANSITION_DEFAULTS = {
    "architect-to-ce": {
        "lock": "contracts/locks/architect-to-ce-transition.v1.lock.json",
        "output": "ce-input.json",
        "receipt": "project-gate-a2c-receipt.json",
    },
    "ce-to-builder": {
        "lock": "contracts/locks/ce-to-builder-transition.v1.lock.json",
        "output": "builder-input.json",
        "receipt": "project-gate-c2b-receipt.json",
    },
}


def load_transition_targets(
    path: str | Path = "contracts/transition-targets/ev4-transition-targets.v1.json",
) -> dict[str, str]:
    data = load_json_file(path)
    targets = data.get("targets") if isinstance(data, dict) else []
    return {
        item["handoff_target"]: item["transition_id"]
        for item in targets
        if isinstance(item, dict)
        and "handoff_target" in item
        and "transition_id" in item
    }


def intake_producer_export(
    artifact: Any,
    *,
    transition_name: str | None = None,
    registry_path: str | Path = "contracts/producer-adoption/ev4-producer-adoption-set.v1.json",
    targets_path: str | Path = "contracts/transition-targets/ev4-transition-targets.v1.json",
    repository_root: str | Path = ".",
) -> dict[str, Any]:
    """Validate the immutable Producer envelope and routing without authorizing dispatch."""

    original = canonical_dumps(artifact) if isinstance(artifact, (dict, list)) else None
    diagnostics: list[dict[str, Any]] = []
    if not isinstance(artifact, dict):
        return _result(
            "invalid",
            None,
            None,
            [
                _diag(
                    "PG_EXPORT_SCHEMA_INVALID",
                    "error",
                    "$",
                    "Producer Gate Export input must be a JSON object.",
                    "Producer",
                )
            ],
        )

    item = copy.deepcopy(artifact)
    acquisition = item.get("acquisition_mode") if isinstance(item.get("acquisition_mode"), dict) else None
    if acquisition is None or "mode" not in acquisition:
        diagnostics.append(
            _diag(
                "PG-P05-ACQUISITION-MODE-MISSING",
                "error",
                "$.acquisition_mode",
                "Explicit acquisition mode is required.",
                "Producer",
            )
        )
    elif acquisition.get("mode") != "producer_emitted_gate_artifact":
        diagnostics.append(
            _diag(
                "PG-P05-ACQUISITION-MODE-MISMATCH",
                "error",
                "$.acquisition_mode.mode",
                "Selected mode must match producer_emitted_gate_artifact.",
                "Producer",
            )
        )
    if isinstance(acquisition, dict) and acquisition.get("silent_fallback_allowed") is not False:
        diagnostics.append(
            _diag(
                "PG-P05-SILENT-FALLBACK-FORBIDDEN",
                "error",
                "$.acquisition_mode.silent_fallback_allowed",
                "Silent fallback is forbidden.",
                "Project Gate",
            )
        )
    if isinstance(acquisition, dict) and acquisition.get("evidence_sources") not in (
        None,
        ["producer_emitted_gate_artifact"],
    ):
        diagnostics.append(
            _diag(
                "PG-P05-EVIDENCE-MIXING-FORBIDDEN",
                "error",
                "$.acquisition_mode.evidence_sources",
                "Evidence mixing is forbidden.",
                "Project Gate",
            )
        )

    # Intake is intentionally contract/routing-only. Runtime authorization is
    # revalidated immediately before a supported dispatch with actual owner roots.
    common = ProducerGateExportValidator(repository_root, operational=False).validate(item)
    diagnostics.extend(_with_repair_owner(common.get("diagnostics", []), default_owner="Producer"))

    registry_result = validate_adoption_registry(registry_path)
    if registry_result["status"] != "valid":
        diagnostics.extend(registry_result["diagnostics"])
    try:
        registry = load_json_file(registry_path)
    except Exception:
        registry = {}
    if not isinstance(registry, dict):
        registry = {}

    producer = item.get("producer") if isinstance(item.get("producer"), dict) else {}
    match = None
    producers = registry.get("producers", []) if isinstance(registry.get("producers"), list) else []
    for candidate in producers:
        if isinstance(candidate, dict) and candidate.get("stage") == producer.get("stage"):
            match = candidate
    if not match:
        diagnostics.append(
            _diag(
                "PG-P05-PRODUCER-REGISTRY-INVALID",
                "error",
                "$.producer.stage",
                "Producer stage is not adopted.",
                "Project Gate",
            )
        )
    else:
        if producer.get("repository") != match.get("repository"):
            diagnostics.append(
                _diag(
                    "PG-P05-PRODUCER-REGISTRY-INVALID",
                    "error",
                    "$.producer.repository",
                    "Producer repository does not match adoption registry.",
                    "Producer",
                )
            )
        runtime_pin = match.get("runtime_pin") if isinstance(match.get("runtime_pin"), dict) else {}
        if producer.get("commit_sha") != runtime_pin.get("merged_commit_sha"):
            diagnostics.append(
                _diag(
                    "PG-P05-PRODUCER-REGISTRY-INVALID",
                    "error",
                    "$.producer.commit_sha",
                    "Producer commit must match merged runtime pin.",
                    "Producer",
                )
            )

    target = (item.get("handoff") or {}).get("target") if isinstance(item.get("handoff"), dict) else None
    resolved = load_transition_targets(targets_path).get(target)
    if resolved is None:
        diagnostics.append(
            _diag(
                "PG-P05-HANDOFF-TARGET-INVALID",
                "error",
                "$.handoff.target",
                "Unknown handoff target.",
                "Producer",
            )
        )
    if transition_name and resolved and transition_name != resolved:
        diagnostics.append(
            _diag(
                "PG-P05-HANDOFF-TARGET-INVALID",
                "error",
                "$.handoff.target",
                "Handoff target does not match selected transition.",
                "Producer",
                expected_transition=transition_name,
                actual_transition=resolved,
            )
        )
    if original is not None and canonical_dumps(artifact) != original:
        diagnostics.append(
            _diag(
                "PG-P05-PRODUCER-ARTIFACT-MUTATED",
                "error",
                "$",
                "Producer artifact was mutated during intake.",
                "Project Gate",
            )
        )

    status = _status_from_diagnostics(diagnostics)
    return _result(
        status,
        producer,
        resolved,
        sorted(diagnostics, key=lambda item: (item["path"], item["code"])),
    )


def transition_producer_export(
    transition_name: str,
    artifact: Any,
    *,
    join_packet_path: str | Path | None = None,
    snapshot: JsonInputSnapshot | None = None,
    schema_root: str | Path = "schemas",
    lock_path: str | Path | None = None,
    architect_repo: str | Path | None = None,
    ce_repo: str | Path | None = None,
    builder_repo: str | Path | None = None,
    project_gate_repo: str | Path = ".",
    output_path: str | Path | None = None,
    receipt_path: str | Path | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Dispatch from current runtime evidence, without a persistent authorization packet.

    ``join_packet_path`` remains an explicit legacy compatibility hook. It has no
    default and therefore cannot authorize normal execution.
    """

    legacy_preflight: dict[str, Any] | None = None
    if join_packet_path is not None:
        legacy_preflight = validate_join_evidence_packet(join_packet_path)
        if legacy_preflight.get("status") != "passed":
            result = _result(
                "invalid",
                None,
                None,
                _with_repair_owner(legacy_preflight.get("diagnostics", [])),
            )
            result["transition_id"] = transition_name
            result["join_evidence_preflight"] = legacy_preflight
            return result

    result = intake_producer_export(
        artifact,
        transition_name=transition_name,
        **kwargs,
    )
    result["transition_id"] = transition_name
    if legacy_preflight is not None:
        result["join_evidence_preflight"] = legacy_preflight
    if result["status"] == "invalid":
        return result

    resolved = result.get("resolved_transition")
    if resolved == "architect-to-ce":
        missing: list[str] = []
        if snapshot is None:
            missing.append("immutable source snapshot")
        if architect_repo is None:
            missing.append("Architect checkout")
        if ce_repo is None:
            missing.append("CE checkout")
        if missing:
            return _runtime_evidence_required(
                result,
                "PG_A2C_RUNTIME_EVIDENCE_REQUIRED",
                "Producer-emitted A2C dispatch requires immutable source bytes and exact owner checkouts.",
                missing,
            )
        operational_failure = _operational_truth_failure(
            result,
            artifact,
            project_gate_root=project_gate_repo,
            artifact_root=architect_repo,
        )
        if operational_failure is not None:
            return operational_failure

        from .a2c_dispatch import dispatch_architect_export

        defaults = _defaults_for_dispatched_transition(resolved)
        return dispatch_architect_export(
            artifact,
            result,
            snapshot=snapshot,
            schema_root=schema_root,
            lock_path=lock_path if lock_path is not None else defaults["lock"],
            architect_repo=architect_repo,
            ce_repo=ce_repo,
            project_gate_repo=project_gate_repo,
            output_path=output_path if output_path is not None else defaults["output"],
            receipt_path=receipt_path if receipt_path is not None else defaults["receipt"],
        )

    if resolved == "ce-to-builder":
        missing = []
        if snapshot is None:
            missing.append("immutable source snapshot")
        if ce_repo is None:
            missing.append("CE checkout")
        if builder_repo is None:
            missing.append("Builder checkout")
        if missing:
            return _runtime_evidence_required(
                result,
                "PG_C2B_RUNTIME_EVIDENCE_REQUIRED",
                "Producer-emitted C2B dispatch requires immutable source bytes and exact CE and Builder checkouts.",
                missing,
            )
        operational_failure = _operational_truth_failure(
            result,
            artifact,
            project_gate_root=project_gate_repo,
            artifact_root=ce_repo,
        )
        if operational_failure is not None:
            return operational_failure

        from .c2b_dispatch import dispatch_ce_export

        defaults = _defaults_for_dispatched_transition(resolved)
        return dispatch_ce_export(
            artifact,
            result,
            snapshot=snapshot,
            schema_root=schema_root,
            lock_path=lock_path if lock_path is not None else defaults["lock"],
            ce_repo=ce_repo,
            builder_repo=builder_repo,
            project_gate_repo=project_gate_repo,
            output_path=output_path if output_path is not None else defaults["output"],
            receipt_path=receipt_path if receipt_path is not None else defaults["receipt"],
        )

    result["producer_validation"] = {
        "status": "passed",
        "official_validator_status": "not_run",
        "note": "The shared intake resolved a transition that is not yet dispatched by producer-emitted runtime integration.",
    }
    result["downstream_artifact"] = {"status": "not_fabricated"}
    return result


def _operational_truth_failure(
    result: dict[str, Any],
    artifact: Any,
    *,
    project_gate_root: str | Path,
    artifact_root: str | Path,
) -> dict[str, Any] | None:
    validation = OperationalProducerGateExportValidator(
        project_gate_root,
        artifact_root,
    ).validate(artifact)
    if validation.get("status") == "valid":
        return None
    failed = copy.deepcopy(result)
    failed["status"] = "invalid"
    failed["common_validation"] = "failed"
    failed["handoff_allowed"] = False
    failed["diagnostics"] = _with_repair_owner(
        validation.get("diagnostics", []),
        default_owner="Project Gate",
    )
    failed["producer_validation"] = {
        "status": "failed",
        "official_validator_status": "not_run",
        "evidence_classification": "runtime_derived",
    }
    failed["downstream_artifact"] = {"status": "not_published"}
    return failed


def _defaults_for_dispatched_transition(transition_name: str) -> dict[str, str]:
    return _TRANSITION_DEFAULTS[transition_name]


def _runtime_evidence_required(
    result: dict[str, Any],
    code: str,
    message: str,
    missing: list[str],
) -> dict[str, Any]:
    result["status"] = "insufficient_evidence"
    result["diagnostics"] = [
        _diag(
            code,
            "insufficient_evidence",
            "$",
            message,
            "Project Gate",
            missing=missing,
        )
    ]
    result["producer_validation"] = {
        "status": "not_run",
        "official_validator_status": "not_run",
    }
    result["downstream_artifact"] = {"status": "not_published"}
    return result


def _status_from_diagnostics(diagnostics: list[dict[str, Any]]) -> str:
    if any(item.get("severity") == "error" for item in diagnostics):
        return "invalid"
    if any(item.get("severity") == "insufficient_evidence" for item in diagnostics):
        return "insufficient_evidence"
    return "accepted"


def _result(
    status: str,
    producer: Any,
    transition: Any,
    diagnostics: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_version": "producer-emitted-transition-result.v1",
        "status": status,
        "acquisition_mode": "producer_emitted_gate_artifact",
        "producer": producer or {},
        "resolved_transition": transition,
        "common_validation": "passed" if status == "accepted" else "failed",
        "handoff_allowed": False,
        "diagnostics": diagnostics,
    }


def _diag(
    code: str,
    severity: str,
    path: str,
    message: str,
    owner: str,
    **details: Any,
) -> dict[str, Any]:
    return {
        "code": code,
        "severity": severity,
        "path": path,
        "message": message,
        "details": details,
        "repair_owner": owner,
    }


def _with_repair_owner(
    diagnostics: Any,
    *,
    default_owner: str = "Project Gate",
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    if not isinstance(diagnostics, list):
        return result
    for item in diagnostics:
        if isinstance(item, dict):
            result.append(
                {
                    **item,
                    "repair_owner": item.get("repair_owner", default_owner),
                }
            )
    return sorted(
        result,
        key=lambda item: (item.get("path", "$"), item.get("code", "")),
    )
