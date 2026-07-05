# راهنمای نصب و اجرای محلی Project Gate

<section lang="fa" dir="rtl">

این راهنما برای استفاده شخصی و محلی از `EV4-Project-Gate` است؛ یعنی یک نفر، روی یک کامپیوتر، با چند checkout محلی از ریپوهای EV4.

## این ابزار چیست؟

`Project Gate` مثل یک ایست بازرسی بین ریپوهای EV4 است. فایل JSON مرحله قبل را می‌گیرد، ساختار و شواهد را بررسی می‌کند، سپس نتیجه فارسی، diagnostic، JSON و report می‌سازد.

## این ابزار چه چیزی نیست؟

این ابزار:

- جایگزین `EV4-Architect-Repo`، `EV4-Constructability-Engineer-Repo`، `EV4-Builder-Assistant-Repo` یا `EV4-Responsive-Architect` نیست.
- منطق CE، منطق Builder، منطق Responsive یا اعتبارسنجی واقعی Elementor را خودش نمی‌سازد.
- بدون شواهد واقعی نباید ادعای `accepted`، production readiness، frontend correctness، accessibility completion یا export validation کند.
- cloud، account، database، secret storage یا deployment platform لازم ندارد.

## پوشه‌های محلی لازم

بهترین حالت این است که این پنج پوشه کنار هم باشند:

```text
EV4-Project-Gate
EV4-Architect-Repo
EV4-Constructability-Engineer-Repo
EV4-Builder-Assistant-Repo
EV4-Responsive-Architect
```

این‌ها باید کنار هم روی کامپیوترت باشند تا `Project Gate` بتواند فایل‌های رسمی هر ریپو را بخواند.

## نصب Python و وابستگی‌ها

از داخل پوشه `EV4-Project-Gate` اجرا کن:

```bash
python -m pip install -e '.[dev]'
```

در Windows اگر `python` کار نکرد، این را امتحان کن:

```powershell
py -3 -m pip install -e '.[dev]'
```

## اجرای UI محلی

UI توسط Prompt 1 ساخته می‌شود. این بسته فقط launcher امن اضافه می‌کند.

روش ساده:

```bash
python scripts/run-project-gate-ui.py
```

در Windows:

```powershell
.\scripts\run-project-gate-ui.ps1
```

یا فایل زیر را اجرا کن:

```text
scripts/run-project-gate-ui.bat
```

اگر UI هنوز merge نشده باشد، پیام روشن می‌بینی:

```text
UI is not installed yet. Merge Prompt 1 UI branch first.
```

## اجرای demo کنترل‌شده

این demo فقط fixtureهای synthetic را بررسی می‌کند:

```bash
python scripts/run-project-gate-demo.py
```

خروجی زیر ساخته می‌شود:

```text
outputs/runs/demo-<timestamp>/
```

## خروجی‌ها کجا ذخیره می‌شوند؟

خروجی‌های تولیدی باید زیر این مسیر باشند:

```text
outputs/runs/<timestamp-or-run-id>/
```

فایل‌های مورد انتظار:

```text
result.json
report.md
report.html
input.snapshot.json
diagnostics.json
```

خروجی‌های واقعی run نباید commit شوند.

## معنی statusها

- `accepted`: مدارک لازم برای همان بررسی کامل است و بسته می‌تواند در همان محدوده عبور کند.
- `invalid`: ساختار یا schema اشتباه است و سیستم بدون حدس یا اصلاح خودکار آن را رد می‌کند.
- `insufficient_evidence`: بسته قابل فهم است، اما شواهد کافی نیست. این وضعیت هشدار/مسدودکننده است.
- `repair_needed`: بسته قابل فهم است، اما موارد قابل اصلاح دارد و نباید به‌عنوان نتیجه نهایی عبور کند.

## جلوگیری از ادعای اشتباه

تا وقتی شواهد واقعی owner repositoryها، خروجی واقعی Builder، خروجی واقعی Responsive، export evidence و accessibility evidence وجود نداشته باشد، نتیجه واقعی end-to-end باید `insufficient_evidence` باقی بماند.

</section>
