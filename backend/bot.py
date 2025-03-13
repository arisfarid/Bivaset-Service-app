import os
import sys
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, Message, Chat, User
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

from utils import save_timestamp, check_for_updates
from handlers.start_handler import start

# تنظیم لاگ‌ها
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('apscheduler').setLevel(logging.WARNING)

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

async def send_update_notification(token: str, active_chats: list, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Sending update notification to {len(active_chats)} chats")
    for chat_id in active_chats:
        try:
            # دکمه شیشه‌ای برای ری‌استارت
            keyboard = [[InlineKeyboardButton("راه‌اندازی مجدد", callback_data='restart')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(
                chat_id=chat_id,
                text="🎉 ربات آپدیت شد! لطفاً برای ادامه روی دکمه بزنید.",
                reply_markup=reply_markup,
                disable_notification=True
            )
            logger.info(f"Sent update notification to {chat_id}")
        except Exception as e:
            logger.error(f"Failed to send update to {chat_id}: {e}")
    save_timestamp()  # زمان رو ذخیره می‌کنیم تا تکرار نشه

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'restart':
        logger.info(f"Restart requested by {query.from_user.id}")
        # شبیه‌سازی اجرای /start
        await start(update, context)

async def check_and_notify(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Checking for updates...")
    logger.info(f"Bot data: {context.bot_data}")
    if check_for_updates(context.bot_data):
        logger.info("Update detected, sending notifications...")
        active_chats = context.bot_data.get('active_chats', [])
        logger.info(f"Active chats: {active_chats}")
        await send_update_notification(TOKEN, active_chats, context)

if not TOKEN:
    logger.error("Error: TELEGRAM_BOT_TOKEN environment variable not set.")
    sys.exit(1)

logger.info(f"Using Telegram Bot Token: {TOKEN[:10]}...")

app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(handle_callback))

# Add periodic job for update check
app.job_queue.run_repeating(check_and_notify, interval=10, first=0)

logger.info("Bot is starting polling...")
app.run_polling()