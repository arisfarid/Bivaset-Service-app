# submission_handler.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from utils import generate_title, convert_deadline_to_date, log_chat, BASE_URL
import requests
import logging
from handlers.start_handler import start
from handlers.attachment_handler import upload_attachments

logger = logging.getLogger(__name__)

START, REGISTER, ROLE, EMPLOYER_MENU, CATEGORY, SUBCATEGORY, DESCRIPTION, LOCATION_TYPE, LOCATION_INPUT, DETAILS, DETAILS_FILES, DETAILS_DATE, DETAILS_DEADLINE, DETAILS_BUDGET, DETAILS_QUANTITY, SUBMIT, VIEW_PROJECTS, PROJECT_ACTIONS = range(18)

async def submit_project(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text != "✅ ثبت درخواست":
        return DETAILS

    location = context.user_data.get('location')
    location_data = [location['longitude'], location['latitude']] if location else None

    data = {
        'title': generate_title(context),
        'description': context.user_data.get('description', ''),
        'category': context.user_data.get('category_id', ''),
        'service_location': context.user_data.get('service_location', ''),
        'location': location_data,
        'files': await upload_attachments(context.user_data.get('files', []), context),
        'user_telegram_id': str(update.effective_user.id)
    }
    if context.user_data.get('budget'):
        data['budget'] = context.user_data['budget']
    if context.user_data.get('need_date'):
        data['start_date'] = context.user_data['need_date']
    if context.user_data.get('deadline'):
        data['deadline_date'] = convert_deadline_to_date(context.user_data['deadline'])

    logger.info(f"Sending project data to API: {data}")
    await log_chat(update, context)
    try:
        response = requests.post(f"{BASE_URL}projects/", json=data)
        if response.status_code == 201:
            project = response.json()
            project_id = project.get('id', 'نامشخص')
            files = context.user_data.get('files', [])
            message_lines = [
                f"🎉 درخواست شما با کد {project_id} ثبت شد!",
                f"📌 دسته‌بندی: {context.user_data.get('categories', {}).get(context.user_data.get('category_id', ''), {}).get('name', 'نامشخص')}",
                f"📝 توضیحات: {context.user_data.get('description', '')}"
            ]
            if context.user_data.get('need_date'):
                message_lines.append(f"📅 تاریخ نیاز: {context.user_data['need_date']}")
            if context.user_data.get('deadline'):
                message_lines.append(f"⏳ مهلت انجام: {context.user_data['deadline']} روز")
            if context.user_data.get('budget'):
                message_lines.append(f"💰 بودجه: {context.user_data['budget']} تومان")
            if context.user_data.get('quantity'):
                message_lines.append(f"📏 مقدار و واحد: {context.user_data['quantity']}")
            if location_data:
                message_lines.append(f"📍 لوکیشن: https://maps.google.com/maps?q={location['latitude']},{location['longitude']}")
            if len(files) > 1:
                message_lines.append("📸 لینک عکس‌ها:\n" + "\n".join([f"- {file}" for file in files[1:]]))
            message = "\n".join(message_lines)

            inline_keyboard = [
                [InlineKeyboardButton("✏️ ویرایش", callback_data=f"edit_{project_id}"),
                 InlineKeyboardButton("⛔ بستن", callback_data=f"close_{project_id}")],
                [InlineKeyboardButton("🗑 حذف", callback_data=f"delete_{project_id}"),
                 InlineKeyboardButton("⏰ تمدید", callback_data=f"extend_{project_id}")],
                [InlineKeyboardButton("💡 پیشنهادها", callback_data=f"offers_{project_id}")]
            ]
            if files:
                await update.message.reply_photo(
                    photo=files[0],
                    caption=message,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard)
                )
            else:
                await update.message.reply_text(
                    message,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard)
                )
        else:
            logger.error(f"API error: {response.text}")
            await update.message.reply_text(f"❌ خطا در ثبت درخواست: {response.text[:50]}...")
    except requests.exceptions.ConnectionError:
        logger.error("Connection error while submitting project")
        await update.message.reply_text("❌ خطا: سرور بک‌اند در دسترس نیست.")
    except Exception as e:
        logger.error(f"Error submitting project: {e}")
        await update.message.reply_text("❌ خطا در ثبت درخواست.")
    context.user_data.clear()
    await start(update, context)
    return ROLE