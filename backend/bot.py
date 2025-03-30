import os
import sys
import signal
import asyncio
import logging
import requests
import nest_asyncio
from utils import BASE_URL, restart_chat
from telegram import Update
from telegram.ext import (
    Application, CallbackQueryHandler, 
    ContextTypes, PicklePersistence, PersistenceInput,
    CommandHandler, ConversationHandler
)
from handlers.state_handler import get_conversation_handler, handle_error
from handlers.callback_handler import handle_callback
from keyboards import MAIN_MENU_KEYBOARD

# تنظیمات اولیه با اضافه کردن handler برای stdout
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log", mode='w'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('apscheduler').setLevel(logging.WARNING)

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
PERSISTENCE_PATH = os.path.join(os.path.dirname(__file__), 'data', 'persistence.pickle')
os.makedirs(os.path.dirname(PERSISTENCE_PATH), exist_ok=True)

# متغیرهای گلوبال
app = None
is_shutting_down = False

nest_asyncio.apply()

async def post_init(application: Application):
    """اجرا شدن بعد از راه‌اندازی"""
    logger.info("Bot started, initializing...")
    
    try:
        if application.persistence:
            bot_data = await application.persistence.get_bot_data()
            if not bot_data:
                bot_data = {}
                
            active_chats = bot_data.get('active_chats', [])
            logger.info(f"Found {len(active_chats)} active chats")
            
            for chat_id in active_chats[:]:
                try:
                    success = await restart_chat(application, chat_id)
                    if success:
                        logger.info(f"Chat {chat_id} restarted automatically.")
                    else:
                        logger.error(f"Chat {chat_id} failed to restart automatically.")
                except Exception as e:
                    logger.error(f"Failed to restart chat {chat_id}: {e}")
            
            bot_data['active_chats'] = active_chats
            await application.persistence.update_bot_data(bot_data)
            logger.info("Updated persistence data")
            
    except Exception as e:
        logger.error(f"Error in post_init: {e}", exc_info=True)

async def shutdown():
    """Cleanup and shutdown"""
    global app, is_shutting_down
    
    if is_shutting_down:
        return
        
    is_shutting_down = True    
    logger.info("Shutting down application...")
    
    if app:
        try:
            if app.persistence:
                await app.persistence.flush()
            await app.stop()
            await app.shutdown()
            app = None
            logger.info("Application shutdown complete")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}", exc_info=True)

async def run_bot():
    """Main async function to run the bot"""
    global app

    try:
        # تنظیم persistence
        persistence = PicklePersistence(
            filepath=PERSISTENCE_PATH,
            store_data=PersistenceInput(
                bot_data=True,
                chat_data=True,
                user_data=True,
                callback_data=True
            ),
            update_interval=30
        )

        # ساخت application
        app = (
            Application.builder()
            .token(TOKEN)
            .persistence(persistence)
            .post_init(post_init)
            .concurrent_updates(True)
            .build()
        )

        # اضافه کردن هندلرها
        app.add_handler(CommandHandler("start", reset_conversation))
        app.add_handler(get_conversation_handler())
        app.add_handler(CallbackQueryHandler(handle_callback))
        app.add_error_handler(handle_error)

        logger.info("Bot started successfully!")
        # فراخوانی run_polling که خودش initialize و start را اجرا می‌کند
        await app.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
            close_loop=False
        )

    except Exception as e:
        logger.error(f"Error in run_bot: {e}", exc_info=True)
        if app:
            await shutdown()
        raise

async def reset_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # این هندلر کانورسیون قبلی را ریست می‌کند
    context.user_data.clear()
    # ارسال پیام خوش‌آمد مجدد
    await update.message.reply_text(
        "👋 سلام! دوباره خوش آمدید.\nلطفاً /start را برای شروع مجدد ارسال کنید.",
        reply_markup=MAIN_MENU_KEYBOARD
    )
    return ConversationHandler.END

def main():
    """Main function"""
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set!")
        sys.exit(1)

    # تنظیم signal handlers
    def handle_signals(signum, frame):
        logger.info(f"Received signal {signum}")
        if app:
            # استفاده از get_event_loop به جای new_event_loop
            loop = asyncio.get_event_loop()
            loop.run_until_complete(shutdown())
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signals)
    signal.signal(signal.SIGTERM, handle_signals)

    try:
        # اجرای ربات
        asyncio.get_event_loop().run_until_complete(run_bot())
    except KeyboardInterrupt:
        logger.info("Received KeyboardInterrupt")
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
    finally:
        if app:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(shutdown())
            loop.close()

if __name__ == '__main__':
    main()
