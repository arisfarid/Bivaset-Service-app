from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from utils import BASE_URL, log_chat, ensure_active_chat
from keyboards import MAIN_MENU_KEYBOARD, REGISTER_MENU_KEYBOARD, EMPLOYER_MENU_KEYBOARD
from handlers.phone_handler import check_phone
from helpers.menu_manager import MenuManager
import logging

logger = logging.getLogger(__name__)

# تعریف حالت‌ها
START, REGISTER, ROLE, EMPLOYER_MENU = range(4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation with the bot."""
    logger.info(f"=== Entering start function - User: {update.effective_user.id} ===")
    logger.info(f"Current context state: {context.user_data.get('state')}")
    
    # بررسی وضعیت فعلی
    current_state = context.user_data.get('state')
    
    # اگر کاربر در وسط یک فرآیند است (به جز حالت‌های اولیه)
    # اما اگر درخواست restart داشته باشیم، فرآیند را مجدد شروع می‌کنیم
    is_restart = False
    args = context.args
    if args and args[0] == "restart":
        is_restart = True
        logger.info(f"Restart command detected via URL for user {update.effective_user.id}")
    
    if not is_restart and current_state not in [None, START, REGISTER, ROLE]:
        # پاک کردن منوهای قبلی و غیرفعال کردن آنها
        await MenuManager.disable_previous_menus(update, context)
        
        # ارسال پیام هشدار
        confirmation_text = (
            "⚠️ شما در حال حاضر در یک فرآیند فعال هستید.\n"
            "آیا مایل به خروج از فرآیند فعلی و شروع مجدد هستید؟"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ بله، شروع مجدد", callback_data="confirm_restart")],
            [InlineKeyboardButton("❌ خیر، ادامه فرآیند فعلی", callback_data="continue_current")]
        ])
        
        await update.message.reply_text(confirmation_text, reply_markup=keyboard)
        return current_state
    
    # اگر این یک restart است یا در مرحله اولیه هستیم
    await ensure_active_chat(update, context)
    
    # اگر این یک restart است، پیام‌های قبلی را پاک کن
    if is_restart:
        try:
            # با استفاده از متد جدید، پاک کردن پیام‌های قبلی
            await MenuManager.clear_chat_history(update, context)
            logger.info(f"Cleared chat history for user {update.effective_user.id} during restart")
        except Exception as e:
            logger.error(f"Error cleaning chat history during restart: {e}")
    else:
        # پاک کردن تمام منوهای قبلی
        await MenuManager.clear_menus(update, context)
    
    message = update.callback_query.message if update.callback_query else update.message
    if not message:
        logger.error("No message object found in update")
        return REGISTER

    # بررسی وجود شماره تلفن
    has_phone = await check_phone(update, context)
    
    # پاک کردن context کاربر در هنگام راه‌اندازی مجدد یا شروع جدید
    if is_restart:
        context.user_data.clear()
        context.user_data['state'] = REGISTER
    
    if (has_phone):
        # اگر شماره داشت، نمایش منوی اصلی
        context.user_data['state'] = ROLE
        welcome_message = (
            f"👋 سلام {update.effective_user.first_name}! به ربات خدمات بی‌واسط خوش آمدید.\n"
            "لطفاً یکی از گزینه‌ها را انتخاب کنید:"
        )
        # استفاده از MenuManager برای نمایش منو
        await MenuManager.show_menu(
            update, 
            context, 
            welcome_message,
            MAIN_MENU_KEYBOARD,
            reply_markup=ReplyKeyboardRemove()
        )
        return ROLE
    else:
        # اگر شماره نداشت، درخواست ثبت شماره
        await message.reply_text(
            "👋 سلام! برای استفاده از امکانات ربات، لطفاً شماره تلفن خود را به اشتراک بگذارید:",
            reply_markup=REGISTER_MENU_KEYBOARD
        )
        return REGISTER

async def handle_confirm_restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle restart confirmation"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "confirm_restart":
        # پاک کردن وضعیت قبلی
        context.user_data.clear()
        await query.message.delete()
        
        try:
            # پاک کردن تاریخچه چت با استفاده از متد جدید
            await MenuManager.clear_chat_history(update, context)
            logger.info(f"Cleared chat history for user {update.effective_user.id} during confirmed restart")
        except Exception as e:
            logger.error(f"Error cleaning chat history during confirmed restart: {e}")
            # در صورت خطا، از روش قبلی استفاده کنیم
            await MenuManager.clear_menus(update, context)
        
        # نمایش منوی اصلی
        welcome_message = (
            f"👋 سلام {update.effective_user.first_name}! به ربات خدمات بی‌واسط خوش آمدید.\n"
            "لطفاً یکی از گزینه‌ها را انتخاب کنید:"
        )
        
        # استفاده از MenuManager برای نمایش منو
        await MenuManager.show_menu(
            update, 
            context, 
            welcome_message,
            MAIN_MENU_KEYBOARD
        )
        
        context.user_data['state'] = ROLE
        return ROLE
        
    elif query.data == "continue_current":
        # ادامه فرآیند فعلی
        await query.message.delete()
        
        # بازگشت به وضعیت فعلی
        return context.user_data.get('state')

async def handle_role(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle role selection."""
    logger.info(f"=== Entering handle_role - User: {update.effective_user.id} ===")
    logger.info(f"Message text: {update.message.text if update.message else 'None'}")
    logger.info(f"Current state: {context.user_data.get('state')}")
    text = update.message.text if update.message else None
    
    if text == "درخواست خدمات | کارفرما 👔":
        context.user_data['state'] = EMPLOYER_MENU
        
        # پاک کردن تاریخچه چت با استفاده از متد جدید
        try:
            await MenuManager.clear_chat_history(update, context, message_count=15)  # تعداد کمتری پیام را پاک می‌کنیم
            logger.info(f"Cleared partial chat history for user {update.effective_user.id} during role change")
        except Exception as e:
            logger.error(f"Error cleaning chat history during role change: {e}")
            # در صورت خطا، از روش قبلی استفاده کنیم
            await MenuManager.clear_menus(update, context)
        
        employer_message = "🎉 عالیه، {}! می‌خوای خدمات جدید درخواست کنی یا پیشنهادات رو ببینی؟".format(
            update.effective_user.full_name
        )
        
        # استفاده از MenuManager برای نمایش منو
        await MenuManager.show_menu(
            update, 
            context, 
            employer_message,
            EMPLOYER_MENU_KEYBOARD,
            reply_markup=ReplyKeyboardRemove()
        )
        return EMPLOYER_MENU
    
    # اگر پیام غیرمجاز ارسال شد
    from localization import get_message
    lang = context.user_data.get('lang', 'fa')
    await update.message.reply_text(
        get_message("only_select_from_buttons", lang=lang),
        reply_markup=ReplyKeyboardRemove()
    )
    return ROLE

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # پاک کردن تاریخچه چت با استفاده از متد جدید
    try:
        await MenuManager.clear_chat_history(update, context)
        logger.info(f"Cleared chat history for user {update.effective_user.id} during cancel")
    except Exception as e:
        logger.error(f"Error cleaning chat history during cancel: {e}")
        # در صورت خطا، از روش قبلی استفاده کنیم
        await MenuManager.clear_menus(update, context)
    
    context.user_data.clear()
    await update.message.reply_text("عملیات لغو شد. دوباره شروع کن!")
    return ConversationHandler.END