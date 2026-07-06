# Local Repository Preflight

این سند رفتار بخش `بررسی آماده‌سازی مسیرها / Preflight` در پنل محلی Project Gate را توضیح می‌دهد.

## هدف

Preflight یک بررسی سبک و read-only است که قبل از اجرای اصلی انجام می‌شود تا خطاهای قابل پیشگیری زودتر دیده شوند.

```text
JSON + selected transition + local paths
-> Preflight
-> readable setup checklist
-> optional full Project Gate run
```

Preflight اجرای کامل Project Gate نیست و transition output نمی‌سازد.

## چه چیزهایی بررسی می‌شود؟

- مسیرهای لازم برای transition انتخاب‌شده.
- وجود داشتن مسیر local روی filesystem.
- directory بودن مسیر.
- اینکه مقدار واردشده GitHub URL نباشد.
- وجود نشانه `.git` به‌عنوان هشدار سبک برای checkout بودن پوشه.
- وجود فایل‌های pin‌شده در lock manifest مربوط به transition.
- شکل کلی JSON و `stage` مورد انتظار.
- تشخیص اینکه فایل بارگذاری‌شده `result.json` قبلی UI نباشد.
- هشدار validation-only برای `validate_bundle`.

## چه چیزهایی بررسی نمی‌شود؟

Preflight عمداً این موارد را انجام نمی‌دهد:

- `git pull`, `git checkout`, `git clone` یا هر mutation دیگر.
- hash verification.
- schema validation کامل.
- اجرای validator رسمی specialistها.
- اجرای adapter رسمی specialistها.
- اصلاح خودکار JSON.
- ساخت خروجی CE/Builder/Responsive.

Hash، identity، schema و validator همچنان در اجرای واقعی Gate مرجع نهایی هستند.

## مسیرهای مورد انتظار

| transition | مسیرهای لازم |
|---|---|
| `validate_bundle` | هیچ مسیر specialist لازم نیست. |
| `inspect_capabilities` | JSON و مسیر repo لازم نیست. |
| `architect_to_ce` | `architect_repo_path`, `ce_repo_path` |
| `ce_to_builder` | `ce_repo_path`, `builder_repo_path` |
| `builder_to_responsive` | `builder_repo_path`, `responsive_repo_path` |
| `final_gate` | `project_gate_repo_path`, `responsive_repo_path` |

مسیرهای غیرلازم اگر پر شده باشند، error حساب نمی‌شوند و با classification برابر `not_required_for_selected_transition` نشان داده می‌شوند.

## چرا GitHub URL پذیرفته نمی‌شود؟

Project Gate برای اجرای local باید فایل‌های schema، validator، contract و fixture را از filesystem بخواند. بنابراین این مقدار درست نیست:

```text
https://github.com/rezahh107/EV4-Constructability-Engineer-Repo
```

باید مسیر پوشه checkout محلی را بدهی، مثل:

```text
C:\Users\reza\Documents\GitHub\EV4-Constructability-Engineer-Repo
```

## workflow پیشنهادی برای GitHub Desktop

وقتی Preflight می‌گوید فایل pin‌شده گم است:

1. در GitHub Desktop، از `Current repository` همان ریپو را انتخاب کن.
2. `Current branch` را روی `main` بگذار.
3. `Fetch origin` را بزن.
4. اگر `Pull origin` ظاهر شد، آن را هم بزن.
5. دوباره Preflight را اجرا کن.

CLI اختیاری برای کاربر پیشرفته:

```bash
git status
git checkout main
git pull --ff-only
```

## source bundle با result.json فرق دارد

`result.json` خروجی گزارش Project Gate UI است. برای transition بعدی، معمولاً باید source bundle همان stage را بدهی، نه result قبلی UI.

نمونه اشتباه برای `architect_to_ce`:

```json
{
  "schema_version": "ev4-project-gate-ui-result.v1",
  "result_type": "service_response"
}
```

برای `architect_to_ce` ورودی باید bundle خروجی Architect با `stage=architect` باشد.

برای `ce_to_builder` ورودی باید خروجی CE از مرحله قبل با `stage=ce` باشد.

## classificationها

| classification | معنی |
|---|---|
| `missing` | مسیر یا JSON لازم وارد نشده است. |
| `exists` | مسیر local وجود دارد. |
| `does_not_exist` | مسیر local روی filesystem پیدا نشد. |
| `looks_like_github_url` | به‌جای مسیر local، URL وارد شده است. |
| `not_directory` | مسیر به فایل اشاره می‌کند، نه پوشه. |
| `not_git_checkout` | پوشه هست، اما `.git` دیده نشد. |
| `unexpected_repository` | تقریباً همه فایل‌های pin‌شده مورد انتظار در آن پوشه نیست. |
| `required_file_missing` | بعضی فایل‌های pin‌شده لازم گم هستند. |
| `ok` | check مربوطه در محدوده Preflight مشکلی نشان نداد. |
| `not_required_for_selected_transition` | مسیر برای transition انتخاب‌شده لازم نیست. |
| `wrong_input_type` | فایل ورودی از نوع نتیجه UI است، نه source bundle. |
| `wrong_stage_for_transition` | مقدار `stage` با transition انتخاب‌شده نمی‌خواند. |
| `validation_only_no_transition_output` | `validate_bundle` خروجی مرحله بعد نمی‌سازد. |

## statusهای Preflight

| status | معنی |
|---|---|
| `ready` | required checks در محدوده Preflight پاس شده‌اند. |
| `warnings` | خطای required وجود ندارد، اما هشدار یا ابهام هست. |
| `blocked` | حداقل یک check لازم error دارد؛ اجرای اصلی احتمالاً شکست می‌خورد. |

## هشدار محدوده

Preflight فقط برای کاهش خطاهای تکراری local setup است. اگر Preflight سبز شد، هنوز ادعای `accepted`، production readiness، frontend correctness، Responsive correctness یا Elementor validation واقعی ایجاد نمی‌شود.
