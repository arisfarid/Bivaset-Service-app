from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from utils import get_categories, get_user_phone, log_chat
import logging
from handlers.location_handler import handle_location
from handlers.start_handler import check_phone
from keyboards import REGISTER_MENU_KEYBOARD, EMPLOYER_MENU_KEYBOARD, CONTRACTOR_MENU_KEYBOARD, MAIN_MENU_KEYBOARD
from asyncio import Lock

logger = logging.getLogger(__name__)

START, REGISTER, ROLE, EMPLOYER_MENU, CATEGORY, SUBCATEGORY, DESCRIPTION, LOCATION_TYPE, LOCATION_INPUT, DETAILS, DETAILS_FILES, DETAILS_DATE, DETAILS_DEADLINE, DETAILS_BUDGET, DETAILS_QUANTITY, SUBMIT, VIEW_PROJECTS, PROJECT_ACTIONS = range(18)

# ایجاد قفل سراسری
message_lock = Lock()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    current_state = context.user_data.get('state', ROLE)
    
    # اگر location ارسال شده
    if update.message.location:
        return await handle_location(update, context)
        
    # بررسی ثبت‌نام
    if not await check_phone(update, context):
        return REGISTER
        
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
        
        # مستقیماً به انتخاب دسته‌بندی برود بدون پیام اضافی
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