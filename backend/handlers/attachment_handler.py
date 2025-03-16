from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging
from utils import upload_files, log_chat  # Added log_chat
from .project_details_handler import create_dynamic_keyboard

logger = logging.getLogger(__name__)

async def handle_attachment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    state = context.user_data.get('state')
    telegram_id = str(update.effective_user.id)
    current_files = context.user_data.get('files', [])

    if state == 'replacing_photo' and update.message.photo:
        new_photo = update.message.photo[-1].file_id
        index = context.user_data.get('replace_index')
        if 0 <= index < len(current_files):
            old_photo = current_files[index]
            current_files[index] = new_photo
            logger.info(f"Replaced photo {old_photo} with {new_photo} at index {index}")
            await update.message.reply_text("🔄 عکس جایگزین شد!")
            await log_chat(update, context)  # Log chat
            await show_photo_management(update, context)
            context.user_data['state'] = 'managing_photos'
        return True

    if update.message and update.message.photo:
        # فقط بزرگ‌ترین سایز عکس رو بگیریم (آخرین file_id توی لیست)
        new_photos = [update.message.photo[-1].file_id]
        if 'files' not in context.user_data:
            context.user_data['files'] = []

        current_files = context.user_data['files']
        # فقط عکس‌های جدید و غیرتکراری رو اضافه کن
        added_photos = [photo for photo in new_photos if photo not in current_files]
        remaining_slots = 5 - len(current_files)
        
        if state == 'new_project_details_files':
            if remaining_slots <= 0:
                await update.message.reply_text(
                    "❌ لیست عکس‌ها پره! برای حذف یا جایگزینی، 'مدیریت عکس‌ها' رو بزن."
                )
                await log_chat(update, context)  # Log chat
            else:
                photos_to_add = added_photos[:remaining_slots]
                current_files.extend(photos_to_add)
                ignored_count = len(new_photos) - len(photos_to_add)
                logger.info(f"Photos received from {telegram_id}: {photos_to_add}")
                await update.message.reply_text(
                    f"📸 {len(photos_to_add)} عکس ثبت شد. الان {len(current_files)} از ۵ تاست."
                    f"{f' ({ignored_count} عکس نادیده گرفته شد)' if ignored_count > 0 else ''}\n"
                    "برای حذف یا جایگزینی، 'مدیریت عکس‌ها' رو بزن."
                )
                await log_chat(update, context)  # Log chat
            
            keyboard = [
                [KeyboardButton("🏁 اتمام ارسال تصاویر"), KeyboardButton("📋 مدیریت عکس‌ها")],
                [KeyboardButton("⬅️ بازگشت")]
            ]
            await update.message.reply_text(
                "📸 عکس دیگه‌ای داری؟ اگه نه، 'اتمام ارسال تصاویر' رو بزن:",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            await log_chat(update, context)  # Log chat
            return True
        else:
            await update.message.reply_text("📸 الان نمی‌تونی عکس بفرستی! اول یه درخواست شروع کن.")
            await log_chat(update, context)  # Log chat
            context.user_data.pop('files', None)
            return True

    # مدیریت دکمه‌ها
    text = update.message.text if update.message else None
    if state in ['new_project_details_files', 'managing_photos']:
        if text == "🏁 اتمام ارسال تصاویر":
            context.user_data['state'] = 'new_project_details'
            await update.message.reply_text(
                "📋 جزئیات درخواست:",
                reply_markup=create_dynamic_keyboard(context)
            )
            await log_chat(update, context)  # Log chat
            return True
        elif text == "📋 مدیریت عکس‌ها":
            await show_photo_management(update, context)
            return True
        elif text == "⬅️ بازگشت":
            context.user_data['state'] = 'new_project_details'
            await update.message.reply_text(
                "📋 جزئیات درخواست:",
                reply_markup=create_dynamic_keyboard(context)
            )
            await log_chat(update, context)  # Log chat
            return True

    return False

async def show_photo_management(update: Update, context: ContextTypes.DEFAULT_TYPE):
    files = context.user_data.get('files', [])
    if not files:
        if update.message:
            await update.message.reply_text("📭 هنوز عکسی نفرستادی!")
            await log_chat(update, context)  # Log chat
        else:
            await update.callback_query.message.reply_text("📭 هنوز عکسی نفرستادی!")
            await log_chat(update, context)  # Log chat
        keyboard = [
            [KeyboardButton("🏁 اتمام ارسال تصاویر"), KeyboardButton("📋 مدیریت عکس‌ها")],
            [KeyboardButton("⬅️ بازگشت")]
        ]
        if update.message:
            await update.message.reply_text(
                "📸 برو عکس بفرست یا برگرد:",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            await log_chat(update, context)  # Log chat
        else:
            await update.callback_query.message.reply_text(
                "📸 برو عکس بفرست یا برگرد:",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            await log_chat(update, context)  # Log chat
        return

    # ارسال هر عکس با دکمه‌های مدیریت
    for i, file_id in enumerate(files):
        inline_keyboard = [
            [InlineKeyboardButton(f"🗑 حذف عکس {i+1}", callback_data=f"delete_photo_{i}"),
             InlineKeyboardButton(f"🔄 جایگزین عکس {i+1}", callback_data=f"replace_photo_{i}")]
        ]
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=file_id,
            caption=f"📸 عکس {i+1} از {len(files)}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard)
        )
    # دکمه برگشت به آپلود
    if update.message:
        await update.message.reply_text(
            "📸 کاری دیگه‌ای با عکس‌ها داری؟",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ برگشت به ارسال", callback_data="back_to_upload")]])
        )
        await log_chat(update, context)  # Log chat
    else:
        await update.callback_query.message.reply_text(
            "📸 کاری دیگه‌ای با عکس‌ها داری؟",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ برگشت به ارسال", callback_data="back_to_upload")]])
        )
        await log_chat(update, context)  # Log chat
    context.user_data['state'] = 'managing_photos'

async def upload_attachments(files, context):
    return await upload_files(files, context)