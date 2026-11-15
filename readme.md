# Mr. Timer — Telegram reminder bot

A small, single-user Telegram bot for one-shot countdown reminders. You send `/timer 30s`, the bot confirms it, and when the time is up it sends you "Время вышло!" ("Time's up!"). Everything lives in the memory of one process — there is no database, no files and no external storage, so the whole bot is a single Python file.

## TL;DR

You already have Python 3.12 and a bot token? Then:

1. Copy `.env.example` to `.env` and paste your real token into it.
2. Windows: run `run.bat` (double-click it, or `run.bat` in `cmd`) — or `.\run.ps1` in PowerShell. Linux/macOS: `./run.sh`.
3. On the first run the script creates `.venv`, installs dependencies and starts the bot. Open your bot in Telegram and send `/start`.

## What it does

- **One active timer per chat.** A new `/timer` silently replaces the previous one (it is cancelled and will never ring). `/cancel` cancels the active timer.
- **Correct Russian plural forms** — `10 минут`, `2 минуты`, `1 секунду`, `11 часов` — handled by a dedicated `pluralize()` function.
- **Robust edge-case handling** — unreadable/zero/negative durations, missing arguments, unknown commands, arbitrary text, and users who blocked the bot.
- **In-memory only.** Timers are `asyncio` tasks in a dict. Restarting the bot loses them — by design.

### Commands

All bot replies are in Russian, exactly as written below.

| You send | Bot replies |
| --- | --- |
| `/start` or any unrecognized text | `Я Mr. Timer. Команды: /timer 30s — установить таймер, /cancel — отменить.` |
| `/timer <duration>` (e.g. `/timer 30s`, `/timer 10m`, `/timer 2h`) | `Таймер на 10 минут установлен` (matches your duration) |
| — when the timer fires | `Время вышло!` |
| `/cancel` (active timer) | `Таймер отменён` |
| `/cancel` (no active timer) | `Нет активного таймера` |
| `/timer` with unreadable duration (`/timer 3.5s`, `/timer 0s`, `/timer -5m`, `/timer 30s10`, `/timer` alone) | `Не понял длительность. Формат: /timer Nh, Nm или Ns, где N — целое число больше нуля. Примеры: /timer 30s, /timer 10m, /timer 2h` |

Duration format: one argument, `N` followed by a unit letter `s` (seconds), `m` (minutes) or `h` (hours), case-insensitive. `N` must be an integer greater than zero.

## Requirements

