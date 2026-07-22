# EV4 Project Gate — GUI Producer-Emitted Architect → CE

## راهنمای فارسی اپراتور

### هدف

پنل `EV4 Project Gate Local Operator Panel` سطح اصلی و پشتیبانی‌شده برای اجرای واقعی Architect → CE است. عملیات عادی owner به فرمان CLI نیاز ندارد. CLI برای تست، اتوماسیون و debugging باقی می‌ماند و همان service مشترک را مصرف می‌کند.

### تفاوت artifactها

- `producer-gate-export.v1`: خروجی رسمی producer است. در حالت `producer_emitted_gate_artifact` فقط فایل اصلی JSON پذیرفته می‌شود، چون immutable snapshot و بازبینی هویت فایل به مسیر واقعی نیاز دارد.
- `stage-evidence-bundle.v1`: بسته شواهد مستقیم است و فقط با `Validate Stage Evidence Bundle` یا مسیر pinned سازگار اجرا می‌شود.
- `ev4-project-gate-ui-result.v1` و `project-gate-service-result.v1`: گزارش نتیجه‌اند و منبع transition نیستند. استفاده از آن‌ها به‌عنوان source با `PG.UI.RESULT_ARTIFACT_USED_AS_SOURCE` متوقف می‌شود.

### تشخیص آشکار مسیر

پس از انتخاب `architect-project-gate.json`، پنل schema و قرارداد producer را بررسی می‌کند. اگر export معتبر از Architect به `ce-intake` باشد، پیام زیر نمایش داده می‌شود و انتخاب‌ها همچنان قابل بازبینی‌اند:

> Producer Gate Export شناسایی شد. مسیر Architect → CE و روش دریافت producer_emitted_gate_artifact انتخاب شد.

Routing پنهان، fallback acquisition mode و استخراج دستی `final_stage_bundle` مجاز نیست.

### فایل اصلی اجباری است

Paste کردن JSON در حالت producer-emitted معتبر نیست. پنل قبل از dispatch با `PG.UI.PRODUCER_SOURCE_FILE_REQUIRED` متوقف می‌شود. فایل paste‌شده به فایل موقت authoritative تبدیل نمی‌شود و mode نیز خودکار تغییر نمی‌کند.

### مسیرهای پیش‌فرض محلی

در اولین اجرا:

- Project Gate: `E:\GitHub\EV4 Shared Contracts`
- Architect: `E:\GitHub\EV4-Architect-Repo`
- CE: `E:\GitHub\EV4 Constructability Engineer Repo`
- Builder: `E:\GitHub\Builder Assistant`
- Responsive: `E:\GitHub\EV4 Responsive Architect`
- Output: `E:\GitHub\EV4 Project Gate Outputs`

همه مسیرها editable هستند و Browse دارند. آخرین مقادیر پذیرفته‌شده در فایل زیر ذخیره می‌شوند و وارد Git نمی‌شوند:

`%APPDATA%\EV4-Project-Gate\operator-settings.json`

دکمه `Reset to defaults` فایل محلی را حذف و defaults را بازمی‌گرداند.

### هویت repository

نام پوشه local هویت repository نیست. کنترل authoritative از Git metadata، origin URL، expected owner/repository و pinهای موجود انجام می‌شود. بنابراین پوشه `E:\GitHub\EV4 Shared Contracts` هنگامی پذیرفته می‌شود که origin آن `rezahh107/EV4-Project-Gate` باشد. origin اشتباه، checkout مفقود، Git metadata غیرقابل‌خواندن یا pin mismatch به‌صورت fail-closed گزارش می‌شود.

### اجرای workflow

1. فایل اصلی `architect-project-gate.json` را Upload کنید.
2. تشخیص `producer-gate-export.v1` و انتخاب visible مسیر را بازبینی کنید.
3. مسیر checkoutها و output را بازبینی یا Browse کنید.
4. `بررسی نوع فایل و مسیرها` را اجرا کنید.
5. فقط پس از Ready شدن Preflight، `اجرای authoritative Project Gate` فعال می‌شود.
6. وضعیت immutable snapshot، validatorهای رسمی، transition و publication را در نتیجه و diagnostics بررسی کنید.
7. فایل‌های خروجی را دانلود یا با `Open output folder` پوشه واقعی اجرا را باز کنید.

### خروجی‌ها

برای هر اجرا یک پوشه collision-safe زیر output base ساخته می‌شود:

```text
<output-base>/run-<UTC timestamp>-<random>/
  ce-input.json
  project-gate-a2c-receipt.json
  result.json
  report.md
  report.html
```

- `ce-input.json`: ورودی مستقل و اعتبارسنجی‌شده مرحله CE.
- `project-gate-a2c-receipt.json`: receipt قابل‌راستی‌آزمایی Project Gate شامل provenance و hashهای publication.

فایل موجود overwrite نمی‌شود. success فقط بعد از publication و verification معتبر است.

### Diagnostics اصلی

- `PG.UI.PRODUCER_SOURCE_FILE_REQUIRED`: فایل اصلی را Upload کنید و Paste را پاک کنید.
- `PG.UI.SOURCE_SCHEMA_MODE_MISMATCH`: schema و acquisition mode را هماهنگ کنید.
- `PG.UI.SOURCE_SCHEMA_TRANSITION_MISMATCH`: transition انتخابی با producer stage/target سازگار نیست.
- `PG.UI.RESULT_ARTIFACT_USED_AS_SOURCE`: به‌جای result/report، source export اصلی را انتخاب کنید.
- diagnostics خانواده `PG_INT_REPOSITORY_*`: checkout، origin یا pin را اصلاح کنید.
- diagnostics snapshot خانواده `PG_A2C_INPUT_*`: فایل symlink، غیرعادی، تغییرکرده، غیر UTF-8 یا JSON نامعتبر را جایگزین کنید.
- diagnostics publication: output directory، collision یا دسترسی write را اصلاح کنید.

