# Generated outputs

<section lang="fa" dir="rtl">

این پوشه فقط قرارداد محل خروجی‌ها را نگه می‌دارد. فایل‌های تولیدی run نباید commit شوند.

مسیر استاندارد خروجی:

```text
outputs/runs/<timestamp-or-run-id>/
```

فایل‌های مورد انتظار در هر run:

```text
result.json
report.md
report.html
input.snapshot.json
diagnostics.json
```

`outputs/.gitkeep` و `outputs/README.md` باید tracked بمانند، اما `outputs/runs/` باید ignored باشد.

</section>
