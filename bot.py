"""Mr. Timer — Telegram-бот-таймер на aiogram 3.x.

Одноместный бот: один активный таймер на чат, всё состояние — в памяти процесса.
"""

import asyncio
import os
import re
import sys
import time
from dataclasses import dataclass

from aiogram import Bot, Dispatcher, Router
from aiogram.exceptions import TelegramForbiddenError
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

HELP_TEXT = "Я Mr. Timer. Команды: /timer 30s — установить таймер, /cancel — отменить."
BAD_DURATION_TEXT = (
    "Не понял длительность. Формат: /timer Nh, Nm или Ns, где N — целое число больше нуля. "
    "Примеры: /timer 30s, /timer 10m, /timer 2h"
)
EXPIRED_TEXT = "Время вышло!"
NO_TIMER_TEXT = "Нет активного таймера"
CANCELLED_TEXT = "Таймер отменён"

router = Router()

DURATION_RE = re.compile(r"^(?P<n>\d+)(?P<u>[hmsHMS])$")
UNIT_SECONDS = {"h": 3600, "m": 60, "s": 1}


@dataclass
class TimerRecord:
    task: asyncio.Task
    expires_at: float


# Состояние только в памяти процесса: потеря таймеров при рестарте допустима.
timers: dict[int, TimerRecord] = {}


def pluralize(n: int, unit: str) -> str:
    """Русская плюрализация для целого n > 0; unit — 'h', 'm' или 's'."""
    if n % 10 == 1 and n % 100 != 11:
        return {"h": "час", "m": "минуту", "s": "секунду"}[unit]
    if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
        return {"h": "часа", "m": "минуты", "s": "секунды"}[unit]
    return {"h": "часов", "m": "минут", "s": "секунд"}[unit]


def forget(chat_id: int, record: TimerRecord) -> None:
    # Удаляем только свою запись: к моменту срабатывания в dict уже может
    # лежать TimerRecord нового /timer — его трогать нельзя.
    if timers.get(chat_id) is record:
        del timers[chat_id]


async def timer_task(bot: Bot, chat_id: int, seconds: int, record: TimerRecord) -> None:
    try:
        # Спим строго по разобранной длительности, а не по expires_at.
        await asyncio.sleep(seconds)
        try:
            await bot.send_message(chat_id, EXPIRED_TEXT)
        except TelegramForbiddenError:
            # Пользователь заблокировал бота: молча удаляем свою запись.
            forget(chat_id, record)
    except asyncio.CancelledError:
        # Отменённый таймер (замена /timer или /cancel) не отправляет ничего;
        # свою запись уже удалил тот, кто вызвал cancel().
        return
    else:
        forget(chat_id, record)


@router.message(Command("timer"))
async def handle_timer(message: Message, command: Command) -> None:
    args = (command.args or "").strip()
    match = DURATION_RE.fullmatch(args)
    if match is None or int(match.group("n")) <= 0:
        await message.answer(BAD_DURATION_TEXT)
        return

    n = int(match.group("n"))
    unit = match.group("u").lower()
    seconds = UNIT_SECONDS[unit] * n
    chat_id = message.chat.id

    # Один таймер на чат: снимаем старый, только потом создаём новый.
    old = timers.pop(chat_id, None)
    if old is not None:
        old.task.cancel()

    record = TimerRecord(task=None, expires_at=time.monotonic() + seconds)  # type: ignore[arg-type]
    record.task = asyncio.create_task(timer_task(message.bot, chat_id, seconds, record))
    timers[chat_id] = record

    await message.answer(f"Таймер на {n} {pluralize(n, unit)} установлен")


@router.message(Command("cancel"))
async def handle_cancel(message: Message) -> None:
    old = timers.pop(message.chat.id, None)
    if old is None:
        await message.answer(NO_TIMER_TEXT)
        return
    # Отменяем именно свою задачу: CancelledError она гасит внутри себя,
    # поэтому «Время вышло!» отменённому таймеру не придёт никогда.
    old.task.cancel()
    await message.answer(CANCELLED_TEXT)


@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    await message.answer(HELP_TEXT)


@router.message()
async def handle_unknown(message: Message) -> None:
    # Catch-all: неизвестные команды и произвольный текст.
    await message.answer(HELP_TEXT)


async def main() -> None:
    token = os.environ.get("BOT_TOKEN")
    if not token:
        print("Не задан BOT_TOKEN. Задай переменную окружения BOT_TOKEN и повтори запуск.")
        sys.exit(1)

    bot = Bot(token=token)
    dp = Dispatcher()
    dp.include_router(router)
    # Сессию закрывает сам polling (close_bot_session=True по умолчанию).
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
