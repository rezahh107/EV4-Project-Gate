from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from ev4_transition.canonical_json import canonical_sha256
from ev4_transition.producer_gate_export import ProducerGateExportValidator
from ev4_transition.producer_integration.intake import intake_producer_export

from tests.unit.prompt00_fixture_factory import producer_export

ROOT = Path(__file__).resolve().parents[2]
LOCK_PATH = ROOT / "contracts/locks/pcvp-v1.lock.json"
VENDORED_ROOT = ROOT / "contracts/vendor/decision-kernel/pcvp/v1.0.0"


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
            (
                ROOT
                / "fixtures/producer-emitted/valid/architect-export.v1.json"
            ).read_text(encoding="utf-8")
        )
    return producer_export()


def _codes(result: dict) -> set[str]:
    return {item["code"] for item in result["diagnostics"]}


def test_legacy_export_without_pcvp_carrier_remains_valid() -> None:
    artifact = _export()
    before = copy.deepcopy(artifact)
    result = ProducerGateExportValidator(ROOT, operational=False).validate(
        artifact
    )

    assert result["status"] == "valid", result
    assert result["pcvp_carrier"]["status"] == "legacy_absent"
    assert result["pcvp_carrier"]["compatibility_mode"] == "DUAL_READ"
    assert result["pcvp_carrier"]["activation_effect"] == "NONE"
    assert artifact == before


def test_valid_carrier_is_surfaced_losslessly_without_activation() -> None:
    artifact = _export(live_registry_pin=True)
    artifact["continuation_assurance"] = _carrier()
    before = copy.deepcopy(artifact)

    result = intake_producer_export(artifact, repository_root=ROOT)

    assert result["status"] == "accepted", result
    assert result["pcvp_carrier"]["status"] == "validated"
    assert result["pcvp_carrier"]["policy_id"] == "EV4-PCVP"
    assert result["pcvp_carrier"]["policy_version"] == "1.0.0"
    assert result["pcvp_carrier"]["source_stage"] == "ARCHITECT"
    assert result["pcvp_carrier"]["adoption_status"] == "not_yet_adopted"
    assert result["pcvp_carrier"]["activation_effect"] == "NONE"
    assert result["pcvp_carrier"]["carrier"] == {
        "continuation_assurance": before["continuation_assurance"]
    }
    assert result["pcvp_carrier"]["canonical_sha256"] == canonical_sha256(
        result["pcvp_carrier"]["carrier"]
    )
    assert artifact == before


def test_unsupported_policy_version_fails_closed() -> None:
    artifact = _export()
    artifact["continuation_assurance"] = _carrier()
    artifact["continuation_assurance"]["policy_version"] = "2.0.0"

    result = ProducerGateExportValidator(ROOT, operational=False).validate(
        artifact
    )

    assert result["status"] == "invalid"
    assert "PG_PCVP_CARRIER_SCHEMA_INVALID" in _codes(result)
    assert result["pcvp_carrier"]["status"] == "invalid"


def test_wrong_repository_profile_stage_fails_closed() -> None:
    artifact = _export()
    artifact["continuation_assurance"] = _carrier()
    artifact["continuation_assurance"]["source_stage"] = "PROJECT_GATE"

    result = ProducerGateExportValidator(ROOT, operational=False).validate(
        artifact
    )

    assert result["status"] == "invalid"
    assert "PG_PCVP_SOURCE_STAGE_MISMATCH" in _codes(result)


@pytest.mark.parametrize(
    ("mutation", "expected_code"),
    [
        (
            lambda carrier: carrier["authorizations"][0].update(
                status="REVOKED"
            ),
            "PG_PCVP_EFFECT_AUTH_NOT_ACTIVE",
        ),
        (
            lambda carrier: carrier["authorizations"][0].update(
                allowed_effect_ids=[],
                allowed_effect_classes=["REASONING_ONLY"],
            ),
            "PG_PCVP_EFFECT_AUTH_NOT_COVERING",
        ),
        (
            lambda carrier: carrier["effects"][0].update(
                permitted_scope="different scope"
            ),
            "PG_PCVP_EFFECT_AUTH_SCOPE_MISMATCH",
        ),
        (
            lambda carrier: carrier["effects"][0].update(
                depends_on_claim_ids=["CLM-MISSING"]
            ),
            "PG_PCVP_EFFECT_CLAIM_REF_UNRESOLVED",
        ),
        (
            lambda carrier: carrier["stage_summary"].update(
                owner_projection="RED"
            ),
            "PG_PCVP_RED_WITH_NON_BLOCKED_EFFECT",
        ),
    ],
)
def test_mechanically_invalid_carriers_fail_closed(
    mutation,
    expected_code: str,
) -> None:
    artifact = _export()
    artifact["continuation_assurance"] = _carrier()
    mutation(artifact["continuation_assurance"])

    result = ProducerGateExportValidator(ROOT, operational=False).validate(
        artifact
    )

    assert result["status"] == "invalid"
    assert expected_code in _codes(result)


def test_pcvp_lock_covers_exact_non_authoritative_schema_bytes() -> None:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))

    assert lock["architecture_lock_id"] == "EV4-PCVP-ROLL-LOCK-20260727-R1"
    assert lock["canonical"] == {
        "repository": "rezahh107/EV4-Decision-Kernel",
        "commit_sha": "069a50fa243b01fa578a7c1bcb8864d9e796d34b",
        "root": "kernel/pcvp/v1.0.0/bundle/04-SCHEMAS",
    }
    assert lock["vendored"]["local_copy_authoritative"] is False
    assert lock["policy"]["adoption_status"] == "not_yet_adopted"
    assert lock["policy"]["activation"] == "NONE"
    assert {
        item["name"]: item["sha256"] for item in lock["files"]
    } == {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(VENDORED_ROOT.glob("*.schema.json"))
    }
