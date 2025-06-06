import os
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)
import logging

# --- Конфигурация ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
FORWARD_TO_CHAT_ID = os.environ.get("FORWARD_TO_CHAT_ID")
PORT = int(os.environ.get("PORT", 10000))

# --- Логирование ---
logging.basicConfig(level=logging.INFO)

# --- Flask ---
app = Flask(__name__)

# --- Telegram App ---
telegram_app = Application.builder().token(BOT_TOKEN).build()

# --- Conversation States ---
ASK_DETAILS, ASK_FILES = range(2)
user_data_dict = {}


# --- Telegram Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    user_data_dict[user.id] = {}
    await update.message.reply_text("Какие действия были предприняты?")
    return ASK_DETAILS

async def ask_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    user_data_dict[user_id]["действия"] = update.message.text
    await update.message.reply_text("Пришлите документы, скрины или напишите 'нет'")
    return ASK_FILES

async def ask_files(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    data = user_data_dict.get(user_id, {})
    text = (
        f"Новый кейс обхода клиента:\n\n"
        f"Действия: {data.get('действия')}\n"
        f"Комментарий: {update.message.text}"
    )
    await context.bot.send_message(chat_id=FORWARD_TO_CHAT_ID, text=text)
    await update.message.reply_text("✅ Спасибо! Мы начали работу по обращению.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END

# --- Регистрация хендлеров ---
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        ASK_DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_details)],
        ASK_FILES: [MessageHandler(filters.ALL & ~filters.COMMAND, ask_files)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
telegram_app.add_handler(conv_handler)


# --- Flask Routes ---
@app.route("/")
def index():
    return "OK"

@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    asyncio.create_task(telegram_app.process_update(update))
    return "ok", 200


# --- Основной запуск ---
if __name__ == "__main__":
    async def setup():
        await telegram_app.bot.delete_webhook()
        await telegram_app.bot.set_webhook(url=WEBHOOK_URL)

    asyncio.run(setup())
    app.run(host="0.0.0.0", port=PORT)
