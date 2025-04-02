import os
import sys
import signal
import asyncio
import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, PicklePersistence, PersistenceInput, ConversationHandler
from telegram import Update
from handlers.state_handler import get_conversation_handler, handle_error
from handlers.callback_handler import handle_callback
from keyboards import MAIN_MENU_KEYBOARD, RESTART_INLINE_MENU_KEYBOARD
from utils import restart_chat

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
    """مدیریت راه‌اندازی مجدد پس از آپدیت"""
    logger.info("Bot started, initializing...")
    
    try:
        bot_data = await application.persistence.get_bot_data() or {}
        active_chats = bot_data.get('active_chats', [])
        logger.info(f"Found {len(active_chats)} active chats")
        
        # پاک کردن پیام‌های آپدیت قدیمی
        if 'update_messages' in bot_data:
            for chat_id, message_id in bot_data['update_messages'].items():
                try:
                    await application.bot.delete_message(
                        chat_id=int(chat_id),
                        message_id=message_id
                    )
                except Exception as e:
                    logger.warning(f"Could not delete old update message in chat {chat_id}: {e}")
        
        # ریست کردن لیست پیام‌های آپدیت
        bot_data['update_messages'] = {}
        
        update_message = (
            "🔄 *ربات بی‌واسط به‌روزرسانی شد!*\n\n"
            "✨ امکانات جدید اضافه شده\n"
            "🛠 بهبود عملکرد و رفع باگ‌ها\n\n"
            "برای استفاده از نسخه جدید، لطفاً روی دکمه زیر کلیک کنید:"
        )

        for chat_id in active_chats[:]:
            try:
                # ارسال پیام آپدیت بی‌صدا
                sent_message = await application.bot.send_message(
                    chat_id=chat_id,
                    text=update_message,
                    parse_mode='Markdown',
                    disable_notification=True,
                    reply_markup=RESTART_INLINE_MENU_KEYBOARD
                )
                
                # ذخیره message_id برای پاک کردن بعدی
                bot_data['update_messages'][str(chat_id)] = sent_message.message_id
                
                logger.info(f"Update message sent to chat {chat_id}")
                
                # تاخیر کوتاه بین ارسال‌ها
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Failed to send update message to chat {chat_id}: {e}")
                active_chats.remove(chat_id)
                continue
        
        # ذخیره تغییرات در persistence
        bot_data['active_chats'] = active_chats
        await application.persistence.update_bot_data(bot_data)
        logger.info("Updated persistence data")
        
    except Exception as e:
        logger.error(f"Error in post_init: {e}")

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
    
    # تغییر ترتیب ثبت هندلرها
    app.add_handler(get_conversation_handler())  # اول
    app.add_handler(CommandHandler("start", reset_conversation))  # دوم
    app.add_handler(CallbackQueryHandler(handle_callback))  # سوم
    app.add_error_handler(handle_error)  # آخر
    
    # اضافه کردن لاگر برای دیباگ
    logging.getLogger('telegram').setLevel(logging.DEBUG)
    logging.getLogger('telegram.ext.conversationhandler').setLevel(logging.DEBUG)
    
    return app

async def reset_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = update.effective_chat.id
    bot_data = context.bot_data
    if 'active_chats' not in bot_data:
        bot_data['active_chats'] = []
    if chat_id not in bot_data['active_chats']:
        bot_data['active_chats'].append(chat_id)
        await context.application.persistence.update_bot_data(bot_data)
        logger.info(f"Added {chat_id} to active chats from reset_conversation")
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