from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ev4_transition.canonical_json import load_json_file
from ev4_transition.runners.git_blobs import git_blob_sha256_from_runner

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
STAGES = ["architect", "ce", "builder", "responsive"]
REPOSITORIES = {
    "architect": "rezahh107/EV4-Architect-Repo",
    "ce": "rezahh107/EV4-Constructability-Engineer-Repo",
    "builder": "rezahh107/EV4-Builder-Assistant-Repo",
    "responsive": "rezahh107/EV4-Responsive-Architect",
}
ALLOWED_ROLES = {
    "handoff",
    "adoption_doc",
    "pipeline_manifest",
    "stage_payload_schema",
    "producer_gate_export_schema",
    "producer_gate_export_lock",
    "stage_bundle_schema",
    "validator",
    "ci_workflow",
    "fixture",
    "ce_stage_bundle_schema_reference",
}


class RegistryError(Exception):
    def __init__(self, diagnostics: list[dict[str, Any]]):
        self.diagnostics = diagnostics
        super().__init__("producer registry invalid")


def validate_adoption_registry(
    path: str | Path = "contracts/producer-adoption/ev4-producer-adoption-set.v1.json",
) -> dict[str, Any]:
    try:
        reg = load_json_file(path)
    except Exception as exc:
        diags = []
        _d(diags, "$", "registry must be readable JSON", error_type=type(exc).__name__)
        return _result(diags)

    diags: list[dict[str, Any]] = []
    if not isinstance(reg, dict):
        _d(diags, "$", "registry root must be a JSON object", observed_type=type(reg).__name__)
        return _result(diags)

    if reg.get("schema_id") != "ev4-producer-adoption-set.v1":
        _d(diags, "$.schema_id", "unexpected registry schema id")

    prompt0 = reg.get("prompt_0")
    if not isinstance(prompt0, dict):
        _d(diags, "$.prompt_0", "prompt_0 must be an object")
        prompt0 = {}
    if prompt0.get("producer_gate_export_schema_sha256") != "c556bb9deeccdcafeb885a1c8b3dbd660e4e06f452b8ac3c7040d21377465fcc":
        _d(diags, "$.prompt_0.producer_gate_export_schema_sha256", "Prompt 0 Producer Gate Export hash mismatch")
    if prompt0.get("stage_bundle_schema_sha256") != "fc1ec6d3f7aecbabaeb0a3455d9eb42788779d2fa1531e8c7b2cb3bde706a886":
        _d(diags, "$.prompt_0.stage_bundle_schema_sha256", "Prompt 0 Stage Bundle hash mismatch")

    producers = reg.get("producers")
    if not isinstance(producers, list):
        _d(diags, "$.producers", "producers must be an array")
        return _result(diags)

    stages: list[Any] = []
    for i, producer in enumerate(producers):
        producer_path = f"$.producers[{i}]"
        if not isinstance(producer, dict):
            stages.append(None)
            _d(diags, producer_path, "producer entry must be an object", observed_type=type(producer).__name__)
            continue

        stage = producer.get("stage")
        stages.append(stage)
        if stage not in STAGES:
            _d(diags, f"{producer_path}.stage", "unexpected producer stage")
        elif producer.get("repository") != REPOSITORIES[stage]:
            _d(diags, f"{producer_path}.repository", "wrong producer repository")

        runtime_pin = producer.get("runtime_pin")
        if not isinstance(runtime_pin, dict):
            _d(diags, f"{producer_path}.runtime_pin", "runtime_pin must be an object")
            runtime_pin = {}
        pr_head = producer.get("pr_head_sha")
        runtime = runtime_pin.get("merged_commit_sha")
        for sha_path, value in [
            (f"{producer_path}.pr_head_sha", pr_head),
            (f"{producer_path}.runtime_pin.merged_commit_sha", runtime),
        ]:
            if not isinstance(value, str) or not SHA_RE.fullmatch(value):
                _d(diags, sha_path, "commit must be lowercase 40-character SHA")
            if value in {"main", "master"} or (isinstance(value, str) and value.startswith("refs/")):
                _d(diags, sha_path, "moving refs are forbidden", code="PG-P05-MOVING-REF-FORBIDDEN")
        if runtime == pr_head and isinstance(runtime, str):
            _d(
                diags,
                f"{producer_path}.runtime_pin.merged_commit_sha",
                "PR head cannot be used as runtime pin",
                code="PG-P05-PR-HEAD-AS-RUNTIME-PIN",
            )

        artifacts = producer.get("artifacts")
        if not isinstance(artifacts, list):
            _d(diags, f"{producer_path}.artifacts", "artifacts must be an array")
            artifacts = []
        roles: list[str] = []
        for j, artifact in enumerate(artifacts):
            artifact_path = f"{producer_path}.artifacts[{j}]"
            if not isinstance(artifact, dict):
                _d(diags, artifact_path, "artifact entry must be an object", observed_type=type(artifact).__name__)
                continue
            role = artifact.get("role")
            if not isinstance(role, str):
                _d(diags, f"{artifact_path}.role", "artifact role must be a string")
                continue
            roles.append(role)
            if role not in ALLOWED_ROLES:
                _d(diags, f"{artifact_path}.role", "unexpected artifact role")
            if artifact.get("verification_status") == "verified" and artifact.get("canonical_status") == "insufficient_evidence":
                _d(diags, artifact_path, "artifact cannot be verified when canonical record is insufficient_evidence")
        if roles != sorted(roles):
            _d(diags, f"{producer_path}.artifacts", "artifact roles must be deterministically ordered")
        if "producer_gate_export_schema" not in roles:
            _d(diags, f"{producer_path}.artifacts", "missing required Producer Gate Export schema record")

    if stages != STAGES:
        _d(diags, "$.producers", "producer ordering must be architect, ce, builder, responsive and stages must be unique")
    return _result(diags)


def git_blob_sha256(repo: str | Path, commit_sha: str, path: str) -> dict[str, Any]:
    if not SHA_RE.fullmatch(commit_sha):
        return {
            "status": "invalid",
            "diagnostic": {
                "code": "PG-P05-MOVING-REF-FORBIDDEN",
                "severity": "error",
                "path": "$.commit_sha",
                "message": "Only immutable lowercase commit SHAs are accepted.",
                "repair_owner": "Project Gate",
            },
        }
    return git_blob_sha256_from_runner(repo, commit_sha, path)


def _result(diags: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "producer-adoption-validation-result.v1",
        "status": "invalid" if diags else "valid",
        "diagnostics": sorted(diags, key=lambda item: (item["path"], item["code"])),
    }


def _d(
    diags: list[dict[str, Any]],
    path: str,
    msg: str,
    code: str = "PG-P05-PRODUCER-REGISTRY-INVALID",
    **details: Any,
) -> None:
    diags.append(
        {
            "code": code,
            "severity": "error",
            "path": path,
            "message": msg,
            "details": details,
            "repair_owner": "Project Gate",
        }
    )
