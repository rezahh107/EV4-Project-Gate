# PROMPT-08 Handoff — Local Operator Panel User Guide

```yaml
prompt: PROMPT-08
action_kind: repair_and_verify
scope: documentation_only
branch: project-gate-prompt-08-operator-user-guide
base_branch: main
base_sha: 4598f51fd8599e4ca77d4760431d646af4d7b93f
reviewed_head_sha: 3b153bd9d2e1721b1dd889f87f0779abb2102332
repair_content_head_sha: 7a55723ceab73153dd626b94fd7b40b47502ca1c
finding_status: implemented_pending_rereview
merge_performed: false
approval_performed: false
deployment_performed: false
```

## هدف

افزودن مستندات فارسی کاربردی برای پنل محلی `EV4 Project Gate` بر اساس UI و service implementation موجود، بدون تغییر در transition semantics، schemaها، validatorها، adapterها یا capability truth.

این scope دو سطح دارد:

1. مرجع جامع و جزءبه‌جزء برای تمام componentهای UI؛
2. شروع سریع کوتاه برای استفاده شخصی و روزمره، تصمیم‌گیری بر اساس هدف، status و artifact.

این handoff همچنین تعمیر finding رسمی `PRF-001` را ثبت می‌کند. این ثبت به معنی بسته‌شدن نهایی finding نیست؛ تصمیم نهایی فقط پس از PR Inspector re-review روی exact head جدید معتبر است.

## Commitها

| Commit | شرح |
|---|---|
| `7dd4755c6e01faebe1fa2d8d98d2eab9d75eec65` | افزودن راهنمای جامع پنل محلی |
| `1f1b935ad2395801a8a01334d7c4d8997a6bbf0f` | لینک دادن راهنمای جامع از `docs/OPERATOR_GUIDE.md` |
| `584defa6921fb8ee156c5a72771cc08e5301f5b4` | افزودن راهنما به فهرست اسناد مرتبط پنل |
| `1e001673a91bc28397648ce326b6fd338dd3c99f` | افزودن شروع سریع شخصی و task-oriented |
| `0de96388841fa85e96a62a20424e50413f35b698` | لینک دادن شروع سریع از Operator Guide |
| `c3e5723907d3589517decaf32b87dcba346ed65b` | افزودن شروع سریع به اسناد مرتبط UI |
| `c53888361903d3a63c0af37f299bf61762d6160b` | اصلاح command نصب fallback در سند UI |
| `d0fe1fad98dea8afe9d0c15b741b482ffb4aa4a5` | تعمیر سناریوی A2C و ممنوعیت استفاده از UI report/nested output |
| `7a55723ceab73153dd626b94fd7b40b47502ca1c` | هم‌راستاسازی Operator Guide با artifactهای مستقل A2C و C2B |

## فایل‌های تغییرکرده

- `docs/LOCAL_OPERATOR_PANEL_USER_GUIDE.fa.md` — توضیح 61 جزء رابط، جریان استفاده، statusها، Diagnostics، Capabilities، outputها، خطاهای رایج و troubleshooting؛ تعمیر مرز artifact در سناریوی A2C.
- `docs/LOCAL_OPERATOR_PANEL_QUICK_START.fa.md` — شروع سریع پنج‌دقیقه‌ای، جدول انتخاب transition، جدول اقدام بعد از status، قواعد artifact و خطاهای سریع.
- `docs/OPERATOR_GUIDE.md` — لینک مستقیم به شروع سریع و راهنمای جامع؛ الزام standalone `ce-input.json` و `builder-input.json`.
- `docs/UI_OPERATOR_PANEL.md` — افزودن شروع سریع و راهنمای جامع به اسناد مرتبط.
- `docs/handoffs/PROMPT-08_HANDOFF.md` — این handoff و evidence تعمیر.

## PRF-001 — Invariant Extraction

