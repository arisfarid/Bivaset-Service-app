import os
import requests
import re
import sys
import logging
import asyncio
from datetime import datetime, timedelta
from khayyam import JalaliDatetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import Update
from telegram.ext import ContextTypes
from localization import get_message
from keyboards import get_main_menu_keyboard

logger = logging.getLogger(__name__)

BASE_URL = 'http://185.204.171.107:8000/api/'
BOT_FILE = os.path.abspath(__file__)
TIMESTAMP_FILE = '/home/ubuntu/Bivaset-Service-app/backend/last_update.txt'

async def get_user_phone(telegram_id: str) -> str:
    """دریافت شماره تلفن کاربر از دیتابیس"""
    logger.info(f"Getting phone for telegram_id: {telegram_id}")
    try:
        response = requests.get(f"{BASE_URL}users/?telegram_id={telegram_id}")
        logger.info(f"API Response: {response.status_code}")
        
        if response.status_code == 200 and response.json():
            user_data = response.json()[0]
            phone = user_data.get('phone')
            if phone and not phone.startswith('tg_'):
                logger.info(f"Found valid phone: {phone}")
                return phone
        logger.info("No valid phone found")
        return None
    except Exception as e:
        logger.error(f"Error in get_user_phone: {e}")
        return None

async def save_user_phone(telegram_id: str, phone: str, name: str = None) -> tuple[bool, str]:
    """ذخیره یا آپدیت شماره تلفن کاربر در دیتابیس"""
    logger.info(f"=== Starting save_user_phone function for {telegram_id} ===")
    try:
        # چک کردن تکراری نبودن شماره
        check_response = requests.get(f"{BASE_URL}users/?phone={phone}")
        if check_response.status_code == 200 and check_response.json():
            existing_user = check_response.json()[0]
            if existing_user['telegram_id'] != telegram_id:
                logger.warning(f"Phone {phone} already registered to {existing_user['telegram_id']}")
                return False, "duplicate_phone"

        user_data = {
            'phone': phone,
            'telegram_id': telegram_id,
            'name': name or 'کاربر',
            'role': 'client'
        }

        # چک کردن وجود کاربر
        user_response = requests.get(f"{BASE_URL}users/?telegram_id={telegram_id}")
        
        if user_response.status_code == 200 and user_response.json():
            # آپدیت کاربر موجود
            user = user_response.json()[0]
            update_url = f"{BASE_URL}users/{user['id']}/"
            response = requests.put(update_url, json=user_data)
        else:
            # ایجاد کاربر جدید
            response = requests.post(f"{BASE_URL}users/", json=user_data)

        success = response.status_code in [200, 201]
        logger.info(f"Save operation {'successful' if success else 'failed'}")
        return success, "success" if success else "api_error"

    except Exception as e:
        logger.error(f"Error in save_user_phone: {e}")
        return False, "server_error"

async def get_categories():
    """دریافت دسته‌بندی‌ها از API"""
    try:
        response = requests.get(f"{BASE_URL}categories/")
        if response.status_code == 200:
            categories = {}
            for cat in response.json():
                categories[cat['id']] = {
                    'name': cat['name'],
                    'description': cat['description'],
                    'parent': cat['parent'],
                    'children': cat['children']
                }
            return categories
        return {}
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        return {}

async def upload_files(file_ids, context):
    uploaded_urls = []
    project_id = context.user_data.get('project_id')  # دریافت project_id از context
    for file_id in file_ids:
        try:
            file = await context.bot.get_file(file_id)
            file_data = await file.download_as_bytearray()
            files = {'file': ('image.jpg', file_data, 'image/jpeg')}
            data = {'project_id': project_id}  # ارسال project_id
            response = requests.post(f"{BASE_URL.rstrip('/api/')}/upload/", files=files, data=data)
            if response.status_code == 201:
                file_url = response.json().get('file_url')
                uploaded_urls.append(file_url)
            else:
                uploaded_urls.append(None)
        except Exception as e:
            uploaded_urls.append(None)
    return uploaded_urls

