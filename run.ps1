# run.ps1 - Mr. Timer launcher for Windows PowerShell.
# Loads BOT_TOKEN from .env if needed, bootstraps .venv on first run, starts the bot.
# If your policy blocks scripts:  powershell -ExecutionPolicy Bypass -File .\run.ps1

$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

# ---- 1) Load BOT_TOKEN from .env if it is not already in the environment ----
if (-not $env:BOT_TOKEN -and (Test-Path .env)) {
    foreach ($line in Get-Content .env) {
        if ($line -match '^\s*#' -or $line -notmatch '=') { continue }
        $key, $value = $line -split '=', 2
        if ($key.Trim().ToUpper() -eq 'BOT_TOKEN') { $env:BOT_TOKEN = $value.Trim() }
    }
}
if (-not $env:BOT_TOKEN) {
    Write-Host 'ERROR: BOT_TOKEN is not set.'
    Write-Host 'Copy .env.example to .env, paste your token from @BotFather after BOT_TOKEN=,'
    Write-Host 'or set the BOT_TOKEN environment variable, then run this script again.'
    exit 1
}

# ---- 2) Bootstrap the virtual environment on first run ----
if (-not (Test-Path .venv/Scripts/python.exe)) {
    Write-Host 'First run: creating virtual environment .venv ...'
    & python -m venv .venv
    if ($LASTEXITCODE -ne 0) { Write-Host 'ERROR: could not create a virtual environment. Install Python 3.12+ (python.org) and retry.'; exit 1 }
    Write-Host 'First run: installing dependencies from requirements.txt ...'
    & .venv/Scripts/python.exe -m pip install --disable-pip-version-check -q -r requirements.txt
    if ($LASTEXITCODE -ne 0) { Write-Host 'ERROR: pip install failed. Check your internet connection and retry.'; exit 1 }
}

# ---- 3) Run the bot ----
Write-Host 'Starting Mr. Timer... Press Ctrl+C to stop.'
& .venv/Scripts/python.exe bot.py
exit $LASTEXITCODE
