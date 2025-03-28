import os
import sys
import logging
import requests
import json  # Add this for json.dump()
from datetime import datetime  # Add this import
from utils import save_timestamp, check_for_updates, BASE_URL
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes, ConversationHandler, PicklePersistence
from handlers.start_handler import start, handle_contact, handle_role, cancel
from handlers.message_handler import handle_message
from handlers.category_handler import handle_category_selection
from handlers.location_handler import handle_location
from handlers.attachment_handler import handle_attachment, handle_photos_command
from handlers.project_details_handler import handle_project_details
from handlers.submission_handler import submit_project
from handlers.state_handler import handle_project_states
from handlers.view_handler import handle_view_projects
from handlers.callback_handler import handle_callback
from keyboards import RESTART_INLINE_MENU_KEYBOARD,MAIN_MENU_KEYBOARD # اضافه شده

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('apscheduler').setLevel(logging.WARNING)

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# تنظیم مسیر ذخیره‌سازی persistence
PERSISTENCE_PATH = os.path.join(os.path.dirname(__file__), 'conversation_data')

# ایجاد persistence handler
persistence = PicklePersistence(
    filepath=PERSISTENCE_PATH,
    store_data={"user_data": True, "chat_data": True, "bot_data": True, "callback_data": False}
)

# ایجاد application با persistence
app = Application.builder()\
    .token(TOKEN)\
    .persistence(persistence)\
    .build()

# تعریف حالت‌ها
START, REGISTER, ROLE, EMPLOYER_MENU, CATEGORY, SUBCATEGORY, DESCRIPTION, LOCATION_TYPE, LOCATION_INPUT, DETAILS, DETAILS_FILES, DETAILS_DATE, DETAILS_DEADLINE, DETAILS_BUDGET, DETAILS_QUANTITY, SUBMIT, VIEW_PROJECTS, PROJECT_ACTIONS = range(18)

async def send_update_and_restart(token: str, active_chats: list, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Starting update and restart for {len(active_chats)} chats")
    updated = False
    for chat_id in active_chats:
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text="🎉 ربات آپدیت شد! لطفاً برای ادامه روی دکمه بزنید.",
                reply_markup=RESTART_INLINE_MENU_KEYBOARD,  # استفاده از کیبورد متمرکز
                disable_notification=True
            )
            logger.info(f"Sent update notification to {chat_id}")
            updated = True
        except Exception as e:
            logger.error(f"Failed to send update to {chat_id}: {e}")
    if active_chats and updated:
        context.bot_data['last_update_processed'] = True
        save_timestamp()

async def check_and_notify(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Checking for updates...")
    logger.info(f"Bot data: {context.bot_data}")
    last_update_processed = context.bot_data.get('last_update_processed', False)
    if check_for_updates(context.bot_data) and not last_update_processed:
        logger.info("Update detected, sending notifications...")
        active_chats = context.bot_data.get('active_chats', [])
        logger.info(f"Active chats: {active_chats}")
        await send_update_and_restart(TOKEN, active_chats, context)

async def test_job(application: Application):
    logger.info("Test job running every 5 seconds")

if not TOKEN:
    logger.error("Error: TELEGRAM_BOT_TOKEN environment variable not set.")
    sys.exit(1)

logger.info(f"Using Telegram Bot Token: {TOKEN[:10]}...")

# تابع کمکی برای لاگ کردن state
async def log_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_state = context.user_data.get('state', START)
    logger.info(f"Processing message for user {update.effective_user.id}, current state: {current_state}")
    return current_state

# Helper function to create MessageHandlers for states
def create_message_handler(callback, additional_filters=None):
    filters_combined = filters.TEXT & ~filters.COMMAND
    if additional_filters:
        filters_combined |= additional_filters
    return MessageHandler(filters_combined, callback)

# تنظیم ConversationHandler
conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler("start", start),
        MessageHandler(filters.Regex("^درخواست خدمات \| کارفرما 👔$"), handle_message)
    ],
    states={
        START: [MessageHandler(filters.TEXT & ~filters.COMMAND, start)],
        
        REGISTER: [MessageHandler(filters.CONTACT, handle_contact)],
        
        ROLE: [
            MessageHandler(filters.Regex("^درخواست خدمات \| کارفرما 👔$"), handle_message),
            MessageHandler(filters.Regex("^پیشنهاد قیمت \| مجری 🦺$"), handle_message),
        ],
        
        EMPLOYER_MENU: [
            MessageHandler(filters.Regex("^📋 درخواست خدمات جدید$"), handle_message),
            MessageHandler(filters.Regex("^📊 مشاهده درخواست‌ها$"), handle_view_projects),
            MessageHandler(filters.Regex("^⬅️ بازگشت$"), lambda u, c: start(u, c)),
        ],
        
        CATEGORY: [
            MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex("^⬅️ بازگشت$"), 
                         handle_category_selection),
            MessageHandler(filters.Regex("^⬅️ بازگشت$"), 
                         lambda u, c: handle_message(u, c)),
        ],
        
        SUBCATEGORY: [
            MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex("^⬅️ بازگشت$"), 
                         handle_category_selection),
            MessageHandler(filters.Regex("^⬅️ بازگشت$"), 
                         lambda u, c: handle_category_selection(u, c)),
        ],
        
        DESCRIPTION: [
            MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex("^⬅️ بازگشت$"), 
                         handle_project_details),
            MessageHandler(filters.Regex("^⬅️ بازگشت$"), 
                         lambda u, c: handle_category_selection(u, c)),
        ],
        
        LOCATION_TYPE: [
            MessageHandler(filters.LOCATION, handle_location),
            MessageHandler(filters.Regex("^(🏠 محل من|🔧 محل مجری|💻 غیرحضوری)$"), handle_location),
            MessageHandler(filters.Regex("^⬅️ بازگشت$"), 
                         lambda u, c: handle_project_details(u, c)),
        ],
        
        DETAILS: [
            MessageHandler(filters.Regex("^✅ ثبت درخواست$"), submit_project),
            MessageHandler(filters.Regex("^(📸|📅|⏳|💰|📏)"), handle_project_details),
            MessageHandler(filters.Regex("^⬅️ بازگشت$"), 
                         lambda u, c: handle_location(u, c)),
        ],
        
        DETAILS_FILES: [
            MessageHandler(filters.PHOTO, handle_attachment),
            MessageHandler(filters.Regex("^🏁 اتمام ارسال تصاویر$"), 
                         lambda u, c: handle_project_details(u, c)),
            MessageHandler(filters.Regex("^⬅️ بازگشت$"), 
                         lambda u, c: handle_project_details(u, c)),
        ],
    },
    fallbacks=[
        CommandHandler("cancel", cancel),
        CallbackQueryHandler(handle_callback),
        MessageHandler(filters.ALL, lambda u, c: ROLE)  # برگشت به منوی اصلی در صورت ورودی نامعتبر
    ],
    name="main_conversation",
    persistent=True,
    allow_reentry=True
)

