from __future__ import annotations

import copy
import json
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from ev4_transition.canonical_json import canonical_sha256
from ev4_transition.producer_gate_export import ProducerGateExportValidator
from ev4_transition.producer_integration.intake import intake_producer_export
import ev4_transition.pcvp_carrier as pcvp
import ev4_transition.pcvp_owner as owner

from tests.unit.prompt00_fixture_factory import producer_export

ROOT = Path(__file__).resolve().parents[2]
LOCK_PATH = ROOT / "contracts/locks/pcvp-v1.lock.json"
KERNEL_ENV = "EV4_PCVP_KERNEL_REPO"


def _carrier() -> dict:
    return {
        "policy_id": "EV4-PCVP",
        "policy_version": "1.0.0",
        "source_stage": "ARCHITECT",
        "claims": [
            {
                "claim_id": "CLM-ARCH-001",
                "statement": "The bounded architecture draft has source evidence.",
                "criticality": "CRITICAL",
                "applicability_state": "APPLICABLE",
                "verification_state": "VERIFIED",
                "lifecycle_state": "ACTIVE",
                "evidence_refs": ["EVD-ARCH-001"],
                "dependency_refs": [],
                "assumption_refs": [],
            }
        ],
        "effects": [
            {
                "effect_id": "EFF-ARCH-001",
                "effect_class": "DRAFT_ONLY",
                "depends_on_claim_ids": ["CLM-ARCH-001"],
                "continuation_state": "CONTINUE",
                "authorization_ref": "AUTH-ARCH-001",
                "blocker_reason": None,
                "permitted_scope": "provisional architecture handoff only",
            }
        ],
        "authorizations": [
            {
                "authorization_id": "AUTH-ARCH-001",
                "basis": "PROFILE_PREAUTHORIZED",
                "status": "ACTIVE",
                "allowed_effect_ids": ["EFF-ARCH-001"],
                "allowed_effect_classes": ["DRAFT_ONLY"],
                "bound_unknown_ids": [],
                "bound_assumption_ids": [],
                "stage_scope": {
                    "from": "ARCHITECT",
                    "through": "CONSTRUCTABILITY_ENGINEER",
                },
                "permitted_scope": "provisional architecture handoff only",
                "valid_until_events": [
                    "NEW_MATERIAL_BLOCKER",
                    "OWNER_REVOCATION",
                    "SCOPE_EXPANSION",
                ],
            }
        ],
        "unresolved_items": [],
        "stage_summary": {
            "owner_projection": "GREEN",
            "yellow_substate": None,
            "derived_from_claim_ids": ["CLM-ARCH-001"],
            "current_effect_id": "EFF-ARCH-001",
            "lifecycle_state": "ACTIVE",
            "derivation_reason": "critical dependent claim is verified",
        },
    }


def _export(*, live_registry_pin: bool = False) -> dict:
    if live_registry_pin:
        return json.loads(
            (ROOT / "fixtures/producer-emitted/valid/architect-export.v1.json").read_text(
                encoding="utf-8"
            )
        )
    return producer_export()


def _kernel_repo() -> Path:
    value = os.environ.get(KERNEL_ENV)
    if not value:
        pytest.skip(f"{KERNEL_ENV} is required for exact owner integration tests")
    path = Path(value).resolve(strict=True)
    assert subprocess.check_output(
        ["git", "-C", str(path), "rev-parse", "HEAD"], text=True
    ).strip() == pcvp.CANONICAL_COMMIT
    return path


def _codes(result: dict) -> set[str]:
    return {item["code"] for item in result["diagnostics"]}


def _profile() -> dict:
    return {
        "profile_id": "EV4-PCVP-PROFILE-ARCHITECT",
        "profile_version": "1.0.0",
        "profile_status": "release_candidate",
        "policy_id": "EV4-PCVP",
        "policy_version": "1.0.0",
        "repository": "rezahh107/EV4-Architect-Repo",
        "stage_id": "ARCHITECT",
        "produces_for": ["CONSTRUCTABILITY_ENGINEER"],
        "preauthorized_effects": [
            {"effect_class": "REASONING_ONLY"},
            {"effect_class": "DRAFT_ONLY"},
        ],
        "safe_reversible_default_enabled": True,
        "safe_reversible_default_effect_classes": ["REASONING_ONLY", "DRAFT_ONLY"],
    }


def test_legacy_absence_is_dependency_free_and_lossless(monkeypatch: pytest.MonkeyPatch) -> None:
    artifact = _export()
    before = copy.deepcopy(artifact)
    monkeypatch.setattr(owner.shutil, "which", lambda name: pytest.fail(f"unexpected {name}"))

    result = ProducerGateExportValidator(ROOT, operational=False).validate(artifact)

    assert result["status"] == "valid", result
    assert result["pcvp_carrier"]["status"] == "legacy_absent"
    assert result["pcvp_carrier"]["compatibility_mode"] == "DUAL_READ"
    assert result["pcvp_carrier"]["activation_effect"] == "NONE"
    assert artifact == before


