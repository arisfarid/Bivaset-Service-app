from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
import logging
from utils import upload_files
from .project_details_handler import create_dynamic_keyboard

logger = logging.getLogger(__name__)

async def handle_attachment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get('state')
    telegram_id = str(update.effective_user.id)

    if update.message and update.message.photo:
        photo_file = update.message.photo[-1].file_id
        if 'files' not in context.user_data:
            context.user_data['files'] = []
        context.user_data['files'].append(photo_file)
        logger.info(f"Photo received from {telegram_id}: {photo_file}")

        if state == 'new_project_details_files':
            files = context.user_data.get('files', [])
            if len(files) >= 5:
                await update.message.reply_text("❌ حداکثر ۵ عکس می‌تونی بفرستی! 'اتمام ارسال تصاویر' رو بزن.")
                return True
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
            return True
        else:
            await update.message.reply_text("📸 الان نمی‌تونی عکس بفرستی! اول یه درخواست شروع کن.")
            return True

    # مدیریت اتمام ارسال
    text = update.message.text if update.message else None
    if state == 'new_project_details_files' and text == "🏁 اتمام ارسال تصاویر":
        context.user_data['state'] = 'new_project_details'
        await update.message.reply_text(
            f"📋 جزئیات درخواست:",
            reply_markup=create_dynamic_keyboard(context)
        )
        return True

    return False

async def upload_attachments(files, context):
    return await upload_files(files, context)  # تابع آپلود از utils