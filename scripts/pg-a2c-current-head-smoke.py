#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from ev4_transition.canonical_json import canonical_dumps
from ev4_transition.external_lock import ARCHITECT_COMMIT, ARCHITECT_REPO, CE_COMMIT, CE_REPO
from ev4_transition.runners.repository_identity import inspect_checkout

PROJECT_GATE_REPOSITORY = "rezahh107/EV4-Project-Gate"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prove current-head synthetic Architect→CE compatibility.")
    parser.add_argument("--architect-repo", type=Path, required=True)
    parser.add_argument("--ce-repo", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    project_gate = Path.cwd().resolve()
    architect = args.architect_repo.resolve()
    ce = args.ce_repo.resolve()
    evidence = args.evidence_dir.resolve()
    evidence.mkdir(parents=True, exist_ok=True)

    identities = {
        "project_gate": inspect_checkout(project_gate, expected_repository=PROJECT_GATE_REPOSITORY),
        "architect": inspect_checkout(architect, expected_repository=ARCHITECT_REPO, expected_commit=ARCHITECT_COMMIT),
        "ce": inspect_checkout(ce, expected_repository=CE_REPO, expected_commit=CE_COMMIT),
    }
    if any(item["status"] != "accepted" for item in identities.values()):
        _write_json(evidence / "identity-failure.json", identities)
        raise SystemExit("exact repository identity verification failed")

    _ensure_named_branch(architect)
    architect_export = architect / "architect-project-gate.json"
    architect_export.unlink(missing_ok=True)
    payload = architect / "fixtures/architect-stage-payload/valid/minimal-complete.v1.json"
    exporter_command = [
        sys.executable,
        "scripts/export-architect-project-gate.py",
        "--payload",
        str(payload.relative_to(architect)),
        "--run-id",
        "pg-a2c-current-head-synthetic",
        "--output",
        architect_export.name,
        "--format",
        "json",
    ]
    exporter = _run(exporter_command, cwd=architect)
    _write_process(evidence / "architect-exporter-result.json", exporter_command, exporter)
    if exporter.returncode != 0 or not architect_export.is_file():
        raise SystemExit("official Architect exporter did not emit an accepted artifact")

    export_value = _read_json(architect_export)
    if export_value.get("schema_version") != "producer-gate-export.v1":
        raise SystemExit("Architect exporter emitted an unexpected contract identity")
    if export_value.get("synthetic") is False or not bool((export_value.get("final_stage_bundle") or {}).get("synthetic")):
        raise SystemExit("current-head integration fixture must remain honestly synthetic")

    source_copy = evidence / "architect-project-gate.json"
    source_copy.write_bytes(architect_export.read_bytes())
    source_bundle_path = evidence / "architect-source-bundle.json"
    _write_json(source_bundle_path, export_value["final_stage_bundle"])

    output = evidence / "ce-input.json"
    receipt = evidence / "project-gate-a2c-receipt.json"
    first_ce = evidence / "ce-input.first.json"
    first_receipt = evidence / "project-gate-a2c-receipt.first.json"
    for path in (output, receipt, first_ce, first_receipt):
        path.unlink(missing_ok=True)

    cli_command = [
        sys.executable,
        "-m",
        "ev4_transition.cli",
        "transition",
        "architect-to-ce",
        str(architect_export),
        "--acquisition-mode",
        "producer_emitted_gate_artifact",
        "--architect-repo",
        str(architect),
        "--ce-repo",
        str(ce),
        "--output",
        str(output.relative_to(project_gate)),
        "--receipt-output",
        str(receipt.relative_to(project_gate)),
        "--format",
        "json",
    ]
    first = _run(cli_command, cwd=project_gate)
    _write_process(evidence / "project-gate-first-result.json", cli_command, first)
    if first.returncode != 0 or not output.is_file() or not receipt.is_file():
        raise SystemExit("Project Gate did not publish accepted standalone outputs")
    first_result = _single_json_line(first.stdout)
    if first_result.get("status") != "accepted" or first_result.get("handoff_allowed") is not True:
        raise SystemExit("Project Gate did not report an accepted handoff")
    if first_result.get("producer_validation", {}).get("official_validator_status") != "accepted":
        raise SystemExit("official Architect validator was not accepted")
    if first_result.get("consumer_validation", {}).get("status") != "accepted":
        raise SystemExit("official CE validator was not accepted")

    shutil.copyfile(output, first_ce)
    shutil.copyfile(receipt, first_receipt)
    first_ce_bytes = first_ce.read_bytes()
    first_receipt_bytes = first_receipt.read_bytes()
    output.unlink()
    receipt.unlink()

    second = _run(cli_command, cwd=project_gate)
    _write_process(evidence / "project-gate-second-result.json", cli_command, second)
    if second.returncode != 0:
        raise SystemExit("deterministic repeat execution failed")
    if output.read_bytes() != first_ce_bytes:
        raise SystemExit("repeated Project Gate execution changed CE input bytes")
    if receipt.read_bytes() != first_receipt_bytes:
        raise SystemExit("repeated Project Gate execution changed receipt bytes")

    ce_input = _read_json(output)
    receipt_value = _read_json(receipt)
    if ce_input.get("schema_id") != "ev4-ce-architect-stage-intake@1.1.0":
        raise SystemExit("standalone output is not the active CE-owned intake contract")
    if receipt_value.get("schema_version") != "project-gate-a2c-receipt.v1":
        raise SystemExit("receipt contract identity is missing")
    if receipt_value.get("synthetic") is not True:
        raise SystemExit("receipt did not preserve synthetic evidence classification")

    ce_validator_command = [
        sys.executable,
        "scripts/validate-ce-architect-stage-intake.py",
        "--repo-root",
        str(ce),
        "--file",
        str(output),
        "--source-bundle",
        str(source_bundle_path),
        "--expect",
        "valid",
        "--format",
        "json",
    ]
    ce_validation = _run(ce_validator_command, cwd=ce)
    _write_process(evidence / "official-ce-revalidation.json", ce_validator_command, ce_validation)
    if ce_validation.returncode != 0:
        raise SystemExit("standalone CE input failed official CE revalidation")

    overwrite = _run(cli_command, cwd=project_gate)
    _write_process(evidence / "overwrite-rejection.json", cli_command, overwrite)
    overwrite_result = _single_json_line(overwrite.stdout)
    if overwrite.returncode == 0 or overwrite_result.get("status") != "invalid":
        raise SystemExit("existing outputs were not rejected fail-closed")
    if not any(item.get("code") == "PG_A2C_OUTPUT_EXISTS" for item in overwrite_result.get("diagnostics", [])):
        raise SystemExit("overwrite rejection diagnostic was not deterministic")

    summary = {
        "schema_version": "pg-a2c-exact-head-evidence.v1",
        "evidence_classification": "cross_repository_integration",
        "real_run": "not_available",
        "synthetic": True,
        "repository_identities": {key: {"repository": value["repository"], "commit": value["commit"]} for key, value in identities.items()},
        "architect_export": {
            "path": source_copy.name,
            "sha256_file_bytes": _sha256(source_copy),
            "export_id": export_value.get("export_id"),
        },
        "ce_input": {
            "path": output.name,
            "schema_id": ce_input.get("schema_id"),
            "sha256_file_bytes": _sha256(output),
            "canonical_sha256": first_result["downstream_artifact"]["canonical_sha256"],
        },
        "receipt": {
            "path": receipt.name,
            "schema_version": receipt_value.get("schema_version"),
            "receipt_id": receipt_value.get("receipt_id"),
            "sha256_file_bytes": _sha256(receipt),
            "canonical_sha256": first_result["receipt"]["canonical_sha256"],
        },
        "validators": {
            "architect": first_result["producer_validation"]["official_validator_status"],
            "ce": first_result["consumer_validation"]["status"],
            "ce_standalone_revalidation": "valid",
        },
        "determinism": {
            "ce_input_byte_identical": True,
            "receipt_byte_identical": True,
        },
        "fail_closed": {
            "overwrite_rejected": True,
            "stale_pin_tests": "covered_by_exact_head_test_suite",
            "tamper_tests": "covered_by_adversarial_test_suite",
        },
        "operator_command": "ev4-transition transition architect-to-ce architect-project-gate.json --acquisition-mode producer_emitted_gate_artifact --architect-repo ../EV4-Architect-Repo --ce-repo ../EV4-Constructability-Engineer-Repo --output ce-input.json --receipt-output project-gate-a2c-receipt.json --format json",
    }
    _write_json(evidence / "summary.json", summary)
    print(canonical_dumps(summary))
    return 0


def _ensure_named_branch(repo: Path) -> None:
    current = subprocess.run(["git", "-C", str(repo), "symbolic-ref", "--short", "HEAD"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, check=False)
    if current.returncode == 0:
        return
    subprocess.run(["git", "-C", str(repo), "switch", "-c", "pg-a2c-current-head-integration"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def _run(command: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env.update({"LC_ALL": "C.UTF-8", "LANG": "C.UTF-8", "PYTHONHASHSEED": "0"})
    return subprocess.run(command, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False, timeout=120)


def _write_process(path: Path, command: list[str], completed: subprocess.CompletedProcess[str]) -> None:
    _write_json(path, {"command": command, "exit_code": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr})


def _single_json_line(text: str) -> dict[str, Any]:
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        raise SystemExit("expected structured JSON output was empty")
    value = json.loads(lines[-1])
    if not isinstance(value, dict):
        raise SystemExit("structured JSON output was not an object")
    return value


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"), parse_constant=_reject_constant)
    if not isinstance(value, dict):
        raise SystemExit(f"expected JSON object: {path}")
    return value


def _write_json(path: Path, value: Any) -> None:
    path.write_text(canonical_dumps(value) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _reject_constant(value: str) -> Any:
    raise ValueError(f"non-finite JSON constant is forbidden: {value}")


if __name__ == "__main__":
    raise SystemExit(main())
