from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import logging
from handlers.start_handler import start
from handlers.category_handler import handle_category_callback
from handlers.edit_handler import handle_edit_callback
from handlers.view_handler import handle_view_callback
from handlers.attachment_handler import show_photo_management
from utils import log_chat
from keyboards import EMPLOYER_INLINE_MENU_KEYBOARD, FILE_MANAGEMENT_MENU_KEYBOARD, RESTART_INLINE_MENU_KEYBOARD, BACK_INLINE_MENU_KEYBOARD

logger = logging.getLogger(__name__)

START, REGISTER, ROLE, EMPLOYER_MENU, CATEGORY, SUBCATEGORY, DESCRIPTION, LOCATION_TYPE, LOCATION_INPUT, DETAILS, DETAILS_FILES, DETAILS_DATE, DETAILS_DEADLINE, DETAILS_BUDGET, DETAILS_QUANTITY, SUBMIT, VIEW_PROJECTS, PROJECT_ACTIONS = range(18)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data
    logger.info(f"Callback data received: {data}")
    await log_chat(update, context)

    try:
        if data.startswith('delete_photo_'):
            index = int(data.split('_')[2])
            files = context.user_data.get('files', [])
            if 0 <= index < len(files):
                deleted_file = files.pop(index)
                logger.info(f"Deleted photo {deleted_file} at index {index}")
                # ویرایش پیام فعلی به جای ارسال پیام جدید
                if files:
                    await query.edit_message_text(
                        "🗑 عکس حذف شد! دوباره مدیریت کن یا ادامه بده.",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton(f"🗑 حذف عکس {i+1}", callback_data=f"delete_photo_{i}")]
                            for i in range(len(files))
                        ] + [[InlineKeyboardButton("➡️ ادامه", callback_data="continue")]])
                    )
                    await show_photo_management(update, context)
                else:
                    await query.edit_message_text(
                        "🗑 همه عکس‌ها حذف شدن! حالا چی؟",
                        reply_markup=FILE_MANAGEMENT_MENU_KEYBOARD
                    )
            else:
                await query.edit_message_text("❌ عکس مورد نظر پیدا نشد!")
            return DETAILS_FILES

        elif data.startswith('replace_photo_'):
            index = int(data.split('_')[2])
            context.user_data['replace_index'] = index
            await query.message.reply_text("📸 لطفاً عکس جدید رو بفرست تا جایگزین بشه:")
            context.user_data['state'] = 'replacing_photo'
            return DETAILS_FILES

        elif data == 'back_to_upload':
            await query.message.reply_text(
                "📸 عکس دیگه‌ای داری؟",
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
        await update.effective_chat.send_message(
            "❌ یه مشکل پیش اومد! بریم از اول شروع کنیم؟",
            reply_markup=RESTART_INLINE_MENU_KEYBOARD
        )
        context.user_data['state'] = ROLE
        return ROLE

async def show_employer_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.edit_text(
        "🎉 عالیه! می‌خوای خدمات جدید درخواست کنی یا پیشنهادات رو ببینی؟",
        reply_markup=EMPLOYER_INLINE_MENU_KEYBOARD
    )
    context.user_data['state'] = EMPLOYER_MENU

async def handle_attachment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    current_state = context.user_data.get('state')
    if current_state == 'replacing_photo' and update.message and update.message.photo:
        new_photo = update.message.photo[-1].file_id
        index = context.user_data.get('replace_index')
        if 'files' in context.user_data and 0 <= index < len(context.user_data['files']):
            old_photo = context.user_data['files'][index]
            context.user_data['files'][index] = new_photo
            logger.info(f"Replaced photo {old_photo} with {new_photo} at index {index}")
            await update.message.reply_text("🔄 عکس جایگزین شد!")
            await show_photo_management(update, context)
        context.user_data['state'] = DETAILS_FILES
        return DETAILS_FILES
    return current_state