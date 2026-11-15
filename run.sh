#!/usr/bin/env bash
# run.sh - Mr. Timer launcher for Linux/macOS.
# Loads BOT_TOKEN from .env if needed, bootstraps .venv on first run, starts the bot.
set -euo pipefail
cd "$(dirname "$0")"

# ---- 1) Load BOT_TOKEN from .env if it is not already in the environment ----
if [ -z "${BOT_TOKEN:-}" ] && [ -f .env ]; then
  while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in ''|'#'*) continue ;; esac
    case "$line" in *'='*) ;; *) continue ;; esac
    key="${line%%=*}"; value="${line#*=}"
    value="${value%$'\r'}"                      # strip CR if .env came from Windows
    [ "${key//[[:space:]]/}" = "BOT_TOKEN" ] && { BOT_TOKEN="$value"; export BOT_TOKEN; }
  done < .env
fi
if [ -z "${BOT_TOKEN:-}" ]; then
  echo "ERROR: BOT_TOKEN is not set." >&2
  echo "Copy .env.example to .env, paste your token from @BotFather after BOT_TOKEN=," >&2
  echo "or export BOT_TOKEN, then run this script again." >&2
  exit 1
fi

# ---- 2) Bootstrap the virtual environment on first run ----
if [ ! -x .venv/bin/python ]; then
  echo "First run: creating virtual environment .venv ..."
  python3 -m venv .venv
  echo "First run: installing dependencies from requirements.txt ..."
  .venv/bin/python -m pip install --disable-pip-version-check -q -r requirements.txt
fi

# ---- 3) Run the bot ----
echo "Starting Mr. Timer... Press Ctrl+C to stop."
exec .venv/bin/python bot.py
