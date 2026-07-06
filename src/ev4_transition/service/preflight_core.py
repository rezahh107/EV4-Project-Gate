from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse

from .json_input import parse_json_input
from .models import GateRequest, RepoPaths
from .repo_paths import required_path_fields

PreflightCheckStatus = Literal["ok", "warning", "error", "not_required", "unknown"]
PreflightResultStatus = Literal["ready", "warnings", "blocked"]
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class PreflightCheck:
    id: str
    label_fa: str
    status: PreflightCheckStatus
    message_fa: str
    technical_detail: str | None = None
    next_action_fa: str | None = None
    classification: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PreflightResult:
    status: PreflightResultStatus
    transition_choice: str
    checks: list[PreflightCheck]
    summary_fa: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "transition_choice": self.transition_choice,
            "checks": [check.to_dict() for check in self.checks],
            "summary_fa": self.summary_fa,
        }


_LOCKS = {
    "architect_to_ce": "contracts/locks/architect-to-ce-transition.v1.lock.json",
    "ce_to_builder": "contracts/locks/ce-to-builder-transition.v1.lock.json",
    "builder_to_responsive": "contracts/locks/builder-to-responsive-transition.v1.lock.json",
    "final_gate": "contracts/locks/final-gate.v1.lock.json",
}
_REPO_FIELD = {
    "rezahh107/EV4-Project-Gate": "project_gate_repo_path",
    "rezahh107/EV4-Architect-Repo": "architect_repo_path",
    "rezahh107/EV4-Constructability-Engineer-Repo": "ce_repo_path",
    "rezahh107/EV4-Builder-Assistant-Repo": "builder_repo_path",
    "rezahh107/EV4-Responsive-Architect": "responsive_repo_path",
}
_LABEL = {
    "project_gate_repo_path": "مسیر Project Gate repo",
    "architect_repo_path": "مسیر Architect repo",
    "ce_repo_path": "مسیر CE repo",
    "builder_repo_path": "مسیر Builder repo",
    "responsive_repo_path": "مسیر Responsive repo",
}
_STAGE = {"architect_to_ce": "architect", "ce_to_builder": "ce", "builder_to_responsive": "builder", "final_gate": "responsive"}
_FIELDS = tuple(_LABEL)
_GITHUB_DESKTOP_FA = "در GitHub Desktop: repository را انتخاب کن، branch را روی main بگذار، Fetch origin و در صورت نیاز Pull origin را بزن، سپس Preflight را دوباره اجرا کن."


def run_preflight(request: GateRequest) -> PreflightResult:
    """Run a read-only setup check before the full Project Gate transition."""

    choice = str(request.transition_choice)
    repo_paths = request.repo_paths or RepoPaths()
    required = set(required_path_fields(choice))
    checks: list[PreflightCheck] = []
    checks.extend(_json_checks(request))
    checks.extend(_lock_manifest_checks(repo_paths, choice))
    required_files = _required_files_by_field(repo_paths, choice)
    for field in _FIELDS:
        checks.extend(_path_checks(repo_paths, field, field in required, required_files.get(field, ()), choice))
    checks.append(
        PreflightCheck(
            "scope.hash_verification.deferred",
            "محدوده Preflight",
            "ok",
            "Preflight فقط وجود فایل‌ها و شکل کلی ورودی را بررسی می‌کند؛ hash و identity verification در اجرای واقعی Gate انجام می‌شود.",
            "hash_verification=deferred_to_gate_run",
            classification="ok",
        )
    )
    return _result(choice, checks)


