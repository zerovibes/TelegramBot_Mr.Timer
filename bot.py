"""Mr. Timer — Telegram-бот-таймер на aiogram 3.x.

Несколько таймеров на чат с переиспользуемыми номерами; всё состояние — в памяти процесса.
"""

import asyncio
import math
import os
import re
import sys
import time
from dataclasses import dataclass

from aiogram import Bot, Dispatcher, Router
from aiogram.exceptions import TelegramForbiddenError
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

HELP_TEXT = (
    "🤖 Я Mr. Timer. Команды: /timer 30s — установить таймер, "
    "/list — посмотреть активные таймеры, "
    "/cancel — отменить все, /cancel 2 — отменить по номеру, "
    "/help — полный список."
)
HELP_DETAIL = (
    "🤖 Я Mr. Timer — бот-напоминалка. Полный список команд:\n"
    "\n"
    "<b>Команды</b>\n"
    "/timer <i>&lt;длительность&gt;</i> — установить таймер; можно держать несколько сразу\n"
    "/list — посмотреть все активные таймеры и остаток времени\n"
    "/cancel — отменить все таймеры этого чата\n"
    "/cancel <i>&lt;номер&gt;</i> — отменить один таймер (номер из /list)\n"
    "/help — эта справка\n"
    "/start — короткое приветствие\n"
    "\n"
    "<b>Длительность</b>\n"
    "<pre>\n"
    "45s        — 45 секунд\n"
    "10m        — 10 минут\n"
    "2h         — 2 часа\n"
    "2m30s      — 2 минуты 30 секунд\n"
    "1h35m24s   — 1 час 35 минут 24 секунды\n"
    "</pre>\n"
    "Единицы можно совмещать в одной команде: порядок h→m→s,\n"
    "каждая единица не более одного раза. Регистр не важен\n"
    "(2H = 2h). Хотя бы одно число должно быть больше нуля.\n"
    "\n"
    "<b>Номера</b>\n"
    "Номера #1, #2… выдаются по чату от самого малого\n"
    "свободного: как только таймер сработает или будет отменён,\n"
    "его номер переиспользуется следующим."
)
BAD_DURATION_TEXT = (
    "⚠️ Не понял длительность. Формат: /timer Nh, Nm, Ns или комбинированный "
    "1h35m24s (единицы в порядке h→m→s), где хотя бы одно N — целое число больше нуля. "
    "Примеры: /timer 30s, /timer 10m, /timer 1h35m24s"
)
BAD_CANCEL_ARG_TEXT = "⚠️ Укажите номер таймера из /list или отправьте /cancel без аргумента. Пример: /cancel 2."
NO_TIMERS_TEXT = "🔕 Активных таймеров нет."

router = Router()

DURATION_RE = re.compile(
    r"^(?:(?P<h>\d+)h)?(?:(?P<m>\d+)m)?(?:(?P<s>\d+)s)?$", re.IGNORECASE
)


@dataclass
class TimerRecord:
    timer_id: int
    task: asyncio.Task
    seconds: int
    expires_at: float


# Состояние только в памяти процесса: потеря таймеров при рестарте допустима.
# timers[chat_id][timer_id] -> TimerRecord: несколько таймеров на чат.
timers: dict[int, dict[int, TimerRecord]] = {}


def pluralize(n: int, unit: str) -> str:
    """Русская плюрализация для целого n > 0; unit — 'h', 'm', 's' или 'timer'."""
    if n % 10 == 1 and n % 100 != 11:
        return {"h": "час", "m": "минуту", "s": "секунду", "timer": "таймер"}[unit]
    if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
        return {"h": "часа", "m": "минуты", "s": "секунды", "timer": "таймера"}[unit]
    return {"h": "часов", "m": "минут", "s": "секунд", "timer": "таймеров"}[unit]


def human(seconds: int) -> str:
    """Длительность из секунд > 0 в читаемый вид: '1 час 35 минут 24 секунды'."""
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    parts = []
    if h:
        parts.append(f"{h} {pluralize(h, 'h')}")
    if m:
        parts.append(f"{m} {pluralize(m, 'm')}")
    if s:
        parts.append(f"{s} {pluralize(s, 's')}")
    return " ".join(parts)


def remaining_text(record: TimerRecord) -> str:
    rem = math.ceil(record.expires_at - time.monotonic())
    if rem <= 0:
        return "меньше секунды"
    return human(rem)


