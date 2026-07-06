# Persian RTL UI Contract

این سند قرارداد کوتاه RTL/LTR برای پنل محلی Project Gate است.

## Persian containers

هر متن visible فارسی در UI یا HTML report باید در container دارای ویژگی‌های زیر باشد:

```html
lang="fa" dir="rtl"
```

متن فارسی باید راست‌چین، کوتاه و عملیاتی باشد.

## Technical LTR isolation

موارد زیر همیشه technical content محسوب می‌شوند و باید LTR/copyable بمانند:

- JSON و raw diagnostics
- file path و repo path
- diagnostic code
- JSONPath
- schema id
- hash
- transition id
- CLI command
- package/module name

برای inline technical content از الگوی زیر استفاده شود:

```html
<bdi dir="ltr"><code>PG_A2C_EXTERNAL_HASH_MISMATCH</code></bdi>
```

برای block technical content از الگوی زیر استفاده شود:

```html
<pre dir="ltr"><code>{ ... }</code></pre>
```

## Report rule

HTML report باید با این ریشه ساخته شود:

```html
<html lang="fa" dir="rtl">
```

Raw JSON و raw diagnostics در report نباید RTL شوند.

## Traceback rule

traceback خام نباید در visible summary فارسی نمایش داده شود. اگر runtime failure رخ داد، summary باید diagnostic کنترل‌شده نشان دهد و raw/advanced channel را برای بررسی فنی نگه دارد.
