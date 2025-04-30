from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ForceReply, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler
from keyboards import create_dynamic_keyboard, FILE_MANAGEMENT_MENU_KEYBOARD, create_category_keyboard, MAIN_MENU_KEYBOARD, get_location_type_keyboard, LOCATION_TYPE_GUIDANCE_TEXT, get_description_short_buttons
from utils import clean_budget, validate_date, validate_deadline, log_chat, format_price
from khayyam import JalaliDatetime
from datetime import datetime, timedelta
import logging
from handlers.phone_handler import require_phone
from handlers.submission_handler import submit_project
from handlers.attachment_handler import handle_photo_navigation, init_photo_management
# Fix circular import by importing from navigation_utils instead of state_handler
from handlers.navigation_utils import add_navigation_to_message, SERVICE_REQUEST_FLOW
from functools import wraps
import json
import os
from localization import get_message

logger = logging.getLogger(__name__)

START, REGISTER, ROLE, EMPLOYER_MENU, CATEGORY, SUBCATEGORY, DESCRIPTION, LOCATION_TYPE, LOCATION_INPUT, DETAILS, DETAILS_FILES, DETAILS_DATE, DETAILS_DEADLINE, DETAILS_BUDGET, DETAILS_QUANTITY, SUBMIT, VIEW_PROJECTS, PROJECT_ACTIONS = range(18)
CHANGE_PHONE, VERIFY_CODE = range(20, 22)  # states جدید

