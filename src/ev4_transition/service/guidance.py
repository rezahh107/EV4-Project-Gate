from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import json
from pathlib import Path
from typing import Any

GUIDANCE_REGISTRY_PATH = Path(__file__).resolve().parents[1] / "data" / "operator-guidance.v1.json"

_GROUP_TITLES_FA = {
    "input_json": "Input JSON",
    "transition_selection": "انتخاب transition",
    "local_repository_paths": "مسیرهای local repository",
    "pinned_external_files": "فایل‌های خارجی pin‌شده",
    "external_lock_hash_verification": "بررسی lock و hash خارجی",
    "architect_source_identity": "هویت source Architect",
    "architect_schema_validation": "اعتبارسنجی schema Architect",
    "architect_semantic_validation": "اعتبارسنجی معنایی Architect",
    "ce_schema_validation": "اعتبارسنجی schema CE",
    "ce_validator": "validator رسمی CE",
    "output_bundle_validation": "اعتبارسنجی output bundle",
    "ui_report_rendering": "UI و report rendering",
    "unknown": "نامشخص",
}

_TRANSITION_TITLES_FA = {
    "validate_bundle": "اعتبارسنجی Stage Evidence Bundle",
    "inspect_capabilities": "بازبینی قابلیت‌ها",
    "architect_to_ce": "Architect → CE",
    "ce_to_builder": "CE → Builder",
    "builder_to_responsive": "Builder → Responsive",
    "final_gate": "Final Evidence Gate",
}

_OUTPUT_STATE_FA = {
    "no_output_because_invalid": "خیر — output برابر null است، چون Gate به وضعیت invalid رسید و بسته مرحله بعد تولید نشد.",
    "no_output_because_insufficient_evidence": "خیر — output برابر null است، چون شواهد کافی نبود و بسته مرحله بعد تولید نشد.",
    "validation_only_no_transition": "خیر — validate_bundle فقط خود bundle را اعتبارسنجی می‌کند و transition به مرحله بعد انجام نمی‌دهد.",
    "transition_output_produced": "بله — output تولید شده است؛ قبل از استفاده، status و evidence scope را بررسی کن.",
    "unknown_output_state": "نامشخص — از result فعلی نمی‌توان با قطعیت وضعیت output را تعیین کرد.",
}

_STATUS_PROBLEM_FA = {
    "accepted": "در محدوده همین بررسی، diagnostic مسدودکننده ثبت نشده است.",
    "repair_needed": "بسته قابل فهم است، اما اصلاح لازم دارد.",
    "insufficient_evidence": "شواهد لازم برای ادامه امن کامل نیست.",
    "invalid": "ورودی، مسیر، قرارداد یا اجرای Gate نامعتبر شده است.",
}

_STATUS_NEXT_ACTION_FA = {
    "accepted": "نتیجه را فقط در محدوده همین Gate استفاده کن؛ این production/readiness proof نیست.",
    "repair_needed": "diagnosticهای warning/error را اصلاح کن و دوباره اجرا کن.",
    "insufficient_evidence": "شواهد یا checkout رسمی گمشده را فراهم کن و دوباره اجرا کن.",
    "invalid": "اولین diagnostic خطادار را اصلاح کن و سپس دوباره اجرا کن.",
}

_STAGE_ORDER = {
    "input_json": 1,
    "transition_selection": 5,
    "local_repository_paths": 10,
    "pinned_external_files": 20,
    "external_lock_hash_verification": 30,
    "architect_source_identity": 40,
    "architect_schema_validation": 50,
    "architect_semantic_validation": 60,
    "ce_schema_validation": 70,
    "ce_validator": 80,
    "output_bundle_validation": 90,
    "ui_report_rendering": 95,
    "unknown": 99,
}


@dataclass(frozen=True)
class GuidanceItem:
    code: str
    group: str
    title_fa: str
    meaning_fa: str
    common_causes_fa: tuple[str, ...]
    next_actions_fa: tuple[str, ...]
    repair_prompt_template: str | None = None


