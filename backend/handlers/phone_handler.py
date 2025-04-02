from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
import random
import requests
import logging
from utils import BASE_URL, save_user_phone
from keyboards import MAIN_MENU_KEYBOARD, REGISTER_MENU_KEYBOARD

logger = logging.getLogger(__name__)

ROLE, CHANGE_PHONE, VERIFY_CODE, REGISTER = range(4)

SMS_API_KEY = "your-api-key"  # تنظیم بعدی
SMS_URL = "https://api.sms.ir/v1/send/verify"
SMS_TEMPLATE_ID = "100000"  # کد قالب SMS.ir
MAX_ATTEMPTS = 5  # حداکثر تعداد تلاش مجاز

async def send_verification_code(phone: str, code: str) -> bool:
    """ارسال کد تأیید از طریق SMS.ir"""
    try:
        payload = {
            "mobile": phone,
            "templateId": SMS_TEMPLATE_ID,
            "parameters": [{"name": "CODE", "value": code}]
        }
        headers = {"X-API-KEY": SMS_API_KEY, "Content-Type": "application/json"}
        response = requests.post(SMS_URL, json=payload, headers=headers)
        if response.status_code == 200 and response.json().get("status") == 1:
            logger.info(f"Verification code sent successfully to {phone}")
            return True
        logger.error(f"Failed to send SMS: {response.text}")
        return False
    except Exception as e:
        logger.error(f"Error sending SMS: {e}")
        return False

async def change_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """شروع فرآیند تغییر شماره تلفن"""
    await update.message.reply_text(
        "📱 لطفاً شماره تلفن جدید خود را وارد کنید:\n"
        "مثال: 09123456789"
    )
    context.user_data['verify_attempts'] = 0  # ریست تعداد تلاش‌ها
    return CHANGE_PHONE

async def handle_new_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """بررسی شماره تلفن جدید و ارسال کد تأیید"""
    new_phone = update.message.text.strip()
    if not new_phone.startswith('09') or not new_phone.isdigit() or len(new_phone) != 11:
        await update.message.reply_text("❌ فرمت شماره نامعتبر است.\nلطفاً شماره را به فرمت 09123456789 وارد کنید.")
        return CHANGE_PHONE

    response = requests.get(f"{BASE_URL}users/?phone={new_phone}")
    if response.status_code == 200 and response.json():
        await update.message.reply_text("❌ این شماره قبلاً توسط کاربر دیگری ثبت شده است.")
        return CHANGE_PHONE

    verification_code = ''.join([str(random.randint(0, 9)) for _ in range(4)])
    context.user_data.update({
        'new_phone': new_phone,
        'verification_code': verification_code,
        'code_expires_at': datetime.now() + timedelta(minutes=2),
        'verify_attempts': 0
    })

    if await send_verification_code(new_phone, verification_code):
        await update.message.reply_text(
            "📤 کد تأیید 4 رقمی به شماره شما ارسال شد.\n"
            "⏰ مهلت وارد کردن کد: 2 دقیقه\n"
            f"📱 شماره: {new_phone}\n\n"
            f"برای تست: کد = {verification_code}"  # حذف در نسخه نهایی
        )
        return VERIFY_CODE
    else:
        await update.message.reply_text("❌ خطا در ارسال کد تأیید.\nلطفاً دوباره تلاش کنید.")
        return CHANGE_PHONE

