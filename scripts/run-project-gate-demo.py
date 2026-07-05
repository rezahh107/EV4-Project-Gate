#!/usr/bin/env python3
"""Run a controlled personal-use demo with synthetic Project Gate fixtures.

This script is packaging glue only. It does not implement transition semantics,
CE constructability logic, Builder runtime logic, Responsive repair logic, or
real end-to-end Elementor validation.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
DEFAULT_OUTPUT_ROOT = ROOT / "outputs" / "runs"
DEFAULT_VALID_FIXTURE = ROOT / "fixtures" / "personal-use" / "sample-valid-stage-bundle.synthetic.json"
DEFAULT_INSUFFICIENT_FIXTURE = ROOT / "fixtures" / "personal-use" / "sample-insufficient-evidence-stage-bundle.synthetic.json"


def _bootstrap_src_path() -> None:
    if SRC.exists() and str(SRC) not in sys.path:
        sys.path.insert(0, str(SRC))


def _module_state(module_name: str, owner: str) -> dict[str, str]:
    try:
        spec = importlib.util.find_spec(module_name)
    except (ImportError, ModuleNotFoundError, AttributeError, ValueError) as exc:
        return {"module": module_name, "status": "missing", "owner": owner, "detail": f"{type(exc).__name__}: {exc}"}
    if spec is None:
        return {"module": module_name, "status": "missing", "owner": owner}
    return {"module": module_name, "status": "available", "owner": owner}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve())).replace("\\", "/")
    except ValueError:
        return str(path)


def _validate_fixture(path: Path, validator: Any) -> dict[str, Any]:
    bundle = _load_json(path)
    result = validator.validate_file(path)
    return {
        "path": _relative(path),
        "synthetic": bool(bundle.get("synthetic")),
        "declared_evidence_status": bundle.get("evidence_status"),
        "validation_status": result.get("status"),
        "diagnostics": result.get("diagnostics", []),
        "result": result,
    }


def _render_markdown(demo_result: dict[str, Any]) -> str:
    lines = [
        '<section lang="fa" dir="rtl" class="ev4-personal-demo-report">',
        "",
        "# گزارش demo کنترل‌شده Project Gate",
        "",
        f"- وضعیت کلی demo: `{demo_result['overall_status']}`",
        f"- نتیجه نهایی مجاز برای demo: `{demo_result['final_gate_status']}`",
        "- نوع داده: فقط `synthetic`",
        "- ادعای شواهد واقعی: `false`",
        "- ادعای production readiness: `false`",
        "",
        "این demo فقط مسیر بسته‌بندی مصرف شخصی را نشان می‌دهد. اگر UI یا service هنوز merge نشده باشد، همان مرحله `pending` می‌ماند و نتیجه واقعی end-to-end ساخته نمی‌شود.",
        "",
        "## وضعیت لایه‌ها",
        f"- UI: `{demo_result['ui']['status']}` — owner: `{demo_result['ui']['owner']}`",
        f"- Service: `{demo_result['service']['status']}` — owner: `{demo_result['service']['owner']}`",
        "",
        "## نمونه‌های بررسی‌شده",
    ]
    for sample in demo_result["samples"]:
        lines.append(
            f"- `{sample['path']}` → status: `{sample['validation_status']}` / synthetic: `{sample['synthetic']}` / evidence: `{sample['declared_evidence_status']}`"
        )
    lines.extend(
        [
            "",
            "## تصمیم امن",
            "تا وقتی شواهد واقعی owner repositoryها، خروجی Builder، خروجی Responsive و export/accessibility evidence واقعی وجود نداشته باشد، تصمیم نهایی باید `insufficient_evidence` باقی بماند.",
            "",
            "</section>",
            "",
        ]
    )
    return "\n".join(lines)


def _render_html(markdown_text: str) -> str:
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="fa" dir="rtl">',
            "<head><meta charset=\"utf-8\"><title>EV4 Project Gate Demo</title></head>",
            "<body>",
            "<pre>",
            escape(markdown_text),
            "</pre>",
            "</body>",
            "</html>",
            "",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the EV4 Project Gate controlled synthetic personal-use demo.")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT, help="Directory that will contain demo-* run folders.")
    parser.add_argument("--valid-fixture", type=Path, default=DEFAULT_VALID_FIXTURE)
    parser.add_argument("--insufficient-fixture", type=Path, default=DEFAULT_INSUFFICIENT_FIXTURE)
    args = parser.parse_args(argv)

    _bootstrap_src_path()
    try:
        from ev4_transition import BundleValidator
    except Exception as exc:  # pragma: no cover - defensive user-facing path
        print("❌ EV4 Project Gate package import failed.")
        print("Run: python -m pip install -e '.[dev]'")
        print(f"error: {type(exc).__name__}: {exc}")
        return 1

    run_id = "demo-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = args.output_root / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    validator = BundleValidator(schema_root=ROOT / "schemas")
    samples = [
        _validate_fixture(args.valid_fixture, validator),
        _validate_fixture(args.insufficient_fixture, validator),
    ]

    ui_state = _module_state("ev4_transition.ui", "Prompt 1")
    service_state = _module_state("ev4_transition.service", "Prompt 2")
    partial = ui_state["status"] != "available" or service_state["status"] != "available"

    demo_result = {
        "schema_version": "ev4-personal-use-demo-result.v1",
        "demo_mode": "controlled_synthetic_personal_use",
        "overall_status": "partial_setup" if partial else "demo_completed",
        "final_gate_status": "insufficient_evidence",
        "real_evidence_claimed": False,
        "production_readiness_claimed": False,
        "real_elementor_validation_claimed": False,
        "ui": ui_state,
        "service": service_state,
        "samples": samples,
        "safe_next_step_fa": "برای اجرای واقعی، ابتدا UI/Service را merge کن و سپس شواهد واقعی owner repositoryها را وارد کن.",
    }

    input_snapshot = {
        "schema_version": "ev4-personal-demo-input-snapshot.v1",
        "fixtures": [_relative(args.valid_fixture), _relative(args.insufficient_fixture)],
        "synthetic_only": True,
        "not_real_handoff_evidence": True,
    }
    diagnostics = {
        "schema_version": "ev4-personal-demo-diagnostics.v1",
        "diagnostics": [
            {"sample": sample["path"], "diagnostics": sample["diagnostics"]} for sample in samples
        ],
    }
    report_md = _render_markdown(demo_result)

    _write_json(run_dir / "result.json", demo_result)
    _write_text(run_dir / "report.md", report_md)
    _write_text(run_dir / "report.html", _render_html(report_md))
    _write_json(run_dir / "input.snapshot.json", input_snapshot)
    _write_json(run_dir / "diagnostics.json", diagnostics)
    _write_json(run_dir / "demo-status.json", demo_result)

    expected_valid = samples[0]["validation_status"] in {"valid", "accepted"}
    expected_insufficient = samples[1]["validation_status"] == "insufficient_evidence"
    synthetic_only = all(sample["synthetic"] for sample in samples)
    safe_claims = not demo_result["real_evidence_claimed"] and not demo_result["production_readiness_claimed"]

    print("✅ Controlled synthetic demo completed.")
    print("این demo شواهد واقعی یا آمادگی production را ادعا نمی‌کند.")
    print(f"output_path: {run_dir}")
    print(f"overall_status: {demo_result['overall_status']}")
    print(f"final_gate_status: {demo_result['final_gate_status']}")

    return 0 if expected_valid and expected_insufficient and synthetic_only and safe_claims else 1


if __name__ == "__main__":
    raise SystemExit(main())
