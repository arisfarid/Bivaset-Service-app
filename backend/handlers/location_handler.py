from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from utils import log_chat
import logging
from keyboards import get_location_input_keyboard, get_location_type_keyboard, LOCATION_TYPE_GUIDANCE_TEXT, BACK_TO_DESCRIPTION_KEYBOARD, REMOVE_KEYBOARD
from localization import get_message, get_location_input_guidance_text

logger = logging.getLogger(__name__)

START, REGISTER, ROLE, EMPLOYER_MENU, CATEGORY, SUBCATEGORY, DESCRIPTION, LOCATION_TYPE, LOCATION_INPUT, DETAILS, DETAILS_FILES, DETAILS_DATE, DETAILS_DEADLINE, DETAILS_BUDGET, DETAILS_QUANTITY, SUBMIT, VIEW_PROJECTS, PROJECT_ACTIONS = range(18)
CHANGE_PHONE, VERIFY_CODE = range(20, 22)  # states جدید

# هندلر اصلی مدیریت مرحله انتخاب و دریافت موقعیت مکانی کاربر
# این تابع مسئول مدیریت انتخاب نوع لوکیشن، دریافت لوکیشن، و هدایت به مرحله توضیحات است
async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # دریافت query و message از آپدیت تلگرام
    query = update.callback_query
    message = update.message
    # تعیین state فعلی کاربر (پیش‌فرض LOCATION_TYPE)
    current_state = context.user_data.get('state', LOCATION_TYPE)
    # تعیین زبان کاربر (پیش‌فرض فارسی)
    lang = context.user_data.get('lang', 'fa')
    logger.info(f"Location handler - State: {current_state}")
    
    # اگر کاربر به مرحله انتخاب نوع لوکیشن منتقل شد (چه با callback و چه با state)
    if current_state == LOCATION_TYPE:
        if query and (not query.data or query.data == "continue_to_location"):
            await query.message.edit_text(
                LOCATION_TYPE_GUIDANCE_TEXT,
                reply_markup=get_location_type_keyboard(lang=lang)
            )
            return LOCATION_TYPE
        elif message:
            await message.reply_text(
                LOCATION_TYPE_GUIDANCE_TEXT,
                reply_markup=get_location_type_keyboard(lang=lang)
            )
            return LOCATION_TYPE

    # اگر callback دریافت شده (مثلاً دکمه‌ای کلیک شده)
    if query:
        data = query.data
        logger.info(f"Location handler received callback: {data}")

        # بازگشت به مرحله انتخاب دسته‌بندی
        if data == "back_to_categories":
            logger.info("Returning to category selection")
            context.user_data['state'] = CATEGORY
            return CATEGORY

        # بازگشت به مرحله توضیحات
        if data == "back_to_description":
            logger.info("Returning to description step")
            context.user_data['state'] = DESCRIPTION
            return DESCRIPTION

        # پردازش انتخاب نوع لوکیشن (حضوری یا غیرحضوری)
        elif data.startswith("location_"):
            location_type = data.split("_")[1]
            context.user_data['service_location'] = {
                'client': 'client_site',
                'contractor': 'contractor_site',
                'remote': 'remote'
            }[location_type]

            # اگر کاربر غیرحضوری را انتخاب کند، مستقیماً به مرحله توضیحات هدایت می‌شود
            if location_type == 'remote':
                context.user_data['state'] = DESCRIPTION
                try:
                    from handlers.project_details_handler import send_description_guidance
                    await send_description_guidance(query.message, context)
                except Exception as e:
                    logger.error(f"Error sending description guidance for remote service: {e}")
                    await query.message.edit_text(
                        get_message("description_request", lang=lang),
                        reply_markup=BACK_TO_DESCRIPTION_KEYBOARD
                    )
                return DESCRIPTION
            else:
                # اگر کاربر خدمات حضوری را انتخاب کند، درخواست ارسال لوکیشن می‌شود
                context.user_data['state'] = LOCATION_INPUT
                await query.message.delete()
                await query.message.reply_text(
                    get_message("location_request", lang=lang),
                    reply_markup=get_location_input_keyboard
                )
                return LOCATION_INPUT

        # بازگشت به انتخاب نوع لوکیشن
        elif data == "back_to_location_type":
            context.user_data['state'] = LOCATION_TYPE
            await query.message.edit_text(
                LOCATION_TYPE_GUIDANCE_TEXT,
                reply_markup=get_location_type_keyboard()
            )
            return LOCATION_TYPE

        # رد کردن ارسال لوکیشن و رفتن به مرحله توضیحات
        elif data == "skip_location":
            context.user_data['state'] = DESCRIPTION
            try:
                from handlers.project_details_handler import send_description_guidance
                await send_description_guidance(query.message, context)
            except Exception as e:
                logger.error(f"Error sending description guidance after skipping location: {e}")
                await query.message.edit_text(
                    get_message("description_request", lang=lang),
                    reply_markup=BACK_TO_DESCRIPTION_KEYBOARD
                )
            return DESCRIPTION

    # اگر کاربر موقعیت مکانی خود را ارسال کند
    if update.message and update.message.location:
        location = update.message.location
        context.user_data['location'] = {'longitude': location.longitude, 'latitude': location.latitude}
        logger.info(f"Received location: {context.user_data['location']}")
        context.user_data['state'] = DESCRIPTION
        # نمایش پیام موفقیت و هدایت به مرحله توضیحات
        await update.message.reply_text(
            get_message("location_success", lang=lang),
            reply_markup=REMOVE_KEYBOARD
        )
        try:
            from handlers.project_details_handler import send_description_guidance
            await send_description_guidance(update.message, context)
            logger.info("Successfully sent description guidance")
        except Exception as e:
            logger.error(f"Error sending description guidance: {e}")
            await update.message.reply_text(
                get_message("description_request_full", lang=lang),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(get_message("back", lang=lang), callback_data="back_to_location_type")]
                ])
            )
        return DESCRIPTION

    # اگر پیام متنی دریافت شد (مثلاً کاربر دکمه بازگشت را زد یا متن اشتباه وارد کرد)
    if update.message and update.message.text:
        if update.message.text == get_message("back", lang=lang):
            if current_state == LOCATION_INPUT:
                context.user_data['state'] = LOCATION_TYPE
                # نمایش پیام بازگشت و منوی انتخاب نوع لوکیشن با توجه به زبان کاربر
                await update.message.reply_text(
                    get_message("back_to_previous", lang=lang),
                    reply_markup=REMOVE_KEYBOARD
                )
                await update.message.reply_text(
                    get_message("location_type_guidance", lang=lang),
                    reply_markup=get_location_type_keyboard(lang=lang)
                )
                return LOCATION_TYPE
        # اگر کاربر به جای لوکیشن، متن ارسال کند
        elif current_state == LOCATION_INPUT:
            logger.info(f"Received text instead of location: {update.message.text}")
            service_location_type = context.user_data.get('service_location')
            service_location_name = {
                'client_site': 'محل کارفرما',
                'contractor_site': 'محل مجری'
            }.get(service_location_type, 'حضوری')
            await update.message.reply_text(
                get_message("location_required", lang=lang, service_location_name=service_location_name),
                parse_mode="Markdown",
                reply_markup=get_location_input_keyboard(lang=lang)
            )
            return LOCATION_INPUT

    # اگر کاربر به جای لوکیشن، عکس یا فایل یا پیام غیرمجاز ارسال کند
    if update.message and current_state == LOCATION_INPUT:
        if any([
            update.message.photo,
            update.message.video,
            update.message.audio,
            update.message.document,
            update.message.sticker,
            update.message.voice
        ]):
            logger.info(f"Received non-location content in location input step")
            await update.message.reply_text(
                get_message("location_invalid_type", lang=lang),
                parse_mode="Markdown",
                reply_markup=get_location_input_keyboard(lang=lang)
            )
            return LOCATION_INPUT

    # در غیر این صورت، state فعلی را حفظ کن
    return current_state