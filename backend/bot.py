import os
import sys
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes, ConversationHandler
from utils import save_timestamp, check_for_updates
from handlers.start_handler import start, handle_contact, handle_role, cancel
from handlers.message_handler import handle_message, cancel as message_cancel
from handlers.category_handler import handle_category_selection, handle_category_callback
from handlers.location_handler import handle_location
from handlers.attachment_handler import handle_attachment
from handlers.project_details_handler import handle_project_details
from handlers.submission_handler import submit_project
from handlers.state_handler import handle_project_states
from handlers.view_handler import handle_view_projects, handle_view_callback
from handlers.edit_handler import handle_edit_callback
from handlers.callback_handler import handle_callback

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('apscheduler').setLevel(logging.WARNING)

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# تعریف حالت‌ها
START, REGISTER, ROLE, EMPLOYER_MENU, CATEGORY, SUBCATEGORY, DESCRIPTION, LOCATION_TYPE, LOCATION_INPUT, DETAILS, DETAILS_FILES, DETAILS_DATE, DETAILS_DEADLINE, DETAILS_BUDGET, DETAILS_QUANTITY, SUBMIT, VIEW_PROJECTS, PROJECT_ACTIONS = range(18)

async def send_update_and_restart(token: str, active_chats: list, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Starting update and restart for {len(active_chats)} chats")
    updated = False
    for chat_id in active_chats:
        try:
            keyboard = [[InlineKeyboardButton("راه‌اندازی مجدد", callback_data='restart')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(
                chat_id=chat_id,
                text="🎉 ربات آپدیت شد! لطفاً برای ادامه روی دکمه بزنید.",
                reply_markup=reply_markup,
                disable_notification=True
            )
            logger.info(f"Sent update notification to {chat_id}")
            updated = True
        except Exception as e:
            logger.error(f"Failed to send update to {chat_id}: {e}")
    if active_chats and updated:
        context.bot_data['last_update_processed'] = True
        save_timestamp()

async def check_and_notify(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Checking for updates...")
    logger.info(f"Bot data: {context.bot_data}")
    last_update_processed = context.bot_data.get('last_update_processed', False)
    if check_for_updates(context.bot_data) and not last_update_processed:
        logger.info("Update detected, sending notifications...")
        active_chats = context.bot_data.get('active_chats', [])
        logger.info(f"Active chats: {active_chats}")
        await send_update_and_restart(TOKEN, active_chats, context)

async def test_job(application: Application):
    logger.info("Test job running every 5 seconds")

if not TOKEN:
    logger.error("Error: TELEGRAM_BOT_TOKEN environment variable not set.")
    sys.exit(1)

logger.info(f"Using Telegram Bot Token: {TOKEN[:10]}...")

app = Application.builder().token(TOKEN).build()

# تنظیم ConversationHandler
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        START: [MessageHandler(filters.TEXT & ~filters.COMMAND, start)],
        REGISTER: [MessageHandler(filters.CONTACT, handle_contact)],
        ROLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_role)],
        EMPLOYER_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)],
        CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_category_selection)],
        SUBCATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_category_selection)],
        DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_project_details)],
        LOCATION_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_location), MessageHandler(filters.LOCATION, handle_location)],
        LOCATION_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_location), MessageHandler(filters.LOCATION, handle_location)],
        DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_project_details)],
        DETAILS_FILES: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_attachment), MessageHandler(filters.PHOTO, handle_attachment)],
        DETAILS_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_project_details)],
        DETAILS_DEADLINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_project_details)],
        DETAILS_BUDGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_project_details)],
        DETAILS_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_project_details)],
        SUBMIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, submit_project)],
        VIEW_PROJECTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_view_projects)],
        PROJECT_ACTIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_project_states)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

# اضافه کردن handlerها
app.add_handler(conv_handler)
app.add_handler(CallbackQueryHandler(handle_callback))

# اضافه کردن jobهای تکراری
app.job_queue.run_repeating(test_job, interval=5, first=0, data=app)
app.job_queue.run_repeating(check_and_notify, interval=10, first=0, data=app)

logger.info("Bot is starting polling...")
app.run_polling()