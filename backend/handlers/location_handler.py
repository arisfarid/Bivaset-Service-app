from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
import logging
from .project_details_handler import create_dynamic_keyboard  # برای بعد از لوکیشن

logger = logging.getLogger(__name__)

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get('state')
    
    # دریافت لوکیشن از پیام
    if update.message and update.message.location:
        location = update.message.location
        context.user_data['location'] = {'longitude': location.longitude, 'latitude': location.latitude}
        if state in ['new_project_location', 'new_project_location_input']:
            if 'service_location' not in context.user_data or not context.user_data['service_location']:
                await update.message.reply_text("❌ لطفاً محل انجام خدمات رو انتخاب کن!")
                return True
            context.user_data['state'] = 'new_project_details'
            await update.message.reply_text(
                f"📋 جزئیات درخواست\n"
                "اگه بخوای می‌تونی برای راهنمایی بهتر مجری‌ها این اطلاعات رو هم وارد کنی:",
                reply_markup=create_dynamic_keyboard(context)
            )
        else:
            await update.message.reply_text("📍 لوکیشن دریافت شد، لطفاً ادامه بده.")
        return True

    # مدیریت انتخاب نوع لوکیشن
    text = update.message.text if update.message else None
    if state == 'new_project_location':
        if text == "⬅️ بازگشت":
            context.user_data['state'] = 'new_project_desc'
            await update.message.reply_text("🌟 توضیحات خدماتت رو بگو:")
            return True
        elif text == "➡️ ادامه":
            if 'service_location' not in context.user_data or not context.user_data['service_location']:
                await update.message.reply_text("❌ لطفاً محل انجام خدمات رو انتخاب کن!")
                return True
            if context.user_data['service_location'] == 'client_site' and 'location' not in context.user_data:
                await update.message.reply_text("❌ لطفاً لوکیشن رو ثبت کن!")
                return True
            context.user_data['state'] = 'new_project_details'
            await update.message.reply_text(
                f"📋 جزئیات درخواست\n"
                "اگه بخوای می‌تونی برای راهنمایی بهتر مجری‌ها این اطلاعات رو هم وارد کنی:",
                reply_markup=create_dynamic_keyboard(context)
            )
            return True
        elif text in ["🏠 محل من", "🔧 محل مجری", "💻 غیرحضوری"]:
            context.user_data['service_location'] = {'🏠 محل من': 'client_site', '🔧 محل مجری': 'contractor_site', '💻 غیرحضوری': 'remote'}[text]
            if text == "🏠 محل من":
                context.user_data['state'] = 'new_project_location_input'
                keyboard = [
                    [KeyboardButton("📍 انتخاب از نقشه", request_location=True), KeyboardButton("📲 ارسال موقعیت فعلی", request_location=True)],
                    [KeyboardButton("⬅️ بازگشت"), KeyboardButton("➡️ ادامه")]
                ]
                await update.message.reply_text(
                    f"📍 برای دریافت قیمت از نزدیک‌ترین مجری، محل انجام خدمات رو از نقشه انتخاب کن:",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
            else:
                context.user_data['location'] = None
                context.user_data['state'] = 'new_project_details'
                await update.message.reply_text(
                    f"📋 جزئیات درخواست:",
                    reply_markup=create_dynamic_keyboard(context)
                )
            return True
        return False

    elif state == 'new_project_location_input':
        if text == "⬅️ بازگشت":
            context.user_data['state'] = 'new_project_location'
            keyboard = [
                [KeyboardButton("🏠 محل من"), KeyboardButton("🔧 محل مجری")],
                [KeyboardButton("💻 غیرحضوری"), KeyboardButton("⬅️ بازگشت")],
                [KeyboardButton("➡️ ادامه")]
            ]
            await update.message.reply_text(
                f"🌟 محل انجام خدماتت رو انتخاب کن:",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            return True
        elif text == "➡️ ادامه":
            if 'location' not in context.user_data:
                await update.message.reply_text("❌ لطفاً لوکیشن رو ثبت کن!")
                return True
            context.user_data['state'] = 'new_project_details'
            await update.message.reply_text(
                f"📋 جزئیات درخواست\n"
                "اگه بخوای می‌تونی برای راهنمایی بهتر مجری‌ها این اطلاعات رو هم وارد کنی:",
                reply_markup=create_dynamic_keyboard(context)
            )
            return True
        return False

    return False