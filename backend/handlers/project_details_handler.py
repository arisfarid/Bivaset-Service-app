from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from telegram.ext import ContextTypes, ConversationHandler
from keyboards import create_dynamic_keyboard, FILE_MANAGEMENT_MENU_KEYBOARD, create_category_keyboard, MAIN_MENU_KEYBOARD
from utils import clean_budget, validate_date, validate_deadline, log_chat, format_price
from khayyam import JalaliDatetime
from datetime import datetime, timedelta
import logging
from handlers.phone_handler import require_phone
from handlers.submission_handler import submit_project
from handlers.attachment_handler import handle_photo_navigation, init_photo_management
from handlers.state_handler import add_navigation_to_message, SERVICE_REQUEST_FLOW

logger = logging.getLogger(__name__)

START, REGISTER, ROLE, EMPLOYER_MENU, CATEGORY, SUBCATEGORY, DESCRIPTION, LOCATION_TYPE, LOCATION_INPUT, DETAILS, DETAILS_FILES, DETAILS_DATE, DETAILS_DEADLINE, DETAILS_BUDGET, DETAILS_QUANTITY, SUBMIT, VIEW_PROJECTS, PROJECT_ACTIONS = range(18)
CHANGE_PHONE, VERIFY_CODE = range(20, 22)  # states جدید

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
            
            # اگر توضیحات موقت داریم، آن را به عنوان توضیحات اصلی ذخیره کنیم
            if 'temp_description' in context.user_data:
                context.user_data['description'] = context.user_data['temp_description']
                # حذف توضیحات موقت بعد از ذخیره
                del context.user_data['temp_description']
            
            context.user_data['state'] = DETAILS
            message_text = "📋 جزئیات درخواست:\nاگه بخوای می‌تونی برای راهنمایی بهتر مجری‌ها این اطلاعات رو هم وارد کنی:"
            
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
            
            message_text = "📅 تاریخ نیاز رو انتخاب کن یا دستی وارد کن (مثلاً 1403/10/15):"
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
                    message_text = "📅 لطفاً تاریخ مورد نظر خود را به فرمت 1403/10/15 وارد کنید:"
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
                
                message_text = f"📅 تاریخ نیاز ثبت شد: {date_str}"
                message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS, context.user_data)
                
                keyboard = create_dynamic_keyboard(context, include_navigation_buttons=False).inline_keyboard
                if navigation_keyboard:
                    keyboard.extend(navigation_keyboard.inline_keyboard)
                    
                await query.message.edit_text(
                    message_text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                await query.answer("✅ تاریخ با موفقیت ثبت شد!")
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
            
            message_text = "⏳ مهلت انجام (برحسب روز) را انتخاب کنید:"
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
                    message_text = "⏳ لطفاً مهلت انجام مورد نظر خود را به روز وارد کنید (مثلاً: 7):"
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
                    
                    message_text = f"⏳ مهلت انجام ثبت شد: {deadline} روز"
                    message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS, context.user_data)
                    
                    keyboard = create_dynamic_keyboard(context, include_navigation_buttons=False).inline_keyboard
                    if navigation_keyboard:
                        keyboard.extend(navigation_keyboard.inline_keyboard)
                        
                    await query.message.edit_text(
                        message_text,
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                    await query.answer("✅ مهلت انجام با موفقیت ثبت شد!")
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
            
            message_text = "💰 بودجه‌ای که برای این خدمات در نظر دارید را انتخاب کنید:"
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
                    message_text = "💰 لطفاً بودجه مورد نظر خود را به تومان وارد کنید (مثلاً: 500000):"
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
                    
                    message_text = f"💰 بودجه ثبت شد: {formatted_budget} تومان"
                    message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS, context.user_data)
                    
                    keyboard = create_dynamic_keyboard(context, include_navigation_buttons=False).inline_keyboard
                    if navigation_keyboard:
                        keyboard.extend(navigation_keyboard.inline_keyboard)
                        
                    await query.message.edit_text(
                        message_text,
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                    await query.answer("✅ بودجه با موفقیت ثبت شد!")
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
            
            message_text = "📏 مقدار و واحد مورد نیاز را انتخاب کنید:"
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
                    message_text = "📏 لطفاً مقدار و واحد مورد نظر خود را وارد کنید (مثلاً: 2 عدد، 5 متر مربع، 3 ساعت):"
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
                
                message_text = f"📏 مقدار و واحد ثبت شد: {quantity}"
                message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS, context.user_data)
                
                keyboard = create_dynamic_keyboard(context, include_navigation_buttons=False).inline_keyboard
                if navigation_keyboard:
                    keyboard.extend(navigation_keyboard.inline_keyboard)
                    
                await query.message.edit_text(
                    message_text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                await query.answer("✅ مقدار و واحد با موفقیت ثبت شد!")
                return DETAILS
        
        # پردازش دکمه ثبت درخواست
        elif data == "submit_project" or data == "✅ ثبت درخواست":
            if not 'description' in context.user_data:
                await query.answer("⚠️ لطفاً ابتدا توضیحات خدمات را وارد کنید!")
                return DETAILS
            
            # ارسال پیام تأیید به کاربر
            await query.answer("در حال ثبت درخواست شما...")
            
            # اگر کاربر از inline button استفاده کرده باشد، نیاز است تا متن مناسب برای submit_project ارسال کنیم
            # ساخت یک پیام مجازی
            await query.message.reply_text("✅ ثبت درخواست")
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
                
                # با استفاده از navigation utility
                message_text = "📋 جزئیات درخواست\nاگه بخوای می‌تونی برای راهنمایی بهتر مجری‌ها این اطلاعات رو هم وارد کنی:"
                message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS, context.user_data)
                
                if navigation_keyboard:
                    # ادغام کیبوردها
                    keyboard_rows = create_dynamic_keyboard(context, include_navigation_buttons=False).inline_keyboard
                    keyboard_rows.extend(navigation_keyboard.inline_keyboard)
                    await message.reply_text(message_text, reply_markup=InlineKeyboardMarkup(keyboard_rows))
                else:
                    await message.reply_text(message_text, reply_markup=create_dynamic_keyboard(context))
                
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
                
                message_text = "📅 تاریخ نیاز رو انتخاب کن یا دستی وارد کن (مثلاً 1403/10/15):"
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
                
                message_text = "⏳ مهلت انجام (برحسب روز) را انتخاب کنید:"
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
                
                message_text = "💰 بودجه‌ای که برای این خدمات در نظر دارید را انتخاب کنید:"
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
                
                message_text = "📏 مقدار و واحد مورد نیاز را انتخاب کنید:"
                message_text, navigation_keyboard = add_navigation_to_message(message_text, DETAILS_QUANTITY, context.user_data)
                
                if navigation_keyboard:
                    keyboard.extend(navigation_keyboard.inline_keyboard)
                
                await message.reply_text(
                    message_text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return DETAILS_QUANTITY
            else:
                await message.reply_text("❌ گزینه نامعتبر! لطفاً یکی از دکمه‌ها رو انتخاب کن.")
                return DETAILS
        
        elif current_state == DETAILS_DATE:
            if text == "⬅️ بازگشت":
                context.user_data['state'] = DETAILS
                message_text = "📋 جزئیات درخواست:\nاگه بخوای می‌تونی برای راهنمایی بهتر مجری‌ها این اطلاعات رو هم وارد کنی:"
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
                    message_text = "❌ تاریخ باید از امروز به بعد باشه!"
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
                    
                    message_text = f"📅 تاریخ نیاز ثبت شد: {text}"
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
                message_text = "❌ تاریخ نامعتبر! لطفاً به فرمت 1403/10/15 وارد کن و از امروز به بعد باشه."
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
                message_text = "📋 جزئیات درخواست:\nاگه بخوای می‌تونی برای راهنمایی بهتر مجری‌ها این اطلاعات رو هم وارد کنی:"
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
                
                message_text = f"⏳ مهلت انجام ثبت شد: {deadline} روز"
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
                message_text = "❌ مهلت نامعتبر! لطفاً یه عدد وارد کن (مثلاً 7)."
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
                message_text = "📋 جزئیات درخواست:\nاگه بخوای می‌تونی برای راهنمایی بهتر مجری‌ها این اطلاعات رو هم وارد کنی:"
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
                
                message_text = f"💰 بودجه ثبت شد: {formatted_budget} تومان"
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
                message_text = "❌ بودجه نامعتبر! لطفاً فقط عدد وارد کن (مثلاً 500000)."
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
                message_text = "📋 جزئیات درخواست:\nاگه بخوای می‌تونی برای راهنمایی بهتر مجری‌ها این اطلاعات رو هم وارد کنی:"
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
            
            message_text = f"📏 مقدار و واحد ثبت شد: {text}"
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

# تابع کمکی برای ارسال پیام راهنمای توضیحات
async def send_description_guidance(message, context):
    """ارسال پیام راهنما برای نوشتن توضیحات کامل"""
    try:
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
        
        # اطمینان از اینکه state درست تنظیم شده
        context.user_data['state'] = DESCRIPTION
        
        # استفاده از سیستم ناوبری جدید
        guidance_text, navigation_keyboard = add_navigation_to_message(guidance_text, DESCRIPTION, context.user_data)
        
        # ایجاد کیبورد با دکمه‌های بازگشت و شروع مجدد
        keyboard = [
            [InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_location_type")],
            [InlineKeyboardButton("🔄 شروع مجدد", callback_data="restart")]
        ]
        
        # ادغام با کیبورد ناوبری اگر وجود دارد
        if navigation_keyboard:
            keyboard.extend(navigation_keyboard.inline_keyboard)
            
        # ارسال پیام راهنما با کیبورد
        await message.reply_text(
            guidance_text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        logger.info(f"Description guidance sent successfully to user {message.chat.id}")
        return True
    except Exception as e:
        logger.error(f"Error in send_description_guidance: {e}")
        # در صورت خطا، یک پیام ساده ارسال کنیم
        try:
            await message.reply_text(
                "🌟 لطفاً توضیحات کاملی از خدمات درخواستی خود بنویسید:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_location_type")],
                    [InlineKeyboardButton("🔄 شروع مجدد", callback_data="restart")]
                ])
            )
            return True
        except:
            return False