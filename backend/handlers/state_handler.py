from telegram import Update
from telegram.ext import (
    CommandHandler, MessageHandler, CallbackQueryHandler, 
    ConversationHandler, filters, ContextTypes
)
import logging
from handlers.start_handler import start, handle_contact, handle_role, cancel
from handlers.message_handler import handle_message
from handlers.category_handler import handle_category_selection
from handlers.location_handler import handle_location
from handlers.attachment_handler import handle_attachment, handle_photos_command
from handlers.project_details_handler import handle_project_details
from handlers.view_handler import handle_view_projects
from handlers.callback_handler import handle_callback

logger = logging.getLogger(__name__)

# تعریف state ها
START, REGISTER, ROLE, EMPLOYER_MENU, CATEGORY, SUBCATEGORY, DESCRIPTION, \
LOCATION_TYPE, LOCATION_INPUT, DETAILS, DETAILS_FILES, DETAILS_DATE, \
DETAILS_DEADLINE, DETAILS_BUDGET, DETAILS_QUANTITY, SUBMIT, VIEW_PROJECTS, \
PROJECT_ACTIONS, CHANGE_PHONE, VERIFY_CODE = range(20)

from handlers.submission_handler import submit_project
from handlers.phone_handler import change_phone, handle_new_phone, verify_new_phone

def get_conversation_handler() -> ConversationHandler:
    """تنظیم و برگرداندن ConversationHandler اصلی"""
    return ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("change_phone", change_phone)
        ],
        states={
            ROLE: [CallbackQueryHandler(handle_role)],
            EMPLOYER_MENU: [CallbackQueryHandler(handle_message)],
            CATEGORY: [CallbackQueryHandler(handle_category_selection)],
            SUBCATEGORY: [CallbackQueryHandler(handle_category_selection)],
            REGISTER: [
                MessageHandler(filters.CONTACT, handle_contact),  # اضافه کردن هندلر contact
                CommandHandler("start", start)
            ],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_project_details)],
            LOCATION_TYPE: [CallbackQueryHandler(handle_location)],
            LOCATION_INPUT: [
                MessageHandler(filters.LOCATION, handle_location),
                CallbackQueryHandler(handle_location)
            ],
            DETAILS: [CallbackQueryHandler(handle_project_details)],
            DETAILS_FILES: [CallbackQueryHandler(handle_attachment)],
            CHANGE_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_phone)],
            VERIFY_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, verify_new_phone)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(handle_callback, pattern="^cancel$")
        ],
        name="main_conversation",
        persistent=True,
        per_chat=True,
        per_user=True,
        per_message=False  # Changed to False to allow different handler types
    )

async def log_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لاگ کردن state فعلی"""
    current_state = context.user_data.get('state', START)
    logger.info(f"Processing message for user {update.effective_user.id}, current state: {current_state}")
    return current_state

async def handle_error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """مدیریت خطاهای کلی"""
    logger.error(f"Exception while handling an update: {context.error}")
    
    try:
        if context and context.user_data:
            context.user_data.clear()
            if update.effective_user:
                await context.application.persistence.update_user_data(
                    user_id=update.effective_user.id, 
                    data=context.user_data
                )
        
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ خطایی رخ داد. لطفاً دوباره شروع کنید با /start"
            )
            
    except Exception as e:
        logger.error(f"Error in error handler: {e}")