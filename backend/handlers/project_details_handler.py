from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ForceReply, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler
from keyboards import create_dynamic_keyboard, get_file_management_menu_keyboard, create_category_keyboard, get_main_menu_keyboard, get_location_type_keyboard, get_date_selection_keyboard, get_deadline_selection_keyboard, get_budget_selection_keyboard, get_quantity_selection_keyboard, get_custom_input_keyboard
from utils import clean_budget, validate_date, validate_deadline, log_chat, format_price
from khayyam import JalaliDatetime
from datetime import datetime, timedelta
import logging
from handlers.phone_handler import require_phone
from handlers.submission_handler import submit_project
from handlers.attachment_handler import handle_photo_navigation, init_photo_management
from handlers.states import START, REGISTER, ROLE, EMPLOYER_MENU, CATEGORY, SUBCATEGORY, DESCRIPTION, LOCATION_TYPE, LOCATION_INPUT, DETAILS, DETAILS_FILES, DETAILS_DATE, DETAILS_DEADLINE, DETAILS_BUDGET, DETAILS_QUANTITY, SUBMIT, VIEW_PROJECTS, PROJECT_ACTIONS, CHANGE_PHONE, VERIFY_CODE
from localization import get_message
from handlers.navigation_utils import add_navigation_to_message, SERVICE_REQUEST_FLOW
from functools import wraps
import json
import os

logger = logging.getLogger(__name__)

