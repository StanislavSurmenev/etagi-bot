import os
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)
import logging
import asyncio

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Переменные окружения
BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
FORWARD_TO_CHAT_ID = os.environ.get("FORWARD_TO_CHAT_ID")

# Flask-приложение
app = Flask(__name__)

# Telegram Application
telegram_app = Application.builder().token(BOT_TOKEN).build()

# Состояния
ASK_DETAILS, ASK_FILES = range(2)

# Хранилище данных пользователей
user_data_dict = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    user_data_dict[user.id] = {}
    await update.message.reply_text("Какие действия были уже предприняты? (звонки, сообщения, фиксация и т.п.)")
    return ASK_DETAILS


async def ask_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    user_data_dict[user.id]["действия"] = update.message.text
    await update.message.reply_text("Пришлите документы, скрины, фото или видео (можно несколько), или напишите 'нет'")
    return ASK_FILES


async def ask_files(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    data = user_data_dict.get(user.id, {})
    summary = (
        f"Новый кейс обхода клиента:\n\n"
        f"Действия: {data.get('действия')}\n"
        f"Комментарий: {update.message.text}"
    )

    await context.bot.send_message(chat_id=FORWARD_TO_CHAT_ID, text=summary)
    await update.message.reply_text("Спасибо! Мы начали работу по обращению.")
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END


# Хендлер
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        ASK_DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_details)],
        ASK_FILES: [MessageHandler(filters.ALL & ~filters.COMMAND, ask_files)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

telegram_app.add_handler(conv_handler)


@app.route("/")
def index():
    return "OK"


@app.route("/webhook", methods=["POST"])
async def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), telegram_app.bot)
        await telegram_app.process_update(update)
        return "OK", 200


@app.before_first_request
def setup_webhook():
    loop = asyncio.get_event_loop()

    async def set_webhook():
        await telegram_app.bot.delete_webhook()
        await telegram_app.bot.set_webhook(url=WEBHOOK_URL)

    loop.create_task(set_webhook())


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
