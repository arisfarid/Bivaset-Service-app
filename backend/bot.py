import os
import sys
import signal
import asyncio
import logging
import requests
from utils import BASE_URL
from telegram import Update
from telegram.ext import (
    Application, MessageHandler, filters, CallbackQueryHandler, 
    ContextTypes, PicklePersistence, PersistenceInput
)
from handlers.state_handler import get_conversation_handler, handle_error
from handlers.attachment_handler import handle_photos_command
from handlers.callback_handler import handle_callback
from keyboards import MAIN_MENU_KEYBOARD

# تنظیمات اولیه
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,
    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('apscheduler').setLevel(logging.WARNING)

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
PERSISTENCE_PATH = os.path.join(os.path.dirname(__file__), 'data', 'persistence.pickle')
os.makedirs(os.path.dirname(PERSISTENCE_PATH), exist_ok=True)

# متغیر global در سطح ماژول
application = None
shutdown_event = asyncio.Event()

async def post_init(application: Application):
    """اجرا شدن بعد از راه‌اندازی"""
    logger.info("Bot started, sending restart notification to active chats...")
    bot_data = application.bot_data
    active_chats = bot_data.get('active_chats', [])
    
    for chat_id in active_chats:
        try:
# ارسال پیام به صورت بی‌صدا
            message = await application.bot.send_message(
                chat_id=chat_id,
                text="🔄 ربات مجدداً راه‌اندازی شد!\nلطفاً از منوی زیر ادامه دهید:",
                reply_markup=MAIN_MENU_KEYBOARD,
                disable_notification=True  # بی‌صدا
            )
            await asyncio.sleep(3)
            try:
                await message.delete()
            except Exception as e:
                logger.error(f"Failed to delete restart message: {e}")
        except Exception as e:
            logger.error(f"Failed to notify chat {chat_id}: {e}")

def signal_handler(signum, frame):
    """Handler for system signals that runs in the main thread"""
    logger.info(f"Received signal {signum}")
    if application:
        # Set shutdown event
        shutdown_event.set()
        # Stop the event loop
        loop = asyncio.get_event_loop()
        loop.stop()
        
async def shutdown():
    """Cleanup and shutdown"""
    global application
    if application:
        logger.info("Shutting down application...")
        try:
            await application.stop()
            await application.shutdown()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        finally:
            application = None
            sys.exit(0)

async def watchdog_job(context: ContextTypes.DEFAULT_TYPE):
    """چک کردن سلامت API"""
    if not shutdown_event.is_set():
        try:
            response = requests.get(f"{BASE_URL}health/")
            if response.status_code != 200:
                logger.error("API health check failed")
        except Exception as e:
            logger.error(f"Watchdog error: {e}")

async def run_bot():
    """Main async function to run the bot"""
    global application
    
    try:
        persistence = PicklePersistence(
            filepath=PERSISTENCE_PATH,
            store_data=PersistenceInput(
                bot_data=True,
                chat_data=True,
                user_data=True,
                callback_data=False
            ),
            update_interval=60
        )
            
        application = (
            Application.builder()
            .token(TOKEN)
            .persistence(persistence)
            .post_init(post_init)
            .build()
        )

        application.add_handler(get_conversation_handler())
        application.add_handler(CallbackQueryHandler(handle_callback))
        application.add_handler(MessageHandler(
            filters.Regex(r'^/view_photos_\d+$') & filters.TEXT,
            handle_photos_command
        ))
        application.add_error_handler(handle_error)
        application.job_queue.run_repeating(watchdog_job, interval=300)
        
        await application.initialize()
        await application.start()
        await application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"Error in run_bot: {e}")
        if application:
            await shutdown()
        sys.exit(1)

def main():
    """Main function that sets up signal handlers and runs the bot"""
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set!")
        sys.exit(1)

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Get or create event loop
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(run_bot())
    except KeyboardInterrupt:
        logger.info("Received KeyboardInterrupt in main")
        if application:
            loop.run_until_complete(shutdown())
    finally:
        loop.close()

if __name__ == '__main__':
    main()