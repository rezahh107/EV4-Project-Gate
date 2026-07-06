@echo off
setlocal
cd /d "%~dp0"
title EV4 Project Gate Launcher

echo ==========================================
echo       EV4 Project Gate - Local UI
echo ==========================================
echo.

where uv >nul 2>nul
if errorlevel 1 (
    echo [ERROR] uv was not found on PATH. / uv dar PATH peyda nashod.
    echo Install it with: / Ba in dastoor nasb kon:
    echo winget install --id=astral-sh.uv -e
    echo Then close and reopen the terminal. / Bad terminal ra beband va dobare baz kon.
    pause
    exit /b 1
)

if not exist "pyproject.toml" (
    echo [ERROR] pyproject.toml was not found. / File pyproject.toml peyda nashod.
    echo Keep this file in the repository root. / In file ra dar rishe repository negah dar.
    pause
    exit /b 1
)

echo [1/2] Checking project dependencies... / Dar hale barrasi dependency-ha...
uv sync --locked --extra dev --extra ui
if errorlevel 1 (
    echo [ERROR] Dependency setup failed. / Nasb ya sync dependency-ha namovafagh bood.
    echo Review the error above and try again. / Khata-ye bala ra barrasi kon va dobare emtehan kon.
    pause
    exit /b 1
)

echo.
echo [2/2] Starting EV4 Project Gate... / Dar hale ejraye EV4 Project Gate...
echo Open the local URL shown below in your browser. / Adresse local zir ra dar browser baz kon.
echo Keep this window open. Press Ctrl+C to stop the app.
echo In panjere ra baz negah dar. Baraye tavaghof Ctrl+C bezan.
echo.

uv run --locked ev4-project-gate-ui

set "APP_EXIT=%ERRORLEVEL%"
echo.
if not "%APP_EXIT%"=="0" echo [ERROR] The app stopped with exit code %APP_EXIT%. / Barname ba code %APP_EXIT% motavaqef shod.
if "%APP_EXIT%"=="0" echo EV4 Project Gate has stopped. / EV4 Project Gate motavaqef shod.
pause
exit /b %APP_EXIT%