async def upload_attachments(files, context):
    """آپلود فایل‌ها به سرور"""
    try:
        # استفاده از upload_files موجود
        return await upload_files(files, context)
    except Exception as e:
        logger.error(f"Error in upload_attachments: {e}")
        return []

def persian_to_english(text):
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    english_digits = '0123456789'
    translation_table = str.maketrans(persian_digits, english_digits)
    return text.translate(translation_table)

def clean_budget(budget_str):
    if not budget_str:
        return None
    budget_str = persian_to_english(budget_str)
    budget_str = ''.join(filter(str.isdigit, budget_str))
    return int(budget_str) if budget_str and budget_str.isdigit() else None

def validate_deadline(deadline_str):
    if not deadline_str:
        return None
    deadline_str = persian_to_english(deadline_str)
    if deadline_str.isdigit():
        return deadline_str
    return None

def validate_date(date_str):
    date_str = persian_to_english(date_str)
    pattern = r'^\d{4}/\d{2}/\d{2}$'
    if not re.match(pattern, date_str):
        return False
    try:
        year, month, day = map(int, date_str.split('/'))
        input_date = JalaliDatetime(year, month, day)
        today = JalaliDatetime.now()
        if input_date >= today:
            return True
        return False
    except ValueError:
        return False

def convert_deadline_to_date(deadline_str):
    if not deadline_str:
        return None
    deadline_str = persian_to_english(deadline_str)
    days = int(deadline_str)
    return (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')

def generate_title(context):
    desc = context.user_data.get('description', '')
    category_id = context.user_data.get('category_id', '')
    categories = context.user_data.get('categories', {})
    category_name = categories.get(category_id, {}).get('name', 'نامشخص')
    location = context.user_data.get('location', None)
    deadline = context.user_data.get('deadline', None)
    quantity = context.user_data.get('quantity', None)
    service_location = context.user_data.get('service_location', '')
    
    title = f"{category_name}: {desc[:20]}"
    if service_location == 'remote':
        title += " (غیرحضوری)"
    else:
        city = "تهران" if location else "محل نامشخص"
        title += f" در {city}"
    if deadline:
        title += f"، مهلت {deadline} روز"
    if quantity:
        title += f" ({quantity})"
    return title.strip()

async def log_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ثبت لاگ تعامل با کاربر"""
    if update.message:
        logger.info(f"Message from user {update.effective_user.id}: {update.message.text}")
    elif update.callback_query:
        logger.info(f"Callback from user {update.effective_user.id}: {update.callback_query.data}")

def format_price(number):
    """تبدیل اعداد مبلغ به فرمت هزارگان با کاما"""
    try:
        return "{:,}".format(int(number))
    except (ValueError, TypeError):
        return number

async def ensure_active_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اطمینان از افزودن چت به لیست چت‌های فعال"""
    chat_id = update.effective_chat.id
    if 'active_chats' not in context.bot_data:
        context.bot_data['active_chats'] = []
    if chat_id not in context.bot_data['active_chats']:
        context.bot_data['active_chats'].append(chat_id)
        logger.info(f"Added {chat_id} to active chats")
    return True

async def restart_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """راه‌اندازی مجدد گفتگو با کاربر"""
    try:
        # پاک کردن داده‌های کاربر
        context.user_data.clear()
        context.user_data['state'] = 2  # ROLE
        
        # ارسال پیام خوش‌آمدگویی و منوی اصلی
        await update.message.reply_text(
            get_message("welcome", context, update),
            reply_markup=get_main_menu_keyboard(lang=context.user_data.get('lang', 'fa'))
        )
        logger.info(f"Chat restarted for user {update.effective_user.id}")
        return True
    except Exception as e:
        logger.error(f"Error restarting chat: {e}")
        return False

async def delete_previous_messages(sent, context, n=3):
    """
    بعد از ارسال پیام جدید (sent)، n پیام قبلی (چه از ربات چه از کاربر) را حذف می‌کند.
    """
    try:
        chat_id = sent.chat_id
        last_msg_id = sent.message_id
        for i in range(1, n + 1):
            msg_id = last_msg_id - i
            if msg_id > 0:
                try:
                    await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
                except Exception:
                    pass
    except Exception:
        pass