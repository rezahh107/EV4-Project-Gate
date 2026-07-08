# Operator Panel UX Contract

این سند قرارداد نهایی UX پنل محلی `EV4 Project Gate` است. این قرارداد رفتار UI، report و راهنمای انسانی را تثبیت می‌کند؛ منطق validation، transition، schema، canonical JSON، hash، status mapping یا specialist contracts را تغییر نمی‌دهد.

## Purpose

پنل محلی یک رابط انسانی برای اجرای کنترل‌شده Project Gate است:

```text
source JSON
-> optional Preflight
-> Project Gate service run
-> result.json + report.md + report.html
-> optional downstream output only when output is produced
```

پنل، موتور پنجم EV4 نیست و هیچ specialist logic جدیدی پیاده‌سازی نمی‌کند.

## Supported transitions

| UI choice | service choice | behavior |
|---|---|---|
| `Validate Stage Evidence Bundle` | `validate_bundle` | فقط Stage Evidence Bundle را اعتبارسنجی می‌کند؛ CE/Builder/Responsive output نمی‌سازد. |
| `Architect → CE` | `architect_to_ce` | Architect Stage Evidence Bundle را فقط بعد از schema/lock/hash/validator checks به CE input bundle تبدیل می‌کند. |
| `CE → Builder` | `ce_to_builder` | از service layer اجرا می‌شود و بدون شواهد/checkout معتبر fail-closed می‌ماند. |
| `Builder → Responsive` | `builder_to_responsive` | از service layer اجرا می‌شود و بدون شواهد/checkout معتبر fail-closed می‌ماند. |
| `Final Evidence Gate` | `final_gate` | از service layer اجرا می‌شود و بدون evidence معتبر fail-closed می‌ماند. |
| `Inspect Capabilities` | `inspect_capabilities` | فقط capability snapshot را read-only نشان می‌دهد. |

## Expected user flow

1. transition را انتخاب کن.
2. source JSON درست همان transition را upload یا paste کن.
3. مسیرهای local checkout لازم را وارد کن.
4. Preflight را برای خطاهای قابل پیشگیری اجرا کن.
5. اگر Preflight خطا داشت، مسیر یا input را اصلاح کن.
6. اجرای اصلی Project Gate را اجرا کن.
7. `status`, guidance, diagnostics و downloads را بررسی کن.
8. فقط وقتی `output` تولید شده و status/evidence اجازه می‌دهد، output را به مرحله بعد بده.

## Input vs result distinction

- `source Stage Evidence Bundle` ورودی اجرای Gate است.
- `result.json` گزارش اجرای UI است، نه الزاماً ورودی مرحله بعد.
- `output: null` یعنی downstream input package ساخته نشده است.
- `output.stage == "ce"` در `architect_to_ce` یعنی CE input bundle تولید شده است، اما فقط در محدوده status و evidence همان run قابل استفاده است.

## Preflight responsibilities

Preflight فقط advisory و read-only است. مجاز است این موارد را بررسی کند:

- وجود مسیرهای local لازم؛
- اینکه GitHub URL به‌جای local path وارد نشده باشد؛
- directory بودن مسیرها؛
- وجود فایل‌های pin‌شده در checkout؛
- شکل کلی JSON، wrong stage و استفاده اشتباه از `result.json`؛
- هشدار `validate_bundle` به‌عنوان validation-only.

Preflight مرجع hash/schema/validator authority نیست. تصمیم نهایی همیشه با اجرای واقعی Gate است.

## Guidance responsibilities

راهنمای عملیاتی باید در fail یا block به این پرسش‌ها جواب دهد:

```text
کجا متوقف شد؟
چه چیزی قبل از آن درست پیش رفت؟
مشکل فعلی چیست؟
اقدام بعدی دقیق چیست؟
آیا خروجی مرحله بعد ساخته شد؟
```

Guidance نباید raw diagnostics را حذف کند یا status را تغییر دهد.

## Diagnostics responsibilities

- raw diagnostics باید در advanced view و report باقی بماند.
- diagnostic code، JSONPath، repo path، schema id، hash و command باید LTR/copyable باشند.
- traceback خام نباید در visible summary نمایش داده شود؛ به diagnostic کنترل‌شده تبدیل می‌شود.

## Report responsibilities

`report.md` و `report.html` باید شامل این بخش‌ها باشند:

- status؛
- operational guidance summary؛
- Preflight summary اگر موجود باشد؛
- grouped diagnostics؛
- raw diagnostics؛
- raw JSON result در LTR code block.

HTML report باید از `<html lang="fa" dir="rtl">` استفاده کند و raw JSON/code را با `<pre dir="ltr">` نمایش دهد.

## RTL/LTR rendering rules

- متن فارسی: `lang="fa" dir="rtl"` و right-aligned.
- شناسه‌های فنی: LTR-isolated با `<bdi dir="ltr">` یا `<pre dir="ltr">`.
- JSON، path، repo، diagnostic code، JSONPath، hash، transition id و CLI command نباید RTL شوند.

## Theme/token rules

UI باید از semantic tokens در `src/ev4_transition/presentation/theme_tokens.py` استفاده کند. status باید icon + label + semantic tone داشته باشد، نه color-only. focus ring و code background token اجباری هستند.

Theme behavior باید این شرایط را حفظ کند:

- Light Mode readable باشد.
- Dark Mode readable باشد و pure black / pure white inversion نباشد.
- System Mode فقط fallback باشد و انتخاب صریح کاربر یا Gradio theme class را خراب نکند.
- EV4 custom CSS و Gradio theme variables باید از یک token source مشتق شوند.
- primary button باید explicit foreground/background داشته باشد.
- input، upload، radio، accordion، footer، disabled و Settings modal باید token-backed و readable باشند.
- disabled state نباید فقط با opacity نمایش داده شود.

## Contrast rules

Contrast-critical pairs باید با تست token-level پوشش داده شوند:

- متن عادی حداقل `4.5:1`؛
- متن بزرگ حداقل `3:1`؛
- component/focus boundary حداقل `3:1`.

Browser/computed-style visual QA همچنان evidence جدا لازم دارد و فقط با token tests کامل محسوب نمی‌شود.

## No-readiness-claim rules

پنل نباید ادعا کند:

- production readiness؛
- real Elementor validation؛
- frontend correctness؛
- responsive correctness؛
- accessibility completion؛
- CE approval؛
- Builder authorization؛
- end-to-end EV4 readiness.

## Out of scope

- automatic JSON repair؛
- automatic git clone/pull/fetch؛
- telemetry؛
- background monitoring؛
- new transition feature؛
- specialist schema/validator/adapter changes.
