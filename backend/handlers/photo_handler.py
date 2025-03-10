from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from utils import create_dynamic_keyboard

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('state') != 'new_project_details_files':
        await update.message.reply_text("❌ لطفاً اول '📸 تصاویر یا فایل' رو انتخاب کن!")
        return
    if 'files' not in context.user_data:
        context.user_data['files'] = []
    
    if len(context.user_data['files']) >= 5:
        await update.message.reply_text("📸 تعداد تصاویر قابل ارسال پر شده. عکس جدید جایگزین اولین عکس شد.")
        context.user_data['files'].pop(0)
    
    photo = update.message.photo[-1]
    context.user_data['files'].append(photo.file_id)
    await update.message.reply_text(f"📸 عکس {len(context.user_data['files'])} از 5 دریافت شد.")
    
    keyboard = [
        [KeyboardButton("🏁 اتمام ارسال تصاویر"), KeyboardButton("⬅️ بازگشت")]
    ]
    await update.message.reply_text(
        "📸 اگه دیگه عکسی نداری، 'اتمام ارسال تصاویر' رو بزن:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

    if len(context.user_data['files']) >= 5:
        context.user_data['state'] = 'new_project_details'
        await update.message.reply_text(
            f"📋 جزئیات درخواست\n"
            "اگه بخوای می‌تونی برای راهنمایی بهتر مجری‌ها این اطلاعات رو هم وارد کنی:",
            reply_markup=create_dynamic_keyboard(context)
        )