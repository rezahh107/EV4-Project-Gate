from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from ev4_transition.common_contracts import validate_common_contract_lock, verify_vendored_common_contract

from .prompt00_fixture_factory import ROOT, load_json, lock_for


def codes(result: dict) -> set[str]:
    return {item["code"] for item in result["diagnostics"]}


def test_valid_exact_byte_lock_passes(tmp_path: Path) -> None:
    producer_root = tmp_path / "producer"
    lock = lock_for(ROOT, producer_root)
    assert validate_common_contract_lock(lock, ROOT) == []
    result = verify_vendored_common_contract(lock, ROOT, producer_root, ROOT)
    assert result["status"] == "valid"
    assert result["byte_equal"] is True
    assert result["schema_identity_valid"] is True


def test_invalid_lock_fixture_recipes_emit_expected_diagnostics(tmp_path: Path) -> None:
    recipes = load_json("tests/fixtures/common_contract_lock/invalid/cases.json")
    assert recipes["synthetic"] is True
    for case in recipes["cases"]:
        producer_root = tmp_path / case["name"]
        lock = lock_for(ROOT, producer_root)
        if case["name"] == "canonical_ref_main": lock["canonical"]["commit_sha"] = "main"
        elif case["name"] == "malformed_commit_sha": lock["canonical"]["commit_sha"] = "ABC"
        elif case["name"] == "canonical_hash_mismatch": lock["canonical"]["file_sha256"] = "0" * 64
        elif case["name"] == "vendored_hash_mismatch": lock["vendored"]["file_sha256"] = "0" * 64
        elif case["name"] == "byte_mismatch_semantically_equal":
            target = producer_root / lock["vendored"]["path"]
            parsed = json.loads(target.read_text(encoding="utf-8"))
            target.write_text(json.dumps(parsed, sort_keys=True, separators=(",", ":")), encoding="utf-8")
            lock["vendored"]["file_sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
        elif case["name"] == "local_copy_authoritative_true": lock["vendored"]["local_copy_authoritative"] = True
        elif case["name"] == "moving_default_branch_comparison_enabled": lock["verification"]["compare_against_moving_default_branch"] = True
        elif case["name"] == "contract_owner_drift": lock["contract_owner"] = "rezahh107/EV4-Architect-Repo"
        elif case["name"] == "canonical_path_drift": lock["canonical"]["path"] = "contracts/common/common-contract-lock.v1.schema.json"
        elif case["name"] == "root_relative_path": lock["vendored"]["path"] = "/contracts/project-gate/producer-gate-export.v1.schema.json"
        elif case["name"] == "path_traversal": lock["vendored"]["path"] = "../producer-gate-export.v1.schema.json"
        elif case["name"] == "absolute_path": lock["vendored"]["path"] = str((producer_root / "contracts/project-gate/producer-gate-export.v1.schema.json").resolve())
        elif case["name"] == "backslash_path": lock["vendored"]["path"] = r"contracts\project-gate\producer-gate-export.v1.schema.json"
        elif case["name"] == "missing_file": (producer_root / lock["vendored"]["path"]).unlink()
        else: raise AssertionError(case["name"])
        result = verify_vendored_common_contract(lock, ROOT, producer_root, ROOT)
        assert result["status"] == "invalid", case["name"]
        assert case["expected_code"] in codes(result), (case["name"], result)


def test_semantic_equality_never_replaces_byte_equality(tmp_path: Path) -> None:
    producer_root = tmp_path / "producer"
    lock = lock_for(ROOT, producer_root)
    target = producer_root / lock["vendored"]["path"]
    parsed = json.loads(target.read_text(encoding="utf-8"))
    target.write_text(json.dumps(parsed, sort_keys=True, separators=(",", ":")), encoding="utf-8")
    lock["vendored"]["file_sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
    result = verify_vendored_common_contract(lock, ROOT, producer_root, ROOT)
    assert "PG_COMMON_CONTRACT_BYTE_MISMATCH" in codes(result)
    assert "PG_COMMON_CONTRACT_SEMANTIC_EQUALITY_ONLY" in codes(result)


def test_verifier_source_has_no_network_or_git_dependency() -> None:
    source = (ROOT / "src/ev4_transition/common_contracts.py").read_text(encoding="utf-8")
    for token in ("requests", "urllib", "httpx", "subprocess", "git clone", "api.github.com"):
        assert token not in source


def test_reusable_workflow_is_read_only_and_sha_pinned() -> None:
    workflow = (ROOT / ".github/workflows/verify-vendored-common-contract.yml").read_text(encoding="utf-8")
    assert "workflow_call:" in workflow
    assert "permissions:\n  contents: read" in workflow
    assert "persist-credentials: false" in workflow
    assert "ref: ${{ steps.lock.outputs.commit_sha }}" in workflow
    assert "@main" not in workflow
    assert "contents: write" not in workflow
