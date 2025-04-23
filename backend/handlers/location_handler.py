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
                # اگر غیرحضوری بود مستقیم به مرحله توضیحات برو با راهنمای کامل
                context.user_data['state'] = DESCRIPTION
                
                try:
                    # استفاده از تابع send_description_guidance برای نمایش راهنمای کامل
                    from handlers.project_details_handler import send_description_guidance
                    await send_description_guidance(query.message, context)
                except Exception as e:
                    logger.error(f"Error sending description guidance for remote service: {e}")
                    # اگر خطا رخ داد، همان پیام ساده قبلی نمایش داده شود
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
                    "📍 برای اتصال به نزدیک‌ترین مجری، لطفاً لوکیشن (موقعیت) خود را ارسال کنید:"
                    "\n\nاگر هم اکنون در محل مورد نظرتان برای دریافت خدمات قرار دارید، از دکمه ارسال موقعیت فعلی استفاده کنید یا با استفاده از آیکون 📎 (پیوست) موقعیت دلخواه خود را از نقشه انتخاب کنید.",
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
        
        # ارسال پیام با کیبورد اینلاین برای وارد کردن توضیحات
        try:
            from handlers.project_details_handler import send_description_guidance
            from keyboards import create_restart_keyboard
            
            # ارسال راهنمای توضیحات با دکمه‌های بازگشت و راه‌اندازی مجدد
            success = await send_description_guidance(update.message, context)
            
            # اگر ارسال راهنما موفق نبود، یک پیام ساده با دکمه راه‌اندازی مجدد ارسال کنیم
            if not success:
                restart_keyboard = create_restart_keyboard()
                await update.message.reply_text(
                    "🌟 حالا لطفاً توضیحات کاملی از خدمات درخواستی خود بنویسید:\n\n"
                    "اگر با مشکلی مواجه شدید، می‌توانید از دکمه شروع مجدد استفاده کنید.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_location_type")],
                        [InlineKeyboardButton("🔄 شروع مجدد", callback_data="restart")]
                    ])
                )
            
            logger.info("Successfully sent description guidance")
        except Exception as e:
            # در صورت خطا، یک پیام ساده دستورالعمل با دکمه راه‌اندازی مجدد ارسال کنیم
            logger.error(f"Error sending description guidance: {e}")
            await update.message.reply_text(
                "🌟 حالا لطفاً توضیحات کاملی از خدمات درخواستی خود بنویسید:\n\n"
                "اگر با مشکلی مواجه شدید، می‌توانید از دکمه شروع مجدد استفاده کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_location_type")],
                    [InlineKeyboardButton("🔄 شروع مجدد", callback_data="restart")]
                ])
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
        
        # اگر هر پیام متنی دیگری به جز "بازگشت" ارسال شد و در مرحله ورود لوکیشن هستیم
        elif current_state == LOCATION_INPUT:
            # ثبت لاگ
            logger.info(f"Received text instead of location: {update.message.text}")
            
            # ارسال پیام راهنما به کاربر
            service_location_type = context.user_data.get('service_location')
            service_location_name = {
                'client_site': 'محل کارفرما',
                'contractor_site': 'محل مجری'
            }.get(service_location_type, 'حضوری')
            
            await update.message.reply_text(
                f"❌ لطفاً *موقعیت مکانی* خود را ارسال کنید.\n\n"
                f"برای خدمات در {service_location_name} نیاز به دانستن موقعیت مکانی شما داریم تا مجری مناسب را پیدا کنیم.\n\n"
                f"📱 از دکمه «ارسال موقعیت فعلی» استفاده کنید یا\n"
                f"📎 روی آیکون پیوست (📎) کلیک کرده و گزینه «Location» را انتخاب کنید.",
                parse_mode="Markdown",
                reply_markup=LOCATION_INPUT_KEYBOARD
            )
            # حالت را تغییر نمی‌دهیم تا کاربر دوباره فرصت ارسال لوکیشن داشته باشد
            return LOCATION_INPUT

    # بررسی سایر نوع پیام‌ها (عکس، فایل، استیکر و غیره)
    if update.message and current_state == LOCATION_INPUT:
        # بررسی انواع پیام غیر متنی و غیر لوکیشن
        if any([
            update.message.photo,
            update.message.video,
            update.message.audio,
            update.message.document,
            update.message.sticker,
            update.message.voice
        ]):
            logger.info(f"Received non-location content in location input step")
            
            # ارسال پیام راهنما
            await update.message.reply_text(
                "❌ نوع پیام ارسالی قابل پذیرش نیست.\n\n"
                "لطفاً *فقط موقعیت مکانی* خود را ارسال کنید. این اطلاعات برای یافتن نزدیک‌ترین مجری به شما ضروری است.\n\n"
                "📱 از دکمه «ارسال موقعیت فعلی» استفاده کنید یا\n"
                "📎 روی آیکون پیوست (📎) کلیک کرده و گزینه «Location» را انتخاب کنید.",
                parse_mode="Markdown",
                reply_markup=LOCATION_INPUT_KEYBOARD
            )
            return LOCATION_INPUT

    return current_state