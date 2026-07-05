from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from ev4_transition.canonical_json import bytes_sha256, canonical_sha256, load_json_file, write_canonical_json
from ev4_transition.contract_source import ContractSource, LocalCheckoutContractSource
from ev4_transition.diagnostics import Diagnostic, diagnostic, project_gate_status_from_diagnostics, sort_diagnostics

GATE_ID = "ev4-final-evidence-gate@1.0.0"
GATE_VERSION = "1.0.0"
LOCK_SCHEMA_VERSION = "final-gate-lock.v1"
PG_REPO = "rezahh107/EV4-Project-Gate"
PG_COMMIT = "main"
RESPONSIVE_REPO = "rezahh107/EV4-Responsive-Architect"
RESPONSIVE_COMMIT = "main"
RESPONSIVE_OUTPUT_SCHEMA = "ev4-responsive-output@0.3.0"
RESPONSIVE_OUTPUT_SCHEMA_PATH = "schemas/ev4-responsive-output.schema.json"
RESPONSIVE_OUTPUT_VALIDATOR = "validation/e2e/run_responsive_tree_architecture_refactor_check.py"

FORBIDDEN_FINAL_CLAIMS = {
    "production_ready",
    "release_ready",
    "pixel_perfect",
    "live_render_validated",
    "export_json_validated",
    "export_validated",
    "accessibility_passed",
    "responsive_correctness_validated",
    "ci_success_as_frontend_evidence",
    "frontend_correctness",
    "production_readiness",
    "responsive_correctness",
}


@dataclass(frozen=True)
class ExpectedDependency:
    role: str
    repository: str
    accepted_commit: str
    path: str
    contract_or_schema_id: str
    identity_marker: str


_EXPECTED_ITEMS = [
    ExpectedDependency("project_gate_a2c_lock", PG_REPO, PG_COMMIT, "contracts/locks/architect-to-ce-transition.v1.lock.json", "architect-to-ce-transition-lock.v1", "architect"),
    ExpectedDependency("project_gate_c2b_lock", PG_REPO, PG_COMMIT, "contracts/locks/ce-to-builder-transition.v1.lock.json", "ce-to-builder-transition-lock.v1", "ce-to-builder"),
    ExpectedDependency("project_gate_b2r_lock", PG_REPO, PG_COMMIT, "contracts/locks/builder-to-responsive-transition.v1.lock.json", "builder-to-responsive-transition-lock.v1", "builder-to-responsive"),
    ExpectedDependency("responsive_input_boundary", RESPONSIVE_REPO, RESPONSIVE_COMMIT, "contracts/BUILDER_TO_RESPONSIVE_INPUT_BOUNDARY.md", "builder-responsive-input-boundary", "Builder"),
    ExpectedDependency("responsive_output_schema", RESPONSIVE_REPO, RESPONSIVE_COMMIT, RESPONSIVE_OUTPUT_SCHEMA_PATH, RESPONSIVE_OUTPUT_SCHEMA, "responsive-output"),
    ExpectedDependency("responsive_output_validator", RESPONSIVE_REPO, RESPONSIVE_COMMIT, RESPONSIVE_OUTPUT_VALIDATOR, "responsive-output-validator", "responsive"),
]
EXPECTED_FINAL_GATE_DEPENDENCIES = {item.role: item for item in _EXPECTED_ITEMS}
REQUIRED_ROLES = set(EXPECTED_FINAL_GATE_DEPENDENCIES)


@dataclass(frozen=True)
class FinalGateConfig:
    schema_root: Path
    lock: dict[str, Any]
    project_gate_repo_root: Path | None = None
    responsive_repo_root: Path | None = None
    timeout_seconds: float = 30
    require_real_evidence: bool = True


