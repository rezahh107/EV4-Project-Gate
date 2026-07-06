# Generated outputs

<section lang="fa" dir="rtl">

این پوشه فقط قرارداد محل خروجی‌های controlled demo / demo کنترل‌شده را نگه می‌دارد. فایل‌های تولیدی run نباید commit شوند.

مسیر استاندارد خروجی demo:

```text
outputs/runs/<timestamp-or-run-id>/
```

فایل‌های مورد انتظار در هر demo run:

```text
result.json
report.md
report.html
input.snapshot.json
diagnostics.json
```

`outputs/.gitkeep` و `outputs/README.md` باید tracked بمانند، اما `outputs/runs/` باید ignored باشد.

رفتار download در UI ممکن است از artifactهای UI استفاده کند. این قرارداد، رفتار نهایی UI را تعیین نمی‌کند تا یک PR integration مسیر UI، service و demo را هم‌راستا کند.

</section>