def _json_checks(request: GateRequest) -> list[PreflightCheck]:
    choice = str(request.transition_choice)
    if choice == "inspect_capabilities":
        return [PreflightCheck("json.not_required.inspect_capabilities", "ورودی JSON", "not_required", "برای Inspect Capabilities ورودی JSON لازم نیست.", "transition_choice=inspect_capabilities", classification="not_required_for_selected_transition")]
    checks: list[PreflightCheck] = []
    if choice == "validate_bundle":
        checks.append(PreflightCheck("transition.validate_bundle.validation_only", "نوع اجرای انتخاب‌شده", "warning", "این انتخاب فقط اعتبارسنجی می‌کند و خروجی CE/Builder/Responsive نمی‌سازد.", "transition_choice=validate_bundle", "اگر خروجی مرحله بعد می‌خواهی، transition مناسب مثل Architect → CE را انتخاب کن.", "validation_only_no_transition_output"))
    parsed = parse_json_input(input_json_path=request.input_json_path, input_json_text=request.input_json_text, input_data=request.input_data)
    if parsed.diagnostics:
        code = parsed.diagnostics[0].code
        return checks + [PreflightCheck("json.source.invalid_or_missing", "ورودی JSON", "error", "ورودی JSON قابل خواندن یا قابل parse نیست.", code, "یک فایل JSON معتبر بارگذاری کن یا متن JSON معتبر را paste کن.", "missing" if code == "PG.SERVICE.JSON_INPUT_MISSING" else "invalid_json_source")]
    if not isinstance(parsed.value, dict):
        return checks + [PreflightCheck("json.source.not_object", "ورودی JSON", "error", "ورودی JSON باید object باشد، نه array یا مقدار primitive.", f"json_source={parsed.source}", "فایل Stage Evidence Bundle کامل را بده.", "invalid_json_source")]
    value = parsed.value
    if choice != "validate_bundle" and _looks_like_project_gate_result(value):
        return checks + [PreflightCheck("json.source.project_gate_result", "نوع فایل JSON", "error", "این فایل نتیجه اجرای قبلی UI است، نه Stage Evidence Bundle ورودی source.", "schema_version=ev4-project-gate-ui-result.v1 result_type=service_response", "برای transition انتخاب‌شده باید source bundle مرحله قبل را بدهی، نه result.json.", "wrong_input_type")]
    expected = _STAGE.get(choice)
    observed = value.get("stage")
    if expected and isinstance(observed, str) and observed != expected:
        return checks + [PreflightCheck("json.source.wrong_stage", "stage ورودی JSON", "error", f"برای این transition ورودی باید stage={expected} باشد.", f"expected_stage={expected}; observed_stage={observed}", _wrong_stage_action(choice, expected), "wrong_stage_for_transition")]
    if expected and observed is None:
        return checks + [PreflightCheck("json.source.stage_unknown", "stage ورودی JSON", "warning", "فیلد stage در Preflight دیده نشد؛ schema validation واقعی در اجرای Gate تصمیم نهایی را می‌گیرد.", f"expected_stage={expected}; observed_stage=<missing>", "مطمئن شو فایل ورودی همان Stage Evidence Bundle source برای transition انتخاب‌شده است.", "unknown")]
    if expected:
        checks.append(PreflightCheck("json.source.stage_ok", "stage ورودی JSON", "ok", f"ورودی JSON از نظر stage با transition انتخاب‌شده هم‌خوان است: {expected}.", f"stage={expected}", classification="ok"))
    else:
        checks.append(PreflightCheck("json.source.present", "ورودی JSON", "ok", "ورودی JSON خوانده شد. اعتبارسنجی schema در اجرای واقعی Gate انجام می‌شود.", f"json_source={parsed.source}", classification="ok"))
    return checks


