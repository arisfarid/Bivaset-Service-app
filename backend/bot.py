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
    active_chats = bot_data.get('active_chats', [])
    logger.info(f"Found {len(active_chats)} active chats")
    await asyncio.sleep(2)  # صبر برای اطمینان از اتمام initialize
    # کد ری‌استارت چت‌ها رو اینجا نگه می‌داریم (بدون تغییر)

async def shutdown(application: Application):
    logger.info("Shutting down application...")
    if application.running:
        await application.stop()
        await application.shutdown()
    logger.info("Application shutdown complete")

async def run_bot():
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
    
    logger.info("Bot started successfully!")
    await app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
    
    return app  # برگردوندن app برای مدیریت بهتر

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

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def signal_handler():
        logger.info("Received shutdown signal")
        if 'app' in locals():
            await shutdown(app)
        loop.stop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(signal_handler()))

    try:
        app = loop.run_until_complete(run_bot())
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
    finally:
        if 'app' in locals():
            loop.run_until_complete(shutdown(app))
        loop.close()

if __name__ == '__main__':
    main()