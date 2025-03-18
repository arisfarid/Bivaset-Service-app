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

logger = logging.getLogger(__name__)

START, REGISTER, ROLE, EMPLOYER_MENU, CATEGORY, SUBCATEGORY, DESCRIPTION, LOCATION_TYPE, LOCATION_INPUT, DETAILS, DETAILS_FILES, DETAILS_DATE, DETAILS_DEADLINE, DETAILS_BUDGET, DETAILS_QUANTITY, SUBMIT, VIEW_PROJECTS, PROJECT_ACTIONS = range(18)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    telegram_id = str(update.effective_user.id)
    
    # چک کردن ثبت‌نام کاربر
    phone = await get_user_phone(telegram_id)
    logger.info(f"Checking phone in handle_message for {telegram_id}: {phone}")
    if not phone or phone == f"tg_{telegram_id}":
        keyboard = [[KeyboardButton("ثبت شماره تلفن", request_contact=True)]]
        await update.message.reply_text(
            "😊 برای استفاده از ربات، لطفاً اول شماره تلفنت رو ثبت کن!",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        )
        return REGISTER

    await log_chat(update, context)

    # لاگ کردن state فعلی
    current_state = context.user_data.get('state', ROLE)
    logger.info(f"Current state for {telegram_id}: {current_state}")

    if current_state == ROLE:
        if text == "درخواست خدمات | کارفرما 👔":
            context.user_data['state'] = EMPLOYER_MENU
            keyboard = [
                [KeyboardButton("📋 درخواست خدمات جدید"), KeyboardButton("📊 مشاهده درخواست‌ها")],
                [KeyboardButton("⬅️ بازگشت")]
            ]
            await update.message.reply_text(
                "🎉 عالیه، {}! می‌خوای خدمات جدید درخواست کنی یا پیشنهادات رو ببینی؟".format(update.effective_user.full_name),
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            return EMPLOYER_MENU
        elif text == "پیشنهاد قیمت | مجری 🦺":
            keyboard = [
                [KeyboardButton("📋 مشاهده درخواست‌ها"), KeyboardButton("💡 پیشنهاد کار")],
                [KeyboardButton("⬅️ بازگشت")]
            ]
            await update.message.reply_text(
                "🌟 خوبه، {}! می‌خوای درخواست‌های موجود رو ببینی یا پیشنهاد کار بدی؟".format(update.effective_user.full_name),
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            return ROLE  # بعداً برای مجری‌ها گسترش داده بشه
        else:
            await update.message.reply_text("❌ گزینه نامعتبر! لطفاً از منو انتخاب کن.")
            return ROLE
    elif current_state == EMPLOYER_MENU:
        logger.info(f"Processing EMPLOYER_MENU input: {text}")
        if text == "📋 درخواست خدمات جدید":
            context.user_data.clear()
            context.user_data['files'] = []
            context.user_data['categories'] = await get_categories()
            if not context.user_data['categories']:
                await update.message.reply_text("❌ خطا: دسته‌بندی‌ها در دسترس نیست!")
                return EMPLOYER_MENU
            root_cats = [cat_id for cat_id, cat in context.user_data['categories'].items() if cat['parent'] is None]
            keyboard = [[KeyboardButton(context.user_data['categories'][cat_id]['name'])] for cat_id in root_cats] + [[KeyboardButton("⬅️ بازگشت")]]
            await update.message.reply_text(
                "🌟 دسته‌بندی خدماتت رو انتخاب کن:",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            context.user_data['state'] = CATEGORY
            return CATEGORY
        elif text == "📊 مشاهده درخواست‌ها":
            context.user_data['state'] = VIEW_PROJECTS
            await handle_view_projects(update, context)
            return VIEW_PROJECTS
        elif text == "⬅️ بازگشت":
            context.user_data['state'] = ROLE
            keyboard = [["درخواست خدمات | کارفرما 👔"], ["پیشنهاد قیمت | مجری 🦺"]]
            await update.message.reply_text("🌟 چی می‌خوای امروز؟", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
            return ROLE
        else:
            await update.message.reply_text("❌ گزینه نامعتبر! لطفاً از منو انتخاب کن.")
            return EMPLOYER_MENU
    
    # انتقال به handlerهای دیگر بر اساس حالت
    if await handle_category_selection(update, context):
        return context.user_data.get('state', CATEGORY)
    if await handle_location(update, context):
        return context.user_data.get('state', LOCATION_TYPE)
    if await handle_attachment(update, context):
        return context.user_data.get('state', DETAILS_FILES)
    if await handle_project_details(update, context):
        return context.user_data.get('state', DETAILS)
    if await handle_project_states(update, context):
        return context.user_data.get('state', VIEW_PROJECTS)
    
    await update.message.reply_text("❌ گزینه نامعتبر! لطفاً از منو انتخاب کن.")
    return current_state

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("عملیات لغو شد. دوباره شروع کن!")
    return ConversationHandler.END