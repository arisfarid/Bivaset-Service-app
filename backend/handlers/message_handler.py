from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from utils import get_categories, get_user_phone, log_chat
import logging
from handlers.category_handler import handle_category_selection
from handlers.location_handler import handle_location
from handlers.attachment_handler import handle_attachment
from handlers.project_details_handler import handle_project_details
from handlers.state_handler import handle_project_states
from handlers.start_handler import check_phone
from handlers.view_handler import handle_view_projects
from keyboards import REGISTER_MENU_KEYBOARD, EMPLOYER_MENU_KEYBOARD, CONTRACTOR_MENU_KEYBOARD, MAIN_MENU_KEYBOARD
from asyncio import Lock

logger = logging.getLogger(__name__)

START, REGISTER, ROLE, EMPLOYER_MENU, CATEGORY, SUBCATEGORY, DESCRIPTION, LOCATION_TYPE, LOCATION_INPUT, DETAILS, DETAILS_FILES, DETAILS_DATE, DETAILS_DEADLINE, DETAILS_BUDGET, DETAILS_QUANTITY, SUBMIT, VIEW_PROJECTS, PROJECT_ACTIONS = range(18)

# ایجاد قفل سراسری
message_lock = Lock()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    current_state = context.user_data.get('state', ROLE)
    
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
        # پاک کردن context و تنظیم state جدید
        context.user_data.clear()
        context.user_data['state'] = CATEGORY
        context.user_data['files'] = []
        
        # دریافت دسته‌بندی‌ها
        categories = await get_categories()
        if not categories:
            await update.message.reply_text("❌ خطا در دریافت دسته‌بندی‌ها")
            return EMPLOYER_MENU
            
        context.user_data['categories'] = categories
        root_cats = [cat_id for cat_id, cat in categories.items() if cat['parent'] is None]
        keyboard = [[KeyboardButton(categories[cat_id]['name'])] for cat_id in root_cats]
        keyboard.append([KeyboardButton("⬅️ بازگشت")])
        
        await update.message.reply_text(
            "🌟 دسته‌بندی خدماتت رو انتخاب کن:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        logger.info(f"User {update.effective_user.id} started new request")
        return CATEGORY

    return current_state

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("عملیات لغو شد. دوباره شروع کن!")
    return ConversationHandler.END