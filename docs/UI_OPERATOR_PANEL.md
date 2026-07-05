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
python -m pip install -e '.[dev]'
python -m ev4_transition.ui.app
```

همچنین entry point زیر اضافه شده است:

```bash
ev4-project-gate-ui
```

## محدوده اجرایی Prompt 1

| بخش | وضعیت UI | توضیح |
|---|---|---|
| Validate Stage Evidence Bundle | wired | از `BundleValidator` موجود استفاده می‌کند. |
| Architect → CE | wired with local paths | فقط با مسیرهای local checkout برای Architect و CE اجرا می‌شود. |
| CE → Builder | pending | fake execution ندارد؛ نیازمند service layer در Prompt 2 است. |
| Builder → Responsive | pending | fake execution ندارد؛ نیازمند service layer در Prompt 2 است. |
| Final Evidence Gate | pending | fake execution ندارد؛ نیازمند service layer در Prompt 2 است. |
| Inspect Capabilities | wired | فقط `capability-status.v1.json` را read-only می‌خواند. |

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

رندر report از `src/ev4_transition/reports/` استفاده می‌کند و result object را mutate نمی‌کند.
