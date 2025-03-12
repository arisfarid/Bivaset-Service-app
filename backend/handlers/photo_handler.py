from telegram import Update
from telegram.ext import ContextTypes
from utils import create_dynamic_keyboard

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get('state')
    if state == 'new_project_details_files':
        files = context.user_data.get('files', [])
        if len(files) >= 5:
            await update.message.reply_text("❌ حداکثر ۵ عکس می‌تونی بفرستی! 'اتمام ارسال تصاویر' رو بزن.")
            return
        photo_file = update.message.photo[-1].file_id  # فقط بزرگ‌ترین سایز عکس
        files.append(photo_file)
        context.user_data['files'] = files[:1] if len(files) > 1 else files  # فقط اولین عکس رو نگه دار
        await update.message.reply_text(f"📸 عکس {len(files)} از ۵ دریافت شد.")
        if len(files) > 1:
            await update.message.reply_text("❌ فقط یه عکس در هر نوبت بفرست! عکس بعدی رو جدا بفرست.")
            context.user_data['files'] = files[:1]  # بقیه رو پاک کن
        keyboard = [
            [KeyboardButton("🏁 اتمام ارسال تصاویر"), KeyboardButton("⬅️ بازگشت")]
        ]
        await update.message.reply_text(
            "📸 اگه عکس دیگه‌ای نداری، 'اتمام ارسال تصاویر' رو بزن:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
    else:
        await update.message.reply_text("📸 الان نمی‌تونی عکس بفرستی! اول یه درخواست شروع کن.")