def verify_final_gate_lock(lock: dict[str, Any], source: ContractSource) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    if not isinstance(lock, dict):
        return [diagnostic("PG.FINAL.LOCK_NOT_OBJECT", "error", "Final gate lock manifest must be an object.", "$")]
    if lock.get("schema_version") != LOCK_SCHEMA_VERSION:
        diagnostics.append(diagnostic("PG.FINAL.LOCK_VERSION_MISMATCH", "error", "Final gate lock schema version is missing or unknown.", "$.schema_version", expected=LOCK_SCHEMA_VERSION, actual=lock.get("schema_version")))
    if lock.get("gate_id") != GATE_ID:
        diagnostics.append(diagnostic("PG.FINAL.LOCK_TRANSITION_ID_MISMATCH", "error", "Final gate id does not match this gate.", "$.gate_id", expected=GATE_ID, actual=lock.get("gate_id")))
    files = lock.get("files")
    if not isinstance(files, list):
        diagnostics.append(diagnostic("PG.FINAL.LOCK_FILES_NOT_ARRAY", "error", "Final gate lock files must be an array.", "$.files"))
        return sort_diagnostics(diagnostics)
    seen: set[str] = set()
    for index, item in enumerate(files):
        path = f"$.files[{index}]"
        if not isinstance(item, dict):
            diagnostics.append(diagnostic("PG.FINAL.LOCK_ENTRY_NOT_OBJECT", "error", "Lock entry must be an object.", path))
            continue
        role = item.get("role")
        expected = EXPECTED_FINAL_GATE_DEPENDENCIES.get(role)
        if expected is None:
            diagnostics.append(diagnostic("PG.FINAL.LOCK_ROLE_UNEXPECTED", "error", "Unexpected final gate lock role.", f"{path}.role", role=role))
            continue
        seen.add(role)
        for field, expected_value, code in [
            ("repository", expected.repository, "PG.FINAL.LOCK_REPOSITORY_MISMATCH"),
            ("accepted_commit", expected.accepted_commit, "PG.FINAL.LOCK_COMMIT_MISMATCH"),
            ("path", expected.path, "PG.FINAL.LOCK_PATH_MISMATCH"),
            ("contract_or_schema_id", expected.contract_or_schema_id, "PG.FINAL.LOCK_IDENTITY_MISMATCH"),
        ]:
            if item.get(field) != expected_value:
                diagnostics.append(diagnostic(code, "error", "Final gate lock entry does not match expected dependency.", f"{path}.{field}", expected=expected_value, actual=item.get(field), role=role))
        try:
            content = source.read_bytes(expected.repository, expected.accepted_commit, expected.path)
        except Exception as exc:
            diagnostics.append(diagnostic("PG.FINAL.OWNER_FILE_READ_FAILED", "insufficient_evidence", "Pinned final gate owner file could not be read.", path, role=role, repository=expected.repository, file_path=expected.path, error_type=type(exc).__name__))
            continue
        if item.get("sha256_file_bytes") != bytes_sha256(content):
            diagnostics.append(diagnostic("PG.FINAL.EXTERNAL_HASH_MISMATCH", "error", "Pinned final gate file hash does not match lock manifest.", path, role=role, repository=expected.repository, file_path=expected.path))
        if expected.identity_marker not in content.decode("utf-8", errors="replace"):
            diagnostics.append(diagnostic("PG.FINAL.EXTERNAL_IDENTITY_MISMATCH", "error", "Pinned final gate identity marker was not found.", path, role=role, repository=expected.repository, file_path=expected.path))
    missing = sorted(REQUIRED_ROLES - seen)
    if missing:
        diagnostics.append(diagnostic("PG.FINAL.LOCK_ROLE_MISSING", "error", "Final gate lock is missing required owner dependency roles.", "$.files", missing_roles=missing))
    return sort_diagnostics(diagnostics)


def final_gate_from_local_paths(final_input: Any, schema_root: str | Path, lock_path: str | Path, project_gate_repo: str | Path, responsive_repo: str | Path, *, timeout_seconds: float = 30, require_real_evidence: bool = True) -> dict[str, Any]:
    config = FinalGateConfig(Path(schema_root), load_json_file(lock_path), Path(project_gate_repo), Path(responsive_repo), timeout_seconds, require_real_evidence)
    source = LocalCheckoutContractSource({PG_REPO: Path(project_gate_repo), RESPONSIVE_REPO: Path(responsive_repo)})
    return run_final_gate(final_input, source, config)


