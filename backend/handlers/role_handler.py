from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, filters

async def handle_role(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    choice = update.message.text
    if choice == "👔درخواست خدمات (کارفرما)":
        context.user_data['role'] = 'client'
        await update.message.reply_text("عالیه! 😊 لطفاً پروژه‌ت رو تعریف کن.")
        return 2  # Move to project submission state
    elif choice == "🦺پیشنهاد قیمت (مجری)":
        context.user_data['role'] = 'contractor'
        await update.message.reply_text("خوبه! 😊 حالا می‌تونی پروژه‌ها رو ببینی و پیشنهاد بدی.")
        return 3  # Move to proposal submission state
    else:
        await update.message.reply_text("❌ گزینه نامعتبر! لطفاً از منو انتخاب کن.")
        return 1  # Stay in role selection state

role_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_role)
