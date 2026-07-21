from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from ev4_transition.service.json_input import parse_json_input
from ev4_transition.service.producer_handoff import inspect_producer_handoff_request

_RESULT_SCHEMAS = {"ev4-project-gate-ui-result.v1", "project-gate-service-result.v1"}


def classify_source_file(source_path: str | None, project_gate_repo_path: str | None = None) -> dict[str, Any]:
    if not source_path:
        return _result("idle", None, None, None, "فایل JSON را انتخاب کنید.")
    parsed = parse_json_input(input_json_path=source_path)
    if parsed.diagnostics:
        return {
            **_result("invalid", None, None, None, "فایل JSON قابل خواندن یا معتبر نیست."),
            "diagnostics": [item.to_dict() for item in parsed.diagnostics],
        }
    if not isinstance(parsed.value, dict):
        return _result("invalid", None, None, None, "ریشه فایل JSON باید object باشد.")

    value = deepcopy(parsed.value)
    schema = value.get("schema_version")
    if schema in _RESULT_SCHEMAS or _looks_like_result(value):
        return {
            **_result("invalid", str(schema), None, None, "فایل result/report منبع transition نیست."),
            "diagnostics": [_diag("PG.UI.RESULT_ARTIFACT_USED_AS_SOURCE", "Project Gate result/report artifact cannot be used as a transition source.")],
        }
    if schema == "producer-gate-export.v1":
        inspection = inspect_producer_handoff_request(
            source_path,
            project_gate_repo_path=(project_gate_repo_path or ".").strip() or ".",
        ).to_dict()
        resolved = inspection.get("resolved_transition")
        if inspection.get("status") == "accepted" and resolved == "architect-to-ce":
            return {
                **_result(
                    "source_classified",
                    schema,
                    "Architect → CE",
                    "producer_emitted_gate_artifact",
                    "Producer Gate Export شناسایی شد. مسیر Architect → CE و روش دریافت producer_emitted_gate_artifact انتخاب شد.",
                ),
                "producer_stage": _nested(inspection, "routing", "producer_stage"),
                "handoff_target": _nested(inspection, "routing", "target_stage"),
                "inspection": inspection,
            }
        return {
            **_result("invalid", schema, None, "producer_emitted_gate_artifact", "Producer Gate Export شناسایی شد، اما مسیر آن برای اجرای انتخابی قابل قبول نیست."),
            "inspection": inspection,
            "diagnostics": list(inspection.get("diagnostics") or []),
        }
    if schema == "stage-evidence-bundle.v1":
        return _result(
            "source_classified",
            schema,
            "Validate Stage Evidence Bundle",
            "pinned_owner_file_computation",
            "Stage Evidence Bundle شناسایی شد؛ فقط مسیر اعتبارسنجی مستقیم انتخاب شد.",
        )
    return {
        **_result("invalid", str(schema) if schema is not None else None, None, None, "نوع artifact پشتیبانی‌شده تشخیص داده نشد."),
        "diagnostics": [_diag("PG.UI.SOURCE_SCHEMA_MODE_MISMATCH", "Unsupported or missing source schema identity.")],
    }


def _looks_like_result(value: dict[str, Any]) -> bool:
    return "engine_result" in value and "transition_choice" in value and "diagnostics" in value


def _nested(value: dict[str, Any], first: str, second: str) -> Any:
    item = value.get(first)
    return item.get(second) if isinstance(item, dict) else None


def _diag(code: str, message: str) -> dict[str, Any]:
    return {"code": code, "severity": "error", "path": "$", "message": message}


def _result(status: str, schema: str | None, transition: str | None, mode: str | None, message_fa: str) -> dict[str, Any]:
    return {
        "status": status,
        "source_filename": None,
        "source_schema": schema,
        "selected_transition": transition,
        "selected_acquisition_mode": mode,
        "message_fa": message_fa,
        "diagnostics": [],
    }
