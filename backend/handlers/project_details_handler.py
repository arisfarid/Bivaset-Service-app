from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from telegram.ext import ContextTypes, ConversationHandler
from keyboards import create_dynamic_keyboard, FILE_MANAGEMENT_MENU_KEYBOARD, create_category_keyboard, MAIN_MENU_KEYBOARD
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

        # اضافه کردن callback برای بازگشت به مرحله توضیحات
        elif data == "back_to_description":
            # برگشت به مرحله توضیحات با پیام راهنمای کامل
            context.user_data['state'] = DESCRIPTION
            await send_description_guidance(query.message, context)
            return DESCRIPTION            

    # پردازش پیام‌های متنی
    if message:
        # بررسی نوع محتوای پیام
        if current_state == DESCRIPTION:
            # بررسی محتوای غیر متنی
            if not message.text and any([
                message.photo,
                message.video,
                message.audio,
                message.document,
                message.sticker,
                message.voice,
                message.location
            ]):
                logger.info(f"User {update.effective_user.id} sent non-text content in DESCRIPTION state")
                await message.reply_text(
                    "❌ لطفاً فقط متن توضیحات را وارد کنید.\n\n"
                    "در این مرحله، نیاز داریم توضیحات متنی دقیقی از خدمات موردنظرتان دریافت کنیم.\n"
                    "لطفاً توضیحات خود را به صورت متن بنویسید.",
                    reply_markup=ForceReply(selective=True)
                )
                return DESCRIPTION
                
            # پردازش پیام متنی
            text = message.text
            logger.info(f"Project details text: {text}")

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
                # بررسی کیفیت توضیحات (اختیاری: پیشنهاد بهبود برای توضیحات کوتاه)
                if len(text) < 20:  # اگر توضیحات خیلی کوتاه است
                    await message.reply_text(
                        "⚠️ توضیحات شما کوتاه به نظر می‌رسد.\n\n"
                        "توضیحات کامل‌تر به مجریان کمک می‌کند تا قیمت دقیق‌تری پیشنهاد دهند.\n"
                        "آیا می‌خواهید توضیحات بیشتری اضافه کنید؟\n\n"
                        "اگر توضیحات کامل است، می‌توانید به مرحله بعد بروید.",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("✅ ادامه به مرحله بعد", callback_data="continue_to_details")],
                            [InlineKeyboardButton("✏️ اصلاح توضیحات", callback_data="back_to_description")]
                        ])
                    )
                    # ذخیره توضیحات موقت برای استفاده بعدی
                    context.user_data['temp_description'] = text
                    return DESCRIPTION
                
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

    # اگر وارد حالت توضیحات شدیم، پیام راهنما نمایش بده
    if context.user_data.get('state') == DESCRIPTION and not (message or query):
        await send_description_guidance(update.message or update.callback_query.message, context)
        return DESCRIPTION

    return current_state

# تابع کمکی برای ارسال پیام راهنمای توضیحات
async def send_description_guidance(message, context):
    """ارسال پیام راهنما برای نوشتن توضیحات کامل"""
    
    # دریافت سرویس انتخاب شده برای ارائه مثال مناسب
    category_id = context.user_data.get('category_id')
    categories = context.user_data.get('categories', {})
    category_name = categories.get(category_id, {}).get('name', 'خدمات')
    
    # مثال‌های متناسب با نوع خدمات
    examples = {
        'تعمیر': "مثال: «یخچال سامسونگ مدل X دچار مشکل برفک شده و صدای عجیبی می‌دهد. حدود 3 سال قدمت دارد.»",
        'نظافت': "مثال: «آپارتمان 80 متری با 2 اتاق خواب و سرویس بهداشتی نیاز به نظافت کامل دارد. کف سرامیک است.»",
        'بازسازی': "مثال: «دیوار آشپزخانه نیاز به کاشی‌کاری جدید دارد. متراژ تقریبی 5 متر است و کاشی‌ها توسط خودم تهیه شده.»",
        'نقاشی': "مثال: «برای نقاشی 3 اتاق خواب با سقف کناف نیاز به استادکار دارم. رنگ سفید مات مدنظر است.»",
        'حمل و نقل': "مثال: «نیاز به جابجایی اثاثیه منزل از تهرانپارس به پونک دارم. حدود 20 کارتن و 5 تکه مبلمان است.»"
    }
    
    # انتخاب یک مثال پیش‌فرض اگر دسته‌بندی خاصی با مثال‌ها تطابق نداشت
    example = "مثال: «نیاز به اتو کشی 10 پیراهن و 3 شلوار برای روز سه‌شنبه دارم، ترجیحاً با اتوی بخار»"
    
    # جستجو برای یک مثال مناسب با نوع خدمات
    if category_name:
        for key in examples:
            if key in category_name:
                example = examples[key]
                break
    
    guidance_text = (
        "🌟 *لطفاً توضیحات کاملی از خدمات درخواستی خود بنویسید*\n\n"
        "توضیحات دقیق به مجریان کمک می‌کند تا قیمت دقیق‌تری پیشنهاد دهند و برای شما تجربه بهتری رقم بزنند.\n\n"
        "📝 *توضیحات خوب شامل موارد زیر است:*\n"
        "• جزئیات مشکل یا نیاز شما\n"
        "• ابعاد، مدل یا نوع وسایل\n"
        "• انتظارات شما از نتیجه کار\n"
        "• زمان مورد نظر برای انجام خدمات\n\n"
        f"{example}\n\n"
        "🔍 هرچه توضیحات شما کامل‌تر باشد، مجریان با دقت بیشتری می‌توانند هزینه و زمان اجرا را برآورد کنند."
    )
    
    # ارسال پیام راهنما با ForceReply برای تشویق کاربر به نوشتن
    await message.reply_text(
        guidance_text,
        parse_mode='Markdown',
        reply_markup=ForceReply(selective=True)
    )