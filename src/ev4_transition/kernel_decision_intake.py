from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Literal

from jsonschema import Draft202012Validator

from .canonical_json import bytes_sha256, canonical_sha256, load_json_file
from .contract_source import ContractSource, LocalCheckoutContractSource
from .diagnostics import Diagnostic, diagnostic, sort_diagnostics
from .kernel_decision_dependencies import KERNEL_ACCEPTED_COMMIT, KERNEL_INTAKE_RESULT_SCHEMA_ID, KERNEL_INTAKE_SCHEMA_ID, KERNEL_REPOSITORY
from .kernel_decision_lock import verify_kernel_semantic_lock
from .kernel_decision_binding import binding_diagnostics, scan_authored_fields, scan_forbidden_claims

PacketStatus = Literal["accepted", "repair_needed", "insufficient_evidence", "invalid"]


@dataclass(frozen=True)
class KernelAuditExecution:
    state: Literal["completed", "unavailable", "malformed"]
    audit: dict[str, Any] | None
    execution_record: dict[str, Any] | None = None
    diagnostics: tuple[Diagnostic, ...] = ()


@dataclass(frozen=True)
class KernelDecisionIntakeConfig:
    schema_root: Path
    lock: dict[str, Any]
    kernel_repo_root: Path | None = None
    project_gate_repo_root: Path | None = None
    timeout_seconds: float = 30


def kernel_decision_intake_from_local_paths(bundle: Any, *, schema_root: str | Path, lock_path: str | Path, kernel_repo: str | Path, project_gate_repo: str | Path, timeout_seconds: float = 30) -> dict[str, Any]:
    from .runners.kernel_decision import execute_kernel_l2_audit
    kernel_root, project_gate_root = Path(kernel_repo), Path(project_gate_repo)
    source = LocalCheckoutContractSource({KERNEL_REPOSITORY: kernel_root})
    config = KernelDecisionIntakeConfig(Path(schema_root), load_json_file(lock_path), kernel_root, project_gate_root, timeout_seconds)
    return run_kernel_decision_intake(bundle, source, config, audit_executor=lambda packet: execute_kernel_l2_audit(packet, kernel_repo_root=kernel_root, project_gate_repo_root=project_gate_root, timeout_seconds=timeout_seconds))


