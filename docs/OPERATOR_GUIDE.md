# Operator Guide — EV4 Project Gate Local Panel

این سند راهنمای استفاده از پنل محلی Project Gate است. پنل فقط یک لایه انسانی برای اجرای بررسی‌های Project Gate است و منطق transition، schema، validator یا قرارداد specialist جدید ایجاد نمی‌کند.

شروع سریع برای استفاده روزمره: [`LOCAL_OPERATOR_PANEL_QUICK_START.fa.md`](LOCAL_OPERATOR_PANEL_QUICK_START.fa.md)

راهنمای جامع و جزءبه‌جزء رابط کاربری: [`LOCAL_OPERATOR_PANEL_USER_GUIDE.fa.md`](LOCAL_OPERATOR_PANEL_USER_GUIDE.fa.md)

## جریان عملیاتی

```text
source Stage Evidence Bundle
-> optional Local Repository Preflight
-> Project Gate check / transition
-> result.json + report.md + report.html
-> optional downstream input bundle only when output is produced
```

## روش پیشنهادی

1. transition را انتخاب کن.
2. JSON درست را بارگذاری یا paste کن.
3. مسیرهای local checkout لازم را وارد کن.
4. اول `بررسی مسیرها و ورودی‌ها` را بزن.
5. اگر Preflight خطا داشت، مسیر یا فایل ورودی را اصلاح کن.
6. بعد `اجرای بررسی Project Gate` را بزن.

## transitionها و ورودی مورد انتظار

| transition | ورودی JSON مورد انتظار | خروجی مرحله بعد |
|---|---|---|
| `validate_bundle` | هر `Stage Evidence Bundle` برای اعتبارسنجی envelope | ندارد؛ validation-only است. |
| `architect_to_ce` | Architect bundle با `stage=architect` و `ev4-architect-stage-payload@1.0.0` | در صورت موفقیت، CE input bundle با `stage=ce`. |
| `ce_to_builder` | CE bundle با `stage=ce` | فقط با شواهد/checkout معتبر؛ fail-closed. |
| `builder_to_responsive` | Builder bundle با `stage=builder` | فقط با شواهد/checkout معتبر؛ fail-closed. |
| `final_gate` | Responsive/final evidence ورودی مورد انتظار gate نهایی | فقط با شواهد معتبر؛ fail-closed. |
| `inspect_capabilities` | ورودی JSON لازم ندارد | فقط snapshot قابلیت‌ها را نشان می‌دهد. |

## مسیرهای local repository

برای transitionهای واقعی، مسیرها باید پوشه‌های local checkout باشند، نه URL گیت‌هاب.

| transition | مسیرهای لازم |
|---|---|
| `validate_bundle` | مسیر specialist لازم ندارد. |
| `inspect_capabilities` | مسیر repo لازم ندارد. |
| `architect_to_ce` | `architect_repo_path`, `ce_repo_path` |
| `ce_to_builder` | `ce_repo_path`, `builder_repo_path` |
| `builder_to_responsive` | `builder_repo_path`, `responsive_repo_path` |
| `final_gate` | `project_gate_repo_path`, `responsive_repo_path` |

مسیرهای غیرلازم در Preflight خطا حساب نمی‌شوند و با `not_required_for_selected_transition` نمایش داده می‌شوند.

## Preflight چه کار می‌کند؟

بخش `بررسی آماده‌سازی مسیرها / Preflight` یک بررسی سبک و مستقل است. این بخش full transition را اجرا نمی‌کند، اما قبل از اجرای اصلی نشان می‌دهد:

- برای transition انتخاب‌شده کدام مسیرها لازم هستند.
- آیا مسیرهای لازم وجود دارند و directory هستند.
- آیا GitHub URL به‌جای local path وارد شده است.
- آیا checkout شبیه Git checkout است.
- آیا فایل‌های pin‌شده لازم در local checkout دیده می‌شوند.
- آیا JSON شبیه source bundle درست است یا `result.json` قبلی UI است.
- آیا `validate_bundle` فقط validation-only است و خروجی CE/Builder/Responsive نمی‌سازد.

Preflight hash verification، schema validation کامل، اجرای validator رسمی، اجرای adapter رسمی و اصلاح خودکار انجام نمی‌دهد. اجرای واقعی Project Gate همچنان مرجع نهایی است.

## وقتی فایل pin‌شده گم است

در GitHub Desktop:

1. از `Current repository` همان ریپو را انتخاب کن.
2. `Current branch` را روی `main` بگذار.
3. `Fetch origin` را بزن.
4. اگر `Pull origin` ظاهر شد، آن را هم بزن.
5. دوباره Preflight را اجرا کن.

## source bundle و result.json

`result.json` خروجی گزارش UI است، نه ورودی transition بعدی. برای `architect_to_ce` باید source bundle خروجی Architect را بدهی. برای `ce_to_builder` باید خروجی CE از مرحله قبل را بدهی.

## معنی statusها

| status | معنی عملیاتی |
|---|---|
| `accepted` | فقط در محدوده همین gate و evidence موجود پذیرفته شده است. |
| `repair_needed` | بسته قابل فهم است، اما قبل از ادامه باید اصلاح شود. |
| `insufficient_evidence` | evidence، checkout، lock، validator یا فایل رسمی کافی نیست؛ این وضعیت مسدودکننده است. |
| `invalid` | JSON، schema identity، مسیر، hash، transition selection یا اجرای gate نامعتبر است. |

## تفسیر `output: null`

`output: null` یعنی downstream input package تولید نشده است. فایل `result.json` یا report را به‌عنوان ورودی مرحله بعد استفاده نکن.

موارد رایج:

- در `validate_bundle`، `output: null` طبیعی است چون این مسیر transition نیست.
- در خطای schema یا identity، `output: null` یعنی بسته مرحله بعد ساخته نشده است.
- در `insufficient_evidence`، ادامه فقط وقتی امن است که status و evidence scope اجازه دهند.

## استفاده از repair prompt

وقتی diagnostic قابل اصلاح شناخته‌شده باشد، مثل `PG_A2C_ARCHITECT_SCHEMA_VALIDATION_FAILED`، پنل یک بخش `Repair prompt / پرامپت اصلاح` نشان می‌دهد. Project Gate خودش JSON کاربر را اصلاح نمی‌کند، evidence نمی‌سازد، و specialist logic را پیاده‌سازی نمی‌کند.

## این ابزار چه چیزی را نباید ادعا کند

پنل نباید ادعا کند: production readiness، real Elementor validation، frontend correctness، responsive correctness، CE approval، Builder authorization، یا end-to-end EV4 readiness.

شناسه‌های فنی مثل `diagnostic code`، `JSONPath`، `schema id`، `repo path`، `hash` و `transition id` باید LTR و copyable بمانند.

جزئیات بیشتر: `docs/LOCAL_REPOSITORY_PREFLIGHT.md`.
