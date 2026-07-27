from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from ev4_transition.service import GateRequest, RepoPaths, effective_repository_fields
from ev4_transition.service.request_identity import build_gate_request_identity

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "fixtures/producer-emitted/valid/architect-export.v1.json"
ALL_FIELDS = (
    "project_gate_repo_path",
    "architect_repo_path",
    "ce_repo_path",
    "builder_repo_path",
    "responsive_repo_path",
    "kernel_repo_path",
)


@pytest.mark.parametrize(
    "transition,mode,expected",
    [
        ("validate_bundle", "pinned_owner_file_computation", ()),
        ("inspect_capabilities", "pinned_owner_file_computation", ()),
        ("architect_to_ce", "pinned_owner_file_computation", ("architect_repo_path", "ce_repo_path", "project_gate_repo_path")),
        ("architect_to_ce", "producer_emitted_gate_artifact", ("project_gate_repo_path", "architect_repo_path", "ce_repo_path", "kernel_repo_path")),
        ("ce_to_builder", "pinned_owner_file_computation", ("ce_repo_path", "builder_repo_path", "project_gate_repo_path")),
        ("ce_to_builder", "producer_emitted_gate_artifact", ("project_gate_repo_path", "ce_repo_path", "builder_repo_path", "kernel_repo_path")),
        ("builder_to_responsive", "pinned_owner_file_computation", ("builder_repo_path", "responsive_repo_path", "project_gate_repo_path")),
        ("final_gate", "pinned_owner_file_computation", ("project_gate_repo_path", "responsive_repo_path", "kernel_repo_path")),
    ],
)
def test_effective_repository_fields_are_derived_from_contracts(transition: str, mode: str, expected: tuple[str, ...]) -> None:
    assert effective_repository_fields(transition, mode) == expected


def _request(transition: str, mode: str) -> GateRequest:
    repos = RepoPaths(**{field: f"/{field}" for field in ALL_FIELDS})
    if mode == "producer_emitted_gate_artifact":
        return GateRequest(
            transition_choice=transition,  # type: ignore[arg-type]
            acquisition_mode=mode,  # type: ignore[arg-type]
            input_json_path=str(SOURCE),
            repo_paths=repos,
            output_dir="/outputs",
            preflight_mode="external_token",
        )
    return GateRequest(
        transition_choice=transition,  # type: ignore[arg-type]
        acquisition_mode=mode,  # type: ignore[arg-type]
        input_data={"stage": "architect"},
        repo_paths=repos,
        output_dir="/outputs",
        preflight_mode="external_token",
    )


@pytest.mark.parametrize(
    "transition,mode",
    [
        ("architect_to_ce", "pinned_owner_file_computation"),
        ("architect_to_ce", "producer_emitted_gate_artifact"),
        ("ce_to_builder", "pinned_owner_file_computation"),
        ("ce_to_builder", "producer_emitted_gate_artifact"),
        ("builder_to_responsive", "pinned_owner_file_computation"),
        ("final_gate", "pinned_owner_file_computation"),
    ],
)
def test_required_paths_change_fingerprint_and_irrelevant_paths_do_not(transition: str, mode: str) -> None:
    request = _request(transition, mode)
    baseline = build_gate_request_identity(request).fingerprint
    effective = set(effective_repository_fields(transition, mode))

    for field in ALL_FIELDS:
        mutated = replace(
            request,
            repo_paths=replace(request.repo_paths, **{field: f"/changed/{field}"}),
        )
        changed = build_gate_request_identity(mutated).fingerprint
        if field in effective:
            assert changed != baseline, field
        else:
            assert changed == baseline, field


def test_source_bytes_and_effective_contract_inputs_remain_bound(tmp_path: Path) -> None:
    source = tmp_path / "producer.json"
    source.write_bytes(SOURCE.read_bytes())
    request = GateRequest(
        transition_choice="architect_to_ce",
        acquisition_mode="producer_emitted_gate_artifact",
        input_json_path=str(source),
        repo_paths=RepoPaths(
            project_gate_repo_path="/project-gate",
            architect_repo_path="/architect",
            ce_repo_path="/ce",
        ),
        output_dir="/outputs",
        schema_root="schemas",
        lock_path="lock.json",
        timeout_seconds=30,
        require_real_evidence=True,
        preflight_mode="external_token",
    )
    baseline = build_gate_request_identity(request).fingerprint

    source.write_bytes(source.read_bytes() + b"\n")
    assert build_gate_request_identity(request).fingerprint != baseline

    fresh = replace(request, input_json_path=str(SOURCE))
    fresh_baseline = build_gate_request_identity(fresh).fingerprint
    for mutated in (
        replace(fresh, output_dir="/other-output"),
        replace(fresh, schema_root="other-schemas"),
        replace(fresh, lock_path="other-lock.json"),
        replace(fresh, timeout_seconds=31),
        replace(fresh, require_real_evidence=False),
        replace(fresh, acquisition_mode="pinned_owner_file_computation"),
        replace(fresh, transition_choice="ce_to_builder"),
    ):
        assert build_gate_request_identity(mutated).fingerprint != fresh_baseline
