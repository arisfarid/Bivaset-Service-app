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

async def change_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Prompt user to enter a new phone number."""
    await update.message.reply_text(
        "📱 لطفاً شماره تلفن جدید خود را وارد کنید:\n"
        "مثال: 09123456789"
    )
    return CHANGE_PHONE

async def handle_new_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Validate and send a verification code for the new phone number."""
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
    
    await update.message.reply_text(
        "📤 کد تأیید ارسال شد.\n"
        f"(کد تست: {verification_code})\n"
        "لطفاً کد 6 رقمی دریافتی را وارد کنید:"
    )
    return VERIFY_CODE

async def verify_new_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Verify the code and update the phone number."""
    code = update.message.text.strip()
    stored_code = context.user_data.get('verification_code')
    expires_at = context.user_data.get('code_expires_at')
    new_phone = context.user_data.get('new_phone')
    
    if not all([stored_code, expires_at, new_phone]):
        await update.message.reply_text(
            "❌ اطلاعات تأیید نامعتبر است.",
            reply_markup=MAIN_MENU_KEYBOARD
        )
        return CHANGE_PHONE
        
    if datetime.now() > expires_at:
        await update.message.reply_text(
            "⏰ کد تأیید منقضی شده است.",
            reply_markup=MAIN_MENU_KEYBOARD
        )
        return CHANGE_PHONE
        
    if code != stored_code:
        await update.message.reply_text(
            "❌ کد وارد شده اشتباه است.",
            reply_markup=MAIN_MENU_KEYBOARD
        )
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
                    "✅ شماره تلفن شما با موفقیت تغییر کرد.",
                    reply_markup=MAIN_MENU_KEYBOARD
                )
            else:
                await update.message.reply_text(
                    "❌ خطا در بروزرسانی شماره تلفن.",
                    reply_markup=MAIN_MENU_KEYBOARD
                )
                
        for key in ['verification_code', 'code_expires_at', 'new_phone']:
            context.user_data.pop(key, None)
            
    except Exception as e:
        logger.error(f"Error updating phone: {e}")
        await update.message.reply_text(
            "❌ خطا در بروزرسانی شماره تلفن.",
            reply_markup=MAIN_MENU_KEYBOARD
        )
    
    return CHANGE_PHONE