def run_kernel_decision_intake(bundle: Any, contract_source: ContractSource, config: KernelDecisionIntakeConfig, *, audit_executor: Callable[[dict[str, Any]], KernelAuditExecution] | None = None) -> dict[str, Any]:
    diagnostics: list[Diagnostic] = []
    accepted_requires = {key: False for key in ("kernel_pin_verified", "semantic_lock_verified", "intake_schema_valid", "packet_binding_valid", "l2_executed_all", "no_unsupported_claims")}
    accepted_requires["result_schema_valid"] = True
    bundle_schema = _load_schema(config.schema_root / "stage-bundle/stage-bundle.v1.schema.json", "PG.KERNEL_INTAKE.STAGE_BUNDLE_SCHEMA_UNAVAILABLE", diagnostics)
    intake_schema = _load_schema(config.schema_root / "kernel-decision-intake/kernel-decision-intake.v1.schema.json", "PG.KERNEL_INTAKE.INTAKE_SCHEMA_UNAVAILABLE", diagnostics)
    result_schema = _load_schema(config.schema_root / "kernel-decision-intake-result/kernel-decision-intake-result.v1.schema.json", "PG.KERNEL_INTAKE.RESULT_SCHEMA_UNAVAILABLE", diagnostics)
    if bundle_schema is not None:
        diagnostics.extend(_schema_errors(bundle_schema, bundle, "$", stage_bundle=True))
    data = _extract_data(bundle, diagnostics)
    scan_authored_fields(bundle, diagnostics)
    scan_forbidden_claims(bundle, diagnostics)
    if intake_schema is not None and data is not None:
        diagnostics.extend(_schema_errors(intake_schema, data, "$.payload.data"))
    pin = data.get("kernel_pin") if isinstance(data, dict) else None
    accepted_requires["kernel_pin_verified"] = isinstance(pin, dict) and pin.get("repository") == KERNEL_REPOSITORY and pin.get("accepted_commit") == KERNEL_ACCEPTED_COMMIT
    if not accepted_requires["kernel_pin_verified"]:
        diagnostics.append(diagnostic("PG.KERNEL_INTAKE.KERNEL_PIN_INVALID", "error", "Intake Kernel pin must match the approved immutable repository and commit.", "$.payload.data.kernel_pin"))
    lock_diagnostics = verify_kernel_semantic_lock(config.lock, contract_source)
    diagnostics.extend(lock_diagnostics)
    accepted_requires["semantic_lock_verified"] = not any(item.severity in {"error", "insufficient_evidence"} for item in lock_diagnostics)
    accepted_requires["intake_schema_valid"] = data is not None and not any(item.code in {"PG.KERNEL_INTAKE.INTAKE_SCHEMA_UNKNOWN", "PG.KERNEL_INTAKE.DECISION_RECORD_REQUIRED", "PG.KERNEL_INTAKE.RESOLVER_INPUT_REQUIRED", "PG.KERNEL_INTAKE.AUDIT_CONTEXT_REQUIRED", "PG.KERNEL_INTAKE.STAGE_BUNDLE_SCHEMA_INVALID"} or item.code.startswith("PG.KERNEL_INTAKE.SCHEMA_") for item in diagnostics)
    packets = data.get("decision_packets") if isinstance(data, dict) and isinstance(data.get("decision_packets"), list) else []
    by_index = binding_diagnostics(packets, contract_source)
    for items in by_index.values():
        diagnostics.extend(items)
    accepted_requires["packet_binding_valid"] = bool(packets) and not any(by_index.values())
    accepted_requires["no_unsupported_claims"] = not any(item.code in {"PG.KERNEL_INTAKE.UNSUPPORTED_ASSERTED_CLAIM", "PG.KERNEL_INTAKE.FORBIDDEN_CLAIM"} for item in diagnostics)
    global_blocking = [item for item in diagnostics if item.severity in {"error", "insufficient_evidence"}]
    packet_results: list[dict[str, Any]] = []
    for index, packet in enumerate(packets):
        packet_diagnostics = list(by_index.get(index, []))
        if global_blocking:
            severity = "error" if any(item.severity == "error" for item in global_blocking) else "insufficient_evidence"
            packet_diagnostics.append(diagnostic("PG.KERNEL_INTAKE.EXECUTION_BLOCKED", severity, "Kernel L2 execution was blocked by intake, pin, lock, policy, schema, or binding validation.", f"$.payload.data.decision_packets[{index}]"))
            execution = KernelAuditExecution("unavailable", None)
        elif audit_executor is None:
            execution = KernelAuditExecution("unavailable", None, diagnostics=(diagnostic("PG.KERNEL_INTAKE.KERNEL_EXECUTION_UNAVAILABLE", "insufficient_evidence", "Kernel L2 audit executor is unavailable.", f"$.payload.data.decision_packets[{index}]"),))
        else:
            try:
                execution = audit_executor(packet)
            except Exception as exc:
                execution = KernelAuditExecution("unavailable", None, diagnostics=(diagnostic("PG.KERNEL_INTAKE.KERNEL_EXECUTION_UNAVAILABLE", "insufficient_evidence", "Kernel L2 execution raised an exception.", f"$.payload.data.decision_packets[{index}]", error_type=type(exc).__name__),))
        packet_results.append(_packet_result(packet, index, execution, packet_diagnostics))
    accepted_requires["l2_executed_all"] = bool(packet_results) and all(item["l2_executed"] for item in packet_results)
    result = _build_result(bundle, data, config.lock, packet_results, diagnostics, accepted_requires, _overall_status(packet_results, diagnostics))
    return _finalize(result, result_schema, bundle, data, config.lock, packet_results, diagnostics, accepted_requires)


def _extract_data(bundle: Any, diagnostics: list[Diagnostic]) -> dict[str, Any] | None:
    if not isinstance(bundle, dict):
        diagnostics.append(diagnostic("PG.KERNEL_INTAKE.INPUT_NOT_OBJECT", "error", "Kernel intake must be a Stage Evidence Bundle object.", "$"))
        return None
    payload_schema, payload = bundle.get("payload_schema"), bundle.get("payload")
    if not isinstance(payload_schema, dict) or (payload_schema.get("id"), payload_schema.get("version"), payload_schema.get("owner_repository")) != (KERNEL_INTAKE_SCHEMA_ID, "1.0.0", "rezahh107/EV4-Project-Gate"):
        diagnostics.append(diagnostic("PG.KERNEL_INTAKE.INTAKE_SCHEMA_UNKNOWN", "error", "payload_schema must identify the Project Gate-owned KROAD-011 contract.", "$.payload_schema"))
    if not isinstance(payload, dict) or payload.get("schema_id") != KERNEL_INTAKE_SCHEMA_ID:
        diagnostics.append(diagnostic("PG.KERNEL_INTAKE.INTAKE_SCHEMA_UNKNOWN", "error", "payload.schema_id must identify the KROAD-011 contract.", "$.payload.schema_id"))
        return None
    data = payload.get("data")
    if not isinstance(data, dict):
        diagnostics.append(diagnostic("PG.KERNEL_INTAKE.SCHEMA_INVALID", "error", "KROAD-011 payload data must be an object.", "$.payload.data"))
        return None
    return data


