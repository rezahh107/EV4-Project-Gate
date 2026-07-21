from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from .behavioral_coverage import CoverageSourceError, inspect_coverage_source, validate_coverage_source
from .bundle_validator import BundleValidator
from .canonical_json import canonical_dumps, load_json_file
from .presentation.status_mapping import exit_code_for_status
from .reports import render_plain_summary
from .service import GateRequest, RepoPaths, cli_transition_names, contract_for_service, run_gate_request, service_choice_for_cli

_CAPABILITY_STATUS_PATH = Path(__file__).resolve().parent / "data" / "capability-status.v1.json"
_REPO_FIELD_TO_ARG = {
    "project_gate_repo_path": "project_gate_repo",
    "architect_repo_path": "architect_repo",
    "ce_repo_path": "ce_repo",
    "builder_repo_path": "builder_repo",
    "responsive_repo_path": "responsive_repo",
    "kernel_repo_path": "kernel_repo",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ev4-transition")
    parser.add_argument("--schema-root", default="schemas")
    sub = parser.add_subparsers(dest="command", required=True)

    validate_parser = sub.add_parser("validate", help="Validate a Stage Evidence Bundle.")
    validate_parser.add_argument("bundle")
    validate_parser.add_argument("--require-evidence", action="append", default=[])
    validate_parser.add_argument("--format", choices=["json", "persian"], default="json")

    transition_parser = sub.add_parser("transition", help="Run a deterministic Project Gate transition.")
    transition_parser.add_argument("transition_name", choices=cli_transition_names())
    transition_parser.add_argument("bundle")
    transition_parser.add_argument("--architect-repo")
    transition_parser.add_argument("--ce-repo")
    transition_parser.add_argument("--builder-repo")
    transition_parser.add_argument("--responsive-repo")
    transition_parser.add_argument("--project-gate-repo")
    transition_parser.add_argument("--kernel-repo")
    transition_parser.add_argument("--lock")
    transition_parser.add_argument("--output")
    transition_parser.add_argument("--receipt-output")
    transition_parser.add_argument("--format", choices=["json", "persian"], default="json")
    transition_parser.add_argument(
        "--acquisition-mode",
        choices=["pinned_owner_file_computation", "producer_emitted_gate_artifact"],
        default="pinned_owner_file_computation",
    )

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
        result = BundleValidator(args.schema_root).validate_file(args.bundle, required_evidence_ids=args.require_evidence)
        _emit(result, args.format)
        return _exit_for_status(result["status"])

    if args.command == "transition":
        service_choice = service_choice_for_cli(args.transition_name)
        preflight_failure = _transition_preflight(args, service_choice)
        if preflight_failure is not None:
            _emit(preflight_failure, args.format)
            return _exit_for_status(preflight_failure["status"])

        request = GateRequest(
            transition_choice=service_choice,  # type: ignore[arg-type]
            input_json_path=args.bundle,
            repo_paths=RepoPaths(
                project_gate_repo_path=args.project_gate_repo or ".",
                architect_repo_path=args.architect_repo,
                ce_repo_path=args.ce_repo,
                builder_repo_path=args.builder_repo,
                responsive_repo_path=args.responsive_repo,
                kernel_repo_path=args.kernel_repo,
            ),
            acquisition_mode=args.acquisition_mode,
            schema_root=args.schema_root,
            lock_path=args.lock,
            output_path=args.output,
            receipt_path=args.receipt_output,
        )
        response = run_gate_request(request)
        payload = _cli_payload(response.to_dict())
        _emit(payload, args.format)
        return _exit_for_status(str(payload.get("status", "invalid")))

    if args.command == "coverage":
        return _coverage_command(args)

    info = _load_capability_status()
    _emit(info, args.format)
    return 0


def _cli_payload(response: dict[str, Any]) -> dict[str, Any]:
    engine = response.get("engine_result")
    if isinstance(engine, dict):
        payload = dict(engine)
        if response.get("service_diagnostics"):
            existing = list(payload.get("diagnostics") or [])
            payload["diagnostics"] = existing + list(response["service_diagnostics"])
        return payload
    return {
        "schema_version": "project-gate-service-result.v1",
        "result_type": "service_layer_failure",
        "status": response.get("status", "invalid"),
        "transition_choice": response.get("transition_choice"),
        "diagnostics": list(response.get("service_diagnostics") or []),
        "handoff_allowed": False,
        "output": None,
    }


def _transition_preflight(args: argparse.Namespace, service_choice: str | None = None) -> dict[str, Any] | None:
    choice = service_choice or service_choice_for_cli(args.transition_name)
    contract = contract_for_service(choice)
    repo_fields = contract.producer_required_repo_fields if args.acquisition_mode == "producer_emitted_gate_artifact" else contract.required_repo_fields
    for repo_field in repo_fields:
        arg_field = _REPO_FIELD_TO_ARG[repo_field]
        value = getattr(args, arg_field, None)
        if isinstance(value, str):
            value = value.strip()
            setattr(args, arg_field, value)
        option = "--" + arg_field.replace("_", "-")
        if not value:
            return _simple_insufficient(
                "CLI_LOCAL_PATH_REQUIRED",
                "A local checkout path is required for this guarded transition.",
                option=option,
                transition_name=args.transition_name,
            )
        if _looks_like_url(value):
            return _simple_insufficient(
                "CLI_GITHUB_URL_REJECTED",
                "GitHub URLs are rejected; provide a local checkout path.",
                option=option,
                transition_name=args.transition_name,
            )
        if not Path(value).is_dir():
            return _simple_insufficient(
                "CLI_LOCAL_PATH_NOT_FOUND",
                "Local checkout path was not found.",
                option=option,
                path=value,
                transition_name=args.transition_name,
            )
    return None


def _looks_like_url(value: str) -> bool:
    lowered = value.lower()
    return lowered.startswith(("http://", "https://", "git@")) or "github.com" in lowered


def _simple_insufficient(code: str, message: str, **details: Any) -> dict[str, Any]:
    return {
        "status": "insufficient_evidence",
        "diagnostics": [{"code": code, "severity": "insufficient_evidence", "message": message, "path": "$", "details": details}],
    }


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
            "diagnostics": [{"code": "PG_BRC_SOURCE_UNPARSEABLE", "severity": "error", "message": str(exc), "path": "$"}],
        }
        print(canonical_dumps(payload))
        return 2
    raise AssertionError(f"unknown coverage command: {args.coverage_command}")


