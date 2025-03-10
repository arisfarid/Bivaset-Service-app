from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from utils import get_user_phone
import logging

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Start command received")
    name = update.effective_user.full_name or "کاربر"
    telegram_id = str(update.effective_user.id)
    phone = await get_user_phone(telegram_id)
    if phone and phone != f"tg_{telegram_id}":
        context.user_data['phone'] = phone
    keyboard = [
        [KeyboardButton("📋 درخواست خدمات (کارفرما)")],
        [KeyboardButton("🔧 پیشنهاد قیمت (مجری)")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"👋 سلام {name}! به خدمات بی‌واسط خوش اومدی!\n"
        "من اینجا کمکت می‌کنم کاملاً رایگان خدمات درخواست کنی یا کار پیدا کنی. چی می‌خوای امروز؟ ✨",
        reply_markup=reply_markup
    )
    if 'active_chats' not in context.bot_data:
        context.bot_data['active_chats'] = []
    if update.effective_chat.id not in context.bot_data['active_chats']:
        context.bot_data['active_chats'].append(update.effective_chat.id)