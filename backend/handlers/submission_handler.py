from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils import generate_title, convert_deadline_to_date
from django.contrib.gis.geos import Point
import requests
import logging
from .start_handler import start
from .attachment_handler import upload_attachments

logger = logging.getLogger(__name__)
BASE_URL = 'http://185.204.171.107:8000/api/'

async def submit_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    location = context.user_data.get('location')
    location_data = None
    if location:
        location_data = {
            'type': 'Point',
            'coordinates': [location['longitude'], location['latitude']]
        }
    
    data = {
        'title': generate_title(context),
        'description': context.user_data.get('description', ''),
        'category': context.user_data.get('category_id', ''),
        'service_location': context.user_data.get('service_location', ''),
        'location': location_data,
        'budget': context.user_data.get('budget', None),
        'deadline_date': convert_deadline_to_date(context.user_data.get('deadline', None)),
        'start_date': context.user_data.get('need_date', None),
        'files': await upload_attachments(context.user_data.get('files', []), context),
        'user_telegram_id': str(update.effective_user.id)
    }
    logger.info(f"Sending project data to API: {data}")
    try:
        response = requests.post(f"{BASE_URL}projects/", json=data)
        if response.status_code == 201:
            project = response.json()
            project_id = project.get('id', 'نامشخص')
            files = context.user_data.get('files', [])
            message = (
                f"🎉 درخواست شما با کد {project_id} ثبت شد!\n"
                f"📌 دسته‌بندی: {context.user_data.get('categories', {}).get(context.user_data.get('category_id', ''), {}).get('name', 'نامشخص')}\n"
                f"📝 توضیحات: {context.user_data.get('description', '')}\n"
                f"📅 تاریخ نیاز: {context.user_data.get('need_date', 'مشخص نشده')}\n"
                f"⏳ مهلت انجام: {context.user_data.get('deadline', 'مشخص نشده')} روز\n"
                f"💰 بودجه: {context.user_data.get('budget', 'مشخص نشده')} تومان\n"
                f"📏 مقدار و واحد: {context.user_data.get('quantity', 'مشخص نشده')}\n"
            )
            if context.user_data.get('location'):
                message += f"📍 لوکیشن: https://maps.google.com/maps?q={context.user_data['location']['latitude']},{context.user_data['location']['longitude']}\n"
            if len(files) > 1:
                message += "📸 لینک عکس‌ها:\n" + "\n".join([f"- {file}" for file in files[1:]])
            inline_keyboard = [
                [InlineKeyboardButton("✏️ ویرایش", callback_data=f"edit_{project_id}"),
                 InlineKeyboardButton("⛔ بستن", callback_data=f"close_{project_id}")],
                [InlineKeyboardButton("🗑 حذف", callback_data=f"delete_{project_id}"),
                 InlineKeyboardButton("⏰ تمدید", callback_data=f"extend_{project_id}")],
                [InlineKeyboardButton("💡 پیشنهادها", callback_data=f"offers_{project_id}")]
            ]
            if files:
                await update.message.reply_photo(
                    photo=files[0],
                    caption=message,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard)
                )
            else:
                await update.message.reply_text(
                    message,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard)
                )
        else:
            logger.error(f"API error: {response.text}")
            await update.message.reply_text(f"❌ خطا در ثبت درخواست: {response.text[:50]}...")
    except requests.exceptions.ConnectionError:
        logger.error("Connection error while submitting project")
        await update.message.reply_text("❌ خطا: سرور بک‌اند در دسترس نیست.")
    context.user_data.clear()
    await start(update, context)