def _load_schema(path: Path, code: str, diagnostics: list[Diagnostic]) -> dict[str, Any] | None:
    try:
        schema = load_json_file(path)
        Draft202012Validator.check_schema(schema)
        return schema
    except Exception as exc:
        diagnostics.append(diagnostic(code, "insufficient_evidence", "Required Project Gate schema is absent or invalid.", "$.schema_version", schema_path=str(path), error_type=type(exc).__name__))
        return None


def _schema_errors(schema: dict[str, Any], value: Any, base: str, *, stage_bundle: bool = False) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for error in sorted(Draft202012Validator(schema).iter_errors(value), key=lambda item: (list(item.absolute_path), item.message)):
        path = _join_path(base, list(error.absolute_path))
        code = "PG.KERNEL_INTAKE.STAGE_BUNDLE_SCHEMA_INVALID" if stage_bundle else "PG.KERNEL_INTAKE.SCHEMA_INVALID"
        missing = next((item for item in error.validator_value if item not in error.instance), None) if error.validator == "required" and isinstance(error.instance, dict) and isinstance(error.validator_value, list) else None
        if missing in {"decision_record", "resolver_input", "audit_context"}:
            code = {"decision_record": "PG.KERNEL_INTAKE.DECISION_RECORD_REQUIRED", "resolver_input": "PG.KERNEL_INTAKE.RESOLVER_INPUT_REQUIRED", "audit_context": "PG.KERNEL_INTAKE.AUDIT_CONTEXT_REQUIRED"}[missing]
            path += f".{missing}"
        elif error.validator == "enum" and path.endswith(".claim"):
            code = "PG.KERNEL_INTAKE.UNSUPPORTED_ASSERTED_CLAIM"
        elif error.validator == "pattern" and path.endswith("accepted_commit"):
            code = "PG.KERNEL_INTAKE.KERNEL_PIN_INVALID"
        diagnostics.append(diagnostic(code, "error", error.message, path, validator=error.validator))
    return sort_diagnostics(diagnostics)


