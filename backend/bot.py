import os
import sys
import signal
import asyncio
import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, PicklePersistence, PersistenceInput, ConversationHandler
from telegram import Update
from handlers.state_handler import get_conversation_handler, handle_error
from handlers.callback_handler import handle_callback
from keyboards import MAIN_MENU_KEYBOARD

# تنظیمات لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.FileHandler("bot.log", mode='w'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('apscheduler').setLevel(logging.WARNING)

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
PERSISTENCE_PATH = os.path.join(os.path.dirname(__file__), 'data', 'persistence.pickle')
os.makedirs(os.path.dirname(PERSISTENCE_PATH), exist_ok=True)

async def post_init(application: Application):
    logger.info("Bot started, initializing...")
    bot_data = await application.persistence.get_bot_data() or {}
    active_chats = bot_data.get('active_chats', [])  # تعریف active_chats
    logger.info(f"Found {len(active_chats)} active chats")
    # خط تستی
    if 123456789 not in active_chats:  # فقط اگه وجود نداره اضافه کن
        active_chats.append(123456789)
        bot_data['active_chats'] = active_chats
        await application.persistence.update_bot_data(bot_data)
        logger.info("Added test chat_id 123456789 to active_chats")
    await asyncio.sleep(2)
    for chat_id in active_chats[:]:
        try:
            for attempt in range(3):
                success = await restart_chat(application, chat_id)
                if success:
                    logger.info(f"Chat {chat_id} restarted successfully on attempt {attempt + 1}")
                    break
                else:
                    logger.warning(f"Restart attempt {attempt + 1} failed for chat {chat_id}")
                    await asyncio.sleep(1)
            else:
                logger.error(f"All restart attempts failed for chat {chat_id}")
                active_chats.remove(chat_id)
        except Exception as e:
            logger.error(f"Failed to restart chat {chat_id}: {e}")
            active_chats.remove(chat_id)
            continue
        await asyncio.sleep(0.5)
    bot_data['active_chats'] = active_chats
    await application.persistence.update_bot_data(bot_data)
    logger.info("Updated persistence data")
    
async def shutdown(application: Application):
    logger.info("Shutting down application...")
    if application.running:
        await application.stop()
        await application.shutdown()
    logger.info("Application shutdown complete")

def build_application():
    persistence = PicklePersistence(
        filepath=PERSISTENCE_PATH,
        store_data=PersistenceInput(bot_data=True, chat_data=True, user_data=True, callback_data=True),
        update_interval=30
    )
    
    app = (
        Application.builder()
        .token(TOKEN)
        .persistence(persistence)
        .post_init(post_init)
        .concurrent_updates(True)
        .build()
    )
    
    app.add_handler(CommandHandler("start", reset_conversation))
    app.add_handler(get_conversation_handler())
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_error_handler(handle_error)
    
    return app

async def reset_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "👋 سلام! دوباره خوش آمدید.\nلطفاً /start را برای شروع مجدد ارسال کنید.",
        reply_markup=MAIN_MENU_KEYBOARD
    )
    return ConversationHandler.END

def main():
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set!")
        sys.exit(1)

    app = build_application()
    logger.info("Bot started successfully!")
    
    # مدیریت سیگنال‌ها
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}")
        asyncio.run(shutdown(app))
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
    finally:
        asyncio.run(shutdown(app))

if __name__ == '__main__':
    main()