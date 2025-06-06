import os
import asyncio
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, ApplicationBuilder, CallbackQueryHandler, CommandHandler,
    ConversationHandler, MessageHandler, ContextTypes, filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = "https://etagi-bot.onrender.com/webhook"
PORT = int(os.environ.get("PORT", 10000))
FORWARD_TO_CHAT_ID = "1183134999"

(ASK_FIO, ASK_REQUEST_ID, ASK_CONTRACT, ASK_CLIENT, ASK_OBJECT, ASK_TIME, ASK_ACTIONS, ASK_FILES) = range(8)
user_data_dict = {}

app = Flask(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Запустить опрос", callback_data="start_survey")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Привет! Чтобы оставить обращение, нажмите кнопку ниже:", reply_markup=reply_markup)

async def start_survey_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.edit_text("Новый кейс обхода клиента:\n\nВаши ФИО и ФИО РГП?")
    return ASK_FIO

async def ask_fio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_dict[update.effective_user.id] = {"ФИО и ФИО РГП": update.message.text}
    await update.message.reply_text("Номер заявки, по которой произошел обход?")
    return ASK_REQUEST_ID

async def ask_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_dict[update.effective_user.id]["Номер заявки"] = update.message.text
    await update.message.reply_text("Номер и дата договора (например, Э0425ШМ04 от 12.04.2025)?")
    return ASK_CONTRACT

async def ask_contract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_dict[update.effective_user.id]["Договор"] = update.message.text
    await update.message.reply_text("ФИО клиента, который совершил обход?")
    return ASK_CLIENT

async def ask_client(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_dict[update.effective_user.id]["ФИО клиента"] = update.message.text
    await update.message.reply_text("По какому объекту обход? (номер объекта, адрес)")
    return ASK_OBJECT

async def ask_object(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_dict[update.effective_user.id]["Объект"] = update.message.text
    await update.message.reply_text("Когда это произошло (дата, примерное время)?")
    return ASK_TIME

async def ask_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_dict[update.effective_user.id]["Время"] = update.message.text
    await update.message.reply_text("Какие действия были уже предприняты? (звонки, сообщения, фиксация и т.п.)")
    return ASK_ACTIONS

async def ask_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_dict[update.effective_user.id]["Действия"] = update.message.text
    await update.message.reply_text("Пришлите документы, скрины, фото или видео (можно несколько), или напишите 'нет'")
    return ASK_FILES

async def ask_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    data = user_data_dict.get(user.id, {})
    summary = (
        f"Новый кейс обхода клиента:\n\n"
        f"ФИО и ФИО РГП: {data.get('ФИО и ФИО РГП')}\n"
        f"Номер заявки: {data.get('Номер заявки')}\n"
        f"Договор: {data.get('Договор')}\n"
        f"ФИО клиента: {data.get('ФИО клиента')}\n"
        f"
