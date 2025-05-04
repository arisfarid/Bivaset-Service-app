from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from utils import log_chat, delete_previous_messages
import logging
from keyboards import (
    get_location_input_keyboard,
    get_location_type_keyboard,
    BACK_TO_DESCRIPTION_KEYBOARD,
    REMOVE_KEYBOARD,
    get_employer_menu_keyboard,
    create_category_keyboard
)
from localization import get_message
from handlers.states import START, REGISTER, ROLE, EMPLOYER_MENU, CATEGORY, SUBCATEGORY, DESCRIPTION, LOCATION_TYPE, LOCATION_INPUT, DETAILS, DETAILS_FILES, DETAILS_DATE, DETAILS_DEADLINE, DETAILS_BUDGET, DETAILS_QUANTITY, SUBMIT, VIEW_PROJECTS, PROJECT_ACTIONS, CHANGE_PHONE, VERIFY_CODE
import asyncio

logger = logging.getLogger(__name__)

# هندلر اصلی مدیریت مرحله انتخاب و دریافت موقعیت مکانی کاربر
# این تابع مسئول مدیریت انتخاب نوع لوکیشن، دریافت لوکیشن، و هدایت به مرحله توضیحات است
async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # حذف ۳ پیام آخر (چه از ربات چه از کاربر)
    await delete_previous_messages(update, context, n=3)
    # دریافت query و message از آپدیت تلگرام
    query = update.callback_query
    message = update.message
    # تعیین state فعلی کاربر (پیش‌فرض LOCATION_TYPE)
    current_state = context.user_data.get('state', LOCATION_TYPE)
    # تعیین زبان کاربر (پیش‌فرض فارسی)
    lang = context.user_data.get('lang', 'fa')
    logger.info(f"handle_location called. current_state={current_state}, message={update.message}")
    if update.message:
        logger.info(f"update.message.text={getattr(update.message, 'text', None)} | photo={bool(getattr(update.message, 'photo', None))} | video={bool(getattr(update.message, 'video', None))} | document={bool(getattr(update.message, 'document', None))}")
    logger.info(f"Location handler - State: {current_state}")
    
    # اگر کاربر به مرحله انتخاب نوع لوکیشن منتقل شد (چه با callback و چه با state)
    if current_state == LOCATION_TYPE:
        if query and (not query.data or query.data == "continue_to_location"):
            sent = await query.message.edit_text(
                get_message("location_type_guidance", lang=lang),
                reply_markup=get_location_type_keyboard(lang=lang),
                parse_mode="Markdown"
            )
            return LOCATION_TYPE
        elif message:
            sent = await message.reply_text(
                get_message("location_type_guidance", lang=lang),
                reply_markup=get_location_type_keyboard(lang=lang),
                parse_mode="Markdown"
            )
            await delete_previous_messages(sent, context, n=3)
            return LOCATION_TYPE

    # اگر callback دریافت شده (مثلاً دکمه‌ای کلیک شده)
    if query:
        data = query.data
        logger.info(f"Location handler received callback: {data}")

        # بازگشت به مرحله انتخاب دسته‌بندی
        if data == "back_to_categories":
            logger.info("Returning to category selection")
            context.user_data['state'] = CATEGORY
            # Instead of calling handle_category_selection directly, just show the category selection menu
            categories = context.user_data.get('categories', {})
            keyboard = create_category_keyboard(categories)
            await query.message.edit_text(
                get_message("category_main_select", lang=lang),
                reply_markup=keyboard
            )
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

            # اگر کاربر غیرحضوری را انتخاب کند، مستقیماً به مرحله توضیحات هدایت شود
            if location_type == 'remote':
                context.user_data['state'] = DESCRIPTION
                await query.message.edit_text(
                    get_message("remote_service_selected", lang=lang) + "\n\n" + 
                    get_message("enter_description", lang=lang),
                    reply_markup=BACK_TO_DESCRIPTION_KEYBOARD
                )
                return DESCRIPTION
            else:
                # اگر کاربر خدمات حضوری را انتخاب کند، درخواست ارسال لوکیشن می‌شود
                context.user_data['state'] = LOCATION_INPUT
                await query.message.delete()
                sent = await query.message.reply_text(
                    get_message("location_request", lang=lang),
                    reply_markup=get_location_input_keyboard(lang=lang)
                )
                await delete_previous_messages(sent, context, n=3)
                return LOCATION_INPUT

        # بازگشت به انتخاب نوع لوکیشن
        elif data == "back_to_location_type":
            context.user_data['state'] = LOCATION_TYPE
            sent = await query.message.edit_text(
                get_message("location_type_guidance", lang=lang),
                reply_markup=get_location_type_keyboard(),
                parse_mode="Markdown"
            )
            await delete_previous_messages(sent, context, n=3)
            return LOCATION_TYPE

        # رد کردن ارسال لوکیشن و رفتن به مرحله توضیحات
        elif data == "skip_location":
            context.user_data['state'] = DESCRIPTION
            await delete_previous_messages(sent, context, n=3)
            return DESCRIPTION

    # اگر کاربر موقعیت مکانی خود را ارسال کند
    if update.message and update.message.location:
        location = update.message.location
        context.user_data['location'] = {'longitude': location.longitude, 'latitude': location.latitude}
        logger.info(f"Received location: {context.user_data['location']}")
        context.user_data['state'] = DESCRIPTION
        # نمایش پیام موفقیت و هدایت به مرحله توضیحات
        sent = await update.message.reply_text(
            get_message("location_success", lang=lang),
            reply_markup=REMOVE_KEYBOARD
        )
        await delete_previous_messages(sent, context, n=3)
        return DESCRIPTION

    # اگر پیام متنی یا غیرمتنی دریافت شد (در مرحله LOCATION_INPUT)
    if update.message and current_state == LOCATION_INPUT:
        # اگر عکس، ویدیو، فایل، استیکر یا ویس ارسال شد (حتی اگر متن نداشته باشد)
        if any([
            update.message.photo,
            update.message.video,
            update.message.audio,
            update.message.document,
            update.message.sticker,
            update.message.voice
        ]):
            logger.info(f"Received non-location content in location input step")
            sent = await update.message.reply_text(
                get_message("location_invalid_type", lang=lang),
                parse_mode="Markdown",
                reply_markup=get_location_input_keyboard(lang=lang)
            )
            await delete_previous_messages(sent, context, n=3)
            return LOCATION_INPUT
        # اگر متن بازگشت ارسال شد
        if update.message.text and update.message.text == get_message("back", lang=lang):
            context.user_data['state'] = LOCATION_TYPE
            sent = await update.message.reply_text(
                get_message("back_to_previous", lang=lang),
                reply_markup=REMOVE_KEYBOARD
            )
            await delete_previous_messages(sent, context, n=3)
            sent2 = await update.message.reply_text(
                get_message("location_type_guidance", lang=lang),
                reply_markup=get_location_type_keyboard(lang=lang),
                parse_mode="Markdown"
            )
            await delete_previous_messages(sent2, context, n=3)
            return LOCATION_TYPE
        # اگر متن ارسال شد (و متن بازگشت نبود)
        elif update.message.text:
            logger.info(f"Received text instead of location: {update.message.text}")
            sent = await update.message.reply_text(
                get_message("location_invalid_type", lang=lang),
                parse_mode="Markdown",
                reply_markup=get_location_input_keyboard(lang=lang)
            )
            await delete_previous_messages(sent, context, n=3)
            return LOCATION_INPUT

    # در غیر این صورت، state فعلی را حفظ کن
    return current_state
