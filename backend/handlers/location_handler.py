from telegram import Update
from telegram.ext import ContextTypes
from utils import create_dynamic_keyboard

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    location = update.message.location
    context.user_data['location'] = {'longitude': location.longitude, 'latitude': location.latitude}
    if context.user_data.get('state') == 'new_project_location_input':
        context.user_data['state'] = 'new_project_details'
        await update.message.reply_text(
            f"📋 جزئیات درخواست\n"
            "اگه بخوای می‌تونی برای راهنمایی بهتر مجری‌ها این اطلاعات رو هم وارد کنی:",
            reply_markup=create_dynamic_keyboard(context)
        )
    else:
        await update.message.reply_text("📍 لوکیشن دریافت شد، لطفاً ادامه بده.")