@dataclass(frozen=True)
class DiagnosticGroup:
    group: str
    title_fa: str
    count: int
    top_messages: tuple[str, ...]
    next_action_fa: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "group": self.group,
            "title_fa": self.title_fa,
            "count": self.count,
            "top_messages": list(self.top_messages),
            "next_action_fa": self.next_action_fa,
        }


@dataclass(frozen=True)
class OperatorGuidance:
    headline_fa: str
    where_stopped_fa: str
    passed_steps_fa: tuple[str, ...]
    current_problem_fa: str
    next_actions_fa: tuple[str, ...]
    output_state: str
    output_state_fa: str
    diagnostic_groups: tuple[DiagnosticGroup, ...]
    repair_prompt_fa_or_en: str | None
    severity: str
    safe_to_continue: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "headline_fa": self.headline_fa,
            "where_stopped_fa": self.where_stopped_fa,
            "passed_steps_fa": list(self.passed_steps_fa),
            "current_problem_fa": self.current_problem_fa,
            "next_actions_fa": list(self.next_actions_fa),
            "output_state": self.output_state,
            "output_state_fa": self.output_state_fa,
            "diagnostic_groups": [group.to_dict() for group in self.diagnostic_groups],
            "repair_prompt_fa_or_en": self.repair_prompt_fa_or_en,
            "severity": self.severity,
            "safe_to_continue": self.safe_to_continue,
        }


def build_operator_guidance(result: dict[str, Any]) -> OperatorGuidance:
    diagnostics = _diagnostics(result)
    registry = load_guidance_registry()
    groups = group_diagnostics(diagnostics, registry)
    primary = _primary_guidance(diagnostics, registry)
    status = str(result.get("status", "invalid"))
    transition_choice = str(result.get("transition_choice", ""))
    transition_title = _TRANSITION_TITLES_FA.get(transition_choice, transition_choice or "transition نامشخص")
    output_state = classify_output_state(result)
    output_state_fa = _output_state_fa(result, output_state)

    return OperatorGuidance(
        headline_fa=_headline_fa(status, transition_title, output_state),
        where_stopped_fa=_where_stopped_fa(status, transition_title, groups, primary, output_state),
        passed_steps_fa=tuple(_passed_steps_fa(status, primary, output_state)),
        current_problem_fa=_current_problem_fa(status, primary),
        next_actions_fa=tuple(_next_actions_fa(status, primary, output_state, transition_choice)),
        output_state=output_state,
        output_state_fa=output_state_fa,
        diagnostic_groups=tuple(groups),
        repair_prompt_fa_or_en=_repair_prompt(result, diagnostics, registry),
        severity=_severity_from_status(status),
        safe_to_continue=output_state == "transition_output_produced" and status in {"accepted", "valid"},
    )


def classify_output_state(result: dict[str, Any]) -> str:
    transition_choice = str(result.get("transition_choice", ""))
    status = str(result.get("status", "invalid"))
    output = result.get("output")
    if transition_choice == "validate_bundle":
        return "validation_only_no_transition"
    if output is None:
        return "no_output_because_insufficient_evidence" if status == "insufficient_evidence" else "no_output_because_invalid"
    if isinstance(output, dict):
        return "transition_output_produced"
    return "unknown_output_state"


def group_diagnostics(diagnostics: list[dict[str, Any]], registry: dict[str, GuidanceItem] | None = None) -> list[DiagnosticGroup]:
    registry = registry or load_guidance_registry()
    buckets: dict[str, list[dict[str, Any]]] = {}
    for diagnostic in diagnostics:
        code = str(diagnostic.get("code", "UNKNOWN_DIAGNOSTIC"))
        item = registry.get(code)
        group = item.group if item else _fallback_group(code)
        buckets.setdefault(group, []).append(diagnostic)

    groups: list[DiagnosticGroup] = []
    for group, items in sorted(buckets.items(), key=lambda pair: (_STAGE_ORDER.get(pair[0], 99), pair[0])):
        groups.append(
            DiagnosticGroup(
                group=group,
                title_fa=_GROUP_TITLES_FA.get(group, group),
                count=len(items),
                top_messages=tuple(_safe_ui_message(str(item.get("message", ""))) for item in items[:3]),
                next_action_fa=_group_actions(group, items, registry),
            )
        )
    return groups


