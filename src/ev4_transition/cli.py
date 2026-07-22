from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path
from typing import Any

from .behavioral_coverage import CoverageSourceError, inspect_coverage_source, validate_coverage_source
from .bundle_validator import BundleValidator
from .canonical_json import canonical_dumps, load_json_file
from .presentation.status_mapping import exit_code_for_status
from .reports import render_plain_summary
from .service import GateRequest, RepoPaths, cli_transition_names, run_gate_request, run_preflight, service_choice_for_cli

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
    transition_parser.add_argument("transition_name", choices=cli_transition_names())
    transition_parser.add_argument("bundle")
    transition_parser.add_argument("--architect-repo")
    transition_parser.add_argument("--ce-repo")
    transition_parser.add_argument("--builder-repo")
    transition_parser.add_argument("--responsive-repo")
    transition_parser.add_argument("--project-gate-repo")
    transition_parser.add_argument("--kernel-repo")
    transition_parser.add_argument("--lock")
    transition_parser.add_argument("--output-dir")
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
            output_dir=args.output_dir,
            output_path=args.output,
            receipt_path=args.receipt_output,
            preflight_mode="external_token",
        )
        preflight = run_preflight(request)
        if preflight.status != "ready" or not preflight.request_fingerprint:
            status, diagnostic = _cli_preflight_failure(preflight)
            payload = {
                "schema_version": "project-gate-cli-preflight-result.v1",
                "status": status,
                "transition_choice": service_choice,
                "preflight": preflight.to_dict(),
                "diagnostics": [diagnostic],
                "handoff_allowed": False,
                "output": None,
            }
            _emit(payload, args.format)
            return _exit_for_status(payload["status"])
        request = replace(request, preflight_fingerprint=preflight.request_fingerprint)
        response = run_gate_request(request)
        payload = _cli_payload(response.to_dict())
        _emit(payload, args.format)
        return _exit_for_status(str(payload.get("status", "invalid")))

    if args.command == "coverage":
        return _coverage_command(args)

    info = _load_capability_status()
    _emit(info, args.format)
    return 0



def _cli_preflight_failure(preflight: Any) -> tuple[str, dict[str, Any]]:
    error_checks = [check for check in preflight.checks if check.status == "error"]
    def text(check: Any) -> str:
        return f"{getattr(check, 'id', '')} {getattr(check, 'technical_detail', '')}"
    combined = " ".join(text(check) for check in error_checks)
    status = "insufficient_evidence" if any(marker in combined for marker in ("path.", "PG_INT_REPOSITORY_PATH", "PG_INT_GITHUB_URL_REJECTED", "PG_INT_OUTPUT_DIRECTORY_UNAVAILABLE")) else "invalid"
    selected = next((check for check in error_checks if "PG_INT_GITHUB_URL_REJECTED" in text(check) or (str(getattr(check, "id", "")).startswith("path.") and "github_url" in text(check))), None)
    code = "CLI_GITHUB_URL_REJECTED" if selected is not None else ""
    if selected is None:
        selected = next((check for check in error_checks if "PG_INT_REPOSITORY_PATH_NOT_FOUND" in text(check) or (str(getattr(check, "id", "")).startswith("path.") and "does_not_exist" in text(check))), None)
        code = "CLI_LOCAL_PATH_NOT_FOUND" if selected is not None else ""
    if selected is None:
        selected = next((check for check in error_checks if "PG_INT_REPOSITORY_PATH_REQUIRED" in text(check) or (str(getattr(check, "id", "")).startswith("path.") and ".missing" in text(check))), None)
        code = "CLI_LOCAL_PATH_REQUIRED" if selected is not None else ""
    if selected is None:
        selected = error_checks[0] if error_checks else None
        code = "CLI_AUTHORITATIVE_PREFLIGHT_NOT_READY"
    check_id = str(getattr(selected, "id", ""))
    field = next((name for name in ("project_gate_repo_path", "architect_repo_path", "ce_repo_path", "builder_repo_path", "responsive_repo_path", "kernel_repo_path") if name in check_id), None)
    option = "--" + field.removesuffix("_path").replace("_", "-") if field else None
    details: dict[str, Any] = {"authoritative_check_ids": [str(getattr(check, "id", "")) for check in error_checks]}
    if option:
        details["option"] = option
    if code == "CLI_LOCAL_PATH_NOT_FOUND" and selected is not None:
        details["path"] = str(getattr(selected, "technical_detail", ""))
    return status, {
        "code": code,
        "severity": "insufficient_evidence" if status == "insufficient_evidence" else "error",
        "message": preflight.summary_fa,
        "path": "$.preflight",
        "details": details,
    }


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
