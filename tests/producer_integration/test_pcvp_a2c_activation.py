from __future__ import annotations

import copy
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Callable

import pytest

from ev4_transition.canonical_json import canonical_sha256
from ev4_transition.producer_integration import a2c_dispatch, intake_runtime
from ev4_transition.runners import pcvp_activation

ROOT = Path(__file__).resolve().parents[2]
CARRIER = {
    "pcvp_version": "1.0.0",
    "policy_id": "EV4-PCVP",
    "claims": [],
    "effects": [],
    "authorizations": [],
}


def _accepted_outcome(owner: str, commit: str, validator: str):
    record = SimpleNamespace(
        owner_repo=owner,
        owner_commit=commit,
        validator_path=validator,
        exit_code=0,
        timeout_policy=SimpleNamespace(seconds=30),
        to_dict=lambda: {
            "owner_repo": owner,
            "owner_commit": commit,
            "validator_path": validator,
            "exit_code": 0,
        },
    )
    return SimpleNamespace(
        status="accepted",
        diagnostics=[],
        execution_record=record,
        stdout_hash="1" * 64,
        stderr_hash="2" * 64,
    )


def _validated_intake(carrier: dict | None) -> dict:
    result = {"status": "accepted", "diagnostics": []}
    if carrier is not None:
        document = {"continuation_assurance": copy.deepcopy(carrier)}
        result["pcvp_carrier"] = {
            "status": "validated",
            "carrier": document,
            "canonical_sha256": canonical_sha256(document),
        }
    return result


def _configure_transition(monkeypatch: pytest.MonkeyPatch, order: list[str]) -> None:
    monkeypatch.setattr(
        a2c_dispatch,
        "inspect_checkout",
        lambda *_args, expected_repository=None, expected_commit=None, **_kwargs: {
            "status": "accepted",
            "repository": expected_repository,
            "commit": expected_commit or "project-gate-head",
            "diagnostics": [],
        },
    )

    def architect(*_args, **_kwargs):
        order.append("architect")
        return _accepted_outcome(
            a2c_dispatch.ARCHITECT_REPO,
            a2c_dispatch.ARCHITECT_COMMIT,
            "architect-validator",
        )

    def ce(_repo, payload, _source_bundle):
        order.append("ce")
        if "continuation_assurance" in payload:
            assert payload["continuation_assurance"] == CARRIER
        return _accepted_outcome(
            a2c_dispatch.CE_REPO,
            a2c_dispatch.CE_COMMIT,
            "ce-validator",
        )

    monkeypatch.setattr(a2c_dispatch, "execute_architect_validator", architect)
    monkeypatch.setattr(a2c_dispatch, "execute_ce_validator", ce)

    def transition(source, *_args, validator_hooks, **_kwargs):
        validator_hooks.architect(source)
        payload = {
            "schema_id": "ev4-ce-architect-stage-intake@1.1.0",
            "intake_status": "complete",
        }
        diagnostics = validator_hooks.ce(payload, source)
        return {
            "status": "invalid" if diagnostics else "accepted",
            "diagnostics": [item.to_dict() for item in diagnostics],
            "output": {"payload": {"data": payload}},
        }

    monkeypatch.setattr(a2c_dispatch, "transition_from_local_paths", transition)


def _call(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    carrier: dict | None,
    intake_carrier: dict | None = None,
    handoff_allowed: bool = False,
    transition_impl: Callable[..., dict] | None = None,
):
    order: list[str] = []
    _configure_transition(monkeypatch, order)
    if transition_impl is not None:
        monkeypatch.setattr(
            a2c_dispatch,
            "transition_from_local_paths",
            transition_impl,
        )
    source = tmp_path / "architect-project-gate.json"
    source.write_text("{}", encoding="utf-8")
    artifact = {
        "final_stage_bundle": {"bundle_id": "A2C-PCVP-1"},
        "handoff": {"allowed": handoff_allowed},
    }
    if carrier is not None:
        artifact["continuation_assurance"] = copy.deepcopy(carrier)
    intake = _validated_intake(carrier if intake_carrier is None else intake_carrier)
    result = a2c_dispatch.dispatch_architect_export(
        artifact,
        intake,
        snapshot=SimpleNamespace(
            path=source,
            sha256_file_bytes="0" * 64,
        ),
        schema_root=tmp_path / "schemas",
        lock_path=tmp_path / "lock.json",
        architect_repo=tmp_path / "architect",
        ce_repo=tmp_path / "ce",
        project_gate_repo=tmp_path / "project-gate",
        output_path=tmp_path / "ce-input.json",
        receipt_path=tmp_path / "project-gate-a2c-receipt.json",
        decision_kernel_repo=tmp_path / "decision-kernel",
    )
    return result, order


