from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from ev4_transition.canonical_json import canonical_dumps, load_json_file
from ev4_transition.io.secure_snapshot import JsonInputSnapshot
from ev4_transition.producer_gate_export import ProducerGateExportValidator

from .join_preflight import validate_join_evidence_packet
from .registry import validate_adoption_registry

TRANSITIONS = {
    "ce-intake": "architect-to-ce",
    "builder-intake": "ce-to-builder",
    "responsive-intake": "builder-to-responsive",
    "final-evidence-gate": "final-evidence-gate",
}


def load_transition_targets(path: str | Path = "contracts/transition-targets/ev4-transition-targets.v1.json") -> dict[str, str]:
    data = load_json_file(path)
    targets = data.get("targets") if isinstance(data, dict) else []
    return {item["handoff_target"]: item["transition_id"] for item in targets if isinstance(item, dict) and "handoff_target" in item and "transition_id" in item}


def intake_producer_export(
    artifact: Any,
    *,
    transition_name: str | None = None,
    registry_path: str | Path = "contracts/producer-adoption/ev4-producer-adoption-set.v1.json",
    targets_path: str | Path = "contracts/transition-targets/ev4-transition-targets.v1.json",
    repository_root: str | Path = ".",
) -> dict[str, Any]:
    original = canonical_dumps(artifact) if isinstance(artifact, (dict, list)) else None
    diags: list[dict[str, Any]] = []
    status = "accepted"
    if not isinstance(artifact, dict):
        return _result(
            "invalid",
            None,
            None,
            [_diag("PG_EXPORT_SCHEMA_INVALID", "error", "$", "Producer Gate Export input must be a JSON object.", "Producer")],
        )

    item = copy.deepcopy(artifact)
    acq = item.get("acquisition_mode") if isinstance(item.get("acquisition_mode"), dict) else None
    if acq is None or "mode" not in acq:
        diags.append(_diag("PG-P05-ACQUISITION-MODE-MISSING", "error", "$.acquisition_mode", "Explicit acquisition mode is required.", "Producer"))
    elif acq.get("mode") != "producer_emitted_gate_artifact":
        diags.append(_diag("PG-P05-ACQUISITION-MODE-MISMATCH", "error", "$.acquisition_mode.mode", "Selected mode must match producer_emitted_gate_artifact.", "Producer"))
    if isinstance(acq, dict) and acq.get("silent_fallback_allowed") is not False:
        diags.append(_diag("PG-P05-SILENT-FALLBACK-FORBIDDEN", "error", "$.acquisition_mode.silent_fallback_allowed", "Silent fallback is forbidden.", "Project Gate"))
    if isinstance(acq, dict) and acq.get("evidence_sources") not in (None, ["producer_emitted_gate_artifact"]):
        diags.append(_diag("PG-P05-EVIDENCE-MIXING-FORBIDDEN", "error", "$.acquisition_mode.evidence_sources", "Evidence mixing is forbidden.", "Project Gate"))

    common = ProducerGateExportValidator(repository_root).validate(item)
    for d in common.get("diagnostics", []):
        diags.append({**d, "repair_owner": d.get("repair_owner", "Producer")})

    reg_result = validate_adoption_registry(registry_path)
    if reg_result["status"] != "valid":
        diags.extend(reg_result["diagnostics"])
    try:
        reg = load_json_file(registry_path)
    except Exception:
        reg = {}
    if not isinstance(reg, dict):
        reg = {}

    prod = item.get("producer") if isinstance(item.get("producer"), dict) else {}
    match = None
    for p in reg.get("producers", []) if isinstance(reg.get("producers"), list) else []:
        if isinstance(p, dict) and p.get("stage") == prod.get("stage"):
            match = p
    if not match:
        diags.append(_diag("PG-P05-PRODUCER-REGISTRY-INVALID", "error", "$.producer.stage", "Producer stage is not adopted.", "Project Gate"))
    else:
        if prod.get("repository") != match.get("repository"):
            diags.append(_diag("PG-P05-PRODUCER-REGISTRY-INVALID", "error", "$.producer.repository", "Producer repository does not match adoption registry.", "Producer"))
        runtime_pin = match.get("runtime_pin") if isinstance(match.get("runtime_pin"), dict) else {}
        if prod.get("commit_sha") != runtime_pin.get("merged_commit_sha"):
            diags.append(_diag("PG-P05-PRODUCER-REGISTRY-INVALID", "error", "$.producer.commit_sha", "Producer commit must match merged runtime pin.", "Producer"))

    target = (item.get("handoff") or {}).get("target") if isinstance(item.get("handoff"), dict) else None
    targets = load_transition_targets(targets_path)
    resolved = targets.get(target)
    if resolved is None:
        diags.append(_diag("PG-P05-HANDOFF-TARGET-INVALID", "error", "$.handoff.target", "Unknown handoff target.", "Producer"))
    if transition_name and resolved and transition_name != resolved:
        diags.append(_diag("PG-P05-HANDOFF-TARGET-INVALID", "error", "$.handoff.target", "Handoff target does not match selected transition.", "Producer", expected_transition=transition_name, actual_transition=resolved))
    if original is not None and canonical_dumps(artifact) != original:
        diags.append(_diag("PG-P05-PRODUCER-ARTIFACT-MUTATED", "error", "$", "Producer artifact was mutated during intake.", "Project Gate"))

    if any(d["severity"] == "error" for d in diags):
        status = "invalid"
    elif any(d["severity"] == "insufficient_evidence" for d in diags):
        status = "insufficient_evidence"
    return _result(status, prod, resolved, sorted(diags, key=lambda x: (x["path"], x["code"])))


