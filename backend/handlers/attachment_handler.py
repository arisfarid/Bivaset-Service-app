import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ContextTypes, ConversationHandler
from utils import upload_files, log_chat, BASE_URL
import logging
from keyboards import create_dynamic_keyboard, FILE_MANAGEMENT_MENU_KEYBOARD
from django.conf import settings  # اضافه کردن ایمپورت
import os  # اضافه کردن ایمپورت

logger = logging.getLogger(__name__)

START, REGISTER, ROLE, EMPLOYER_MENU, CATEGORY, SUBCATEGORY, DESCRIPTION, LOCATION_TYPE, LOCATION_INPUT, DETAILS, DETAILS_FILES, DETAILS_DATE, DETAILS_DEADLINE, DETAILS_BUDGET, DETAILS_QUANTITY, SUBMIT, VIEW_PROJECTS, PROJECT_ACTIONS = range(18)

async def handle_attachment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    current_state = context.user_data.get('state', DETAILS_FILES)
    telegram_id = str(update.effective_user.id)

    if update.message and update.message.video:
        await update.message.reply_text("❌ فقط عکس قبول می‌شه! ویدئو رو نمی‌تونم ثبت کنم.")
        await log_chat(update, context)
        return current_state

    if current_state == 'replacing_photo' and update.message and update.message.photo:
        new_photo = update.message.photo[-1].file_id
        index = context.user_data.get('replace_index')
        files = context.user_data.get('files', [])
        if 0 <= index < len(files):
            if new_photo in files:
                await update.message.reply_text("❌ این عکس قبلاً توی لیست هست!")
            else:
                old_photo = files[index]
                files[index] = new_photo
                logger.info(f"Replaced photo {old_photo} with {new_photo} at index {index}")
                await update.message.reply_text("🔄 عکس جایگزین شد!")
            await show_photo_management(update, context)
            context.user_data['state'] = DETAILS_FILES
        return DETAILS_FILES

    if update.message and update.message.photo:
        new_photo = update.message.photo[-1].file_id
        if 'files' not in context.user_data:
            context.user_data['files'] = []
        files = context.user_data['files']
        if new_photo not in files:
            remaining_slots = 5 - len(files)
            if remaining_slots <= 0:
                await update.message.reply_text(
                    "❌ لیست عکس‌ها پره! برای حذف یا جایگزینی، 'مدیریت عکس‌ها' رو بزن.",
                    reply_markup=FILE_MANAGEMENT_MENU_KEYBOARD
                )
            else:
                files.append(new_photo)
                logger.info(f"Photo received from {telegram_id}: {new_photo}")
                await update.message.reply_text(
                    f"📸 ۱ عکس جدید ثبت شد. الان {len(files)} از ۵ تاست.\n"
                    "برای ادامه یا مدیریت، گزینه‌ای انتخاب کن:",
                    reply_markup=FILE_MANAGEMENT_MENU_KEYBOARD
                )
        else:
            await update.message.reply_text(
                "❌ این عکس قبلاً ثبت شده! برای مدیریت، گزینه‌ای انتخاب کن:",
                reply_markup=FILE_MANAGEMENT_MENU_KEYBOARD
            )
        context.user_data['files'] = files
        await log_chat(update, context)
        return DETAILS_FILES

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
        await update.message.reply_text(
            "📭 هنوز عکسی نفرستادی!",
            reply_markup=FILE_MANAGEMENT_MENU_KEYBOARD
        )
        await log_chat(update, context)
        return

    keyboard = [
        [InlineInlineKeyboardButton(f"📸 عکس {i+1}", callback_data=f"view_photo_{i}"),
         InlineInlineKeyboardButton("✏️ ویرایش", callback_data=f"edit_photo_{i}")]
        for i in range(len(files))
    ]
    keyboard.append([InlineInlineKeyboardButton("⬅️ برگشت به ارسال", callback_data="back_to_upload")])
    await update.message.reply_text(
        "📸 عکس‌های ثبت‌شده:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    context.user_data['state'] = DETAILS_FILES
    await log_chat(update, context)

async def handle_photos_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Starting handle_photos_command")  # لاگ شروع
    
    try:
        # اگر از callback آمده
        if update.callback_query:
            project_id = context.user_data.get('current_project_id')
            chat_id = update.callback_query.message.chat_id
        # اگر از کامند مستقیم آمده
        else:
            command = update.message.text
            project_id = command.split("_")[2]
            chat_id = update.message.chat_id
            
        logger.info(f"Attempting to fetch photos for project {project_id} for chat {chat_id}")  # لاگ اطلاعات

        # دریافت اطلاعات فایل‌ها از API
        response = requests.get(f"{BASE_URL}projects/{project_id}/")
        logger.info(f"API Response: status={response.status_code}")  # لاگ پاسخ API
        
        if response.status_code == 200:
            project_data = response.json()
            project_files = project_data.get('files', [])
            logger.info(f"Found {len(project_files)} files for project")  # لاگ تعداد فایل‌ها
            
            if not project_files:
                logger.warning("No files found for project")  # لاگ عدم وجود فایل
                message = "❌ هیچ عکسی برای این درخواست یافت نشد."
                if update.callback_query:
                    await update.callback_query.message.reply_text(message)
                else:
                    await update.message.reply_text(message)
                return

            # آماده‌سازی لیست عکس‌ها برای ارسال به صورت آلبوم
            media_group = []
            base_url = BASE_URL.rstrip('/api').rstrip('/')
            
            for i, file_path in enumerate(project_files):
                full_url = f"{base_url}/media/{file_path}"
                logger.info(f"Processing file {i+1}: {full_url}")
                
                try:
                    photo_response = requests.get(full_url)
                    if photo_response.status_code == 200:
                        media_group.append(InputMediaPhoto(
                            media=photo_response.content,
                            caption="عکس اصلی" if i == 0 else ""  # تغییر کپشن فقط برای اولین عکس
                        ))
                        logger.info(f"Successfully added file {i+1} to media group")
                    else:
                        logger.error(f"Failed to download photo {i+1}. Status: {photo_response.status_code}")
                except Exception as e:
                    logger.error(f"Error processing photo {i+1}: {e}")

            if media_group:
                # ارسال عکس‌ها
                if update.callback_query:
                    await context.bot.send_media_group(chat_id=chat_id, media=media_group)
                else:
                    await update.message.reply_media_group(media=media_group)
                logger.info("Successfully sent all photos")  # لاگ موفقیت نهایی
            else:
                message = "❌ خطا در بارگیری عکس‌ها."
                if update.callback_query:
                    await update.callback_query.message.reply_text(message)
                else:
                    await update.message.reply_text(message)
                logger.error("No photos were successfully processed")  # لاگ خطای کلی
        else:
            logger.error(f"Failed to fetch project data. Status: {response.status_code}")  # لاگ خطای API
            message = "❌ خطا در دریافت اطلاعات پروژه."
            if update.callback_query:
                await update.callback_query.message.reply_text(message)
            else:
                await update.message.reply_text(message)
                
    except Exception as e:
        logger.error(f"Error in handle_photos_command: {e}")  # لاگ خطای کلی
        message = "❌ خطا در پردازش درخواست."
        if update.callback_query:
            await update.callback_query.message.reply_text(message)
        else:
            await update.message.reply_text(message)