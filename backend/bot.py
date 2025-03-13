import os
import sys
import logging
from telegram import KeyboardButton, ReplyKeyboardMarkup, Bot  # Add Bot import
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler
import asyncio  # Add asyncio import
from utils import save_timestamp, check_for_updates
from handlers.start_handler import start, handle_contact, check_phone, handle_role
from handlers.location_handler import handle_location
from handlers.photo_handler import handle_photo
from handlers.message_handler import handle_message
from handlers.callback_handler import handle_callback
from handlers.new_project_handlers import handle_new_project
from handlers.view_projects_handlers import handle_view_projects
from handlers.project_details_handlers import handle_project_details

# تنظیم لاگ‌ها
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log"),  # ذخیره لاگ توی فایل
        logging.StreamHandler()  # نمایش توی کنسول
    ]
)
logger = logging.getLogger(__name__)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('apscheduler').setLevel(logging.WARNING)

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

async def notify_update(context):
    if 'active_chats' in context.bot_data:
        for chat_id in context.bot_data['active_chats']:
            await context.bot.send_message(
                chat_id=chat_id,
                text="🔄 ربات بروزرسانی شد و امکانات جدید دریافت کرد! 🌟",
                disable_notification=True  # بی‌صدا
            )

async def send_update_notification(token: str, active_chats: list):
    bot = Bot(token)
    for chat_id in active_chats:
        try:
            await bot.send_message(chat_id=chat_id, text="🎉 ربات آپدیت شد! لطفاً ادامه بدهید.", disable_notification=True)
        except Exception as e:
            logging.info(f"Failed to send update notification to {chat_id}: {e}")

async def main():
    if not TOKEN:
        logger.error("Error: TELEGRAM_BOT_TOKEN environment variable not set.")
        sys.exit(1)
    
    logger.info(f"Using Telegram Bot Token: {TOKEN[:10]}...")
    
    app = Application.builder().token(TOKEN).build()
    
    if 'active_chats' in app.bot_data:
        await send_update_notification(TOKEN, app.bot_data['active_chats'])
        app.bot_data['active_chats'] = []

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    app.add_handler(MessageHandler(filters.LOCATION, handle_location))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    # ConversationHandler setup
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            0: [MessageHandler(filters.CONTACT, handle_contact)],
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_role)],  # Update state 1
            2: [],
            3: []
        },
        fallbacks=[CommandHandler('cancel', start)]
    )
    app.add_handler(conv_handler)
    
    app.job_queue.run_repeating(check_for_updates, interval=10)
    save_timestamp()
    app.post_init = notify_update  # بعد از استارت پیام بفرست
    logger.info("Bot is starting polling...")
    await app.run_polling()

if __name__ == '__main__':
    asyncio.run(main())