@echo off
setlocal EnableExtensions
chcp 65001 >nul
rem =====================================================================
rem  run.bat - Mr. Timer launcher for Windows (cmd).
rem  1. Loads BOT_TOKEN from .env if it is not already in the environment.
rem  2. On first run creates .venv and installs requirements.txt.
rem  3. Starts the bot. Press Ctrl+C to stop.
rem =====================================================================

cd /d "%~dp0"

rem ---- 1) Load BOT_TOKEN from .env if not already defined ----
if not defined BOT_TOKEN if exist ".env" (
  for /f "usebackq eol=# tokens=1* delims==" %%a in (".env") do if /i "%%a"=="BOT_TOKEN" set "BOT_TOKEN=%%b"
)

rem ---- 2) Fail early with a clear message if the token is missing ----
if not defined BOT_TOKEN (
  echo ERROR: BOT_TOKEN is not set.
  echo Copy .env.example to .env, paste your token from @BotFather after BOT_TOKEN=,
  echo or set the BOT_TOKEN environment variable, then run this script again.
  exit /b 1
)

rem ---- 3) Bootstrap the virtual environment on first run ----
if not exist ".venv\Scripts\python.exe" (
  echo First run: creating virtual environment .venv ...
  call :make_venv
  if errorlevel 1 (
    echo ERROR: could not create a virtual environment. Install Python 3.12+ ^(python.org^) and retry.
    exit /b 1
  )
  echo First run: installing dependencies from requirements.txt ...
  ".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q -r requirements.txt
  if errorlevel 1 (
    echo ERROR: pip install failed. Check your internet connection and retry.
    exit /b 1
  )
)

rem ---- 4) Run the bot ----
echo Starting Mr. Timer... Press Ctrl+C to stop.
".venv\Scripts\python.exe" bot.py
set "RC=%ERRORLEVEL%"
endlocal & exit /b %RC%

rem ---- helpers ----
:make_venv
py -3.12 -m venv .venv 2>nul && exit /b 0
py -3 -m venv .venv 2>nul && exit /b 0
python -m venv .venv 2>nul && exit /b 0
exit /b 1
