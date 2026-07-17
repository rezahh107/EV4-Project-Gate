from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .canonical_json import load_json_file
from .diagnostics import Diagnostic, diagnostic, sort_diagnostics

VALIDATOR_ID = "ev4-producer-gate-export-validator"
VALIDATOR_VERSION = "1.0.0"
SCHEMA_ID = "https://ev4.local/contracts/common/producer-gate-export.v1.schema.json"
STAGE_BUNDLE_ID = "https://ev4.local/schemas/stage-bundle/stage-bundle.v1.schema.json"


class ProducerGateExportValidator:
    def __init__(self, repository_root: str | Path = ".") -> None:
        self.repository_root = Path(repository_root)
        self.schema = load_json_file(self.repository_root / "contracts/common/producer-gate-export.v1.schema.json")
        self.stage_bundle_schema = load_json_file(self.repository_root / "schemas/stage-bundle/stage-bundle.v1.schema.json")
        runtime_schema = copy.deepcopy(self.schema)
        runtime_schema["properties"]["final_stage_bundle"] = self.stage_bundle_schema
        runtime_schema["$defs"]["hash"] = self.stage_bundle_schema["$defs"]["hashRecord"]
        self._validator = Draft202012Validator(runtime_schema)

    def validate(self, artifact: Any) -> dict[str, Any]:
        item = copy.deepcopy(artifact)
        diagnostics: list[Diagnostic] = []
        for error in sorted(self._validator.iter_errors(item), key=lambda e: (_path(list(e.absolute_path)), e.message)):
            diagnostics.append(diagnostic("PG_EXPORT_SCHEMA_INVALID", "error", error.message, _path(list(error.absolute_path))))
        if isinstance(item, dict):
            diagnostics.extend(self._semantic_diagnostics(item))
            validation = item.get("validation") if isinstance(item.get("validation"), dict) else {}
            if any(x.severity == "error" for x in diagnostics) and (validation.get("schema_valid") is True or validation.get("semantic_valid") is True):
                diagnostics.append(diagnostic("PG_EXPORT_SELF_VALIDATION_OVERCLAIM", "error", "Artifact self-validation flags cannot claim valid when validation errors exist.", "$.validation"))
        ordered = sort_diagnostics(_deduplicate(diagnostics))
        return {
            "schema_version": "producer-gate-export-validation-result.v1",
            "validator_id": VALIDATOR_ID,
            "validator_version": VALIDATOR_VERSION,
            "status": "invalid" if any(d.severity == "error" for d in ordered) else "valid",
            "diagnostics": [d.to_dict() for d in ordered],
        }

    def _semantic_diagnostics(self, artifact: dict[str, Any]) -> list[Diagnostic]:
        d: list[Diagnostic] = []
        if artifact.get("schema_version") != "producer-gate-export.v1":
            d.append(diagnostic("PG_EXPORT_SCHEMA_INVALID", "error", "Producer Gate Export must not use a Stage Bundle envelope identity.", "$.schema_version"))
        manifest = artifact.get("stage_manifest")
        handoff = artifact.get("handoff") if isinstance(artifact.get("handoff"), dict) else {}
        producer = artifact.get("producer") if isinstance(artifact.get("producer"), dict) else {}
        final = artifact.get("final_stage_bundle") if isinstance(artifact.get("final_stage_bundle"), dict) else {}
        if isinstance(manifest, list):
            ids: dict[Any, int] = {}; ords: dict[Any, int] = {}; ord_values: list[int] = []
            for i, stage in enumerate(manifest):
                if not isinstance(stage, dict): continue
                sid, ordinal = stage.get("stage_id"), stage.get("ordinal")
                if sid in ids: d.append(diagnostic("PG_EXPORT_DUPLICATE_STAGE_ID", "error", "Stage IDs must be unique.", f"$.stage_manifest[{i}].stage_id", first_index=ids[sid]))
                else: ids[sid] = i
                if ordinal in ords: d.append(diagnostic("PG_EXPORT_DUPLICATE_STAGE_ORDINAL", "error", "Stage ordinals must be unique.", f"$.stage_manifest[{i}].ordinal", first_index=ords[ordinal]))
                else: ords[ordinal] = i
                if isinstance(ordinal, int): ord_values.append(ordinal)
                output = stage.get("output") if isinstance(stage.get("output"), dict) else {}
                if stage.get("status") == "complete" and output.get("present") is not True:
                    d.append(diagnostic("PG_EXPORT_COMPLETE_STAGE_WITHOUT_OUTPUT", "error", "Complete stages must declare a present output artifact.", f"$.stage_manifest[{i}].output"))
                if output.get("present") is True:
                    if not output.get("artifact_ref"):
                        d.append(diagnostic("PG_EXPORT_OUTPUT_REF_MISSING", "error", "Present output requires artifact_ref.", f"$.stage_manifest[{i}].output.artifact_ref"))
                    hash_record = output.get("artifact_hash")
                    if not (isinstance(hash_record, dict) and hash_record.get("algorithm") == "sha256" and isinstance(hash_record.get("value"), str) and len(hash_record.get("value")) == 64):
                        d.append(diagnostic("PG_EXPORT_OUTPUT_INTEGRITY_MISSING", "error", "Present output requires a valid SHA-256 hash record.", f"$.stage_manifest[{i}].output.artifact_hash"))
                if handoff.get("allowed") is True and stage.get("mandatory") is True:
                    if stage.get("status") in {"not_run", "insufficient_evidence"}:
                        d.append(diagnostic("PG_EXPORT_HANDOFF_ALLOWED_WITH_MISSING_MANDATORY_STAGE", "error", "Handoff cannot be allowed while a mandatory stage is missing or not run.", f"$.stage_manifest[{i}].status"))
                    if stage.get("status") == "blocked":
                        d.append(diagnostic("PG_EXPORT_HANDOFF_ALLOWED_WITH_BLOCKED_MANDATORY_STAGE", "error", "Handoff cannot be allowed while a mandatory stage is blocked.", f"$.stage_manifest[{i}].status"))
            if ord_values != sorted(ord_values):
                d.append(diagnostic("PG_EXPORT_STAGE_MANIFEST_OUT_OF_ORDER", "error", "Stage manifest ordinals must be sorted ascending.", "$.stage_manifest"))
        if handoff.get("allowed") is True and handoff.get("blocking_diagnostics"):
            d.append(diagnostic("PG_EXPORT_HANDOFF_ALLOWED_WITH_BLOCKING_DIAGNOSTICS", "error", "Handoff cannot be allowed with blocking diagnostics.", "$.handoff.blocking_diagnostics"))
        if handoff.get("allowed") is False and not handoff.get("failure_reasons"):
            d.append(diagnostic("PG_EXPORT_HANDOFF_DISALLOWED_WITHOUT_FAILURE_REASON", "error", "Disallowed handoff requires structured failure reasons.", "$.handoff.failure_reasons"))
        if handoff.get("allowed") is True and handoff.get("status") not in {"successful", "successful_with_flags"}:
            d.append(diagnostic("PG_EXPORT_SELF_VALIDATION_OVERCLAIM", "error", "Handoff allowed status combination is invalid.", "$.handoff.status"))
        if handoff.get("allowed") is False and handoff.get("status") in {"successful", "successful_with_flags"}:
            d.append(diagnostic("PG_EXPORT_SELF_VALIDATION_OVERCLAIM", "error", "Handoff disallowed status combination is invalid.", "$.handoff.status"))
        produced_by = final.get("produced_by") if isinstance(final.get("produced_by"), dict) else {}
        payload_schema = final.get("payload_schema") if isinstance(final.get("payload_schema"), dict) else {}
        if producer.get("repository") and produced_by.get("repository") and producer.get("repository") != produced_by.get("repository"):
            d.append(diagnostic("PG_EXPORT_FINAL_BUNDLE_PRODUCER_MISMATCH", "error", "Final Stage Bundle producer repository must match export producer.", "$.final_stage_bundle.produced_by.repository"))
        if producer.get("commit_sha") and produced_by.get("commit_sha") and producer.get("commit_sha") != produced_by.get("commit_sha"):
            d.append(diagnostic("PG_EXPORT_FINAL_BUNDLE_COMMIT_MISMATCH", "error", "Final Stage Bundle producer commit must match export producer commit.", "$.final_stage_bundle.produced_by.commit_sha"))
        if producer.get("stage") and final.get("stage") and producer.get("stage") != final.get("stage"):
            d.append(diagnostic("PG_EXPORT_FINAL_BUNDLE_STAGE_MISMATCH", "error", "Final Stage Bundle stage must match export producer stage.", "$.final_stage_bundle.stage"))
        if producer.get("repository") and payload_schema.get("owner_repository") and producer.get("repository") != payload_schema.get("owner_repository"):
            d.append(diagnostic("PG_EXPORT_FINAL_BUNDLE_PAYLOAD_OWNER_MISMATCH", "error", "Final Stage Bundle payload owner must match export producer repository.", "$.final_stage_bundle.payload_schema.owner_repository"))
        acquisition = artifact.get("acquisition_mode") if isinstance(artifact.get("acquisition_mode"), dict) else {}
        if acquisition.get("silent_fallback_allowed") is not False:
            d.append(diagnostic("PG_EXPORT_SILENT_FALLBACK_FORBIDDEN", "error", "Silent fallback between acquisition modes is forbidden.", "$.acquisition_mode.silent_fallback_allowed"))
        if acquisition.get("mode") != "producer_emitted_gate_artifact":
            d.append(diagnostic("PG_EXPORT_ACQUISITION_MODE_UNKNOWN", "error", "Unknown acquisition mode.", "$.acquisition_mode.mode"))
        validation = artifact.get("validation") if isinstance(artifact.get("validation"), dict) else {}
        prior_errors = [x for x in d if x.severity == "error" and x.code != "PG_EXPORT_SELF_VALIDATION_OVERCLAIM"]
        if prior_errors and (validation.get("schema_valid") is True or validation.get("semantic_valid") is True):
            d.append(diagnostic("PG_EXPORT_SELF_VALIDATION_OVERCLAIM", "error", "Artifact self-validation flags cannot claim valid when validation errors exist.", "$.validation"))
        return d


def _deduplicate(items: list[Diagnostic]) -> list[Diagnostic]:
    seen: set[tuple[str, str, str]] = set(); result: list[Diagnostic] = []
    for item in items:
        key = (item.code, item.path, item.message)
        if key not in seen:
            seen.add(key); result.append(item)
    return result


def _path(parts: list[Any]) -> str:
    value = "$"
    for part in parts:
        value += f"[{part}]" if isinstance(part, int) else f".{part}"
    return value