def next_timer_id(chat: dict[int, TimerRecord]) -> int:
    # Нумерация по активным таймерам чата: малейший свободный номер,
    # освободившиеся (сработали/отменены) переиспользуются — «125» не накопится.
    timer_id = 1
    while timer_id in chat:
        timer_id += 1
    return timer_id


def forget(chat_id: int, record: TimerRecord) -> None:
    # Удаляем только свою запись: номер мог уже переиспользоваться новым
    # таймером, поэтому сверяем identity объекта, а не номер.
    chat = timers.get(chat_id)
    if chat is not None and chat.get(record.timer_id) is record:
        del chat[record.timer_id]
        if not chat:
            timers.pop(chat_id, None)


async def timer_task(bot: Bot, chat_id: int, record: TimerRecord) -> None:
    try:
        # Спим строго по разобранной длительности, а не по expires_at.
        await asyncio.sleep(record.seconds)
        try:
            await bot.send_message(
                chat_id,
                f"⏰ Время вышло! #{record.timer_id} на {human(record.seconds)}.",
            )
        except TelegramForbiddenError:
            # Пользователь заблокировал бота: молча удаляем свою запись.
            forget(chat_id, record)
    except asyncio.CancelledError:
        # Отменённый таймер (/cancel) не отправляет ничего; свою запись
        # уже удалил тот, кто вызвал cancel().
        return
    else:
        forget(chat_id, record)


@router.message(Command("timer"))
async def handle_timer(message: Message, command: Command) -> None:
    args = (command.args or "").strip()
    match = DURATION_RE.fullmatch(args)
    seconds = 0
    if match:
        seconds = (
            3600 * int(match["h"] or 0) + 60 * int(match["m"] or 0) + int(match["s"] or 0)
        )
    if match is None or seconds <= 0:
        await message.answer(BAD_DURATION_TEXT)
        return

    chat_id = message.chat.id
    chat = timers.setdefault(chat_id, {})
    timer_id = next_timer_id(chat)
    record = TimerRecord(
        timer_id=timer_id, task=None, seconds=seconds,  # type: ignore[arg-type]
        expires_at=time.monotonic() + seconds,
    )
    record.task = asyncio.create_task(timer_task(message.bot, chat_id, record))
    # Выбор номера и запись в dict идут одним синхронным шагом (без await между
    # ними), поэтому два конкурентных /timer не могут выбрать один и тот же номер.
    chat[timer_id] = record

    await message.answer(f"⏱️ Таймер #{timer_id} на {human(seconds)} установлен")


@router.message(Command("list"))
async def handle_list(message: Message) -> None:
    chat = timers.get(message.chat.id)
    if not chat:
        await message.answer(NO_TIMERS_TEXT)
        return
    lines = [f"📋 У вас {len(chat)} {pluralize(len(chat), 'timer')}:"]
    for record in sorted(chat.values(), key=lambda r: r.expires_at):
        lines.append(
            f"#{record.timer_id} — {human(record.seconds)}, осталось {remaining_text(record)}"
        )
    await message.answer("\n".join(lines))


@router.message(Command("cancel"))
async def handle_cancel(message: Message, command: Command) -> None:
    chat_id = message.chat.id
    args = (command.args or "").strip()

    # /cancel — снимаем все таймеры чата одним pop'ом, затем cancel() каждой задачи.
    if not args:
        chat = timers.pop(chat_id, None)
        if not chat:
            await message.answer(NO_TIMERS_TEXT)
            return
        for record in chat.values():
            record.task.cancel()
        await message.answer(f"🛑 Отменено: {len(chat)} {pluralize(len(chat), 'timer')}")
        return

    # /cancel <номер> — снимаем один таймер по номеру из /list.
    if not args.isdigit():
        await message.answer(BAD_CANCEL_ARG_TEXT)
        return
    timer_id = int(args)
    chat = timers.get(chat_id)
    record = chat.pop(timer_id, None) if chat is not None else None
    if record is None:
        await message.answer(f"🔕 Нет активного таймера #{timer_id}.")
        return
    record.task.cancel()
    if not timers.get(chat_id):
        timers.pop(chat_id, None)
    await message.answer(f"🛑 Таймер #{timer_id} отменён.")


@router.message(Command("help"))
async def handle_help(message: Message) -> None:
    await message.answer(HELP_DETAIL, parse_mode="HTML")


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