async def send_description_guidance(message, context):
    """
    ارسال پیام راهنمای کامل برای مرحله وارد کردن توضیحات
    """
    from localization import get_message
    guidance_text = get_message("description_guidance", lang=context.user_data.get('lang', 'fa'))
    # فقط یک دکمه بازگشت نمایش داده شود
    keyboard = [
        [InlineKeyboardButton(get_message("back", lang=context.user_data.get('lang', 'fa')), callback_data="back_to_location_type")]
    ]
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
                LOCATION_TYPE_GUIDANCE_TEXT,
                reply_markup=get_location_type_keyboard(),
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
            message_text = get_message("details_guidance", lang=context.user_data.get('lang', 'fa'))
            
            # افزودن اطلاعات ناوبری به پیام
            message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS, context.user_data)
            
            # اگر navigation keyboard داریم، آن را ادغام کنیم با کیبورد اصلی
            if navigation_keyboard:
                dynamic_keyboard = create_dynamic_keyboard(context, include_navigation_buttons=False)
                # ادغام دکمه‌های ناوبری با کیبورد اصلی
                keyboard_rows = dynamic_keyboard.inline_keyboard
                keyboard_rows.extend(navigation_keyboard.inline_keyboard)
                await query.message.edit_text(message_text, reply_markup=InlineKeyboardMarkup(keyboard_rows))
            else:
                await query.message.edit_text(message_text, reply_markup=create_dynamic_keyboard(context))
                
            return DETAILS

        # اضافه کردن callback برای بازگشت به مرحله توضیحات
        elif data == "back_to_description":
            # برگشت به مرحله توضیحات با پیام راهنمای کامل
            context.user_data['state'] = DESCRIPTION
            await send_description_guidance(query.message, context)
            return DESCRIPTION
        
        # پردازش مدیریت فایل ها و بازگشت به جزئیات
        elif data == "finish_files" or data == "manage_photos" or data == "back_to_details":
            return await handle_photo_navigation(update, context, data)
        
        # پردازش انتخاب مدیریت عکس‌ها
        elif data == "photo_management" or data == "📸 تصاویر یا فایل" or data == "manage_photos":
            return await init_photo_management(update, context)
        
        # پردازش ورود تاریخ نیاز
        elif data == "need_date" or data == "📅 تاریخ نیاز":
            context.user_data['state'] = DETAILS_DATE
            today = JalaliDatetime(datetime.now()).strftime('%Y/%m/%d')
            tomorrow = JalaliDatetime(datetime.now() + timedelta(days=1)).strftime('%Y/%m/%d')
            day_after = JalaliDatetime(datetime.now() + timedelta(days=2)).strftime('%Y/%m/%d')
            keyboard = [
                [InlineKeyboardButton(f"📅 امروز ({today})", callback_data=f"date_today_{today}")],
                [InlineKeyboardButton(f"📅 فردا ({tomorrow})", callback_data=f"date_tomorrow_{tomorrow}")],
                [InlineKeyboardButton(f"📅 پس‌فردا ({day_after})", callback_data=f"date_day_after_{day_after}")],
                [InlineKeyboardButton("✏️ تاریخ دلخواه", callback_data="date_custom")],
                [InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_details")]
            ]
            
            message_text = get_message("select_date", lang=context.user_data.get('lang', 'fa'))
            message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS_DATE, context.user_data)
            
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
                    message_text = get_message("enter_custom_date", lang=context.user_data.get('lang', 'fa'))
                    message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS_DATE, context.user_data)
                    
                    keyboard = [[InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_details")]]
                    if navigation_keyboard:
                        keyboard.extend(navigation_keyboard.inline_keyboard)
                        
                    await query.message.edit_text(
                        message_text,
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                    await query.answer()
                    return DETAILS_DATE
                
                # استخراج تاریخ از callback data
                date_str = '_'.join(parts[2:])
                context.user_data['need_date'] = date_str
                context.user_data['state'] = DETAILS
                
                message_text = get_message("date_registered", lang=context.user_data.get('lang', 'fa'), date=date_str)
                message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS, context.user_data)
                
                keyboard = create_dynamic_keyboard(context, include_navigation_buttons=False).inline_keyboard
                if navigation_keyboard:
                    keyboard.extend(navigation_keyboard.inline_keyboard)
                    
                await query.message.edit_text(
                    message_text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                await query.answer(get_message("date_success", lang=context.user_data.get('lang', 'fa')))
                return DETAILS
        
        # پردازش ورود مهلت انجام
        elif data == "deadline" or data == "⏳ مهلت انجام":
            context.user_data['state'] = DETAILS_DEADLINE
            keyboard = [
                [
                    InlineKeyboardButton("1 روز", callback_data="deadline_1"),
                    InlineKeyboardButton("2 روز", callback_data="deadline_2"),
                    InlineKeyboardButton("3 روز", callback_data="deadline_3")
                ],
                [
                    InlineKeyboardButton("5 روز", callback_data="deadline_5"),
                    InlineKeyboardButton("7 روز", callback_data="deadline_7"),
                    InlineKeyboardButton("10 روز", callback_data="deadline_10")
                ],
                [
                    InlineKeyboardButton("14 روز", callback_data="deadline_14"),
                    InlineKeyboardButton("30 روز", callback_data="deadline_30")
                ],
                [InlineKeyboardButton("✏️ مقدار دلخواه", callback_data="deadline_custom")],
                [InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_details")]
            ]
            
            message_text = get_message("select_deadline", lang=context.user_data.get('lang', 'fa'))
            message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS_DEADLINE, context.user_data)
            
            if navigation_keyboard:
                keyboard.extend(navigation_keyboard.inline_keyboard)
                
            await query.message.edit_text(
                message_text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return DETAILS_DEADLINE
        
        # پردازش انتخاب مهلت انجام
        elif data.startswith("deadline_"):
            parts = data.split("_")
            if len(parts) == 2:
                if parts[1] == "custom":
                    # نمایش پیام برای ورود مهلت دستی
                    message_text = get_message("enter_custom_deadline", lang=context.user_data.get('lang', 'fa'))
                    message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS_DEADLINE, context.user_data)
                    
                    keyboard = [[InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_details")]]
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
                    
                    message_text = get_message("deadline_registered", lang=context.user_data.get('lang', 'fa'), deadline=deadline)
                    message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS, context.user_data)
                    
                    keyboard = create_dynamic_keyboard(context, include_navigation_buttons=False).inline_keyboard
                    if navigation_keyboard:
                        keyboard.extend(navigation_keyboard.inline_keyboard)
                        
                    await query.message.edit_text(
                        message_text,
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                    await query.answer(get_message("deadline_success", lang=context.user_data.get('lang', 'fa')))
                    return DETAILS
        
        # پردازش ورود بودجه
        elif data == "budget" or data == "💰 بودجه":
            context.user_data['state'] = DETAILS_BUDGET
            keyboard = [
                [
                    InlineKeyboardButton("100,000 تومان", callback_data="budget_100000"),
                    InlineKeyboardButton("200,000 تومان", callback_data="budget_200000")
                ],
                [
                    InlineKeyboardButton("500,000 تومان", callback_data="budget_500000"),
                    InlineKeyboardButton("1,000,000 تومان", callback_data="budget_1000000")
                ],
                [
                    InlineKeyboardButton("2,000,000 تومان", callback_data="budget_2000000"),
                    InlineKeyboardButton("5,000,000 تومان", callback_data="budget_5000000")
                ],
                [InlineKeyboardButton("✏️ مبلغ دلخواه", callback_data="budget_custom")],
                [InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_details")]
            ]
            
            message_text = get_message("select_budget", lang=context.user_data.get('lang', 'fa'))
            message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS_BUDGET, context.user_data)
            
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
                    message_text = get_message("enter_custom_budget", lang=context.user_data.get('lang', 'fa'))
                    message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS_BUDGET, context.user_data)
                    
                    keyboard = [[InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_details")]]
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
                    
                    message_text = get_message("budget_registered", lang=context.user_data.get('lang', 'fa'), budget=formatted_budget)
                    message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS, context.user_data)
                    
                    keyboard = create_dynamic_keyboard(context, include_navigation_buttons=False).inline_keyboard
                    if navigation_keyboard:
                        keyboard.extend(navigation_keyboard.inline_keyboard)
                        
                    await query.message.edit_text(
                        message_text,
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                    await query.answer(get_message("budget_success", lang=context.user_data.get('lang', 'fa')))
                    return DETAILS
        
        # پردازش ورود مقدار و واحد
        elif data == "quantity" or data == "📏 مقدار و واحد":
            context.user_data['state'] = DETAILS_QUANTITY
            keyboard = [
                [
                    InlineKeyboardButton("1 عدد", callback_data="quantity_1_عدد"),
                    InlineKeyboardButton("2 عدد", callback_data="quantity_2_عدد"),
                    InlineKeyboardButton("3 عدد", callback_data="quantity_3_عدد")
                ],
                [
                    InlineKeyboardButton("1 متر", callback_data="quantity_1_متر"),
                    InlineKeyboardButton("5 متر", callback_data="quantity_5_متر"),
                    InlineKeyboardButton("10 متر", callback_data="quantity_10_متر")
                ],
                [
                    InlineKeyboardButton("1 روز", callback_data="quantity_1_روز"),
                    InlineKeyboardButton("1 ساعت", callback_data="quantity_1_ساعت")
                ],
                [InlineKeyboardButton("✏️ مقدار دلخواه", callback_data="quantity_custom")],
                [InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_details")]
            ]
            
            message_text = get_message("select_quantity", lang=context.user_data.get('lang', 'fa'))
            message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS_QUANTITY, context.user_data)
            
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
                    message_text = get_message("enter_custom_quantity", lang=context.user_data.get('lang', 'fa'))
                    message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS_QUANTITY, context.user_data)
                    
                    keyboard = [[InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_details")]]
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
                
                message_text = get_message("quantity_registered", lang=context.user_data.get('lang', 'fa'), quantity=quantity)
                message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS, context.user_data)
                
                keyboard = create_dynamic_keyboard(context, include_navigation_buttons=False).inline_keyboard
                if navigation_keyboard:
                    keyboard.extend(navigation_keyboard.inline_keyboard)
                    
                await query.message.edit_text(
                    message_text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                await query.answer(get_message("quantity_success", lang=context.user_data.get('lang', 'fa')))
                return DETAILS
        
        # پردازش دکمه ثبت درخواست
        elif data == "submit_project" or data == "✅ ثبت درخواست":
            if not 'description' in context.user_data:
                await query.answer(get_message("enter_description_first", lang=context.user_data.get('lang', 'fa')))
                return DETAILS
            
            # ارسال پیام تأیید به کاربر
            await query.answer(get_message("submitting_request", lang=context.user_data.get('lang', 'fa')))
            
            # اگر کاربر از inline button استفاده کرده باشد، نیاز است تا متن مناسب برای submit_project ارسال کنیم
            # ساخت یک پیام مجازی
            await query.message.reply_text(get_message("submit_request", lang=context.user_data.get('lang', 'fa')))
            # فراخوانی تابع ثبت پروژه
            return await submit_project(update, context)

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
                    get_message("description_only_text", lang=context.user_data.get('lang', 'fa')),
                    reply_markup=ForceReply(selective=True)
                )
                return DESCRIPTION
                
            # پردازش پیام متنی
            text = message.text
            logger.info(f"Project details text: {text}")

            if text == "⬅️ بازگشت":
                # برگشت به انتخاب نوع لوکیشن
                context.user_data['state'] = LOCATION_TYPE
                await message.reply_text(
                    LOCATION_TYPE_GUIDANCE_TEXT,
                    reply_markup=get_location_type_keyboard(),
                    parse_mode="Markdown"
                )
                return LOCATION_TYPE
            else:
                # بررسی کیفیت توضیحات (اختیاری: پیشنهاد بهبود برای توضیحات کوتاه)
                if len(text) < 20:  # اگر توضیحات خیلی کوتاه است
                    # حذف منوی قبلی راهنما (در صورت وجود)
                    if 'current_menu_id' in context.user_data:
                        try:
                            await message.bot.delete_message(
                                chat_id=message.chat_id,
                                message_id=context.user_data['current_menu_id']
                            )
                        except Exception:
                            pass
                        context.user_data.pop('current_menu_id', None)
                    from keyboards import get_description_short_buttons
                    await message.reply_text(
                        get_message("description_too_short", lang=context.user_data.get('lang', 'fa')),
                        reply_markup=get_description_short_buttons(lang=context.user_data.get('lang', 'fa'))
                    )
                    # ذخیره توضیحات موقت برای استفاده بعدی
                    context.user_data['temp_description'] = text
                    return DESCRIPTION
                
                # ذخیره توضیحات و رفتن به جزئیات
                context.user_data['description'] = text
                context.user_data['state'] = DETAILS
                try:
                    message_text = get_message("details_guidance", lang=context.user_data.get('lang', 'fa'))
                    message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS, context.user_data)
                    from keyboards import create_dynamic_keyboard
                    keyboard_rows = create_dynamic_keyboard(context, include_navigation_buttons=False).inline_keyboard
                    if navigation_keyboard:
                        keyboard_rows.extend(navigation_keyboard.inline_keyboard)
                    await message.reply_text(message_text, reply_markup=InlineKeyboardMarkup(keyboard_rows))
                except Exception as e:
                    logger.error(f"Error sending DETAILS step after description: {e}")
                    await message.reply_text(get_message("step_error", lang=context.user_data.get('lang', 'fa')))
                return DETAILS

        elif current_state == DETAILS:
            if text == "⬅️ بازگشت":
                # برگشت به مرحله توضیحات
                context.user_data['state'] = DESCRIPTION
                last_description = context.user_data.get('description', '')
                await message.reply_text(
                    get_message("details_prev_description", lang=context.user_data.get('lang', 'fa'), last_description=last_description),
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_location_type")]
                    ])
                )
                return DESCRIPTION
            elif text == "✅ ثبت درخواست":
                return await submit_project(update, context)
            elif text == "📸 تصاویر یا فایل":
                # Using the centralized photo management function
                return await init_photo_management(update, context)
            elif text == "📅 تاریخ نیاز":
                # کاربر از متن به جای دکمه استفاده کرده - تغییر وضعیت به DETAILS_DATE
                context.user_data['state'] = DETAILS_DATE
                today = JalaliDatetime(datetime.now()).strftime('%Y/%m/%d')
                tomorrow = JalaliDatetime(datetime.now() + timedelta(days=1)).strftime('%Y/%m/%d')
                day_after = JalaliDatetime(datetime.now() + timedelta(days=2)).strftime('%Y/%m/%d')
                keyboard = [
                    [InlineKeyboardButton(f"📅 امروز ({today})", callback_data=f"date_today_{today}")],
                    [InlineKeyboardButton(f"📅 فردا ({tomorrow})", callback_data=f"date_tomorrow_{tomorrow}")],
                    [InlineKeyboardButton(f"📅 پس‌فردا ({day_after})", callback_data=f"date_day_after_{day_after}")],
                    [InlineKeyboardButton("✏️ تاریخ دلخواه", callback_data="date_custom")],
                    [InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_details")]
                ]
                
                message_text = get_message("select_date", lang=context.user_data.get('lang', 'fa'))
                message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS_DATE, context.user_data)
                
                if navigation_keyboard:
                    keyboard.extend(navigation_keyboard.inline_keyboard)
                
                await message.reply_text(
                    message_text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return DETAILS_DATE
            elif text == "⏳ مهلت انجام":
                # کاربر از متن به جای دکمه استفاده کرده - تغییر وضعیت به DETAILS_DEADLINE
                context.user_data['state'] = DETAILS_DEADLINE
                keyboard = [
                    [
                        InlineKeyboardButton("1 روز", callback_data="deadline_1"),
                        InlineKeyboardButton("2 روز", callback_data="deadline_2"),
                        InlineKeyboardButton("3 روز", callback_data="deadline_3")
                    ],
                    [
                        InlineKeyboardButton("5 روز", callback_data="deadline_5"),
                        InlineKeyboardButton("7 روز", callback_data="deadline_7"),
                        InlineKeyboardButton("10 روز", callback_data="deadline_10")
                    ],
                    [
                        InlineKeyboardButton("14 روز", callback_data="deadline_14"),
                        InlineKeyboardButton("30 روز", callback_data="deadline_30")
                    ],
                    [InlineKeyboardButton("✏️ مقدار دلخواه", callback_data="deadline_custom")],
                    [InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_details")]
                ]
                
                message_text = get_message("select_deadline", lang=context.user_data.get('lang', 'fa'))
                message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS_DEADLINE, context.user_data)
                
                if navigation_keyboard:
                    keyboard.extend(navigation_keyboard.inline_keyboard)
                
                await message.reply_text(
                    message_text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return DETAILS_DEADLINE
            elif text == "💰 بودجه":
                # کاربر از متن به جای دکمه استفاده کرده - تغییر وضعیت به DETAILS_BUDGET
                context.user_data['state'] = DETAILS_BUDGET
                keyboard = [
                    [
                        InlineKeyboardButton("100,000 تومان", callback_data="budget_100000"),
                        InlineKeyboardButton("200,000 تومان", callback_data="budget_200000")
                    ],
                    [
                        InlineKeyboardButton("500,000 تومان", callback_data="budget_500000"),
                        InlineKeyboardButton("1,000,000 تومان", callback_data="budget_1000000")
                    ],
                    [
                        InlineKeyboardButton("2,000,000 تومان", callback_data="budget_2000000"),
                        InlineKeyboardButton("5,000,000 تومان", callback_data="budget_5000000")
                    ],
                    [InlineKeyboardButton("✏️ مبلغ دلخواه", callback_data="budget_custom")],
                    [InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_details")]
                ]
                
                message_text = get_message("select_budget", lang=context.user_data.get('lang', 'fa'))
                message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS_BUDGET, context.user_data)
                
                if navigation_keyboard:
                    keyboard.extend(navigation_keyboard.inline_keyboard)
                
                await message.reply_text(
                    message_text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return DETAILS_BUDGET
            elif text == "📏 مقدار و واحد":
                # کاربر از متن به جای دکمه استفاده کرده - تغییر وضعیت به DETAILS_QUANTITY
                context.user_data['state'] = DETAILS_QUANTITY
                keyboard = [
                    [
                        InlineKeyboardButton("1 عدد", callback_data="quantity_1_عدد"),
                        InlineKeyboardButton("2 عدد", callback_data="quantity_2_عدد"),
                        InlineKeyboardButton("3 عدد", callback_data="quantity_3_عدد")
                    ],
                    [
                        InlineKeyboardButton("1 متر", callback_data="quantity_1_متر"),
                        InlineKeyboardButton("5 متر", callback_data="quantity_5_متر"),
                        InlineKeyboardButton("10 متر", callback_data="quantity_10_متر")
                    ],
                    [
                        InlineKeyboardButton("1 روز", callback_data="quantity_1_روز"),
                        InlineKeyboardButton("1 ساعت", callback_data="quantity_1_ساعت")
                    ],
                    [InlineKeyboardButton("✏️ مقدار دلخواه", callback_data="quantity_custom")],
                    [InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_details")]
                ]
                
                message_text = get_message("select_quantity", lang=context.user_data.get('lang', 'fa'))
                message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS_QUANTITY, context.user_data)
                
                if navigation_keyboard:
                    keyboard.extend(navigation_keyboard.inline_keyboard)
                
                await message.reply_text(
                    message_text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return DETAILS_QUANTITY
            else:
                await message.reply_text(get_message("invalid_option", lang=context.user_data.get('lang', 'fa')))
                return DETAILS
        
        elif current_state == DETAILS_DATE:
            if text == "⬅️ بازگشت":
                context.user_data['state'] = DETAILS
                message_text = get_message("details_guidance", lang=context.user_data.get('lang', 'fa'))
                message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS, context.user_data)
                
                keyboard = create_dynamic_keyboard(context, include_navigation_buttons=False).inline_keyboard
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
                    message_text = get_message("date_must_be_future", lang=context.user_data.get('lang', 'fa'))
                    message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS_DATE, context.user_data)
                    
                    keyboard = [[InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_details")]]
                    if navigation_keyboard:
                        keyboard.extend(navigation_keyboard.inline_keyboard)
                        
                    await message.reply_text(
                        message_text,
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                else:
                    context.user_data['need_date'] = text
                    context.user_data['state'] = DETAILS
                    
                    message_text = get_message("date_registered", lang=context.user_data.get('lang', 'fa'), date=text)
                    message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS, context.user_data)
                    
                    keyboard = create_dynamic_keyboard(context, include_navigation_buttons=False).inline_keyboard
                    if navigation_keyboard:
                        keyboard.extend(navigation_keyboard.inline_keyboard)
                        
                    await message.reply_text(
                        message_text,
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                    return DETAILS
            else:
                message_text = get_message("invalid_date_format", lang=context.user_data.get('lang', 'fa'))
                message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS_DATE, context.user_data)
                
                keyboard = [[InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_details")]]
                if navigation_keyboard:
                    keyboard.extend(navigation_keyboard.inline_keyboard)
                    
                await message.reply_text(
                    message_text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            return DETAILS_DATE
        
        elif current_state == DETAILS_DEADLINE:
            if text == "⬅️ بازگشت":
                context.user_data['state'] = DETAILS
                message_text = get_message("details_guidance", lang=context.user_data.get('lang', 'fa'))
                message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS, context.user_data)
                
                keyboard = create_dynamic_keyboard(context, include_navigation_buttons=False).inline_keyboard
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
                
                message_text = get_message("deadline_registered", lang=context.user_data.get('lang', 'fa'), deadline=deadline)
                message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS, context.user_data)
                
                keyboard = create_dynamic_keyboard(context, include_navigation_buttons=False).inline_keyboard
                if navigation_keyboard:
                    keyboard.extend(navigation_keyboard.inline_keyboard)
                    
                await message.reply_text(
                    message_text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return DETAILS
            else:
                message_text = get_message("invalid_deadline", lang=context.user_data.get('lang', 'fa'))
                message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS_DEADLINE, context.user_data)
                
                keyboard = [[InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_details")]]
                if navigation_keyboard:
                    keyboard.extend(navigation_keyboard.inline_keyboard)
                    
                await message.reply_text(
                    message_text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            return DETAILS_DEADLINE
        
        elif current_state == DETAILS_BUDGET:
            if text == "⬅️ بازگشت":
                context.user_data['state'] = DETAILS
                message_text = get_message("details_guidance", lang=context.user_data.get('lang', 'fa'))
                message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS, context.user_data)
                
                keyboard = create_dynamic_keyboard(context, include_navigation_buttons=False).inline_keyboard
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
                
                message_text = get_message("budget_registered", lang=context.user_data.get('lang', 'fa'), budget=formatted_budget)
                message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS, context.user_data)
                
                keyboard = create_dynamic_keyboard(context, include_navigation_buttons=False).inline_keyboard
                if navigation_keyboard:
                    keyboard.extend(navigation_keyboard.inline_keyboard)
                    
                await message.reply_text(
                    message_text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return DETAILS
            else:
                message_text = get_message("invalid_budget", lang=context.user_data.get('lang', 'fa'))
                message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS_BUDGET, context.user_data)
                
                keyboard = [[InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_details")]]
                if navigation_keyboard:
                    keyboard.extend(navigation_keyboard.inline_keyboard)
                    
                await message.reply_text(
                    message_text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            return DETAILS_BUDGET
        
        elif current_state == DETAILS_QUANTITY:
            if text == "⬅️ بازگشت":
                context.user_data['state'] = DETAILS
                message_text = get_message("details_guidance", lang=context.user_data.get('lang', 'fa'))
                message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS, context.user_data)
                
                keyboard = create_dynamic_keyboard(context, include_navigation_buttons=False).inline_keyboard
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
            
            message_text = get_message("quantity_registered", lang=context.user_data.get('lang', 'fa'), quantity=text)
            message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS, context.user_data)
            
            keyboard = create_dynamic_keyboard(context, include_navigation_buttons=False).inline_keyboard
            if navigation_keyboard:
                keyboard.extend(navigation_keyboard.inline_keyboard)
                
            await message.reply_text(
                message_text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return DETAILS

    # اگر وارد حالت توضیحات شدیم، پیام راهنما نمایش بده
    if context.user_data.get('state') == DESCRIPTION and not (message or query):
        await send_description_guidance(update.message or update.callback_query.message, context)
        return DESCRIPTION

    return current_state