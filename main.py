import os
import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, Dispatcher, CallbackContext
)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# .env переменные
TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 10000))

# Flask-приложение
app = Flask(__name__)

# Telegram Application
telegram_app = ApplicationBuilder().token(TOKEN).build()

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот работает и принял команду /start")

telegram_app.add_handler(CommandHandler("start", start))


@app.route("/")
def home():
    return "Бот работает."


@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    telegram_app.update_queue.put_nowait(update)
    return "ok"


if __name__ == "__main__":
    import threading

    # Установка webhook
    import asyncio
    asyncio.run(telegram_app.bot.set_webhook(url=WEBHOOK_URL + "/webhook"))

    # Запуск Telegram-приложения в отдельном потоке
    threading.Thread(target=telegram_app.run_polling, daemon=True).start()

    # Flask-сервер
    app.run(host="0.0.0.0", port=PORT)
