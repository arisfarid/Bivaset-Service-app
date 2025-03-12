from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
import requests
from utils import BASE_URL

async def check_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    response = requests.get(f"{BASE_URL}users/?telegram_id={telegram_id}")
    if response.status_code == 200 and response.json():
        context.user_data['phone'] = response.json()[0]['phone']
    else:
        keyboard = [[KeyboardButton("ثبت شماره تلفن", request_contact=True)]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text(
            " 😊 برای استفاده از امکانات ربات، لطفاً شماره تلفنت رو با دکمه زیر ثبت کن! 📱",
            reply_markup=reply_markup
        )

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        await start(update, context)
    except requests.exceptions.ConnectionError:
        await update.message.reply_text("❌ خطا: سرور بک‌اند در دسترس نیست.")
