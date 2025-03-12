from telegram import Update
from telegram.ext import ContextTypes
from handlers.new_project_handlers import handle_new_project, handle_new_project_states
from handlers.view_projects_handlers import handle_view_projects, handle_view_projects_states
from handlers.project_details_handlers import handle_project_details

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    telegram_id = str(update.effective_user.id)
    
    if text == "📋 درخواست خدمات (کارفرما)":
        keyboard = [
            [KeyboardButton("📋 درخواست خدمات جدید"), KeyboardButton("📊 مشاهده درخواست‌ها")],
            [KeyboardButton("⬅️ بازگشت")]
        ]
        await update.message.reply_text(
            "🎉 عالیه، {}! می‌خوای خدمات جدید درخواست کنی یا پیشنهادات رو ببینی؟".format(update.effective_user.full_name),
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return
    elif text == "🔧 پیشنهاد قیمت (مجری)":
        keyboard = [
            [KeyboardButton("📋 مشاهده درخواست‌ها"), KeyboardButton("💡 پیشنهاد کار")],
            [KeyboardButton("⬅️ بازگشت")]
        ]
        await update.message.reply_text(
            "🌟 خوبه، {}! می‌خوای درخواست‌های موجود رو ببینی یا پیشنهاد کار بدی؟".format(update.effective_user.full_name),
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return
    elif text == "📋 درخواست خدمات جدید":
        await handle_new_project(update, context)
        return
    elif text == "📊 مشاهده درخواست‌ها":
        await handle_view_projects(update, context)
        return
    
    # بررسی حالت‌های پروژه جدید
    if await handle_new_project_states(update, context, text):
        return
    # بررسی حالت‌های مشاهده درخواست‌ها
    if await handle_view_projects_states(update, context, text):
        return
    # بررسی حالت‌های جزئیات پروژه
    if await handle_project_details(update, context, text):
        return
    
    await update.message.reply_text("❌ گزینه نامعتبر! لطفاً از منو انتخاب کن.")