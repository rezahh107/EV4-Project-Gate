# Controlled End-to-End Demo Workflow

<section lang="fa" dir="rtl">

این سند یک demo کنترل‌شده را توضیح می‌دهد، نه اجرای واقعی production و نه end-to-end واقعی EV4.

## هدف demo

هدف این است که کاربر غیر CLI بفهمد مسیر شخصی Project Gate چطور شروع می‌شود، خروجی‌ها کجا ذخیره می‌شوند، و چرا بدون شواهد واقعی نباید `accepted` ادعا شود.

## دستور اجرا

```bash
python scripts/run-project-gate-demo.py
```

خروجی در مسیر زیر ساخته می‌شود:

```text
outputs/runs/demo-<timestamp>/
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
- اگر service layer از Prompt 2 merge نشده باشد، مرحله service با status `missing` یا `pending` گزارش می‌شود.
- اگر UI از Prompt 1 merge نشده باشد، مرحله UI با status `missing` یا `pending` گزارش می‌شود.
- اگر شواهد واقعی وجود نداشته باشد، تصمیم نهایی باید `insufficient_evidence` باقی بماند.

## فایل‌های خروجی demo

```text
result.json
report.md
report.html
input.snapshot.json
diagnostics.json
```

## سناریوی مورد انتظار

1. sample valid synthetic با bundle validator بررسی می‌شود.
2. sample insufficient synthetic با bundle validator بررسی می‌شود.
3. demo بررسی می‌کند که UI و service module موجود هستند یا نه.
4. demo خروجی فارسی و JSON می‌سازد.
5. demo هرگز ادعای real Elementor validation یا production readiness نمی‌کند.

## چیزی که این demo ثابت نمی‌کند

این demo ثابت نمی‌کند که:

- خروجی واقعی Architect آماده عبور است.
- CE constructability واقعی انجام شده است.
- Builder اجرای واقعی Elementor انجام داده است.
- Responsive validation واقعی انجام شده است.
- accessibility/export/frontend correctness کامل شده است.
- کل زنجیره EV4 آماده production است.

</section>