- **Python 3.12 or newer** (developed and tested on Python 3.12.11).
- **Telegram** account and a bot token from [@BotFather](https://t.me/BotFather).
- The only external dependency is `aiogram>=3.7,<4.0` (see `requirements.txt`); everything else is the Python standard library.
- An internet connection on first run (to install dependencies) and while the bot is running.

## Getting started, step by step

Follow these steps in order. No programming experience is needed for steps 1, 4 and 6.

### Step 1 — Create the bot and get its token (in Telegram)

1. Open Telegram (phone or desktop) and search for **`@BotFather`** — it is Telegram's official bot, with a blue verification badge.
2. Send `/newbot` to it.
3. BotFather asks for a **display name** — any text, e.g. `Mr. Timer`.
4. Then it asks for a **username**: unique, ending with `bot` (or `_bot`), e.g. `my_mister_timer_bot`. If Telegram says it is taken, try another one.
5. You will see a message `Use this token to access the HTTP API` followed by a long string like `123456789:AAHfk2m_...` — **this is your token**. Tap/click it to copy.
6. **Treat the token as a password:** whoever has it controls your bot. Never post it in chats or commit it to GitHub. If it leaks, send `/revoke` to @BotFather to generate a new one.

### Step 2 — Put the project on your machine

- **With Git:** `git clone https://github.com/<your-username>/<repo-name>.git`, then `cd <repo-name>`.
- **Without Git:** on GitHub click **Code → Download ZIP**, unzip it, and open the unzipped folder.

*How to open a terminal in that folder:* on Windows, open the folder in File Explorer, type `cmd` (or `powershell`) in the address bar and press Enter; on Linux/macOS, `cd ~/path/to/folder` in Terminal.

### Step 3 — Install Python 3.12 (only if it is not installed yet)

- **Windows:** download from [python.org/downloads](https://www.python.org/downloads/windows/) and during installation tick **"Add python.exe to PATH"**. Verify with `python --version` in `cmd`.
- **macOS:** install from [python.org](https://www.python.org/downloads/mac-osx/) or `brew install python@3.12`. Verify with `python3 --version`.
- **Ubuntu/Debian:** `sudo apt update && sudo apt install python3.12 python3.12-venv`. Verify with `python3 --version`.

### Step 4 — Give the launcher your token

The launcher scripts look for the token in the `BOT_TOKEN` environment variable first, then in a `.env` file. The recommended way is `.env`:

1. Copy `.env.example` to `.env` (on Windows: right-click → Copy, then Paste and rename; in a terminal: `copy .env.example .env` / `cp .env.example .env`).
2. Open `.env` in any plain text editor (Notepad is fine).
3. Replace the value after `BOT_TOKEN=` with your real token from step 1 — keep the `123:` part, the line must look like `BOT_TOKEN=123456789:AAHfk2m_...`. Save the file.

`.env` is listed in `.gitignore`, so it will never be uploaded to GitHub. `bot.py` itself never reads `.env` — the launcher scripts load it and pass the token to Python as a variable.

*Alternative (no `.env`):* set the variable yourself right before running —

```powershell
$env:BOT_TOKEN="123456789:AAHfk2m_..."; .\run.ps1
```

```bash
export BOT_TOKEN=123456789:AAHfk2m_...   # then: ./run.sh or .venv/bin/python bot.py
```

### Step 5 — Run the bot

| OS | Command |
| --- | --- |
| Windows (cmd) | `run.bat` |
| Windows (PowerShell) | `powershell -ExecutionPolicy Bypass -File .\run.ps1` (or `.\run.ps1` if script execution is allowed) |
| Linux / macOS | `./run.sh` (first time: `chmod +x run.sh` if it says "Permission denied") |

The first run takes a minute: the script creates a virtual environment `.venv`, installs `aiogram` into it, then starts the bot. After `Starting Mr. Timer... Press Ctrl+C to stop.` the bot is online. Keep the window open — closing it or pressing **Ctrl+C** stops the bot (and any active timer is lost, by design).

<details>
<summary>Manual alternative (what the scripts do inside)</summary>

```bash
python -m venv .venv                          # Windows: python -m venv .venv
# Windows: .venv\Scripts\activate  |  Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt     # Windows: .venv\Scripts\python.exe -m pip install -r requirements.txt
python bot.py                                 # or .venv\bin/python bot.py / .venv\Scripts\python.exe bot.py
```
</details>

### Step 6 — Test it in Telegram

The bot replies in Russian; send commands in English as shown.

1. Find your bot by its `@username` (or use the `t.me/...` link BotFather gave you) and open the chat. Press **Start** or send `/start` — you should get the help line.
2. Send `/timer 10s` → `Таймер на 10 секунд установлен`. Wait ~10 seconds → `Время вышло!` arrives on its own.
3. Send `/timer 1m` → `Таймер на 1 минуту установлен`.
4. Send `/timer 10s`, then immediately `/timer 10m` → the 10-second timer is silently replaced; only `Таймер на 10 минут установлен` will ever ring.
5. Send `/cancel` → `Таймер отменён`. Send `/cancel` again → `Нет активного таймера`.
6. Try bad durations: `/timer 3.5s`, `/timer 0s`, `/timer` (no argument) → each gets the format-hint message.
7. Send anything else, e.g. `hello` or `/help` → the same short help line as `/start`.

## Troubleshooting

| Symptom | Cause and fix |
| --- | --- |
| `TelegramUnauthorizedError: Unauthorized` at startup | The token is wrong, mistyped or revoked. Re-copy it from @BotFather into `.env` (or `/revoke` for a fresh one). |
| `Не задан BOT_TOKEN. Задай переменную окружения BOT_TOKEN и повтори запуск.` | `.env` is missing/empty, or you ran `python bot.py` directly without setting the variable. Use a launcher script or set `BOT_TOKEN` first. |
| `ModuleNotFoundError: No module named 'aiogram'` | Dependencies were installed outside the venv, or the venv is not active. Use `run.bat` / `run.ps1` / `run.sh`, or activate `.venv` first. |
| PowerShell says scripts are disabled | Run `powershell -ExecutionPolicy Bypass -File .\run.ps1`. |
| `./run.sh: Permission denied` | `chmod +x run.sh`, then `./run.sh`. |
| Bot says nothing at all | The window was closed / Ctrl+C pressed, or you blocked the bot in Telegram (unblock it and send `/start`). |
| Token works on your machine but timers vanish after restart | By design: state lives only in this process. |

## Project structure

```
.
├── bot.py            # the entire bot — one file, no TODOs, no stubs
├── requirements.txt  # single line: aiogram>=3.7,<4.0
├── run.bat           # Windows launcher (cmd): loads .env, bootstraps .venv, runs the bot
├── run.ps1           # Windows launcher (PowerShell), same behavior
├── run.sh            # Linux/macOS launcher, same behavior
├── .env.example      # token template — copy it to .env and fill in your token
├── .gitignore        # keeps .env, .venv and __pycache__ out of Git
└── readme.md         # this file
```

## How it works (short version)

- `main()` reads `BOT_TOKEN` from the environment (clean exit with code 1 if missing), then starts long polling via `Dispatcher.start_polling()` (aiogram 3.x).
- Each `/timer` parses `N` + unit from `command.args` with the regex `^(?P<n>\d+)(?P<u>[hmsHMS])$`, cancels any previous timer task, and schedules a new `asyncio.sleep()` task.
- The task sleeps strictly by the parsed duration, sends `Время вышло!` when it wakes, and deletes its own entry from the `timers` dict **only if the entry is still its own** (`timers.get(chat_id) is record`) — so a replaced or cancelled timer can never overwrite or delete the new one.
- `CancelledError` is swallowed inside the task, so a cancelled timer never sends anything. If the user blocked the bot, `TelegramForbiddenError` is caught and the entry is removed silently.

## Known limitations (by design)

- One active timer per chat; no combined durations like `1h30m`, no Cyrillic units, no upper duration limit, no persistence.
- State is process memory only: a restart loses all timers.
- Run the bot in a single process; running two copies would double every reply.

## Publishing this project to GitHub (reference)

```bash
git init
git add .
git commit -m "Mr. Timer: Telegram timer bot (aiogram 3.x, single-file)"
git branch -M main
git remote add origin https://github.com/<your-username>/<repo-name>.git
git push -u origin main
```

The `.gitignore` already excludes `.env`, `.venv/` and `__pycache__/`, so your token never leaves your machine.