def run_final_gate(final_input: Any, contract_source: ContractSource, config: FinalGateConfig, progress_sink: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    diagnostics: list[Diagnostic] = []
    accepted_requires = {
        "prior_lock_chain_verified": False,
        "responsive_output_present": False,
        "responsive_output_schema_verified": False,
        "responsive_output_validator_passed": False,
        "real_evidence_present": False,
        "no_forbidden_final_claim": False,
        "result_schema_valid": False,
    }

    if not isinstance(final_input, dict):
        diagnostics.append(diagnostic("PG.FINAL.INPUT_NOT_OBJECT", "error", "Final gate input must be an object.", "$", observed_type=type(final_input).__name__))
        return _result(final_input, None, diagnostics, accepted_requires, config)

    output = final_input.get("responsive_output") if isinstance(final_input.get("responsive_output"), dict) else final_input
    if not isinstance(output, dict):
        diagnostics.append(diagnostic("PG.FINAL.RESPONSIVE_OUTPUT_MISSING", "insufficient_evidence", "Responsive output evidence is missing.", "$.responsive_output"))
        return _result(final_input, None, diagnostics, accepted_requires, config)
    accepted_requires["responsive_output_present"] = True

    lock_diags = verify_final_gate_lock(config.lock, contract_source)
    diagnostics.extend(lock_diags)
    accepted_requires["prior_lock_chain_verified"] = not any(d.severity in {"error", "insufficient_evidence"} for d in lock_diags)

    forbidden = _find_forbidden_claims(final_input)
    if forbidden:
        diagnostics.append(diagnostic("PG.FINAL.FORBIDDEN_CLAIM", "error", "Final gate input contains forbidden readiness/correctness claims.", "$", forbidden_claims=forbidden))
    accepted_requires["no_forbidden_final_claim"] = not forbidden

    if _contains_key_or_value(final_input, "ci_success_as_frontend_evidence"):
        diagnostics.append(diagnostic("PG.FINAL.CI_FRONTEND_CORRECTNESS_CLAIM", "error", "CI success is not frontend correctness evidence.", "$"))

    if _synthetic_only(final_input):
        diagnostics.append(diagnostic("PG.FINAL.SYNTHETIC_ONLY_EVIDENCE", "insufficient_evidence", "Synthetic fixtures cannot satisfy final real-evidence requirements.", "$"))
    accepted_requires["real_evidence_present"] = _real_evidence_present(final_input) and not _synthetic_only(final_input)
    if config.require_real_evidence and not accepted_requires["real_evidence_present"]:
        diagnostics.append(diagnostic("PG.FINAL.REAL_EVIDENCE_MISSING", "insufficient_evidence", "Final gate requires real non-synthetic Responsive evidence.", "$.evidence"))

    schema = _load_responsive_output_schema(contract_source, diagnostics)
    if schema is not None:
        accepted_requires["responsive_output_schema_verified"] = True
        for err in sorted(Draft202012Validator(schema).iter_errors(output), key=lambda item: (list(item.path), item.message)):
            diagnostics.append(diagnostic("PG.FINAL.RESPONSIVE_SCHEMA_VALIDATION_FAILED", "error", err.message, _json_path(list(err.path))))

    accepted_requires["responsive_output_validator_passed"] = _run_responsive_output_validator(config, output, diagnostics)
    return _result(final_input, output, diagnostics, accepted_requires, config)


def _load_responsive_output_schema(source: ContractSource, diagnostics: list[Diagnostic]) -> dict[str, Any] | None:
    try:
        raw = source.read_bytes(RESPONSIVE_REPO, RESPONSIVE_COMMIT, RESPONSIVE_OUTPUT_SCHEMA_PATH)
        schema = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        diagnostics.append(diagnostic("PG.FINAL.RESPONSIVE_SCHEMA_UNAVAILABLE", "insufficient_evidence", "Responsive-owned output schema is absent or unreadable.", "$.responsive_schema", error_type=type(exc).__name__))
        return None
    return schema if isinstance(schema, dict) else None


def _run_responsive_output_validator(config: FinalGateConfig, output: dict[str, Any], diagnostics: list[Diagnostic]) -> bool:
    if config.responsive_repo_root is None:
        diagnostics.append(diagnostic("PG.FINAL.RESPONSIVE_VALIDATOR_MISSING", "insufficient_evidence", "Responsive checkout is required to run the official output validator.", "$.responsive_validator"))
        return False
    validator = Path(config.responsive_repo_root) / RESPONSIVE_OUTPUT_VALIDATOR
    if not validator.exists():
        diagnostics.append(diagnostic("PG.FINAL.RESPONSIVE_VALIDATOR_MISSING", "insufficient_evidence", "Official Responsive output validator is absent.", "$.responsive_validator", validator_path=RESPONSIVE_OUTPUT_VALIDATOR))
        return False
    with tempfile.TemporaryDirectory(prefix="ev4-final-") as td:
        payload = Path(td) / "responsive-output.json"
        write_canonical_json(payload, output)
        completed = subprocess.run([sys.executable, str(validator), str(payload)], cwd=config.responsive_repo_root, text=True, capture_output=True, timeout=config.timeout_seconds, check=False)
    if completed.returncode != 0:
        diagnostics.append(diagnostic("PG.FINAL.RESPONSIVE_VALIDATOR_FAILED", "insufficient_evidence", "Official Responsive output validator did not pass.", "$.responsive_validator", exit_code=completed.returncode))
        return False
    return True


def _result(original: Any, output: dict[str, Any] | None, diagnostics: list[Diagnostic], accepted_requires: dict[str, bool], config: FinalGateConfig) -> dict[str, Any]:
    ordered = sort_diagnostics(diagnostics)
    if not ordered and not all(accepted_requires.values()):
        missing = sorted(k for k, v in accepted_requires.items() if not v and k != "result_schema_valid")
        ordered = sort_diagnostics([diagnostic("PG.FINAL.ACCEPTED_REQUIRES_MISSING", "insufficient_evidence", "Accepted final status requires every accepted_requires item to be true.", "$.accepted_requires", missing=missing)])
    status = project_gate_status_from_diagnostics(ordered)
    result = {
        "schema_version": "final-gate-result.v1",
        "result_type": "final_evidence_gate",
        "gate_id": GATE_ID,
        "gate_version": GATE_VERSION,
        "status": status,
        "diagnostics": [d.to_dict() for d in ordered],
        "accepted_requires": {**accepted_requires, "result_schema_valid": True},
        "hashes": {"source_input_hash": {"algorithm": "sha256", "canonicalization": "ev4-canonical-json.v1", "scope": "source_input", "value": _safe_hash(original)}},
        "output": output if status == "accepted" else None,
    }
    _validate_result_schema(config.schema_root, result)
    return result


def _validate_result_schema(schema_root: Path, result: dict[str, Any]) -> None:
    path = schema_root / "final-gate-result" / "final-gate-result.v1.schema.json"
    if not path.exists():
        return
    errors = sorted(Draft202012Validator(load_json_file(path)).iter_errors(result), key=lambda item: (list(item.path), item.message))
    if errors:
        raise RuntimeError("; ".join(f"{_json_path(list(e.path))}: {e.message}" for e in errors))


def _find_forbidden_claims(value: Any) -> list[str]:
    found: set[str] = set()

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, child in node.items():
                if isinstance(key, str) and key in FORBIDDEN_FINAL_CLAIMS:
                    found.add(key)
                walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)
        elif isinstance(node, str):
            token = node.strip()
            if token in FORBIDDEN_FINAL_CLAIMS:
                found.add(token)

    walk(value)
    return sorted(found)


def _contains_key_or_value(value: Any, needle: str) -> bool:
    if isinstance(value, dict):
        return any(k == needle or _contains_key_or_value(v, needle) for k, v in value.items())
    if isinstance(value, list):
        return any(_contains_key_or_value(v, needle) for v in value)
    return value == needle


def _synthetic_only(value: Any) -> bool:
    return _contains_key_or_value(value, "synthetic_only") or _contains_key_or_value(value, "synthetic_fixture")


def _real_evidence_present(value: Any) -> bool:
    if isinstance(value, dict):
        if value.get("evidence_status") == "real" or value.get("real_evidence") is True:
            return True
        return any(_real_evidence_present(v) for v in value.values())
    if isinstance(value, list):
        return any(_real_evidence_present(v) for v in value)
    return False


def _safe_hash(value: Any) -> str:
    try:
        return canonical_sha256(value)
    except Exception:
        return bytes_sha256(b"unhashable")


def _json_path(parts: list[Any]) -> str:
    out = "$"
    for part in parts:
        out += f"[{part}]" if isinstance(part, int) else f".{part}"
    return out
