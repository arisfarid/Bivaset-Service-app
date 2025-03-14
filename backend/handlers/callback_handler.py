from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
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
        context.user_data.clear()
        await start(update, context)
    elif data == 'back':
        state = context.user_data.get('state', 'start')
        if state == 'new_project_category':
            context.user_data['state'] = None
            await start(update, context)
        elif state == 'new_project_subcategory':
            context.user_data['state'] = 'new_project_category'
            categories = context.user_data.get('categories', {})
            root_cats = [cat_id for cat_id, cat in categories.items() if cat['parent'] is None]
            keyboard = [[KeyboardButton(categories[cat_id]['name'])] for cat_id in root_cats] + [[KeyboardButton("⬅️ بازگشت")]]
            await query.message.edit_text(
                f"🌟 دسته‌بندی خدماتت رو انتخاب کن:",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
        elif state in ['new_project_desc', 'new_project_location', 'new_project_location_input', 'new_project_details']:
            await show_employer_menu(update, context)
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