from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
import logging
from .start_handler import start
from .category_handler import handle_category_callback
from .edit_handler import handle_edit_callback
from .view_handler import handle_view_callback
from .attachment_handler import show_photo_management

logger = logging.getLogger(__name__)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    logger.info(f"Callback data received: {data}")

    if data.startswith('delete_photo_'):
        index = int(data.split('_')[2])
        files = context.user_data.get('files', [])
        if 0 <= index < len(files):
            deleted_file = files.pop(index)
            logger.info(f"Deleted photo {deleted_file} at index {index}")
            await query.edit_message_text("🗑 عکس حذف شد! دوباره مدیریت کن یا ادامه بده.")
            await show_photo_management(update, context)
        return
    elif data.startswith('replace_photo_'):
        index = int(data.split('_')[2])
        context.user_data['replace_index'] = index
        context.user_data['state'] = 'replacing_photo'
        await query.edit_message_text("📸 لطفاً عکس جدید رو بفرست تا جایگزین بشه:")
        return
    elif data == 'back_to_upload':
        context.user_data['state'] = 'new_project_details_files'
        keyboard = [
            [KeyboardButton("🏁 اتمام ارسال تصاویر"), KeyboardButton("📋 مدیریت عکس‌ها")],
            [KeyboardButton("⬅️ بازگشت")]
        ]
        await query.edit_message_text(
            "📸 عکس دیگه‌ای داری؟",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return
    elif data == 'restart':
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

async def handle_attachment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get('state')
    if state == 'replacing_photo' and update.message and update.message.photo:
        new_photo = update.message.photo[-1].file_id
        index = context.user_data.get('replace_index')
        if 'files' in context.user_data and 0 <= index < len(context.user_data['files']):
            old_photo = context.user_data['files'][index]
            context.user_data['files'][index] = new_photo
            logger.info(f"Replaced photo {old_photo} with {new_photo} at index {index}")
            await update.message.reply_text("🔄 عکس جایگزین شد!")
            await show_photo_management(update, context)
        context.user_data['state'] = 'managing_photos'
        return True