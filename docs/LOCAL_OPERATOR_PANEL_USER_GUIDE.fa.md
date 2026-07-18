# راهنمای جامع پنل محلی EV4 Project Gate

> زبان: فارسی  
> رابط هدف: `EV4 Project Gate Local Operator Panel`  
> فایل اصلی UI: `src/ev4_transition/ui/app.py`

این سند اجزای پنل محلی Project Gate را از بالا به پایین توضیح می‌دهد و برای کاربری نوشته شده است که می‌خواهد بدون استفاده مستقیم از CLI، یک ورودی JSON را بررسی کند، مسیر repositoryهای محلی را بدهد، نتیجه فارسی را بفهمد و گزارش‌ها را دانلود کند.

## 1. محدوده این پنل

این UI فقط یک لایه انسانی روی سرویس داخلی Project Gate است:

```text
UI/operator panel
→ GateRequest
→ run_gate_request(...)
→ GateResponse
→ Persian summary + Diagnostics + result.json + reports
```

Project Gate یک checkpoint و orchestrator است؛ جای Architect، CE، Builder یا Responsive را نمی‌گیرد و نباید evidence، schema یا نتیجه specialist را اختراع کند.

این پنل به‌تنهایی موارد زیر را اثبات نمی‌کند:

- production readiness؛
- صحت واقعی Elementor؛
- صحت frontend؛
- صحت Responsive؛
- تکمیل accessibility؛
- آمادگی end-to-end کل EV4.

حتی `accepted` نیز فقط در محدوده همان Gate و evidence موجود معتبر است.

---

## 2. جریان پیشنهادی استفاده

```text
1. Transition را انتخاب کن
2. Acquisition mode را انتخاب کن
3. JSON صحیح را upload یا paste کن
4. مسیر local checkoutهای لازم را وارد کن
5. Preflight را اجرا کن
6. خطاهای Preflight را اصلاح کن
7. بررسی اصلی Project Gate را اجرا کن
8. خلاصه نتیجه را بخوان
9. Diagnostics را در صورت نیاز باز کن
10. result.json و گزارش‌ها را دانلود کن
11. فقط در صورت تولید output معتبر، مرحله بعد را ادامه بده
```

---

# 3. اجزای رابط از بالا به پایین

## 3.1 سربرگ برنامه

### 1. `Local Operator Panel`

مشخص می‌کند این صفحه پنل اپراتور محلی است؛ یعنی برنامه روی سیستم شما اجرا می‌شود و برای transitionهای واقعی از repositoryهای local checkout استفاده می‌کند.

### 2. `EV4 Project Gate`

نام برنامه است. نقش آن کنترل و اعتبارسنجی گذارهای بین repositoryهای EV4 است:

```text
Architect → Project Gate → CE → Project Gate → Builder
→ Project Gate → Responsive → Project Gate → final evidence
```

### 3. نشان `gate runner`

یک badge توصیفی است و نشان می‌دهد این صفحه برای اجرای Gate ساخته شده است. این badge دکمه یا status نتیجه نیست.

### 4. «پنل محلی بررسی گذارها»

زیرعنوان فارسی صفحه است. منظور از `transition`، بررسی و انتقال کنترل‌شده از خروجی یک specialist به ورودی specialist بعدی است.

### 5. نوار هشدار زرد

هشدار می‌دهد که پنل فقط Project Gate را اجرا می‌کند و نباید نتیجه آن را با اثبات نهایی تولید، Elementor واقعی، frontend یا Responsive اشتباه گرفت.

### 6. متن راهنمای کوتاه زیر هشدار

جریان کلی را یادآوری می‌کند:

```text
JSON را upload یا paste کن
→ transition را انتخاب کن
→ نتیجه فارسی و Diagnostics را ببین
→ خروجی‌ها را دانلود کن
```

---

## 3.2 انتخاب نوع بررسی

### 7. `انتخاب بررسی / Transition`

مشخص می‌کند Project Gate چه عملیاتی را اجرا کند.