def load_guidance_registry(path: str | Path = GUIDANCE_REGISTRY_PATH) -> dict[str, GuidanceItem]:
    return _load_guidance_registry_cached(str(path))


@lru_cache(maxsize=4)
def _load_guidance_registry_cached(path: str) -> dict[str, GuidanceItem]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != "ev4-project-gate-operator-guidance.v1":
        raise ValueError("operator guidance registry schema_version mismatch")
    items = payload.get("items")
    if not isinstance(items, list):
        raise ValueError("operator guidance registry items must be a list")

    registry: dict[str, GuidanceItem] = {}
    for raw in items:
        if not isinstance(raw, dict):
            raise ValueError("operator guidance item must be an object")
        code = _required_str(raw, "code")
        item = GuidanceItem(
            code=code,
            group=_required_str(raw, "group"),
            title_fa=_required_str(raw, "title_fa"),
            meaning_fa=_required_str(raw, "meaning_fa"),
            common_causes_fa=tuple(_required_str_list(raw, "common_causes_fa")),
            next_actions_fa=tuple(_required_str_list(raw, "next_actions_fa")),
            repair_prompt_template=raw.get("repair_prompt_template") if isinstance(raw.get("repair_prompt_template"), str) else None,
        )
        if code in registry:
            raise ValueError(f"duplicate operator guidance code: {code}")
        registry[code] = item
    return registry


def _required_str(raw: dict[str, Any], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"operator guidance item missing string field: {key}")
    return value


def _required_str_list(raw: dict[str, Any], key: str) -> list[str]:
    value = raw.get(key)
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item.strip() for item in value):
        raise ValueError(f"operator guidance item missing string list field: {key}")
    return value


def _diagnostics(result: dict[str, Any]) -> list[dict[str, Any]]:
    diagnostics = result.get("diagnostics", [])
    if not isinstance(diagnostics, list):
        return []
    return [item for item in diagnostics if isinstance(item, dict)]


def _primary_guidance(diagnostics: list[dict[str, Any]], registry: dict[str, GuidanceItem]) -> GuidanceItem | None:
    known: list[tuple[int, int, GuidanceItem]] = []
    for index, diagnostic in enumerate(diagnostics):
        item = registry.get(str(diagnostic.get("code", "")))
        if item is not None:
            known.append((_STAGE_ORDER.get(item.group, 99), index, item))
    if not known:
        return None
    known.sort(key=lambda item: (item[0], item[1]))
    return known[0][2]


def _fallback_group(code: str) -> str:
    if code.startswith("PG.SERVICE.JSON") or code in {"INPUT_NOT_OBJECT"}:
        return "input_json"
    if code.startswith("PG.SERVICE.TRANSITION"):
        return "transition_selection"
    if code.startswith("PG.SERVICE.REPO_PATH"):
        return "local_repository_paths"
    if code in {"PG.SERVICE.LOCAL_FILE_ACCESS_FAILED", "PG.SERVICE.FILE_READ_ERROR"}:
        return "pinned_external_files"
    if "EXTERNAL_FILE_READ" in code:
        return "pinned_external_files"
    if "HASH" in code or "LOCK" in code:
        return "external_lock_hash_verification"
    if "SOURCE" in code:
        return "architect_source_identity"
    if "ARCHITECT_SCHEMA" in code:
        return "architect_schema_validation"
    if "ARCHITECT" in code and "VALIDATION" in code:
        return "architect_semantic_validation"
    if "CE_SCHEMA" in code:
        return "ce_schema_validation"
    if "CE" in code and "VALIDATION" in code:
        return "ce_validator"
    if "OUTPUT" in code or "RESULT_SCHEMA" in code:
        return "output_bundle_validation"
    if code.startswith("PG.UI") or "REPORT" in code:
        return "ui_report_rendering"
    return "unknown"