async def description_handler(message, context: ContextTypes.DEFAULT_TYPE, update: Update):
    """
    ارسال پیام راهنمای کامل برای مرحله وارد کردن توضیحات
    """
    # دریافت توضیحات قبلی اگر موجود باشد
    last_description = context.user_data.get('description', context.user_data.get('temp_description', ''))
    
    # اگر توضیحات قبلی موجود باشد، آن را نمایش می‌دهیم
    guidance_text = get_message("description_guidance", context, update)
    if last_description:
        guidance_text += get_message("previous_description_with_confirm", context, update)
    else:
        guidance_text += get_message("write_description_prompt", context, update)
    
    # افزودن اطلاعات ناوبری به پیام
    guidance_text, navigation_keyboard = add_navigation_to_message(guidance_text, DESCRIPTION, context.user_data, context, update)
    
    # اگر توضیحات قبلی داریم، دکمه‌های تأیید را اضافه می‌کنیم
    if last_description:
        keyboard = [
            [InlineKeyboardButton(get_message("confirm_and_continue", context, update), callback_data="continue_to_details")],
            [InlineKeyboardButton(get_message("back", context, update), callback_data="back_to_location_type")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton(get_message("back", context, update), callback_data="back_to_location_type")]
        ]
      # اگر navigation keyboard داریم، آن را ادغام می‌کنیم
    if navigation_keyboard:
        keyboard += navigation_keyboard.inline_keyboard
    
    await message.edit_text(
        guidance_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

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
            await query.message.edit_text(
                get_message("location_type_guidance", context, update),
                reply_markup=get_location_type_keyboard(context, update),
                parse_mode="Markdown"
            )
            return LOCATION_TYPE
            
        elif data == "continue_to_details":
            # ادامه به جزئیات
            
            # اگر توضیحات موقت داریم، آن را به عنوان توضیحات اصلی ذخیره کنیم
            if 'temp_description' in context.user_data:
                context.user_data['description'] = context.user_data['temp_description']
                # حذف توضیحات موقت بعد از ذخیره
                del context.user_data['temp_description']
            
            context.user_data['state'] = DETAILS
            message_text = get_message("project_details", context, update)
            
            # افزودن اطلاعات ناوبری به پیام
            message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS, context.user_data, context, update)
            
            # اگر navigation keyboard داریم، آن را ادغام کنیم با کیبورد اصلی
            if navigation_keyboard:
                dynamic_keyboard = create_dynamic_keyboard(context, update)
                # ادغام دکمه‌های ناوبری با کیبورد اصلی
                keyboard_rows = dynamic_keyboard.inline_keyboard
                keyboard_rows.extend(navigation_keyboard.inline_keyboard)
                await query.message.edit_text(message_text, reply_markup=InlineKeyboardMarkup(keyboard_rows))
            else:
                await query.message.edit_text(message_text, reply_markup=create_dynamic_keyboard(context, update))
                
            return DETAILS

        # اضافه کردن callback برای بازگشت به مرحله توضیحات
        elif data == "back_to_description":
            # برگشت به مرحله توضیحات با پیام راهنمای کامل
            context.user_data['state'] = DESCRIPTION
            await description_handler(query.message, context, update)
            return DESCRIPTION
        
        # پردازش مدیریت فایل ها و بازگشت به جزئیات
        elif data == "finish_files" or data == "manage_photos" or data == "back_to_details":
            return await handle_photo_navigation(update, context, data)
        
        # پردازش انتخاب مدیریت عکس‌ها
        elif data == "photo_management" or data == get_message("images_button", context, update) or data == "manage_photos":
            return await init_photo_management(update, context)
        
        # پردازش ورود تاریخ نیاز
        elif data == "need_date" or data == get_message("need_date_button", context, update):
            context.user_data['state'] = DETAILS_DATE
            message_text = get_message("select_need_date_prompt", context, update)
            message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS_DATE, context.user_data, context, update)
            
            keyboard = get_date_selection_keyboard(context, update).inline_keyboard
            if navigation_keyboard:
                keyboard.extend(navigation_keyboard.inline_keyboard)
                
            await query.message.edit_text(
                message_text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return DETAILS_DATE
        
        # پردازش انتخاب تاریخ‌های پیش‌فرض
        elif data.startswith("date_"):
            parts = data.split("_")
            if len(parts) >= 3:
                date_type = parts[1]
                
                if date_type == "custom":
                    # نمایش پیام برای ورود تاریخ دستی
                    message_text = get_message("enter_custom_date_prompt", context, update)
                    message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS_DATE, context.user_data, context, update)
                    
                    keyboard = get_custom_input_keyboard(context, update).inline_keyboard
                    if navigation_keyboard:
                        keyboard.extend(navigation_keyboard.inline_keyboard)
                        
                    await query.message.edit_text(
                        message_text,
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                    await query.answer()
                    return DETAILS_DATE
                
                # استخراج تاریخ از callback data
                date_str = '_'.join(parts[2:]).replace('_', '/')
                context.user_data['need_date'] = date_str
                context.user_data['state'] = DETAILS
                
                message_text = get_message("need_date_saved", context, update)
                message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS, context.user_data, context, update)
                
                keyboard = create_dynamic_keyboard(context, update).inline_keyboard
                if navigation_keyboard:
                    keyboard.extend(navigation_keyboard.inline_keyboard)
                    
                await query.message.edit_text(
                    message_text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                await query.answer(get_message("date_saved_success", context, update))
                return DETAILS
        
        # پردازش ورود مهلت انجام
        elif data == "deadline" or data == get_message("deadline_button", context, update):
            context.user_data['state'] = DETAILS_DEADLINE
            message_text = get_message("select_deadline_prompt", context, update)
            message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS_DEADLINE, context.user_data, context, update)
            
            keyboard = get_deadline_selection_keyboard(context, update).inline_keyboard
            if navigation_keyboard:
                keyboard.extend(navigation_keyboard.inline_keyboard)
                
            await query.message.edit_text(
                message_text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return DETAILS_DATE
        
        # پردازش انتخاب مهلت انجام
        elif data.startswith("deadline_"):
            parts = data.split("_")
            if len(parts) == 2:
                if parts[1] == "custom":
                    # نمایش پیام برای ورود مهلت دستی
                    message_text = get_message("enter_custom_deadline_prompt", context, update)
                    message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS_DEADLINE, context.user_data, context, update)
                    
                    keyboard = get_custom_input_keyboard(context, update).inline_keyboard
                    if navigation_keyboard:
                        keyboard.extend(navigation_keyboard.inline_keyboard)
                        
                    await query.message.edit_text(
                        message_text,
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                    await query.answer()
                    return DETAILS_DEADLINE
                
                # استخراج مهلت از callback data
                deadline = validate_deadline(parts[1])
                if deadline:
                    context.user_data['deadline'] = deadline
                    context.user_data['state'] = DETAILS
                    
                    message_text = get_message("deadline_saved", context, update)
                    message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS, context.user_data, context, update)
                    
                    keyboard = create_dynamic_keyboard(context, update).inline_keyboard
                    if navigation_keyboard:
                        keyboard.extend(navigation_keyboard.inline_keyboard)
                        
                    await query.message.edit_text(
                        message_text,
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                    await query.answer(get_message("deadline_saved_success", context, update))
                    return DETAILS
        
        # پردازش ورود بودجه
        elif data == "budget" or data == get_message("budget_button", context, update):
            context.user_data['state'] = DETAILS_BUDGET
            message_text = get_message("select_budget_prompt", context, update)
            message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS_BUDGET, context.user_data, context, update)
            
            keyboard = get_budget_selection_keyboard(context, update).inline_keyboard
            if navigation_keyboard:
                keyboard.extend(navigation_keyboard.inline_keyboard)
                
            await query.message.edit_text(
                message_text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return DETAILS_BUDGET
        
        # پردازش انتخاب بودجه
        elif data.startswith("budget_"):
            parts = data.split("_")
            if len(parts) == 2:
                if parts[1] == "custom":
                    # نمایش پیام برای ورود بودجه دستی
                    message_text = get_message("enter_custom_budget_prompt", context, update)
                    message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS_BUDGET, context.user_data, context, update)
                    
                    keyboard = get_custom_input_keyboard(context, update).inline_keyboard
                    if navigation_keyboard:
                        keyboard.extend(navigation_keyboard.inline_keyboard)
                        
                    await query.message.edit_text(
                        message_text,
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                    await query.answer()
                    return DETAILS_BUDGET
                
                # استخراج بودجه از callback data
                budget = clean_budget(parts[1])
                if budget:
                    formatted_budget = format_price(budget)
                    context.user_data['budget'] = budget
                    context.user_data['state'] = DETAILS
                    
                    message_text = get_message("budget_saved", context, update)
                    message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS, context.user_data, context, update)
                    
                    keyboard = create_dynamic_keyboard(context, update).inline_keyboard
                    if navigation_keyboard:
                        keyboard.extend(navigation_keyboard.inline_keyboard)
                        
                    await query.message.edit_text(
                        message_text,
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                    await query.answer(get_message("budget_saved_success", context, update))
                    return DETAILS
        
        # پردازش ورود مقدار و واحد
        elif data == "quantity" or data == get_message("quantity_button", context, update):
            context.user_data['state'] = DETAILS_QUANTITY
            message_text = get_message("select_quantity_prompt", context, update)
            message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS_QUANTITY, context.user_data, context, update)
            
            keyboard = get_quantity_selection_keyboard(context, update).inline_keyboard
            if navigation_keyboard:
                keyboard.extend(navigation_keyboard.inline_keyboard)
                
            await query.message.edit_text(
                message_text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return DETAILS_QUANTITY
        
        # پردازش انتخاب مقدار و واحد
        elif data.startswith("quantity_"):
            parts = data.split("_")
            if len(parts) >= 2:
                if parts[1] == "custom":
                    # نمایش پیام برای ورود مقدار و واحد دستی
                    message_text = get_message("enter_custom_quantity_prompt", context, update)
                    message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS_QUANTITY, context.user_data, context, update)
                    
                    keyboard = get_custom_input_keyboard(context, update).inline_keyboard
                    if navigation_keyboard:
                        keyboard.extend(navigation_keyboard.inline_keyboard)
                        
                    await query.message.edit_text(
                        message_text,
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                    await query.answer()
                    return DETAILS_QUANTITY
                
                # استخراج مقدار و واحد از callback data
                quantity = '_'.join(parts[1:])
                context.user_data['quantity'] = quantity
                context.user_data['state'] = DETAILS
                
                message_text = get_message("quantity_saved", context, update)
                message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS, context.user_data, context, update)
                
                keyboard = create_dynamic_keyboard(context, update).inline_keyboard
                if navigation_keyboard:
                    keyboard.extend(navigation_keyboard.inline_keyboard)
                    
                await query.message.edit_text(
                    message_text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                await query.answer(get_message("quantity_saved_success", context, update))
                return DETAILS
        
        # پردازش دکمه ثبت درخواست
        elif data == "submit_project" or data == get_message("submit_project_button", context, update):
            if not 'description' in context.user_data:
                await query.answer(get_message("description_required", context, update))
                return DETAILS
            
            # ارسال پیام تأیید به کاربر
            await query.answer(get_message("submitting_request", context, update))
            
            # اگر کاربر از inline button استفاده کرده باشد، نیاز است تا متن مناسب برای submit_project ارسال کنیم
            # ساخت یک پیام مجازی
            await query.message.reply_text(get_message("submit_project_button", context, update))
            # فراخوانی تابع ثبت پروژه
            return await submit_project(update, context)

    # پردازش پیام‌های متنی
    if message:
        text = message.text
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
                    get_message("description_only_text", context, update),
                    reply_markup=ForceReply(selective=True)
                )
                return DESCRIPTION
                
            # پردازش پیام متنی
            logger.info(f"Project details text: {text}")

            if text == get_message("back", context, update):
                # برگشت به انتخاب نوع لوکیشن
                context.user_data['state'] = LOCATION_TYPE
                await message.reply_text(
                    get_message("location_type_guidance", context, update),
                    reply_markup=get_location_type_keyboard(context, update),
                    parse_mode="Markdown"
                )
                return LOCATION_TYPE
            else:
                # بررسی کیفیت توضیحات (اختیاری: پیشنهاد بهبود برای توضیحات کوتاه)
                if len(text) < 20:  # اگر توضیحات خیلی کوتاه است
                    await message.reply_text(
                        get_message("description_too_short", context, update),
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton(get_message("continue_to_next_step", context, update), callback_data="continue_to_details")],
                            [InlineKeyboardButton(get_message("revise_description", context, update), callback_data="back_to_description")]
                        ])
                    )
                    # ذخیره توضیحات موقت برای استفاده بعدی
                    context.user_data['temp_description'] = text
                    return DESCRIPTION
                
                # ذخیره توضیحات و رفتن به جزئیات
                context.user_data['description'] = text
                context.user_data['state'] = DETAILS
                
                # با استفاده از navigation utility
                message_text = get_message("project_details", context, update)
                message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS, context.user_data, context, update)
                
                # دکمه‌های مخصوص ادامه فرآیند
                continue_keyboard = [
                    [InlineKeyboardButton(get_message("continue_to_next_step", context, update), callback_data="continue_to_submit")]
                ]
                
                if navigation_keyboard:
                    # ادغام کیبوردها
                    keyboard_rows = create_dynamic_keyboard(context, update).inline_keyboard
                    # اضافه کردن دکمه‌های ادامه
                    keyboard_rows.extend(continue_keyboard)
                    # اضافه کردن دکمه‌های ناوبری
                    keyboard_rows.extend(navigation_keyboard.inline_keyboard)
                    await message.reply_text(message_text, reply_markup=InlineKeyboardMarkup(keyboard_rows))
                else:
                    # ادغام دکمه‌های ادامه با کیبورد اصلی
                    keyboard_rows = create_dynamic_keyboard(context, update).inline_keyboard
                    keyboard_rows.extend(continue_keyboard)
                    await message.reply_text(message_text, reply_markup=InlineKeyboardMarkup(keyboard_rows))
                
                return DETAILS

        elif current_state == DETAILS:
            if text == get_message("back", context, update):
                # برگشت به مرحله توضیحات
                context.user_data['state'] = DESCRIPTION
                await description_handler(message, context, update)
                return DESCRIPTION
            elif text == get_message("submit_project_button", context, update):
                return await submit_project(update, context)
            elif text == get_message("images_button", context, update):
                # Using the centralized photo management function
                return await init_photo_management(update, context)
            elif text == get_message("need_date_button", context, update):
                # کاربر از متن به جای دکمه استفاده کرده - تغییر وضعیت به DETAILS_DATE
                context.user_data['state'] = DETAILS_DATE
                message_text = get_message("select_need_date_prompt", context, update)
                message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS_DATE, context.user_data, context, update)
                
                keyboard = get_date_selection_keyboard(context, update).inline_keyboard
                if navigation_keyboard:
                    keyboard.extend(navigation_keyboard.inline_keyboard)
                
                await message.reply_text(
                    message_text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return DETAILS_DATE
            elif text == get_message("deadline_button", context, update):
                # کاربر از متن به جای دکمه استفاده کرده - تغییر وضعیت به DETAILS_DEADLINE
                context.user_data['state'] = DETAILS_DEADLINE
                message_text = get_message("select_deadline_prompt", context, update)
                message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS_DEADLINE, context.user_data, context, update)
                
                keyboard = get_deadline_selection_keyboard(context, update).inline_keyboard
                if navigation_keyboard:
                    keyboard.extend(navigation_keyboard.inline_keyboard)
                
                await message.reply_text(
                    message_text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return DETAILS_DEADLINE
            elif text == get_message("budget_button", context, update):
                # کاربر از متن به جای دکمه استفاده کرده - تغییر وضعیت به DETAILS_BUDGET
                context.user_data['state'] = DETAILS_BUDGET
                message_text = get_message("select_budget_prompt", context, update)
                message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS_BUDGET, context.user_data, context, update)
                
                keyboard = get_budget_selection_keyboard(context, update).inline_keyboard
                if navigation_keyboard:
                    keyboard.extend(navigation_keyboard.inline_keyboard)
                
                await message.reply_text(
                    message_text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return DETAILS_BUDGET
            elif text == get_message("quantity_button", context, update):
                # کاربر از متن به جای دکمه استفاده کرده - تغییر وضعیت به DETAILS_QUANTITY
                context.user_data['state'] = DETAILS_QUANTITY
                message_text = get_message("select_quantity_prompt", context, update)
                message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS_QUANTITY, context.user_data, context, update)
                
                keyboard = get_quantity_selection_keyboard(context, update).inline_keyboard
                if navigation_keyboard:
                    keyboard.extend(navigation_keyboard.inline_keyboard)
                
                await message.reply_text(
                    message_text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return DETAILS_QUANTITY
            else:
                await message.reply_text(get_message("invalid_option", context, update))
                return DETAILS
        
        elif current_state == DETAILS_DATE:
            if text == get_message("back", context, update):
                context.user_data['state'] = DETAILS
                message_text = get_message("project_details", context, update)
                message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS, context.user_data, context, update)
                
                keyboard = create_dynamic_keyboard(context, update).inline_keyboard
                if navigation_keyboard:
                    keyboard.extend(navigation_keyboard.inline_keyboard)
                    
                await message.reply_text(
                    message_text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return DETAILS
            
            # بررسی صحت تاریخ وارد شده
            if validate_date(text):
                input_date = JalaliDatetime.strptime(text, '%Y/%m/%d')
                if input_date < JalaliDatetime(datetime.now()):
                    message_text = get_message("date_must_be_future", context, update)
                    message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS_DATE, context.user_data, context, update)
                    
                    keyboard = get_custom_input_keyboard(context, update).inline_keyboard
                    if navigation_keyboard:
                        keyboard.extend(navigation_keyboard.inline_keyboard)
                        
                    await message.reply_text(
                        message_text,
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                else:
                    context.user_data['need_date'] = text
                    context.user_data['state'] = DETAILS
                    
                    message_text = get_message("need_date_saved", context, update)
                    message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS, context.user_data, context, update)
                    
                    keyboard = create_dynamic_keyboard(context, update).inline_keyboard
                    if navigation_keyboard:
                        keyboard.extend(navigation_keyboard.inline_keyboard)
                        
                    await message.reply_text(
                        message_text,
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                    return DETAILS
            else:
                message_text = get_message("invalid_date_format", context, update)
                message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS_DATE, context.user_data, context, update)
                
                keyboard = get_custom_input_keyboard(context, update).inline_keyboard
                if navigation_keyboard:
                    keyboard.extend(navigation_keyboard.inline_keyboard)
                    
                await message.reply_text(
                    message_text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            return DETAILS_DATE
        
        elif current_state == DETAILS_DEADLINE:
            if text == get_message("back", context, update):
                context.user_data['state'] = DETAILS
                message_text = get_message("project_details", context, update)
                message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS, context.user_data, context, update)
                
                keyboard = create_dynamic_keyboard(context, update).inline_keyboard
                if navigation_keyboard:
                    keyboard.extend(navigation_keyboard.inline_keyboard)
                    
                await message.reply_text(
                    message_text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return DETAILS
            
            # بررسی صحت مهلت وارد شده
            deadline = validate_deadline(text)
            if deadline:
                context.user_data['deadline'] = deadline
                context.user_data['state'] = DETAILS
                
                message_text = get_message("deadline_saved", context, update)
                message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS, context.user_data, context, update)
                
                keyboard = create_dynamic_keyboard(context, update).inline_keyboard
                if navigation_keyboard:
                    keyboard.extend(navigation_keyboard.inline_keyboard)
                    
                await message.reply_text(
                    message_text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return DETAILS
            else:
                message_text = get_message("invalid_deadline", context, update)
                message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS_DEADLINE, context.user_data, context, update)
                
                keyboard = get_custom_input_keyboard(context, update).inline_keyboard
                if navigation_keyboard:
                    keyboard.extend(navigation_keyboard.inline_keyboard)
                    
                await message.reply_text(
                    message_text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            return DETAILS_DEADLINE
        
        elif current_state == DETAILS_BUDGET:
            if text == get_message("back", context, update):
                context.user_data['state'] = DETAILS
                message_text = get_message("project_details", context, update)
                message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS, context.user_data, context, update)
                
                keyboard = create_dynamic_keyboard(context, update).inline_keyboard
                if navigation_keyboard:
                    keyboard.extend(navigation_keyboard.inline_keyboard)
                    
                await message.reply_text(
                    message_text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return DETAILS
            
            # بررسی صحت بودجه وارد شده
            budget = clean_budget(text)
            if budget:
                formatted_budget = format_price(budget)
                context.user_data['budget'] = budget
                context.user_data['state'] = DETAILS
                
                message_text = get_message("budget_saved", context, update)
                message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS, context.user_data, context, update)
                
                keyboard = create_dynamic_keyboard(context, update).inline_keyboard
                if navigation_keyboard:
                    keyboard.extend(navigation_keyboard.inline_keyboard)
                    
                await message.reply_text(
                    message_text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return DETAILS
            else:
                message_text = get_message("invalid_budget", context, update)
                message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS_BUDGET, context.user_data, context, update)
                
                keyboard = get_custom_input_keyboard(context, update).inline_keyboard
                if navigation_keyboard:
                    keyboard.extend(navigation_keyboard.inline_keyboard)
                    
                await message.reply_text(
                    message_text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            return DETAILS_BUDGET
        
        elif current_state == DETAILS_QUANTITY:
            if text == get_message("back", context, update):
                context.user_data['state'] = DETAILS
                message_text = get_message("project_details", context, update)
                message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS, context.user_data, context, update)
                
                keyboard = create_dynamic_keyboard(context, update).inline_keyboard
                if navigation_keyboard:
                    keyboard.extend(navigation_keyboard.inline_keyboard)
                    
                await message.reply_text(
                    message_text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return DETAILS
            
            # ذخیره مقدار و واحد
            context.user_data['quantity'] = text
            context.user_data['state'] = DETAILS
            
            message_text = get_message("quantity_saved", context, update)
            message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS, context.user_data, context, update)
            
            keyboard = create_dynamic_keyboard(context, update).inline_keyboard
            if navigation_keyboard:
                keyboard.extend(navigation_keyboard.inline_keyboard)
                
            await message.reply_text(
                message_text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return DETAILS

    # اگر وارد حالت توضیحات شدیم، پیام راهنما نمایش بده
    if context.user_data.get('state') == DESCRIPTION and not (message or query):
        await description_handler(update.message or update.callback_query.message, context, update)
        return DESCRIPTION

    return current_state