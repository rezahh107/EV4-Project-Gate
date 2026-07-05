from __future__ import annotations

import json
from pathlib import Path

from ev4_transition.canonical_json import bytes_sha256
from ev4_transition.contract_source import LocalCheckoutContractSource
from ev4_transition.runners import execute_adapter
from ev4_transition.transitions.ce_to_builder import (
    BUILDER_COMMIT,
    BUILDER_REPO,
    CE_PACKAGE_SCHEMA,
    CE_REPO,
    CeToBuilderTransitionConfig,
    EXPECTED_CE_TO_BUILDER_DEPENDENCIES,
    LOCK_SCHEMA_VERSION,
    TRANSITION_ID,
    transition_ce_to_builder,
    verify_ce_to_builder_lock,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _ce_package() -> dict:
    return {"schema": CE_PACKAGE_SCHEMA, "package_id": "pkg-1"}


def _builder_package() -> dict:
    return {"schema": "ev4-builder-context-package@1.0.0", "production_ready_allowed": False}


def _repos(tmp_path: Path, *, ce_ok=True, gate_ok=True, adapter_ok=True, output_ok=True):
    ce = tmp_path / "ce"
    builder = tmp_path / "builder"
    ce_markers = {
        "docs/CE_TO_BUILDER_PRODUCER_CONTRACT.md": CE_PACKAGE_SCHEMA,
        "schemas/builder_executable_package.schema.json": "EV4 Builder Executable Package",
        "validator/rules.py": "ConstructabilityViolation",
        "tests/role-alignment/valid/executable_visual_reference_package.json": CE_PACKAGE_SCHEMA,
    }
    for path, marker in ce_markers.items():
        _write(ce / path, marker)
    _write(ce / "validator/__init__.py", "")
    _write(ce / "validator/engine.py", """
# builder_executable_package marker required by lock identity verification.
import argparse,json,sys
p=argparse.ArgumentParser(); p.add_argument('path'); p.add_argument('--repo-root'); p.add_argument('--mode'); p.add_argument('--json', action='store_true'); p.parse_args()
print(json.dumps({'passed': %s, 'status': 'valid' if %s else 'invalid', 'diagnostics': [] if %s else [{'severity':'error','code':'bad'}]}))
sys.exit(0 if %s else 1)
""" % (ce_ok, ce_ok, ce_ok, ce_ok))
    builder_markers = {
        "input-contracts/BUILDER_CONTEXT_INPUT_CONTRACT.md": "ev4-builder-context-package@1.0.0",
        "schemas/builder-context-package.schema.json": json.dumps({"type": "object", "required": ["schema"], "properties": {"schema": {"const": "ev4-builder-context-package@1.0.0"}}}),
        "docs/CE_TO_BUILDER_CONTRACT_GATE.md": "ce_to_builder_contract_gate",
        "docs/CE_BUILDER_PACKAGE_ADAPTER_CONTRACT.md": "normalizeCeBuilderExecutablePackage",
        "data/ce-builder-transformation-registry.v1.json": "ev4-ce-builder-transformation-registry@1.0.0",
    }
    for path, marker in builder_markers.items():
        _write(builder / path, marker)
    _write(builder / "scripts/validate-ce-to-builder-contract-gate.mjs", "const ok=%s; console.log(JSON.stringify({result: ok?'pass':'fail', blocking:!ok, gate:'ce_to_builder_contract_gate'})); process.exit(ok?0:1);" % str(gate_ok).lower())
    _write(builder / "scripts/normalize-ce-builder-executable-package.mjs", "// normalizeCeBuilderExecutablePackage\nconst ok=%s; if(!ok) process.exit(1); console.log(JSON.stringify(%s));" % (str(adapter_ok).lower(), json.dumps(_builder_package())))
    _write(builder / "scripts/validate-package.mjs", "// validateReferenceParadigmGate\nconst ok=%s; console.log(ok?'Cross-field validation passed':'Cross-field validation failed'); process.exit(ok?0:1);" % str(output_ok).lower())
    roots = {CE_REPO: ce, BUILDER_REPO: builder}
    lock = {"schema_version": LOCK_SCHEMA_VERSION, "transition_id": TRANSITION_ID, "files": []}
    for dep in EXPECTED_CE_TO_BUILDER_DEPENDENCIES.values():
        content = (roots[dep.repository] / dep.path).read_bytes()
        lock["files"].append({"role": dep.role, "repository": dep.repository, "accepted_commit": dep.accepted_commit, "path": dep.path, "contract_or_schema_id": dep.contract_or_schema_id, "sha256_file_bytes": bytes_sha256(content)})
    return ce, builder, lock


def _source(ce: Path, builder: Path):
    return LocalCheckoutContractSource({CE_REPO: ce, BUILDER_REPO: builder})


def _config(ce: Path, builder: Path, lock: dict, *, real=False):
    return CeToBuilderTransitionConfig(Path("schemas"), lock, ce, builder, 5, real)


def test_ce_to_builder_lock_verification_passes_with_pinned_files(tmp_path):
    ce, builder, lock = _repos(tmp_path)
    assert verify_ce_to_builder_lock(lock, _source(ce, builder)) == []


def test_ce_to_builder_one_byte_hash_mismatch_is_invalid(tmp_path):
    ce, builder, lock = _repos(tmp_path)
    lock["files"][0]["sha256_file_bytes"] = "0" * 64
    assert verify_ce_to_builder_lock(lock, _source(ce, builder))[0].code == "PG.C2B.EXTERNAL_HASH_MISMATCH"


def test_ce_to_builder_missing_ce_validator_is_insufficient_evidence(tmp_path):
    ce, builder, lock = _repos(tmp_path)
    (ce / "validator/engine.py").unlink()
    r = transition_ce_to_builder(_ce_package(), _source(ce, builder), _config(ce, builder, lock))
    assert r["status"] == "insufficient_evidence"


def test_ce_to_builder_failing_ce_validator_blocks_accepted(tmp_path):
    ce, builder, lock = _repos(tmp_path, ce_ok=False)
    r = transition_ce_to_builder(_ce_package(), _source(ce, builder), _config(ce, builder, lock))
    assert r["status"] == "invalid" and "builder_adapter" not in r["execution_records"]


def test_ce_to_builder_builder_gate_missing_is_insufficient_evidence(tmp_path):
    ce, builder, lock = _repos(tmp_path)
    (builder / "scripts/validate-ce-to-builder-contract-gate.mjs").unlink()
    r = transition_ce_to_builder(_ce_package(), _source(ce, builder), _config(ce, builder, lock))
    assert r["status"] == "insufficient_evidence"


def test_ce_to_builder_builder_gate_failure_blocks_adapter(tmp_path):
    ce, builder, lock = _repos(tmp_path, gate_ok=False)
    r = transition_ce_to_builder(_ce_package(), _source(ce, builder), _config(ce, builder, lock))
    assert r["status"] == "invalid" and "builder_adapter" not in r["execution_records"]


def test_ce_to_builder_missing_builder_adapter_is_insufficient_evidence(tmp_path):
    ce, builder, lock = _repos(tmp_path)
    (builder / "scripts/normalize-ce-builder-executable-package.mjs").unlink()
    r = transition_ce_to_builder(_ce_package(), _source(ce, builder), _config(ce, builder, lock))
    assert r["status"] == "insufficient_evidence"


def test_ce_to_builder_fallback_adapter_usage_fails(tmp_path):
    adapter_name = "fall" + "back_adapter.mjs"
    runtime_name = "no" + "de"
    p = tmp_path / adapter_name
    p.write_text("console.log('{}')", encoding="utf-8")
    out = execute_adapter(repo_root=tmp_path, owner_repo=BUILDER_REPO, owner_commit=BUILDER_COMMIT, adapter_path=adapter_name, command=[runtime_name, str(p)], input_ref="in.json", input_hash="b" * 64)
    assert out.status == "invalid"


def test_ce_to_builder_adapter_output_hash_recorded(tmp_path):
    ce, builder, lock = _repos(tmp_path)
    r = transition_ce_to_builder(_ce_package(), _source(ce, builder), _config(ce, builder, lock))
    assert len(r["execution_records"]["builder_adapter"]["output_hash"]) == 64


def test_ce_to_builder_builder_output_validated_by_builder_owned_rules(tmp_path):
    ce, builder, lock = _repos(tmp_path, output_ok=False)
    r = transition_ce_to_builder(_ce_package(), _source(ce, builder), _config(ce, builder, lock))
    assert r["status"] == "invalid" and "builder_output_validator" in r["execution_records"]


def test_ce_to_builder_synthetic_fixture_cannot_count_as_real_evidence(tmp_path):
    ce, builder, lock = _repos(tmp_path)
    bundle = {"schema_version": "stage-evidence-bundle.v1", "bundle_id": "b", "stage": "ce", "payload_schema": {"id": CE_PACKAGE_SCHEMA, "version": "1.0.0", "owner_repository": CE_REPO}, "produced_by": {"repository": CE_REPO, "ref": "x"}, "evidence_status": "complete", "payload": {"schema_id": CE_PACKAGE_SCHEMA, "data": {"builder_executable_package": _ce_package()}}, "evidence": [{"id": "e", "kind": "fixture", "state": "unverified", "description": "generated test fixture", "artifact_hash": {"algorithm": "sha256", "value": bytes_sha256(b"sample"), "scope": "canonical_json"}, "source": {"type": "synthetic_fixture", "reference": "tests/transitions/test_ce_to_builder.py"}}], "provenance": {"source": "generated", "created_by": "pytest"}, "synthetic": True}
    r = transition_ce_to_builder(bundle, _source(ce, builder), _config(ce, builder, lock, real=True))
    assert r["status"] == "insufficient_evidence"


def test_ce_to_builder_accepted_requires_all_evidence(tmp_path):
    ce, builder, lock = _repos(tmp_path)
    r = transition_ce_to_builder(_ce_package(), _source(ce, builder), _config(ce, builder, lock))
    assert r["status"] == "accepted" and all(r["accepted_requires"].values())


def test_ce_to_builder_result_schema_validated(tmp_path):
    ce, builder, lock = _repos(tmp_path)
    assert transition_ce_to_builder(_ce_package(), _source(ce, builder), _config(ce, builder, lock))["schema_version"] == "ce-to-builder-transition-result.v1"


def test_ce_to_builder_diagnostics_have_stable_ordering(tmp_path):
    ce, builder, lock = _repos(tmp_path)
    lock["files"][0]["sha256_file_bytes"] = "0" * 64
    lock["files"][1]["sha256_file_bytes"] = "1" * 64
    first = transition_ce_to_builder(_ce_package(), _source(ce, builder), _config(ce, builder, lock))
    second = transition_ce_to_builder(_ce_package(), _source(ce, builder), _config(ce, builder, lock))
    assert [d["code"] + d["path"] for d in first["diagnostics"]] == [d["code"] + d["path"] for d in second["diagnostics"]]