```yaml
finding_id: PRF-001
status: implemented_pending_rereview
severity: MEDIUM
blocking_at_reviewed_head: true
surface_symptom: >-
  بخش 4.2 راهنمای جامع به اپراتور می‌گفت output تولیدشده UI را برای CE استفاده کند.
underlying_invariant: >-
  UI result و nested result.output فقط report/diagnostic evidence هستند؛ CE semantic input
  باید standalone ce-input.json باشد که workflow رسمی A2C آن را canonical، atomic و
  post-write-verified منتشر می‌کند. Receipt باید جدا بماند.
failure_boundary: >-
  مرز انتشار Project Gate به CE؛ هر extraction یا forwarding از UI report، publication و
  post-write verification رسمی را دور می‌زند.
affected_components:
  - docs/LOCAL_OPERATOR_PANEL_USER_GUIDE.fa.md
  - docs/OPERATOR_GUIDE.md
assumptions:
  - docs/PG_A2C_OPERATOR_WORKFLOW.md در exact reviewed head مرجع رسمی A2C است.
  - docs/PG_C2B_OPERATOR_WORKFLOW.md در exact reviewed head مرجع رسمی C2B است.
  - هیچ runtime/schema/validator/workflow change برای این تعمیر لازم نیست.
```

## تعمیر انجام‌شده

- دستور مبهم «استفاده از output تولیدشده برای CE» حذف شد.
- `result.json` و `result.output` صریحاً به‌عنوان CE semantic input ممنوع شدند.
- سناریوی A2C اکنون اجرای `docs/PG_A2C_OPERATOR_WORKFLOW.md` را الزام می‌کند.
- فقط standalone `ce-input.json` به CE تحویل داده می‌شود.
- `project-gate-a2c-receipt.json` جدا برای audit و diagnosis باقی می‌ماند.
- Operator Guide نیز برای جلوگیری از drift مجدد، A2C را به `ce-input.json` و C2B را به `builder-input.json` محدود می‌کند.
- ممنوعیت extraction، reconstruction و evidence mixing در Quick Start ضعیف نشد.
- diagnostic واقعی `PG.UI.PREFLIGHT_WRONG_STAGE_FOR_TRANSITION` حفظ شد و پیشنهاد خارجی نادرست برای جایگزینی آن پذیرفته نشد.

## Adjacent Impact Audit

| سطح | نتیجه |
|---|---|
| runtime callers | تغییری ندارد؛ documentation-only |
| service/API | تغییری ندارد |
| schemas/contracts | تغییری ندارد |
| validators/adapters | تغییری ندارد |
| fixtures | تغییری ندارد |
| CLI behavior | تغییری ندارد؛ فقط workflow رسمی موجود مستند شده است |
| UI behavior | تغییری ندارد |
| CI configuration | تغییری ندارد |
| release locks/pins | تغییری ندارد |
| compatibility | semantics موجود حفظ شد |
| rollback | revert دو commit تعمیر مستندات؛ runtime rollback لازم نیست |

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
- `docs/PG_A2C_OPERATOR_WORKFLOW.md`
- `docs/PG_C2B_OPERATOR_WORKFLOW.md`
- تصویر UI ارائه‌شده توسط مالک پروژه در گفتگو

### شواهد قرارداد artifact

`docs/PG_A2C_OPERATOR_WORKFLOW.md` در exact reviewed head اعلام می‌کند:

- `ce-input.json` و `project-gate-a2c-receipt.json` دو فایل جدا هستند؛
- اپراتور نباید nested JSON یا `result.output` را استخراج کند؛
- مرحله بعد فقط standalone `ce-input.json` است.

`docs/PG_C2B_OPERATOR_WORKFLOW.md` در exact reviewed head اعلام می‌کند:

- `builder-input.json` و `project-gate-c2b-receipt.json` دو فایل جدا هستند؛
- اپراتور نباید `result.output` یا envelope تو‌در‌تو را inspect کند؛
- مرحله بعد فقط standalone `builder-input.json` است.

## Validation

### Direct documentation audit

پنج فایل تغییرکرده PR بررسی شدند:

| فایل | نتیجه artifact-boundary audit |
|---|---|
| `docs/LOCAL_OPERATOR_PANEL_USER_GUIDE.fa.md` | A2C فقط standalone `ce-input.json`؛ `result.json` و `result.output` ممنوع |
| `docs/LOCAL_OPERATOR_PANEL_QUICK_START.fa.md` | extraction/reconstruction ممنوع؛ A2C و C2B به artifactهای مستقل اشاره می‌کنند |
| `docs/OPERATOR_GUIDE.md` | A2C فقط `ce-input.json` و C2B فقط `builder-input.json` |
| `docs/UI_OPERATOR_PANEL.md` | فقط download/report behavior را توصیف می‌کند و downstream semantic use را مجاز نمی‌کند |
| `docs/handoffs/PROMPT-08_HANDOFF.md` | مرز report/receipt/artifact و وضعیت rereview را ثبت می‌کند |

