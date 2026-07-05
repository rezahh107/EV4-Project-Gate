from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import json
from pathlib import Path
import tempfile
from typing import Any

from ev4_transition.architect_to_ce import TransitionValidatorHooks, transition_from_local_paths
from ev4_transition.bundle_validator import BundleValidator, ResultValidationError
from ev4_transition.canonical_json import canonical_dumps, load_json_file
from ev4_transition.reports import render_json_result, render_markdown_report, render_optional_html_report
from ev4_transition.validator_runner import run_architect_validator, run_ce_validator

from .components import capability_rows_from_payload, diagnostics_to_rows, status_summary_markdown
from .state import option_for_label


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CAPABILITY_STATUS_PATH = PACKAGE_ROOT / "data" / "capability-status.v1.json"


@dataclass(frozen=True)
class UiRunOutput:
    result: dict[str, Any]
    status_markdown: str
    diagnostics_rows: list[list[str]]
    capability_rows: list[list[str]]
    json_preview: str
    download_paths: list[str]


def run_operator_check(
    transition_label: str | None,
    pasted_json: str | None = None,
    uploaded_file: Any | None = None,
    project_gate_repo_path: str | None = None,
    architect_repo_path: str | None = None,
    ce_repo_path: str | None = None,
    builder_repo_path: str | None = None,
    responsive_repo_path: str | None = None,
    *,
    output_dir: str | Path | None = None,
) -> UiRunOutput:
    """Run the selected UI action through safe Project Gate adapters.

    This function is intentionally thin: it validates UI input, then delegates to
    existing Project Gate validators/transition functions. It does not implement
    transition semantics.
    """

    option = option_for_label(transition_label)
    capability_payload = load_capability_payload()

    if option.transition_id == "inspect_capabilities":
        result = {
            "schema_version": "ev4-project-gate-ui-result.v1",
            "result_type": "capability_inspection",
            "status": "accepted",
            "diagnostics": [],
            "output": deepcopy(capability_payload),
            "provenance": {
                "source": str(CAPABILITY_STATUS_PATH),
                "mode": "read_only",
            },
        }
        return _finalize(result, capability_payload, output_dir)

    parsed_input: Any | None = None
    if pasted_json or uploaded_file:
        parsed, malformed = _parse_json_input(pasted_json, uploaded_file)
        if malformed is not None:
            return _finalize(malformed, capability_payload, output_dir)
        parsed_input = parsed

    if not option.wired:
        result = _guard_result(
            "insufficient_evidence",
            "UI_TRANSITION_NOT_WIRED",
            "insufficient_evidence",
            "این transition هنوز در UI اجرا نمی‌شود؛ نیازمند اتصال service layer در Prompt 2 است.",
            details={
                "transition": option.transition_id,
                "next_action": option.pending_reason_fa or "اتصال service layer در Prompt 2",
            },
        )
        return _finalize(result, capability_payload, output_dir)

    if option.required_json and parsed_input is None:
        result = _guard_result(
            "invalid",
            "UI_INPUT_REQUIRED",
            "error",
            "برای اجرای این بررسی باید یک فایل JSON بارگذاری شود یا JSON در کادر ورودی paste شود.",
            details={"transition": option.transition_id, "next_action": "JSON معتبر وارد کن و دوباره اجرا کن."},
        )
        return _finalize(result, capability_payload, output_dir)

    if option.transition_id == "validate_stage_evidence_bundle":
        result = _run_stage_bundle_validation(parsed_input, project_gate_repo_path)
        return _finalize(result, capability_payload, output_dir)

    if option.transition_id == "architect_to_ce":
        result = _run_architect_to_ce(parsed_input, project_gate_repo_path, architect_repo_path, ce_repo_path)
        return _finalize(result, capability_payload, output_dir)

    result = _guard_result(
        "insufficient_evidence",
        "UI_TRANSITION_NOT_WIRED",
        "insufficient_evidence",
        "این transition در این UI هنوز به adapter امن متصل نشده است.",
        details={"transition": option.transition_id, "next_action": "Prompt 2"},
    )
    return _finalize(result, capability_payload, output_dir)


def load_capability_payload(path: str | Path = CAPABILITY_STATUS_PATH) -> dict[str, Any]:
    payload = load_json_file(path)
    if not isinstance(payload, dict):
        raise ValueError("capability-status.v1.json must contain a JSON object")
    return payload


def build_capability_rows(path: str | Path = CAPABILITY_STATUS_PATH) -> list[list[str]]:
    return capability_rows_from_payload(load_capability_payload(path))


def render_download_artifacts(result: dict[str, Any], output_dir: str | Path | None = None) -> list[str]:
    snapshot = deepcopy(result)
    directory = Path(output_dir) if output_dir is not None else Path(tempfile.mkdtemp(prefix="ev4_project_gate_ui_"))
    directory.mkdir(parents=True, exist_ok=True)

    json_path = directory / "result.json"
    md_path = directory / "report.md"
    html_path = directory / "report.html"

    json_path.write_text(render_json_result(snapshot), encoding="utf-8")
    md_path.write_text(render_markdown_report(snapshot, title="گزارش Project Gate Operator Panel"), encoding="utf-8")
    html_path.write_text(render_optional_html_report(snapshot, title="گزارش Project Gate Operator Panel"), encoding="utf-8")

    return [str(json_path), str(md_path), str(html_path)]


def _run_stage_bundle_validation(parsed_input: Any, project_gate_repo_path: str | None) -> dict[str, Any]:
    root = _resolve_project_gate_root(project_gate_repo_path)
    if isinstance(root, dict):
        return root
    return BundleValidator(root / "schemas").validate_bundle(deepcopy(parsed_input))