def _group_actions(group: str, items: list[dict[str, Any]], registry: dict[str, GuidanceItem]) -> str:
    for item in items:
        guidance = registry.get(str(item.get("code", "")))
        if guidance and guidance.next_actions_fa:
            return guidance.next_actions_fa[0]
    if group == "input_json":
        return "JSON ورودی را اصلاح یا فایل درست را بارگذاری کن."
    if group == "unknown":
        return "diagnostic خام را بررسی کن و از حدس یا normalizing پنهان خودداری کن."
    return "گروه diagnostic را اصلاح کن و دوباره اجرا کن."


def _where_stopped_fa(status: str, transition_title: str, groups: list[DiagnosticGroup], primary: GuidanceItem | None, output_state: str) -> str:
    if status in {"accepted", "valid"} and output_state == "validation_only_no_transition":
        return f"{transition_title} کامل شد؛ این مسیر transition به مرحله بعد نیست."
    if status in {"accepted", "valid"}:
        return f"{transition_title} در محدوده شواهد موجود به پایان رسید."
    if primary is not None:
        return f"{transition_title} در بخش «{_GROUP_TITLES_FA.get(primary.group, primary.group)}» متوقف شد."
    if groups:
        return f"{transition_title} در بخش «{groups[0].title_fa}» متوقف شد."
    return f"{transition_title} متوقف شد، اما diagnostic قابل گروه‌بندی ثبت نشده است."


def _current_problem_fa(status: str, primary: GuidanceItem | None) -> str:
    if primary is None:
        return _STATUS_PROBLEM_FA.get(status, _STATUS_PROBLEM_FA["invalid"])
    return f"{primary.title_fa}: {primary.meaning_fa}"


def _next_actions_fa(status: str, primary: GuidanceItem | None, output_state: str, transition_choice: str) -> list[str]:
    actions: list[str] = []
    if primary is not None:
        actions.extend(primary.next_actions_fa)
    elif output_state == "validation_only_no_transition":
        actions.append("اگر فقط اعتبارسنجی می‌خواستی، همین نتیجه را ثبت کن.")
        actions.append("اگر CE input bundle می‌خواهی، transition Architect → CE را با Architect source bundle اجرا کن.")
    else:
        actions.append(_STATUS_NEXT_ACTION_FA.get(status, _STATUS_NEXT_ACTION_FA["invalid"]))
    if transition_choice == "validate_bundle" and output_state == "validation_only_no_transition":
        reminder = "validate_bundle خروجی CE، Builder یا Responsive تولید نمی‌کند."
        if reminder not in actions:
            actions.append(reminder)
    return actions[:5]


def _passed_steps_fa(status: str, primary: GuidanceItem | None, output_state: str) -> list[str]:
    if status in {"accepted", "valid"} and output_state == "validation_only_no_transition":
        return ["JSON خوانده شد.", "Stage Evidence Bundle در محدوده validator انتخاب‌شده بررسی شد."]
    if status in {"accepted", "valid"}:
        return ["transition انتخاب‌شده بدون diagnostic مسدودکننده در همین محدوده کامل شد."]
    if primary is None:
        return ["از result فعلی مرحلهٔ پاس‌شدهٔ بیشتری با قطعیت قابل ادعا نیست."]
    if primary.group == "local_repository_paths":
        return ["انتخاب transition انجام شد.", "اجرای گران‌تر قبل از داشتن مسیرهای local معتبر شروع نشد."]
    if primary.group == "pinned_external_files":
        return ["JSON و انتخاب transition تا مرحله خواندن فایل‌های local پیش رفت."]
    if primary.group == "external_lock_hash_verification":
        return ["فایل خارجی پیدا شد، اما identity/hash آن باید با lock رسمی منطبق شود."]
    if primary.group == "architect_schema_validation":
        return ["ورودی تا مرحله بررسی schema رسمی Architect رسید.", "با این حال schema validation خود payload شکست خورد و output تولید نشد."]
    if primary.group == "ce_schema_validation":
        return ["mapping تا تولید candidate CE payload پیش رفت.", "اما schema رسمی CE آن را نپذیرفت."]
    if primary.group == "transition_selection":
        return ["JSON اولیه خوانده شد، اما انتخاب transition یا نوع فایل ورودی با هم سازگار نبودند."]
    return ["مرحله توقف از روی diagnostic اصلی تعیین شد؛ پاس قطعی بیشتری ادعا نمی‌شود."]


