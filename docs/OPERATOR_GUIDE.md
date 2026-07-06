# Operator Guide — EV4 Project Gate Local Panel

این سند راهنمای استفاده از پنل محلی Project Gate است. پنل فقط یک لایه انسانی برای اجرای بررسی‌های Project Gate است و منطق transition، schema، validator یا قرارداد specialist جدید ایجاد نمی‌کند.

## اصل عملیاتی

```text
source Stage Evidence Bundle
-> Project Gate check / transition
-> result.json + report.md + report.html
-> optional downstream input bundle only when output is produced
```

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
| `architect_to_ce` | `architect_repo_path`, `ce_repo_path` |
| `ce_to_builder` | `ce_repo_path`, `builder_repo_path` |
| `builder_to_responsive` | `builder_repo_path`, `responsive_repo_path` |
| `final_gate` | `project_gate_repo_path`, `responsive_repo_path` |

اگر مسیر خالی، URL، اشتباه یا ناقص باشد، پنل باید آن را در «راهنمای عملیاتی» توضیح دهد و نباید ادامه را موفق نشان دهد.

## معنی statusها

| status | معنی عملیاتی |
|---|---|
| `accepted` | فقط در محدوده همین gate و evidence موجود پذیرفته شده است. |
| `repair_needed` | بسته قابل فهم است، اما قبل از ادامه باید اصلاح شود. |
| `insufficient_evidence` | evidence، checkout، lock، validator یا فایل رسمی کافی نیست؛ این وضعیت مسدودکننده است. |
| `invalid` | JSON، schema identity، مسیر، hash، transition selection یا اجرای gate نامعتبر است. |

## تفسیر `output: null`

`output: null` یعنی downstream input package تولید نشده است. کاربر نباید فایل `result.json` یا report را به‌عنوان ورودی مرحله بعد استفاده کند.

موارد رایج:

- در `validate_bundle`، `output: null` طبیعی است چون این مسیر transition نیست.
- در خطای schema یا identity، `output: null` یعنی بسته مرحله بعد ساخته نشده است.
- در `insufficient_evidence`، ادامه فقط وقتی امن است که status و evidence scope اجازه دهند.

## استفاده از repair prompt

وقتی diagnostic قابل اصلاح شناخته‌شده باشد، مثل `PG_A2C_ARCHITECT_SCHEMA_VALIDATION_FAILED`، پنل یک بخش `Repair prompt / پرامپت اصلاح` نشان می‌دهد. Project Gate خودش JSON کاربر را اصلاح نمی‌کند، evidence نمی‌سازد، و specialist logic را پیاده‌سازی نمی‌کند.

## این ابزار چه چیزی را نباید ادعا کند

پنل نباید ادعا کند: production readiness، real Elementor validation، frontend correctness، responsive correctness، CE approval، Builder authorization، یا end-to-end EV4 readiness.

شناسه‌های فنی مثل `diagnostic code`، `JSONPath`، `schema id`، `repo path`، `hash` و `transition id` باید LTR و copyable بمانند.
