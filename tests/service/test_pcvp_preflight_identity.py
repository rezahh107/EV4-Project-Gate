from __future__ import annotations

import json
import os
import subprocess
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

import ev4_transition.pcvp_owner as owner
import ev4_transition.producer_integration.facade as producer_facade
import ev4_transition.service.dispatcher as dispatcher
import ev4_transition.service.environment_preflight as environment_preflight
from ev4_transition.producer_integration.intake import intake_producer_export
from ev4_transition.service import GateRequest, RepoPaths, run_gate_request, run_preflight
from ev4_transition.service.request_identity import build_gate_request_identity
from ev4_transition.service.transition_contracts import (
    contract_for_service,
    effective_repository_fields,
)

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "fixtures/producer-emitted/valid/architect-export.v1.json"
KERNEL_ENV = "EV4_PCVP_KERNEL_REPO"
CANONICAL_COMMIT = "069a50fa243b01fa578a7c1bcb8864d9e796d34b"
PROFILE_SCOPE = "discardable provisional handoff; no official validation claim"


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
                "permitted_scope": PROFILE_SCOPE,
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
                "permitted_scope": PROFILE_SCOPE,
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


def _write_export(tmp_path: Path, *, with_carrier: bool) -> Path:
    artifact = json.loads(SOURCE.read_text(encoding="utf-8"))
    if with_carrier:
        artifact["continuation_assurance"] = _carrier()
    path = tmp_path / "architect-export.json"
    path.write_text(
        json.dumps(artifact, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    return path


def _request(
    tmp_path: Path,
    *,
    kernel_repo_path: str | None,
    with_carrier: bool,
    preflight_mode: str = "external_token",
) -> GateRequest:
    architect = tmp_path / "architect"
    ce = tmp_path / "ce"
    architect.mkdir(exist_ok=True)
    ce.mkdir(exist_ok=True)
    return GateRequest(
        transition_choice="architect_to_ce",
        acquisition_mode="producer_emitted_gate_artifact",
        input_json_path=str(_write_export(tmp_path, with_carrier=with_carrier)),
        repo_paths=RepoPaths(
            project_gate_repo_path=str(ROOT),
            architect_repo_path=str(architect),
            ce_repo_path=str(ce),
            kernel_repo_path=kernel_repo_path,
        ),
        output_dir=str(tmp_path / "outputs"),
        preflight_mode=preflight_mode,  # type: ignore[arg-type]
    )


def _kernel_repo() -> Path:
    raw = os.environ.get(KERNEL_ENV)
    if not raw:
        pytest.skip(f"{KERNEL_ENV} is required for exact owner lifecycle tests")
    path = Path(raw).resolve(strict=True)
    assert subprocess.check_output(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        text=True,
    ).strip() == CANONICAL_COMMIT
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
        ["git", "-C", str(target), "checkout", "--quiet", "--detach", CANONICAL_COMMIT],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(target),
            "remote",
            "set-url",
            "origin",
            "https://github.com/rezahh107/EV4-Decision-Kernel.git",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return target


def _route_invalid_codes(result) -> set[str]:
    return {
        check.technical_detail.removeprefix("code=").split(";", 1)[0]
        for check in result.checks
        if check.id == "producer.source.route_invalid"
    }


def test_producer_kernel_path_is_declared_once_in_transition_contract() -> None:
    expected = {
        "architect_to_ce": (
            "project_gate_repo_path",
            "architect_repo_path",
            "ce_repo_path",
            "kernel_repo_path",
        ),
        "ce_to_builder": (
            "project_gate_repo_path",
            "ce_repo_path",
            "builder_repo_path",
            "kernel_repo_path",
        ),
    }
    for transition, fields in expected.items():
        contract = contract_for_service(transition)
        assert contract.producer_optional_repo_fields == ("kernel_repo_path",)
        assert effective_repository_fields(
            transition,
            "producer_emitted_gate_artifact",
        ) == fields


def test_environment_preflight_forwards_operator_kernel_path(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    observed: dict[str, str | None] = {}

    def inspect(*args, **kwargs):
        observed["kernel"] = kwargs.get("decision_kernel_repo_path")
        return SimpleNamespace(
            status="accepted",
            resolved_transition="architect-to-ce",
            diagnostics=[],
        )

    monkeypatch.setattr(environment_preflight, "inspect_producer_handoff_request", inspect)
    request = _request(
        tmp_path,
        kernel_repo_path="/operator/decision-kernel",
        with_carrier=False,
    )

    result = environment_preflight.validate_gate_request_environment(request)

    assert result.status == "ready"
    assert observed == {"kernel": "/operator/decision-kernel"}


def test_present_carrier_without_kernel_checkout_fails_closed(tmp_path: Path) -> None:
    result = run_preflight(
        _request(tmp_path, kernel_repo_path=None, with_carrier=True)
    )

    assert result.status == "blocked"
    assert result.request_fingerprint is None
    assert "PG_PCVP_OWNER_AUTHORITY_UNVERIFIED" in _route_invalid_codes(result)


def test_legacy_absence_public_preflight_is_dependency_free(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def forbidden(*args, **kwargs):
        pytest.fail("legacy carrier absence must not execute Git, Node, npm, or owner subprocesses")

    monkeypatch.setattr(owner.shutil, "which", forbidden)
    monkeypatch.setattr(owner.subprocess, "run", forbidden)

    result = run_preflight(
        _request(tmp_path, kernel_repo_path=None, with_carrier=False)
    )

    assert result.status == "ready"
    assert result.request_fingerprint
    assert not _route_invalid_codes(result)


def test_kernel_path_changes_request_fingerprint(tmp_path: Path) -> None:
    request = _request(
        tmp_path,
        kernel_repo_path="/operator/kernel-a",
        with_carrier=False,
    )
    changed = replace(
        request,
        repo_paths=replace(
            request.repo_paths,
            kernel_repo_path="/operator/kernel-b",
        ),
    )

    first = build_gate_request_identity(request)
    second = build_gate_request_identity(changed)

    assert first.fingerprint != second.fingerprint
    assert first.payload["repository_paths"]["kernel_repo_path"].endswith("kernel-a")
    assert second.payload["repository_paths"]["kernel_repo_path"].endswith("kernel-b")


def test_kernel_path_substitution_rejects_preflight_fingerprint(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    request = _request(
        tmp_path,
        kernel_repo_path="/operator/kernel-a",
        with_carrier=False,
    )
    preflight = run_preflight(request)
    assert preflight.status == "ready"
    called = {"dispatch": False}

    def forbidden_dispatch(*args, **kwargs):
        called["dispatch"] = True
        raise AssertionError("dispatch must not run for a stale fingerprint")

    monkeypatch.setattr(dispatcher, "run_producer_handoff_request", forbidden_dispatch)
    mutated = replace(
        request,
        repo_paths=replace(
            request.repo_paths,
            kernel_repo_path="/operator/kernel-b",
        ),
        preflight_fingerprint=preflight.request_fingerprint,
    )

    response = run_gate_request(mutated)

    assert response.status == "invalid"
    assert response.service_diagnostics[0]["code"] == "PG.SERVICE.PREFLIGHT_FINGERPRINT_STALE"
    assert called["dispatch"] is False


def test_public_preflight_accepts_present_carrier_with_exact_owner(
    tmp_path: Path,
) -> None:
    kernel = _kernel_repo()
    result = run_preflight(
        _request(tmp_path, kernel_repo_path=str(kernel), with_carrier=True)
    )

    assert result.status == "ready", result
    assert result.request_fingerprint
    assert not _route_invalid_codes(result)


def test_public_run_gate_request_reuses_exact_owner_path(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    kernel = _kernel_repo()
    request = _request(
        tmp_path,
        kernel_repo_path=str(kernel),
        with_carrier=True,
    )
    observed: dict[str, list[str | None]] = {"preflight": [], "runtime": []}
    real_inspect = environment_preflight.inspect_producer_handoff_request

    def capture_preflight(*args, **kwargs):
        observed["preflight"].append(kwargs.get("decision_kernel_repo_path"))
        return real_inspect(*args, **kwargs)

    def validated_but_dormant_transition(name, artifact, **kwargs):
        observed["runtime"].append(kwargs.get("decision_kernel_repo"))
        result = intake_producer_export(
            artifact,
            registry_path=kwargs["registry_path"],
            targets_path=kwargs["targets_path"],
            repository_root=kwargs["repository_root"],
            decision_kernel_repo=kwargs.get("decision_kernel_repo"),
        )
        assert result["pcvp_carrier"]["status"] == "validated", result
        result["resolved_transition"] = name
        result["handoff_allowed"] = False
        return result

    monkeypatch.setattr(environment_preflight, "inspect_producer_handoff_request", capture_preflight)
    monkeypatch.setattr(producer_facade, "transition_producer_export", validated_but_dormant_transition)

    preflight = run_preflight(request)
    assert preflight.status == "ready", preflight
    response = run_gate_request(
        replace(request, preflight_fingerprint=preflight.request_fingerprint)
    )

    assert response.status == "accepted", response.to_dict()
    assert response.engine_result is not None
    assert response.engine_result["pcvp_carrier"]["status"] == "validated"
    assert response.engine_result["handoff_allowed"] is False
    assert observed["preflight"] and set(observed["preflight"]) == {str(kernel)}
    assert observed["runtime"] == [str(kernel)]
    assert all(
        item["code"] != "producer.source.route_invalid"
        for item in response.service_diagnostics
    )


@pytest.mark.parametrize("variant", ["wrong_repository", "wrong_commit", "drifted_authority_file"])
def test_public_preflight_rejects_exact_owner_authority_variants(
    tmp_path: Path,
    variant: str,
) -> None:
    kernel = _disposable_kernel_checkout(tmp_path)
    if variant == "wrong_repository":
        subprocess.run(
            [
                "git",
                "-C",
                str(kernel),
                "remote",
                "set-url",
                "origin",
                "https://github.com/example/not-decision-kernel.git",
            ],
            check=True,
        )
    elif variant == "wrong_commit":
        subprocess.run(
            ["git", "-C", str(kernel), "checkout", "--quiet", "--detach", f"{CANONICAL_COMMIT}^"],
            check=True,
        )
    else:
        validator = kernel / "kernel/validator/pcvp-v1.mjs"
        validator.write_text(
            validator.read_text(encoding="utf-8") + "\n// drift\n",
            encoding="utf-8",
        )

    result = run_preflight(
        _request(tmp_path, kernel_repo_path=str(kernel), with_carrier=True)
    )

    assert result.status == "blocked"
    assert "PG_PCVP_OWNER_AUTHORITY_UNVERIFIED" in _route_invalid_codes(result)