### 8. `Validate Stage Evidence Bundle`

فقط envelope عمومی `Stage Evidence Bundle` را اعتبارسنجی می‌کند.

کارهایی که انجام می‌دهد:

- JSON را می‌خواند؛
- ساختار bundle را بررسی می‌کند؛
- schema و diagnostics عمومی را اجرا می‌کند.

کارهایی که انجام نمی‌دهد:

- transition واقعی؛
- ساخت CE input؛
- ساخت Builder input؛
- ساخت Responsive input.

در این حالت `output: null` معمولاً طبیعی است، چون مسیر `validation-only` است.

### 9. `Architect → CE`

ورودی Architect را برای ورود به CE بررسی می‌کند.

ورودی مورد انتظار:

```text
stage = architect
```

در صورت موفقیت، خروجی مرحله بعد باید CE input bundle باشد.

مسیرهای لازم:

```text
architect_repo_path
ce_repo_path
```

### 10. `CE → Builder`

بسته خروجی CE را برای ورود به Builder بررسی می‌کند.

ورودی مورد انتظار:

```text
stage = ce
```

مسیرهای لازم:

```text
ce_repo_path
builder_repo_path
```

این transition fail-closed است؛ نبود evidence، checkout یا owner tooling معتبر نباید به `accepted` منجر شود.

### 11. `Builder → Responsive`

خروجی Builder را برای ورود به Responsive بررسی می‌کند.

ورودی مورد انتظار:

```text
stage = builder
```

مسیرهای لازم:

```text
builder_repo_path
responsive_repo_path
```

### 12. `Final Evidence Gate`

آخرین Gate evidence را اجرا می‌کند.

ورودی مورد انتظار در Preflight:

```text
stage = responsive
```

مسیرهای لازم:

```text
project_gate_repo_path
responsive_repo_path
```

### 13. `Inspect Capabilities`

transition اجرا نمی‌کند و فقط snapshot قابلیت‌های ثبت‌شده Project Gate را از فایل زیر می‌خواند:

```text
src/ev4_transition/data/capability-status.v1.json
```

برای این گزینه JSON و مسیر specialist لازم نیست.

---

## 3.3 روش دریافت evidence

### 14. `Acquisition mode / روش دریافت شواهد`

مشخص می‌کند evidence از چه مسیر قراردادی دریافت شود. این دو mode باید صریح و جدا باقی بمانند؛ silent fallback و evidence mixing مجاز نیست.

### 15. `pinned_owner_file_computation`

حالت پیش‌فرض UI است. برنامه با استفاده از JSON ورودی، lockها، فایل‌های pin‌شده و local checkoutهای owner، درخواست را از service داخلی Project Gate عبور می‌دهد.

این mode برای استفاده معمول از پنل محلی مناسب‌تر است.

### 16. `producer_emitted_gate_artifact`

برای Producer Gate Export کامل است، نه یک Stage Evidence Bundle عادی.

این ورودی معمولاً باید اطلاعاتی مانند موارد زیر داشته باشد:

- producer repository؛
- producer commit؛
- producer stage؛
- handoff target؛
- acquisition mode صریح؛
- evidence source صریح؛
- `silent_fallback_allowed: false`.

در پیاده‌سازی فعلی، dispatch کامل برخی transitionها در این mode به immutable source snapshot و checkoutهای دقیق بیشتری نیاز دارد؛ در نبود آن‌ها نتیجه باید `insufficient_evidence` بماند، نه اینکه evidence ساخته یا mode عوض شود.

### 17. دکمه `اجرای بررسی Project Gate`

اجرای اصلی را شروع می‌کند. این دکمه:

1. ورودی‌های صفحه را جمع می‌کند؛
2. درخواست service را می‌سازد؛
3. بررسی یا transition انتخاب‌شده را اجرا می‌کند؛
4. خلاصه نتیجه، Diagnostics، Capabilities، JSON preview و فایل‌های دانلود را به‌روزرسانی می‌کند.

Preflight و اجرای اصلی دو عملیات جدا هستند.

