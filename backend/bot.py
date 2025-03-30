import os
import sys
import signal
import asyncio
import logging
import requests
from utils import BASE_URL, restart_chat
from telegram import Update
from telegram.ext import (
    Application, MessageHandler, filters, CallbackQueryHandler, 
    ContextTypes, PicklePersistence, PersistenceInput
)
from handlers.state_handler import get_conversation_handler, handle_error
from handlers.callback_handler import handle_callback
from keyboards import MAIN_MENU_KEYBOARD

# تنظیمات اولیه
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,
    filename="bot.log",
    filemode='w'
)
logger = logging.getLogger(__name__)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('apscheduler').setLevel(logging.WARNING)

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
PERSISTENCE_PATH = os.path.join(os.path.dirname(__file__), 'data', 'persistence.pickle')
os.makedirs(os.path.dirname(PERSISTENCE_PATH), exist_ok=True)

# متغیرهای گلوبال
application = None
is_shutting_down = False

async def post_init(application: Application):
    """اجرا شدن بعد از راه‌اندازی"""
    logger.info("Bot started, initializing...")
    
    try:
        # بازیابی داده‌ها از persistence
        if application.persistence:
            bot_data = await application.persistence.get_bot_data()
            active_chats = bot_data.get('active_chats', [])
            
            if active_chats:
                logger.info(f"Found {len(active_chats)} active chats")
                
                for chat_id in active_chats[:]:
                    try:
                        message = await application.bot.send_message(
                            chat_id=chat_id,
                            text="🔄 ربات مجدداً راه‌اندازی شد!",
                            reply_markup=MAIN_MENU_KEYBOARD,
                            disable_notification=True
                        )
                        await asyncio.sleep(2)
                        await message.delete()
                        
                        # ارسال start به صورت خودکار
                        await application.bot.send_message(
                            chat_id=chat_id,
                            text="/start",
                            disable_notification=True
                        )
                        logger.info(f"Restarted chat {chat_id}")
                        
                    except Exception as e:
                        logger.error(f"Failed to restart chat {chat_id}: {e}")
                        active_chats.remove(chat_id)
                        
                # ذخیره لیست به‌روز شده
                bot_data['active_chats'] = active_chats
                await application.persistence.update_bot_data(bot_data)
                
    except Exception as e:
        logger.error(f"Error in post_init: {e}")

async def shutdown():
    """Cleanup and shutdown"""
    global application, is_shutting_down
    
    if is_shutting_down:
        return
        
    is_shutting_down = True    
    logger.info("Shutting down application...")
    
    try:
        if application:
            await application.stop()
            await application.shutdown()
            if application.persistence:
                await application.persistence.flush()
            application = None
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

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

        # اضافه کردن هندلرها
        application.add_handler(get_conversation_handler())
        application.add_handler(CallbackQueryHandler(handle_callback))
        application.add_error_handler(handle_error)
        
        # راه‌اندازی ربات
        await application.initialize()
        await application.start()
        
        logger.info("Bot started successfully!")
        
        # اجرای polling
        await application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
        
    except Exception as e:
        logger.error(f"Error in run_bot: {e}", exc_info=True)
        if application:
            await shutdown()

def main():
    """Main function"""
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set!")
        sys.exit(1)

    try:
        # تنظیم signal handlers
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}")
            if application:
                asyncio.get_event_loop().run_until_complete(shutdown())
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # اجرای ربات
        asyncio.run(run_bot())
        
    except KeyboardInterrupt:
        logger.info("Received KeyboardInterrupt")
        if application:
            asyncio.run(shutdown())
    except Exception as e:
        logger.error(f"Error in main: {e}")
        if application:
            asyncio.run(shutdown())

if __name__ == '__main__':
    main()