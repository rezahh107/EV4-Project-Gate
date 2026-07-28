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

from ev4_transition.canonical_json import canonical_dumps, canonical_sha256
from ev4_transition.external_lock import ARCHITECT_COMMIT, ARCHITECT_REPO, CE_COMMIT, CE_REPO
from ev4_transition.runners.pcvp_activation import ACTIVATION_COMMIT, ACTIVATION_EDGE, ACTIVATION_ID
from ev4_transition.runners.pcvp_owner import CANONICAL_COMMIT, CANONICAL_REPOSITORY
from ev4_transition.runners.repository_identity import inspect_checkout

PROJECT_GATE_REPOSITORY = "rezahh107/EV4-Project-Gate"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Prove exact-head active Architect→Project Gate→CE PCVP compatibility."
    )
    parser.add_argument("--architect-repo", type=Path, required=True)
    parser.add_argument("--ce-repo", type=Path, required=True)
    parser.add_argument("--kernel-repo", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    project_gate = Path.cwd().resolve()
    architect = args.architect_repo.resolve()
    ce = args.ce_repo.resolve()
    kernel = args.kernel_repo.resolve()
    evidence = args.evidence_dir.resolve()
    evidence.mkdir(parents=True, exist_ok=True)
    try:
        evidence.relative_to(project_gate)
    except ValueError as exc:
        raise SystemExit("evidence directory must be inside Project Gate") from exc

    identities = {
        "project_gate": inspect_checkout(
            project_gate,
            expected_repository=PROJECT_GATE_REPOSITORY,
        ),
        "architect": inspect_checkout(
            architect,
            expected_repository=ARCHITECT_REPO,
            expected_commit=ARCHITECT_COMMIT,
        ),
        "ce": inspect_checkout(
            ce,
            expected_repository=CE_REPO,
            expected_commit=CE_COMMIT,
        ),
        "decision_kernel_policy": inspect_checkout(
            kernel,
            expected_repository=CANONICAL_REPOSITORY,
            expected_commit=CANONICAL_COMMIT,
        ),
    }
    if any(item["status"] != "accepted" for item in identities.values()):
        _write_json(evidence / "identity-failure.json", identities)
        raise SystemExit("exact repository identity verification failed")

    _assert_activation_object_available(kernel)
    _ensure_named_branch(architect)
    architect_export = architect / "architect-project-gate.json"
    architect_export.unlink(missing_ok=True)
    payload = architect / "fixtures/architect-stage-payload/valid/minimal-complete.v1.json"
    exporter_command = [
        sys.executable,
        "-B",
        "scripts/export-architect-project-gate.py",
        "--payload",
        str(payload.relative_to(architect)),
        "--run-id",
        "pg-a2c-current-head-active-pcvp",
        "--output",
        architect_export.name,
        "--format",
        "json",
    ]
    exporter = _run(exporter_command, cwd=architect)
    _write_process(
        evidence / "architect-exporter-result.json",
        exporter_command,
        exporter,
    )
    if exporter.returncode not in {0, 2} or not architect_export.is_file():
        raise SystemExit("official Architect exporter did not emit its artifact")

    export_value = _read_json(architect_export)
    final_bundle = export_value.get("final_stage_bundle")
    continuation = export_value.get("continuation_assurance")
    if export_value.get("schema_version") != "producer-gate-export.v1":
        raise SystemExit("Architect exporter emitted an unexpected contract identity")
    if not isinstance(final_bundle, dict) or final_bundle.get("synthetic") is not True:
        raise SystemExit("current-head integration evidence must remain synthetic")
    if not isinstance(continuation, dict):
        raise SystemExit("current active Architect producer did not emit continuation_assurance")
    source_pcvp_hash = canonical_sha256({"continuation_assurance": continuation})
    source_handoff_allowed = bool((export_value.get("handoff") or {}).get("allowed"))
    if not source_handoff_allowed:
        raise SystemExit("exact-head active-path fixture must authorize ordinary A2C handoff for publication proof")

    source_copy = evidence / "architect-project-gate.json"
    source_copy.write_bytes(architect_export.read_bytes())
    source_bundle_path = evidence / "architect-source-bundle.json"
    _write_json(source_bundle_path, final_bundle)

    first_ce = evidence / "ce-input.first.json"
    first_receipt = evidence / "project-gate-a2c-receipt.first.json"
    second_ce = evidence / "ce-input.second.json"
    second_receipt = evidence / "project-gate-a2c-receipt.second.json"
    for path in (first_ce, first_receipt, second_ce, second_receipt):
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
        "--kernel-repo",
        str(kernel),
        "--output-dir",
        evidence.relative_to(project_gate).as_posix(),
        "--format",
        "json",
    ]
    first = _run(cli_command, cwd=project_gate)
    _write_process(evidence / "project-gate-first-result.json", cli_command, first)
    first_result = _single_json_line(first.stdout)
    output = Path(first_result["downstream_artifact"]["path"])
    receipt = Path(first_result["receipt"]["path"])
    _assert_publication(first, first_result, output, receipt)

    shutil.copyfile(output, first_ce)
    shutil.copyfile(receipt, first_receipt)
    first_ce_bytes = first_ce.read_bytes()
    first_receipt_value = _read_json(first_receipt)

    second = _run(cli_command, cwd=project_gate)
    _write_process(evidence / "project-gate-second-result.json", cli_command, second)
    second_result = _single_json_line(second.stdout)
    second_output = Path(second_result["downstream_artifact"]["path"])
    second_receipt_path = Path(second_result["receipt"]["path"])
    _assert_publication(second, second_result, second_output, second_receipt_path)
    shutil.copyfile(second_output, second_ce)
    shutil.copyfile(second_receipt_path, second_receipt)
    if second_ce.read_bytes() != first_ce_bytes:
        raise SystemExit("repeated execution changed CE input bytes")
    second_receipt_value = _read_json(second_receipt)
    if output.parent == second_output.parent:
        raise SystemExit("repeated execution reused a collision-safe execution directory")

    ce_input = _read_json(output)
    receipt_value = _read_json(receipt)
    _assert_receipt_binds_output(first_receipt_value, output, first_result)
    _assert_receipt_binds_output(second_receipt_value, second_output, second_result)
    if first_receipt_value.get("receipt_id") == second_receipt_value.get("receipt_id"):
        raise SystemExit("collision-safe executions unexpectedly reused a receipt identity")
    if ce_input.get("schema_id") != "ev4-ce-architect-stage-intake@1.1.0":
        raise SystemExit("standalone output is not the active CE intake contract")
    if ce_input.get("continuation_assurance") != continuation:
        raise SystemExit("CE intake did not preserve the exact Architect continuation_assurance")
    ce_pcvp_hash = canonical_sha256(
        {"continuation_assurance": ce_input.get("continuation_assurance")}
    )
    if ce_pcvp_hash != source_pcvp_hash:
        raise SystemExit("Architect and CE PCVP carrier canonical identities differ")
    activation = first_result.get("pcvp_activation")
    if not isinstance(activation, dict) or activation.get("activation_commit") != ACTIVATION_COMMIT:
        raise SystemExit("Project Gate did not bind the exact staged activation authority")
    if activation.get("activation_id") != ACTIVATION_ID or activation.get("enabled_edge") != ACTIVATION_EDGE:
        raise SystemExit("Project Gate staged activation evidence drifted")
    if receipt_value.get("schema_version") != "project-gate-a2c-receipt.v1":
        raise SystemExit("receipt contract identity is missing")
    if receipt_value.get("synthetic") is not True:
        raise SystemExit("receipt lost synthetic evidence classification")
    if receipt_value.get("handoff_allowed") is not True:
        raise SystemExit("receipt changed the producer handoff decision")

    ce_validator_command = [
        sys.executable,
        "-B",
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
    _write_process(
        evidence / "official-ce-revalidation.json",
        ce_validator_command,
        ce_validation,
    )
    if ce_validation.returncode != 0:
        raise SystemExit("standalone CE input failed official CE revalidation")

    if not output.parent.name.startswith("run-") or output.parent.parent != evidence.resolve():
        raise SystemExit("first publication escaped the selected output root")
    if not second_output.parent.name.startswith("run-") or second_output.parent.parent != evidence.resolve():
        raise SystemExit("second publication escaped the selected output root")

    summary = {
        "schema_version": "pg-a2c-exact-head-evidence.v1",
        "evidence_classification": "cross_repository_integration",
        "real_run": "not_available",
        "synthetic": True,
        "repository_identities": {
            key: {"repository": value["repository"], "commit": value["commit"]}
            for key, value in identities.items()
        },
        "architect_export": {
            "path": source_copy.name,
            "sha256_file_bytes": _sha256(source_copy),
            "export_id": export_value.get("export_id"),
            "exporter_exit_code": exporter.returncode,
            "handoff_allowed": source_handoff_allowed,
            "continuation_assurance_canonical_sha256": source_pcvp_hash,
        },
        "pcvp_activation": {
            "activation_commit": activation.get("activation_commit"),
            "activation_id": activation.get("activation_id"),
            "enabled_edge": activation.get("enabled_edge"),
            "carrier_lossless": ce_pcvp_hash == source_pcvp_hash,
            "downstream_activation": False,
        },
        "project_gate_result": {
            "status": first_result.get("status"),
            "handoff_allowed": first_result.get("handoff_allowed"),
        },
        "ce_input": {
            "path": output.name,
            "schema_id": ce_input.get("schema_id"),
            "sha256_file_bytes": _sha256(output),
            "canonical_sha256": first_result["downstream_artifact"]["canonical_sha256"],
            "continuation_assurance_canonical_sha256": ce_pcvp_hash,
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
            "receipt_binding_verified_per_execution": True,
            "receipt_identity_unique_per_execution": True,
        },
        "fail_closed": {
            "collision_safe_execution_directories": True,
            "no_overwrite_tests": "covered_by_exact_head_test_suite",
            "stale_pin_tests": "covered_by_exact_head_test_suite",
            "tamper_tests": "covered_by_adversarial_test_suite",
        },
        "operator_command": (
            "ev4-transition transition architect-to-ce architect-project-gate.json "
            "--acquisition-mode producer_emitted_gate_artifact "
            "--architect-repo ../EV4-Architect-Repo "
            "--ce-repo ../EV4-Constructability-Engineer-Repo "
            "--kernel-repo ../EV4-Decision-Kernel "
            "--output-dir pg-a2c-exact-head-evidence --format json"
        ),
    }
    _write_json(evidence / "summary.json", summary)
    print(canonical_dumps(summary))
    return 0


def _assert_activation_object_available(kernel: Path) -> None:
    observed = subprocess.run(
        ["git", "-C", str(kernel), "cat-file", "-e", f"{ACTIVATION_COMMIT}^{{commit}}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if observed.returncode != 0:
        raise SystemExit("exact staged activation commit object is unavailable from the policy checkout")


def _assert_receipt_binds_output(
    receipt_value: dict[str, Any],
    output: Path,
    result: dict[str, Any],
) -> None:
    ce_input = receipt_value.get("ce_input") if isinstance(receipt_value.get("ce_input"), dict) else {}
    expected_suffix = output.resolve().relative_to(Path.cwd().resolve()).as_posix()
    if ce_input.get("path") != expected_suffix:
        raise SystemExit("receipt does not reference its execution-specific CE output path")
    if ce_input.get("canonical_sha256") != result["downstream_artifact"]["canonical_sha256"]:
        raise SystemExit("receipt CE output hash does not match the published artifact")
    if ce_input.get("publication_state") != "published_verified":
        raise SystemExit("receipt did not preserve verified publication state")


def _assert_publication(
    completed: subprocess.CompletedProcess[str],
    result: dict[str, Any],
    output: Path,
    receipt: Path,
) -> None:
    if completed.returncode != 0 or not output.is_file() or not receipt.is_file():
        raise SystemExit("Project Gate did not publish expected standalone outputs")
    if result.get("status") != "accepted":
        raise SystemExit("Project Gate did not accept the exact active A2C path")
    if result.get("handoff_allowed") is not True:
        raise SystemExit("Project Gate changed the producer handoff decision")
    if result.get("producer_validation", {}).get("official_validator_status") != "accepted":
        raise SystemExit("official Architect validator was not accepted")
    if result.get("consumer_validation", {}).get("status") != "accepted":
        raise SystemExit("official CE validator was not accepted")


def _ensure_named_branch(repo: Path) -> None:
    current = subprocess.run(
        ["git", "-C", str(repo), "symbolic-ref", "--short", "HEAD"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=False,
    )
    if current.returncode == 0:
        return
    subprocess.run(
        ["git", "-C", str(repo), "switch", "-c", "pg-a2c-current-head-integration"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _run(command: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env.update(
        {
            "LC_ALL": "C.UTF-8",
            "LANG": "C.UTF-8",
            "PYTHONHASHSEED": "0",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
    )
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
        timeout=420,
    )


def _write_process(
    path: Path,
    command: list[str],
    completed: subprocess.CompletedProcess[str],
) -> None:
    _write_json(
        path,
        {
            "command": command,
            "exit_code": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        },
    )


def _single_json_line(text: str) -> dict[str, Any]:
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        raise SystemExit("expected structured JSON output was empty")
    value = json.loads(lines[-1], parse_constant=_reject_constant)
    if not isinstance(value, dict):
        raise SystemExit("structured JSON output was not an object")
    return value


def _write_json(path: Path, value: Any) -> None:
    path.write_text(canonical_dumps(value) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"), parse_constant=_reject_constant)
    if not isinstance(value, dict):
        raise SystemExit(f"expected object JSON: {path}")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _reject_constant(value: str) -> Any:
    raise ValueError(f"non-finite JSON constant is forbidden: {value}")


if __name__ == "__main__":
    raise SystemExit(main())
