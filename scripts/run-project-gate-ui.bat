@echo off
setlocal
set SCRIPT_DIR=%~dp0
set ROOT=%SCRIPT_DIR%..
set LAUNCHER=%ROOT%\scripts\run-project-gate-ui.py

py -3 "%LAUNCHER%"
if not errorlevel 9009 goto done

python "%LAUNCHER%"
if not errorlevel 9009 goto done

echo Python was not found. Install Python 3.11+ and run: python -m pip install -e '.[dev]'
echo Python peyda nashod. Aval Python 3.11 ya jadidtar ra nasb kon.
exit /b 1

:done
set EXIT_CODE=%ERRORLEVEL%
if not "%EXIT_CODE%"=="0" pause
exit /b %EXIT_CODE%
