import os
import requests
import re
import sys
import logging  # اضافه شده
from datetime import datetime, timedelta
from khayyam import JalaliDatetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)  # اضافه شده

BASE_URL = 'http://185.204.171.107:8000/api/'
BOT_FILE = os.path.abspath(__file__)
TIMESTAMP_FILE = '/home/ubuntu/Bivaset-Service-app/backend/last_update.txt'

async def get_user_phone(telegram_id):
    try:
        response = requests.get(f"{BASE_URL}users/?telegram_id={telegram_id}")
        if response.status_code == 200 and response.json():
            return response.json()[0]['phone']
        return None
    except requests.exceptions.ConnectionError:
        return None

async def get_categories():
    try:
        response = requests.get(f"{BASE_URL}categories/")
        if response.status_code == 200:
            categories = response.json()
            cat_dict = {cat['id']: {'name': cat['name'], 'parent': cat['parent'], 'children': cat['children']} for cat in categories}
            return cat_dict
        return {}
    except requests.exceptions.ConnectionError:
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

# بقیه توابع بدون تغییر
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
    user = update.effective_user
    if update.message:  # برای پیام‌های معمولی
        timestamp = update.message.date.strftime('%d/%m/%Y %H:%M:%S')
        if update.message.text:
            logger.info(f"{user.first_name}, [{timestamp}] - Text: {update.message.text}")
        elif update.message.photo:
            logger.info(f"{user.first_name}, [{timestamp}] - Sent {len(update.message.photo)} photo(s)")
        elif update.message.location:
            logger.info(f"{user.first_name}, [{timestamp}] - Location: {update.message.location.latitude}, {update.message.location.longitude}")
    elif update.callback_query:  # برای callback‌ها
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        logger.info(f"{user.first_name}, [{timestamp}] - Callback: {update.callback_query.data}")

async def ensure_active_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اطمینان از ثبت چت در لیست چت‌های فعال"""
    chat_id = update.effective_chat.id
    
    try:
        # اطمینان از وجود لیست active_chats
        if 'active_chats' not in context.bot_data:
            context.bot_data['active_chats'] = []
            
        # اضافه کردن چت جدید
        if chat_id not in context.bot_data['active_chats']:
            context.bot_data['active_chats'].append(chat_id)
            logger.info(f"Added {chat_id} to active chats. Total active chats: {len(context.bot_data['active_chats'])}")
            
            # ذخیره فوری در persistence
            if context.application and context.application.persistence:
                await context.application.persistence.update_bot_data(context.bot_data)
                logger.debug(f"Persisted active_chats update for chat {chat_id}")
                
        return True
            
    except Exception as e:
        logger.error(f"Error in ensure_active_chat for {chat_id}: {e}")
        return False

def format_price(number):
    """تبدیل اعداد مبلغ به فرمت هزارگان با کاما"""
    try:
        return "{:,}".format(int(number))
    except (ValueError, TypeError):
        return number

async def restart_chat(application, chat_id):
    """
    راه‌اندازی مجدد چت کاربر
    """
    try:
        # پاک کردن داده‌های قبلی کاربر
        user_data = await application.persistence.get_user_data()
        if str(chat_id) in user_data:
            user_data[str(chat_id)].clear()
            await application.persistence.update_user_data(chat_id, user_data[str(chat_id)])

        # ارسال کامند start به صورت خودکار
        await application.bot.send_message(
            chat_id=chat_id,
            text="/start",
            disable_notification=True
        )
        return True

    except Exception as e:
        logger.error(f"Error restarting chat {chat_id}: {e}")
        return False