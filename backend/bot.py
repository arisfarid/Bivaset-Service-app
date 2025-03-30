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
        # بازیابی داده‌ها از persistence
        if application.persistence and os.path.exists(PERSISTENCE_PATH):
            try:
                bot_data = await application.persistence.get_bot_data()
                if bot_data:
                    application.bot_data.update(bot_data)
                    logger.info(f"Loaded persistence data: {bot_data}")
            except Exception as e:
                logger.error(f"Error loading persistence data: {e}")
                application.bot_data.clear()
        
        # اطمینان از وجود لیست active_chats
        if 'active_chats' not in application.bot_data:
            application.bot_data['active_chats'] = []
            logger.info("Created new active_chats list")
        
        active_chats = application.bot_data.get('active_chats', [])
        logger.info(f"Found {len(active_chats)} active chats: {active_chats}")
        
        # ارسال پیام به چت‌های فعال
        for chat_id in active_chats[:]:  # استفاده از کپی برای حذف ایمن
            try:
                # ارسال پیام راه‌اندازی مجدد
                message = await application.bot.send_message(
                    chat_id=chat_id,
                    text="🔄 ربات در حال راه‌اندازی مجدد است...",
                    disable_notification=True
                )
                
                # صبر کوتاه
                await asyncio.sleep(1)
                
                # پاک کردن پیام قبلی و ارسال /start
                try:
                    await message.delete()
                    await application.bot.send_message(
                        chat_id=chat_id,
                        text="/start",
                        disable_notification=True
                    )
                    logger.info(f"Successfully restarted chat {chat_id}")
                    
                except Exception as e:
                    logger.error(f"Error in message handling for chat {chat_id}: {e}")
                    
            except telegram.error.Unauthorized:
                logger.info(f"Removing blocked chat {chat_id}")
                active_chats.remove(chat_id)
            except telegram.error.BadRequest as e:
                if "chat not found" in str(e).lower():
                    logger.info(f"Removing invalid chat {chat_id}")
                    active_chats.remove(chat_id)
                else:
                    logger.error(f"BadRequest for chat {chat_id}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error for chat {chat_id}: {e}")
        
        # ذخیره تغییرات در bot_data
        application.bot_data['active_chats'] = active_chats
        if application.persistence:
            await application.persistence.update_bot_data(application.bot_data)
            logger.info("Updated persistence data with current active chats")
            
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
                callback_data=False
            ),
            update_interval=30
        )

        # ساخت application با تنظیمات جدید
        builder = (
            Application.builder()
            .token(TOKEN)
            .persistence(persistence)
            .post_init(post_init)
            .concurrent_updates(True)
            .get_updates_read_timeout(30)
            .get_updates_write_timeout(30)
        )
        
        application = builder.build()

        # اضافه کردن هندلرها
        application.add_handler(get_conversation_handler())
        application.add_handler(CallbackQueryHandler(handle_callback))
        application.add_handler(MessageHandler(
            filters.Regex(r'^/view_photos_\d+$') & filters.TEXT,
            handle_photos_command
        ))
        application.add_error_handler(handle_error)

        # راه‌اندازی با await
        await application.initialize()
        await application.start()
        await application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
            close_loop=False
        )

    except Exception as e:
        logger.error(f"Error in run_bot: {e}", exc_info=True)
        if application:
            await shutdown()
        raise

def main():
    """Main function"""
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set!")
        sys.exit(1)

    try:
        # استفاده از asyncio.run برای مدیریت event loop
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("Received KeyboardInterrupt")
    except Exception as e:
        logger.error(f"Error in main: {e}")
    finally:
        if application:
            try:
                asyncio.run(shutdown())
            except RuntimeError:
                # اگر event loop قبلاً بسته شده باشد
                pass

if __name__ == '__main__':
    main()