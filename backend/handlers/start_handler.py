from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from utils import get_user_phone, BASE_URL, log_chat, ensure_active_chat
from keyboards import MAIN_MENU_KEYBOARD, REGISTER_MENU_KEYBOARD, EMPLOYER_MENU_KEYBOARD  # اضافه شده
import requests
import logging

logger = logging.getLogger(__name__)

# تعریف حالت‌ها
START, REGISTER, ROLE, EMPLOYER_MENU, CATEGORY, SUBCATEGORY, DESCRIPTION, LOCATION_TYPE, LOCATION_INPUT, DETAILS, DETAILS_FILES, DETAILS_DATE, DETAILS_DEADLINE, DETAILS_BUDGET, DETAILS_QUANTITY, SUBMIT, VIEW_PROJECTS, PROJECT_ACTIONS = range(18)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await ensure_active_chat(update, context)
    # اگر پیام متنی موجود نباشد، از callback استفاده شود:
    message_obj = update.message if update.message else update.callback_query.message
    chat_id = update.effective_chat.id

    if 'active_chats' not in context.bot_data:
        context.bot_data['active_chats'] = []
    if chat_id not in context.bot_data['active_chats']:
        context.bot_data['active_chats'].append(chat_id)
        await context.application.persistence.update_bot_data(context.bot_data)
        logger.info(f"Added {chat_id} to active chats")

    context.user_data.clear()
    welcome_message = (
        f"👋 سلام {update.effective_user.first_name}! به ربات خدمات بی‌واسط خوش آمدید.\n"
        "لطفاً یکی از گزینه‌ها را انتخاب کنید."
    )
    await message_obj.reply_text(welcome_message, reply_markup=MAIN_MENU_KEYBOARD)
    return ROLE

async def check_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    telegram_id = str(update.effective_user.id)
    response = requests.get(f"{BASE_URL}users/?telegram_id={telegram_id}")
    if response.status_code == 200 and response.json():
        phone = response.json()[0]['phone']
        if phone and phone != f"tg_{telegram_id}":
            context.user_data['phone'] = phone
            return await start(update, context)  # برگشت به ROLE بعد از چک
    await update.effective_message.reply_text(
        "😊 برای استفاده از امکانات ربات، لطفاً شماره تلفنت رو با دکمه زیر ثبت کن! 📱",
        reply_markup=REGISTER_MENU_KEYBOARD  # استفاده از REGISTER_MENU_KEYBOARD
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
    """Handle role selection."""
    text = update.message.text
    
    if text == "درخواست خدمات | کارفرما 👔":
        context.user_data['state'] = EMPLOYER_MENU
        await update.message.reply_text(
            "🎉 عالیه، {}! می‌خوای خدمات جدید درخواست کنی یا پیشنهادات رو ببینی؟".format(
                update.effective_user.full_name
            ),
            reply_markup=EMPLOYER_MENU_KEYBOARD
        )
        return EMPLOYER_MENU
    
    return ROLE

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("عملیات لغو شد. دوباره شروع کن!")
    return ConversationHandler.END