### Diff scope

مقایسه exact reviewed head با repair content head:

```yaml
base: 3b153bd9d2e1721b1dd889f87f0779abb2102332
head: 7a55723ceab73153dd626b94fd7b40b47502ca1c
commits: 2
files:
  - docs/LOCAL_OPERATOR_PANEL_USER_GUIDE.fa.md
  - docs/OPERATOR_GUIDE.md
runtime_files_changed: 0
```

### Exact-head workflow evidence پیش از تعمیر

روی reviewed head `3b153bd9d2e1721b1dd889f87f0779abb2102332` این workflowها observed success بودند:

| Workflow | Run ID | Result |
|---|---:|---|
| `Prompt 06 Report UX` | `29656039134` | success |
| `UI Runtime Smoke` | `29656039157` | success |
| `Prompt 05 Builder Responsive Final Gate` | `29656039154` | success |
| `Skeleton Health` | `29656039144` | success |

این successها evidence reviewed head هستند و به‌تنهایی repair head را تأیید نمی‌کنند.

### تست‌های محلی

هیچ local test suite اجرا نشد؛ execution environment محلی repository در این اقدام استفاده نشد. تغییرات documentation-only هستند، اما این دلیل جایگزین exact-head CI نیست.

```yaml
tests_run:
  - direct_documentation_artifact_boundary_audit
  - exact_diff_scope_comparison
tests_not_run:
  - local_pytest
  - local_ui_runtime_smoke
  - local_markdown_link_check
reason: no local repository execution environment used
```

## Exact-head Verification State

```yaml
repair_content_head: 7a55723ceab73153dd626b94fd7b40b47502ca1c
exact_head_ci: pending_observation_after_handoff_commit
fresh_pr_inspector_review: required_not_yet_observed
technical_acceptance: not_claimed
finding_final_closure: not_claimed
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

1. راهنمای جامع به‌عنوان UI Reference حفظ شد.
2. شروع سریع در فایل مستقل باقی ماند تا کاربر شخصی مجبور به مرور راهنمای بلند نباشد.
3. procedureها کوتاه، شماره‌دار و action-oriented باقی ماندند.
4. report output و downstream semantic artifact به‌صورت صریح جدا شدند.
5. برای A2C و C2B فقط workflowهای رسمی repository مسیر تولید artifact مستقل هستند.
6. receiptها فقط evidence/audit هستند و با semantic input ترکیب نمی‌شوند.
7. limitationهای فعلی و fail-closed semantics بدون overclaim حفظ شدند.

## Web sources

منابع زیر در 2026-07-18 برای ساختار راهنمای شخصی بررسی شدند:

- Google Developer Documentation Style Guide — Procedures: `https://developers.google.com/style/procedures`
- Microsoft Style Guide — Writing step-by-step instructions: `https://learn.microsoft.com/en-us/style-guide/procedures-instructions/writing-step-by-step-instructions`
- Diátaxis — How-to guides: `https://diataxis.fr/how-to-guides/`

برای تعمیر `PRF-001` منبع authoritative، فایل‌های live repository و exact reviewed-head workflow contracts بودند؛ web source جدیدی لازم نبود.

## گپ‌ها و `insufficient_evidence`

- fresh PR Inspector review روی exact head جدید هنوز مشاهده نشده است.
- exact-head CI پس از commit نهایی handoff باید جداگانه مشاهده شود.
- browser accessibility certification همچنان `insufficient_evidence` است.
- real non-synthetic handoff evidence همچنان `insufficient_evidence` است.
- این تعمیر documentation-only هیچ evidence gap اجرایی را نمی‌بندد.

## اقدام بعدی مجاز

1. exact PR head را پس از این handoff update ثبت کن.
2. workflowهای GitHub Actions همان exact head را مشاهده و نتیجه را ثبت کن.
3. PR Inspector v1.11.1 را روی exact head جدید دوباره اجرا کن.
4. finding را فقط `implemented_pending_rereview` نگه دار تا review مستقل نتیجه دهد.
5. merge فقط با تصمیم صریح مالک و پس از re-review معتبر.