def transition_producer_export(
    transition_name: str,
    artifact: Any,
    *,
    join_packet_path: str | Path = "docs/evidence/JOIN_EVIDENCE_PACKET_v1.json",
    snapshot: JsonInputSnapshot | None = None,
    schema_root: str | Path = "schemas",
    lock_path: str | Path = "contracts/locks/architect-to-ce-transition.v1.lock.json",
    architect_repo: str | Path | None = None,
    ce_repo: str | Path | None = None,
    project_gate_repo: str | Path = ".",
    output_path: str | Path = "ce-input.json",
    receipt_path: str | Path = "project-gate-a2c-receipt.json",
    **kwargs: Any,
) -> dict[str, Any]:
    preflight = validate_join_evidence_packet(join_packet_path)
    if preflight.get("status") != "passed":
        result = _result("invalid", None, None, _with_repair_owner(preflight.get("diagnostics", [])))
        result["transition_id"] = transition_name
        result["join_evidence_preflight"] = preflight
        return result

    result = intake_producer_export(artifact, transition_name=transition_name, **kwargs)
    result["transition_id"] = transition_name
    result["join_evidence_preflight"] = preflight
    if result["status"] == "invalid":
        return result

    if result.get("resolved_transition") != "architect-to-ce":
        result["producer_validation"] = {
            "status": "passed",
            "official_validator_status": "not_run",
            "note": "The shared intake resolved a non-A2C target; this task does not dispatch other transitions.",
        }
        result["downstream_artifact"] = {"status": "not_fabricated"}
        return result

    missing = []
    if snapshot is None:
        missing.append("immutable source snapshot")
    if architect_repo is None:
        missing.append("Architect checkout")
    if ce_repo is None:
        missing.append("CE checkout")
    if missing:
        result["status"] = "insufficient_evidence"
        result["diagnostics"] = [
            _diag(
                "PG_A2C_RUNTIME_EVIDENCE_REQUIRED",
                "insufficient_evidence",
                "$",
                "Producer-emitted A2C dispatch requires immutable source bytes and exact owner checkouts.",
                "Project Gate",
                missing=missing,
            )
        ]
        result["producer_validation"] = {"status": "not_run", "official_validator_status": "not_run"}
        result["downstream_artifact"] = {"status": "not_published"}
        return result

    from .a2c_dispatch import dispatch_architect_export

    dispatched = dispatch_architect_export(
        artifact,
        result,
        snapshot=snapshot,
        schema_root=schema_root,
        lock_path=lock_path,
        architect_repo=architect_repo,
        ce_repo=ce_repo,
        project_gate_repo=project_gate_repo,
        output_path=output_path,
        receipt_path=receipt_path,
    )
    dispatched["join_evidence_preflight"] = preflight
    return dispatched


def _result(status: str, producer: Any, transition: Any, diagnostics: list[dict[str, Any]]) -> dict[str, Any]:
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


def _diag(code: str, severity: str, path: str, message: str, owner: str, **details: Any) -> dict[str, Any]:
    return {"code": code, "severity": severity, "path": path, "message": message, "details": details, "repair_owner": owner}


def _with_repair_owner(diagnostics: Any) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    if not isinstance(diagnostics, list):
        return result
    for item in diagnostics:
        if isinstance(item, dict):
            result.append({**item, "repair_owner": item.get("repair_owner", "Project Gate")})
    return sorted(result, key=lambda x: (x.get("path", "$"), x.get("code", "")))
