from functools import wraps
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from datetime import datetime, timedelta
import random
import requests
import logging
import json
import aiohttp
from utils import BASE_URL, save_user_phone, log_chat
from handlers.states import START, REGISTER, ROLE, EMPLOYER_MENU, CATEGORY, SUBCATEGORY, DESCRIPTION, LOCATION_TYPE, LOCATION_INPUT, DETAILS, DETAILS_FILES, DETAILS_DATE, DETAILS_DEADLINE, DETAILS_BUDGET, DETAILS_QUANTITY, SUBMIT, VIEW_PROJECTS, PROJECT_ACTIONS, CHANGE_PHONE, VERIFY_CODE
from localization import get_message
from keyboards import get_main_menu_keyboard, REGISTER_MENU_KEYBOARD, REGISTER_INLINE_KEYBOARD

logger = logging.getLogger(__name__)

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
    await update.message.reply_text(get_message("enter_new_phone_prompt", context, update))
    context.user_data['verify_attempts'] = 0  # ریست تعداد تلاش‌ها
    return CHANGE_PHONE

async def handle_new_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """بررسی شماره تلفن جدید و ارسال کد تأیید"""
    logger.info(f"[handle_new_phone] user_id={update.effective_user.id} | context.user_data={context.user_data}")
    new_phone = update.message.text.strip()
    if not new_phone.startswith('09') or not new_phone.isdigit() or len(new_phone) != 11:
        await update.message.reply_text(get_message("invalid_phone", context, update))
        return CHANGE_PHONE

    response = requests.get(f"{BASE_URL}users/?phone={new_phone}")
    if response.status_code == 200 and response.json():
        await update.message.reply_text(get_message("phone_already_registered", context, update))
        return CHANGE_PHONE

    verification_code = ''.join([str(random.randint(0, 9)) for _ in range(4)])
    context.user_data.update({
        'new_phone': new_phone,
        'verification_code': verification_code,
        'code_expires_at': datetime.now() + timedelta(minutes=2),
        'verify_attempts': 0
    })
    logger.info(f"[handle_new_phone] updated context.user_data={context.user_data}")

    if await send_verification_code(new_phone, verification_code):
        await update.message.reply_text(
            get_message("verification_code_sent", context, update)
        )
        return VERIFY_CODE
    else:
        await update.message.reply_text(get_message("error_sending_verification_code", context, update))
        return CHANGE_PHONE

async def verify_new_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """بررسی کد تأیید وارد شده"""
    logger.info(f"[verify_new_phone] user_id={update.effective_user.id} | context.user_data={context.user_data}")
    code = update.message.text.strip()
    stored_code = context.user_data.get('verification_code')
    expires_at = context.user_data.get('code_expires_at')
    new_phone = context.user_data.get('new_phone')
    attempts = context.user_data.get('verify_attempts', 0)

    if not all([stored_code, expires_at, new_phone]):
        await update.message.reply_text(get_message("invalid_verification_info", context, update))
        return CHANGE_PHONE

    if attempts >= MAX_ATTEMPTS:
        await update.message.reply_text(get_message("max_attempts_reached", context, update))
        return CHANGE_PHONE

    if datetime.now() > expires_at:
        await update.message.reply_text(get_message("verification_code_expired", context, update))
        return CHANGE_PHONE

    context.user_data['verify_attempts'] += 1
    logger.info(f"[verify_new_phone] verify_attempts increased: {context.user_data['verify_attempts']}")
    if code != stored_code:
        remaining = MAX_ATTEMPTS - context.user_data['verify_attempts']
        await update.message.reply_text(get_message("incorrect_verification_code", context, update))
        return VERIFY_CODE if remaining > 0 else CHANGE_PHONE

    try:
        telegram_id = str(update.effective_user.id)
        response = requests.get(f"{BASE_URL}users/?telegram_id={telegram_id}")
        if response.status_code == 200 and response.json():
            user = response.json()[0]
            user['phone'] = new_phone
            update_response = requests.put(f"{BASE_URL}users/{user['id']}/", json=user)
            if update_response.status_code == 200:
                await update.message.reply_text(
                    get_message("phone_registered", context, update),
                    reply_markup=get_main_menu_keyboard(context, update)
                )
            else:
                raise Exception("Failed to update phone number")
        for key in ['verification_code', 'code_expires_at', 'new_phone', 'verify_attempts']:
            context.user_data.pop(key, None)
        logger.info(f"[verify_new_phone] cleaned up context.user_data={context.user_data}")
    except Exception as e:
        logger.error(f"Error updating phone: {e}")
        await update.message.reply_text(get_message("error_registering_phone", context, update))
    return CHANGE_PHONE

