# EV4 Project Gate Local Operator Panel

این سند محدوده پنل محلی اپراتور را توضیح می‌دهد. این UI یک لایه انسانی برای اجرای بررسی‌های Project Gate است؛ منطق transition جدید، validator جدید، adapter جدید، schema جدید یا claim جدید درباره production/readiness ایجاد نمی‌کند.

## هدف

کاربر غیر CLI بتواند از طریق یک رابط ساده:

- فایل JSON را upload کند؛
- متن JSON را paste کند؛
- قابلیت‌های Project Gate را بخواند؛
- transitionهای آماده و pending را از هم تشخیص دهد؛
- وضعیت فارسی، راهنمای عملیاتی، diagnostics، و خروجی‌های قابل دانلود را ببیند.

## اجرای محلی

```bash
uv sync --extra dev --extra ui
uv run python -m ev4_transition.ui.app
```

همچنین بعد از sync کردن extra مربوط به UI، entry point زیر در محیط uv در دسترس است:

```bash
uv run ev4-project-gate-ui
```

اگر `gradio` نصب نشده باشد، entry point باید با پیام روشن خطا بدهد و کاربر را به `uv sync --extra ui` راهنمایی کند. `gradio` وابستگی اجباری core package نیست. مسیر `pip install -e ".[dev,ui]"` فقط fallback است اگر `uv` در دسترس نباشد.

## محدوده اجرایی Prompt 06

| بخش | وضعیت UI | توضیح |
|---|---|---|
| Validate Stage Evidence Bundle | wired | از `BundleValidator` موجود استفاده می‌کند. |
| Architect → CE | wired with local paths | فقط با مسیرهای local checkout برای Architect و CE اجرا می‌شود. |
| CE → Builder | wired through service | از service layer اجرا می‌شود و بدون checkout/evidence معتبر fail-closed می‌ماند. |
| Builder → Responsive | wired through service | از service layer اجرا می‌شود و بدون checkout/evidence معتبر fail-closed می‌ماند. |
| Final Evidence Gate | wired through service | از service layer اجرا می‌شود و بدون checkout/evidence معتبر fail-closed می‌ماند. |
| Inspect Capabilities | wired | فقط `capability-status.v1.json` را read-only می‌خواند. |

## Patch 1: visual / RTL / typography polish

این patch فقط presentation را اصلاح کرد:

- header به یک کارت compact operator-panel تبدیل شد؛
- labelهای قابل مشاهده فارسی-اول شدند، بدون تغییر در internal transition choices؛
- متن فارسی با `lang="fa"` و `dir="rtl"` و alignment راست نمایش داده می‌شود؛
- JSON، path، repo name، diagnostic code، JSONPath، hash، command، و code-like text با LTR isolation و font کد نمایش داده می‌شوند؛
- Gradio CSS از semantic tokens در `src/ev4_transition/presentation/theme_tokens.py` استفاده می‌کند؛
- dark mode از near-black surfaces، elevated cards، focus ring، و status icon + text + semantic tone استفاده می‌کند.

## Patch 2: operator guidance / diagnostic help

این patch یک لایه code-backed guidance اضافه می‌کند که بالای raw diagnostics نمایش داده می‌شود:

- `src/ev4_transition/data/operator-guidance.v1.json` رجیستری deterministic guidance برای diagnosticهای شناخته‌شده است؛
- `src/ev4_transition/service/guidance.py` result را به خلاصه عملیاتی فارسی، گروه‌بندی diagnostics، وضعیت output و repair prompt تبدیل می‌کند؛
- UI توضیح می‌دهد gate کجا متوقف شد، چه چیزی قبل از failure پیش رفت، مشکل فعلی چیست و اقدام بعدی دقیق چیست؛
- اگر `output` برابر `null` باشد، پنل صریح می‌گوید downstream input package تولید نشده است؛
- اگر `validate_bundle` اجرا شود، پنل صریح می‌گوید این مسیر validation-only است و CE output تولید نمی‌کند؛
- برای `PG_A2C_ARCHITECT_SCHEMA_VALIDATION_FAILED` پرامپت اصلاح copy-ready ساخته می‌شود؛
- reportهای `report.md` و `report.html` شامل راهنمای عملیاتی، grouped diagnostics و raw JSON LTR هستند.

این patch عمداً موارد زیر را اضافه نمی‌کند:

- automatic JSON repair؛
- mutation ورودی کاربر؛
- schema/validator/specialist contract جدید؛
- automatic GitHub clone/pull؛
- real Elementor validation؛
- browser accessibility certification؛
- end-to-end EV4 readiness claims.

## هشدار محدوده

این ابزار فقط بررسی گیت را اجرا می‌کند؛ اثبات نهایی تولید، فرانت‌اند، Elementor واقعی یا صحت Responsive نیست.

این UI claimهای زیر را نمی‌سازد:

- production readiness
- real Elementor validation
- frontend correctness
- responsive correctness
- accessibility completion
- export validation
- CE approval
- Builder authorization
- end-to-end EV4 readiness

## RTL/LTR

متن فارسی در UI با `dir="rtl"` نمایش داده می‌شود. شناسه‌های فنی، مسیرها، repo nameها، diagnostic codeها، JSON keyها، hashها و commandها با LTR isolation نمایش داده می‌شوند تا copyable بمانند.

## خروجی‌ها

پس از هر run، UI سه خروجی قابل دانلود می‌سازد:

- `result.json`
- `report.md`
- `report.html`

رندر report/download از adapter محلی و service response ساخته می‌شود، result object را mutate نمی‌کند، و اگر نوشتن گزارش fail شود لینک دانلود موفق جعلی تولید نمی‌کند.

## اسناد مرتبط

- `docs/OPERATOR_GUIDE.md`
- `docs/DIAGNOSTIC_GUIDE.md`
- `docs/UI_SERVICE_CONTRACT.md`
- `docs/REPORT_UX_CONTRACT.md`
