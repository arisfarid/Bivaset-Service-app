from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from utils import upload_files, log_chat
import logging
from handlers.project_details_handler import create_dynamic_keyboard
from keyboards import FILE_MANAGEMENT_MENU_KEYBOARD  # اضافه شده

logger = logging.getLogger(__name__)

START, REGISTER, ROLE, EMPLOYER_MENU, CATEGORY, SUBCATEGORY, DESCRIPTION, LOCATION_TYPE, LOCATION_INPUT, DETAILS, DETAILS_FILES, DETAILS_DATE, DETAILS_DEADLINE, DETAILS_BUDGET, DETAILS_QUANTITY, SUBMIT, VIEW_PROJECTS, PROJECT_ACTIONS = range(18)

async def handle_attachment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    current_state = context.user_data.get('state', DETAILS_FILES)
    telegram_id = str(update.effective_user.id)
    current_files = context.user_data.get('files', [])

    if current_state == 'replacing_photo' and update.message.photo:
        new_photo = update.message.photo[-1].file_id
        index = context.user_data.get('replace_index')
        if 0 <= index < len(current_files):
            if new_photo in current_files:
                await update.message.reply_text("❌ این عکس قبلاً توی لیست هست!")
                await log_chat(update, context)
                await show_photo_management(update, context)
                return DETAILS_FILES
            old_photo = current_files[index]
            current_files[index] = new_photo
            logger.info(f"Replaced photo {old_photo} with {new_photo} at index {index}")
            await update.message.reply_text("🔄 عکس جایگزین شد!")
            await log_chat(update, context)
            await show_photo_management(update, context)
            context.user_data['state'] = DETAILS_FILES
        return DETAILS_FILES

    if update.message and update.message.photo:
        new_photos = [update.message.photo[-1].file_id]
        if 'files' not in context.user_data:
            context.user_data['files'] = []

        current_files = context.user_data['files']
        added_photos = [photo for photo in new_photos if photo not in current_files]
        remaining_slots = 5 - len(current_files)
        
        if current_state == DETAILS_FILES:
            if remaining_slots <= 0:
                await update.message.reply_text(
                    "❌ لیست عکس‌ها پره! برای حذف یا جایگزینی، 'مدیریت عکس‌ها' رو بزن."
                )
                await log_chat(update, context)
            else:
                photos_to_add = added_photos[:remaining_slots]
                current_files.extend(photos_to_add)
                logger.info(f"Photos received from {telegram_id}: {photos_to_add}")
                await update.message.reply_text(
                    f"📸 {len(photos_to_add)} عکس ثبت شد. الان {len(current_files)} از ۵ تاست.\n"
                    "برای ادامه یا مدیریت، گزینه‌ای انتخاب کن:"
                )
                await log_chat(update, context)
            
            await update.message.reply_text(
                "📸 عکس دیگه‌ای داری؟ اگه نه، 'اتمام ارسال تصاویر' رو بزن:",
                reply_markup=FILE_MANAGEMENT_MENU_KEYBOARD  # استفاده از FILE_MANAGEMENT_MENU_KEYBOARD
            )
            return DETAILS_FILES
        else:
            await update.message.reply_text("📸 الان نمی‌تونی عکس بفرستی! اول یه درخواست شروع کن.")
            await log_chat(update, context)
            context.user_data.pop('files', None)
            return current_state

    if update.message and update.message.video:
        await update.message.reply_text("❌ فقط عکس قبول می‌شه! ویدئو رو نمی‌تونم ثبت کنم.")
        await log_chat(update, context)
        return current_state

    text = update.message.text if update.message else None
    if current_state in [DETAILS_FILES, 'managing_photos']:
        if text == "🏁 اتمام ارسال تصاویر":
            context.user_data['state'] = DETAILS
            await update.message.reply_text(
                "📋 جزئیات درخواست:",
                reply_markup=create_dynamic_keyboard(context)
            )
            await log_chat(update, context)
            return DETAILS
        elif text == "📋 مدیریت عکس‌ها":
            await show_photo_management(update, context)
            return DETAILS_FILES
        elif text == "⬅️ بازگشت":
            context.user_data['state'] = DETAILS
            await update.message.reply_text(
                "📋 جزئیات درخواست:",
                reply_markup=create_dynamic_keyboard(context)
            )
            await log_chat(update, context)
            return DETAILS

    return current_state

async def show_photo_management(update: Update, context: ContextTypes.DEFAULT_TYPE):
    files = context.user_data.get('files', [])
    if not files:
        await update.message.reply_text("📭 هنوز عکسی نفرستادی!")
        await log_chat(update, context)
        await update.message.reply_text(
            "📸 برو عکس بفرست یا برگرد:",
            reply_markup=FILE_MANAGEMENT_MENU_KEYBOARD  # استفاده از FILE_MANAGEMENT_MENU_KEYBOARD
        )
        await log_chat(update, context)
        return

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
    await update.message.reply_text(
        "📸 کاری دیگه‌ای با عکس‌ها داری؟",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ برگشت به ارسال", callback_data="back_to_upload")]])
    )
    await log_chat(update, context)
    context.user_data['state'] = DETAILS_FILES

async def upload_attachments(files, context):
    return await upload_files(files, context)