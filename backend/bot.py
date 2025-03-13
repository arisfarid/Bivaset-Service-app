import os
import sys
import logging
from telegram import KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler
from utils import save_timestamp, check_for_updates
from handlers.start_handler import start
from handlers.contact_handler import handle_contact
from handlers.location_handler import handle_location
from handlers.photo_handler import handle_photo
from handlers.message_handler import handle_message
from handlers.callback_handler import handle_callback
from handlers.new_project_handlers import handle_new_project
from handlers.view_projects_handlers import handle_view_projects
from handlers.project_details_handlers import handle_project_details
from handlers.register_phone_handlers import check_phone  # removed duplicate import
from handlers.role_handler import role_handler

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

def main():
    if not TOKEN:
        logger.error("Error: TELEGRAM_BOT_TOKEN environment variable not set.")
        sys.exit(1)
    
    logger.info(f"Using Telegram Bot Token: {TOKEN[:10]}...")
    
    app = Application.builder().token(TOKEN).build()
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
            0: [MessageHandler(filters.CONTACT, handle_contact), MessageHandler(filters.TEXT, check_phone)],
            1: [MessageHandler(filters.TEXT, role_handler)],
            2: [MessageHandler(filters.TEXT, handle_new_project)],  # Assuming this exists
            3: [MessageHandler(filters.TEXT, handle_view_projects)]  # Assuming this exists
        },
        fallbacks=[CommandHandler('cancel', start)]
    )
    app.add_handler(conv_handler)
    
    app.job_queue.run_repeating(check_for_updates, interval=10)
    save_timestamp()
    app.post_init = notify_update  # بعد از استارت پیام بفرست
    logger.info("Bot is starting polling...")
    app.run_polling()

if __name__ == '__main__':
    main()