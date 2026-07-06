from __future__ import annotations

from ev4_transition.service.preflight import PreflightCheck, PreflightResult
from ev4_transition.ui.preflight_components import preflight_result_html


def test_preflight_rendering_preserves_rtl_persian_and_ltr_technical_identifiers():
    result = PreflightResult(
        status="blocked",
        transition_choice="architect_to_ce",
        summary_fa="❌ Preflight مسدود است.",
        checks=[
            PreflightCheck(
                id="pinned.ce_repo_path.missing",
                label_fa="فایل‌های pin‌شده برای مسیر CE repo",
                status="error",
                message_fa="پوشه وجود دارد، اما فایل pin‌شده لازم پیدا نشد.",
                technical_detail="schemas/ce_architect_stage_intake.v1_1.schema.json",
                next_action_fa="در GitHub Desktop Fetch origin را بزن.",
                classification="required_file_missing",
            )
        ],
    )

    rendered = preflight_result_html(result)

    assert '<section lang="fa" dir="rtl"' in rendered
    assert "بررسی آماده‌سازی مسیرها / Preflight" in rendered
    assert '<bdi dir="ltr"><code>architect_to_ce</code></bdi>' in rendered
    assert '<bdi dir="ltr"><code>schemas/ce_architect_stage_intake.v1_1.schema.json</code></bdi>' in rendered
    assert '<bdi dir="ltr"><code>required_file_missing</code></bdi>' in rendered
    assert "GitHub Desktop" in rendered