فضای خاکستری اطراف یا زیر دکمه بخشی از layout Gradio است و قابلیت مستقلی ندارد.

---

## 3.4 ورودی JSON

### 18. عنوان کشویی `ورودی JSON`

یک Accordion برای باز و بسته کردن بخش ورودی است. فلش کنار عنوان فقط نمایش بخش را کنترل می‌کند.

### 19. `بارگذاری فایل JSON / Upload JSON`

برای انتخاب یا drag-and-drop یک فایل با پسوند `.json` است.

### 20. `چسباندن متن JSON / Paste JSON`

برای paste کردن محتوای کامل JSON است. کادر با جهت `LTR` نمایش داده می‌شود تا کلیدها و مقادیر فنی copyable بمانند.

نمونه زیر فقط placeholder است:

```json
{"schema_version": "..."}
```

### 21. اولویت Paste نسبت به Upload

اگر هم فایل upload شده باشد و هم کادر Paste متن داشته باشد، متن Paste‌شده انتخاب می‌شود. برای جلوگیری از ابهام، فقط یکی از این دو روش را استفاده کنید.

### 22. نوع JSON مورد انتظار

برای همه گزینه‌ها به‌جز `Inspect Capabilities`، ورودی باید یک JSON object باشد.

نمونه‌های نامعتبر:

```json
[]
```

```json
"hello"
```

```json
123
```

برای transitionهای واقعی، `result.json` خروجی قبلی UI نیز source bundle مرحله قبل محسوب نمی‌شود.

---

## 3.5 مسیر repositoryهای محلی

### 23. عنوان `مسیر پوشه‌های local repository — نه GitHub URL`

این قسمت فقط مسیر filesystem محلی را می‌پذیرد.

درست:

```text
C:\Projects\EV4-Architect-Repo
/home/user/projects/EV4-Architect-Repo
```

نادرست:

```text
https://github.com/rezahh107/EV4-Architect-Repo
```

### 24. `Project Gate path`

مسیر root همین repository است. برای `Final Evidence Gate` لازم است. اگر خالی باشد، UI معمولاً root repository جاری را به‌عنوان مقدار پیش‌فرض service استفاده می‌کند.

### 25. `Architect path`

مسیر local checkout این repository است:

```text
EV4-Architect-Repo
```

برای `Architect → CE` لازم است.

### 26. `CE path`

مسیر local checkout این repository است:

```text
EV4-Constructability-Engineer-Repo
```

برای `Architect → CE` و `CE → Builder` استفاده می‌شود.

### 27. `Builder path`

مسیر local checkout این repository است:

```text
EV4-Builder-Assistant-Repo
```

برای `CE → Builder` و `Builder → Responsive` استفاده می‌شود.

### 28. `Responsive path`

مسیر local checkout این repository است:

```text
EV4-Responsive-Architect
```

برای `Builder → Responsive` و `Final Evidence Gate` استفاده می‌شود.

### 29. جدول مسیرهای لازم

| Transition | مسیرهای ضروری |
|---|---|
| `Validate Stage Evidence Bundle` | مسیر specialist لازم ندارد |
| `Inspect Capabilities` | مسیر لازم ندارد |
| `Architect → CE` | Architect و CE |
| `CE → Builder` | CE و Builder |
| `Builder → Responsive` | Builder و Responsive |
| `Final Evidence Gate` | Project Gate و Responsive |

مسیرهای غیرلازم در Preflight نباید خطای مسدودکننده محسوب شوند.

کنترل‌های ریز انتهای بعضی inputها ممکن است متعلق به مرورگر یا Gradio باشند و معنای قراردادی مستقلی در Project Gate ندارند.

---

## 3.6 بررسی آماده‌سازی یا Preflight

### 30. عنوان `بررسی آماده‌سازی مسیرها / Preflight`

یک بررسی سبک و read-only قبل از اجرای اصلی است.

تصویر ذهنی:

```text
Preflight = بررسی وسایل و ورودی‌های لازم
Gate Run = اجرای بررسی واقعی
```

