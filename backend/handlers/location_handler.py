from telegram import Update
from telegram.ext import ContextTypes
from some_module import create_dynamic_keyboard  # Replace 'some_module' with the actual module name

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    location = update.message.location
    context.user_data['location'] = {'longitude': location.longitude, 'latitude': location.latitude}
    context.user_data['state'] = 'new_project_details'
    await update.message.reply_text(
        f"📋 جزئیات درخواست\n"
        "اگه بخوای می‌تونی برای راهنمایی بهتر مجری‌ها این اطلاعات رو هم وارد کنی:",
        reply_markup=create_dynamic_keyboard(context)
    )