from __future__ import annotations

import copy
import json
import os
import subprocess
import tempfile
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
PROFILE_SCOPE = "discardable provisional handoff; no official validation claim"


def _carrier() -> dict:
    return {
        "policy_id": "EV4-PCVP",
        "policy_version": "1.0.0",
        "source_stage": "ARCHITECT",
        "claims": [{
            "claim_id": "CLM-ARCH-001",
            "statement": "The bounded architecture draft has source evidence.",
            "criticality": "CRITICAL",
            "applicability_state": "APPLICABLE",
            "verification_state": "VERIFIED",
            "lifecycle_state": "ACTIVE",
            "evidence_refs": ["EVD-ARCH-001"],
            "dependency_refs": [],
            "assumption_refs": [],
        }],
        "effects": [{
            "effect_id": "EFF-ARCH-001",
            "effect_class": "DRAFT_ONLY",
            "depends_on_claim_ids": ["CLM-ARCH-001"],
            "continuation_state": "CONTINUE",
            "authorization_ref": "AUTH-ARCH-001",
            "blocker_reason": None,
            "permitted_scope": PROFILE_SCOPE,
        }],
        "authorizations": [{
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
            "permitted_scope": PROFILE_SCOPE,
            "valid_until_events": [
                "NEW_MATERIAL_BLOCKER",
                "OWNER_REVOCATION",
                "SCOPE_EXPANSION",
            ],
        }],
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
            {
                "effect_class": "REASONING_ONLY",
                "scope": "current architecture decision only",
            },
            {"effect_class": "DRAFT_ONLY", "scope": PROFILE_SCOPE},
        ],
        "safe_reversible_default_enabled": True,
        "safe_reversible_default_effect_classes": ["REASONING_ONLY", "DRAFT_ONLY"],
    }


def _profile_diagnostics(carrier: dict, profile: dict | None = None):
    return pcvp._profile_integration_diagnostics(
        profile or _profile(),
        pcvp.PROFILE_BINDINGS["ARCHITECT"],
        {"continuation_assurance": carrier},
        source_stage="ARCHITECT",
        downstream_stage="CONSTRUCTABILITY_ENGINEER",
    )


def _kernel_repo() -> Path:
    value = os.environ.get(KERNEL_ENV)
    if not value:
        pytest.skip(f"{KERNEL_ENV} is required for exact owner integration tests")
    path = Path(value).resolve(strict=True)
    assert subprocess.check_output(
        ["git", "-C", str(path), "rev-parse", "HEAD"], text=True
    ).strip() == pcvp.CANONICAL_COMMIT
    return path


def _disposable_kernel_checkout(tmp_path: Path) -> Path:
    source = _kernel_repo()
    target = tmp_path / "decision-kernel"
    subprocess.run(
        ["git", "clone", "--quiet", "--no-hardlinks", str(source), str(target)],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "-C", str(target), "checkout", "--quiet", "--detach", pcvp.CANONICAL_COMMIT],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            "git", "-C", str(target), "remote", "set-url", "origin",
            f"https://github.com/{pcvp.CANONICAL_REPOSITORY}.git",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return target


def _codes(result: dict) -> set[str]:
    return {item["code"] for item in result["diagnostics"]}


def test_legacy_absence_is_dependency_free_and_lossless(monkeypatch: pytest.MonkeyPatch) -> None:
    artifact = _export()
    before = copy.deepcopy(artifact)
    monkeypatch.setattr(
        owner.shutil, "which", lambda name: pytest.fail(f"unexpected {name}")
    )

    result = ProducerGateExportValidator(ROOT, operational=False).validate(artifact)

    assert result["status"] == "valid", result
    assert result["pcvp_carrier"]["status"] == "legacy_absent"
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


def test_clean_exact_owner_execution_preserves_checkout_and_fixture_parity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    kernel = _kernel_repo()
    artifact = _export(live_registry_pin=True)
    artifact["continuation_assurance"] = _carrier()
    before = copy.deepcopy(artifact)
    head_before = subprocess.check_output(
        ["git", "-C", str(kernel), "rev-parse", "HEAD"], text=True
    ).strip()
    status_before = subprocess.check_output(
        ["git", "-C", str(kernel), "status", "--porcelain=v1", "--untracked-files=all"],
        text=True,
    )
    created: list[Path] = []
    real_temporary_directory = tempfile.TemporaryDirectory

    class RecordingTemporaryDirectory(real_temporary_directory):
        def __enter__(self):
            value = super().__enter__()
            created.append(Path(value))
            return value

    monkeypatch.setattr(owner, "TemporaryDirectory", RecordingTemporaryDirectory)

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
    assert projection["adoption_status"] == "not_yet_adopted"
    assert projection["activation_effect"] == "NONE"
    assert projection["carrier"] == {
        "continuation_assurance": before["continuation_assurance"]
    }
    assert projection["canonical_sha256"] == canonical_sha256(projection["carrier"])
    fixtures = projection["owner_bundle_fixtures"]
    assert fixtures["total"] == 18
    assert fixtures["valid"] == 8
    assert fixtures["invalid"] == 10
    assert fixtures["all_passed_at_declared_layer"] is True
    assert all(item["passed"] is True for item in fixtures["results"])
    assert result["handoff_allowed"] is False
    assert artifact == before
    assert created and all(not path.exists() for path in created)
    assert subprocess.check_output(
        ["git", "-C", str(kernel), "rev-parse", "HEAD"], text=True
    ).strip() == head_before
    assert subprocess.check_output(
        ["git", "-C", str(kernel), "status", "--porcelain=v1", "--untracked-files=all"],
        text=True,
    ) == status_before


