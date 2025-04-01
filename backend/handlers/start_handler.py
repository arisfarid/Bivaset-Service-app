from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from utils import get_user_phone, BASE_URL, log_chat, ensure_active_chat
from keyboards import MAIN_MENU_KEYBOARD, REGISTER_MENU_KEYBOARD, EMPLOYER_MENU_KEYBOARD  # اضافه شده
import requests
import logging
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)

# تعریف حالت‌ها
START, REGISTER, ROLE, EMPLOYER_MENU, CATEGORY, SUBCATEGORY, DESCRIPTION, LOCATION_TYPE, LOCATION_INPUT, DETAILS, DETAILS_FILES, DETAILS_DATE, DETAILS_DEADLINE, DETAILS_BUDGET, DETAILS_QUANTITY, SUBMIT, VIEW_PROJECTS, PROJECT_ACTIONS = range(18)
CHANGE_PHONE, VERIFY_CODE = range(20, 22)  # states جدید

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
    
    if contact.user_id != update.effective_user.id:
        await update.message.reply_text(
            "❌ لطفاً شماره تلفن خودتان را به اشتراک بگذارید!"
        )
        return REGISTER

    url = BASE_URL + 'users/'
    data = {
        'phone': phone,
        'telegram_id': telegram_id,
        'telegram_phone': phone,  # ذخیره شماره تلگرام
        'name': name,
        'role': context.user_data.get('role', 'client')
    }
    
    try:
        response = requests.post(url, json=data)
        if response.status_code in [200, 201]:
            await update.message.reply_text(
                "✅ ثبت‌نام با موفقیت انجام شد!\n"
                "برای تغییر شماره تماس در آینده می‌توانید از دستور /change_phone استفاده کنید."
            )
            return await start(update, context)
        elif response.status_code == 400 and "phone" in response.text:
            await update.message.reply_text(
                "👋 خوش اومدی! شماره‌ات قبلاً ثبت شده."
            )
            return await start(update, context)
    except requests.exceptions.ConnectionError:
        await update.message.reply_text("❌ خطا در ارتباط با سرور")
        return REGISTER

async def change_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """هندلر دستور /change_phone"""
    await update.message.reply_text(
        "📱 لطفاً شماره تلفن جدید خود را وارد کنید:\n"
        "مثال: 09123456789"
    )
    return CHANGE_PHONE

async def handle_new_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """بررسی و ارسال کد تأیید برای شماره جدید"""
    new_phone = update.message.text.strip()
    
    if not new_phone.startswith('09') or not new_phone.isdigit() or len(new_phone) != 11:
        await update.message.reply_text(
            "❌ فرمت شماره نامعتبر است.\n"
            "لطفاً شماره را به فرمت 09123456789 وارد کنید."
        )
        return CHANGE_PHONE
        
    response = requests.get(f"{BASE_URL}users/?phone={new_phone}")
    if response.status_code == 200 and response.json():
        await update.message.reply_text(
            "❌ این شماره قبلاً توسط کاربر دیگری ثبت شده است."
        )
        return CHANGE_PHONE
        
    verification_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
    context.user_data['new_phone'] = new_phone
    context.user_data['verification_code'] = verification_code
    context.user_data['code_expires_at'] = datetime.now() + timedelta(minutes=2)
    
    sms_text = f"کد تایید بی‌واسط: {verification_code}\nاعتبار: 2 دقیقه"
    try:
        await update.message.reply_text(
            "📤 کد تأیید ارسال شد.\n"
            f"(کد تست: {verification_code})\n"
            "لطفاً کد 6 رقمی دریافتی را وارد کنید:"
        )
        return VERIFY_CODE
    except Exception as e:
        logger.error(f"Error sending SMS: {e}")
        await update.message.reply_text(
            "❌ خطا در ارسال کد تأیید.\n"
            "لطفاً دوباره تلاش کنید."
        )
        return CHANGE_PHONE

async def verify_new_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """تأیید کد و تغییر شماره"""
    code = update.message.text.strip()
    stored_code = context.user_data.get('verification_code')
    expires_at = context.user_data.get('code_expires_at')
    new_phone = context.user_data.get('new_phone')
    
    if not all([stored_code, expires_at, new_phone]):
        await update.message.reply_text("❌ اطلاعات تأیید نامعتبر است.")
        return ROLE
        
    if datetime.now() > expires_at:
        await update.message.reply_text("⏰ کد تأیید منقضی شده است.")
        return ROLE
        
    if code != stored_code:
        await update.message.reply_text("❌ کد وارد شده اشتباه است.")
        return VERIFY_CODE
        
    telegram_id = str(update.effective_user.id)
    try:
        response = requests.get(f"{BASE_URL}users/?telegram_id={telegram_id}")
        if response.status_code == 200 and response.json():
            user = response.json()[0]
            user['phone'] = new_phone
            update_response = requests.put(f"{BASE_URL}users/{user['id']}/", json=user)
            
            if update_response.status_code == 200:
                await update.message.reply_text(
                    "✅ شماره تلفن شما با موفقیت تغییر کرد."
                )
            else:
                await update.message.reply_text("❌ خطا در بروزرسانی شماره تلفن.")
        
        for key in ['verification_code', 'code_expires_at', 'new_phone']:
            context.user_data.pop(key, None)
            
    except Exception as e:
        logger.error(f"Error updating phone: {e}")
        await update.message.reply_text("❌ خطا در بروزرسانی شماره تلفن.")
    
    return ROLE

async def handle_role(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle role selection."""
    text = update.message.text
    
    if (text == "درخواست خدمات | کارفرما 👔"):
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