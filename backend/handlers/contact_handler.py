from telegram import Update
from telegram.ext import ContextTypes
import requests
from utils import BASE_URL
from .start_handler import start  # Import the start function

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
            message = f"🎉 ثبت‌نام شد، {name}!"
        elif response.status_code == 400 and "phone" in response.text:
            message = f"👋 خوش اومدی، {name}! شماره‌ات قبلاً ثبت شده."
        else:
            message = f"❌ خطا در ثبت‌نام: {response.text[:50]}..."
        await update.message.reply_text(message)
        await start(update, context)
    except requests.exceptions.ConnectionError:
        await update.message.reply_text("❌ خطا: سرور بک‌اند در دسترس نیست.")