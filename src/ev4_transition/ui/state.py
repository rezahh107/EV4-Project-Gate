from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ev4_transition.presentation.status_mapping import ProjectGateStatus, normalize_status, presentation_for_status


@dataclass(frozen=True)
class TransitionOption:
    transition_id: str
    label_en: str
    label_fa: str
    wired: bool
    required_json: bool
    pending_reason_fa: str = ""


TRANSITION_OPTIONS: tuple[TransitionOption, ...] = (
    TransitionOption(
        "validate_stage_evidence_bundle",
        "Validate Stage Evidence Bundle",
        "اعتبارسنجی Stage Evidence Bundle",
        True,
        True,
    ),
    TransitionOption(
        "architect_to_ce",
        "Architect → CE",
        "Architect → CE",
        True,
        True,
    ),
    TransitionOption(
        "ce_to_builder",
        "CE → Builder",
        "CE → Builder",
        False,
        False,
        "نیازمند اتصال service layer در Prompt 2",
    ),
    TransitionOption(
        "builder_to_responsive",
        "Builder → Responsive",
        "Builder → Responsive",
        False,
        False,
        "نیازمند اتصال service layer در Prompt 2",
    ),
    TransitionOption(
        "final_evidence_gate",
        "Final Evidence Gate",
        "Final Evidence Gate",
        False,
        False,
        "نیازمند اتصال service layer در Prompt 2",
    ),
    TransitionOption(
        "inspect_capabilities",
        "Inspect Capabilities",
        "بازبینی قابلیت‌ها",
        True,
        False,
    ),
)


STATUS_MEANINGS_FA: dict[ProjectGateStatus, str] = {
    "accepted": "این بررسی در همین محدوده پذیرفته شد.",
    "invalid": "ساختار یا قرارداد نامعتبر است.",
    "insufficient_evidence": "شواهد کافی نیست.",
    "repair_needed": "بسته قابل فهم است ولی نیاز به اصلاح دارد.",
}

STATUS_NEXT_ACTION_FA: dict[ProjectGateStatus, str] = {
    "accepted": "نتیجه را فقط در محدوده همین بررسی استفاده کن؛ این تولید-ready یا frontend-ready نیست.",
    "invalid": "JSON، schema identity، مسیرها، hashها و diagnosticهای خطادار را اصلاح کن و دوباره اجرا کن.",
    "insufficient_evidence": "شواهد گمشده را از owner repository یا validator رسمی تهیه کن و دوباره اجرا کن.",
    "repair_needed": "موارد قابل اصلاح را از Diagnostics بردار و بسته را دوباره بساز.",
}


def transition_choices() -> list[str]:
    return [option.label_en for option in TRANSITION_OPTIONS]


def option_for_label(label: str | None) -> TransitionOption:
    if label:
        for option in TRANSITION_OPTIONS:
            if label in {option.label_en, option.label_fa, option.transition_id}:
                return option
    return TRANSITION_OPTIONS[0]


def normalize_ui_status(status: Any) -> ProjectGateStatus:
    try:
        return normalize_status(str(status))
    except ValueError:
        return "invalid"


def status_label_fa(status: Any) -> str:
    normalized = normalize_ui_status(status)
    presentation = presentation_for_status(normalized)
    return f"{presentation.icon} {presentation.persian_label} / {normalized}"
