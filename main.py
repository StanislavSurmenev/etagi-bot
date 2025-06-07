import os
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from functools import wraps

# Переменные окружения
TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Пример: https://etagi-bot.onrender.com
PORT = int(os.getenv("PORT", 10000))

# Flask-приложение
app = Flask(__name__)

# Telegram-приложение
telegram_app = Application.builder().token(TOKEN).build()

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот работает!")

# Регистрация хендлера
telegram_app.add_handler(CommandHandler("start", start))

# Декоратор для асинхронных Flask-роутов
def async_route(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper

# Главная страница
@app.route("/")
def index():
    return "OK", 200

# Обработка входящих webhook-запросов от Telegram
@app.route(WEBHOOK_PATH, methods=["POST"])
@async_route
async def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    await telegram_app.process_update(update)
    return "ok", 200

# Установка webhook при запуске
async def setup_webhook():
    await telegram_app.bot.delete_webhook()
    await telegram_app.bot.set_webhook(url=WEBHOOK_URL + WEBHOOK_PATH)

# Запуск Flask + установка webhook
def run():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(setup_webhook())
    app.run(host="0.0.0.0", port=PORT)

# Точка входа
if __name__ == "__main__":
    run()
