# PROMPT-08 Handoff — Local Operator Panel User Guide

```yaml
prompt: PROMPT-08
scope: documentation_only
branch: project-gate-prompt-08-operator-user-guide
base_branch: main
base_sha: 4598f51fd8599e4ca77d4760431d646af4d7b93f
status: ready_for_review
```

## هدف

افزودن یک راهنمای فارسی جامع و جزءبه‌جزء برای پنل محلی `EV4 Project Gate` بر اساس UI و service implementation موجود، بدون تغییر در transition semantics، schemaها، validatorها، adapterها یا capability truth.

## Commitها

| Commit | شرح |
|---|---|
| `7dd4755c6e01faebe1fa2d8d98d2eab9d75eec65` | افزودن راهنمای جامع پنل محلی |
| `1f1b935ad2395801a8a01334d7c4d8997a6bbf0f` | لینک دادن راهنمای جامع از `docs/OPERATOR_GUIDE.md` |
| `584defa6921fb8ee156c5a72771cc08e5301f5b4` | افزودن راهنما به فهرست اسناد مرتبط پنل |

## فایل‌های تغییرکرده

- `docs/LOCAL_OPERATOR_PANEL_USER_GUIDE.fa.md` — فایل جدید؛ توضیح 61 جزء رابط، جریان استفاده، statusها، Diagnostics، Capabilities، outputها، خطاهای رایج و troubleshooting.
- `docs/OPERATOR_GUIDE.md` — افزودن لینک مستقیم به راهنمای جامع.
- `docs/UI_OPERATOR_PANEL.md` — افزودن راهنما به اسناد مرتبط.
- `docs/handoffs/PROMPT-08_HANDOFF.md` — این handoff.

## شواهد و منابع بررسی‌شده

- `src/ev4_transition/ui/app.py`
- `src/ev4_transition/ui/adapters.py`
- `src/ev4_transition/ui/components.py`
- `src/ev4_transition/ui/preflight_components.py`
- `src/ev4_transition/ui/state.py`
- `src/ev4_transition/service/preflight_core.py`
- `src/ev4_transition/data/capability-status.v1.json`
- `docs/OPERATOR_GUIDE.md`
- `docs/UI_OPERATOR_PANEL.md`
- `docs/UI_SERVICE_CONTRACT.md`
- تصویر UI ارائه‌شده توسط مالک پروژه در گفتگو

## تست‌ها و بررسی‌ها

### انجام‌شده

- تطبیق متن راهنما با componentهای قابل مشاهده در `src/ev4_transition/ui/app.py`.
- تطبیق path requirementها و Preflight با service code و operator docs.
- حفظ تفکیک `result.json` از downstream artifact.
- حفظ fail-closed semantics برای `insufficient_evidence`.
- حفظ boundary: راهنما capability، evidence یا readiness claim جدیدی ایجاد نمی‌کند.

### اجرا نشده

هیچ test suite یا GitHub Actions اجرا نشد، چون این تغییر documentation-only است و کد اجرایی، schema، workflow یا dependency را تغییر نمی‌دهد.

```yaml
tests_run: []
tests_not_run:
  - pytest
  - UI runtime smoke
  - GitHub Actions
reason: documentation-only change
```

## Behavioral Rule Coverage

هیچ behavioral rule به status بالاتری ارتقا داده نشد.

```yaml
coverage_advanced: []
coverage_unchanged: true
new_validator: false
new_fixture: false
new_ci_enforcement: false
new_downstream_contract: false
```

## Diagnostics و CLI/CI

```yaml
new_diagnostics: []
cli_changes: none
ci_changes: none
schema_changes: none
transition_semantics_changes: none
```

## تصمیم‌های طراحی

1. راهنمای جامع به‌صورت فایل مستقل اضافه شد تا `docs/OPERATOR_GUIDE.md` به‌عنوان quick operational guide کوتاه باقی بماند.
2. راهنما بر اساس ترتیب بصری صفحه نوشته شد و 61 جزء اصلی را از بالا به پایین پوشش می‌دهد.
3. technical identifierها، pathها، statusها و codeها به‌صورت LTR و copyable نگه داشته شدند.
4. limitationهای فعلی با زبان fail-closed توضیح داده شدند و هیچ مسیر موفقیت یا evidence فرضی اضافه نشد.
5. `result.json` صریحاً به‌عنوان report artifact معرفی شد، نه ورودی خودکار مرحله بعد.

## Web sources

استفاده نشد. مبنا repository code، repository docs و تصویر UI بود.

## گپ‌ها و `insufficient_evidence`

- browser accessibility certification همچنان `insufficient_evidence` است.
- real non-synthetic handoff evidence برای transitionهای ثبت‌شده همچنان خارج از محدوده این تغییر و `insufficient_evidence` است.
- این تغییر documentation-only است و هیچ evidence gap را نمی‌بندد.

## اقدام بعدی مجاز

1. review محتوای فارسی و لینک‌ها در pull request.
2. در صورت نیاز، اجرای markdown/link check موجود repository توسط CI یا reviewer.
3. merge فقط با تصمیم صریح مالک پروژه.
