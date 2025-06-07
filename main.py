import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio

# Load env
TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_PATH = "/webhook/webhook"
PORT = int(os.environ.get("PORT", 10000))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# Flask app
app = Flask(__name__)

# Telegram bot setup
telegram_app = Application.builder().token(TOKEN).build()

# Example handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот работает.")

telegram_app.add_handler(CommandHandler("start", start))


@app.route("/")
def index():
    return "OK", 200

@app.route(WEBHOOK_PATH, methods=["POST"])
async def webhook():
    if request.method == "POST":
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
