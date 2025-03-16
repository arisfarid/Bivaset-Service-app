from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging
from utils import upload_files
from .project_details_handler import create_dynamic_keyboard

logger = logging.getLogger(__name__)

async def handle_attachment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    state = context.user_data.get('state')
    telegram_id = str(update.effective_user.id)

    if update.message and update.message.photo:
        new_photos = [photo.file_id for photo in update.message.photo]
        if 'files' not in context.user_data:
            context.user_data['files'] = []

        current_files = context.user_data['files']
        # چک کردن تکراری‌ها (بخش سوم رو اینجا پیاده می‌کنیم)
        added_photos = [photo for photo in new_photos if photo not in current_files]
        if not added_photos and new_photos:
            await update.message.reply_text("❌ این عکس‌ها قبلاً فرستاده شدن و اضافه نمی‌شن!")
            return True

        current_files.extend(added_photos)
        
        if state == 'new_project_details_files':
            if len(current_files) > 5:
                removed_count = len(current_files) - 5
                context.user_data['files'] = current_files[:5]
                await update.message.reply_text(
                    f"❌ فقط ۵ عکس می‌تونی بفرستی! {removed_count} عکس اضافی حذف شد."
                )
            else:
                await update.message.reply_text(
                    f"📸 {len(added_photos)} عکس جدید دریافت شد. الان {len(current_files)} از ۵ تاست."
                )
            
            logger.info(f"Photos received from {telegram_id}: {added_photos}")
            
            keyboard = [
                [KeyboardButton("🏁 اتمام ارسال تصاویر"), KeyboardButton("📋 مدیریت عکس‌ها")],
                [KeyboardButton("⬅️ بازگشت")]
            ]
            await update.message.reply_text(
                "📸 عکس دیگه‌ای داری؟ اگه نه، 'اتمام ارسال تصاویر' رو بزن:",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            return True
        else:
            await update.message.reply_text("📸 الان نمی‌تونی عکس بفرستی! اول یه درخواست شروع کن.")
            context.user_data.pop('files', None)
            return True

    # مدیریت دکمه‌ها
    text = update.message.text if update.message else None
    if state == 'new_project_details_files':
        if text == "🏁 اتمام ارسال تصاویر":
            context.user_data['state'] = 'new_project_details'
            await update.message.reply_text(
                "📋 جزئیات درخواست:",
                reply_markup=create_dynamic_keyboard(context)
            )
            return True
        elif text == "📋 مدیریت عکس‌ها":
            await show_photo_management(update, context)
            return True

    return False

async def show_photo_management(update: Update, context: ContextTypes.DEFAULT_TYPE):
    files = context.user_data.get('files', [])
    if not files:
        await update.message.reply_text("📭 هنوز عکسی نفرستادی!")
        keyboard = [
            [KeyboardButton("🏁 اتمام ارسال تصاویر"), KeyboardButton("📋 مدیریت عکس‌ها")],
            [KeyboardButton("⬅️ بازگشت")]
        ]
        await update.message.reply_text(
            "📸 برو عکس بفرست یا برگرد:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return

    message = "📸 عکس‌های ارسالی:\n"
    inline_keyboard = []
    for i, file_id in enumerate(files, 1):
        message += f"{i}. عکس {i} (ID: {file_id[:10]}...)\n"
        inline_keyboard.append([
            InlineKeyboardButton(f"🗑 حذف عکس {i}", callback_data=f"delete_photo_{i-1}"),
            InlineKeyboardButton(f"🔄 جایگزین عکس {i}", callback_data=f"replace_photo_{i-1}")
        ])
    inline_keyboard.append([InlineKeyboardButton("⬅️ برگشت", callback_data="back_to_upload")])
    
    await update.message.reply_text(
        message + "\nچیکار می‌خوای بکنی؟",
        reply_markup=InlineKeyboardMarkup(inline_keyboard)
    )
    context.user_data['state'] = 'managing_photos'

async def upload_attachments(files, context):
    return await upload_files(files, context)