from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from telegram.ext import ContextTypes, ConversationHandler
from keyboards import create_dynamic_keyboard, FILE_MANAGEMENT_MENU_KEYBOARD, create_category_keyboard
from utils import clean_budget, validate_date, validate_deadline, log_chat, format_price
from khayyam import JalaliDatetime
from datetime import datetime, timedelta
import logging
from handlers.phone_handler import require_phone


logger = logging.getLogger(__name__)

START, REGISTER, ROLE, EMPLOYER_MENU, CATEGORY, SUBCATEGORY, DESCRIPTION, LOCATION_TYPE, LOCATION_INPUT, DETAILS, DETAILS_FILES, DETAILS_DATE, DETAILS_DEADLINE, DETAILS_BUDGET, DETAILS_QUANTITY, SUBMIT, VIEW_PROJECTS, PROJECT_ACTIONS = range(18)
CHANGE_PHONE, VERIFY_CODE = range(20, 22)  # states جدید

from handlers.submission_handler import submit_project

@require_phone
async def handle_project_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await log_chat(update, context)
    query = update.callback_query
    message = update.message
    current_state = context.user_data.get('state', DESCRIPTION)
    
    logger.info(f"Project details handler - State: {current_state}")

    # پردازش callback ها
    if query:
        data = query.data
        logger.info(f"Project details callback: {data}")

        if data == "back_to_location_type":
            # برگشت به انتخاب نوع لوکیشن
            context.user_data['state'] = LOCATION_TYPE
            keyboard = [
                [InlineKeyboardButton("🏠 محل من", callback_data="location_client")],
                [InlineKeyboardButton("🔧 محل مجری", callback_data="location_contractor")],
                [InlineKeyboardButton("💻 غیرحضوری", callback_data="location_remote")],
                [InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_categories")]
            ]
            await query.message.edit_text(
                "🌟 محل انجام خدماتت رو انتخاب کن:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return LOCATION_TYPE
            
        elif data == "continue_to_details":
            # ادامه به جزئیات
            context.user_data['state'] = DETAILS
            await query.message.edit_text(
                "📋 جزئیات درخواست:\nاگه بخوای می‌تونی برای راهنمایی بهتر مجری‌ها این اطلاعات رو هم وارد کنی:",
                reply_markup=create_dynamic_keyboard(context)
            )
            return DETAILS

    # پردازش پیام‌های متنی
    if message:
        text = message.text
        logger.info(f"Project details text: {text}")

        if current_state == DESCRIPTION:
            if text == "⬅️ بازگشت":
                # برگشت به انتخاب نوع لوکیشن
                context.user_data['state'] = LOCATION_TYPE
                keyboard = [
                    [InlineKeyboardButton("🏠 محل من", callback_data="location_client")],
                    [InlineKeyboardButton("🔧 محل مجری", callback_data="location_contractor")],
                    [InlineKeyboardButton("💻 غیرحضوری", callback_data="location_remote")],
                    [InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_categories")]
                ]
                await message.reply_text(
                    "🌟 محل انجام خدماتت رو انتخاب کن:",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return LOCATION_TYPE
            else:
                # ذخیره توضیحات و رفتن به جزئیات
                context.user_data['description'] = text
                context.user_data['state'] = DETAILS
                await message.reply_text(
                    "📋 جزئیات درخواست\n"
                    "اگه بخوای می‌تونی برای راهنمایی بهتر مجری‌ها این اطلاعات رو هم وارد کنی:",
                    reply_markup=create_dynamic_keyboard(context)
                )
                return DETAILS

        elif current_state == DETAILS:
            if text == "⬅️ بازگشت":
                # برگشت به مرحله توضیحات
                context.user_data['state'] = DESCRIPTION
                last_description = context.user_data.get('description', '')
                await message.reply_text(
                    f"🌟 توضیحات قبلی:\n{last_description}\n\n"
                    "می‌تونی توضیحات رو ویرایش کنی:",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_location_type")]
                    ])
                )
                return DESCRIPTION

        # ادامه کد برای سایر حالت‌های DETAILS

    return current_state