#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from ev4_transition.canonical_json import bytes_sha256, canonical_dumps
from ev4_transition.external_lock import ARCHITECT_COMMIT, ARCHITECT_REPO

SOURCE_SCHEMA_ID = "ev4-architect-stage-payload@1.0.0"
SYNTHETIC_AUTHORITY_CODE = "PG_A2C_SYNTHETIC_OPERATIONAL_HANDOFF_FORBIDDEN"


def source_bundle(payload: dict[str, Any], *, bundle_id: str = "synthetic-architect-a2c-smoke", stage: str = "architect") -> dict[str, Any]:
    status = "insufficient_evidence" if payload["payload_status"] == "insufficient_evidence" else "complete"
    bundle: dict[str, Any] = {
        "schema_version": "stage-evidence-bundle.v1",
        "bundle_id": bundle_id,
        "stage": stage,
        "payload_schema": {"id": SOURCE_SCHEMA_ID, "version": "1.0.0", "owner_repository": ARCHITECT_REPO},
        "produced_by": {"repository": ARCHITECT_REPO, "ref": "synthetic-fixture", "commit_sha": ARCHITECT_COMMIT},
        "evidence_status": status,
        "payload": {"schema_id": SOURCE_SCHEMA_ID, "data": payload},
        "evidence": [{"id": "architect-payload", "kind": "fixture", "state": "validated", "description": "Synthetic Architect payload fixture.", "artifact_hash": {"algorithm": "sha256", "value": bytes_sha256(canonical_dumps(payload).encode("utf-8")), "scope": "canonical_json"}, "source": {"type": "synthetic_fixture", "reference": "Architect pinned fixture"}}],
        "provenance": {"source": "synthetic-fixture", "created_by": "project-gate-smoke"},
        "synthetic": True,
    }
    if status == "insufficient_evidence":
        bundle["missing_evidence"] = [{"id": item["unresolved_id"], "owner": item["owner"], "reason": item["reason"]} for item in payload.get("unresolved_evidence", [])]
    return bundle


def run_cli(bundle_path: Path, architect_repo: str, ce_repo: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([
        sys.executable, "-m", "ev4_transition.cli", "transition", "architect-to-ce", str(bundle_path.resolve()),
        "--architect-repo", architect_repo,
        "--ce-repo", ce_repo,
        "--format", "json",
    ], text=True, capture_output=True, check=False)


def write_json(path: Path, value: Any) -> None:
    path.write_text(canonical_dumps(value) + "\n", encoding="utf-8")


def assert_transition_case(
    bundle: dict[str, Any],
    expected_exit: int,
    expected_status: str,
    architect_repo: str,
    ce_repo: str,
    work_dir: Path,
    case_id: str,
    *,
    expected_code: str | None = None,
) -> dict[str, Any]:
    bundle_path = work_dir / f"{case_id}.source-bundle.json"
    write_json(bundle_path, bundle)
    completed = run_cli(bundle_path, architect_repo, ce_repo)
    if completed.stderr:
        print(completed.stderr, file=sys.stderr)
    print(completed.stdout)
    if completed.returncode != expected_exit:
        raise AssertionError(f"{case_id}: expected exit {expected_exit}, got {completed.returncode}")
    result = json.loads(completed.stdout)
    if result["status"] != expected_status:
        raise AssertionError(f"{case_id}: expected status {expected_status}, got {result['status']}")
    if expected_status == "invalid" and result.get("output") is not None:
        raise AssertionError(f"{case_id}: invalid transition must not emit output")
    if expected_code is not None:
        codes = {item.get("code") for item in result.get("diagnostics", []) if isinstance(item, dict)}
        if expected_code not in codes:
            raise AssertionError(f"{case_id}: expected diagnostic {expected_code}, got {sorted(codes)}")
    return result


def validate_generated_ce_intake(result: dict[str, Any], source_bundle_value: dict[str, Any], ce_repo: str, work_dir: Path) -> None:
    output = result.get("output")
    if not isinstance(output, dict):
        raise AssertionError("synthetic smoke must still emit a structurally testable CE intake projection")
    intake_path = (work_dir / "generated-ce-intake.v1_1.json").resolve()
    source_path = (work_dir / "generated-source-bundle.v1.json").resolve()
    write_json(intake_path, output["payload"]["data"])
    write_json(source_path, source_bundle_value)
    completed = subprocess.run([
        sys.executable,
        str(Path(ce_repo) / "scripts/validate-ce-architect-stage-intake.py"),
        "--repo-root", ce_repo,
        "--file", str(intake_path),
        "--source-bundle", str(source_path),
        "--format", "json",
    ], text=True, capture_output=True, check=False)
    print(completed.stdout)
    if completed.stderr:
        print(completed.stderr, file=sys.stderr)
    if completed.returncode != 0:
        raise AssertionError(f"official CE validation of generated intake failed with exit {completed.returncode}")
    ce_result = json.loads(completed.stdout)
    if ce_result.get("status") != "valid":
        raise AssertionError(f"official CE validation of generated intake returned {ce_result.get('status')}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--architect-repo", required=True)
    parser.add_argument("--ce-repo", required=True)
    args = parser.parse_args()
    work_dir = Path(".a2c-smoke")
    work_dir.mkdir(exist_ok=True)

    valid_payload = json.loads((Path(args.architect_repo) / "fixtures/architect-stage-payload/valid/minimal-complete.v1.json").read_text(encoding="utf-8"))
    insufficient_payload = json.loads((Path(args.architect_repo) / "fixtures/architect-stage-payload/insufficient-evidence/missing-real-stage-output.v1.json").read_text(encoding="utf-8"))

    # The smoke intentionally uses an owner-provided synthetic fixture. It may prove
    # deterministic transformation and CE schema compatibility, but it must never
    # prove an operational handoff. The expected status is therefore fail-closed.
    valid_bundle = source_bundle(valid_payload)
    valid_result = assert_transition_case(
        valid_bundle,
        2,
        "insufficient_evidence",
        args.architect_repo,
        args.ce_repo,
        work_dir,
        "valid-synthetic",
        expected_code=SYNTHETIC_AUTHORITY_CODE,
    )
    validate_generated_ce_intake(valid_result, valid_bundle, args.ce_repo, work_dir)

    invalid_bundle = source_bundle(valid_payload, stage="builder")
    assert_transition_case(invalid_bundle, 1, "invalid", args.architect_repo, args.ce_repo, work_dir, "invalid")

    insufficient_bundle = source_bundle(insufficient_payload)
    assert_transition_case(insufficient_bundle, 2, "insufficient_evidence", args.architect_repo, args.ce_repo, work_dir, "insufficient")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
