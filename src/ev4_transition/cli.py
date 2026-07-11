from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .architect_to_ce import TransitionValidatorHooks, transition_from_local_paths
from .transitions.builder_to_responsive import transition_from_local_paths as builder_to_responsive_from_local_paths
from .transitions.ce_to_builder import transition_from_local_paths as ce_to_builder_from_local_paths
from .transitions.final_gate import final_gate_from_local_paths
from .behavioral_coverage import CoverageSourceError, inspect_coverage_source, validate_coverage_source
from .bundle_validator import BundleValidator, ResultValidationError
from .canonical_json import canonical_dumps, load_json_file
from .presentation.status_mapping import exit_code_for_status
from .reports import render_plain_summary
from .validator_runner import run_architect_validator, run_ce_validator
from .producer_integration.intake import transition_producer_export

_CAPABILITY_STATUS_PATH = Path(__file__).resolve().parent / "data" / "capability-status.v1.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ev4-transition")
    parser.add_argument("--schema-root", default="schemas")

    sub = parser.add_subparsers(dest="command", required=True)

    validate_parser = sub.add_parser("validate", help="Validate a Stage Evidence Bundle.")
    validate_parser.add_argument("bundle")
    validate_parser.add_argument("--require-evidence", action="append", default=[])
    validate_parser.add_argument("--format", choices=["json", "persian"], default="json")

    transition_parser = sub.add_parser("transition", help="Run a deterministic Project Gate transition.")
    transition_parser.add_argument("transition_name", choices=["architect-to-ce", "ce-to-builder", "builder-to-responsive", "final-evidence-gate"])
    transition_parser.add_argument("bundle")
    transition_parser.add_argument("--architect-repo")
    transition_parser.add_argument("--ce-repo")
    transition_parser.add_argument("--builder-repo")
    transition_parser.add_argument("--responsive-repo")
    transition_parser.add_argument("--project-gate-repo")
    transition_parser.add_argument("--lock")
    transition_parser.add_argument("--format", choices=["json", "persian"], default="json")
    transition_parser.add_argument("--acquisition-mode", choices=["pinned_owner_file_computation", "producer_emitted_gate_artifact"], default="pinned_owner_file_computation")

    coverage_parser = sub.add_parser("coverage", help="Inspect or validate Behavioral Rule Coverage.")
    coverage_sub = coverage_parser.add_subparsers(dest="coverage_command", required=True)
    coverage_inspect = coverage_sub.add_parser("inspect", help="Inspect behavioral coverage without running a transition.")
    coverage_inspect.add_argument("source", nargs="?", default="docs/BEHAVIORAL_RULE_COVERAGE.md")
    coverage_inspect.add_argument("--schema", default="schemas/behavioral-coverage/behavioral-coverage.v1.schema.json")
    coverage_validate = coverage_sub.add_parser("validate", help="Validate behavioral coverage thresholds.")
    coverage_validate.add_argument("source", nargs="?", default="docs/BEHAVIORAL_RULE_COVERAGE.md")
    coverage_validate.add_argument("--schema", default="schemas/behavioral-coverage/behavioral-coverage.v1.schema.json")

    inspect_parser = sub.add_parser("inspect", help="Inspect deterministic core metadata and layered capability truth.")
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
        if args.acquisition_mode == "producer_emitted_gate_artifact":
            result = transition_producer_export(args.transition_name, bundle, repository_root=args.schema_root and ".")
            _emit(result, args.format)
            return _exit_for_status(result["status"])
        preflight = _transition_preflight(args)
        if preflight is not None:
            _emit(preflight, args.format)
            return _exit_for_status(preflight["status"])
        try:
            result = _run_transition(args, bundle)
        except ResultValidationError as exc:
            result = _simple_invalid("TRANSITION_RESULT_SCHEMA_VALIDATION_FAILED", "Transition result schema validation failed.", error=str(exc))
        _emit(result, args.format)
        return _exit_for_status(result["status"])

    if args.command == "coverage":
        return _coverage_command(args)

    info = _load_capability_status()
    _emit(info, args.format)
    return 0