### 31. متن توضیح Preflight

یادآوری می‌کند که Preflight مسیرها، فایل‌های لازم و شکل کلی JSON را بررسی می‌کند، اما جای Gate واقعی را نمی‌گیرد.

### 32. دکمه `بررسی مسیرها و ورودی‌ها`

موارد زیر را بررسی می‌کند:

- وجود و parse شدن JSON؛
- object بودن JSON؛
- هماهنگی `stage` با transition؛
- استفاده نشدن `result.json` قبلی به‌عنوان source bundle؛
- پر بودن مسیرهای لازم؛
- وجود و directory بودن مسیرها؛
- وارد نشدن GitHub URL؛
- وجود نشانه Git checkout مانند `.git`؛
- وجود فایل‌های pin‌شده لازم؛
- وجود lock manifest مربوطه.

### 33. محدودیت Preflight

Preflight این موارد را انجام نمی‌دهد:

- hash verification کامل؛
- schema validation نهایی؛
- اجرای validator رسمی؛
- اجرای adapter رسمی؛
- transition واقعی؛
- اصلاح خودکار JSON؛
- clone یا pull repository.

### 34. کادر نتیجه Preflight

بعد از اجرا یکی از وضعیت‌های کلی زیر را نشان می‌دهد:

```text
ready
warnings
blocked
```

نمادهای هر check:

| نماد | معنی |
|---|---|
| `✓` | موفق |
| `⚠️` | هشدار |
| `❌` | خطای مسدودکننده |
| `↷` | برای transition فعلی لازم نیست |
| `؟` | نامشخص |

هر check ممکن است جزئیات فنی، classification و اقدام پیشنهادی نیز داشته باشد.

---

## 3.7 خلاصه نتیجه

### 35. عنوان `خلاصه نتیجه`

نتیجه قابل‌فهم برای اپراتور را نشان می‌دهد.

### 36. وضعیت `accepted`

بررسی فقط در محدوده evidence فعلی پذیرفته شده است. این وضعیت معادل production-ready نیست.

### 37. وضعیت `repair_needed`

ورودی قابل فهم است، اما قبل از ادامه نیاز به اصلاح دارد.

### 38. وضعیت `insufficient_evidence`

evidence، checkout، lock، validator، owner file یا proof لازم کافی نیست. این status مسدودکننده است.

### 39. وضعیت `invalid`

JSON، schema identity، path، hash، transition selection یا اجرای service/engine نامعتبر بوده است.

### 40. راهنمای عملیاتی داخل خلاصه

خلاصه نتیجه تلاش می‌کند به این پرسش‌ها پاسخ دهد:

- Gate کجا متوقف شد؟
- چه چیزی درست پیش رفت؟
- مشکل فعلی چیست؟
- اقدام بعدی دقیق چیست؟
- آیا output مرحله بعد ساخته شد؟
- ادامه دادن امن است؟
- آیا repair prompt آماده وجود دارد؟

---

## 3.8 Diagnostics

### 41. عنوان `جزئیات پیشرفته / Diagnostics`

جدول read-only دلایل فنی نتیجه است.

### 42. ستون `code`

شناسه diagnostic برای جست‌وجو در کد، مستندات، issue یا repair prompt است.

مثال:

```text
PG.UI.PREFLIGHT_WRONG_STAGE_FOR_TRANSITION
```

### 43. ستون `severity`

شدت diagnostic را نشان می‌دهد؛ مانند:

```text
error
warning
insufficient_evidence
info
```

### 44. ستون `path`

محل مشکل را در JSON یا contract نشان می‌دهد:

```text
$
$.stage
$.producer.commit_sha
```

### 45. ستون `message`

توضیح انسانی مشکل است.

### 46. ستون `owner/repo`

مشخص می‌کند اصلاح مشکل معمولاً بر عهده کدام owner یا repository است.

### 47. ستون `next action`

اقدام پیشنهادی بعدی را نشان می‌دهد؛ مانند اصلاح path، تهیه evidence یا استفاده از source bundle درست.

