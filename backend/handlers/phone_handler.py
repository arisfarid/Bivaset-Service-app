from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
import random
import requests
import logging
from utils import BASE_URL
from keyboards import MAIN_MENU_KEYBOARD

logger = logging.getLogger(__name__)

CHANGE_PHONE, VERIFY_CODE = range(20, 22)

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