def _path_checks(repo_paths: RepoPaths, field: str, required: bool, files: tuple[str, ...], choice: str) -> list[PreflightCheck]:
    label = _LABEL[field]
    value = str(getattr(repo_paths, field) or "").strip()
    if not required:
        return [PreflightCheck(f"path.{field}.not_required_filled" if value else f"path.{field}.not_required", label, "not_required", "این مسیر برای transition انتخاب‌شده لازم نیست و Preflight آن را مسدودکننده حساب نمی‌کند." if value else "این مسیر برای transition انتخاب‌شده لازم نیست.", value or f"transition_choice={choice}", classification="not_required_for_selected_transition")]
    if not value:
        return [PreflightCheck(f"path.{field}.missing", label, "error", "مسیر لازم وارد نشده است.", field, "مسیر پوشه local checkout همین repository را وارد کن.", "missing")]
    if _looks_like_url(value):
        return [PreflightCheck(f"path.{field}.github_url", label, "error", "در این فیلد GitHub URL وارد شده، اما مسیر local filesystem لازم است.", value, "ریپو را local clone کن یا از GitHub Desktop مسیر پوشه repository را پیدا کن و همان مسیر را وارد کن.", "looks_like_github_url")]
    try:
        path = Path(value).expanduser()
        exists = path.exists()
        is_directory = path.is_dir() if exists else False
    except (OSError, ValueError) as exc:
        return [PreflightCheck(f"path.{field}.inaccessible", label, "error", "مسیر local قابل دسترسی نیست.", f"{value}; error_type={type(exc).__name__}", "مسیر را دوباره از File Explorer کپی کن و مطمئن شو Python به آن دسترسی دارد.", "does_not_exist")]
    if not exists:
        return [PreflightCheck(f"path.{field}.does_not_exist", label, "error", "این مسیر روی سیستم فعلی وجود ندارد.", value, "مسیر را اصلاح کن یا ریپو را با GitHub Desktop/clone روی سیستم بگیر.", "does_not_exist")]
    if not is_directory:
        return [PreflightCheck(f"path.{field}.not_directory", label, "error", "این مسیر به فایل اشاره می‌کند؛ باید پوشه repository باشد.", value, "مسیر پوشه root ریپو را وارد کن، نه مسیر یک فایل JSON یا schema.", "not_directory")]
    checks = [PreflightCheck(f"path.{field}.exists", label, "ok", "پوشه local وجود دارد.", value, classification="exists")]
    if not _has_git_checkout_marker(path):
        checks.append(PreflightCheck(f"path.{field}.not_git_checkout", label, "warning", "در این پوشه نشانه .git دیده نشد؛ ممکن است checkout کامل Git نباشد.", value, "اگر این یک export یا copy است، اجرای واقعی ممکن است فقط با فایل‌های لازم جلو برود؛ ولی checkout رسمی GitHub Desktop امن‌تر است.", "not_git_checkout"))
    if files:
        checks.append(_required_files_check(field, label, path, files))
    return checks


def _required_files_check(field: str, label: str, root: Path, files: tuple[str, ...]) -> PreflightCheck:
    try:
        missing = tuple(item for item in files if not (root / item).is_file())
    except (OSError, ValueError) as exc:
        return PreflightCheck(f"pinned.{field}.file_read_error", f"فایل‌های pin‌شده برای {label}", "error", "بررسی فایل‌های pin‌شده به خطای filesystem خورد.", f"root={root}; error_type={type(exc).__name__}", "مسیر و مجوز دسترسی پوشه local checkout را بررسی کن و دوباره Preflight را اجرا کن.", "file_read_error")
    if not missing:
        return PreflightCheck(f"pinned.{field}.ok", f"فایل‌های pin‌شده برای {label}", "ok", "فایل‌های pin‌شده لازم در این checkout پیدا شدند.", f"checked_files={len(files)}", classification="ok")
    preview = ", ".join(missing[:5]) + (f"; +{len(missing) - 5} more" if len(missing) > 5 else "")
    classification = "unexpected_repository" if len(missing) == len(files) else "required_file_missing"
    return PreflightCheck(f"pinned.{field}.missing", f"فایل‌های pin‌شده برای {label}", "error", "پوشه وجود دارد، اما فایل pin‌شده لازم پیدا نشد.", f"missing={preview}", _GITHUB_DESKTOP_FA, classification)


def _lock_manifest_checks(repo_paths: RepoPaths, choice: str) -> list[PreflightCheck]:
    rel = _LOCKS.get(choice)
    if not rel:
        return []
    path = _project_gate_root_for_lock(repo_paths, choice, rel) / rel
    if not path.is_file():
        return [PreflightCheck("lock_manifest.missing", "lock manifest Project Gate", "error", "lock manifest لازم در Project Gate checkout پیدا نشد.", str(path), "مسیر Project Gate repo را اصلاح کن یا خود Project Gate را روی main به‌روز کن. اجرای واقعی Gate همچنان مرجع نهایی است.", "required_file_missing")]
    lock, error = _read_lock_manifest(path)
    if error is not None:
        return [error]
    files = lock.get("files") if lock is not None else None
    if not isinstance(files, list):
        return [PreflightCheck("lock_manifest.files_not_array", "lock manifest Project Gate", "error", "lock manifest باید فیلد files از نوع array داشته باشد.", str(path), "Project Gate checkout را به‌روز کن یا lock manifest را بازبینی کن. اجرای واقعی Gate همچنان مرجع نهایی است.", "invalid_format")]
    return [PreflightCheck("lock_manifest.found", "lock manifest Project Gate", "ok", "lock manifest لازم برای Preflight پیدا شد.", str(path), classification="ok")]