---

## 3.9 Capabilities

### 48. عنوان `وضعیت قابلیت‌ها / Capabilities`

snapshot قابلیت‌های ثبت‌شده repository را نمایش می‌دهد.

این جدول probe زنده سیستم شما نیست و سلامت checkoutهای محلی را اثبات نمی‌کند.

### 49. ردیف‌های اصلی

```text
Architect → CE
CE → Builder
Builder → Responsive
Final Evidence Gate
UI
```

### 50. ستون `بخش`

نام transition یا قابلیت است.

### 51. ستون `orchestration`

وضعیت implementation هسته orchestration را نشان می‌دهد.

### 52. ستون `CLI`

وضعیت exposure از طریق CLI را نشان می‌دهد؛ مانند `implemented` یا `guarded`.

### 53. ستون `evidence`

وضعیت evidence واقعی و غیر synthetic را نشان می‌دهد. وجود implementation به‌تنهایی معادل real handoff evidence نیست.

### 54. ستون `UI status`

نشان می‌دهد قابلیت چگونه به UI متصل شده است؛ برای مثال:

```text
wired through internal service; guarded/fail-closed
```

### 55. ستون `توضیح`

معنای عملی وضعیت را برای اپراتور توضیح می‌دهد.

---

## 3.10 پیش‌نمایش JSON

### 56. عنوان `پیش‌نمایش JSON / result.json`

نتیجه machine-readable اجرای UI و service را با syntax highlighting نمایش می‌دهد.

ساختار نمونه:

```json
{
  "schema_version": "...",
  "result_type": "...",
  "transition_choice": "...",
  "status": "...",
  "diagnostics": [],
  "engine_result": {},
  "output": null
}
```

`result.json` گزارش اجرای Project Gate است و به‌صورت خودکار ورودی مرحله بعد نیست.

اگر:

```json
"output": null
```

باشد، downstream input package تولید نشده است.

---

## 3.11 دانلود خروجی‌ها

### 57. بخش `دانلود خروجی‌ها`

پس از اجرا، UI تلاش می‌کند این فایل‌ها را بسازد:

```text
result.json
report.md
report.html
```

### 58. `result.json`

نسخه machine-readable نتیجه برای automation، audit و تحلیل diagnostics است.

### 59. `report.md`

گزارش Markdown مناسب GitHub، VS Code، issue و PR است.

### 60. `report.html`

گزارش HTML برای مشاهده مستقیم در مرورگر است.

### 61. رفتار هنگام خطای نوشتن فایل

اگر ساخت فایل‌ها fail شود، UI نباید لینک دانلود موفق جعلی نشان دهد. فایل‌های نیمه‌نوشته‌شده پاک می‌شوند و لیست دانلود خالی می‌ماند.

---

## 3.12 اجزای footer مربوط به Gradio

### `تنظیمات`

متعلق به framework رابط یعنی Gradio است و transition، schema یا evidence Project Gate را تغییر نمی‌دهد.

### `ساخته شده با Gradio`

فقط framework رابط کاربری را معرفی می‌کند.

### `استفاده از طریق API`

ممکن است endpointهای خودکار Gradio را نمایش دهد. API قراردادی Project Gate همان service داخلی مستندشده است و endpoint خودکار Gradio نباید بدون قرارداد جداگانه، API عمومی و پایدار EV4 فرض شود.

---

# 4. سناریوهای رایج

## 4.1 فقط می‌خواهم JSON را اعتبارسنجی کنم

1. `Validate Stage Evidence Bundle` را انتخاب کن.
2. `pinned_owner_file_computation` را نگه دار.
3. JSON را upload یا paste کن.
4. Preflight را اجرا کن.
5. بررسی اصلی را اجرا کن.
6. انتظار تولید downstream output نداشته باش.

## 4.2 می‌خواهم Architect → CE را اجرا کنم