def _accepted_activation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        a2c_dispatch,
        "validate_first_edge_activation",
        lambda *_args, **_kwargs: ({
            "status": "validated",
            "activation_commit": pcvp_activation.ACTIVATION_COMMIT,
            "activation_id": pcvp_activation.ACTIVATION_ID,
            "enabled_edge": pcvp_activation.ACTIVATION_EDGE,
        }, []),
    )


def test_legacy_absence_does_not_load_activation_dependency(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        a2c_dispatch,
        "validate_first_edge_activation",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("legacy absence must not load staged activation")
        ),
    )

    result, order = _call(tmp_path, monkeypatch, carrier=None)

    assert result["status"] == "insufficient_evidence"
    assert result["publication_allowed"] is False
    assert "continuation_assurance" not in result["transition_result"]["output"]["payload"]["data"]
    assert order == ["architect", "ce"]


def test_active_carrier_is_attached_before_ce_validator_and_handoff_remains_blocked(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _accepted_activation(monkeypatch)

    result, order = _call(tmp_path, monkeypatch, carrier=CARRIER)

    ce_input = result["transition_result"]["output"]["payload"]["data"]
    assert ce_input["continuation_assurance"] == CARRIER
    assert canonical_sha256({"continuation_assurance": ce_input["continuation_assurance"]}) == canonical_sha256({"continuation_assurance": CARRIER})
    assert "PG_A2C_PCVP_CARRIER_MUTATED" not in {
        item["code"] for item in result["diagnostics"]
    }
    assert result["pcvp_activation"]["enabled_edge"] == pcvp_activation.ACTIVATION_EDGE
    assert result["handoff_allowed"] is False
    assert result["publication_allowed"] is False
    assert order == ["architect", "ce"]


def test_prior_transition_failure_does_not_claim_carrier_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _accepted_activation(monkeypatch)

    def failed_transition(source, *_args, validator_hooks, **_kwargs):
        validator_hooks.architect(source)
        return {
            "status": "invalid",
            "diagnostics": [{
                "code": "A2C_PRIMARY_SCHEMA_FAILURE",
                "severity": "error",
                "path": "$.architect_intent",
                "message": "primary transition failure",
                "details": {},
                "repair_owner": "Architect",
            }],
            "output": None,
        }

    result, order = _call(
        tmp_path,
        monkeypatch,
        carrier=CARRIER,
        transition_impl=failed_transition,
    )

    codes = [item["code"] for item in result["diagnostics"]]
    assert result["status"] == "invalid"
    assert codes == ["A2C_PRIMARY_SCHEMA_FAILURE"]
    assert "PG_A2C_PCVP_CARRIER_MUTATED" not in codes
    assert result["transition_result"]["output"] is None
    assert order == ["architect"]


@pytest.mark.parametrize("mutation", ["omit", "change"])
def test_produced_target_carrier_mutation_reports_both_hashes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    _accepted_activation(monkeypatch)

    def mutated_target_transition(source, *_args, validator_hooks, **_kwargs):
        validator_hooks.architect(source)
        payload = {
            "schema_id": "ev4-ce-architect-stage-intake@1.1.0",
            "intake_status": "complete",
        }
        assert validator_hooks.ce(payload, source) == []
        if mutation == "omit":
            payload.pop("continuation_assurance")
        else:
            payload["continuation_assurance"] = {
                **payload["continuation_assurance"],
                "claims": [{"claim_id": "mutated"}],
            }
        return {
            "status": "accepted",
            "diagnostics": [],
            "output": {"payload": {"data": payload}},
        }

    result, order = _call(
        tmp_path,
        monkeypatch,
        carrier=CARRIER,
        transition_impl=mutated_target_transition,
    )

    mutation_diagnostics = [
        item
        for item in result["diagnostics"]
        if item["code"] == "PG_A2C_PCVP_CARRIER_MUTATED"
    ]
    assert result["status"] == "invalid"
    assert len(mutation_diagnostics) == 1
    details = mutation_diagnostics[0]["details"]
    assert details["expected_canonical_sha256"] == canonical_sha256(
        {"continuation_assurance": CARRIER}
    )
    assert details["actual_canonical_sha256"] == canonical_sha256({
        "continuation_assurance": (
            None
            if mutation == "omit"
            else {
                **CARRIER,
                "claims": [{"claim_id": "mutated"}],
            }
        )
    })
    assert order == ["architect", "ce"]


def test_activation_rejection_stops_before_mapping(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        a2c_dispatch,
        "validate_first_edge_activation",
        lambda *_args, **_kwargs: (None, [{
            "code": "PG_PCVP_ACTIVATION_REJECTED",
            "severity": "error",
            "path": "$.continuation_assurance",
            "message": "rejected",
            "details": {},
            "repair_owner": "Project Gate",
        }]),
    )
    monkeypatch.setattr(
        a2c_dispatch,
        "transition_from_local_paths",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("unauthorized activation must not map")
        ),
    )

    result, _ = _call(tmp_path, monkeypatch, carrier=CARRIER)

    assert result["status"] == "invalid"
    assert result["publication_allowed"] is False
    assert result["transition_result"] is None


