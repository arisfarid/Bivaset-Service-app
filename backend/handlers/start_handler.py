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
            chat_id = update.effective_chat.id
            
            # حذف مستقیم پیام‌های اخیر بات - روش جدید و مطمئن
            # پیام‌های آپدیت معمولاً آخرین پیام‌های ارسال شده توسط بات هستند
            # اگر بات فقط جهت ارسال پیام‌های آپدیت راه‌اندازی شده، اولین پیام باید پیام آپدیت باشد
            try:
                # دریافت آخرین پیام‌های بات
                logger.info(f"Attempting to delete update message for chat {chat_id}")
                
                # فرض کنید آخرین پیام بات همان پیام آپدیت است - از بات تلگرام می‌خواهیم تا آخرین پیامش را حذف کند
                # به دلیل محدودیت‌های API، ما نمی‌توانیم پیام‌های اخیر را بخوانیم، 
                # اما می‌توانیم پیام اخیر را با روش مستقیم حذف کنیم
                
                # ابتدا سعی می‌کنیم پیام با ID مشخص را حذف کنیم
                # (این ID بر اساس الگوی رفتاری ربات شما تخمین زده شده و ممکن است نیاز به تنظیم داشته باشد)
                
                # در لاگ‌ها دیده شد که پیام آپدیت احتمالاً آخرین پیام بات قبل از شروع مجدد است
                # احتمالاً message_id یکی کمتر از پیام فعلی /start است
                current_message_id = update.message.message_id
                
                # تخمین ID پیام آپدیت (معمولاً 1-3 پیام قبل از پیام فعلی)
                for offset in range(1, 4):
                    try:
                        possible_update_msg_id = current_message_id - offset
                        logger.info(f"Trying to delete message with ID {possible_update_msg_id}")
                        
                        await context.bot.delete_message(
                            chat_id=chat_id,
                            message_id=possible_update_msg_id
                        )
                        logger.info(f"Successfully deleted message {possible_update_msg_id}")
                        break  # اگر موفق به حذف پیام شدیم، حلقه را متوقف کن
                    except Exception as e:
                        logger.warning(f"Could not delete message {possible_update_msg_id}: {e}")
                        continue
                
            except Exception as e:
                logger.error(f"Error deleting recent bot messages: {e}")
        except Exception as e:
            logger.error(f"Error handling restart command: {e}")
    
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