async def verify_new_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """بررسی کد تأیید وارد شده"""
    code = update.message.text.strip()
    stored_code = context.user_data.get('verification_code')
    expires_at = context.user_data.get('code_expires_at')
    new_phone = context.user_data.get('new_phone')
    attempts = context.user_data.get('verify_attempts', 0)

    if not all([stored_code, expires_at, new_phone]):
        await update.message.reply_text("❌ اطلاعات تأیید نامعتبر است.")
        return CHANGE_PHONE

    if attempts >= MAX_ATTEMPTS:
        await update.message.reply_text("❌ تعداد تلاش‌های مجاز به پایان رسید.\nلطفاً دوباره درخواست کد کنید.")
        return CHANGE_PHONE

    if datetime.now() > expires_at:
        await update.message.reply_text("⏰ کد تأیید منقضی شده است.\nلطفاً دوباره درخواست کد کنید.")
        return CHANGE_PHONE

    context.user_data['verify_attempts'] += 1
    if code != stored_code:
        remaining = MAX_ATTEMPTS - context.user_data['verify_attempts']
        await update.message.reply_text(f"❌ کد وارد شده اشتباه است.\nتعداد تلاش‌های باقیمانده: {remaining}")
        return VERIFY_CODE if remaining > 0 else CHANGE_PHONE

    try:
        telegram_id = str(update.effective_user.id)
        response = requests.get(f"{BASE_URL}users/?telegram_id={telegram_id}")
        if response.status_code == 200 and response.json():
            user = response.json()[0]
            user['phone'] = new_phone
            update_response = requests.put(f"{BASE_URL}users/{user['id']}/", json=user)
            if update_response.status_code == 200:
                await update.message.reply_text("✅ شماره تلفن شما با موفقیت تأیید و ثبت شد.", reply_markup=MAIN_MENU_KEYBOARD)
            else:
                raise Exception("Failed to update phone number")
        for key in ['verification_code', 'code_expires_at', 'new_phone', 'verify_attempts']:
            context.user_data.pop(key, None)
    except Exception as e:
        logger.error(f"Error updating phone: {e}")
        await update.message.reply_text("❌ خطا در ثبت شماره تلفن.\nلطفاً دوباره تلاش کنید.")
    return CHANGE_PHONE


logger = logging.getLogger(__name__)

