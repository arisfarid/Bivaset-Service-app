from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, filters, MessageHandler
from utils import get_user_phone, BASE_URL, log_chat  # modified import
import requests
import logging

logger = logging.getLogger(__name__)

async def check_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    telegram_id = str(update.effective_user.id)
    response = requests.get(f"{BASE_URL}users/?telegram_id={telegram_id}")
    if response.status_code == 200 and response.json():
        phone = response.json()[0]['phone']
        if phone and phone != f"tg_{telegram_id}":  # فقط اگه شماره واقعی باشه
            context.user_data['phone'] = phone
            return 1
    # اگه شماره نداره یا خطا هست
    keyboard = [[KeyboardButton("ثبت شماره تلفن", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.effective_message.reply_text(
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
        await start(update, context)  # برگشت به منوی اصلی بعد از ثبت
        return 1
    except requests.exceptions.ConnectionError:
        await update.message.reply_text("❌ خطا: سرور بک‌اند در دسترس نیست.")
        return 0

async def handle_role(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    choice = update.message.text
    if choice == "درخواست خدمات | کارفرما 👔":
        context.user_data['role'] = 'client'
        await update.message.reply_text("عالیه! 😊 لطفاً پروژه‌ت رو تعریف کن.")
        return 2
    elif choice == "پیشنهاد قیمت | مجری 🦺":
        context.user_data['role'] = 'contractor'
        await update.message.reply_text("خوبه! 😊 حالا می‌تونی پروژه‌ها رو ببینی و پیشنهاد بدی.")
        return 3
    else:
        await update.message.reply_text("❌ گزینه نامعتبر! لطفاً از منو انتخاب کن.")
        return 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Start command received")
    name = update.effective_user.full_name or "کاربر"
    telegram_id = str(update.effective_user.id)
    chat_id = update.effective_chat.id

    # اضافه کردن چت به active_chats
    if 'active_chats' not in context.bot_data:
        context.bot_data['active_chats'] = []
    if chat_id not in context.bot_data['active_chats']:
        context.bot_data['active_chats'].append(chat_id)
        logger.info(f"Updated active_chats: {context.bot_data['active_chats']}")

    # چک کردن ثبت‌نام کاربر
    phone = await get_user_phone(telegram_id)
    logger.info(f"Phone for telegram_id {telegram_id}: {phone}")
    if not phone or phone == f"tg_{telegram_id}":
        context.user_data['state'] = 'register'
        logger.info("User not registered, redirecting to check_phone")
        await check_phone(update, context)
        return  # اینجا متوقف می‌شه تا ثبت‌نام کامل بشه
    else:
        context.user_data['phone'] = phone

    # Log the chat
    await log_chat(update, context)  # new line added

    # اگه ثبت‌نام شده، منوی اصلی رو نشون بده
    keyboard = [
        ["درخواست خدمات | کارفرما 👔"],
        ["پیشنهاد قیمت | مجری 🦺"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    message = (
        f"👋 سلام {name}! به ربات خدمات بی‌واسط خوش اومدی.\n"
        "من رایگان کمکت می‌کنم برای خدمات مورد نیازت، مجری کاربلد پیدا کنی یا کار مرتبط با تخصصت پیدا کنی. چی می‌خوای امروز؟ 🌟"
    )
    if update.message:  # اومده از /start
        await update.message.reply_text(message, reply_markup=reply_markup)
    elif update.callback_query:  # اومده از دکمه
        await context.bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup)

start_handler = CommandHandler('start', start)
role_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_role)