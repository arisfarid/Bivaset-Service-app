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
        photos = update.message.photo  # لیست عکس‌ها
        if 'files' not in context.user_data:
            context.user_data['files'] = []
        files = context.user_data['files']

        if len(photos) > 1:
            await update.message.reply_text("❌ فقط یه عکس توی هر پیام قبول می‌شه! اولین عکس ثبت شد.")
            photo_file = photos[-1].file_id  # بزرگ‌ترین سایز
            files.append(photo_file)
        else:
            photo_file = photos[-1].file_id
            files.append(photo_file)
            await update.message.reply_text(f"📸 عکس {len(files)} از ۵ ثبت شد.")

        logger.info(f"Photo received from {telegram_id}: {photo_file}")

        if state == 'new_project_details_files':
            if len(files) >= 5:
                await update.message.reply_text("✅ حداکثر ۵ عکس ثبت شد! لطفاً 'اتمام ارسال تصاویر' رو بزن.")
            else:
                keyboard = [
                    [KeyboardButton("🏁 اتمام ارسال تصاویر"), KeyboardButton("⬅️ بازگشت")]
                ]
                await update.message.reply_text(
                    "📸 عکس بعدی رو بفرست یا 'اتمام ارسال تصاویر' رو بزن:",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
        else:
            await update.message.reply_text("📸 الان نمی‌تونی عکس بفرستی! اول یه درخواست شروع کن.")
        return True

    # مدیریت اتمام ارسال
    text = update.message.text if update.message else None
    if state == 'new_project_details_files' and text == "🏁 اتمام ارسال تصاویر":
        context.user_data['state'] = 'new_project_details'
        await update.message.reply_text(
            "📋 جزئیات درخواست:",
            reply_markup=create_dynamic_keyboard(context)
        )
        return True

    return False

async def upload_attachments(files, context):
    return await upload_files(files, context)