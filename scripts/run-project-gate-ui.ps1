$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Resolve-Path (Join-Path $ScriptDir "..")
$Launcher = Join-Path $Root "scripts\run-project-gate-ui.py"

$PyLauncher = Get-Command py -ErrorAction SilentlyContinue
if ($PyLauncher) {
    & py -3 $Launcher
    exit $LASTEXITCODE
}

$Python = Get-Command python -ErrorAction SilentlyContinue
if ($Python) {
    & python $Launcher
    exit $LASTEXITCODE
}

Write-Host "Python was not found. Install Python 3.11+ and run: python -m pip install -e '.[dev]'"
Write-Host "Python پیدا نشد. ابتدا Python 3.11 یا جدیدتر را نصب کن."
exit 1
