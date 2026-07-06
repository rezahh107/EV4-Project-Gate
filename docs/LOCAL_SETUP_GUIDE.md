# راهنمای نصب و اجرای محلی Project Gate

<section lang="fa" dir="rtl">

این راهنما برای استفاده شخصی و محلی از `EV4-Project-Gate` است. مسیر پیش‌فرض نصب و اجرا از این نسخه به بعد `uv` است، نه `pip`.

## این ابزار چیست؟

`Project Gate` مثل یک ایست بازرسی بین ریپوهای EV4 است. فایل JSON مرحله قبل را می‌گیرد، ساختار و شواهد را بررسی می‌کند، سپس نتیجه فارسی، diagnostic، JSON و report می‌سازد.

## این ابزار چه چیزی نیست؟

این ابزار جایگزین ریپوهای specialist نیست، منطق CE/Builder/Responsive یا validation واقعی Elementor را خودش نمی‌سازد، و بدون شواهد واقعی نباید ادعای `accepted`، production readiness، frontend correctness، accessibility completion یا export validation کند.

## پوشه‌های محلی لازم

بهترین حالت این است که این پنج پوشه کنار هم باشند:

```text
EV4-Project-Gate
EV4-Architect-Repo
EV4-Constructability-Engineer-Repo
EV4-Builder-Assistant-Repo
EV4-Responsive-Architect
```

## نصب پیش‌فرض با uv

`Python >=3.11` پشتیبانی می‌شود. فایل `.python-version` مقدار `3.11` دارد تا `uv` برای setup محلی یک interpreter پیش‌فرض و تکرارپذیر انتخاب کند؛ این به معنی نیاز به Python جدیدتر از `>=3.11` نیست.

در Windows ابتدا `uv` را با یکی از روش‌های رسمی نصب کن:

```powershell
winget install --id=astral-sh.uv -e
```

یا قبل از اجرای installer رسمی PowerShell آن را بررسی کن:

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | more"
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

سپس داخل `EV4-Project-Gate` اجرا کن:

```powershell
.\scripts\setup-windows-uv.ps1
```

مسیر cross-platform:

```bash
uv python install 3.11
uv sync --extra dev --extra ui
uv run ev4-transition inspect
```

`uv.lock` در repo commit شده است تا dependency graph بین local و CI ثابت بماند. extraهای `dev` و `ui` در `[project.optional-dependencies]` تعریف شده‌اند و dependency group نیستند؛ بنابراین برای test و UI باید با `--extra dev --extra ui` sync شوند.

`uv sync` محیط پروژه را مدیریت می‌کند و به‌صورت exact می‌تواند packageهای خارج از lockfile را از محیط حذف کند.

## اجرای UI محلی

```bash
uv run python -m ev4_transition.ui.app
```

یا launcher امن:

```bash
uv run python scripts/run-project-gate-ui.py
```

در Windows:

```powershell
.\scripts\run-project-gate-ui.ps1
```

## اجرای demo کنترل‌شده

این demo فقط fixtureهای synthetic را بررسی می‌کند:

```bash
uv run python scripts/run-project-gate-demo.py
```

## بررسی lockfile و testها

```bash
uv lock --check
uv sync --locked --extra dev --extra ui
uv run pytest
uv run python scripts/check-capability-truth.py
uv run python scripts/check-workflow-permissions.py
```

## Fallback if uv is unavailable

فقط اگر `uv` قابل نصب نیست:

```bash
python -m pip install -e '.[dev,ui]'
pytest
python -m ev4_transition.ui.app
```

این مسیر fallback است و مسیر اصلی repo نیست.

## جلوگیری از ادعای اشتباه

تا وقتی شواهد واقعی owner repositoryها، خروجی واقعی Builder، خروجی واقعی Responsive، export evidence و accessibility evidence وجود نداشته باشد، نتیجه واقعی end-to-end باید `insufficient_evidence` باقی بماند.

</section>
