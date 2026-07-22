from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ev4_transition.producer_integration.path_environment import (
    validate_project_gate_root,
    validate_publication_root,
    validate_repository_checkout,
)

from .models import GateRequest, RepoPaths
from .preflight_core import PreflightCheck, PreflightResult
from .producer_handoff import inspect_producer_handoff_request
from .transition_contracts import contract_for_service, lock_path_for_service, producer_transition_for_service

_ROUTING_FILES = (
    "contracts/producer-adoption/ev4-producer-adoption-set.v1.json",
    "contracts/transition-targets/ev4-transition-targets.v1.json",
    "docs/evidence/JOIN_EVIDENCE_PACKET_v1.json",
)
_LABEL = {
    "project_gate_repo_path": "مسیر Project Gate repo",
    "architect_repo_path": "مسیر Architect repo",
    "ce_repo_path": "مسیر CE repo",
    "builder_repo_path": "مسیر Builder repo",
    "responsive_repo_path": "مسیر Responsive repo",
    "kernel_repo_path": "مسیر Kernel repo",
    "output_dir": "مسیر خروجی",
}


def validate_gate_request_environment(request: GateRequest) -> PreflightResult:
    """Validate producer-mode environment without creating directories or executing a handoff."""

    choice = str(request.transition_choice)
    expected_transition = producer_transition_for_service(choice)
    checks: list[PreflightCheck] = []
    if expected_transition is None:
        return _result(
            choice,
            [
                PreflightCheck(
                    "producer.transition.unsupported",
                    "نوع transition",
                    "error",
                    "حالت producer-emitted برای transition انتخاب‌شده پشتیبانی نمی‌شود.",
                    f"transition_choice={choice}",
                    "transition سازگار را انتخاب کن.",
                    "unsupported_transition",
                )
            ],
        )

    repos = request.repo_paths or RepoPaths()
    required_project_gate_files = _ROUTING_FILES + (lock_path_for_service(choice),)
    project_gate_root, project_gate_diags = validate_project_gate_root(
        repos.project_gate_repo_path,
        required_files=required_project_gate_files,
    )
    checks.extend(_path_checks("project_gate_repo_path", project_gate_diags, project_gate_root))

    contract = contract_for_service(choice)
    for field in contract.producer_required_repo_fields:
        if field == "project_gate_repo_path":
            continue
        path, diagnostics = validate_repository_checkout(field, getattr(repos, field))
        checks.extend(_path_checks(field, diagnostics, path))

    output_root, output_diagnostic = validate_publication_root(request.output_dir, create=False)
    checks.extend(_path_checks("output_dir", [output_diagnostic] if output_diagnostic else [], output_root))

    if request.input_json_text is not None or request.input_data is not None or not request.input_json_path:
        checks.append(
            PreflightCheck(
                "producer.source.file_required",
                "فایل Producer Gate Export",
                "error",
                "در حالت producer-emitted فقط فایل اصلی JSON قابل استفاده است.",
                "input_json_path is required; pasted JSON is not accepted",
                "فایل اصلی producer-gate-export.v1 را بارگذاری کن.",
                "missing",
            )
        )
    elif project_gate_root is not None:
        inspected = inspect_producer_handoff_request(
            request.input_json_path,
            project_gate_repo_path=str(project_gate_root),
        )
        if inspected.status == "accepted" and inspected.resolved_transition == expected_transition:
            checks.append(
                PreflightCheck(
                    "producer.source.route_ok",
                    "مسیر Producer Gate Export",
                    "ok",
                    "فایل producer و transition انتخاب‌شده با هم سازگارند.",
                    f"resolved_transition={inspected.resolved_transition}",
                    classification="ok",
                )
            )
        else:
            item = inspected.diagnostics[0] if inspected.diagnostics else {}
            checks.append(
                PreflightCheck(
                    "producer.source.route_invalid",
                    "مسیر Producer Gate Export",
                    "error",
                    str(item.get("message") or "فایل producer برای transition انتخاب‌شده معتبر نیست."),
                    f"code={item.get('code', 'PG_INT_ROUTE_INVALID')}; resolved_transition={inspected.resolved_transition}",
                    "فایل، Project Gate checkout و transition انتخاب‌شده را بررسی کن.",
                    "wrong_input_type",
                )
            )

    checks.append(
        PreflightCheck(
            "scope.runtime_revalidation",
            "محدوده Preflight",
            "ok",
            "Preflight هیچ پوشه یا فایلی ایجاد نمی‌کند؛ Runtime همین قواعد را دوباره اجرا می‌کند.",
            "side_effects=none; runtime_revalidation=required",
            classification="ok",
        )
    )
    return _result(choice, checks)


def _path_checks(field: str, diagnostics: list[dict[str, Any]], path: Path | None) -> list[PreflightCheck]:
    label = _LABEL.get(field, field)
    if diagnostics:
        item = diagnostics[0]
        details = item.get("details") if isinstance(item.get("details"), dict) else {}
        return [
            PreflightCheck(
                f"environment.{field}.{item.get('code', 'invalid')}",
                label,
                "error",
                str(item.get("message", "مسیر معتبر نیست.")),
                json.dumps(details, ensure_ascii=False, sort_keys=True),
                "مسیر local معتبر و قابل استفاده را انتخاب کن.",
                "invalid_path",
            )
        ]
    return [
        PreflightCheck(
            f"environment.{field}.ok",
            label,
            "ok",
            "مسیر برای Preflight قابل استفاده است.",
            str(path) if path is not None else "",
            classification="ok",
        )
    ]


def _result(choice: str, checks: list[PreflightCheck]) -> PreflightResult:
    if any(check.status == "error" for check in checks):
        status = "blocked"
        summary = "Preflight مسدود است؛ اولین diagnostic خطادار را اصلاح کن."
    elif any(check.status == "warning" for check in checks):
        status = "warnings"
        summary = "Preflight با هشدار کامل شد."
    else:
        status = "ready"
        summary = "Preflight آماده است؛ Runtime مسیرها را دوباره اعتبارسنجی می‌کند."
    return PreflightResult(status, choice, checks, summary)