def require_phone(func):
    """دکوراتور برای اجبار به ثبت شماره تلفن"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        # اگر در حالت REGISTER هستیم یا درخواست CONTACT داریم، مستقیماً اجازه عبور بدهیم
        current_state = context.user_data.get('state')
        has_contact = bool(update.message and update.message.contact)
        
        if current_state == REGISTER or has_contact:
            logger.info(f"Bypassing phone check - state: {current_state}, has_contact: {has_contact}")
            return await func(update, context, *args, **kwargs)
            
        if not update.effective_user:
            return

        telegram_id = str(update.effective_user.id)
        
        try:
            # چک کردن شماره تلفن در دیتابیس
            response = requests.get(f"{BASE_URL}users/?telegram_id={telegram_id}")
            
            if response.status_code == 200 and response.json():
                user_data = response.json()[0]
                phone = user_data.get('phone')
                
                # اگر شماره معتبر نداشت یا شماره موقت داشت
                if not phone or phone.startswith('tg_'):
                    logger.info(f"User {telegram_id} needs to register phone")
                    if update.callback_query:
                        await update.callback_query.message.reply_text(
                            "برای استفاده از امکانات ربات، لطفاً ابتدا شماره تلفن خود را ثبت کنید:",
                            reply_markup=REGISTER_MENU_KEYBOARD
                        )
                    else:
                        await update.message.reply_text(
                            "برای استفاده از امکانات ربات، لطفاً ابتدا شماره تلفن خود را ثبت کنید:",
                            reply_markup=REGISTER_MENU_KEYBOARD
                        )
                    context.user_data['state'] = 'REGISTER'
                    return 'REGISTER'
                    
                # اگر شماره معتبر داشت
                return await func(update, context, *args, **kwargs)
                
            else:
                # کاربر در دیتابیس نیست
                logger.info(f"User {telegram_id} not found in database")
                await send_register_prompt(update)
                context.user_data['state'] = 'REGISTER'
                return 'REGISTER'
                
        except Exception as e:
            logger.error(f"Error checking phone requirement: {e}")
            # در صورت خطا اجازه عبور می‌دهیم
            return await func(update, context, *args, **kwargs)
            
    return wrapper

async def send_register_prompt(update: Update):
    """ارسال پیام درخواست ثبت شماره"""
    message = (
        "برای استفاده از امکانات ربات، لطفاً ابتدا شماره تلفن خود را ثبت کنید:"
    )
    if update.callback_query:
        await update.callback_query.message.reply_text(
            message,
            reply_markup=REGISTER_MENU_KEYBOARD
        )
    else:
        await update.message.reply_text(
            message,
            reply_markup=REGISTER_MENU_KEYBOARD
        )

async def check_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """فقط بررسی وجود شماره تلفن معتبر برای کاربر"""
    telegram_id = str(update.effective_user.id)
    logger.info(f"Checking phone for user {telegram_id}")
    
    try:
        response = requests.get(f"{BASE_URL}users/?telegram_id={telegram_id}")
        logger.info(f"Check phone response: {response.status_code} - {response.text}")
        
        if response.status_code == 200 and response.json():
            user_data = response.json()[0]
            phone = user_data.get('phone')
            
            if phone and not phone.startswith('tg_'):
                context.user_data['phone'] = phone
                logger.info(f"Valid phone found: {phone}")
                return True
                
        logger.info("No valid phone found")
        return False

    except Exception as e:
        logger.error(f"Error checking phone: {e}")
        return False

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle receiving the user's phone number."""
    logger.info("=== Starting handle_contact function ===")
    try:
        contact = update.message.contact
        telegram_id = str(update.effective_user.id)
        logger.info(f"Received contact for user {telegram_id}: {contact.phone_number}")
        
        # اطمینان از تطابق شماره با کاربر
        if str(contact.user_id) != telegram_id:
            logger.warning(f"Phone mismatch - Contact user_id: {contact.user_id}, Sender id: {telegram_id}")
            await update.message.reply_text(
                "❌ لطفاً فقط شماره تلفن خودتان را به اشتراک بگذارید!",
                reply_markup=REGISTER_MENU_KEYBOARD
            )
            context.user_data['state'] = REGISTER
            return REGISTER

        # تمیز کردن شماره تلفن
        phone = contact.phone_number.lstrip('+')
        if phone.startswith('98'):
            phone = '0' + phone[2:]
        elif not phone.startswith('0'):
            phone = '0' + phone
        logger.info(f"Cleaned phone number: {phone}")

        # ذخیره شماره در دیتابیس
        success, status = await save_user_phone(telegram_id, phone, update.effective_user.full_name)
        logger.info(f"Save phone result: success={success}, status={status}")
        
        if not success:
            error_messages = {
                "duplicate_phone": "❌ این شماره قبلاً توسط کاربر دیگری ثبت شده است.",
                "api_error": "❌ خطا در ثبت شماره تلفن. لطفاً دوباره تلاش کنید.",
                "server_error": "❌ خطا در ارتباط با سرور. لطفاً دوباره تلاش کنید."
            }
            await update.message.reply_text(
                error_messages.get(status, "❌ خطای ناشناخته. لطفاً دوباره تلاش کنید."),
                reply_markup=REGISTER_MENU_KEYBOARD
            )
            context.user_data['state'] = REGISTER
            return REGISTER

        # ذخیره موفق
        context.user_data['phone'] = phone
        context.user_data['state'] = ROLE
        await update.message.reply_text(
            "✅ شماره تلفن شما با موفقیت ثبت شد.",
            reply_markup=MAIN_MENU_KEYBOARD
        )
        logger.info("Successfully registered phone and set state to ROLE")
        return ROLE

    except Exception as e:
        logger.error(f"Error in handle_contact: {str(e)}")
        context.user_data['state'] = REGISTER
        await update.message.reply_text(
            "❌ خطا در ثبت شماره تلفن. لطفاً دوباره تلاش کنید.",
            reply_markup=REGISTER_MENU_KEYBOARD
        )
        return REGISTER