# اضافه کردن handlerها
app.add_handler(conv_handler)
app.add_handler(CallbackQueryHandler(handle_callback))

# ثبت هندلر جدید برای دستور view_photos
photos_command_handler = MessageHandler(
    filters.Regex(r'^/view_photos_\d+$') & filters.TEXT,
    handle_photos_command
)
app.add_handler(photos_command_handler)
logger.info("Photos command handler registered successfully.")

# اضافه کردن هندلر خطا
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors globally"""
    logger.error(f"Exception while handling an update: {context.error}")
    
    try:
        # پاک کردن context کاربر
        if context and context.user_data:
            context.user_data.clear()
            await context.application.persistence.update_user_data(user_id=update.effective_user.id, data=context.user_data)
        
        # دریافت مجدد دسته‌بندی‌ها
        if str(context.error) == "'categories'":
            context.user_data['categories'] = await get_categories()
            await context.application.persistence.update_user_data(user_id=update.effective_user.id, data=context.user_data)
            
        # ارسال پیام خطا و منوی اصلی
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "🌟 چطور میتونم کمکت کنم؟",
                reply_markup=MAIN_MENU_KEYBOARD
            )
            
        return ROLE
        
    except Exception as e:
        logger.error(f"Error in error handler: {e}")
        return ConversationHandler.END

app.add_error_handler(error_handler)  # اضافه کردن هندلر خطا

# اضافه کردن jobهای تکراری
app.job_queue.run_repeating(test_job, interval=5, first=0, data=app)
app.job_queue.run_repeating(check_and_notify, interval=10, first=0, data=app)

# در bot.py
async def watchdog_job(context: ContextTypes.DEFAULT_TYPE):
    """چک کردن سلامت ربات و ریستارت در صورت نیاز"""
    try:
        # چک کردن وضعیت اتصال به API
        response = requests.get(f"{BASE_URL}health/")
        if response.status_code != 200:
            logger.error("API health check failed. Restarting bot...")
            await restart_bot(context)
    except Exception as e:
        logger.error(f"Watchdog error: {e}")
        await restart_bot(context)

async def restart_bot(context: ContextTypes.DEFAULT_TYPE):
    """ریستارت ربات"""
    try:
        # اطلاع‌رسانی به کاربران فعال
        for chat_id in context.bot_data.get('active_chats', []):
            try:
                # پاک کردن context کاربر قبل از ریستارت
                context.user_data.clear()
                
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="🔄 ربات در حال راه‌اندازی مجدد است.\n"
                         "لطفاً پس از راه‌اندازی مجدد، از منوی اصلی شروع کنید.",
                    reply_markup=MAIN_MENU_KEYBOARD
                )
            except Exception as e:
                logger.error(f"Error notifying user {chat_id}: {e}")
                continue

        # ذخیره وضعیت ربات
        save_bot_state(context)
        
        # ریستارت اپلیکیشن
        os.execv(sys.executable, ['python'] + sys.argv)
    except Exception as e:
        logger.error(f"Error in restart_bot: {e}")

def save_bot_state(context: ContextTypes.DEFAULT_TYPE):
    """ذخیره وضعیت ربات"""
    try:
        with open('bot_state.json', 'w') as f:
            state = {
                'active_chats': context.bot_data.get('active_chats', []),
                'timestamp': datetime.now().timestamp()
            }
            json.dump(state, f)
    except Exception as e:
        logger.error(f"Error saving bot state: {e}")

# اضافه کردن watchdog job
app.job_queue.run_repeating(watchdog_job, interval=300)  # هر 5 دقیقه

logger.info("Bot is starting polling...")
app.run_polling()