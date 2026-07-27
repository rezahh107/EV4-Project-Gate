# راهنمای نصب و اجرای محلی Project Gate

<section lang="fa" dir="rtl">

این راهنما برای استفاده شخصی و محلی از `EV4-Project-Gate` است. مسیر پیش‌فرض نصب و اجرا `uv` است، نه `pip`.

## این ابزار چیست؟

`Project Gate` ایست بازرسی deterministic میان ریپوهای EV4 است. فایل JSON مرحله قبل را می‌گیرد، ساختار، شواهد و owner contractهای لازم را بررسی می‌کند و سپس نتیجه فارسی، diagnostic، JSON و report می‌سازد.

## این ابزار چه چیزی نیست؟

این ابزار جایگزین ریپوهای specialist نیست، منطق CE/Builder/Responsive یا validation واقعی Elementor را خودش نمی‌سازد، و بدون شواهد واقعی نباید ادعای `accepted`، production readiness، frontend correctness، accessibility completion یا export validation کند.

## پوشه‌های محلی لازم

برای جریان‌های اصلی بهتر است این پنج پوشه کنار هم باشند:

```text
EV4-Project-Gate
EV4-Architect-Repo
EV4-Constructability-Engineer-Repo
EV4-Builder-Assistant-Repo
EV4-Responsive-Architect
```

برای Final Gate و برای Producer Gate Exportهایی که `continuation_assurance` دارند، یک checkout محلی `EV4-Decision-Kernel` نیز لازم است:

```text
EV4-Decision-Kernel
```

نبودن این checkout در ورودی legacy که carrier ندارد نباید Git، Node یا npm را فعال کند. در ورودی دارای carrier، checkout باید با commit و byteهای pin‌شده در lock سازگار باشد؛ در غیر این صورت نتیجه fail-closed است.

## نصب پیش‌فرض با uv

`Python >=3.11` پشتیبانی می‌شود. فایل `.python-version` مقدار `3.11` دارد تا `uv` یک interpreter پیش‌فرض و تکرارپذیر انتخاب کند.

در Windows ابتدا `uv` را نصب کن:

```powershell
winget install --id=astral-sh.uv -e
```

یا installer رسمی PowerShell را پس از بررسی اجرا کن:

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
uv sync --locked --extra dev --extra ui
uv run ev4-transition inspect
```

`uv.lock` در repo commit شده است تا dependency graph بین local و CI ثابت بماند. extraهای `dev` و `ui` در `[project.optional-dependencies]` تعریف شده‌اند؛ بنابراین برای test و UI باید با `--extra dev --extra ui` sync شوند.

## اجرای Producer Gate Export

ورودی legacy بدون `continuation_assurance` به Decision Kernel وابسته نیست:

```bash
uv run ev4-handoff producer-export.json \
  --project-gate-repo .
```

وقتی carrier حاضر است، همان checkout انتخاب‌شده باید از Preflight تا runtime ثابت بماند:

```bash
uv run ev4-handoff producer-export.json \
  --project-gate-repo . \
  --kernel-repo ../EV4-Decision-Kernel
```

`kernel_repo_path` در این حالت بخشی از request fingerprint است. تغییر مسیر پس از Preflight باعث stale fingerprint و توقف dispatch می‌شود. Preflight و runtime هر دو همان مسیر اپراتور را استفاده می‌کنند.

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
uv run python -m compileall -q src tests
uv run pytest -vv
uv run python scripts/check-capability-truth.py
uv build --wheel
```

validatorهای قدیمی `scripts/check-workflow-permissions.py` و `scripts/check-github-action-pinning.py` دیگر بخشی از pipeline فعال نیستند و نباید در setup محلی اجرا شوند.

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
