from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from utils import get_categories, get_user_phone, log_chat
import logging
from handlers.category_handler import handle_category_selection
from handlers.location_handler import handle_location
from handlers.attachment_handler import handle_attachment
from handlers.project_details_handler import handle_project_details
from handlers.state_handler import handle_project_states
from handlers.view_handler import handle_view_projects
from keyboards import REGISTER_MENU_KEYBOARD, EMPLOYER_MENU_KEYBOARD, CONTRACTOR_MENU_KEYBOARD, MAIN_MENU_KEYBOARD
from asyncio import Lock

logger = logging.getLogger(__name__)

START, REGISTER, ROLE, EMPLOYER_MENU, CATEGORY, SUBCATEGORY, DESCRIPTION, LOCATION_TYPE, LOCATION_INPUT, DETAILS, DETAILS_FILES, DETAILS_DATE, DETAILS_DEADLINE, DETAILS_BUDGET, DETAILS_QUANTITY, SUBMIT, VIEW_PROJECTS, PROJECT_ACTIONS = range(18)

# ایجاد قفل سراسری
message_lock = Lock()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    
    # بررسی ثبت‌نام
    if not await check_registration(update, context):
        return REGISTER
        
    if text == "درخواست خدمات | کارفرما 👔":
        context.user_data.clear()
        await update.message.reply_text(
            "🎉 عالیه، {}! می‌خوای خدمات جدید درخواست کنی یا پیشنهادات رو ببینی؟".format(
                update.effective_user.full_name
            ),
            reply_markup=EMPLOYER_MENU_KEYBOARD
        )
        return EMPLOYER_MENU
        
    elif text == "📋 درخواست خدمات جدید":
        # دریافت دسته‌بندی‌ها و شروع فرآیند جدید
        categories = await get_categories()
        if not categories:
            await update.message.reply_text("❌ خطا در دریافت دسته‌بندی‌ها")
            return EMPLOYER_MENU
            
        context.user_data['categories'] = categories
        context.user_data['files'] = []
        
        keyboard = create_categories_keyboard(categories)
        await update.message.reply_text(
            "🌟 دسته‌بندی خدماتت رو انتخاب کن:",
            reply_markup=keyboard
        )
        return CATEGORY
    
    return ROLE

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("عملیات لغو شد. دوباره شروع کن!")
    return ConversationHandler.END