import os
import requests
import re
import sys
import logging  # اضافه شده
from datetime import datetime, timedelta
from khayyam import JalaliDatetime
from telegram import KeyboardButton, ReplyKeyboardMarkup

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
    for file_id in file_ids:
        try:
            file = await context.bot.get_file(file_id)
            file_data = await file.download_as_bytearray()
            files = {'file': ('image.jpg', file_data, 'image/jpeg')}
            response = requests.post(f"{BASE_URL}upload/", files=files)
            if response.status_code == 201:
                uploaded_urls.append(response.json().get('file_url'))
            else:
                uploaded_urls.append(None)
        except Exception as e:
            uploaded_urls.append(None)
    return uploaded_urls

def get_last_mod_time():
    return os.path.getmtime(BOT_FILE)

def save_timestamp():
    with open(TIMESTAMP_FILE, 'w') as f:
        f.write(str(get_last_mod_time()))

def load_timestamp():
    if os.path.exists(TIMESTAMP_FILE):
        with open(TIMESTAMP_FILE, 'r') as f:
            return float(f.read())
    return 0

def check_for_updates(bot_data):
    last_mod_time = get_last_mod_time()
    saved_time = load_timestamp()
    logger.info(f"Last mod time: {last_mod_time}, Saved time: {saved_time}")
    result = last_mod_time > saved_time
    logger.info(f"Update check result: {result}")
    return result

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

def create_dynamic_keyboard(context):
    buttons = []
    if 'files' not in context.user_data:
        buttons.append([KeyboardButton("📸 تصاویر یا فایل")])
    if 'need_date' not in context.user_data:
        buttons.append([KeyboardButton("📅 تاریخ نیاز")])
    if 'deadline' not in context.user_data:
        buttons.append([KeyboardButton("⏳ مهلت انجام")])
    if 'budget' not in context.user_data:
        buttons.append([KeyboardButton("💰 بودجه")])
    if 'quantity' not in context.user_data:
        buttons.append([KeyboardButton("📏 مقدار و واحد")])
    buttons.append([KeyboardButton("⬅️ بازگشت"), KeyboardButton("✅ ثبت درخواست")])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)