def _packet_result(packet: Any, index: int, execution: KernelAuditExecution, packet_diagnostics: list[Diagnostic]) -> dict[str, Any]:
    safe = packet if isinstance(packet, dict) else {}
    base = f"$.payload.data.decision_packets[{index}]"
    project_gate = [*packet_diagnostics, *execution.diagnostics]
    upstream: list[dict[str, Any]] = []
    resolver_output = None
    human_override = False
    l2_executed = execution.state == "completed"
    if execution.state == "unavailable":
        if not any(item.code in {"PG.KERNEL_INTAKE.EXECUTION_BLOCKED", "PG.KERNEL_INTAKE.KERNEL_EXECUTION_UNAVAILABLE"} for item in project_gate):
            project_gate.append(diagnostic("PG.KERNEL_INTAKE.KERNEL_EXECUTION_UNAVAILABLE", "insufficient_evidence", "Official pinned Kernel L2 execution is unavailable.", base))
        status: PacketStatus = "invalid" if any(item.severity == "error" for item in project_gate) else "insufficient_evidence"
    elif execution.state == "malformed" or not isinstance(execution.audit, dict):
        project_gate.append(diagnostic("PG.KERNEL_INTAKE.KERNEL_OUTPUT_MALFORMED", "error", "Pinned Kernel bridge returned malformed structured output.", base))
        status = "invalid"
    else:
        audit = execution.audit
        audit_status, raw_diagnostics = audit.get("audit_status"), audit.get("diagnostics")
        if audit_status not in {"pass", "fail", "unsupported"} or not isinstance(raw_diagnostics, list):
            project_gate.append(diagnostic("PG.KERNEL_INTAKE.KERNEL_OUTPUT_MALFORMED", "error", "Pinned Kernel audit output is unknown.", base))
            status = "invalid"
        else:
            upstream = raw_diagnostics
            resolver_output = audit.get("resolver_output") if isinstance(audit.get("resolver_output"), dict) else None
            human_override = audit.get("human_override_observed") is True
            if audit_status == "fail":
                project_gate.append(diagnostic("PG.KERNEL_INTAKE.L2_FAILED", "error", "Pinned Kernel L2 audit returned fail.", base, upstream_codes=_upstream_codes(upstream)))
                status = "invalid"
            elif audit_status == "unsupported":
                project_gate.append(diagnostic("PG.KERNEL_INTAKE.L2_UNSUPPORTED", "insufficient_evidence", "Known family is not covered by pinned Resolver/L2.", base, upstream_codes=_upstream_codes(upstream)))
                status = "insufficient_evidence"
            elif resolver_output is not None and resolver_output.get("resolver_status") == "unresolvable":
                project_gate.append(diagnostic("PG.KERNEL_INTAKE.RESOLVER_UNRESOLVABLE", "insufficient_evidence", "Pinned Resolver output is unresolvable.", base))
                status = "insufficient_evidence"
            elif _has_code(upstream, "L2_DECISION_REQUIRES_REAUDIT") or _decision_record(safe).get("requires_reaudit") is True:
                project_gate.append(diagnostic("PG.KERNEL_INTAKE.REAUDIT_REQUIRED", "warning", "Decision requires re-audit.", f"{base}.decision_record.requires_reaudit"))
                status = "repair_needed"
            else:
                status = "accepted"
                if human_override:
                    project_gate.append(diagnostic("PG.KERNEL_INTAKE.HUMAN_OVERRIDE_OBSERVED", "info", "Explicit human override was observed by pinned Kernel L2.", f"{base}.decision_record.human_override"))
    record = _decision_record(safe)
    resolver = safe.get("resolver_input") if isinstance(safe.get("resolver_input"), dict) else {}
    audit_context = safe.get("audit_context") if isinstance(safe.get("audit_context"), dict) else {}
    packet_id = str(safe.get("packet_id", f"packet-{index}"))
    decision_id = str(safe.get("decision_id", record.get("decision_id", "unknown")))
    return {"packet_id": packet_id, "decision_id": decision_id, "decision_family_id": str(safe.get("decision_family_id", record.get("decision_family_id", "unknown"))), "status": status, "l2_executed": l2_executed, "human_override_observed": human_override, "project_gate_diagnostics": [item.to_dict() for item in sort_diagnostics(project_gate)], "upstream_diagnostics": upstream, "resolver_output": resolver_output, "decision_record_ref": {"packet_id": packet_id, "decision_id": decision_id, "sha256": _safe_hash(record)}, "source_evidence_refs": sorted(item for item in audit_context.get("source_evidence_refs", []) if isinstance(item, str)), "runtime_evidence_refs": sorted(item for item in audit_context.get("runtime_evidence_refs", []) if isinstance(item, str)), "hashes": {key: _hash(key.replace("_hash", ""), value) for key, value in {"packet_hash": safe, "decision_record_hash": record, "resolver_input_hash": resolver, "audit_context_hash": audit_context}.items()}, "provenance": safe.get("provenance") if isinstance(safe.get("provenance"), dict) else {}, "execution_record": execution.execution_record}


def _overall_status(packet_results: list[dict[str, Any]], diagnostics: list[Diagnostic]) -> PacketStatus:
    if any(item.severity == "error" for item in diagnostics) or any(item["status"] == "invalid" for item in packet_results):
        return "invalid"
    if any(item.severity == "insufficient_evidence" for item in diagnostics) or any(item["status"] == "insufficient_evidence" for item in packet_results):
        return "insufficient_evidence"
    if any(item["status"] == "repair_needed" for item in packet_results):
        return "repair_needed"
    return "accepted" if packet_results and all(item["status"] == "accepted" for item in packet_results) else "insufficient_evidence"


