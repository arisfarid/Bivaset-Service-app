from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from utils import BASE_URL, log_chat, ensure_active_chat
from keyboards import MAIN_MENU_KEYBOARD, REGISTER_MENU_KEYBOARD, EMPLOYER_MENU_KEYBOARD
from handlers.phone_handler import check_phone
import logging

logger = logging.getLogger(__name__)

# تعریف حالت‌ها
START, REGISTER, ROLE, EMPLOYER_MENU = range(4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation with the bot."""
    logger.info(f"=== Entering start function - User: {update.effective_user.id} ===")
    logger.info(f"Current context state: {context.user_data.get('state')}")
    await ensure_active_chat(update, context)
    context.user_data['state'] = REGISTER
    
    # بررسی آیا این یک شروع مجدد است (از طریق URL)
    args = context.args
    if args and args[0] == "restart":
        logger.info(f"Restart command detected via URL for user {update.effective_user.id}")
        # حذف پیام اطلاع رسانی بروز رسانی ربات
        try:
            chat_id = str(update.effective_chat.id)
            bot_data = context.bot_data
            
            # اگر پیام اطلاع رسانی آپدیت برای این کاربر وجود دارد، آن را حذف کن
            if 'update_messages' in bot_data and chat_id in bot_data['update_messages']:
                message_id = bot_data['update_messages'][chat_id]
                logger.info(f"Deleting update notification message ID {message_id} for chat {chat_id} via /start restart")
                
                try:
                    await context.bot.delete_message(
                        chat_id=int(chat_id),
                        message_id=message_id
                    )
                    # حذف شناسه پیام از دیکشنری
                    del bot_data['update_messages'][chat_id]
                    # به‌روزرسانی داده‌های بات
                    await context.application.persistence.update_bot_data(bot_data)
                    logger.info(f"Deleted update notification message for chat {chat_id} via /start restart")
                except Exception as e:
                    logger.warning(f"Could not delete update message in chat {chat_id}: {e}")
        except Exception as e:
            logger.error(f"Error deleting update notification via /start restart: {e}")
    
    message = update.callback_query.message if update.callback_query else update.message
    if not message:
        logger.error("No message object found in update")
        return REGISTER

    # بررسی وجود شماره تلفن
    has_phone = await check_phone(update, context)
    
    if (has_phone):
        # اگر شماره داشت، نمایش منوی اصلی
        context.user_data['state'] = ROLE
        welcome_message = (
            f"👋 سلام {update.effective_user.first_name}! به ربات خدمات بی‌واسط خوش آمدید.\n"
            "لطفاً یکی از گزینه‌ها را انتخاب کنید:"
        )
        await message.reply_text(welcome_message, reply_markup=MAIN_MENU_KEYBOARD)
        return ROLE
    else:
        # اگر شماره نداشت، درخواست ثبت شماره
        await message.reply_text(
            "👋 سلام! برای استفاده از امکانات ربات، لطفاً شماره تلفن خود را به اشتراک بگذارید:",
            reply_markup=REGISTER_MENU_KEYBOARD
        )
        return REGISTER

async def handle_role(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle role selection."""
    logger.info(f"=== Entering handle_role - User: {update.effective_user.id} ===")
    logger.info(f"Message text: {update.message.text if update.message else 'None'}")
    logger.info(f"Current state: {context.user_data.get('state')}")
    text = update.message.text if update.message else None
    
    if text == "درخواست خدمات | کارفرما 👔":
        context.user_data['state'] = EMPLOYER_MENU
        await update.message.reply_text(
            "🎉 عالیه، {}! می‌خوای خدمات جدید درخواست کنی یا پیشنهادات رو ببینی؟".format(
                update.effective_user.full_name
            ),
            reply_markup=EMPLOYER_MENU_KEYBOARD
        )
        return EMPLOYER_MENU
    
    return ROLE

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("عملیات لغو شد. دوباره شروع کن!")
    return ConversationHandler.END