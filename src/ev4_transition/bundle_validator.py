from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .canonical_json import CanonicalJsonError, canonical_sha256, load_json_file
from .diagnostics import Diagnostic, diagnostic, sort_diagnostics, status_from_diagnostics
from .provenance import canonical_payload_hash, preserve_provenance


class ResultValidationError(RuntimeError):
    """Raised if this library tries to emit an invalid result object."""


class BundleValidator:
    def __init__(self, schema_root: str | Path = "schemas") -> None:
        self.schema_root = Path(schema_root)
        self.bundle_schema = load_json_file(self.schema_root / "stage-bundle" / "stage-bundle.v1.schema.json")
        self.result_schema = load_json_file(self.schema_root / "transition-result" / "transition-result.v1.schema.json")
        self.bundle_validator = Draft202012Validator(self.bundle_schema)
        self.result_validator = Draft202012Validator(self.result_schema)

    def validate_bundle(self, bundle: Any, required_evidence_ids: list[str] | None = None) -> dict[str, Any]:
        diagnostics: list[Diagnostic] = []

        if not isinstance(bundle, dict):
            diagnostics.append(
                diagnostic(
                    "INPUT_NOT_OBJECT",
                    "error",
                    "Stage Evidence Bundle input must be a JSON object.",
                    "$",
                    observed_type=type(bundle).__name__,
                )
            )
            return self._result(bundle, None, diagnostics)

        for err in self._schema_errors(bundle):
            diagnostics.append(err)

        if not diagnostics:
            diagnostics.extend(self._semantic_diagnostics(bundle, required_evidence_ids or []))

        return self._result(bundle, bundle, diagnostics)

    def validate_file(self, path: str | Path, required_evidence_ids: list[str] | None = None) -> dict[str, Any]:
        try:
            return self.validate_bundle(load_json_file(path), required_evidence_ids)
        except json.JSONDecodeError as exc:
            diagnostics = [
                diagnostic(
                    "MALFORMED_JSON",
                    "error",
                    "File is not valid JSON.",
                    "$",
                    line=exc.lineno,
                    column=exc.colno,
                )
            ]
            return self._result(None, None, diagnostics)

    def validate_result(self, result: dict[str, Any]) -> None:
        errors = sorted(self.result_validator.iter_errors(result), key=lambda err: (list(err.path), err.message))
        if errors:
            messages = "; ".join(f"{_json_path(list(err.path))}: {err.message}" for err in errors)
            raise ResultValidationError(messages)

    def _schema_errors(self, bundle: dict[str, Any]) -> list[Diagnostic]:
        errors: list[Diagnostic] = []
        for err in sorted(self.bundle_validator.iter_errors(bundle), key=lambda item: (_json_path(list(item.path)), item.message)):
            errors.append(
                diagnostic(
                    "SCHEMA_VALIDATION_FAILED",
                    "error",
                    err.message,
                    _json_path(list(err.path)),
                )
            )
        return errors

    def _semantic_diagnostics(self, bundle: dict[str, Any], required_evidence_ids: list[str]) -> list[Diagnostic]:
        diagnostics: list[Diagnostic] = []

        evidence_ids = {item["id"] for item in bundle.get("evidence", [])}
        missing_required = sorted(set(required_evidence_ids) - evidence_ids)
        if missing_required:
            diagnostics.append(
                diagnostic(
                    "REQUIRED_EVIDENCE_MISSING",
                    "insufficient_evidence",
                    "Required evidence is missing; the validator will not invent it.",
                    "$.evidence",
                    missing_evidence=missing_required,
                )
            )

        if bundle.get("evidence_status") == "insufficient_evidence":
            diagnostics.append(
                diagnostic(
                    "BUNDLE_INSUFFICIENT_EVIDENCE",
                    "insufficient_evidence",
                    "The bundle explicitly declares unresolved or insufficient evidence.",
                    "$.evidence_status",
                    missing_evidence=bundle.get("missing_evidence", []),
                )
            )

        return diagnostics

    def _result(self, original: Any, bundle: dict[str, Any] | None, diagnostics: list[Diagnostic]) -> dict[str, Any]:
        ordered = sort_diagnostics(diagnostics)
        hashes = {
            "source_bundle_hash": self._safe_hash(original, "source_bundle"),
            "canonical_payload_hash": self._safe_payload_hash(bundle),
        }
        result = {
            "schema_version": "transition-result.v1",
            "result_type": "stage_bundle_validation",
            "status": status_from_diagnostics(ordered),
            "source_stage": bundle.get("stage") if bundle else None,
            "diagnostics": [item.to_dict() for item in ordered],
            "hashes": hashes,
            "provenance": preserve_provenance(bundle) if bundle else {"source_provenance": None, "produced_by": None},
            "output": None,
        }
        self.validate_result(result)
        return result

    @staticmethod
    def _safe_hash(value: Any, scope: str) -> dict[str, str] | None:
        if value is None:
            return None
        try:
            return {
                "algorithm": "sha256",
                "canonicalization": "ev4-canonical-json.v1",
                "scope": scope,
                "value": canonical_sha256(value),
            }
        except CanonicalJsonError:
            return None

    @staticmethod
    def _safe_payload_hash(bundle: dict[str, Any] | None) -> dict[str, str] | None:
        if not bundle or not isinstance(bundle.get("payload"), dict):
            return None
        return canonical_payload_hash(bundle["payload"])


def _json_path(parts: list[Any]) -> str:
    out = "$"
    for part in parts:
        if isinstance(part, int):
            out += f"[{part}]"
        else:
            out += f".{part}"
    return out
