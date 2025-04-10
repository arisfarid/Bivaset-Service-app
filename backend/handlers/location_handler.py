from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from utils import log_chat
import logging
from keyboards import create_dynamic_keyboard, LOCATION_TYPE_MENU_KEYBOARD, LOCATION_INPUT_MENU_KEYBOARD

logger = logging.getLogger(__name__)

START, REGISTER, ROLE, EMPLOYER_MENU, CATEGORY, SUBCATEGORY, DESCRIPTION, LOCATION_TYPE, LOCATION_INPUT, DETAILS, DETAILS_FILES, DETAILS_DATE, DETAILS_DEADLINE, DETAILS_BUDGET, DETAILS_QUANTITY, SUBMIT, VIEW_PROJECTS, PROJECT_ACTIONS = range(18)
CHANGE_PHONE, VERIFY_CODE = range(20, 22)  # states جدید

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle location selection and input"""
    current_state = context.user_data.get('state', LOCATION_TYPE)
    query = update.callback_query
    message = update.message
    
    # اگر callback دریافت شده
    if query:
        data = query.data
        logger.info(f"Location handler received callback: {data}")

        if data == "back_to_description":
            logger.info("Returning to description state")
            context.user_data['state'] = DESCRIPTION
            await query.message.edit_text(
                "🌟 توضیحات خدماتت رو بگو:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_categories")]
                ])
            )
            return DESCRIPTION

        elif data.startswith("location_"):
            location_type = data.split("_")[1]
            context.user_data['service_location'] = {
                'client': 'client_site',
                'contractor': 'contractor_site',
                'remote': 'remote'
            }[location_type]

            if location_type == 'remote':
                context.user_data['state'] = DETAILS
                await query.message.edit_text(
                    "📋 جزئیات درخواست\n"
                    "اگه بخوای می‌تونی برای راهنمایی بهتر مجری‌ها این اطلاعات رو هم وارد کنی:",
                    reply_markup=create_dynamic_keyboard(context)
                )
                return DETAILS
            else:
                context.user_data['state'] = LOCATION_INPUT
                await query.message.edit_text(
                    "📍 برای اتصال به نزدیک‌ترین مجری، لطفاً لوکیشن خود را ارسال کنید:",
                    reply_markup=LOCATION_INPUT_MENU_KEYBOARD
                )
                return LOCATION_INPUT

        return current_state

    # اگر پیام متنی یا لوکیشن دریافت شده
    text = message.text if message else None
    location = message.location if message else None

    # اگر location دریافت شد
    if location:
        try:
            context.user_data['location'] = {
                'longitude': location.longitude,
                'latitude': location.latitude
            }
            context.user_data['state'] = DETAILS
            await message.reply_text(
                "📋 جزئیات درخواست:\n"
                "اگه بخوای می‌تونی برای راهنمایی بهتر مجری‌ها این اطلاعات رو هم وارد کنی:",
                reply_markup=create_dynamic_keyboard(context)
            )
            return DETAILS

        except Exception as e:
            logger.error(f"Error handling location: {e}")
            await message.reply_text(
                "❌ خطا در ثبت لوکیشن. لطفاً دوباره تلاش کنید.",
                reply_markup=LOCATION_INPUT_MENU_KEYBOARD
            )
            return current_state

    # پردازش دکمه‌های برگشت و ادامه
    if text in ["⬅️ بازگشت", "➡️ ادامه"]:
        if current_state == LOCATION_TYPE:
            if text == "⬅️ بازگشت":
                context.user_data['state'] = DESCRIPTION
                await message.reply_text(
                    "🌟 توضیحات خدماتت رو بگو:",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_categories")]
                    ])
                )
                return DESCRIPTION

            elif text == "➡️ ادامه":
                if 'service_location' not in context.user_data:
                    await message.reply_text(
                        "❌ لطفاً محل انجام خدمات رو انتخاب کن!",
                        reply_markup=LOCATION_TYPE_MENU_KEYBOARD
                    )
                    return LOCATION_TYPE

                if context.user_data['service_location'] in ['client_site', 'contractor_site'] and 'location' not in context.user_data:
                    await message.reply_text(
                        "❌ برای خدمات حضوری، ارسال لوکیشن اجباری است!",
                        reply_markup=LOCATION_INPUT_MENU_KEYBOARD
                    )
                    return LOCATION_INPUT

                context.user_data['state'] = DETAILS
                await message.reply_text(
                    "📋 جزئیات درخواست\n"
                    "اگه بخوای می‌تونی برای راهنمایی بهتر مجری‌ها این اطلاعات رو هم وارد کنی:",
                    reply_markup=create_dynamic_keyboard(context)
                )
                return DETAILS

        elif current_state == LOCATION_INPUT:
            if text == "⬅️ بازگشت":
                context.user_data['state'] = LOCATION_TYPE
                await message.reply_text(
                    "🌟 محل انجام خدماتت رو انتخاب کن:",
                    reply_markup=LOCATION_TYPE_MENU_KEYBOARD
                )
                return LOCATION_TYPE

            elif text == "➡️ ادامه":
                if context.user_data.get('service_location') in ['client_site', 'contractor_site'] and 'location' not in context.user_data:
                    await message.reply_text(
                        "❌ برای خدمات حضوری، ارسال لوکیشن اجباری است!",
                        reply_markup=LOCATION_INPUT_MENU_KEYBOARD
                    )
                    return LOCATION_INPUT

                context.user_data['state'] = DETAILS
                await message.reply_text(
                    "📋 جزئیات درخواست\n"
                    "اگه بخوای می‌تونی برای راهنمایی بهتر مجری‌ها این اطلاعات رو هم وارد کنی:",
                    reply_markup=create_dynamic_keyboard(context)
                )
                return DETAILS

    # اگر متن نامعتبر دریافت شده
    await message.reply_text(
        "❌ لطفاً از دکمه‌های موجود استفاده کنید یا لوکیشن ارسال کنید.",
        reply_markup=LOCATION_INPUT_MENU_KEYBOARD if current_state == LOCATION_INPUT else LOCATION_TYPE_MENU_KEYBOARD
    )
    return current_state