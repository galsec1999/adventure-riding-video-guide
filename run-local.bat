@echo off
setlocal
pushd "%~dp0"

where py >nul 2>nul
if %errorlevel% equ 0 (
    py -3 tools\serve_local.py %*
) else (
    where python >nul 2>nul
    if errorlevel 1 (
        echo ERROR: Python 3 was not found. Install Python 3 and try again. 1>&2
        popd
        exit /b 1
    )
    python tools\serve_local.py %*
)

set "SERVER_EXIT=%errorlevel%"
popd
exit /b %SERVER_EXIT%
