from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .canonical_json import canonical_sha256, load_json_file
from .diagnostics import Diagnostic, diagnostic, sort_diagnostics
from .evidence_truth import derive_evidence_classification, synthetic_indicators

VALIDATOR_ID = "ev4-producer-gate-export-validator"
VALIDATOR_VERSION = "1.1.0"
SCHEMA_ID = "https://ev4.local/contracts/common/producer-gate-export.v1.schema.json"
STAGE_BUNDLE_ID = "https://ev4.local/schemas/stage-bundle/stage-bundle.v1.schema.json"


class ProducerGateExportValidator:
    def __init__(self, repository_root: str | Path = ".", *, operational: bool = True) -> None:
        self.repository_root = Path(repository_root)
        self.operational = operational
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
            if self.operational:
                diagnostics.extend(self._operational_truth_diagnostics(item))
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
            ids: dict[Any, int] = {}
            ords: dict[Any, int] = {}
            ord_values: list[int] = []
            for i, stage in enumerate(manifest):
                if not isinstance(stage, dict):
                    continue
                sid, ordinal = stage.get("stage_id"), stage.get("ordinal")
                if sid in ids:
                    d.append(diagnostic("PG_EXPORT_DUPLICATE_STAGE_ID", "error", "Stage IDs must be unique.", f"$.stage_manifest[{i}].stage_id", first_index=ids[sid]))
                else:
                    ids[sid] = i
                if ordinal in ords:
                    d.append(diagnostic("PG_EXPORT_DUPLICATE_STAGE_ORDINAL", "error", "Stage ordinals must be unique.", f"$.stage_manifest[{i}].ordinal", first_index=ords[ordinal]))
                else:
                    ords[ordinal] = i
                if isinstance(ordinal, int):
                    ord_values.append(ordinal)
                output = stage.get("output") if isinstance(stage.get("output"), dict) else {}
                if stage.get("status") == "complete" and output.get("present") is not True:
                    d.append(diagnostic("PG_EXPORT_COMPLETE_STAGE_WITHOUT_OUTPUT", "error", "Complete stages must declare a present output artifact.", f"$.stage_manifest[{i}].output"))
                if output.get("present") is True:
                    if not output.get("artifact_ref"):
                        d.append(diagnostic("PG_EXPORT_OUTPUT_REF_MISSING", "error", "Present output requires artifact_ref.", f"$.stage_manifest[{i}].output.artifact_ref"))
                    hash_record = output.get("artifact_hash")
                    if not (isinstance(hash_record, dict) and hash_record.get("algorithm") == "sha256" and _is_sha256(hash_record.get("value"))):
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
            d.append(diagnostic("PG_EXPORT_FINAL_BUNDLE_COMMIT_MISMATCH", "error", "Final Stage Bundle producer commit must match export producer.", "$.final_stage_bundle.produced_by.commit_sha"))
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

    def _operational_truth_diagnostics(self, artifact: dict[str, Any]) -> list[Diagnostic]:
        diagnostics: list[Diagnostic] = []
        final = artifact.get("final_stage_bundle") if isinstance(artifact.get("final_stage_bundle"), dict) else None
        handoff = artifact.get("handoff") if isinstance(artifact.get("handoff"), dict) else {}
        if final is None:
            return diagnostics
        indicators = synthetic_indicators(final)
        classification = derive_evidence_classification(final, source_resolved=True, hash_verified=True, owner_validation_status="not_available")
        if handoff.get("allowed") is True and classification == "synthetic":
            diagnostics.append(diagnostic("PG_EXPORT_SYNTHETIC_HANDOFF_FORBIDDEN", "error", "Synthetic Producer evidence cannot authorize an operational handoff.", "$.handoff.allowed", classification="synthetic", synthetic_indicators=indicators))
        manifest = artifact.get("stage_manifest") if isinstance(artifact.get("stage_manifest"), list) else []
        if handoff.get("allowed") is not True or not manifest:
            return diagnostics
        consequential = [(index, stage) for index, stage in enumerate(manifest) if isinstance(stage, dict) and stage.get("mandatory") is True and stage.get("status") == "complete" and isinstance(stage.get("output"), dict) and stage["output"].get("present") is True]
        if not consequential:
            return diagnostics
        index, stage = max(consequential, key=lambda pair: int(pair[1].get("ordinal", -1)))
        output = stage["output"]
        artifact_ref = output.get("artifact_ref")
        hash_record = output.get("artifact_hash") if isinstance(output.get("artifact_hash"), dict) else {}
        declared = hash_record.get("value")
        scope = hash_record.get("scope")
        if artifact_ref == "final_stage_bundle":
            actual = canonical_sha256(final)
            if scope != "canonical_json":
                diagnostics.append(diagnostic("PG_EXPORT_FINAL_HASH_SCOPE_INVALID", "error", "Embedded final_stage_bundle requires canonical_json hash scope.", f"$.stage_manifest[{index}].output.artifact_hash.scope", expected="canonical_json", actual=scope))
            if declared != actual:
                diagnostics.append(diagnostic("PG_EXPORT_FINAL_HASH_MISMATCH", "error", "Declared final Stage Bundle hash does not match the embedded object.", f"$.stage_manifest[{index}].output.artifact_hash.value", declared=declared, actual=actual))
            return diagnostics
        resolved, path_diag = self._resolve_reference(artifact_ref)
        if path_diag is not None:
            diagnostics.append(path_diag)
            return diagnostics
        assert resolved is not None
        raw = resolved.read_bytes()
        actual = hashlib.sha256(raw).hexdigest()
        if scope != "file_bytes":
            diagnostics.append(diagnostic("PG_EXPORT_FINAL_HASH_SCOPE_INVALID", "error", "Referenced final artifact requires file_bytes hash scope.", f"$.stage_manifest[{index}].output.artifact_hash.scope", expected="file_bytes", actual=scope))
        if declared != actual:
            diagnostics.append(diagnostic("PG_EXPORT_FINAL_HASH_MISMATCH", "error", "Declared final artifact hash does not match the referenced bytes.", f"$.stage_manifest[{index}].output.artifact_hash.value", declared=declared, actual=actual))
        try:
            referenced = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            diagnostics.append(diagnostic("PG_EXPORT_FINAL_ARTIFACT_INVALID_JSON", "error", "Referenced final artifact is not valid JSON.", f"$.stage_manifest[{index}].output.artifact_ref"))
        else:
            if canonical_sha256(referenced) != canonical_sha256(final):
                diagnostics.append(diagnostic("PG_EXPORT_FINAL_ARTIFACT_DRIFT", "error", "Referenced final artifact does not match embedded final_stage_bundle.", f"$.stage_manifest[{index}].output.artifact_ref"))
        return diagnostics

    def _resolve_reference(self, artifact_ref: Any) -> tuple[Path | None, Diagnostic | None]:
        if not isinstance(artifact_ref, str) or not artifact_ref:
            return None, diagnostic("PG_EXPORT_OUTPUT_REF_MISSING", "error", "Consequential output requires artifact_ref.", "$.stage_manifest")
        try:
            root = self.repository_root.resolve(strict=True)
            candidate = (root / artifact_ref).resolve(strict=True)
            candidate.relative_to(root)
        except FileNotFoundError:
            return None, diagnostic("PG_EXPORT_REFERENCED_ARTIFACT_MISSING", "error", "Consequential referenced artifact does not exist.", "$.stage_manifest", artifact_ref=artifact_ref)
        except (OSError, RuntimeError, ValueError):
            return None, diagnostic("PG_EXPORT_REFERENCED_ARTIFACT_PATH_UNSAFE", "error", "Consequential referenced artifact path is unsafe.", "$.stage_manifest", artifact_ref=artifact_ref)
        if not candidate.is_file():
            return None, diagnostic("PG_EXPORT_REFERENCED_ARTIFACT_NOT_FILE", "error", "Consequential referenced artifact must be a regular file.", "$.stage_manifest", artifact_ref=artifact_ref)
        return candidate, None


def _is_sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _deduplicate(items: list[Diagnostic]) -> list[Diagnostic]:
    seen: set[tuple[str, str, str]] = set()
    result: list[Diagnostic] = []
    for item in items:
        key = (item.code, item.path, item.message)
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def _path(parts: list[Any]) -> str:
    value = "$"
    for part in parts:
        value += f"[{part}]" if isinstance(part, int) else f".{part}"
    return value
