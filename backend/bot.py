import os
import sys
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from utils import save_timestamp, check_for_updates
from handlers.start_handler import start
from handlers.contact_handler import handle_contact
from handlers.location_handler import handle_location
from handlers.photo_handler import handle_photo
from handlers.message_handler import handle_message
from handlers.callback_handler import handle_callback

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

def main():
    if not TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN environment variable not set.")
        sys.exit(1)
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    app.add_handler(MessageHandler(filters.LOCATION, handle_location))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.job_queue.run_repeating(check_for_updates, interval=10)
    save_timestamp()
    app.run_polling()

if __name__ == '__main__':
    main()