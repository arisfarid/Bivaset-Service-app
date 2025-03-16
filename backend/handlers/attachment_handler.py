from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
import logging
from utils import upload_files
from .project_details_handler import create_dynamic_keyboard

logger = logging.getLogger(__name__)

async def handle_attachment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    state = context.user_data.get('state')
    telegram_id = str(update.effective_user.id)

    if update.message and update.message.photo:
        # گرفتن همه عکس‌های ارسالی توی یه پیام
        new_photos = [photo.file_id for photo in update.message.photo]
        if 'files' not in context.user_data:
            context.user_data['files'] = []

        current_files = context.user_data['files']
        total_files_before = len(current_files)
        current_files.extend(new_photos)
        
        if state == 'new_project_details_files':
            # اعمال محدودیت ۵ عکس
            if len(current_files) > 5:
                removed_count = len(current_files) - 5
                context.user_data['files'] = current_files[:5]
                await update.message.reply_text(
                    f"❌ فقط ۵ عکس می‌تونی بفرستی! {removed_count} عکس اضافی حذف شد."
                )
            else:
                await update.message.reply_text(
                    f"📸 {len(new_photos)} عکس دریافت شد. الان {len(context.user_data['files'])} از ۵ تاست."
                )
            
            logger.info(f"Photos received from {telegram_id}: {new_photos}")
            
            # نمایش دکمه‌ها برای ادامه یا اتمام
            keyboard = [
                [KeyboardButton("🏁 اتمام ارسال تصاویر"), KeyboardButton("⬅️ بازگشت")]
            ]
            await update.message.reply_text(
                "📸 عکس دیگه‌ای داری؟ اگه نه، 'اتمام ارسال تصاویر' رو بزن:",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            return True
        else:
            await update.message.reply_text("📸 الان نمی‌تونی عکس بفرستی! اول یه درخواست شروع کن.")
            context.user_data.pop('files', None)  # پاک کردن فایل‌ها اگه توی حالت درست نباشه
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
    return await upload_files(files, context)  # تابع آپلود از utils