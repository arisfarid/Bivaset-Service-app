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

def get_conversation_handler() -> ConversationHandler:
    """تنظیم و برگرداندن ConversationHandler اصلی"""
    async def handle_non_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Re-prompt for contact on non-contact messages in REGISTER state"""
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

    return ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.TEXT | filters.CONTACT, start)  # اضافه کردن این خط
        ],
        states={
            REGISTER: [
                MessageHandler(filters.CONTACT, handle_contact),  # Handle contact messages first
                MessageHandler(~filters.CONTACT & ~filters.COMMAND, handle_non_contact),  # All other messages
                CommandHandler("start", start)  # Allow restart
            ],
            ROLE: [
                MessageHandler(filters.TEXT | filters.CONTACT, handle_role),  # تغییر این خط
                CallbackQueryHandler(handle_role)  # Handle button clicks
            ],
            EMPLOYER_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message),  # Handle text
                CallbackQueryHandler(handle_message)  # Handle buttons
            ],
            CATEGORY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_category_selection),  # Handle text
                CallbackQueryHandler(handle_category_selection)
            ],
            SUBCATEGORY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_category_selection),  # Handle text
                CallbackQueryHandler(handle_category_selection)
            ],
            DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_project_details)
            ],
            LOCATION_TYPE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_location),  # Handle text
                CallbackQueryHandler(handle_location)
            ],
            LOCATION_INPUT: [
                MessageHandler(filters.LOCATION, handle_location),  # Handle location
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_location),  # Handle text
                CallbackQueryHandler(handle_location)  # Handle buttons
            ],
            DETAILS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_project_details),  # Handle text
                CallbackQueryHandler(handle_project_details)  # Handle buttons
            ],
            DETAILS_FILES: [
                MessageHandler(filters.PHOTO, handle_attachment),  # Handle photos
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_attachment),  # Handle text
                CallbackQueryHandler(handle_attachment)  # Handle buttons
            ],
            CHANGE_PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_phone)  # از phone_handler
            ],
            VERIFY_CODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, verify_new_phone)  # از phone_handler
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(handle_callback),  # اضافه کردن general callback handler
            MessageHandler(filters.ALL, handle_non_contact)  # اضافه کردن fallback برای همه پیام‌ها
        ],
        name="main_conversation",
        persistent=True,
        allow_reentry=True,
        per_chat=False,  # تغییر این پارامتر
        per_user=True,
        per_message=False
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