def _required_files_by_field(repo_paths: RepoPaths, choice: str) -> dict[str, tuple[str, ...]]:
    rel = _LOCKS.get(choice)
    if not rel:
        return {}
    lock_path = _project_gate_root_for_lock(repo_paths, choice, rel) / rel
    lock, error = _read_lock_manifest(lock_path)
    if lock is None or error is not None:
        return {}
    files = lock.get("files")
    if not isinstance(files, list):
        return {}
    grouped: dict[str, list[str]] = {}
    for item in files:
        if isinstance(item, dict) and isinstance(item.get("repository"), str) and isinstance(item.get("path"), str):
            field = _REPO_FIELD.get(item["repository"])
            if field:
                grouped.setdefault(field, []).append(item["path"])
    return {field: tuple(dict.fromkeys(paths)) for field, paths in grouped.items()}


def _read_lock_manifest(path: Path) -> tuple[dict[str, Any] | None, PreflightCheck | None]:
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, ValueError) as exc:
        return None, PreflightCheck("lock_manifest.file_read_error", "lock manifest Project Gate", "error", "lock manifest از filesystem خوانده نشد.", f"path={path}; error_type={type(exc).__name__}", "مسیر، مجوز دسترسی یا سلامت checkout Project Gate را بررسی کن و دوباره Preflight را اجرا کن.", "file_read_error")
    try:
        lock = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, PreflightCheck("lock_manifest.invalid_json", "lock manifest Project Gate", "error", "lock manifest JSON معتبر نیست.", f"path={path}; line={exc.lineno}; column={exc.colno}", "Project Gate checkout را به‌روز کن یا lock manifest را بازبینی کن. اجرای واقعی Gate همچنان مرجع نهایی است.", "invalid_json")
    if not isinstance(lock, dict):
        return None, PreflightCheck("lock_manifest.invalid_format", "lock manifest Project Gate", "error", "lock manifest باید JSON object باشد.", f"path={path}; observed_type={type(lock).__name__}", "Project Gate checkout را به‌روز کن یا lock manifest را بازبینی کن. اجرای واقعی Gate همچنان مرجع نهایی است.", "invalid_format")
    return lock, None


def _project_gate_root_for_lock(repo_paths: RepoPaths, choice: str, lock_rel: str) -> Path:
    raw = repo_paths.project_gate_repo_path
    if raw:
        candidate = Path(str(raw)).expanduser()
        if (candidate / lock_rel).is_file() or "project_gate_repo_path" in set(required_path_fields(choice)):
            return candidate
    return REPOSITORY_ROOT


def _has_git_checkout_marker(path: Path) -> bool:
    marker = path / ".git"
    return marker.is_dir() or marker.is_file()


def _looks_like_url(value: str) -> bool:
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    return bool(parsed.scheme and parsed.netloc) or value.lower().startswith(("github.com/", "www.github.com/", "git" + "@github.com:"))


def _looks_like_project_gate_result(value: dict[str, Any]) -> bool:
    result_type = value.get("result_type")
    return isinstance(result_type, str) and result_type.startswith(("service_", "ui_")) or value.get("schema_version") in {"ev4-project-gate-ui-result.v1", "project-gate-service-result.v1"} or ("engine_result" in value and "transition_choice" in value and "diagnostics" in value)


def _wrong_stage_action(choice: str, expected: str) -> str:
    if choice == "ce_to_builder":
        return "برای CE → Builder باید خروجی CE از مرحله قبل را بدهی."
    if choice == "architect_to_ce":
        return "برای Architect → CE باید فایل source bundle خروجی Architect را بدهی."
    return f"فایل ورودی درست با stage={expected} را انتخاب کن."


def _result(choice: str, checks: list[PreflightCheck]) -> PreflightResult:
    statuses = {check.status for check in checks}
    if "error" in statuses:
        return PreflightResult("blocked", choice, checks, "❌ Preflight مسدود است؛ اجرای اصلی احتمالاً شکست می‌خورد. اول موارد خطادار را اصلاح کن.")
    if {"warning", "unknown"} & statuses:
        return PreflightResult("warnings", choice, checks, "⚠️ Preflight هشدار دارد؛ اجرای اصلی ممکن است ادامه پیدا کند، اما توضیح‌ها را قبل از اجرا بخوان.")
    return PreflightResult("ready", choice, checks, "✅ آماده‌سازی لازم برای اجرای انتخاب‌شده در Preflight مشکلی نشان نداد.")
