# Operator Panel Manual QA Checklist

این checklist قبل از usable دانستن پنل محلی برای personal local operation اجرا می‌شود. این QA production readiness یا accessibility certification نیست.

## 1. UI launch

- setup: در checkout محلی `uv sync --extra dev --extra ui` و سپس `uv run python -m ev4_transition.ui.app` را اجرا کن.
- expected result: صفحه `EV4 Project Gate Local Operator Panel` بدون traceback باز شود.
- failure sign: import/runtime traceback، blank page، یا پیام مبهم درباره `gradio`.

## 2. Visual layout and header

- setup: صفحه اصلی را در مرورگر باز کن.
- expected result: header compact، کارت‌مانند، خوانا و بدون بلوک خام/سنگین باشد.
- failure sign: header خیلی بزرگ، متن فشرده، یا ظاهر raw Gradio.

## 3. Persian RTL

- setup: بخش‌های header، Preflight، خلاصه نتیجه و راهنمای عملیاتی را نگاه کن.
- expected result: متن فارسی راست‌چین و RTL باشد.
- failure sign: متن فارسی چپ‌چین، شکسته یا با ترتیب mixed-language گیج‌کننده دیده شود.

## 4. Technical LTR isolation

- setup: diagnostic code، path، JSONPath، repo name و `result.json` preview را بررسی کن.
- expected result: technical identifiers با LTR isolation و copyable نمایش داده شوند.
- failure sign: path یا code در متن فارسی به‌هم‌ریخته، معکوس، یا غیرقابل کپی باشد.

## 5. Theme/dark-mode readability

- setup: سیستم/مرورگر را در dark mode قرار بده و صفحه را refresh کن.
- expected result: surfaceها near-black باشند، متن خوانا باشد، focus ring و code background دیده شود.
- failure sign: pure black/white inversion، contrast ضعیف، یا statusهای color-only.

## 6. Validate bundle flow

- setup: `Validate Stage Evidence Bundle` را با یک Stage Evidence Bundle معتبر یا fixture شناخته‌شده اجرا کن.
- expected result: UI توضیح دهد validation-only است و CE output نمی‌سازد.
- failure sign: کاربر فکر کند `validate_bundle` خروجی مرحله بعد تولید کرده است.

## 7. Architect → CE missing path flow

- setup: `Architect → CE` را با JSON مناسب ولی بدون `architect_repo_path` یا `ce_repo_path` اجرا/Preflight کن.
- expected result: خطای مسیر local واضح، action دقیق و `output: null` دیده شود.
- failure sign: GitHub URL به‌عنوان کافی پذیرفته شود یا خطای مبهم filesystem نشان داده شود.

## 8. Architect → CE stale checkout / pinned file missing flow

- setup: مسیر repo موجود ولی ناقص/stale بده که فایل pin‌شده در آن نیست.
- expected result: Preflight missing pinned file را نشان دهد و GitHub Desktop fetch/pull guidance بدهد.
- failure sign: خطا به‌صورت accepted یا warning غیرمسدودکننده نمایش داده شود.

## 9. Architect → CE invalid Architect schema flow

- setup: Architect bundle با schema violation شناخته‌شده اجرا کن.
- expected result: diagnostic `PG_A2C_ARCHITECT_SCHEMA_VALIDATION_FAILED`، توضیح فارسی، repair prompt و `output: null` نمایش داده شود.
- failure sign: خروجی CE ساخته شود یا خطا بدون مسیر/اقدام دقیق نمایش داده شود.

## 10. Output produced flow

- setup: یک run معتبر `architect_to_ce` با owner checkouts و evidence لازم اجرا کن.
- expected result: اگر `output.stage == "ce"` باشد، UI بگوید CE input bundle تولید شده و scope warning را حفظ کند.
- failure sign: خروجی با production/frontend/readiness proof اشتباه گرفته شود.

## 11. Report downloads

- setup: پس از run، `result.json`, `report.md`, `report.html` را دانلود و باز کن.
- expected result: status، guidance، Preflight summary در صورت وجود، grouped diagnostics، raw diagnostics و raw JSON result وجود داشته باشد.
- failure sign: raw JSON حذف شده، HTML بدون `dir="rtl"` است، یا code blockها LTR نیستند.

## 12. No false readiness claims

- setup: همه متن‌های header، summary، docs و report را مرور کن.
- expected result: هشدار محدوده درباره نبود production/frontend/Elementor/Responsive readiness حفظ شده باشد.
- failure sign: متن‌هایی مثل production-ready، frontend correct، real Elementor validated، CE approved یا Builder authorized دیده شود.

## 13. Keyboard/focus sanity

- setup: با keyboard بین controls حرکت کن.
- expected result: focus ring واضح باشد و fieldهای LTR/RTL رفتار قابل پیش‌بینی داشته باشند.
- failure sign: focus نامرئی، tab order گیج‌کننده، یا ورود path/JSON با جهت اشتباه.
