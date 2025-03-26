import requests
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from utils import upload_files, log_chat, BASE_URL
import logging
from handlers.project_details_handler import create_dynamic_keyboard
from keyboards import FILE_MANAGEMENT_MENU_KEYBOARD

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
        [InlineKeyboardButton(f"📸 عکس {i+1}", callback_data=f"view_photo_{i}"),
         InlineKeyboardButton("✏️ ویرایش", callback_data=f"edit_photo_{i}")]
        for i in range(len(files))
    ]
    keyboard.append([InlineKeyboardButton("⬅️ برگشت به ارسال", callback_data="back_to_upload")])
    await update.message.reply_text(
        "📸 عکس‌های ثبت‌شده:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    context.user_data['state'] = DETAILS_FILES
    await log_chat(update, context)

async def upload_attachments(files, context):
    return await upload_files(files, context)

async def handle_photo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command = update.message.text
    logger.info(f"Received command: {command}")
    if command.startswith("/view_photo_"):
        try:
            photo_index = int(command.split("_")[2])
            uploaded_files = context.user_data.get('uploaded_files', [])
            logger.info(f"Uploaded files: {uploaded_files}")
            if 0 <= photo_index < len(uploaded_files):
                photo_url = uploaded_files[photo_index]
                logger.info(f"Sending photo: {photo_url}")
                await update.message.reply_photo(photo=f"{settings.MEDIA_URL}{photo_url}", caption=f"📷 عکس {photo_index + 1}")
            else:
                logger.warning(f"Photo index {photo_index} out of range.")
                await update.message.reply_text("❌ عکس مورد نظر یافت نشد.")
        except (IndexError, ValueError) as e:
            logger.error(f"Error processing command {command}: {e}")
            await update.message.reply_text("❌ دستور نامعتبر است.")

async def upload_files(file_ids, context):
    uploaded_urls = []
    project_id = context.user_data.get('project_id')  # دریافت project_id از context
    for file_id in file_ids:
        try:
            file = await context.bot.get_file(file_id)
            file_data = await file.download_as_bytearray()
            files = {'file': ('image.jpg', file_data, 'image/jpeg')}
            data = {'project_id': project_id}  # ارسال project_id
            response = requests.post(f"{BASE_URL.rstrip('/api/')}/upload/", files=files, data=data)
            logger.info(f"Upload response: {response.status_code}, {response.text}")  # اضافه کردن لاگ
            if response.status_code == 201:
                file_url = response.json().get('file_url')
                uploaded_urls.append(file_url)
            else:
                uploaded_urls.append(None)
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            uploaded_urls.append(None)
    return uploaded_urls