def _build_result(bundle: Any, data: dict[str, Any] | None, lock: dict[str, Any], packet_results: list[dict[str, Any]], diagnostics: list[Diagnostic], accepted_requires: dict[str, bool], status: PacketStatus) -> dict[str, Any]:
    packets = data.get("decision_packets", []) if isinstance(data, dict) and isinstance(data.get("decision_packets"), list) else []
    counts = {"provisional_count": sum(1 for packet in packets if isinstance(_decision_record(packet).get("provisional_status"), dict) and _decision_record(packet)["provisional_status"].get("is_provisional") is True), "human_override_count": sum(1 for item in packet_results if item["human_override_observed"]), "unresolved_decision_count": sum(1 for item in packet_results if item["status"] == "insufficient_evidence" or isinstance(item.get("resolver_output"), dict) and item["resolver_output"].get("resolver_status") == "unresolvable"), "accepted_decision_count": sum(1 for item in packet_results if item["status"] == "accepted"), "rejected_decision_count": sum(1 for item in packet_results if item["status"] == "invalid")}
    return {"schema_version": KERNEL_INTAKE_RESULT_SCHEMA_ID, "result_type": "kernel_decision_intake", "status": status, "kernel_pin": {"repository": KERNEL_REPOSITORY, "accepted_commit": KERNEL_ACCEPTED_COMMIT, "semantic_lock_sha256": _safe_hash(lock)}, "accepted_requires": dict(accepted_requires), "diagnostics": [item.to_dict() for item in sort_diagnostics(diagnostics)], "upstream_diagnostics": [{"packet_id": item["packet_id"], "diagnostics": item["upstream_diagnostics"]} for item in packet_results], "packet_results": packet_results, "derived_counts": counts, "decision_record_refs": [item["decision_record_ref"] for item in packet_results], "source_evidence_refs": sorted(({"packet_id": item["packet_id"], "reference": reference} for item in packet_results for reference in item["source_evidence_refs"]), key=lambda item: (item["packet_id"], item["reference"])), "runtime_evidence_refs": sorted(({"packet_id": item["packet_id"], "reference": reference} for item in packet_results for reference in item["runtime_evidence_refs"]), key=lambda item: (item["packet_id"], item["reference"])), "hashes": {"source_input_hash": _hash("source_input", bundle), "semantic_lock_hash": _hash("semantic_lock", lock)}, "provenance": {"source_bundle_id": str(bundle.get("bundle_id", "unknown")) if isinstance(bundle, dict) else "unknown", "source_bundle_provenance": bundle.get("provenance", {}) if isinstance(bundle, dict) and isinstance(bundle.get("provenance"), dict) else {}, "result_producer": "rezahh107/EV4-Project-Gate"}}


def _finalize(result: dict[str, Any], schema: dict[str, Any] | None, bundle: Any, data: dict[str, Any] | None, lock: dict[str, Any], packet_results: list[dict[str, Any]], diagnostics: list[Diagnostic], accepted_requires: dict[str, bool]) -> dict[str, Any]:
    if schema is None:
        return _build_result(bundle, data, lock, packet_results, [*diagnostics, diagnostic("PG.KERNEL_INTAKE.RESULT_SCHEMA_UNAVAILABLE", "insufficient_evidence", "Kernel intake result schema is unavailable.", "$.schema_version")], {**accepted_requires, "result_schema_valid": False}, "insufficient_evidence")
    errors = _schema_errors(schema, result, "$")
    if not errors:
        return result
    fallback = _build_result(bundle, data, lock, packet_results, [*diagnostics, *[diagnostic("PG.KERNEL_INTAKE.RESULT_SCHEMA_VALIDATION_FAILED", "error", item.message, item.path) for item in errors]], {**accepted_requires, "result_schema_valid": False}, "invalid")
    if list(Draft202012Validator(schema).iter_errors(fallback)):
        raise ValueError("KROAD-011 fail-closed result does not satisfy result schema")
    return fallback


def _decision_record(packet: Any) -> dict[str, Any]:
    if not isinstance(packet, dict):
        return {}
    value = packet.get("decision_record")
    return value if isinstance(value, dict) else {}


def _upstream_codes(items: list[Any]) -> list[str]:
    return sorted(item.get("code") for item in items if isinstance(item, dict) and isinstance(item.get("code"), str))


def _has_code(items: list[Any], code: str) -> bool:
    return code in _upstream_codes(items)


def _safe_hash(value: Any) -> str:
    try:
        return canonical_sha256(value)
    except Exception:
        return bytes_sha256(b"unhashable")


def _hash(scope: str, value: Any) -> dict[str, str]:
    return {"algorithm": "sha256", "scope": scope, "value": _safe_hash(value)}


def _join_path(base: str, parts: list[Any]) -> str:
    for part in parts:
        base += f"[{part}]" if isinstance(part, int) else f".{part}"
    return base
