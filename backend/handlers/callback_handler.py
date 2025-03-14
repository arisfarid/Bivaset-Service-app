from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging
from .start_handler import start
from .category_handler import handle_category_callback
from .edit_handler import handle_edit_callback
from .view_handler import handle_view_callback

logger = logging.getLogger(__name__)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    logger.info(f"Callback data received: {data}")

    if data == 'restart':
        logger.info(f"Restart requested by {update.effective_user.id}")
        context.user_data.clear()
        await start(update, context)
    elif data == 'back':
        current_step = context.user_data.get('current_step', 'start')
        if current_step == 'select_category':
            await start(update, context)  # بازگشت به منوی نقش
        elif current_step == 'select_subcategory':
            await show_categories(update, context)  # بازگشت به دسته‌بندی‌ها
        elif current_step in ['description', 'service_location', 'location', 'details']:
            await show_employer_menu(update, context)  # بازگشت به منوی کارفرما
        else:
            await start(update, context)
    elif data.isdigit():  # دسته‌بندی
        await handle_category_callback(update, context)
    elif data in ['new_project', 'view_projects']:
        logger.info(f"Redirecting {data} to message_handler")
    elif data.startswith(('edit_', 'delete_', 'close_', 'extend_', 'offers_')):
        await handle_edit_callback(update, context)
    elif data == 'select_location':
        await query.message.edit_text(
            "📍 لطفاً لوکیشن رو با استفاده از دکمه پیوست تلگرام (📎) بفرستید:\n"
            "1. روی 📎 بزنید.\n2. گزینه 'Location' رو انتخاب کنید.\n3. لوکیشن رو بفرستید."
        )
        context.user_data['current_step'] = 'location'
    else:
        await handle_view_callback(update, context)

async def show_employer_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📋 درخواست خدمات جدید", callback_data='new_project')],
        [InlineKeyboardButton("👀 مشاهده درخواست‌ها", callback_data='view_projects')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.edit_text(
        "🎉 عالیه! می‌خوای خدمات جدید درخواست کنی یا پیشنهادات رو ببینی؟",
        reply_markup=reply_markup
    )