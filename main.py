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
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# --- Flask ---
app = Flask(__name__)

# --- Telegram App ---
telegram_app = Application.builder().token(BOT_TOKEN).build()

# --- Conversation states ---
ASK_DETAILS, ASK_FILES = range(2)
user_data_dict = {}


# --- Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    user_data_dict[user.id] = {}
    await update.message.reply_text("Какие действия были уже предприняты? (звонки, сообщения, фиксация и т.п.)")
    return ASK_DETAILS

async def ask_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data_dict[update.message.from_user.id]["действия"] = update.message.text
    await update.message.reply_text("Пришлите документы, скрины, фото или видео (можно несколько), или напишите 'нет'")
    return ASK_FILES

async def ask_files(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    data = user_data_dict.get(user.id, {})
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


# --- Flask routes ---
@app.route("/")
def index():
    return "OK"


@app.route("/webhook", methods=["POST"])
async def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), telegram_app.bot)
        await telegram_app.process_update(update)
    return "OK", 200


# --- Webhook setup ---
async def main():
    await telegram_app.bot.delete_webhook()
    await telegram_app.bot.set_webhook(url=WEBHOOK_URL)
    telegram_app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL,
        web_app=app,
    )


if __name__ == "__main__":
    asyncio.run(main())
