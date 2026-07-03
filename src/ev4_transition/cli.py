from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .architect_to_ce import transition_from_local_paths
from .bundle_validator import BundleValidator
from .canonical_json import canonical_dumps, load_json_file
from .diagnostics import persian_summary
from .validator_runner import run_architect_validator, run_ce_validator


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ev4-transition")
    parser.add_argument("--schema-root", default="schemas")

    sub = parser.add_subparsers(dest="command", required=True)

    validate_parser = sub.add_parser("validate", help="Validate a Stage Evidence Bundle.")
    validate_parser.add_argument("bundle")
    validate_parser.add_argument("--require-evidence", action="append", default=[])
    validate_parser.add_argument("--format", choices=["json", "persian"], default="json")

    transition_parser = sub.add_parser("transition", help="Run a deterministic Project Gate transition.")
    transition_parser.add_argument("transition_name", choices=["architect-to-ce"])
    transition_parser.add_argument("bundle")
    transition_parser.add_argument("--architect-repo", required=True)
    transition_parser.add_argument("--ce-repo", required=True)
    transition_parser.add_argument("--lock", default="contracts/locks/architect-to-ce-transition.v1.lock.json")
    transition_parser.add_argument("--format", choices=["json", "persian"], default="json")

    inspect_parser = sub.add_parser("inspect", help="Inspect deterministic core metadata.")
    inspect_parser.add_argument("--format", choices=["json", "persian"], default="json")

    args = parser.parse_args(argv)

    if args.command == "validate":
        validator = BundleValidator(args.schema_root)
        result = validator.validate_file(args.bundle, required_evidence_ids=args.require_evidence)
        _emit(result, args.format)
        return _exit_for_status(result["status"])

    if args.command == "transition":
        bundle_path = Path(args.bundle)
        try:
            bundle = load_json_file(bundle_path)
        except json.JSONDecodeError as exc:
            payload = _simple_invalid("MALFORMED_JSON", "File is not valid JSON.", line=exc.lineno, column=exc.colno)
            _emit(payload, args.format)
            return 1
        except OSError as exc:
            payload = _simple_invalid("FILE_READ_ERROR", "File could not be read.", error_type=type(exc).__name__)
            _emit(payload, args.format)
            return 1
        result = transition_from_local_paths(bundle, args.schema_root, args.lock, args.architect_repo, args.ce_repo)
        if result.get("output") is not None:
            extras = []
            extras.extend(run_architect_validator(args.architect_repo, bundle["payload"]["data"]))
            extras.extend(run_ce_validator(args.ce_repo, result["output"]["payload"]["data"]))
            if extras:
                result = _append_external_diagnostics(result, [item.to_dict() for item in extras])
        _emit(result, args.format)
        return _exit_for_status(result["status"])

    info = {
        "package": "ev4-project-gate",
        "implemented": [
            "canonical_json",
            "sha256",
            "structured_diagnostics",
            "stage_bundle_validation",
            "transition_result_schema_foundation",
            "architect-to-ce transition",
            "minimal_cli"
        ],
        "not_implemented": [
            "ce-to-builder transition",
            "builder-to-responsive transition",
            "real EV4 artifact validation",
            "UI"
        ]
    }
    _emit(info, args.format)
    return 0


def _append_external_diagnostics(result: dict[str, Any], diagnostics: list[dict[str, Any]]) -> dict[str, Any]:
    combined = dict(result)
    combined["diagnostics"] = sorted(result.get("diagnostics", []) + diagnostics, key=lambda d: (d.get("path", "$"), d.get("severity", ""), d.get("code", ""), d.get("message", "")))
    if any(item["severity"] == "error" for item in combined["diagnostics"]):
        combined["status"] = "invalid"
        combined["output"] = None
        combined["hashes"]["target_payload"] = None
        combined["hashes"]["target_bundle"] = None
    elif any(item["severity"] == "insufficient_evidence" for item in combined["diagnostics"]):
        combined["status"] = "insufficient_evidence"
    return combined


def _simple_invalid(code: str, message: str, **details: Any) -> dict[str, Any]:
    return {"status": "invalid", "diagnostics": [{"code": code, "severity": "error", "message": message, "path": "$", "details": details}]}


def _exit_for_status(status: str) -> int:
    if status == "valid":
        return 0
    if status == "insufficient_evidence":
        return 2
    return 1


def _emit(payload: dict[str, Any], fmt: str) -> None:
    if fmt == "persian":
        if "status" in payload:
            print(persian_summary(payload["status"]))
        else:
            print("هسته قطعی پایتون آماده است؛ انتقال Architect → CE پیاده‌سازی شده و سایر انتقال‌ها هنوز پیاده‌سازی نشده‌اند.")
        return
    print(canonical_dumps(payload))


if __name__ == "__main__":
    raise SystemExit(main())