def test_carrier_mutation_after_intake_is_rejected_before_activation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    validated = copy.deepcopy(CARRIER)
    validated["claims"] = [{"claim_id": "validated"}]
    monkeypatch.setattr(
        a2c_dispatch,
        "validate_first_edge_activation",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("mutated carrier must fail before activation")
        ),
    )

    result, _ = _call(
        tmp_path,
        monkeypatch,
        carrier=CARRIER,
        intake_carrier=validated,
    )

    assert result["status"] == "invalid"
    assert {item["code"] for item in result["diagnostics"]} == {"PG_A2C_PCVP_CARRIER_MUTATED"}
    assert result["publication_allowed"] is False


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("activation_id", "EV4-PCVP-ACT-WRONG"),
        ("enabled_edges", ["CE_TO_BUILDER"]),
        ("disabled_edges", ["BUILDER_TO_RESPONSIVE", "RESPONSIVE_TO_FINAL"]),
        ("official_adoption_authorization", False),
        ("full_rollout_authorized", True),
    ],
)
def test_activation_response_mutations_fail_closed(field: str, value: object) -> None:
    response = {
        "result": "PASS",
        "activation_id": pcvp_activation.ACTIVATION_ID,
        "official_adoption_authorization": True,
        "enabled_edges": [pcvp_activation.ACTIVATION_EDGE],
        "disabled_edges": list(pcvp_activation.DISABLED_EDGES),
        "full_rollout_authorized": False,
        "remote_prerequisites_verified": False,
    }
    response[field] = value

    diagnostics = pcvp_activation._validate_official_response(response)

    assert diagnostics
    assert diagnostics[0]["code"] == "PG_PCVP_ACTIVATION_REJECTED"


def test_policy_activation_and_a2c_identities_are_distinct_and_exact() -> None:
    pcvp_lock = json.loads((ROOT / "contracts/locks/pcvp-v1.lock.json").read_text(encoding="utf-8"))
    a2c_lock = json.loads((ROOT / "contracts/locks/architect-to-ce-transition.v1.lock.json").read_text(encoding="utf-8"))

    assert pcvp_lock["owner"]["commit_sha"] == "069a50fa243b01fa578a7c1bcb8864d9e796d34b"
    assert pcvp_lock["activation_authority"]["commit_sha"] == pcvp_activation.ACTIVATION_COMMIT
    assert pcvp_lock["owner"]["commit_sha"] != pcvp_lock["activation_authority"]["commit_sha"]
    architect_commits = {
        item["accepted_commit"]
        for item in a2c_lock["files"]
        if item["repository"] == a2c_dispatch.ARCHITECT_REPO
    }
    ce_commits = {
        item["accepted_commit"]
        for item in a2c_lock["files"]
        if item["repository"] == a2c_dispatch.CE_REPO
    }
    assert architect_commits == {"bd7cb512f9b61222cee2512fbfc53a2bb01a1175"}
    assert ce_commits == {"bc4a901d82fcdbdb131e30058b399508262706c5"}


def test_operational_revalidation_preserves_exact_a2c_pcvp_context(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class FakeOperationalValidator:
        def __init__(
            self,
            project_gate_root: str | Path,
            artifact_root: str | Path,
            **kwargs: object,
        ) -> None:
            captured["project_gate_root"] = project_gate_root
            captured["artifact_root"] = artifact_root
            captured.update(kwargs)

        def validate(self, artifact: object) -> dict[str, object]:
            captured["artifact"] = artifact
            return {"status": "valid", "diagnostics": []}

    monkeypatch.setattr(
        intake_runtime,
        "OperationalProducerGateExportValidator",
        FakeOperationalValidator,
    )
    artifact = {"continuation_assurance": copy.deepcopy(CARRIER)}
    kernel = tmp_path / "decision-kernel"

    failure = intake_runtime._operational_truth_failure(
        {"status": "accepted"},
        artifact,
        project_gate_root=tmp_path / "project-gate",
        artifact_root=tmp_path / "architect",
        decision_kernel_repo=kernel,
        downstream_stage="CONSTRUCTABILITY_ENGINEER",
    )

    assert failure is None
    assert captured["decision_kernel_repo"] == kernel
    assert captured["downstream_stage"] == "CONSTRUCTABILITY_ENGINEER"
    assert captured["artifact"] == artifact
