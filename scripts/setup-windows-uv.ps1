$ErrorActionPreference = "Stop"

$ScriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
$Root = Resolve-Path (Join-Path $ScriptDir "..")
Set-Location $Root

function Write-Info($Message) {
    Write-Host "==> $Message"
}

Write-Info "EV4 Project Gate uv setup / راه‌اندازی uv برای Project Gate"

$Uv = Get-Command uv -ErrorAction SilentlyContinue
if (-not $Uv) {
    Write-Host "uv was not found on PATH. This script will not install remote tools automatically."
    Write-Host "uv در PATH پیدا نشد. این اسکریپت هیچ ابزار اینترنتی را خودکار نصب نمی‌کند."
    Write-Host "Official install options / گزینه‌های رسمی نصب:"
    Write-Host "  winget install --id=astral-sh.uv -e"
    Write-Host "  powershell -ExecutionPolicy ByPass -c \"irm https://astral.sh/uv/install.ps1 | iex\""
    Write-Host "Inspect installer first / قبل از اجرا بررسی کن:"
    Write-Host "  powershell -c \"irm https://astral.sh/uv/install.ps1 | more\""
    exit 1
}

Write-Info "uv version"
uv --version

Write-Info "Install Python 3.11 if needed / نصب Python 3.11 در صورت نیاز"
uv python install 3.11

Write-Info "Sync locked project environment with dev and ui extras / همگام‌سازی محیط با extraهای dev و ui"
uv sync --locked --extra dev --extra ui

Write-Info "Smoke check / بررسی سریع"
uv run --locked ev4-transition inspect

Write-Host ""
Write-Host "Next commands / دستورهای بعدی:"
Write-Host "  uv run --locked python -m ev4_transition.ui.app"
Write-Host "  uv run --locked python scripts/run-project-gate-demo.py"
Write-Host "  uv run --locked pytest"
Write-Host ""
Write-Host "Reminder: demos use synthetic fixtures and do not prove production readiness, real Elementor validation, frontend correctness, responsive correctness, accessibility completion, export validation, or real end-to-end readiness."
Write-Host "یادآوری: demoها synthetic هستند و اثبات readiness واقعی یا validation واقعی Elementor نیستند."