def _headline_fa(status: str, transition_title: str, output_state: str) -> str:
    if output_state == "transition_output_produced" and status in {"accepted", "valid"}:
        return f"{transition_title}: خروجی مرحله بعد تولید شد."
    if output_state == "validation_only_no_transition":
        return f"{transition_title}: فقط اعتبارسنجی انجام شد."
    return f"{transition_title}: ادامه متوقف شد."


def _output_state_fa(result: dict[str, Any], output_state: str) -> str:
    output = result.get("output")
    if output_state == "transition_output_produced" and isinstance(output, dict) and output.get("stage") == "ce":
        return "بله — output ساخته شد و stage آن ce است؛ این همان CE input bundle است، اما فقط در محدوده status و evidence فعلی قابل استفاده است."
    return _OUTPUT_STATE_FA.get(output_state, _OUTPUT_STATE_FA["unknown_output_state"])


def _severity_from_status(status: str) -> str:
    if status in {"accepted", "valid"}:
        return "success"
    if status in {"repair_needed", "insufficient_evidence"}:
        return "warning"
    return "danger"


def _safe_ui_message(value: str) -> str:
    blocked_markers = ("Traceback", "File ", "line ", "raise ")
    if any(marker in value for marker in blocked_markers):
        return "جزئیات runtime از نمای اصلی حذف شد؛ diagnostics خام را در بخش پیشرفته بررسی کن."
    return value.replace("\n", " ").strip()[:500]


def _repair_prompt(result: dict[str, Any], diagnostics: list[dict[str, Any]], registry: dict[str, GuidanceItem]) -> str | None:
    repairable = [
        diagnostic
        for diagnostic in diagnostics
        if registry.get(str(diagnostic.get("code", "")))
        and registry[str(diagnostic.get("code", ""))].repair_prompt_template == "architect_schema_repair_v1"
    ]
    if not repairable:
        return None

    violations = []
    for diagnostic in repairable[:20]:
        code = str(diagnostic.get("code", "UNKNOWN_DIAGNOSTIC"))
        path = str(diagnostic.get("path", "$"))
        message = _safe_prompt_text(str(diagnostic.get("message", "")))
        violations.append(f"- code: {code} | path: {path} | message: {message}")

    transition_choice = str(result.get("transition_choice", "architect_to_ce"))
    return "\n".join(
        [
            "The previous Architect Stage Evidence Bundle failed Project Gate architect_to_ce validation.",
            "",
            "Repair only the Architect Stage Evidence Bundle so it strictly conforms to:",
            "ev4-architect-stage-payload@1.0.0",
            "",
            "Do not change the selected candidate, architecture meaning, evidence meaning, or downstream boundary assertions.",
            "Do not invent evidence. Do not normalize specialist outputs silently.",
            "",
            f"Project Gate transition choice: {transition_choice}",
            "",
            "Fix the schema violations listed below:",
            *violations,
            "",
            "Return only the corrected full JSON Stage Evidence Bundle.",
        ]
    )


def _safe_prompt_text(value: str) -> str:
    blocked_markers = ("Traceback", "File ", "line ", "raise ")
    if any(marker in value for marker in blocked_markers):
        return "[technical runtime details omitted from repair prompt]"
    return value.replace("\n", " ").strip()[:500]
