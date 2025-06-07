from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from functools import wraps
import os, asyncio

# Настройки
TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_PATH = "/webhook"
PORT = int(os.getenv("PORT", 10000))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# Flask
app = Flask(__name__)

# Telegram Application
telegram_app = Application.builder().token(TOKEN).build()

# Обработчик команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот работает!")

telegram_app.add_handler(CommandHandler("start", start))

# Обёртка: async → sync для Flask
def async_route(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        return asyncio.run(fn(*args, **kwargs))
    return wrapper

@app.route("/")
def index():
    return "OK", 200

@app.route(WEBHOOK_PATH, methods=["POST"])
@async_route
async def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    await telegram_app.process_update(update)
    return "ok", 200

async def setup_webhook():
    await telegram_app.bot.delete_webhook()
    await telegram_app.bot.set_webhook(url=WEBHOOK_URL + WEBHOOK_PATH)

def run():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(setup_webhook())
    app.run(host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    run()