def _run_transition(args: argparse.Namespace, bundle: dict[str, Any]) -> dict[str, Any]:
    if args.transition_name == "architect-to-ce":
        hooks = TransitionValidatorHooks(
            architect=lambda payload: run_architect_validator(args.architect_repo, payload),
            ce=lambda payload, source_bundle: run_ce_validator(args.ce_repo, payload, source_bundle),
        )
        return transition_from_local_paths(
            bundle,
            args.schema_root,
            args.lock or "contracts/locks/architect-to-ce-transition.v1.lock.json",
            args.architect_repo,
            args.ce_repo,
            validator_hooks=hooks,
        )
    if args.transition_name == "ce-to-builder":
        return ce_to_builder_from_local_paths(
            bundle,
            args.schema_root,
            args.lock or "contracts/locks/ce-to-builder-transition.v1.lock.json",
            args.ce_repo,
            args.builder_repo,
        )
    if args.transition_name == "builder-to-responsive":
        return builder_to_responsive_from_local_paths(
            bundle,
            args.schema_root,
            args.lock or "contracts/locks/builder-to-responsive-transition.v1.lock.json",
            args.builder_repo,
            args.responsive_repo,
        )
    if args.transition_name == "final-evidence-gate":
        return final_gate_from_local_paths(
            bundle,
            args.schema_root,
            args.lock or "contracts/locks/final-gate.v1.lock.json",
            args.project_gate_repo,
            args.responsive_repo,
        )
    return _simple_insufficient("CLI_TRANSITION_NOT_WIRED", "Transition is not wired in the public CLI.", transition_name=args.transition_name)


def _transition_preflight(args: argparse.Namespace) -> dict[str, Any] | None:
    required_by_transition = {
        "architect-to-ce": ["architect_repo", "ce_repo"],
        "ce-to-builder": ["ce_repo", "builder_repo"],
        "builder-to-responsive": ["builder_repo", "responsive_repo"],
        "final-evidence-gate": ["project_gate_repo", "responsive_repo"],
    }
    required = required_by_transition.get(args.transition_name, [])
    for field in required:
        value = getattr(args, field, None)
        if isinstance(value, str):
            value = value.strip()
            setattr(args, field, value)
        option = "--" + field.replace("_", "-")
        if not value:
            return _simple_insufficient("CLI_LOCAL_PATH_REQUIRED", "A local checkout path is required for this guarded transition.", option=option, transition_name=args.transition_name)
        if _looks_like_url(value):
            return _simple_insufficient("CLI_GITHUB_URL_REJECTED", "GitHub URLs are rejected; provide a local checkout path so pinned file bytes and owner tools can be verified.", option=option, transition_name=args.transition_name)
        if not Path(value).is_dir():
            return _simple_insufficient("CLI_LOCAL_PATH_NOT_FOUND", "Local checkout path was not found.", option=option, path=value, transition_name=args.transition_name)
    return None


def _looks_like_url(value: str) -> bool:
    lowered = value.lower()
    return lowered.startswith(("http://", "https://", "git@")) or "github.com" in lowered


def _simple_insufficient(code: str, message: str, **details: Any) -> dict[str, Any]:
    return {"status": "insufficient_evidence", "diagnostics": [{"code": code, "severity": "insufficient_evidence", "message": message, "path": "$", "details": details}]}


def _load_capability_status() -> dict[str, Any]:
    payload = load_json_file(_CAPABILITY_STATUS_PATH)
    capabilities = payload.get("capabilities")
    ce_to_builder = capabilities.get("ce_to_builder") if isinstance(capabilities, dict) else None
    expected = {
        "orchestration_baseline": "implemented",
        "cli_exposure": "guarded",
        "owner_fixture_integration": "verified",
        "real_non_synthetic_handoff": "insufficient_evidence",
    }
    if payload.get("schema_version") != "ev4-project-gate-capability-status.v1" or ce_to_builder != expected:
        raise ValueError("packaged capability truth is invalid")
    for guarded_name in ["ce-to-builder", "builder-to-responsive", "final-evidence-gate"]:
        if guarded_name not in payload.get("public_cli_transitions", []):
            raise ValueError(f"{guarded_name} guarded CLI exposure is not recorded")
    return payload



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
            print(render_plain_summary(payload), end="")
        else:
            print("هسته قطعی و Architect → CE به‌صورت functional در CLI فعال‌اند؛ CE → Builder، Builder → Responsive و Final Evidence Gate فقط به‌صورت guarded/fail-closed در CLI موجودند و شواهد real non-synthetic همچنان insufficient_evidence است.")
        return
    print(canonical_dumps(payload))


if __name__ == "__main__":
    raise SystemExit(main())
