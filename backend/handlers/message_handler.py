from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from utils import get_categories, get_user_phone, log_chat, ensure_active_chat
import logging
from handlers.location_handler import handle_location
from handlers.start_handler import check_phone
from keyboards import create_category_keyboard, EMPLOYER_MENU_KEYBOARD, CONTRACTOR_MENU_KEYBOARD, MAIN_MENU_KEYBOARD
from asyncio import Lock
from handlers.phone_handler import require_phone

START, REGISTER, ROLE, EMPLOYER_MENU, CATEGORY, SUBCATEGORY, DESCRIPTION, LOCATION_TYPE, LOCATION_INPUT, DETAILS, DETAILS_FILES, DETAILS_DATE, DETAILS_DEADLINE, DETAILS_BUDGET, DETAILS_QUANTITY, SUBMIT, VIEW_PROJECTS, PROJECT_ACTIONS = range(18)
CHANGE_PHONE, VERIFY_CODE = range(20, 22)  # states جدید
logger = logging.getLogger(__name__)

# ایجاد قفل سراسری
message_lock = Lock()
@require_phone
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await ensure_active_chat(update, context)
    current_state = context.user_data.get('state', ROLE)
    
    # Force phone check first
    if not await check_phone(update, context):
        logger.info(f"User {update.effective_user.id} blocked: no phone registered")
        context.user_data['state'] = REGISTER
        return REGISTER
    
    chat_id = update.effective_chat.id
    text = update.message.text
    
    # اضافه کردن به لیست چت‌های فعال
    if 'active_chats' not in context.bot_data:
        context.bot_data['active_chats'] = []
    if chat_id not in context.bot_data['active_chats']:
        context.bot_data['active_chats'].append(chat_id)
        logger.info(f"Added {chat_id} to active chats")
    
    # اگر location ارسال شده
    if update.message.location:
        return await handle_location(update, context)
        
    if text == "درخواست خدمات | کارفرما 👔":
        # پاک کردن context و تنظیم state جدید
        context.user_data.clear()
        context.user_data['state'] = EMPLOYER_MENU
        
        # ارسال منوی کارفرما
        await update.message.reply_text(
            "🎉 عالیه، {}! می‌خوای خدمات جدید درخواست کنی یا پیشنهادات رو ببینی؟".format(
                update.effective_user.full_name
            ),
            reply_markup=EMPLOYER_MENU_KEYBOARD
        )
        logger.info(f"User {update.effective_user.id} entered employer menu")
        return EMPLOYER_MENU

    elif text == "📋 درخواست خدمات جدید":
        context.user_data.clear()
        context.user_data['state'] = CATEGORY
        categories = await get_categories()
        
        if not categories:
            await update.message.reply_text("❌ خطا در دریافت دسته‌بندی‌ها")
            return EMPLOYER_MENU
            
        context.user_data['categories'] = categories
        keyboard = create_category_keyboard(categories)
        
        # حذف پیام "چی میخوای امروز؟" و مستقیماً نمایش دسته‌بندی‌ها
        await update.message.reply_text(
            "🌟 دسته‌بندی خدماتت رو انتخاب کن:",
            reply_markup=keyboard
        )
        return CATEGORY

    return current_state

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("عملیات لغو شد. دوباره شروع کن!")
    return ConversationHandler.END