async def check_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if user has registered phone number"""
    logger.info(f"Checking phone for user {update.effective_user.id}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f'http://localhost:8000/api/users/?telegram_id={update.effective_user.id}') as response:
                logger.info(f"Check phone response: {response.status} - {await response.text()}")
                if response.status == 200:
                    data = json.loads(await response.text())
                    if data and len(data) > 0 and data[0].get('phone'):
                        logger.info(f"Valid phone found: {data[0]['phone']}")
                        return True
    except Exception as e:
        logger.error(f"Error checking phone requirement: {e}")
    return False

def require_phone(func):
    """دکوراتور برای چک کردن شماره تلفن"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        logger.info(f"[require_phone] user_id={update.effective_user.id} | context.user_data={context.user_data}")
        try:
            if not await check_phone(update, context):
                if update.callback_query:
                    # استفاده از InlineKeyboardMarkup برای callback_query
                    message = update.callback_query.message
                    await update.callback_query.answer(get_message("phone_required", context, update))
                    # جداگانه ارسال کیبورد ReplyKeyboardMarkup برای دریافت شماره تلفن
                    await message.reply_text(
                        get_message("share_phone_instruction", context, update),
                        reply_markup=REGISTER_MENU_KEYBOARD
                    )
                else:
                    # استفاده مستقیم از ReplyKeyboardMarkup برای پیام‌های معمولی
                    await update.message.reply_text(
                        get_message("share_phone_prompt", context, update),
                        reply_markup=REGISTER_MENU_KEYBOARD
                    )
                context.user_data['state'] = REGISTER
                return REGISTER
            return await func(update, context, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in phone requirement decorator: {e}")
            if update.callback_query:
                try:
                    await update.callback_query.answer(get_message("general_error", context, update))
                except Exception:
                    pass
            return REGISTER
    return wrapper

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle received contact for phone registration"""
    logger.info(f"[handle_contact] user_id={update.effective_user.id} | context.user_data={context.user_data}")
    contact = update.message.contact
    
    if not contact.phone_number:
        await update.message.reply_text(
            get_message("invalid_phone", context, update),
            reply_markup=REGISTER_MENU_KEYBOARD
        )
        return REGISTER

    try:
        phone = contact.phone_number.replace('+', '')
        user_data = {
            'phone': phone,
            'telegram_id': str(update.effective_user.id),
            'name': update.effective_user.first_name,
            'role': 'client'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post('http://localhost:8000/api/users/', json=user_data) as response:
                logger.info(f"Register response: {response.status} - {await response.text()}")
                if response.status in [200, 201]:
                    await update.message.reply_text(
                        get_message("phone_registered", context, update),
                        reply_markup=get_main_menu_keyboard(context, update)
                    )
                    return ROLE
                else:
                    await update.message.reply_text(
                        get_message("error_registering_phone", context, update),
                        reply_markup=REGISTER_MENU_KEYBOARD
                    )
                    return REGISTER
    except Exception as e:
        logger.error(f"Error registering phone: {e}")
        await update.message.reply_text(
            get_message("error_registering_phone", context, update),
            reply_markup=REGISTER_MENU_KEYBOARD
        )
        return REGISTER