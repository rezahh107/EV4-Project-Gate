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

    # Generate the source through the current public Architect Runtime authority.
    # The Stage history is an owner fixture, so the resulting handoff must remain
    # synthetic/blocked; the producer provenance itself comes from the real exact
    # checkout because git_provider=None uses Architect's SubprocessGitProvider.
    architect_output = evidence / "architect-runtime-output"
    if architect_output.exists():
        shutil.rmtree(architect_output)
    architect_output.mkdir(parents=True)
    runtime_command = _architect_runtime_command(architect_output)
    runtime = _run(runtime_command, cwd=architect)
    _write_process(evidence / "architect-runtime-finalization.json", runtime_command, runtime)
    if runtime.returncode != 0:
        raise SystemExit("official Architect Runtime finalization failed")
    runtime_result = _single_json_line(runtime.stdout)
    if runtime_result.get("finalization_succeeded") is not True:
        raise SystemExit("official Architect Runtime did not finalize the Project Gate artifact")
    if runtime_result.get("synthetic") is not True:
        raise SystemExit("owner-fixture Runtime evidence must remain synthetic")
    if runtime_result.get("handoff_allowed") is not False:
        raise SystemExit("synthetic Architect Runtime evidence unexpectedly authorized handoff")
    if runtime_result.get("publication_status") != "published_blocked":
        raise SystemExit("synthetic Architect Runtime finalization status drifted")

    architect_export = architect_output / "architect-project-gate.json"
    if not architect_export.is_file():
        raise SystemExit("official Architect Runtime did not publish architect-project-gate.json")
    export_value = _read_json(architect_export)
    final_bundle = export_value.get("final_stage_bundle")
    continuation = export_value.get("continuation_assurance")
    if export_value.get("schema_version") != "producer-gate-export.v1":
        raise SystemExit("Architect Runtime emitted an unexpected export contract identity")
    producer = export_value.get("producer") if isinstance(export_value.get("producer"), dict) else {}
    if producer.get("repository") != ARCHITECT_REPO or producer.get("commit_sha") != ARCHITECT_COMMIT:
        raise SystemExit("Architect Runtime export did not carry the exact current producer identity")
    if not isinstance(final_bundle, dict) or final_bundle.get("synthetic") is not True:
        raise SystemExit("Architect Runtime final bundle lost synthetic classification")
    if not isinstance(continuation, dict):
        raise SystemExit("current active Architect Runtime did not emit continuation_assurance")
    if bool((export_value.get("handoff") or {}).get("allowed")) is not False:
        raise SystemExit("synthetic Architect export unexpectedly upgraded ordinary handoff")

    source_pcvp_hash = canonical_sha256({"continuation_assurance": continuation})
    source_copy = evidence / "architect-project-gate.json"
    source_copy.write_bytes(architect_export.read_bytes())
    source_bundle_path = evidence / "architect-source-bundle.json"
    _write_json(source_bundle_path, final_bundle)

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
    _assert_blocked_active_path(first, first_result)

    second = _run(cli_command, cwd=project_gate)
    _write_process(evidence / "project-gate-second-result.json", cli_command, second)
    second_result = _single_json_line(second.stdout)
    _assert_blocked_active_path(second, second_result)

    first_ce = _transition_ce_input(first_result)
    second_ce = _transition_ce_input(second_result)
    if canonical_dumps(first_ce) != canonical_dumps(second_ce):
        raise SystemExit("repeated exact active-path execution changed CE intake bytes")
    if first_ce.get("continuation_assurance") != continuation:
        raise SystemExit("CE intake did not preserve the exact Architect continuation_assurance")
    ce_pcvp_hash = canonical_sha256(
        {"continuation_assurance": first_ce.get("continuation_assurance")}
    )
    if ce_pcvp_hash != source_pcvp_hash:
        raise SystemExit("Architect and CE PCVP carrier canonical identities differ")

    activation = first_result.get("pcvp_activation")
    if not isinstance(activation, dict):
        raise SystemExit("Project Gate omitted staged activation evidence")
    if activation.get("activation_commit") != ACTIVATION_COMMIT:
        raise SystemExit("Project Gate did not bind the exact staged activation commit")
    if activation.get("activation_id") != ACTIVATION_ID:
        raise SystemExit("Project Gate staged activation id drifted")
    if activation.get("enabled_edge") != ACTIVATION_EDGE:
        raise SystemExit("Project Gate staged activation edge drifted")
    if activation.get("full_rollout_authorized") is not False:
        raise SystemExit("Project Gate incorrectly reported full PCVP rollout authority")

    # Re-run the official CE validator on the exact mapped object. This file is
    # test evidence only; Project Gate correctly refuses operational publication
    # because the Architect fixture handoff is false.
    mapped_ce_path = evidence / "ce-input.synthetic-blocked.validation-only.json"
    _write_json(mapped_ce_path, first_ce)
    ce_validator_command = [
        sys.executable,
        "-B",
        "scripts/validate-ce-architect-stage-intake.py",
        "--repo-root",
        str(ce),
        "--file",
        str(mapped_ce_path),
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
        raise SystemExit("mapped active-PCVP CE intake failed official CE revalidation")

    summary = {
        "schema_version": "pg-a2c-exact-head-evidence.v1",
        "evidence_classification": "cross_repository_integration",
        "real_run": "not_available",
        "synthetic": True,
        "repository_identities": {
            key: {"repository": value["repository"], "commit": value["commit"]}
            for key, value in identities.items()
        },
        "architect_runtime": {
            "public_api": "scripts/architect_quality_runtime.py#finalize_project_gate",
            "artifact_path": source_copy.name,
            "artifact_sha256_file_bytes": _sha256(source_copy),
            "producer_commit": producer.get("commit_sha"),
            "handoff_allowed": False,
            "publication_status": runtime_result.get("publication_status"),
            "continuation_assurance_canonical_sha256": source_pcvp_hash,
        },
        "pcvp_activation": {
            "activation_commit": activation.get("activation_commit"),
            "activation_id": activation.get("activation_id"),
            "enabled_edge": activation.get("enabled_edge"),
            "full_rollout_authorized": activation.get("full_rollout_authorized"),
            "carrier_lossless": ce_pcvp_hash == source_pcvp_hash,
            "downstream_activation": False,
        },
        "project_gate_result": {
            "status": first_result.get("status"),
            "handoff_allowed": first_result.get("handoff_allowed"),
            "publication_allowed": first_result.get("publication_allowed"),
            "downstream_artifact": first_result.get("downstream_artifact"),
            "receipt": first_result.get("receipt"),
        },
        "ce_intake": {
            "schema_id": first_ce.get("schema_id"),
            "canonical_sha256": canonical_sha256(first_ce),
            "continuation_assurance_canonical_sha256": ce_pcvp_hash,
            "official_revalidation": "valid",
            "publication_claim": "none_validation_only",
        },
        "owner_validators": {
            "architect": first_result.get("producer_validation", {}).get("official_validator_status"),
            "ce": first_result.get("consumer_validation", {}).get("status"),
        },
        "determinism": {
            "mapped_ce_input_canonical_identical": True,
        },
        "authority_preservation": {
            "source_handoff_false_remains_false": True,
            "publication_remains_blocked": True,
            "policy_and_activation_commits_distinct": CANONICAL_COMMIT != ACTIVATION_COMMIT,
        },
    }
    _write_json(evidence / "summary.json", summary)
    print(canonical_dumps(summary))
    return 0


def _architect_runtime_command(output_directory: Path) -> list[str]:
    code = r'''
import importlib
import importlib.util
import json
import sys
from pathlib import Path

root = Path.cwd().resolve()
scripts = root / "scripts"
tests = root / "tests"
sys.path.insert(0, str(scripts))
sys.path.insert(0, str(tests))

spec = importlib.util.spec_from_file_location(
    "_pg_pcvp_exact_head_architect_runtime",
    scripts / "architect_quality_runtime.py",
)
assert spec is not None and spec.loader is not None
runtime = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = runtime
spec.loader.exec_module(runtime)
legacy = importlib.import_module("_legacy_architect_runtime_truth_spine")

result = runtime.finalize_project_gate(
    legacy.full_outputs(),
    run_context=legacy.context("fixture"),
    repository_root=root,
    output_directory=Path(sys.argv[1]).resolve(),
    git_provider=None,
)
print(json.dumps(result.to_dict(), sort_keys=True, separators=(",", ":")))
'''
    return [sys.executable, "-B", "-c", code, str(output_directory)]


def _assert_blocked_active_path(
    completed: subprocess.CompletedProcess[str],
    result: dict[str, Any],
) -> None:
    if completed.returncode != 2:
        raise SystemExit(f"blocked synthetic A2C path expected exit 2, observed {completed.returncode}")
    if result.get("status") != "insufficient_evidence":
        raise SystemExit("blocked synthetic A2C path did not remain insufficient_evidence")
    if result.get("handoff_allowed") is not False:
        raise SystemExit("PCVP upgraded ordinary handoff authority")
    if result.get("publication_allowed") is not False:
        raise SystemExit("PCVP upgraded publication authority")
    if (result.get("downstream_artifact") or {}).get("status") != "not_published":
        raise SystemExit("blocked synthetic A2C path unexpectedly published CE input")
    if (result.get("receipt") or {}).get("status") != "not_generated":
        raise SystemExit("blocked synthetic A2C path unexpectedly generated a receipt")
    if result.get("producer_validation", {}).get("official_validator_status") != "accepted":
        raise SystemExit("official Architect validator was not accepted")
    if result.get("consumer_validation", {}).get("status") != "accepted":
        raise SystemExit("official CE validator was not accepted")
    _transition_ce_input(result)


def _transition_ce_input(result: dict[str, Any]) -> dict[str, Any]:
    transition = result.get("transition_result")
    output = transition.get("output") if isinstance(transition, dict) else None
    payload = output.get("payload") if isinstance(output, dict) else None
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, dict):
        raise SystemExit("Project Gate did not preserve mapped CE intake for blocked handoff evidence")
    if data.get("schema_id") != "ev4-ce-architect-stage-intake@1.1.0":
        raise SystemExit("mapped object is not the canonical CE Architect intake")
    return data


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
