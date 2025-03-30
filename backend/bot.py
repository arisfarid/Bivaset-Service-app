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
        # بازیابی لیست چت‌های فعال
        if application.persistence:
            bot_data = await application.persistence.get_bot_data()
            active_chats = bot_data.get('active_chats', [])
            
            if active_chats:
                logger.info(f"Found {len(active_chats)} active chats")
                
                # راه‌اندازی مجدد همه چت‌های فعال
                success_count = 0
                for chat_id in active_chats[:]:  # استفاده از کپی برای حذف ایمن
                    try:
                        # نوتیفیکیشن راه‌اندازی مجدد
                        temp_msg = await application.bot.send_message(
                            chat_id=chat_id,
                            text="🔄 در حال راه‌اندازی مجدد...",
                            disable_notification=True
                        )
                        
                        # راه‌اندازی مجدد چت
                        if await restart_chat(application, chat_id):
                            success_count += 1
                            logger.info(f"Successfully restarted chat {chat_id}")
                        else:
                            logger.warning(f"Failed to restart chat {chat_id}")
                            
                        # پاک کردن پیام موقت
                        await temp_msg.delete()
                        
                    except Exception as e:
                        logger.error(f"Error restarting chat {chat_id}: {e}")
                        # حذف چت‌های غیرفعال از لیست
                        active_chats.remove(chat_id)
                
                logger.info(f"Successfully restarted {success_count} out of {len(active_chats)} chats")
                
                # ذخیره لیست به‌روز شده
                bot_data['active_chats'] = active_chats
                await application.persistence.update_bot_data(bot_data)
                
    except Exception as e:
        logger.error(f"Error in post_init: {e}", exc_info=True)
        raise

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
        # ذخیره آخرین وضعیت persistence
        if application and application.persistence:
            try:
                await application.persistence.flush()
                logger.info("Persistence data saved")
            except Exception as e:
                logger.error(f"Error saving persistence data: {e}")

async def run_bot():
    """Main async function to run the bot"""
    global application

    try:
        # تنظیم persistence
        persistence = PicklePersistence(
            filepath=PERSISTENCE_PATH,
            store_data=PersistenceInput(
                bot_data=True,
                chat_data=True,
                user_data=True,
                callback_data=True  # تغییر به True
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
        application.add_error_handler(handle_error)
        
        # راه‌اندازی ربات
        await application.initialize()
        await application.start()
        
        logger.info("Bot started successfully!")
        
        # اجرای polling به صورت blocking
        await application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
            close_loop=False
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
        handle_signals()
        
        # استفاده از asyncio.run برای مدیریت event loop
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