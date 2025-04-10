from telegram import Update
from telegram.ext import (
    CommandHandler, MessageHandler, CallbackQueryHandler, 
    ConversationHandler, filters, ContextTypes
)
import logging
from handlers.start_handler import start, handle_role, cancel
from handlers.phone_handler import handle_contact
from handlers.message_handler import handle_message
from handlers.category_handler import handle_category_selection
from handlers.location_handler import handle_location
from handlers.attachment_handler import handle_attachment, handle_photos_command
from handlers.project_details_handler import handle_project_details
from handlers.view_handler import handle_view_projects
from handlers.callback_handler import handle_callback
from keyboards import REGISTER_MENU_KEYBOARD

logger = logging.getLogger(__name__)

# تعریف state ها
START, REGISTER, ROLE, EMPLOYER_MENU, CATEGORY, SUBCATEGORY, DESCRIPTION, \
LOCATION_TYPE, LOCATION_INPUT, DETAILS, DETAILS_FILES, DETAILS_DATE, \
DETAILS_DEADLINE, DETAILS_BUDGET, DETAILS_QUANTITY, SUBMIT, VIEW_PROJECTS, \
PROJECT_ACTIONS, CHANGE_PHONE, VERIFY_CODE = range(20)

from handlers.submission_handler import submit_project
from handlers.phone_handler import change_phone, handle_new_phone, verify_new_phone

async def handle_non_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"=== Entering handle_non_contact - User: {update.effective_user.id} ===")
    logger.info(f"Message type: {type(update.message)}")
    logger.info(f"Message text: {update.message.text if update.message else 'None'}")
    logger.info(f"Current state: {context.user_data.get('state')}")
    logger.info("=== Non-contact message received in REGISTER state ===")
    current_state = context.user_data.get('state')
    logger.info(f"Current state: {current_state}")
    
    if current_state != REGISTER:
        return current_state
        
    message = update.callback_query.message if update.callback_query else update.message
    if not message:
        logger.error("No message object found in update")
        return REGISTER
        
    logger.info(f"User {update.effective_user.id} sent non-contact message in REGISTER state")
    await message.reply_text(
        "⚠️ برای استفاده از ربات، باید شماره تلفن خود را به اشتراک بگذارید.\n"
        "لطفاً از دکمه زیر استفاده کنید:",
        reply_markup=REGISTER_MENU_KEYBOARD
    )
    context.user_data['state'] = REGISTER
    return REGISTER

def get_conversation_handler() -> ConversationHandler:
    """ایجاد مدیریت کننده مکالمه با ترتیب جدید مراحل"""
    logger.info("=== Initializing ConversationHandler ===")
    return ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            REGISTER: [
                MessageHandler(filters.CONTACT, handle_contact),
                MessageHandler(~filters.CONTACT & ~filters.COMMAND, handle_non_contact),
                CommandHandler("start", start),
                CallbackQueryHandler(handle_callback)
            ],
            ROLE: [
                MessageHandler(filters.TEXT, handle_role),
                CallbackQueryHandler(handle_callback)
            ],
            EMPLOYER_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message),
                CallbackQueryHandler(handle_callback)
            ],
            CATEGORY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_category_selection),
                CallbackQueryHandler(handle_category_selection)
            ],
            SUBCATEGORY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_category_selection),
                CallbackQueryHandler(handle_category_selection)
            ],
            LOCATION_TYPE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_location),
                CallbackQueryHandler(handle_location)
            ],
            LOCATION_INPUT: [
                MessageHandler(filters.LOCATION, handle_location),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_location),
                CallbackQueryHandler(handle_location)
            ],
            DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_project_details),
                CallbackQueryHandler(handle_project_details)
            ],
            DETAILS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_project_details),
                CallbackQueryHandler(handle_project_details)
            ],
            DETAILS_FILES: [
                MessageHandler(filters.PHOTO, handle_attachment),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_attachment),
                CallbackQueryHandler(handle_attachment)
            ],
            CHANGE_PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_phone)
            ],
            VERIFY_CODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, verify_new_phone)
            ],
            VIEW_PROJECTS: [
                CallbackQueryHandler(handle_view_projects)
            ],
            PROJECT_ACTIONS: [
                CallbackQueryHandler(handle_view_projects)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(filters.ALL, handle_non_contact)
        ],
        name="main_conversation",
        persistent=True,
        allow_reentry=True
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