from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TransitionContract:
    service_choice: str
    cli_name: str | None
    lock_path: str | None
    source_stage: str | None
    required_repo_fields: tuple[str, ...]
    optional_repo_fields: tuple[str, ...] = ()
    producer_transition: str | None = None
    producer_required_repo_fields: tuple[str, ...] = ()
    downstream_filename: str | None = None
    receipt_filename: str | None = None


_TRANSITIONS: tuple[TransitionContract, ...] = (
    TransitionContract("validate_bundle", None, None, None, ()),
    TransitionContract("inspect_capabilities", None, None, None, ()),
    TransitionContract(
        "architect_to_ce",
        "architect-to-ce",
        "contracts/locks/architect-to-ce-transition.v1.lock.json",
        "architect",
        ("architect_repo_path", "ce_repo_path"),
        ("project_gate_repo_path",),
        "architect-to-ce",
        ("project_gate_repo_path", "architect_repo_path", "ce_repo_path"),
        "ce-input.json",
        "project-gate-a2c-receipt.json",
    ),
    TransitionContract(
        "ce_to_builder",
        "ce-to-builder",
        "contracts/locks/ce-to-builder-transition.v1.lock.json",
        "ce",
        ("ce_repo_path", "builder_repo_path"),
        ("project_gate_repo_path",),
        "ce-to-builder",
        ("project_gate_repo_path", "ce_repo_path", "builder_repo_path"),
        "builder-input.json",
        "project-gate-c2b-receipt.json",
    ),
    TransitionContract(
        "builder_to_responsive",
        "builder-to-responsive",
        "contracts/locks/builder-to-responsive-transition.v1.lock.json",
        "builder",
        ("builder_repo_path", "responsive_repo_path"),
        ("project_gate_repo_path",),
    ),
    TransitionContract(
        "final_gate",
        "final-evidence-gate",
        "contracts/locks/final-gate.v1.lock.json",
        "responsive",
        ("project_gate_repo_path", "responsive_repo_path", "kernel_repo_path"),
    ),
)

_BY_SERVICE = {item.service_choice: item for item in _TRANSITIONS}
_BY_CLI = {item.cli_name: item for item in _TRANSITIONS if item.cli_name is not None}


def all_service_choices() -> frozenset[str]:
    return frozenset(_BY_SERVICE)


def cli_transition_names() -> tuple[str, ...]:
    return tuple(item.cli_name for item in _TRANSITIONS if item.cli_name is not None)


def contract_for_service(service_choice: str) -> TransitionContract:
    try:
        return _BY_SERVICE[service_choice]
    except KeyError as exc:
        raise ValueError(f"Unknown transition service choice: {service_choice}") from exc


def service_choice_for_cli(cli_name: str) -> str:
    try:
        return _BY_CLI[cli_name].service_choice
    except KeyError as exc:
        raise ValueError(f"Unknown CLI transition name: {cli_name}") from exc


def producer_transition_for_service(service_choice: str) -> str | None:
    return contract_for_service(service_choice).producer_transition


def required_repo_fields(service_choice: str) -> tuple[str, ...]:
    return contract_for_service(service_choice).required_repo_fields


def source_stage_for_service(service_choice: str) -> str | None:
    return contract_for_service(service_choice).source_stage


def lock_path_for_service(service_choice: str) -> str:
    lock_path = contract_for_service(service_choice).lock_path
    if lock_path is None:
        raise ValueError(f"Transition {service_choice} has no lock path")
    return lock_path


def repository_path_matrix() -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "service_choice": item.service_choice,
            "cli_name": item.cli_name,
            "required_repo_fields": item.required_repo_fields,
            "optional_repo_fields": item.optional_repo_fields,
            "producer_transition": item.producer_transition,
            "producer_required_repo_fields": item.producer_required_repo_fields,
            "downstream_filename": item.downstream_filename,
            "receipt_filename": item.receipt_filename,
        }
        for item in _TRANSITIONS
    )
