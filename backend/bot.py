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
    filename="bot.log",  # فقط به فایل لاگ بنویسد
    filemode='w'  # هر بار فایل لاگ را خالی کند
)
logger = logging.getLogger(__name__)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('apscheduler').setLevel(logging.WARNING)

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
PERSISTENCE_PATH = os.path.join(os.path.dirname(__file__), 'data', 'persistence.pickle')
os.makedirs(os.path.dirname(PERSISTENCE_PATH), exist_ok=True)

# متغیرهای گلوبال
application = None
shutdown_event = asyncio.Event()
is_shutting_down = False

async def post_init(application: Application):
    """اجرا شدن بعد از راه‌اندازی"""
    logger.info("Bot started, initializing...")
    
    try:
        # اول persistence را لود کنیم
        if application.persistence:
            bot_data = await application.persistence.get_bot_data()
            if bot_data:
                application.bot_data.update(bot_data)
                logger.info("Loaded persistence data")
            
        # بررسی و ایجاد لیست active_chats
        if 'active_chats' not in application.bot_data:
            application.bot_data['active_chats'] = []
        
        active_chats = application.bot_data['active_chats']
        logger.info(f"Found {len(active_chats)} active chats")
        
        # ارسال پیام به چت‌های فعال با تاخیر
        await asyncio.sleep(2)  # صبر برای اطمینان از آماده بودن کامل ربات
        
        for chat_id in active_chats:
            try:
                message = await application.bot.send_message(
                    chat_id=chat_id,
                    text="🔄 ربات مجدداً راه‌اندازی شد!\nلطفاً منتظر بمانید...",
                    reply_markup=MAIN_MENU_KEYBOARD,
                    disable_notification=True
                )
                
                await asyncio.sleep(2)
                
                try:
                    await message.delete()
                    await application.bot.send_message(
                        chat_id=chat_id,
                        text="/start",
                        disable_notification=True
                    )
                    logger.info(f"Sent restart notification to {chat_id}")
                except Exception as e:
                    logger.error(f"Failed to process restart for {chat_id}: {e}")
            except Exception as e:
                logger.error(f"Failed to notify {chat_id}: {e}")
                if "chat not found" in str(e).lower() or "blocked" in str(e).lower():
                    active_chats.remove(chat_id)
                    logger.info(f"Removed inactive chat {chat_id}")
        
        # ذخیره تغییرات
        if application.persistence:
            await application.persistence.update_bot_data(application.bot_data)
            logger.info("Updated persistence data")
            
    except Exception as e:
        logger.error(f"Error in post_init: {e}")
        raise  # اضافه کردن raise برای اطلاع از خطا

def handle_signals():
    """تنظیم signal handlers"""
    def signal_handler(signum, frame):
        """Handler برای سیگنال‌های سیستمی"""
        global is_shutting_down
        if not is_shutting_down:
            is_shutting_down = True
            logger.info(f"Received signal {signum}")
            
            # اجرای shutdown در event loop اصلی
            if application:
                loop = asyncio.get_event_loop()
                loop.create_task(shutdown())
                loop.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

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
            application = None
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
    finally:
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

        # اضافه کردن هندلرها
        application.add_handler(get_conversation_handler())
        application.add_handler(CallbackQueryHandler(handle_callback))
        application.add_handler(MessageHandler(
            filters.Regex(r'^/view_photos_\d+$') & filters.TEXT,
            handle_photos_command
        ))
        application.add_error_handler(handle_error)
        
        # راه‌اندازی ربات به صورت blocking
        await application.initialize()
        await application.start()
        await application.run_polling(allowed_updates=Update.ALL_TYPES, close_loop=False)
        
    except Exception as e:
        logger.error(f"Error in run_bot: {e}")
    finally:
        if application:
            await application.stop()
            await application.shutdown()

def main():
    """Main function"""
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set!")
        sys.exit(1)

    try:
        # تنظیم signal handlers
        handle_signals()
        
        # ایجاد و تنظیم event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # اجرای ربات
        loop.run_until_complete(run_bot())
        
    except KeyboardInterrupt:
        logger.info("Received KeyboardInterrupt")
    finally:
        # اطمینان از بسته شدن loop
        loop = asyncio.get_event_loop()
        loop.stop()
        loop.close()

if __name__ == '__main__':
    main()