def test_present_carrier_without_owner_checkout_is_insufficient() -> None:
    artifact = _export(live_registry_pin=True)
    artifact["continuation_assurance"] = _carrier()

    result = intake_producer_export(artifact, repository_root=ROOT)

    assert result["status"] == "insufficient_evidence"
    assert result["pcvp_carrier"]["status"] == "insufficient_evidence"
    assert "PG_PCVP_OWNER_AUTHORITY_UNVERIFIED" in _codes(result)
    assert result["handoff_allowed"] is False


def test_exact_owner_execution_validates_losslessly_without_activation() -> None:
    kernel = _kernel_repo()
    artifact = _export(live_registry_pin=True)
    artifact["continuation_assurance"] = _carrier()
    before = copy.deepcopy(artifact)

    result = intake_producer_export(
        artifact,
        repository_root=ROOT,
        decision_kernel_repo=kernel,
    )

    assert result["status"] == "accepted", result
    projection = result["pcvp_carrier"]
    assert projection["status"] == "validated"
    assert projection["owner_observed_layer"] == "ACCEPT"
    assert projection["profile_id"] == "EV4-PCVP-PROFILE-ARCHITECT"
    assert projection["downstream_stage"] == "CONSTRUCTABILITY_ENGINEER"
    assert projection["adoption_status"] == "not_yet_adopted"
    assert projection["activation_effect"] == "NONE"
    assert projection["carrier"] == {"continuation_assurance": before["continuation_assurance"]}
    assert projection["canonical_sha256"] == canonical_sha256(projection["carrier"])
    assert result["handoff_allowed"] is False
    assert artifact == before


def test_owner_fixture_suite_passes_at_declared_layers() -> None:
    kernel = _kernel_repo()
    artifact = _export(live_registry_pin=True)
    artifact["continuation_assurance"] = _carrier()

    result = intake_producer_export(
        artifact,
        repository_root=ROOT,
        decision_kernel_repo=kernel,
    )

    fixtures = result["pcvp_carrier"]["owner_bundle_fixtures"]
    assert fixtures["total"] == 18
    assert fixtures["valid"] == 8
    assert fixtures["invalid"] == 10
    assert fixtures["all_passed_at_declared_layer"] is True
    assert all(item["passed"] is True for item in fixtures["results"])


@pytest.mark.parametrize(
    ("mutation", "expected_code"),
    [
        (
            lambda carrier: carrier.update(policy_version="2.0.0"),
            "PG_PCVP_CARRIER_SCHEMA_INVALID",
        ),
        (
            lambda carrier: carrier["authorizations"][0].update(status="REVOKED"),
            "PG_PCVP_EFFECT_AUTH_NOT_ACTIVE",
        ),
        (
            lambda carrier: carrier["effects"][0].update(depends_on_claim_ids=["CLM-MISSING"]),
            "PG_PCVP_EFFECT_CLAIM_REF_UNRESOLVED",
        ),
    ],
)
def test_owner_rejections_are_not_bypassed(mutation, expected_code: str) -> None:
    kernel = _kernel_repo()
    artifact = _export(live_registry_pin=True)
    artifact["continuation_assurance"] = _carrier()
    mutation(artifact["continuation_assurance"])

    result = intake_producer_export(
        artifact,
        repository_root=ROOT,
        decision_kernel_repo=kernel,
    )

    assert result["status"] == "invalid"
    assert result["pcvp_carrier"]["status"] == "invalid"
    assert expected_code in _codes(result)
    assert result["handoff_allowed"] is False


def test_profile_preauthorization_rejects_external_and_irreversible_classes() -> None:
    binding = pcvp.PROFILE_BINDINGS["ARCHITECT"]
    for effect_class in ("EXTERNAL_MUTATION", "IRREVERSIBLE_OR_AUTHORITY_BEARING"):
        carrier = _carrier()
        carrier["effects"][0]["effect_class"] = effect_class
        carrier["authorizations"][0]["allowed_effect_classes"] = [effect_class]
        diagnostics = pcvp._profile_integration_diagnostics(
            _profile(),
            binding,
            {"continuation_assurance": carrier},
            source_stage="ARCHITECT",
            downstream_stage="CONSTRUCTABILITY_ENGINEER",
        )
        assert "PG_PCVP_PROFILE_PREAUTHORIZATION_REJECTED" in {item.code for item in diagnostics}


