from telegram import Update
from telegram.ext import ContextTypes
import logging
from .start_handler import start
from .category_handler import handle_category_callback
from .edit_handler import handle_edit_callback
from .view_handler import handle_view_callback

logger = logging.getLogger(__name__)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    logger.info(f"Callback data received: {data}")
    await query.answer()

    if data == 'restart':
        logger.info(f"Restart requested by {query.from_user.id}")
        await start(update, context)
    elif data.isdigit():  # دسته‌بندی
        await handle_category_callback(update, context)
    elif data in ['new_project', 'view_projects']:
        logger.info(f"Redirecting {data} to message_handler")
    elif data.startswith(('edit_', 'delete_', 'close_', 'extend_', 'offers_')):
        await handle_edit_callback(update, context)
    else:
        await handle_view_callback(update, context)