# Controlled End-to-End Demo Workflow

<section lang="fa" dir="rtl">

این سند یک demo کنترل‌شده را توضیح می‌دهد، نه اجرای واقعی production و نه end-to-end واقعی EV4.

## آماده‌سازی

مسیر پیش‌فرض با `uv` است:

```bash
uv python install 3.11
uv sync --extra dev --extra ui
```

برای اجرای قفل‌شده و شبیه CI:

```bash
uv lock --check
uv sync --locked --extra dev --extra ui
```

## دستور اجرا

```bash
uv run python scripts/run-project-gate-demo.py
```

خروجی demo در مسیر زیر ساخته می‌شود:

```text
outputs/runs/demo-<timestamp-or-run-id>/
```

## مسیر مفهومی demo

```text
Validate Stage Evidence Bundle
→ Architect
→ CE if available
→ CE
→ Builder baseline if service exists
→ Builder
→ Responsive baseline if service exists
→ Final Gate baseline if service exists
```

## رفتار صادقانه demo

- فایل‌های ورودی demo synthetic هستند.
- این demo شواهد واقعی handoff نیست.
- اگر service layer موجود نباشد، مرحله service با status `missing` یا `pending` گزارش می‌شود.
- اگر UI موجود نباشد، مرحله UI با status `missing` یا `pending` گزارش می‌شود.
- اگر شواهد واقعی وجود نداشته باشد، تصمیم نهایی باید `insufficient_evidence` باقی بماند.
- demo نباید real Elementor validation، export validation، accessibility completion، frontend correctness، responsive correctness، production readiness یا real end-to-end readiness ادعا کند.

## فایل‌های خروجی demo

```text
result.json
report.md
report.html
input.snapshot.json
diagnostics.json
```

## Fallback if uv is unavailable

فقط اگر `uv` قابل نصب نیست:

```bash
python -m pip install -e '.[dev,ui]'
python scripts/run-project-gate-demo.py
```

</section>