def test_safe_default_and_stage_scope_profile_checks_are_exact() -> None:
    binding = pcvp.PROFILE_BINDINGS["ARCHITECT"]
    carrier = _carrier()
    carrier["authorizations"][0]["basis"] = "SAFE_REVERSIBLE_DEFAULT"
    carrier["effects"][0]["effect_class"] = "REVERSIBLE_LOCAL_CHANGE"
    carrier["authorizations"][0]["allowed_effect_classes"] = ["REVERSIBLE_LOCAL_CHANGE"]
    carrier["authorizations"][0]["stage_scope"] = {
        "from": "BUILDER_ASSISTANT",
        "through": "PROJECT_GATE",
    }
    profile = _profile()
    profile["produces_for"] = ["PROJECT_GATE"]

    diagnostics = pcvp._profile_integration_diagnostics(
        profile,
        binding,
        {"continuation_assurance": carrier},
        source_stage="ARCHITECT",
        downstream_stage="CONSTRUCTABILITY_ENGINEER",
    )
    codes = {item.code for item in diagnostics}
    assert "PG_PCVP_PROFILE_DOWNSTREAM_NOT_ALLOWED" in codes
    assert "PG_PCVP_PROFILE_SAFE_DEFAULT_REJECTED" in codes
    assert "PG_PCVP_STAGE_SCOPE_FROM_MISMATCH" in codes
    assert "PG_PCVP_STAGE_SCOPE_THROUGH_MISMATCH" in codes


def test_wrong_profile_identity_is_rejected() -> None:
    profile = _profile()
    profile["repository"] = "rezahh107/EV4-Project-Gate"
    diagnostics = pcvp._profile_integration_diagnostics(
        profile,
        pcvp.PROFILE_BINDINGS["ARCHITECT"],
        {"continuation_assurance": _carrier()},
        source_stage="ARCHITECT",
        downstream_stage="CONSTRUCTABILITY_ENGINEER",
    )
    assert "PG_PCVP_PROFILE_IDENTITY_MISMATCH" in {item.code for item in diagnostics}


def test_owner_authority_identity_rejects_wrong_commit_and_repository(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    owner_path = tmp_path / "owner"
    owner_path.mkdir()
    monkeypatch.setattr(owner.shutil, "which", lambda name: "/usr/bin/git")
    monkeypatch.setattr(owner, "_load_lock", lambda root: ({}, []))
    monkeypatch.setattr(owner, "_verify_files", lambda root, lock, git: [])

    values = iter((str(owner_path), "0" * 40, "https://github.com/example/wrong.git"))
    monkeypatch.setattr(owner, "_git", lambda *args: next(values))

    authority, diagnostics = pcvp._verify_owner_authority(ROOT, owner_path, "ARCHITECT")
    assert authority is None
    assert {item.code for item in diagnostics} == {"PG_PCVP_OWNER_AUTHORITY_UNVERIFIED"}
    reasons = {item.details.get("reason") for item in diagnostics}
    assert "commit_mismatch" in reasons
    assert "repository_identity_mismatch" in reasons


def test_node_and_malformed_bridge_fail_closed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    authority = pcvp.OwnerAuthority(
        root=tmp_path,
        validator_path=tmp_path / "pcvp-v1.mjs",
        bundle_root=tmp_path / "bundle",
        profile_path=tmp_path / "profile.yaml",
        profile_binding=pcvp.PROFILE_BINDINGS["ARCHITECT"],
    )
    monkeypatch.setattr(owner.shutil, "which", lambda name: None)
    response, diagnostics = pcvp._run_owner_bridge(
        authority, {"continuation_assurance": _carrier()}
    )
    assert response is None
    assert diagnostics[0].severity == "insufficient_evidence"

    monkeypatch.setattr(owner.shutil, "which", lambda name: "/usr/bin/node")
    monkeypatch.setattr(
        owner.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0,
            stdout='{"schema_version":"ev4-pcvp-owner-bridge-response.v1","status":"OK"} trailing',
            stderr="",
        ),
    )
    response, diagnostics = pcvp._run_owner_bridge(
        authority, {"continuation_assurance": _carrier()}
    )
    assert response is None
    assert diagnostics[0].code == "PG_PCVP_OWNER_RESPONSE_INVALID"


def test_execution_lock_covers_exact_owner_authority_set() -> None:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    assert lock["schema_version"] == "ev4-pcvp-execution-authority-lock.v1"
    assert lock["architecture_lock_id"] == "EV4-PCVP-ROLL-LOCK-20260727-R1"
    assert lock["owner"] == {
        "repository": pcvp.CANONICAL_REPOSITORY,
        "commit_sha": pcvp.CANONICAL_COMMIT,
        "bundle_root": pcvp.BUNDLE_ROOT,
        "validator_path": pcvp.VALIDATOR_PATH,
    }
    assert lock["policy"]["adoption_status"] == "not_yet_adopted"
    assert lock["policy"]["activation"] == "NONE"
    assert {item["path"] for item in lock["authority_files"]} == pcvp._expected_authority_paths()
    assert all(item.get("sha256_file_bytes") or item.get("git_blob_sha") for item in lock["authority_files"])


def test_no_executable_local_owner_mirror_or_canonical_semantic_fallback() -> None:
    source = (ROOT / "src/ev4_transition/pcvp_carrier.py").read_text(encoding="utf-8")
    assert "Draft202012Validator" not in source
    assert "_cross_record_diagnostics" not in source
    assert "_projection_diagnostics" not in source
    assert not (ROOT / "contracts/vendor/decision-kernel/pcvp/v1.0.0").exists()
