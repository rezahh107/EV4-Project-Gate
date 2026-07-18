# شروع سریع پنل محلی EV4 Project Gate

```yaml
document_purpose: personal_local_use
interface: EV4 Project Gate Local Operator Panel
verified_against_commit: 4598f51fd8599e4ca77d4760431d646af4d7b93f
last_reviewed: 2026-07-18
primary_ui_file: src/ev4_transition/ui/app.py
```

این فایل مسیر کوتاه استفاده روزمره از پنل است. برای توضیح جزءبه‌جزء همه بخش‌ها به [`LOCAL_OPERATOR_PANEL_USER_GUIDE.fa.md`](LOCAL_OPERATOR_PANEL_USER_GUIDE.fa.md) مراجعه کن.

## شروع سریع پنج‌دقیقه‌ای

### 1. پنل را اجرا کن

در root ریپوی `EV4-Project-Gate`:

```bash
uv sync --extra dev --extra ui
uv run ev4-project-gate-ui
```

روش معادل:

```bash
uv run python -m ev4_transition.ui.app
```

### 2. برای اولین آزمایش امن، فقط اعتبارسنجی را انتخاب کن

در بخش `انتخاب بررسی / Transition` گزینه زیر را انتخاب کن:

```text
Validate Stage Evidence Bundle
```

در بخش `Acquisition mode` مقدار پیش‌فرض زیر را نگه دار:

```text
pinned_owner_file_computation
```

### 3. یک JSON معتبر وارد کن

برای آزمایش کنترل‌شده می‌توانی فایل زیر را upload کنی:

```text
fixtures/valid/architect-stage-bundle.v1.json
```

برای جلوگیری از ابهام، هم‌زمان از Upload و Paste استفاده نکن. اگر کادر Paste خالی نباشد، متن Paste‌شده بر فایل uploadشده اولویت دارد.

### 4. Preflight را اجرا کن

دکمه زیر را بزن:

```text
بررسی مسیرها و ورودی‌ها
```

برای `Validate Stage Evidence Bundle` مسیر repositoryهای specialist لازم نیست.

- `ready`: آماده اجرای اصلی است.
- `warnings`: هشدارها را بخوان؛ ممکن است اجرای اصلی همچنان ممکن باشد.
- `blocked`: ابتدا خطا را اصلاح کن و ادامه نده.

### 5. بررسی اصلی را اجرا کن

دکمه زیر را بزن:

```text
اجرای بررسی Project Gate
```

سپس به‌ترتیب این بخش‌ها را بخوان:

1. `خلاصه نتیجه`
2. `جزئیات پیشرفته / Diagnostics`
3. `پیش‌نمایش JSON / result.json`
4. `دانلود خروجی‌ها`

### 6. نتیجه را درست تفسیر کن

`Validate Stage Evidence Bundle` فقط validation انجام می‌دهد. در این مسیر، `output: null` طبیعی است و ورودی CE، Builder یا Responsive تولید نمی‌شود.

---

## می‌خواهم چه کاری انجام دهم؟

| هدف | انتخاب UI | JSON مورد انتظار | مسیرهای local لازم | خروجی مرحله بعد |
|---|---|---|---|---|
| فقط بررسی ساختار bundle | `Validate Stage Evidence Bundle` | یک `Stage Evidence Bundle` | ندارد | ندارد؛ validation-only |
| انتقال Architect به CE | `Architect → CE` | `stage=architect` | Architect + CE | فقط در صورت موفقیت و evidence معتبر |
| انتقال CE به Builder | `CE → Builder` | `stage=ce` | CE + Builder | فقط در صورت موفقیت و evidence معتبر |
| انتقال Builder به Responsive | `Builder → Responsive` | `stage=builder` | Builder + Responsive | فقط در صورت موفقیت و evidence معتبر |
| بررسی نهایی evidence | `Final Evidence Gate` | ورودی با `stage=responsive` در Preflight | Project Gate + Responsive | وابسته به evidence و قرارداد فعال |
| فقط مشاهده وضعیت قابلیت‌ها | `Inspect Capabilities` | لازم نیست | لازم نیست | ندارد؛ فقط snapshot قابلیت‌ها |

### انتخاب Acquisition mode

برای استفاده عادی از همین پنل، مقدار زیر را نگه دار:

```text
pinned_owner_file_computation
```

گزینه `producer_emitted_gate_artifact` فقط برای یک Producer Gate Export کامل است. این گزینه جای Stage Evidence Bundle عادی نیست و بدون runtime evidence و checkoutهای لازم باید fail-closed بماند.

---

## بعد از مشاهده status چه کنم؟

