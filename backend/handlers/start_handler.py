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

async def check_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if user has registered their phone number"""
    telegram_id = str(update.effective_user.id)
    logger.info(f"Checking phone for user {telegram_id}")
    
    try:
        response = requests.get(f"{BASE_URL}users/?telegram_id={telegram_id}")
        logger.info(f"Check phone response: {response.status_code}")
        
        if response.status_code == 200 and response.json():
            user_data = response.json()[0]
            phone = user_data.get('phone')
            
            if not phone or phone.startswith('tg_'):
                logger.info(f"User {telegram_id} has no valid phone")
                await update.effective_message.reply_text(
                    "😊 برای استفاده از امکانات ربات، لطفاً شماره تلفن خود را با دکمه زیر به اشتراک بگذارید:",
                    reply_markup=REGISTER_MENU_KEYBOARD
                )
                return False
            
            context.user_data['phone'] = phone
            logger.info(f"User {telegram_id} has valid phone: {phone}")
            return True
            
        logger.info(f"User {telegram_id} not found")
        await update.effective_message.reply_text(
            "😊 برای استفاده از امکانات ربات، لطفاً شماره تلفن خود را با دکمه زیر به اشتراک بگذارید:",
            reply_markup=REGISTER_MENU_KEYBOARD
        )
        return False

    except Exception as e:
        logger.error(f"Error checking phone for {telegram_id}: {e}")
        await update.effective_message.reply_text(
            "❌ خطا در بررسی اطلاعات کاربر. لطفاً دوباره تلاش کنید.",
            reply_markup=REGISTER_MENU_KEYBOARD
        )
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """شروع مکالمه با ربات"""
    await ensure_active_chat(update, context)
    
    # بررسی شماره تلفن
    if not await check_phone(update, context):
        return REGISTER
        
    # ادامه روند معمول
    # Commented out to preserve state (role/phone) after registration
    # context.user_data.clear()
    welcome_message = (
        f"👋 سلام {update.effective_user.first_name}! به ربات خدمات بی‌واسط خوش آمدید.\n"
        "لطفاً یکی از گزینه‌ها را انتخاب کنید."
    )
    await update.effective_message.reply_text(welcome_message, reply_markup=MAIN_MENU_KEYBOARD)
    return ROLE

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle receiving the user's phone number."""
    contact = update.message.contact
    if not contact:
        await update.message.reply_text(
            "❌ لطفاً از دکمه 'ثبت شماره تلفن' استفاده کنید.",
            reply_markup=REGISTER_MENU_KEYBOARD
        )
        return REGISTER

    # Remove '+' from the phone number if present
    phone = contact.phone_number.lstrip('+')
    name = update.effective_user.full_name or "کاربر"
    telegram_id = str(update.effective_user.id)
    
    # Ensure the phone number belongs to the user
    if str(contact.user_id) != telegram_id:
        await update.message.reply_text(
            "❌ لطفاً شماره تلفن خودتان را به اشتراک بگذارید!",
            reply_markup=REGISTER_MENU_KEYBOARD
        )
        return REGISTER

    logger.info(f"Received contact for user {telegram_id}: {phone}")

    try:
        # Check if the phone number is already registered
        phone_check = requests.get(f"{BASE_URL}users/?phone={phone}")
        if phone_check.status_code == 200 and phone_check.json():
            existing_user = phone_check.json()[0]
            if existing_user['telegram_id'] != telegram_id:
                await update.message.reply_text(
                    "❌ این شماره قبلاً توسط کاربر دیگری ثبت شده است.",
                    reply_markup=REGISTER_MENU_KEYBOARD
                )
                return REGISTER

        data = {
            'phone': phone,
            'telegram_id': telegram_id,
            'name': name,
            'role': context.user_data.get('role', 'client')
        }

        # Check if the user exists by telegram_id
        response = requests.get(f"{BASE_URL}users/?telegram_id={telegram_id}")
        logger.info(f"GET user response: {response.status_code}")

        if response.status_code == 200 and response.json():
            # Update existing user
            user = response.json()[0]
            update_response = requests.put(f"{BASE_URL}users/{user['id']}/", json=data)
            logger.info(f"PUT response: {update_response.status_code}")
            
            if update_response.status_code == 200:
                await update.message.reply_text(
                    "✅ شماره تلفن شما با موفقیت ثبت شد.",
                    reply_markup=MAIN_MENU_KEYBOARD
                )
            else:
                raise Exception(f"Failed to update user: {update_response.text}")
        else:
            # Create a new user
            create_response = requests.post(f"{BASE_URL}users/", json=data)
            logger.info(f"POST response: {create_response.status_code}")
            
            if create_response.status_code in [200, 201]:
                await update.message.reply_text(
                    "✅ ثبت‌نام شما با موفقیت انجام شد.",
                    reply_markup=MAIN_MENU_KEYBOARD
                )
            else:
                raise Exception(f"Failed to create user: {create_response.text}")

        # Save phone in context
        context.user_data['phone'] = phone
        return ROLE

    except Exception as e:
        logger.error(f"Error in handle_contact: {e}")
        await update.message.reply_text(
            "❌ خطا در ثبت شماره تلفن.\nلطفاً دوباره تلاش کنید.",
            reply_markup=REGISTER_MENU_KEYBOARD
        )
        return REGISTER

