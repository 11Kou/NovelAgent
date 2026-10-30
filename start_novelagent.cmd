@echo off
setlocal
title NovelAgent
pushd "%~dp0"

if not exist "backend\.venv\Scripts\python.exe" (
    echo [ERROR] Backend Python environment was not found.
    echo Please follow the Setup section in README.md first.
    popd
    pause
    exit /b 1
)

"backend\.venv\Scripts\python.exe" "scripts\dev_start.py" --no-reload --open %*
set "launch_result=%errorlevel%"
popd
if not "%launch_result%"=="0" (
    echo.
    echo [ERROR] NovelAgent could not start. See the message above.
    pause
)
exit /b %launch_result%
