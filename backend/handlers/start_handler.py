from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, filters, MessageHandler
from utils import get_user_phone, BASE_URL
import requests
import logging

logger = logging.getLogger(__name__)

async def check_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    telegram_id = str(update.effective_user.id)
    response = requests.get(f"{BASE_URL}users/?telegram_id={telegram_id}")
    if response.status_code == 200 and response.json():
        context.user_data['phone'] = response.json()[0]['phone']
        return 1
    else:
        keyboard = [[KeyboardButton("ثبت شماره تلفن", request_contact=True)]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text(
            " 😊 برای استفاده از امکانات ربات، لطفاً شماره تلفنت رو با دکمه زیر ثبت کن! 📱",
            reply_markup=reply_markup
        )
        return 0

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    contact = update.message.contact
    phone = contact.phone_number
    name = update.effective_user.full_name or "کاربر"
    telegram_id = str(update.effective_user.id)
    url = BASE_URL + 'users/'
    data = {'phone': phone, 'telegram_id': telegram_id, 'name': name, 'role': context.user_data.get('role', 'client')}
    try:
        response = requests.post(url, json=data)
        context.user_data['phone'] = phone
        if response.status_code in [200, 201]:
            message = f"ممنون! 😊 شماره‌ت ثبت شد، حالا می‌تونی ادامه بدی!"
        elif response.status_code == 400 and "phone" in response.text:
            message = f"👋 خوش اومدی، {name}! شماره‌ات قبلاً ثبت شده."
        else:
            message = f"❌ خطا در ثبت‌نام: {response.text[:50]}..."
        await update.message.reply_text(message)
        await start(update, context)
        return 1
    except requests.exceptions.ConnectionError:
        await update.message.reply_text("❌ خطا: سرور بک‌اند در دسترس نیست.")
        return 0

async def handle_role(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    choice = update.message.text
    if choice == "درخواست خدمات | کارفرما 👔":
        context.user_data['role'] = 'client'
        await update.message.reply_text("عالیه! 😊 لطفاً پروژه‌ت رو تعریف کن.")
        return 2  # Move to project submission state
    elif choice == "پیشنهاد قیمت | مجری 🦺":
        context.user_data['role'] = 'contractor'
        await update.message.reply_text("خوبه! 😊 حالا می‌تونی پروژه‌ها رو ببینی و پیشنهاد بدی.")
        return 3  # Move to proposal submission state
    else:
        await update.message.reply_text("❌ گزینه نامعتبر! لطفاً از منو انتخاب کن.")
        return 1  # Stay in role selection state

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Start command received")
    name = update.effective_user.full_name or "کاربر"
    telegram_id = str(update.effective_user.id)
    phone = await get_user_phone(telegram_id)
    if phone and phone != f"tg_{telegram_id}":
        context.user_data['phone'] = phone
    keyboard = [
        ["درخواست خدمات | کارفرما 👔"],
        ["پیشنهاد قیمت | مجری 🦺"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        f"👋 سلام {name}! به ربات خدمات بی‌واسط خوش اومدی.\n"
        "من رایگان کمکت می‌کنم برای خدمات مورد نیازت، مجری کاربلد پیدا کنی یا کار مرتبط با تخصصت پیدا کنی. چی می‌خوای امروز؟ 🌟",
        reply_markup=reply_markup
    )
    if 'active_chats' not in context.bot_data:
        context.bot_data['active_chats'] = []
    if update.effective_chat.id not in context.bot_data['active_chats']:
        context.bot_data['active_chats'].append(update.effective_chat.id)
        logger.info(f"Updated active_chats: {context.bot_data['active_chats']}")

start_handler = CommandHandler('start', start)
role_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_role)