import os
import sys
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
            await application.bot.send_message(
                chat_id=chat_id,
                text="🔄 ربات مجدداً راه‌اندازی شد!\nلطفاً از منوی زیر ادامه دهید:",
                reply_markup=MAIN_MENU_KEYBOARD
            )
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

async def watchdog_job(context: ContextTypes.DEFAULT_TYPE):
    """چک کردن سلامت ربات و ریستارت در صورت نیاز"""
    try:
        response = requests.get(f"{BASE_URL}health/")
        if response.status_code != 200:
            logger.error("API health check failed")
            os.execv(sys.executable, ['python'] + sys.argv)
    except Exception as e:
        logger.error(f"Watchdog error: {e}")
        os.execv(sys.executable, ['python'] + sys.argv)

def main():
    try:
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
        
        # اضافه کردن watchdog job
        app.job_queue.run_repeating(watchdog_job, interval=300)
        
        # اجرای ربات
        app.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == '__main__':
    main()