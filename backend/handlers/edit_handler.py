from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
import requests
import logging
from utils import BASE_URL, log_chat

logger = logging.getLogger(__name__)

START, REGISTER, ROLE, EMPLOYER_MENU, CATEGORY, SUBCATEGORY, DESCRIPTION, LOCATION_TYPE, LOCATION_INPUT, DETAILS, DETAILS_FILES, DETAILS_DATE, DETAILS_DEADLINE, DETAILS_BUDGET, DETAILS_QUANTITY, SUBMIT, VIEW_PROJECTS, PROJECT_ACTIONS = range(18)

async def handle_edit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    data = query.data
    await log_chat(update, context)

    if data.startswith(('edit_', 'delete_', 'close_', 'extend_', 'offers_')):
        action, project_id = data.split('_', 1)
        if action == 'edit':
            await query.edit_message_text("✏️ ویرایش پروژه هنوز پیاده‌سازی نشده!")
        elif action == 'delete':
            await query.edit_message_text("🗑 حذف پروژه هنوز پیاده‌سازی نشده!")
        elif action == 'close':
            await query.edit_message_text("⛔ بستن پروژه هنوز پیاده‌سازی نشده!")
        elif action == 'extend':
            await query.edit_message_text("⏰ تمدید پروژه هنوز پیاده‌سازی نشده!")
        elif action == 'offers':
            if query.message.text:
                await query.edit_message_text("💡 مشاهده پیشنهادها هنوز پیاده‌سازی نشده!")
            else:
                await query.answer("💡 مشاهده پیشنهادها هنوز پیاده‌سازی نشده!", show_alert=True)
        return PROJECT_ACTIONS
    return context.user_data.get('state', PROJECT_ACTIONS)