1. `Architect → CE` را انتخاب کن.
2. source bundle با `stage=architect` را وارد کن.
3. مسیر local Architect و CE را بده.
4. Preflight را اجرا کن.
5. خطاهای path، lock یا file را رفع کن.
6. Gate را اجرا کن.
7. فقط اگر status و output معتبر بودند، output تولیدشده را برای مرحله CE استفاده کن.

## 4.3 می‌خواهم فقط قابلیت‌ها را ببینم

1. `Inspect Capabilities` را انتخاب کن.
2. JSON و path لازم نیست.
3. بررسی اصلی را اجرا کن.
4. جدول را به‌عنوان repository snapshot بخوان، نه runtime probe سیستم.

---

# 5. اشتباه‌های رایج

## اشتباه 1: وارد کردن GitHub URL در فیلد path

فیلدها به local filesystem path نیاز دارند.

## اشتباه 2: استفاده از `result.json` به‌عنوان ورودی transition بعدی

`result.json` گزارش است. فقط downstream artifact واقعی و مجاز باید وارد مرحله بعد شود.

## اشتباه 3: نادیده گرفتن `insufficient_evidence`

این status هشدار عادی نیست؛ ادامه کار باید تا تهیه evidence لازم متوقف شود.

## اشتباه 4: تصور اینکه Capabilities وضعیت زنده سیستم را نشان می‌دهد

این جدول از capability source repository خوانده می‌شود.

## اشتباه 5: استفاده هم‌زمان از Upload و Paste

در صورت وجود متن Paste، فایل upload شده اولویت ندارد. فقط یک source انتخاب کن.

## اشتباه 6: برداشت production readiness از `accepted`

`accepted` فقط در محدوده Gate و evidence فعلی معتبر است.

---

# 6. Troubleshooting سریع

| وضعیت | بررسی اولیه |
|---|---|
| JSON خوانده نمی‌شود | syntax، encoding و object بودن JSON را بررسی کن |
| `wrong_stage` | transition یا `stage` فایل را اصلاح کن |
| path وجود ندارد | path را از File Explorer یا terminal دوباره کپی کن |
| GitHub URL detected | repository را clone کن و local path بده |
| pinned file missing | checkout را روی revision مورد انتظار به‌روز کن |
| `insufficient_evidence` | diagnostics را برای missing evidence، checkout یا owner tooling بخوان |
| `output: null` | بررسی کن که مسیر validation-only نباشد و Gate قبل از تولید output متوقف نشده باشد |
| فایل دانلود ساخته نشد | permission و filesystem path را بررسی کن؛ موفقیت دانلود نباید فرض شود |

---

# 7. اجرای محلی

روش اصلی:

```bash
uv sync --extra dev --extra ui
uv run python -m ev4_transition.ui.app
```

entry point جایگزین:

```bash
uv run ev4-project-gate-ui
```

fallback در نبود `uv`:

```bash
python -m pip install -e '.[dev,ui]'
python -m ev4_transition.ui.app
```

---

# 8. منابع فنی مرتبط

- `src/ev4_transition/ui/app.py`
- `src/ev4_transition/ui/adapters.py`
- `src/ev4_transition/ui/components.py`
- `src/ev4_transition/ui/preflight_components.py`
- `src/ev4_transition/ui/state.py`
- `src/ev4_transition/service/preflight_core.py`
- `src/ev4_transition/data/capability-status.v1.json`
- `docs/OPERATOR_GUIDE.md`
- `docs/UI_OPERATOR_PANEL.md`
- `docs/UI_SERVICE_CONTRACT.md`

---

# 9. قانون نگهداری این سند

هر تغییر در یکی از موارد زیر باید با بازبینی این راهنما همراه باشد:

- componentهای قابل مشاهده در `src/ev4_transition/ui/app.py`؛
- transition choiceها؛
- acquisition modeها؛
- path requirementها؛
- status semantics؛
- Diagnostics columns؛
- download artifactها؛
- Preflight behavior.

این سند نباید capability جدید، evidence جدید یا readiness claim جدیدی اضافه کند که در کد و capability source رسمی repository پشتیبانی نشده است.
