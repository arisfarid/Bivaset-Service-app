from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from handlers.project_details_handler import create_dynamic_keyboard
from utils import log_chat
import logging
from keyboards import LOCATION_TYPE_MENU_KEYBOARD, LOCATION_INPUT_MENU_KEYBOARD, EMPLOYER_MENU_KEYBOARD

logger = logging.getLogger(__name__)

START, REGISTER, ROLE, EMPLOYER_MENU, CATEGORY, SUBCATEGORY, DESCRIPTION, LOCATION_TYPE, LOCATION_INPUT, DETAILS, DETAILS_FILES, DETAILS_DATE, DETAILS_DEADLINE, DETAILS_BUDGET, DETAILS_QUANTITY, SUBMIT, VIEW_PROJECTS, PROJECT_ACTIONS = range(18)

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    current_state = context.user_data.get('state', LOCATION_TYPE)
    text = update.message.text if update.message and update.message.text else None
    location = update.message.location if update.message and update.message.location else None

    # پردازش لوکیشن
    if location:
        context.user_data['location'] = {'longitude': location.longitude, 'latitude': location.latitude}
        await log_chat(update, context)
        if current_state in [LOCATION_TYPE, LOCATION_INPUT]:
            if 'service_location' not in context.user_data or not context.user_data['service_location']:
                await update.message.reply_text(
                    "❌ لطفاً محل انجام خدمات رو انتخاب کن!",
                    reply_markup=LOCATION_TYPE_MENU_KEYBOARD
                )
                return LOCATION_TYPE
            context.user_data['state'] = DETAILS
            await update.message.reply_text(
                "📋 جزئیات درخواست\n"
                "اگه بخوای می‌تونی برای راهنمایی بهتر مجری‌ها این اطلاعات رو هم وارد کنی:",
                reply_markup=create_dynamic_keyboard(context)
            )
            return DETAILS
        await update.message.reply_text("📍 لوکیشن دریافت شد، لطفاً ادامه بده.")
        return current_state

    # حالت انتخاب نوع مکان
    if current_state == LOCATION_TYPE:
        if text == "⬅️ بازگشت":
            context.user_data['state'] = DESCRIPTION
            await update.message.reply_text("🌟 توضیحات خدماتت رو بگو:")
            await log_chat(update, context)
            return DESCRIPTION
        elif text == "➡️ ادامه":
            if 'service_location' not in context.user_data or not context.user_data['service_location']:
                await update.message.reply_text(
                    "❌ لطفاً محل انجام خدمات رو انتخاب کن!",
                    reply_markup=LOCATION_TYPE_MENU_KEYBOARD
                )
                return LOCATION_TYPE
            if context.user_data['service_location'] == 'client_site' and 'location' not in context.user_data:
                await update.message.reply_text(
                    "❌ لطفاً لوکیشن رو ثبت کن!",
                    reply_markup=LOCATION_INPUT_MENU_KEYBOARD
                )
                return LOCATION_TYPE
            context.user_data['state'] = DETAILS
            await update.message.reply_text(
                "📋 جزئیات درخواست\n"
                "اگه بخوای می‌تونی برای راهنمایی بهتر مجری‌ها این اطلاعات رو هم وارد کنی:",
                reply_markup=create_dynamic_keyboard(context)
            )
            return DETAILS
        elif text in ["🏠 محل من", "🔧 محل مجری", "💻 غیرحضوری"]:
            context.user_data['service_location'] = {
                '🏠 محل من': 'client_site',
                '🔧 محل مجری': 'contractor_site',
                '💻 غیرحضوری': 'remote'
            }[text]
            await log_chat(update, context)
            if text == "🏠 محل من":
                context.user_data['state'] = LOCATION_INPUT
                await update.message.reply_text(
                    "📍 برای دریافت قیمت از نزدیک‌ترین مجری، محل انجام خدمات رو از نقشه انتخاب کن:",
                    reply_markup=LOCATION_INPUT_MENU_KEYBOARD
                )
                return LOCATION_INPUT
            else:
                context.user_data['location'] = None
                context.user_data['state'] = DETAILS
                await update.message.reply_text(
                    "📋 جزئیات درخواست:",
                    reply_markup=create_dynamic_keyboard(context)
                )
                return DETAILS
        else:
            await update.message.reply_text(
                "❌ لطفاً گزینه معتبر انتخاب کن!",
                reply_markup=LOCATION_TYPE_MENU_KEYBOARD
            )
            return LOCATION_TYPE

    # حالت ورود لوکیشن
    elif current_state == LOCATION_INPUT:
        if text == "⬅️ بازگشت":
            context.user_data['state'] = LOCATION_TYPE
            await update.message.reply_text(
                "🌟 محل انجام خدماتت رو انتخاب کن:",
                reply_markup=LOCATION_TYPE_MENU_KEYBOARD
            )
            await log_chat(update, context)
            return LOCATION_TYPE
        elif text == "➡️ ادامه":
            if 'location' not in context.user_data:
                await update.message.reply_text(
                    "❌ لطفاً لوکیشن رو ثبت کن!",
                    reply_markup=LOCATION_INPUT_MENU_KEYBOARD
                )
                return LOCATION_INPUT
            context.user_data['state'] = DETAILS
            await update.message.reply_text(
                "📋 جزئیات درخواست\n"
                "اگه بخوای می‌تونی برای راهنمایی بهتر مجری‌ها این اطلاعات رو هم وارد کنی:",
                reply_markup=create_dynamic_keyboard(context)
            )
            return DETAILS
        else:
            # پیام جامع برای هر نوع محتوای غیرلوکیشن
            await update.message.reply_text(
                "❌ لطفاً فقط لوکیشن رو از نقشه بفرست! عکس، ویدیو، متن یا هر چیز دیگه قابل قبول نیست.",
                reply_markup=LOCATION_INPUT_MENU_KEYBOARD
            )
            await log_chat(update, context)
            return LOCATION_INPUT

    return current_state