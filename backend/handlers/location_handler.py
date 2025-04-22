from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from utils import log_chat
import logging
from keyboards import create_category_keyboard, LOCATION_TYPE_MENU_KEYBOARD, LOCATION_INPUT_KEYBOARD, LOCATION_INPUT_MENU_KEYBOARD, BACK_TO_DESCRIPTION_KEYBOARD, REMOVE_KEYBOARD

logger = logging.getLogger(__name__)

START, REGISTER, ROLE, EMPLOYER_MENU, CATEGORY, SUBCATEGORY, DESCRIPTION, LOCATION_TYPE, LOCATION_INPUT, DETAILS, DETAILS_FILES, DETAILS_DATE, DETAILS_DEADLINE, DETAILS_BUDGET, DETAILS_QUANTITY, SUBMIT, VIEW_PROJECTS, PROJECT_ACTIONS = range(18)
CHANGE_PHONE, VERIFY_CODE = range(20, 22)  # states جدید

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle location selection and input"""
    query = update.callback_query
    message = update.message
    current_state = context.user_data.get('state', LOCATION_TYPE)
    logger.info(f"Location handler - State: {current_state}")
    
    # اگر callback دریافت شده
    if query:
        data = query.data
        logger.info(f"Location handler received callback: {data}")

        # برگشت به مرحله قبل
        if data == "back_to_categories":
            logger.info("Returning to category selection")
            categories = context.user_data.get('categories', {})
            category_id = context.user_data.get('category_id')
            if category_id:
                category = categories.get(category_id)
                if category and category.get('parent'):
                    # برگشت به زیردسته‌ها
                    parent = categories.get(category['parent'])
                    keyboard = []
                    for child_id in parent.get('children', []):
                        child = categories.get(child_id)
                        if child:
                            keyboard.append([
                                InlineKeyboardButton(
                                    child['name'],
                                    callback_data=f"subcat_{child_id}"
                                )
                            ])
                    keyboard.append([InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_categories")])
                    await query.message.edit_text(
                        f"📋 زیرمجموعه {parent['name']} را انتخاب کنید:",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                else:
                    # برگشت به دسته‌های اصلی
                    keyboard = create_category_keyboard(categories)
                    await query.message.edit_text(
                        "🌟 دسته‌بندی خدماتت رو انتخاب کن:",
                        reply_markup=keyboard
                    )
            context.user_data['state'] = CATEGORY
            return CATEGORY

        # پردازش انتخاب نوع لوکیشن
        elif data.startswith("location_"):
            location_type = data.split("_")[1]
            context.user_data['service_location'] = {
                'client': 'client_site',
                'contractor': 'contractor_site',
                'remote': 'remote'
            }[location_type]

            if location_type == 'remote':
                # اگر غیرحضوری بود مستقیم به مرحله توضیحات برو
                context.user_data['state'] = DESCRIPTION
                await query.message.edit_text(
                    "🌟 توضیحات خدماتت رو بگو:",
                    reply_markup=BACK_TO_DESCRIPTION_KEYBOARD
                )
                return DESCRIPTION
            else:
                # برای خدمات حضوری درخواست لوکیشن با کیبورد معمولی
                context.user_data['state'] = LOCATION_INPUT
                
                # حذف پیام قبلی و ارسال پیام جدید با کیبورد مناسب
                await query.message.delete()
                await query.message.reply_text(
                    "📍 برای اتصال به نزدیک‌ترین مجری، لطفاً لوکیشن خود را ارسال کنید:"
                    "\n\nشما می‌توانید از دکمه ارسال موقعیت فعلی استفاده کنید یا با استفاده از آیکون 📎 (پیوست) لوکیشن دلخواه خود را از نقشه انتخاب کنید.",
                    reply_markup=LOCATION_INPUT_KEYBOARD
                )
                return LOCATION_INPUT

        # برگشت به انتخاب نوع لوکیشن
        elif data == "back_to_location_type":
            context.user_data['state'] = LOCATION_TYPE
            await query.message.edit_text(
                "🌟 محل انجام خدماتت رو انتخاب کن:",
                reply_markup=LOCATION_TYPE_MENU_KEYBOARD
            )
            return LOCATION_TYPE

        # رد کردن ارسال لوکیشن
        elif data == "skip_location":
            context.user_data['state'] = DESCRIPTION
            await query.message.edit_text(
                "🌟 توضیحات خدماتت رو بگو:",
                reply_markup=BACK_TO_DESCRIPTION_KEYBOARD
            )
            return DESCRIPTION

    # اگر لوکیشن دریافت شد
    if update.message and update.message.location:
        location = update.message.location
        context.user_data['location'] = {'longitude': location.longitude, 'latitude': location.latitude}
        logger.info(f"Received location: {context.user_data['location']}")
        context.user_data['state'] = DESCRIPTION
        
        # بازگشت به کیبورد اینلاین
        await update.message.reply_text(
            "✅ موقعیت مکانی شما با موفقیت دریافت شد!",
            reply_markup=REMOVE_KEYBOARD
        )
        
        await update.message.reply_text(
            "🌟 توضیحات خدماتت رو بگو:",
            reply_markup=BACK_TO_DESCRIPTION_KEYBOARD
        )
        return DESCRIPTION

    # اگر پیام متنی دریافت شد (مثلاً برگشت)
    if update.message and update.message.text:
        if update.message.text == "⬅️ بازگشت":
            if current_state == LOCATION_INPUT:
                context.user_data['state'] = LOCATION_TYPE
                
                # حذف کیبورد مخصوص لوکیشن
                await update.message.reply_text(
                    "برگشت به مرحله قبل...",
                    reply_markup=REMOVE_KEYBOARD
                )
                
                # نمایش منوی انتخاب نوع لوکیشن
                await update.message.reply_text(
                    "🌟 محل انجام خدماتت رو انتخاب کن:",
                    reply_markup=LOCATION_TYPE_MENU_KEYBOARD
                )
                return LOCATION_TYPE

    return current_state