import os
import sys
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from utils import save_timestamp, check_for_updates
from handlers.start_handler import start
from handlers.contact_handler import handle_contact
from handlers.location_handler import handle_location
from handlers.photo_handler import handle_photo
from handlers.message_handler import handle_message
from handlers.callback_handler import handle_callback
from handlers.state_handlers import handle_new_project, handle_view_projects, handle_project_details

# غیرفعال کردن لاگ‌های httpx
logging.getLogger('httpx').setLevel(logging.WARNING)

# تنظیم لاگ فقط برای پیام‌های مهم
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.WARNING)
logger = logging.getLogger(__name__)

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

def main():
    if not TOKEN:
        logger.error("Error: TELEGRAM_BOT_TOKEN environment variable not set.")
        sys.exit(1)
    
    logger.info(f"Using Telegram Bot Token: {TOKEN[:10]}...")  # فقط 10 کاراکتر اول توکن رو نشون بده
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    app.add_handler(MessageHandler(filters.LOCATION, handle_location))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.job_queue.run_repeating(check_for_updates, interval=60)  # فاصله چک آپدیت رو به 60 ثانیه افزایش بده
    save_timestamp()
    logger.info("Bot is starting polling...")
    app.run_polling()

if __name__ == '__main__':
    main()