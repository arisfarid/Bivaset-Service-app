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
            
            # صبر کردن 3 ثانیه
            await asyncio.sleep(3)
            
            # پاک کردن پیام
            try:
                await message.delete()
            except Exception as e:
                logger.error(f"Failed to delete restart message: {e}")
                
            logger.info(f"Sent restart notification to {chat_id}")
            
        except Exception as e:
            logger.error(f"Failed to notify chat {chat_id}: {e}")
            continue

    # پاک کردن context تمام کاربران
    for user_id in bot_data.get('user_data', {}):
        try:
            await application.user_data.clear()
            await application.persistence.update_user_data(user_id=user_id, data={})
        except Exception as e:
            logger.error(f"Failed to clear context for user {user_id}: {e}")

async def signal_handler(signum, frame):
    """Handle system signals"""
    logger.info(f"Received signal {signum}")
    # Clean shutdown
    await shutdown()

async def shutdown():
    """Cleanup and shutdown"""
    logger.info("Shutting down...")
    try:
        # Stop the application
        await application.stop()
        await application.shutdown()
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
    finally:
        # Force exit after 5 seconds
        await asyncio.sleep(5)
        sys.exit(0)

async def watchdog_job(context: ContextTypes.DEFAULT_TYPE):
    """چک کردن سلامت API"""
    try:
        response = requests.get(f"{BASE_URL}health/")
        if response.status_code != 200:
            logger.error("API health check failed")
            # به جای ریستارت، فقط لاگ می‌کنیم
            return
    except Exception as e:
        logger.error(f"Watchdog error: {e}")
        return

def main():
    try:
        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        if not TOKEN:
            logger.error("TELEGRAM_BOT_TOKEN not set!")
            sys.exit(1)

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
            
        app = (
            Application.builder()
            .token(TOKEN)
            .persistence(persistence)
            .post_init(post_init)
            .build()
        )

        # اضافه کردن هندلرها
        app.add_handler(get_conversation_handler())
        app.add_handler(CallbackQueryHandler(handle_callback))
        app.add_handler(MessageHandler(
            filters.Regex(r'^/view_photos_\d+$') & filters.TEXT,
            handle_photos_command
        ))
        app.add_error_handler(handle_error)
        
        # Add watchdog job with longer interval
        app.job_queue.run_repeating(watchdog_job, interval=300)
        
        # Store application globally for shutdown
        global application
        application = app
        
        # اجرای ربات
        app.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        sys.exit(1)

if __name__ == '__main__':
    application = None  # Global variable for application instance
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Received KeyboardInterrupt")
        if application:
            asyncio.run(shutdown())