def _run_architect_to_ce(
    parsed_input: Any,
    project_gate_repo_path: str | None,
    architect_repo_path: str | None,
    ce_repo_path: str | None,
) -> dict[str, Any]:
    root = _resolve_project_gate_root(project_gate_repo_path)
    if isinstance(root, dict):
        return root

    architect_root = _required_local_repo_path(architect_repo_path, "Architect repo path")
    if isinstance(architect_root, dict):
        return architect_root

    ce_root = _required_local_repo_path(ce_repo_path, "CE repo path")
    if isinstance(ce_root, dict):
        return ce_root

    hooks = TransitionValidatorHooks(
        architect=lambda payload: run_architect_validator(architect_root, payload),
        ce=lambda payload, source_bundle: run_ce_validator(ce_root, payload, source_bundle),
    )
    try:
        return transition_from_local_paths(
            deepcopy(parsed_input),
            root / "schemas",
            root / "contracts" / "locks" / "architect-to-ce-transition.v1.lock.json",
            architect_root,
            ce_root,
            validator_hooks=hooks,
        )
    except ResultValidationError as exc:
        return _guard_result(
            "invalid",
            "TRANSITION_RESULT_SCHEMA_VALIDATION_FAILED",
            "error",
            "Transition result schema validation failed.",
            details={"error": str(exc), "next_action": "schema و output transition را بررسی کن."},
        )
    except OSError as exc:
        return _guard_result(
            "invalid",
            "LOCAL_PATH_READ_ERROR",
            "error",
            "یکی از مسیرهای local checkout قابل خواندن نیست.",
            details={"error_type": type(exc).__name__, "next_action": "مسیر پوشه‌های local را اصلاح کن."},
        )


def _parse_json_input(pasted_json: str | None, uploaded_file: Any | None) -> tuple[Any | None, dict[str, Any] | None]:
    try:
        text = _read_json_text(pasted_json, uploaded_file)
        return json.loads(text, parse_constant=_reject_json_constant), None
    except json.JSONDecodeError as exc:
        return None, _guard_result(
            "invalid",
            "MALFORMED_JSON",
            "error",
            "JSON واردشده معتبر نیست و هیچ بررسی اجرا نشد.",
            details={"line": exc.lineno, "column": exc.colno, "next_action": "syntax فایل JSON را اصلاح کن."},
        )
    except (OSError, ValueError) as exc:
        return None, _guard_result(
            "invalid",
            "MALFORMED_JSON",
            "error",
            "JSON واردشده معتبر نیست و هیچ بررسی اجرا نشد.",
            details={"error": str(exc), "next_action": "syntax فایل JSON را اصلاح کن."},
        )


def _read_json_text(pasted_json: str | None, uploaded_file: Any | None) -> str:
    if pasted_json and pasted_json.strip():
        return pasted_json

    if uploaded_file is None:
        raise ValueError("JSON input is required")

    file_name = uploaded_file if isinstance(uploaded_file, str) else getattr(uploaded_file, "name", None)
    if not file_name:
        raise ValueError("Uploaded JSON file path is not available")
    return Path(file_name).read_text(encoding="utf-8")


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"Invalid JSON constant: {value}")


def _resolve_project_gate_root(project_gate_repo_path: str | None) -> Path | dict[str, Any]:
    if not project_gate_repo_path or not project_gate_repo_path.strip():
        return REPOSITORY_ROOT
    return _required_local_repo_path(project_gate_repo_path, "Project Gate repo path")


def _required_local_repo_path(value: str | None, label: str) -> Path | dict[str, Any]:
    if not value or not value.strip():
        return _guard_result(
            "invalid",
            "UI_LOCAL_PATH_REQUIRED",
            "error",
            f"{label} باید مسیر یک پوشه local باشد، نه GitHub URL.",
            details={"field": label, "next_action": "مسیر checkout محلی را وارد کن."},
        )

    text = value.strip()
    if text.startswith(("http://", "https://")) or "github.com/" in text:
        return _guard_result(
            "invalid",
            "UI_LOCAL_PATH_NOT_URL",
            "error",
            f"{label} باید مسیر پوشه local باشد، نه GitHub URL.",
            details={"field": label, "observed": text, "next_action": "مثلاً ../EV4-Architect-Repo"},
        )

    path = Path(text).expanduser()
    if not path.exists() or not path.is_dir():
        return _guard_result(
            "invalid",
            "UI_LOCAL_PATH_NOT_FOUND",
            "error",
            f"{label} پیدا نشد یا پوشه نیست.",
            details={"field": label, "path": str(path), "next_action": "مسیر local checkout را اصلاح کن."},
        )
    return path


def _guard_result(
    status: str,
    code: str,
    severity: str,
    message: str,
    *,
    path: str = "$",
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    diagnostic: dict[str, Any] = {
        "code": code,
        "severity": severity,
        "message": message,
        "path": path,
    }
    if details:
        diagnostic["details"] = details
    return {
        "schema_version": "ev4-project-gate-ui-result.v1",
        "result_type": "ui_guard",
        "status": status,
        "diagnostics": [diagnostic],
        "output": None,
    }


def _finalize(result: dict[str, Any], capability_payload: dict[str, Any], output_dir: str | Path | None) -> UiRunOutput:
    downloads = render_download_artifacts(result, output_dir)
    return UiRunOutput(
        result=result,
        status_markdown=status_summary_markdown(result),
        diagnostics_rows=diagnostics_to_rows(result.get("diagnostics", [])),
        capability_rows=capability_rows_from_payload(capability_payload),
        json_preview=canonical_dumps(result),
        download_paths=downloads,
    )