خطاهای غیرمنتظره در مرز UI مهار می‌شوند؛ traceback خام در نمای اصلی نمایش داده نمی‌شود. گزارش فنی و log محلی باید با correlation ID برای عیب‌یابی استفاده شوند.

---

## Technical English

The Local Operator Panel is the primary owner workflow. Both GUI and CLI submit `GateRequest` objects to the same `run_gate_request` service authority. For `producer_emitted_gate_artifact`, the service requires a real file path and delegates to `run_producer_handoff_request`, which uses the secure snapshot authority and the existing producer handoff facade.

The authoritative lifecycle preserves:

- strict Producer Gate Export intake and adoption/target contracts;
- immutable byte capture and SHA-256 source identity;
- symlink, non-regular file, UTF-8, strict JSON and mutation/replacement rejection;
- repository origin and pin checks based on Git metadata rather than folder names;
- official Architect and CE validators;
- transition-result validation;
- atomic verified publication and no-overwrite behavior;
- verified downstream receipt generation;
- fail-closed status and structured diagnostics.

The GUI is an adapter for source selection, visible route confirmation, local settings, preflight rendering, result rendering, downloads and opening the real output folder. It does not independently implement producer transition orchestration and does not shell out to the CLI.

Normal owner operation requires no CLI command.

## Repair architecture and repository-path contract

The operator surfaces are passive adapters. They construct `GateRequest` and call `run_gate_request`; they do not capture snapshots, resolve producer routes, call transition engines, or publish artifacts independently.

```text
GUI adapter ─┐
             ├─> GateRequest -> run_gate_request
CLI adapter ─┘                     |
                                    v
                         producer_handoff service
                                    |
                                    v
                immutable snapshot + Project Gate routing
                + repository identity/pins + validators
                + atomic publication + receipt verification
```

The shared repository-path contract is centralized in `service/transition_contracts.py`:

| Transition | Required repositories | Engine consumer |
| --- | --- | --- |
| `architect_to_ce` | Architect, CE | Architect/CE transition boundary |
| `ce_to_builder` | CE, Builder | CE/Builder transition boundary |
| `builder_to_responsive` | Builder, Responsive | Builder/Responsive transition boundary |
| `final_gate` | Project Gate, Responsive, Decision Kernel | Final Gate + Kernel L2 audit |

`project_gate_repo_path` remains available to producer-emitted A2C/C2B routing and is validated by the producer-handoff facade. A supplied `JsonInputSnapshot` is accepted only as an already-captured capability; its bytes, SHA-256, parsed value, source path, filesystem identity, and current source bytes are revalidated before routing. It does not select a different transition authority.

## Native UI runner boundaries

`Browse…` launches the Tk directory chooser in a bounded child process through `ev4_transition.runners.native_dialog`. This keeps Tk on the child process main thread and preserves the previous value on cancellation, timeout, malformed response, or unavailable GUI facilities. `Open output folder` is isolated in `ev4_transition.runners.open_output_folder` and uses argument vectors with `shell=False`.

## Exact-head CI evidence

The repair workflow checks out and verifies the exact PR Head, runs focused and full tests, constructs the Gradio demo, builds a wheel, clean-installs the wheel, imports packaged runner/UI modules, and creates source evidence outside the checkout tree. The evidence manifest records `tested_head_sha`, archive path, SHA-256 digest, and packaging result. Archive or manifest paths inside the source tree are rejected.

## Owner acceptance boundary

CI does not prove native Windows dialog behavior, repository checkouts on the owner workstation, or execution of the original non-synthetic Architect export. Owner acceptance remains mandatory and must verify the original source classification, visible route/mode, settings persistence/reset, repository origins and pins, immutable source identity, `ce-input.json`, `project-gate-a2c-receipt.json`, hashes/paths, reports, Browse, Open output folder, and operation without CLI.

## Request-bound authoritative Preflight

Source classification only suggests a compatible transition and acquisition mode. It never grants readiness. Every executable GUI and CLI request is built once as a complete `GateRequest` and evaluated by `service.preflight.run_preflight`.

A `ready` result carries a deterministic request fingerprint covering the transition, acquisition mode, source path and immutable source identity, every repository path including Decision Kernel, output root, schema/lock overrides, downstream publication arguments, timeout, evidence mode, and other dispatch-affecting fields. GUI execution sends that fingerprint back to `run_gate_request`; Runtime captures the current source snapshot, reruns the authoritative Preflight, recomputes the fingerprint, and refuses dispatch when the token is absent or stale.

Any change to an authority-bearing control clears the token immediately, disables Run, and clears the verified attempt-directory state. This includes source, transition, acquisition mode, pasted input, every repository path, and output root. Classification is not an execution authorization.

## Attempt directories and report publication

The service allocates one collision-safe `run-*` directory for every GUI/CLI execution attempt before publishing any result files. A successful Architect → CE attempt contains five verified files. An invalid or blocked attempt contains only the three verified reports:

```text
<output-root>/run-<unique-id>/
  result.json
  report.md
  report.html
```

The UI does not write report files. `service.report_publication` stages all three reports, publishes them with no-overwrite links, verifies exact bytes, and rolls the group back when staging, collision, concurrent creation, or post-write verification fails. Download paths are exposed only for verified existing files returned by the service. `Open output folder` consumes the service-returned verified attempt directory rather than parsing editable result JSON.

Existing fixed files directly under `<output-root>` are never replaced by either successful or failed attempts.
