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
    logger.info("Bot started, loading persistence data...")
    
    try:
        # بازیابی داده‌های persistence
        if application.persistence:
            bot_data = await application.persistence.get_bot_data()
            if not bot_data:
                bot_data = {}
            application.bot_data.update(bot_data)
        
        # اطمینان از وجود لیست active_chats
        if 'active_chats' not in application.bot_data:
            application.bot_data['active_chats'] = []
            
        active_chats = application.bot_data['active_chats']
        logger.info(f"Found {len(active_chats)} active chats")
        
        # ارسال پیام به چت‌های فعال
        for chat_id in active_chats:
            try:
                # ارسال پیام آپدیت بی‌صدا
                message = await application.bot.send_message(
                    chat_id=chat_id,
                    text="🔄 ربات مجدداً راه‌اندازی شد!\nلطفاً منتظر بمانید...",
                    reply_markup=MAIN_MENU_KEYBOARD,
                    disable_notification=True
                )
                
                # صبر کوتاه
                await asyncio.sleep(2)
                
                try:
                    # پاک کردن پیام آپدیت
                    await message.delete()
                    
                    # ارسال کامند start به صورت خودکار
                    await application.bot.send_message(
                        chat_id=chat_id,
                        text="/start",
                        disable_notification=True
                    )
                    logger.info(f"Sent restart notification and auto-start to {chat_id}")
                    
                except Exception as e:
                    logger.error(f"Failed to process restart for chat {chat_id}: {e}")
                    continue
                    
            except Exception as e:
                logger.error(f"Failed to notify chat {chat_id}: {e}")
                # اگر چت غیرفعال است، از لیست حذف می‌کنیم
                if "chat not found" in str(e).lower() or "blocked" in str(e).lower():
                    active_chats.remove(chat_id)
                    logger.info(f"Removed inactive chat {chat_id}")
                continue

        # ذخیره تغییرات
        if application.persistence:
            await application.persistence.update_bot_data(application.bot_data)
            
    except Exception as e:
        logger.error(f"Error in post_init: {e}")

def handle_signals():
    """تنظیم signal handlers"""
    def signal_handler(signum, frame):
        """Handler برای سیگنال‌های سیستمی"""
        global is_shutting_down
        if is_shutting_down:
            return
        is_shutting_down = True
        logger.info(f"Received signal {signum}")
        shutdown_event.set()

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
        # ایجاد persistence
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
        
        # ساخت application
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
        application.job_queue.run_repeating(watchdog_job, interval=300)
        
        await application.initialize()
        await application.start()
        
        # اجرای polling تا زمان دریافت سیگنال shutdown
        while not shutdown_event.is_set():
            try:
                await application.update_queue.get()
            except asyncio.CancelledError:
                break
            
    except Exception as e:
        logger.error(f"Error in run_bot: {e}")
        await shutdown()

def main():
    """Main function"""
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set!")
        sys.exit(1)

    # تنظیم signal handlers
    handle_signals()

    try:
        # اجرای اصلی برنامه
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("Received KeyboardInterrupt")
    finally:
        # اطمینان از cleanup مناسب
        if application:
            asyncio.run(shutdown())

if __name__ == '__main__':
    main()