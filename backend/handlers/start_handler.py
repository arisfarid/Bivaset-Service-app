from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from utils import get_user_phone, BASE_URL, log_chat
import requests
import logging

logger = logging.getLogger(__name__)

# تعریف حالت‌ها
START, REGISTER, ROLE, EMPLOYER_MENU, CATEGORY, SUBCATEGORY, DESCRIPTION, LOCATION_TYPE, LOCATION_INPUT, DETAILS, DETAILS_FILES, DETAILS_DATE, DETAILS_DEADLINE, DETAILS_BUDGET, DETAILS_QUANTITY, SUBMIT, VIEW_PROJECTS, PROJECT_ACTIONS = range(18)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info("Start command received")
    name = update.effective_user.full_name or "کاربر"
    telegram_id = str(update.effective_user.id)
    chat_id = update.effective_chat.id

    if 'active_chats' not in context.bot_data:
        context.bot_data['active_chats'] = []
    if chat_id not in context.bot_data['active_chats']:
        context.bot_data['active_chats'].append(chat_id)
        logger.info(f"Updated active_chats: {context.bot_data['active_chats']}")

    phone = await get_user_phone(telegram_id)
    logger.info(f"Phone for telegram_id {telegram_id}: {phone}")
    if not phone or phone == f"tg_{telegram_id}":
        return await check_phone(update, context)
    context.user_data['phone'] = phone
    await log_chat(update, context)

    keyboard = [["درخواست خدمات | کارفرما 👔"], ["پیشنهاد قیمت | مجری 🦺"]]
    message = (
        f"👋 سلام {name}! به ربات خدمات بی‌واسط خوش اومدی.\n"
        "من رایگان کمکت می‌کنم برای خدمات مورد نیازت، مجری کاربلد پیدا کنی یا کار مرتبط با تخصصت پیدا کنی. چی می‌خوای امروز؟ 🌟"
    )
    if update.message:
        await update.message.reply_text(message, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True))
    elif update.callback_query:
        await context.bot.send_message(chat_id=chat_id, text=message, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return ROLE

async def check_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    telegram_id = str(update.effective_user.id)
    response = requests.get(f"{BASE_URL}users/?telegram_id={telegram_id}")
    if response.status_code == 200 and response.json():
        phone = response.json()[0]['phone']
        if phone and phone != f"tg_{telegram_id}":
            context.user_data['phone'] = phone
            return await start(update, context)  # برگشت به ROLE بعد از چک
    keyboard = [[KeyboardButton("ثبت شماره تلفن", request_contact=True)]]
    await update.effective_message.reply_text(
        "😊 برای استفاده از امکانات ربات، لطفاً شماره تلفنت رو با دکمه زیر ثبت کن! 📱",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return REGISTER

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
        return await start(update, context)  # برگشت به ROLE
    except requests.exceptions.ConnectionError:
        await update.message.reply_text("❌ خطا: سرور بک‌اند در دسترس نیست.")
        return REGISTER

async def handle_role(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    choice = update.message.text
    await log_chat(update, context)
    if choice == "درخواست خدمات | کارفرما 👔":
        context.user_data['role'] = 'client'
        keyboard = [
            [KeyboardButton("📋 درخواست خدمات جدید"), KeyboardButton("📊 مشاهده درخواست‌ها")],
            [KeyboardButton("⬅️ بازگشت")]
        ]
        await update.message.reply_text(
            "عالیه! 😊 می‌خوای پروژه‌ت رو تعریف کنی یا درخواست‌ها رو ببینی؟",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return EMPLOYER_MENU
    elif choice == "پیشنهاد قیمت | مجری 🦺":
        context.user_data['role'] = 'contractor'
        await update.message.reply_text("خوبه! 😊 حالا می‌تونی پروژه‌ها رو ببینی و پیشنهاد بدی.")
        return ROLE  # TODO: بعداً برای مجری‌ها گسترش داده بشه
    else:
        await update.message.reply_text("❌ گزینه نامعتبر! لطفاً از منو انتخاب کن.")
        return ROLE

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("عملیات لغو شد. دوباره شروع کن!")
    return ConversationHandler.END