def _exit_for_status(status: str) -> int:
    return exit_code_for_status(status)


def _emit(payload: dict[str, Any], fmt: str) -> None:
    if fmt == "persian":
        if "status" in payload:
            print(render_plain_summary(payload), end="")
        else:
            print(_render_capability_summary_fa(payload), end="")
        return
    print(canonical_dumps(payload))


def _render_capability_summary_fa(payload: dict[str, Any]) -> str:
    capabilities = payload.get("capabilities") if isinstance(payload.get("capabilities"), dict) else {}
    rows = (
        ("Architect → CE", capabilities.get("architect_to_ce")),
        ("CE → Builder", capabilities.get("ce_to_builder")),
        ("Builder → Responsive", capabilities.get("builder_to_responsive")),
        ("Final Evidence Gate", capabilities.get("final_evidence_gate")),
    )
    lines = ["وضعیت قابلیت‌های Project Gate:"]
    for label, value in rows:
        item = value if isinstance(value, dict) else {}
        exposure = item.get("cli_exposure", "unknown")
        real = item.get("real_non_synthetic_handoff", item.get("real_non_synthetic_evidence", "unknown"))
        mode = "functional" if label == "Architect → CE" else "guarded/fail-closed"
        lines.append(f"- {label}: {mode}; cli={exposure}; real_evidence={real}")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
