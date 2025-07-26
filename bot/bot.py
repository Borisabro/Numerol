import asyncio
import logging
import os
import tempfile
from collections import deque
from pathlib import Path

import speech_recognition as sr
from pydub import AudioSegment
from telegram import Update
from telegram.ext import (AIORateLimiter, Application, CommandHandler,
                          ContextTypes, MessageHandler, filters)

from numerology import life_path, expression, COLOR_MAP

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load bot token from environment
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("Set TELEGRAM_BOT_TOKEN environment variable")

# In-memory history per user
user_history: dict[int, deque] = {}
HISTORY_LIMIT = 10


# ------ Helpers ------

def add_history(user_id: int, calc_type: str, value: str, result: int):
    hist = user_history.setdefault(user_id, deque(maxlen=HISTORY_LIMIT))
    hist.appendleft({
        "type": calc_type,
        "value": value,
        "result": result,
        "color": COLOR_MAP.get(calc_type, "#000000"),
    })


def format_entry(entry: dict) -> str:
    return f"<b>{entry['type']}:</b> {entry['value']} = <b>{entry['result']}</b>"


# ------ Command handlers ------


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Привет! Я бот-нумеролог.\n"
        "Используйте /life ГГГГ-ММ-ДД для расчёта Числа жизненного пути\n"
        "или /name Ваше_Имя для Числа судьбы.\n"
        "Я также понимаю голосовые сообщения с датой рождения или именем."
    )
    await update.message.reply_text(text)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)


async def life_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Укажите дату: /life 1990-05-23")
        return
    date_str = context.args[0]
    try:
        num, desc = life_path(date_str)
        add_history(update.effective_user.id, "life_path", date_str, num)
        await update.message.reply_html(f"Ваше число жизненного пути: <b>{num}</b>\n{desc}")
    except ValueError as e:
        await update.message.reply_text(str(e))


async def name_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Укажите имя: /name Иван Иванов")
        return
    name = " ".join(context.args)
    try:
        num, desc = expression(name)
        add_history(update.effective_user.id, "expression", name, num)
        await update.message.reply_html(f"Ваше число судьбы: <b>{num}</b>\n{desc}")
    except ValueError as e:
        await update.message.reply_text(str(e))


async def history_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    hist = user_history.get(update.effective_user.id)
    if not hist:
        await update.message.reply_text("История пуста.")
        return
    text = "Последние расчёты:\n" + "\n".join(format_entry(e) for e in hist)
    await update.message.reply_html(text)


# ------ Voice handler ------


def recognize_voice(file_path: Path) -> str | None:
    recognizer = sr.Recognizer()
    with sr.AudioFile(str(file_path)) as source:
        audio = recognizer.record(source)
    try:
        return recognizer.recognize_google(audio, language="ru-RU")
    except sr.UnknownValueError:
        return None
    except sr.RequestError as e:
        logger.warning("Speech recognition error: %s", e)
        return None


async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice = update.message.voice
    file = await context.bot.get_file(voice.file_id)
    with tempfile.TemporaryDirectory() as tmpdir:
        ogg_path = Path(tmpdir) / "voice.ogg"
        wav_path = Path(tmpdir) / "voice.wav"
        await file.download_to_drive(str(ogg_path))
        # Convert OGG->WAV using pydub (requires ffmpeg)
        audio = AudioSegment.from_ogg(ogg_path)
        audio.export(wav_path, format="wav")
        text = recognize_voice(wav_path)
    if not text:
        await update.message.reply_text("Не удалось распознать речь.")
        return

    # Very naive parsing: if contains at least 6 digits treat as date (allow formats 1990-05-23 or 23-05-1990)
    date_candidate = ''.join(ch for ch in text if ch.isdigit() or ch == '-')
    if len([d for d in date_candidate if d.isdigit()]) >= 6 and '-' in date_candidate:
        try:
            num, desc = life_path(date_candidate)
            add_history(update.effective_user.id, "life_path", date_candidate, num)
            await update.message.reply_html(f"Ваше число жизненного пути: <b>{num}</b>\n{desc}")
            return
        except ValueError:
            pass  # fall back to name

    # Fallback: treat entire text as name
    name = text.strip().title()
    try:
        num, desc = expression(name)
        add_history(update.effective_user.id, "expression", name, num)
        await update.message.reply_html(f"Ваше число судьбы: <b>{num}</b>\n{desc}")
    except ValueError as e:
        await update.message.reply_text(str(e))


async def main():
    application = (
        Application.builder()
        .token(TOKEN)
        .rate_limiter(AIORateLimiter())
        .build()
    )

    application.add_handler(CommandHandler(["start", "help"], start))
    application.add_handler(CommandHandler("life", life_cmd))
    application.add_handler(CommandHandler("name", name_cmd))
    application.add_handler(CommandHandler("history", history_cmd))
    application.add_handler(MessageHandler(filters.VOICE, voice_handler))

    logger.info("Bot started")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    await application.updater.idle()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")