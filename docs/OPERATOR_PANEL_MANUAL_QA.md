# Operator Panel Manual QA Checklist

این checklist قبل از usable دانستن پنل محلی برای personal local operation اجرا می‌شود. این QA production readiness یا accessibility certification نیست.

## 1. UI launch

- setup: در checkout محلی `uv sync --extra dev --extra ui` و سپس `uv run python -m ev4_transition.ui.app` را اجرا کن.
- expected result: صفحه `EV4 Project Gate Local Operator Panel` بدون traceback باز شود.
- failure sign: import/runtime traceback، blank page، یا پیام مبهم درباره `gradio`.

## 2. Light mode readability

- setup: در Settings یا مرورگر، Light Mode را انتخاب کن و صفحه را refresh کن.
- expected result: header، radio labelها، primary button، secondary buttons، upload area، textarea، accordion headerها، footer و Settings modal خوانا باشند.
- failure sign: متن خاکستری کم‌رنگ روی سفید/خاکستری، مرز input نامشخص، button text کم‌کنتراست، یا accordion label کم‌رنگ.

## 3. Dark mode readability

- setup: در Settings یا مرورگر، Dark Mode را انتخاب کن و صفحه را refresh کن.
- expected result: surfaceها near-black/layered باشند، متن اصلی و ثانویه خوانا باشد، primary button foreground/background واضح باشد، focus ring و code background دیده شود.
- failure sign: pure black/white inversion، dark text on dark background، gray-on-gray controls، یا statusهای color-only.

## 4. System mode behavior

- setup: System Mode را انتخاب کن، OS/browser را بین Light و Dark تغییر بده، سپس refresh کن.
- expected result: Gradio theme و EV4 custom tokens با هم تغییر کنند و mixed-theme دیده نشود.
- failure sign: بعضی بخش‌ها Light و بعضی بخش‌ها Dark بمانند، مخصوصاً transition radio group، JSON textarea یا Settings modal.

## 5. Settings modal

- setup: Settings modal را در Light و Dark باز کن.
- expected result: title، theme buttons، language select، section headings، توضیحات Screen Studio/PWA و disabled controls قابل خواندن باشند.
- failure sign: متن modal تقریباً ناپدید شود، disabled controls به‌خاطر opacity stack ناخوانا شوند، یا background/foreground از theme اصلی جدا شود.

## 6. Persian RTL

- setup: بخش‌های header، Preflight، خلاصه نتیجه و راهنمای عملیاتی را نگاه کن.
- expected result: متن فارسی راست‌چین و RTL باشد.
- failure sign: متن فارسی چپ‌چین، شکسته یا با ترتیب mixed-language گیج‌کننده دیده شود.

## 7. Technical LTR isolation

- setup: diagnostic code، path، JSONPath، repo name و `result.json` preview را بررسی کن.
- expected result: technical identifiers با LTR isolation و copyable نمایش داده شوند.
- failure sign: path یا code در متن فارسی به‌هم‌ریخته، معکوس، یا غیرقابل کپی باشد.

## 8. Upload, textarea, radio and accordion states

- setup: روی upload area، JSON textarea، radio labelها و accordionها hover/focus کن.
- expected result: default، hover، focus، selected و collapsed states در هر دو theme قابل تشخیص باشند.
- failure sign: radio label کم‌کنتراست، upload boundary نامشخص، textarea mixed-theme، یا accordion collapsed label ناخوانا.

## 9. Disabled states

- setup: Settings modal و هر control غیرفعال را در Light و Dark بررسی کن.
- expected result: disabled state از active state قابل تشخیص باشد اما متن/label اصلی همچنان خوانا بماند.
- failure sign: opacity باعث ناپدید شدن متن شود یا disabled control با panel background یکی شود.

## 10. Keyboard/focus sanity

- setup: با keyboard بین controls حرکت کن.
- expected result: focus ring واضح باشد و fieldهای LTR/RTL رفتار قابل پیش‌بینی داشته باشند.
- failure sign: focus نامرئی، tab order گیج‌کننده، یا ورود path/JSON با جهت اشتباه.

## 11. Validate bundle flow

- setup: `Validate Stage Evidence Bundle` را با یک Stage Evidence Bundle معتبر یا fixture شناخته‌شده اجرا کن.
- expected result: UI توضیح دهد validation-only است و CE output نمی‌سازد.
- failure sign: کاربر فکر کند `validate_bundle` خروجی مرحله بعد تولید کرده است.

## 12. Architect → CE missing path flow

- setup: `Architect → CE` را با JSON مناسب ولی بدون `architect_repo_path` یا `ce_repo_path` اجرا/Preflight کن.
- expected result: خطای مسیر local واضح، action دقیق و `output: null` دیده شود.
- failure sign: GitHub URL به‌عنوان کافی پذیرفته شود یا خطای مبهم filesystem نشان داده شود.

## 13. Architect → CE stale checkout / pinned file missing flow

- setup: مسیر repo موجود ولی ناقص/stale بده که فایل pin‌شده در آن نیست.
- expected result: Preflight missing pinned file را نشان دهد و GitHub Desktop fetch/pull guidance بدهد.
- failure sign: خطا به‌صورت accepted یا warning غیرمسدودکننده نمایش داده شود.

## 14. Architect → CE invalid Architect schema flow

- setup: Architect bundle با schema violation شناخته‌شده اجرا کن.
- expected result: diagnostic `PG_A2C_ARCHITECT_SCHEMA_VALIDATION_FAILED`، توضیح فارسی، repair prompt و `output: null` نمایش داده شود.
- failure sign: خروجی CE ساخته شود یا خطا بدون مسیر/اقدام دقیق نمایش داده شود.

## 15. Output produced flow

- setup: یک run معتبر `architect_to_ce` با owner checkouts و evidence لازم اجرا کن.
- expected result: اگر `output.stage == "ce"` باشد، UI بگوید CE input bundle تولید شده و scope warning را حفظ کند.
- failure sign: خروجی با production/frontend/readiness proof اشتباه گرفته شود.

## 16. Report downloads

- setup: پس از run، `result.json`, `report.md`, `report.html` را دانلود و باز کن.
- expected result: status، guidance، Preflight summary در صورت وجود، grouped diagnostics، raw diagnostics و raw JSON result وجود داشته باشد.
- failure sign: raw JSON حذف شده، HTML بدون `dir="rtl"` است، یا code blockها LTR نیستند.

## 17. No false readiness claims

- setup: همه متن‌های header، summary، docs و report را مرور کن.
- expected result: هشدار محدوده درباره نبود production/frontend/Elementor/Responsive readiness حفظ شده باشد.
- failure sign: متن‌هایی مثل production-ready، frontend correct، real Elementor validated، CE approved یا Builder authorized دیده شود.

## 18. Evidence recording

- after QA: screenshotهای Light، Dark و Settings modal را کنار نام branch/head SHA نگه دار.
- browser visual validation تا وقتی screenshot/manual evidence ثبت نشده، `insufficient_evidence` باقی می‌ماند.
