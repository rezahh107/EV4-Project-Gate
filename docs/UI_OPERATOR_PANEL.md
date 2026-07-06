# EV4 Project Gate Local Operator Panel

این سند محدوده پنل محلی اپراتور را توضیح می‌دهد. این UI یک لایه انسانی برای اجرای بررسی‌های Project Gate است؛ منطق transition جدید، validator جدید، adapter جدید، schema جدید یا claim جدید درباره production/readiness ایجاد نمی‌کند.

## هدف

کاربر غیر CLI بتواند از طریق یک رابط ساده:

- فایل JSON را upload کند؛
- متن JSON را paste کند؛
- قابلیت‌های Project Gate را بخواند؛
- transitionهای آماده و pending را از هم تشخیص دهد؛
- وضعیت فارسی، diagnostics، و خروجی‌های قابل دانلود را ببیند.

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

این patch فقط presentation را اصلاح می‌کند:

- header به یک کارت compact operator-panel تبدیل شده است؛
- labelهای قابل مشاهده فارسی-اول شده‌اند، بدون تغییر در internal transition choices؛
- متن فارسی با `lang="fa"` و `dir="rtl"` و alignment راست نمایش داده می‌شود؛
- JSON، path، repo name، diagnostic code، JSONPath، hash، command، و code-like text با LTR isolation و font کد نمایش داده می‌شوند؛
- Gradio CSS از semantic tokens در `src/ev4_transition/presentation/theme_tokens.py` استفاده می‌کند؛
- dark mode از near-black surfaces، elevated cards، focus ring، و status icon + text + semantic tone استفاده می‌کند.

این patch عمداً موارد زیر را اضافه نمی‌کند:

- diagnostic grouping logic؛
- repair prompt generator؛
- operator guidance registry؛
- preflight pinned-file checking؛
- repeated failure escape hatch؛
- transition logic جدید؛
- schema/validator/specialist contract جدید.

## هشدار محدوده

این ابزار فقط بررسی گیت را اجرا می‌کند؛ اثبات نهایی تولید، فرانت‌اند، Elementor واقعی یا صحت Responsive نیست.

این UI claimهای زیر را نمی‌سازد:

- production readiness
- real Elementor validation
- frontend correctness
- responsive correctness
- accessibility completion
- export validation

## RTL/LTR

متن فارسی در UI با `dir="rtl"` نمایش داده می‌شود. شناسه‌های فنی، مسیرها، repo nameها، diagnostic codeها، JSON keyها، hashها و commandها با LTR isolation نمایش داده می‌شوند تا copyable بمانند.

## خروجی‌ها

پس از هر run، UI سه خروجی قابل دانلود می‌سازد:

- `result.json`
- `report.md`
- `report.html`

رندر report/download از adapter محلی و service response ساخته می‌شود، result object را mutate نمی‌کند، و اگر نوشتن گزارش fail شود لینک دانلود موفق جعلی تولید نمی‌کند.