@pytest.mark.parametrize("package_name", ["ajv", "yaml"])
def test_caller_node_modules_cannot_influence_clean_owner_execution(
    package_name: str,
    tmp_path: Path,
) -> None:
    kernel = _disposable_kernel_checkout(tmp_path)
    package = kernel / "node_modules" / package_name
    package.mkdir(parents=True)
    (package / "package.json").write_text(
        json.dumps({
            "name": package_name,
            "version": "0.0.0-poison",
            "type": "module",
            "exports": "./index.js",
        }),
        encoding="utf-8",
    )
    (package / "index.js").write_text(
        "throw new Error('caller node_modules was loaded');\n",
        encoding="utf-8",
    )
    artifact = _export(live_registry_pin=True)
    artifact["continuation_assurance"] = _carrier()

    result = intake_producer_export(
        artifact,
        repository_root=ROOT,
        decision_kernel_repo=kernel,
    )

    assert result["status"] == "accepted", result
    assert result["pcvp_carrier"]["status"] == "validated"
    assert package.exists()


def test_npm_ci_failure_is_insufficient_evidence(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    authority = pcvp.OwnerAuthority(
        root=tmp_path,
        validator_path=tmp_path / "pcvp-v1.mjs",
        bundle_root=tmp_path / "bundle",
        profile_path=tmp_path / "profile.yaml",
        profile_binding=pcvp.PROFILE_BINDINGS["ARCHITECT"],
        lock={"authority_files": []},
        initial_file_digests={},
    )
    calls: list[list[str]] = []
    monkeypatch.setattr(owner.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(owner, "_materialize_tracked_tree", lambda *args: [])
    monkeypatch.setattr(owner, "_verify_materialized_files", lambda *args: [])
    monkeypatch.setattr(owner, "_checkout_unchanged_diagnostics", lambda *args: [])

    def fail_npm(args, **kwargs):
        calls.append(list(args))
        return SimpleNamespace(returncode=17, stdout="", stderr="failed")

    monkeypatch.setattr(owner.subprocess, "run", fail_npm)

    response, diagnostics = pcvp._run_owner_bridge(
        authority, {"continuation_assurance": _carrier()}
    )

    assert response is None
    assert diagnostics[0].code == "PG_PCVP_OWNER_EXECUTION_UNAVAILABLE"
    assert diagnostics[0].details["reason"] == "npm_ci_failed"
    assert calls == [[
        "/usr/bin/npm", "ci", "--ignore-scripts", "--no-audit", "--no-fund"
    ]]


def test_profile_exact_class_and_scope_match_is_accepted() -> None:
    codes = {item.code for item in _profile_diagnostics(_carrier())}
    assert "PG_PCVP_PROFILE_SCOPE_NOT_AUTHORIZED" not in codes
    assert "PG_PCVP_PROFILE_PREAUTHORIZATION_AMBIGUOUS" not in codes
    assert "PG_PCVP_PROFILE_PREAUTHORIZATION_REJECTED" not in codes


@pytest.mark.parametrize(
    "scope",
    [
        "all architecture decisions",
        "discardable provisional handoff",
        "discardable provisional architecture handoff; no official validation claim",
    ],
)
def test_profile_nonidentical_scope_is_rejected_without_inference(scope: str) -> None:
    carrier = _carrier()
    carrier["effects"][0]["permitted_scope"] = scope
    carrier["authorizations"][0]["permitted_scope"] = scope

    assert "PG_PCVP_PROFILE_SCOPE_NOT_AUTHORIZED" in {
        item.code for item in _profile_diagnostics(carrier)
    }


def test_profile_duplicate_exact_scope_is_ambiguous() -> None:
    profile = _profile()
    profile["preauthorized_effects"].append(
        {"effect_class": "DRAFT_ONLY", "scope": PROFILE_SCOPE}
    )

    assert "PG_PCVP_PROFILE_PREAUTHORIZATION_AMBIGUOUS" in {
        item.code for item in _profile_diagnostics(_carrier(), profile)
    }


def test_profile_class_safe_default_and_stage_checks_remain_separate() -> None:
    carrier = _carrier()
    carrier["effects"][0]["effect_class"] = "EXTERNAL_MUTATION"
    carrier["authorizations"][0]["allowed_effect_classes"] = ["EXTERNAL_MUTATION"]
    codes = {item.code for item in _profile_diagnostics(carrier)}
    assert "PG_PCVP_PROFILE_PREAUTHORIZATION_REJECTED" in codes
    assert "PG_PCVP_PROFILE_SCOPE_NOT_AUTHORIZED" in codes

    carrier = _carrier()
    carrier["authorizations"][0]["basis"] = "SAFE_REVERSIBLE_DEFAULT"
    carrier["effects"][0]["effect_class"] = "REVERSIBLE_LOCAL_CHANGE"
    carrier["authorizations"][0]["allowed_effect_classes"] = [
        "REVERSIBLE_LOCAL_CHANGE"
    ]
    carrier["authorizations"][0]["stage_scope"] = {
        "from": "BUILDER_ASSISTANT",
        "through": "PROJECT_GATE",
    }
    profile = _profile()
    profile["produces_for"] = ["PROJECT_GATE"]
    codes = {item.code for item in _profile_diagnostics(carrier, profile)}
    assert "PG_PCVP_PROFILE_DOWNSTREAM_NOT_ALLOWED" in codes
    assert "PG_PCVP_PROFILE_SAFE_DEFAULT_REJECTED" in codes
    assert "PG_PCVP_STAGE_SCOPE_FROM_MISMATCH" in codes
    assert "PG_PCVP_STAGE_SCOPE_THROUGH_MISMATCH" in codes


def test_owner_authority_identity_rejects_wrong_commit_and_repository(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    owner_path = tmp_path / "owner"
    owner_path.mkdir()
    monkeypatch.setattr(owner.shutil, "which", lambda name: "/usr/bin/git")
    monkeypatch.setattr(
        owner, "_load_lock", lambda root: ({"authority_files": []}, [])
    )
    monkeypatch.setattr(owner, "_verify_files", lambda root, lock, git: [])
    monkeypatch.setattr(
        owner, "_capture_file_digests", lambda root, lock: ({}, [])
    )
    values = iter((
        str(owner_path),
        "0" * 40,
        "https://github.com/example/wrong.git",
        "",
    ))
    monkeypatch.setattr(owner, "_git", lambda *args: next(values))

    authority, diagnostics = pcvp._verify_owner_authority(
        ROOT, owner_path, "ARCHITECT"
    )

    assert authority is None
    reasons = {item.details.get("reason") for item in diagnostics}
    assert "commit_mismatch" in reasons
    assert "repository_identity_mismatch" in reasons


@pytest.mark.parametrize(
    ("completed", "expected_code"),
    [
        (
            SimpleNamespace(returncode=0, stdout="{", stderr=""),
            "PG_PCVP_OWNER_RESPONSE_INVALID",
        ),
        (
            SimpleNamespace(
                returncode=0,
                stdout='{"schema_version":"ev4-pcvp-owner-bridge-response.v1","status":"OK"} trailing',
                stderr="",
            ),
            "PG_PCVP_OWNER_RESPONSE_INVALID",
        ),
        (
            SimpleNamespace(returncode=0, stdout="{}", stderr="unexpected"),
            "PG_PCVP_OWNER_RESPONSE_INVALID",
        ),
        (
            SimpleNamespace(returncode=9, stdout="", stderr=""),
            "PG_PCVP_OWNER_EXECUTION_UNAVAILABLE",
        ),
        (
            SimpleNamespace(
                returncode=0,
                stdout=json.dumps({
                    "schema_version": "ev4-pcvp-owner-bridge-response.v1",
                    "status": "BRIDGE_ERROR",
                    "error": {
                        "code": "OWNER_EXECUTION_FAILED",
                        "name": "TypeError",
                        "message": "required owner exports unavailable",
                    },
                }),
                stderr="",
            ),
            "PG_PCVP_OWNER_EXECUTION_UNAVAILABLE",
        ),
    ],
)
def test_strict_bridge_failures_are_deterministic(
    completed: SimpleNamespace,
    expected_code: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(owner.subprocess, "run", lambda *args, **kwargs: completed)

    response, diagnostics = owner._execute_bridge(
        "/usr/bin/node",
        tmp_path,
        tmp_path / "validator.mjs",
        tmp_path / "bundle",
        {"continuation_assurance": _carrier()},
        {},
    )

    assert response is None
    assert diagnostics[0].code == expected_code


def test_execution_lock_and_no_parallel_authority_invariants() -> None:
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
    assert {
        item["path"] for item in lock["authority_files"]
    } == pcvp._expected_authority_paths()
    source = (ROOT / "src/ev4_transition/pcvp_carrier.py").read_text(
        encoding="utf-8"
    )
    owner_source = (ROOT / "src/ev4_transition/pcvp_owner.py").read_text(
        encoding="utf-8"
    )
    assert "Draft202012Validator" not in source
    assert "_cross_record_diagnostics" not in source
    assert "_projection_diagnostics" not in source
    assert "npm" in owner_source
    assert "TemporaryDirectory" in owner_source
    assert not (
        ROOT / "contracts/vendor/decision-kernel/pcvp/v1.0.0"
    ).exists()
