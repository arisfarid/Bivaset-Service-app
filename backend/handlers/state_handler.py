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
PROJECT_ACTIONS = range(18)

from handlers.submission_handler import submit_project

def get_conversation_handler() -> ConversationHandler:
    """تنظیم و برگرداندن ConversationHandler اصلی"""
    return ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            START: [MessageHandler(filters.TEXT & ~filters.COMMAND, start)],
            REGISTER: [MessageHandler(filters.CONTACT, handle_contact)],
            ROLE: [
                MessageHandler(filters.Regex("^درخواست خدمات \| کارفرما 👔$"), handle_role),
                MessageHandler(filters.Regex("^پیشنهاد قیمت \| مجری 🦺$"), handle_role)
            ],
            EMPLOYER_MENU: [
                MessageHandler(filters.Regex("^📋 درخواست خدمات جدید$"), handle_message),
                MessageHandler(filters.Regex("^📊 مشاهده درخواست‌ها$"), handle_view_projects),
                MessageHandler(filters.Regex("^⬅️ بازگشت$"), start)
            ],
            CATEGORY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex("^⬅️ بازگشت$"), 
                             handle_category_selection),
                MessageHandler(filters.Regex("^⬅️ بازگشت$"), 
                             lambda u, c: handle_message(u, c)),
            ],
            SUBCATEGORY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex("^⬅️ بازگشت$"), 
                             handle_category_selection),
                MessageHandler(filters.Regex("^⬅️ بازگشت$"), 
                             lambda u, c: handle_category_selection(u, c)),
            ],
            DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex("^⬅️ بازگشت$"), 
                             handle_project_details),
                MessageHandler(filters.Regex("^⬅️ بازگشت$"), 
                             lambda u, c: handle_category_selection(u, c)),
            ],
            LOCATION_TYPE: [
                MessageHandler(filters.LOCATION, handle_location),
                MessageHandler(filters.Regex("^(🏠 محل من|🔧 محل مجری|💻 غیرحضوری)$"), 
                             handle_location),
                MessageHandler(filters.Regex("^⬅️ بازگشت$"), 
                             lambda u, c: handle_project_details(u, c)),
            ],
            LOCATION_INPUT: [
                MessageHandler(filters.LOCATION, handle_location),
                MessageHandler(filters.Regex("^⬅️ بازگشت$"), 
                             lambda u, c: handle_location(u, c)),
            ],
            DETAILS: [
                MessageHandler(filters.Regex("^✅ ثبت درخواست$"), submit_project),
                MessageHandler(filters.Regex("^(📸|📅|⏳|💰|📏)"), handle_project_details),
                MessageHandler(filters.Regex("^⬅️ بازگشت$"), 
                             lambda u, c: handle_location(u, c)),
            ],
            DETAILS_FILES: [
                MessageHandler(filters.PHOTO, handle_attachment),
                MessageHandler(filters.Regex("^🏁 اتمام ارسال تصاویر$"), 
                             lambda u, c: handle_project_details(u, c)),
                MessageHandler(filters.Regex("^⬅️ بازگشت$"), 
                             lambda u, c: handle_project_details(u, c)),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(handle_callback)
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