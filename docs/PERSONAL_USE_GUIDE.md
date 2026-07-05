# راهنمای استفاده شخصی از Project Gate

<section lang="fa" dir="rtl">

مدل ذهنی ساده: `Project Gate` مثل گمرک بین ریپوهاست. اگر مدارک کامل باشد، بسته عبور می‌کند. اگر مدارک ناقص باشد، `insufficient_evidence` می‌دهد. اگر ساختار اشتباه باشد، `invalid` می‌دهد.

## جریان کاری اصلی

1. UI را باز کن.
2. نوع check یا transition را انتخاب کن.
3. فایل JSON را upload کن یا متن JSON را paste کن.
4. مسیر پوشه‌های محلی ریپوها را انتخاب کن.
5. روی Run کلیک کن.
6. نتیجه فارسی و diagnostics را بخوان.
7. فایل‌های `JSON`، `Markdown` و `HTML` report را دانلود یا از پوشه خروجی بردار.
8. تصمیم بگیر: عبور، اصلاح، یا تهیه شواهد بیشتر.

## وقتی UI هنوز آماده نیست

این بسته launcher اضافه کرده است:

```bash
python scripts/run-project-gate-ui.py
```

اگر Prompt 1 هنوز merge نشده باشد، launcher به‌جای traceback پیام روشن می‌دهد و پیشنهاد می‌کند demo synthetic را اجرا کنی:

```bash
python scripts/run-project-gate-demo.py
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

## خروجی‌هایی که باید انتظار داشته باشی

در هر run، خروجی‌ها زیر مسیر زیر ذخیره می‌شوند:

```text
outputs/runs/<timestamp-or-run-id>/
```

فایل‌ها:

```text
result.json
report.md
report.html
input.snapshot.json
diagnostics.json
```

## تصمیم بعد از نتیجه

- اگر `accepted` بود: فقط در همان محدوده شواهد ثبت‌شده استفاده کن.
- اگر `invalid` بود: ساختار JSON، schema identity، مسیرها و hashها را اصلاح کن.
- اگر `insufficient_evidence` بود: مدرک گمشده را از owner repository یا validator رسمی تهیه کن.
- اگر `repair_needed` بود: diagnosticهای قابل اصلاح را رفع کن و دوباره اجرا کن.

## محدودیت مهم demo

نمونه‌های داخل `examples/personal-use/` و `fixtures/personal-use/` همگی synthetic هستند. آن‌ها برای یادگیری مسیر کار هستند، نه اثبات واقعی EV4، نه validation واقعی Elementor، و نه readiness برای production.

</section>