async def change_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """هندلر دستور /change_phone"""
    await update.effective_message.reply_text(
        "📱 لطفاً شماره تلفن جدید خود را وارد کنید:\n"
        "مثال: 09123456789"
    )
    return CHANGE_PHONE

async def handle_new_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """بررسی و ارسال کد تأیید برای شماره جدید"""
    new_phone = update.message.text.strip()
    
    if not new_phone.startswith('09') or not new_phone.isdigit() or len(new_phone) != 11:
        await update.effective_message.reply_text(
            "❌ فرمت شماره نامعتبر است.\n"
            "لطفاً شماره را به فرمت 09123456789 وارد کنید."
        )
        return CHANGE_PHONE
        
    response = requests.get(f"{BASE_URL}users/?phone={new_phone}")
    if response.status_code == 200 and response.json():
        await update.effective_message.reply_text(
            "❌ این شماره قبلاً توسط کاربر دیگری ثبت شده است."
        )
        return CHANGE_PHONE
        
    verification_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
    context.user_data['new_phone'] = new_phone
    context.user_data['verification_code'] = verification_code
    context.user_data['code_expires_at'] = datetime.now() + timedelta(minutes=2)
    
    sms_text = f"کد تایید بی‌واسط: {verification_code}\nاعتبار: 2 دقیقه"
    try:
        await update.effective_message.reply_text(
            "📤 کد تأیید ارسال شد.\n"
            f"(کد تست: {verification_code})\n"
            "لطفاً کد 6 رقمی دریافتی را وارد کنید:"
        )
        return VERIFY_CODE
    except Exception as e:
        logger.error(f"Error sending SMS: {e}")
        await update.effective_message.reply_text(
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
        await update.effective_message.reply_text("❌ اطلاعات تأیید نامعتبر است.")
        return ROLE
        
    if datetime.now() > expires_at:
        await update.effective_message.reply_text("⏰ کد تأیید منقضی شده است.")
        return ROLE
        
    if code != stored_code:
        await update.effective_message.reply_text("❌ کد وارد شده اشتباه است.")
        return VERIFY_CODE
        
    telegram_id = str(update.effective_user.id)
    try:
        response = requests.get(f"{BASE_URL}users/?telegram_id={telegram_id}")
        if response.status_code == 200 and response.json():
            user = response.json()[0]
            user['phone'] = new_phone
            update_response = requests.put(f"{BASE_URL}users/{user['id']}/", json=user)
            
            if update_response.status_code == 200:
                await update.effective_message.reply_text(
                    "✅ شماره تلفن شما با موفقیت تغییر کرد."
                )
            else:
                await update.effective_message.reply_text("❌ خطا در بروزرسانی شماره تلفن.")
        
        for key in ['verification_code', 'code_expires_at', 'new_phone']:
            context.user_data.pop(key, None)
            
    except Exception as e:
        logger.error(f"Error updating phone: {e}")
        await update.effective_message.reply_text("❌ خطا در بروزرسانی شماره تلفن.")
    
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