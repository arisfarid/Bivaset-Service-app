from telegram import Update
from telegram.ext import ContextTypes
from utils import create_dynamic_keyboard  # Import the function from utils

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    location = update.message.location
    context.user_data['location'] = {'longitude': location.longitude, 'latitude': location.latitude}
    context.user_data['state'] = 'new_project_details'
    await update.message.reply_text(
        f"📋 جزئیات درخواست\n"
        "اگه بخوای می‌تونی برای راهنمایی بهتر مجری‌ها این اطلاعات رو هم وارد کنی:",
        reply_markup=create_dynamic_keyboard(context)
    )