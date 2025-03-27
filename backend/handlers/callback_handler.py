from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import logging
from handlers.start_handler import start
from handlers.category_handler import handle_category_callback
from handlers.edit_handler import handle_edit_callback
from handlers.view_handler import handle_view_callback
from handlers.attachment_handler import show_photo_management, handle_photos_command
from utils import log_chat
from keyboards import EMPLOYER_INLINE_MENU_KEYBOARD, FILE_MANAGEMENT_MENU_KEYBOARD, RESTART_INLINE_MENU_KEYBOARD, BACK_INLINE_MENU_KEYBOARD

logger = logging.getLogger(__name__)

START, REGISTER, ROLE, EMPLOYER_MENU, CATEGORY, SUBCATEGORY, DESCRIPTION, LOCATION_TYPE, LOCATION_INPUT, DETAILS, DETAILS_FILES, DETAILS_DATE, DETAILS_DEADLINE, DETAILS_BUDGET, DETAILS_QUANTITY, SUBMIT, VIEW_PROJECTS, PROJECT_ACTIONS = range(18)

async def send_photo_with_caption(context, chat_id, photo, caption, reply_markup=None):
    await context.bot.send_photo(
        chat_id=chat_id,
        photo=photo,
        caption=caption,
        reply_markup=reply_markup
    )

async def send_message_with_keyboard(context, chat_id, text, reply_markup):
    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=reply_markup
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    data = query.data

    if data.startswith('view_photos_'):
        project_id = data.split('_')[2]
        # اجرای دستور view_photos
        context.user_data['current_project_id'] = project_id
        await handle_photos_command(update, context)
        await query.answer()
        return PROJECT_ACTIONS

    await query.answer()
    data = query.data
    logger.info(f"Callback data received: {data}")
    await log_chat(update, context)

    chat_id = update.effective_chat.id

    try:
        if data.startswith('view_photo_'):
            index = int(data.split('_')[2])
            files = context.user_data.get('files', [])
            if 0 <= index < len(files):
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=files[index],
                    caption=f"📸 عکس {index+1} از {len(files)}"
                )
            return DETAILS_FILES

        elif data.startswith('edit_photo_'):
            index = int(data.split('_')[2])
            files = context.user_data.get('files', [])
            if 0 <= index < len(files):
                keyboard = [
                    [InlineKeyboardButton("🗑 حذف", callback_data=f"delete_photo_{index}"),
                     InlineKeyboardButton("🔄 جایگزینی", callback_data=f"replace_photo_{index}")],
                    [InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_management")]
                ]
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=files[index],
                    caption=f"📸 عکس {index+1} از {len(files)}",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            return DETAILS_FILES

        elif data.startswith('delete_photo_'):
            index = int(data.split('_')[2])
            files = context.user_data.get('files', [])
            if 0 <= index < len(files):
                deleted_file = files.pop(index)
                logger.info(f"Deleted photo {deleted_file} at index {index}")
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="🗑 عکس حذف شد! دوباره مدیریت کن یا ادامه بده.",
                    reply_markup=FILE_MANAGEMENT_MENU_KEYBOARD
                )
                await show_photo_management(update, context)
            else:
                logger.warning(f"Attempted to delete non-existent photo at index {index}")
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="❌ عکس مورد نظر پیدا نشد!",
                    reply_markup=FILE_MANAGEMENT_MENU_KEYBOARD
                )
            return DETAILS_FILES

        elif data.startswith('replace_photo_'):
            index = int(data.split('_')[2])
            context.user_data['replace_index'] = index
            await context.bot.send_message(
                chat_id=chat_id,
                text="📸 لطفاً عکس جدید رو بفرست تا جایگزین بشه:",
                reply_markup=None
            )
            context.user_data['state'] = 'replacing_photo'
            return DETAILS_FILES

        elif data == 'back_to_management':
            await show_photo_management(update, context)
            return DETAILS_FILES

        elif data == 'back_to_upload':
            await context.bot.send_message(
                chat_id=chat_id,
                text="📸 عکس دیگه‌ای داری؟",
                reply_markup=FILE_MANAGEMENT_MENU_KEYBOARD
            )
            context.user_data['state'] = DETAILS_FILES
            return DETAILS_FILES

        elif data == 'restart':
            context.user_data.clear()
            await query.message.delete()
            await start(update, context)
            return ROLE

        elif data == 'back':
            current_state = context.user_data.get('state', ROLE)
            if current_state == CATEGORY:
                context.user_data['state'] = ROLE
                await start(update, context)
                return ROLE
            elif current_state == SUBCATEGORY:
                context.user_data['state'] = CATEGORY
                categories = context.user_data.get('categories', {})
                root_cats = [cat_id for cat_id, cat in categories.items() if cat['parent'] is None]
                keyboard = [[KeyboardButton(categories[cat_id]['name'])] for cat_id in root_cats] + [[KeyboardButton("⬅️ بازگشت")]]
                await query.message.edit_text(
                    "🌟 دسته‌بندی خدماتت رو انتخاب کن:",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
                return CATEGORY
            elif current_state in [DESCRIPTION, LOCATION_TYPE, LOCATION_INPUT, DETAILS]:
                await show_employer_menu(update, context)
                return EMPLOYER_MENU
            else:
                await start(update, context)
                return ROLE

        elif data.isdigit():
            await handle_category_callback(update, context)
            return SUBMIT

        elif data in ['new_project', 'view_projects']:
            logger.info(f"Redirecting {data} to message_handler")
            return EMPLOYER_MENU

        elif data.startswith(('edit_', 'delete_', 'close_', 'extend_', 'offers_')):
            await handle_edit_callback(update, context)
            return PROJECT_ACTIONS

        elif data == 'select_location':
            await query.message.edit_text(
                "📍 لطفاً لوکیشن رو با استفاده از دکمه پیوست تلگرام (📎) بفرستید:\n"
                "1. روی 📎 بزنید.\n2. گزینه 'Location' رو انتخاب کنید.\n3. لوکیشن رو بفرستید."
            )
            context.user_data['state'] = LOCATION_INPUT
            return LOCATION_INPUT

        else:
            await handle_view_callback(update, context)
            return PROJECT_ACTIONS

    except Exception as e:
        logger.error(f"Unexpected error in callback handler: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ یه مشکل پیش اومد! لطفاً دوباره تلاش کن.",
            reply_markup=FILE_MANAGEMENT_MENU_KEYBOARD
        )
        await show_photo_management(update, context)
        return DETAILS_FILES

async def show_employer_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="🎉 عالیه! می‌خوای خدمات جدید درخواست کنی یا پیشنهادات رو ببینی؟",
        reply_markup=EMPLOYER_INLINE_MENU_KEYBOARD
    )
    context.user_data['state'] = EMPLOYER_MENU