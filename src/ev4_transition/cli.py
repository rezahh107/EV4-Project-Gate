from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .architect_to_ce import TransitionValidatorHooks, transition_from_local_paths
from .behavioral_coverage import CoverageSourceError, inspect_coverage_source, validate_coverage_source
from .bundle_validator import BundleValidator, ResultValidationError
from .canonical_json import canonical_dumps, load_json_file
from .diagnostics import persian_summary
from .presentation.status_mapping import exit_code_for_status
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

    coverage_parser = sub.add_parser("coverage", help="Inspect or validate Behavioral Rule Coverage.")
    coverage_sub = coverage_parser.add_subparsers(dest="coverage_command", required=True)
    coverage_inspect = coverage_sub.add_parser("inspect", help="Inspect behavioral coverage without running a transition.")
    coverage_inspect.add_argument("source", nargs="?", default="docs/BEHAVIORAL_RULE_COVERAGE.md")
    coverage_inspect.add_argument("--schema", default="schemas/behavioral-coverage/behavioral-coverage.v1.schema.json")
    coverage_validate = coverage_sub.add_parser("validate", help="Validate behavioral coverage thresholds.")
    coverage_validate.add_argument("source", nargs="?", default="docs/BEHAVIORAL_RULE_COVERAGE.md")
    coverage_validate.add_argument("--schema", default="schemas/behavioral-coverage/behavioral-coverage.v1.schema.json")

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
        hooks = TransitionValidatorHooks(
            architect=lambda payload: run_architect_validator(args.architect_repo, payload),
            ce=lambda payload, source_bundle: run_ce_validator(args.ce_repo, payload, source_bundle),
        )
        try:
            result = transition_from_local_paths(bundle, args.schema_root, args.lock, args.architect_repo, args.ce_repo, validator_hooks=hooks)
        except ResultValidationError as exc:
            result = _simple_invalid("TRANSITION_RESULT_SCHEMA_VALIDATION_FAILED", "Transition result schema validation failed.", error=str(exc))
        _emit(result, args.format)
        return _exit_for_status(result["status"])

    if args.command == "coverage":
        return _coverage_command(args)

    info = {
        "package": "ev4-project-gate",
        "implemented": [
            "canonical_json",
            "sha256",
            "structured_diagnostics",
            "stage_bundle_validation",
            "transition_result_schema_foundation",
            "status_presentation_mapping",
            "behavioral_coverage_validation",
            "architect-to-ce transition",
            "minimal_cli",
        ],
        "not_implemented": [
            "ce-to-builder transition",
            "builder-to-responsive transition",
            "real EV4 artifact validation",
            "UI",
        ],
    }
    _emit(info, args.format)
    return 0


def _coverage_command(args: argparse.Namespace) -> int:
    try:
        if args.coverage_command == "inspect":
            report = inspect_coverage_source(args.source, args.schema)
            print(canonical_dumps(report.to_dict()))
            return 0
        if args.coverage_command == "validate":
            report = validate_coverage_source(args.source, args.schema)
            print(canonical_dumps(report.to_dict()))
            return 0 if report.status == "thresholds_met" else 1
    except CoverageSourceError as exc:
        payload = {
            "schema_version": "behavioral-coverage-report.v1",
            "source": getattr(args, "source", None),
            "status": "source_unparseable",
            "rule_count": 0,
            "diagnostics": [
                {"code": "PG_BRC_SOURCE_UNPARSEABLE", "severity": "error", "message": str(exc), "path": "$"}
            ],
        }
        print(canonical_dumps(payload))
        return 2
    raise AssertionError(f"unknown coverage command: {args.coverage_command}")


def _simple_invalid(code: str, message: str, **details: Any) -> dict[str, Any]:
    return {"status": "invalid", "diagnostics": [{"code": code, "severity": "error", "message": message, "path": "$", "details": details}]}


def _exit_for_status(status: str) -> int:
    return exit_code_for_status(status)


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
