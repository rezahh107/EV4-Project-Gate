# راهنمای استفاده شخصی از Project Gate

<section lang="fa" dir="rtl">

مدل ذهنی ساده: `Project Gate` مثل گمرک بین ریپوهاست. اگر مدارک کامل باشد، بسته عبور می‌کند. اگر مدارک ناقص باشد، `insufficient_evidence` می‌دهد. اگر ساختار اشتباه باشد، `invalid` می‌دهد.

## آماده‌سازی پیش‌فرض

مسیر پیش‌فرض repo با `uv` است:

```bash
uv python install 3.11
uv sync --extra dev --extra ui
uv run ev4-transition inspect
```

`dev` و `ui` extraهای `[project.optional-dependencies]` هستند، نه dependency group. برای اجرای UI و testها آن‌ها را با `--extra dev --extra ui` sync کن. `uv.lock` برای تکرارپذیری commit شده و `uv sync` محیط پروژه را از lockfile مدیریت می‌کند.

## جریان کاری اصلی

1. UI را باز کن.
2. نوع check یا transition را انتخاب کن.
3. فایل JSON را upload کن یا متن JSON را paste کن.
4. مسیر پوشه‌های محلی ریپوها را انتخاب کن.
5. روی Run کلیک کن.
6. نتیجه فارسی و diagnostics را بخوان.
7. خروجی‌های UI را از همان UI دانلود کن؛ معمولاً `result.json`، `report.md` و `report.html` یا artifactهای downloadشده توسط UI هستند.
8. تصمیم بگیر: عبور، اصلاح، یا تهیه شواهد بیشتر.

## اجرای UI

```bash
uv run python -m ev4_transition.ui.app
```

اگر launcher لازم داری:

```bash
uv run python scripts/run-project-gate-ui.py
```

## اجرای demo synthetic

```bash
uv run python scripts/run-project-gate-demo.py
```

## معنی statusها

### `accepted`

یعنی شواهد لازم برای همان check مشخص کامل بوده است. این status به‌تنهایی به معنی production readiness عمومی نیست.

### `invalid`

یعنی JSON یا envelope با schema و قرارداد Project Gate نمی‌خواند. سیستم نباید خودش حدس بزند یا خروجی specialistها را silently normalize کند.

### `insufficient_evidence`

یعنی ساختار قابل فهم است، اما مدارک کافی نیست. این وضعیت مثل پرونده‌ای است که در گمرک متوقف می‌شود چون سند لازم همراهش نیست.

### `repair_needed`

یعنی بسته قابل فهم است، اما موارد قابل اصلاح دارد. باید diagnosticها اصلاح شوند و دوباره check اجرا شود.

## قرارداد خروجی demo کنترل‌شده

```text
outputs/runs/<timestamp-or-run-id>/
```

فایل‌های مورد انتظار demo:

```text
result.json
report.md
report.html
input.snapshot.json
diagnostics.json
```

## Fallback if uv is unavailable

فقط اگر `uv` قابل نصب نیست:

```bash
python -m pip install -e '.[dev,ui]'
python -m ev4_transition.ui.app
```

## محدودیت مهم demo

نمونه‌های داخل `examples/personal-use/` و `fixtures/personal-use/` همگی synthetic هستند. آن‌ها برای یادگیری مسیر کار هستند، نه اثبات واقعی EV4، نه validation واقعی Elementor، نه export validation، نه accessibility completion، و نه readiness برای production.

</section>
