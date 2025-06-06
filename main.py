import os
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, ContextTypes, filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g., https://etagi-bot.onrender.com/webhook
FORWARD_TO_CHAT_ID = "1183134999"

ASK_FIO, ASK_REQUEST_ID, ASK_CONTRACT, ASK_CLIENT, ASK_OBJECT, ASK_TIME, ASK_ACTIONS, ASK_FILES = range(8)
user_data_dict = {}

app = Flask(__name__)
application = ApplicationBuilder().token(BOT_TOKEN).build()

# --- Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🚀 Запустить опрос", callback_data="start_survey")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Привет! Чтобы оставить обращение, нажмите кнопку ниже 👇", reply_markup=reply_markup)

async def start_survey_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.edit_text("\U0001F4E5 Новый кейс обхода клиента:\n\nВаши ФИО и ФИО РГП?")
    return ASK_FIO

async def ask_fio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_dict[update.effective_user.id] = {"ФИО и ФИО РГП": update.message.text}
    await update.message.reply_text("Номер заявки, по которой произошел обход?")
    return ASK_REQUEST_ID

async def ask_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_dict[update.effective_user.id]["Номер заявки"] = update.message.text
    await update.message.reply_text("Номер и дата договора?")
    return ASK_CONTRACT

async def ask_contract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_dict[update.effective_user.id]["Договор"] = update.message.text
    await update.message.reply_text("ФИО клиента, который совершил обход?")
    return ASK_CLIENT

async def ask_client(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_dict[update.effective_user.id]["ФИО клиента"] = update.message.text
    await update.message.reply_text("По какому объекту обход?")
    return ASK_OBJECT

async def ask_object(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_dict[update.effective_user.id]["Объект"] = update.message.text
    await update.message.reply_text("Когда это произошло?")
    return ASK_TIME

async def ask_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_dict[update.effective_user.id]["Время"] = update.message.text
    await update.message.reply_text("Какие действия были предприняты?")
    return ASK_ACTIONS

async def ask_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_dict[update.effective_user.id]["Действия"] = update.message.text
    await update.message.reply_text("Пришлите документы или напишите 'нет'")
    return ASK_FILES

async def ask_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    data = user_data_dict.get(user.id, {})
    summary = (
        f"\U0001F4E5 Новый кейс обхода клиента:\n\n"
        f"ФИО и ФИО РГП: {data.get('ФИО и ФИО РГП')}\n"
        f"Номер заявки: {data.get('Номер заявки')}\n"
        f"Договор: {data.get('Договор')}\n"
        f"ФИО клиента: {data.get('ФИО клиента')}\n"
        f"Объект: {data.get('Объект')}\n"
        f"Время: {data.get('Время')}\n"
        f"Действия: {data.get('Действия')}"
    )
    await update.message.reply_text("\u2705 Спасибо! Мы начали работу по обращению.", reply_markup=ReplyKeyboardRemove())
    try:
        await context.bot.send_message(chat_id=FORWARD_TO_CHAT_ID, text=summary)
        if update.message.document or update.message.photo:
            await update.message.forward(chat_id=FORWARD_TO_CHAT_ID)
    except Exception as e:
        print("Ошибка при пересылке:", e)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Опрос прерван.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# --- Conversation logic ---
conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_survey_callback, pattern="^start_survey$")],
    states={
        ASK_FIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_fio)],
        ASK_REQUEST_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_request)],
        ASK_CONTRACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_contract)],
        ASK_CLIENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_client)],
        ASK_OBJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_object)],
        ASK_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_time)],
        ASK_ACTIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_actions)],
        ASK_FILES: [MessageHandler(filters.ALL, ask_files)],
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)

application.add_handler(CommandHandler("start", start))
application.add_handler(conv_handler)

@app.route("/")
def index():
    return "ok"

@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "ok"

if __name__ == "__main__":
    import asyncio
    import logging
    logging.basicConfig(level=logging.INFO)

    async def main():
        await application.bot.delete_webhook()
        await application.bot.set_webhook(url=WEBHOOK_URL)
        print("Bot and webhook started successfully.")
        app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

    asyncio.run(main())