| status | ادامه مجاز است؟ | اقدام بعدی |
|---|---:|---|
| `accepted` و downstream artifact رسمی موجود است | فقط در محدوده evidence اعلام‌شده | artifact رسمی را طبق workflow همان transition استفاده کن |
| `accepted` ولی `output: null` | خیر | هیچ بسته مرحله بعد ساخته نشده است |
| `repair_needed` | خیر | Diagnostics را اصلاح کن و دوباره اجرا کن |
| `insufficient_evidence` | خیر | checkout، validator، lock یا evidence گمشده را تهیه کن |
| `invalid` | خیر | JSON، path، schema identity، hash یا transition selection را اصلاح کن |

قاعده ساده:

```text
accepted به‌تنهایی کافی نیست
status + evidence scope + downstream artifact رسمی باید با هم معتبر باشند
```

---

## کدام فایل را بعد از اجرا استفاده کنم؟

### فایل‌های دانلودی UI

پنل فعلی این فایل‌های گزارشی را می‌سازد:

```text
result.json
report.md
report.html
```

| فایل | کاربرد | ورودی semantic مرحله بعد است؟ |
|---|---|---:|
| `result.json` | نتیجه machine-readable اجرای UI و service | خیر، به‌صورت خودکار نیست |
| `report.md` | گزارش انسانی برای GitHub یا VS Code | خیر |
| `report.html` | گزارش خوانا در مرورگر | خیر |

### قانون ایمنی artifact

- `result.json` را به‌عنوان source bundle مرحله بعد upload نکن.
- اگر `output: null` است، هیچ downstream package تولید نشده است.
- یک `output` تو‌در‌تو را دستی copy، استخراج یا بازسازی نکن، مگر workflow رسمی همان transition صریحاً آن را مجاز کرده باشد.
- receipt یا گزارش Project Gate را با ورودی semantic specialist بعدی ادغام نکن.

### artifact مستقل رسمی

برای transitionهایی که workflow مستقل رسمی دارند، همان workflow را اجرا کن:

| Transition | راهنمای رسمی | artifact مستقل |
|---|---|---|
| Architect → CE | `docs/PG_A2C_OPERATOR_WORKFLOW.md` | `ce-input.json` + receipt جداگانه |
| CE → Builder | `docs/PG_C2B_OPERATOR_WORKFLOW.md` | `builder-input.json` + receipt جداگانه |

برای transitionهای دیگر، فقط از workflow و capability truth فعلی repository استفاده کن. اگر artifact مستقل یا مسیر رسمی روشن نیست، ادامه را متوقف کن و نتیجه را `insufficient_evidence` در نظر بگیر؛ artifact اختراع یا بازسازی نکن.

---

## جریان روزمره پیشنهادی

```text
1. هدف را از جدول انتخاب کن
2. source JSON مرحله قبل را پیدا کن
3. transition درست را انتخاب کن
4. pinned_owner_file_computation را نگه دار
5. فقط مسیرهای local لازم را وارد کن
6. Preflight را اجرا کن
7. blockedها را رفع کن
8. Gate را اجرا کن
9. status و Diagnostics را بخوان
10. وجود downstream artifact رسمی را جداگانه تأیید کن
11. گزارش‌ها را برای audit نگه دار
12. فقط artifact رسمی را به مرحله بعد بده
```

---

## خطاهای سریع و اقدام مستقیم

| چیزی که می‌بینی | اقدام مستقیم |
|---|---|
| `wrong_stage` | transition یا فایل JSON را عوض کن تا `stage` هماهنگ شود |
| GitHub URL در path | repository را local clone کن و مسیر پوشه root را بده |
| `pinned file missing` | checkout را روی revision مورد انتظار به‌روز کن و Preflight را تکرار کن |
| `result.json used as source` | source bundle واقعی مرحله قبل را وارد کن |
| `insufficient_evidence` | diagnostic را برای missing checkout، validator، lock یا evidence بخوان |
| `output: null` | ادامه نده؛ بسته مرحله بعد ساخته نشده است |
| دانلودی ساخته نشد | permission و filesystem را بررسی کن؛ موفقیت نوشتن فایل را فرض نکن |

---

## محدودیت‌هایی که باید همیشه یادت بماند

این پنل به‌تنهایی موارد زیر را اثبات نمی‌کند:

- production readiness؛
- صحت واقعی Elementor؛
- صحت frontend یا Responsive؛
- accessibility completion؛
- real non-synthetic end-to-end handoff.

`accepted` فقط در محدوده Gate و evidence همان اجرا معتبر است.

## راهنمای کامل

برای توضیح همه 61 جزء UI، ستون‌های Diagnostics و Capabilities، جزئیات Preflight و troubleshooting گسترده‌تر:

- [`LOCAL_OPERATOR_PANEL_USER_GUIDE.fa.md`](LOCAL_OPERATOR_PANEL_USER_GUIDE.fa.md)
- [`OPERATOR_GUIDE.md`](OPERATOR_GUIDE.md)
- [`UI_OPERATOR_PANEL.md`](UI_OPERATOR_PANEL.md)
