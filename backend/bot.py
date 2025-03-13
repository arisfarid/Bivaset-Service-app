import os
import sys
import logging
from telegram import KeyboardButton, ReplyKeyboardMarkup, Bot, Update, Message, Chat, User
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler, ContextTypes

from utils import save_timestamp, check_for_updates
from handlers.start_handler import start, handle_contact, check_phone, handle_role
from handlers.location_handler import handle_location
from handlers.photo_handler import handle_photo
from handlers.message_handler import handle_message
from handlers.callback_handler import handle_callback
from handlers.new_project_handlers import handle_new_project
from handlers.view_projects_handlers import handle_view_projects
from handlers.project_details_handlers import handle_project_details

# تنظیم لاگ‌ها
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('apscheduler').setLevel(logging.WARNING)

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

async def send_update_and_restart(token: str, active_chats: list, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Starting update and restart for {len(active_chats)} chats")
    updated = False  # Flag to track if any update was successful
    for chat_id in active_chats:
        try:
            await context.bot.send_message(chat_id=chat_id, text="🎉 ربات آپدیت شد! لطفاً ادامه بدهید.", disable_notification=True)
            logger.info(f"Sent update notification to {chat_id}")
            # Simulate /start for this chat
            fake_update = Update(
                update_id=0,
                message=Message(
                    message_id=0,
                    chat=Chat(id=chat_id, type='private'),
                    date=None,
                    from_user=User(id=chat_id, is_bot=False, first_name="BotUpdate")
                )
            )
            await start(fake_update, context)
            logger.info(f"Restarted bot for chat {chat_id}")
            updated = True  # Mark as updated if we reach here
        except Exception as e:
            logger.error(f"Failed to process update for {chat_id}: {e}")
    if active_chats and updated:  # Save timestamp only if there were chats and update succeeded
        save_timestamp()

async def check_and_notify(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Checking for updates...")
    logger.info(f"Bot data: {context.bot_data}")
    if check_for_updates(context.bot_data):
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

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
app.add_handler(MessageHandler(filters.LOCATION, handle_location))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(handle_callback))

# ConversationHandler setup
conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        0: [MessageHandler(filters.CONTACT, handle_contact)],
        1: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_role)],
        2: [],
        3: []
    },
    fallbacks=[CommandHandler('cancel', start)]
)
app.add_handler(conv_handler)

# Add periodic jobs
app.job_queue.run_repeating(test_job, interval=5, first=0, data=app)
app.job_queue.run_repeating(check_and_notify, interval=10, first=0, data=app)

logger.info("Bot is starting polling...")
app.run_polling()
# Updated at Thu Mar 13 18:40:04 UTC 2025
# Updated at Thu Mar 13 18:50:18 UTC 2025
# Updated at Thu Mar 13 18:59:44 UTC 2025
# Updated at Thu Mar 13 19:15:28 UTC 2025
# Updated at Thu Mar 13 22:22:03 UTC 2025
# Updated at Thu Mar 13 22:34:54 UTC 2025
