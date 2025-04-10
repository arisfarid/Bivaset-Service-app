from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from telegram.ext import ContextTypes, ConversationHandler
from keyboards import create_dynamic_keyboard, FILE_MANAGEMENT_MENU_KEYBOARD, create_category_keyboard
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
    text = update.message.text if update.message else None
    current_state = context.user_data.get('state', DESCRIPTION)
    logger.info(f"Processing project details - State: {current_state}, Text: {text}")

    if current_state == DESCRIPTION:
        if text == "⬅️ بازگشت":
            logger.info("Back button pressed in description state")
            context.user_data['state'] = CATEGORY
            categories = context.user_data.get('categories', {})
            category_group = context.user_data.get('category_group')
            
            if category_group and categories.get(category_group):
                # برگشت به منوی زیردسته‌ها
                parent = categories[category_group]
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
                await update.message.reply_text(
                    f"📋 زیرمجموعه {parent['name']} را انتخاب کنید:",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                # برگشت به منوی اصلی دسته‌بندی‌ها
                keyboard = create_category_keyboard(categories)
                await update.message.reply_text(
                    "🌟 دسته‌بندی خدماتت رو انتخاب کن:",
                    reply_markup=keyboard
                )
            return CATEGORY

        # ذخیره توضیحات و رفتن به مرحله بعد
        context.user_data['description'] = text
        context.user_data['state'] = LOCATION_TYPE
        keyboard = [
            [InlineKeyboardButton("🏠 محل من", callback_data="location_client")],
            [InlineKeyboardButton("🔧 محل مجری", callback_data="location_contractor")],
            [InlineKeyboardButton("💻 غیرحضوری", callback_data="location_remote")],
            [InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_description")]
        ]
        await update.message.reply_text(
            "🌟 محل انجام خدماتت رو انتخاب کن:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return LOCATION_TYPE

    elif current_state == LOCATION_TYPE:
        if text == "⬅️ بازگشت":
            logger.info("Back button pressed in location type state")
            context.user_data['state'] = DESCRIPTION
            await update.message.reply_text(
                "🌟 توضیحات خدماتت رو بگو:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_categories")]
                ])
            )
            return DESCRIPTION

    elif current_state == DETAILS:
        if text == "⬅️ بازگشت":
            context.user_data['state'] = LOCATION_TYPE
            keyboard = [
                [InlineKeyboardButton("🏠 محل من"), InlineKeyboardButton("🔧 محل مجری")],
                [InlineKeyboardButton("💻 غیرحضوری"), InlineKeyboardButton("⬅️ بازگشت")],
                [InlineKeyboardButton("➡️ ادامه")]
            ]
            await update.message.reply_text(
                f"🌟 محل انجام خدماتت رو انتخاب کن:",
                reply_markup=InlineKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            return LOCATION_TYPE
        elif text == "✅ ثبت درخواست":
            await submit_project(update, context)
            return SUBMIT
        elif text == "📸 تصاویر یا فایل":
            context.user_data['state'] = DETAILS_FILES
            files = context.user_data.get('files', [])
            if files:
                await update.message.reply_text(
                    f"📸 تا الان {len(files)} عکس فرستادی. می‌تونی عکس جدید بفرستی یا مدیریت کنی.",
                    reply_markup=FILE_MANAGEMENT_MENU_KEYBOARD
                )
            else:
                await update.message.reply_text(
                    "📸 لطفاً تصاویر رو یکی‌یکی بفرست (حداکثر ۵ تا). فقط عکس قبول می‌شه!",
                    reply_markup=FILE_MANAGEMENT_MENU_KEYBOARD
                )
            return DETAILS_FILES
        elif text == "📅 تاریخ نیاز":
            context.user_data['state'] = DETAILS_DATE
            today = JalaliDatetime(datetime.now()).strftime('%Y/%m/%d')
            tomorrow = JalaliDatetime(datetime.now() + timedelta(days=1)).strftime('%Y/%m/%d')
            day_after = JalaliDatetime(datetime.now() + timedelta(days=2)).strftime('%Y/%m/%d')
            keyboard = [
                [InlineKeyboardButton(f"📅 امروز ({today})")],
                [InlineKeyboardButton(f"📅 فردا ({tomorrow})")],
                [InlineKeyboardButton(f"📅 پس‌فردا ({day_after})")],
                [InlineKeyboardButton("✏️ تاریخ دلخواه")],
                [InlineKeyboardButton("⬅️ بازگشت")]
            ]
            await update.message.reply_text(
                "📅 تاریخ نیاز رو انتخاب کن یا دستی وارد کن (مثلاً 1403/10/15):",
                reply_markup=InlineKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            return DETAILS_DATE
        elif text == "⏳ مهلت انجام":
            context.user_data['state'] = DETAILS_DEADLINE
            await update.message.reply_text(
                "⏳ مهلت انجام رو بر حسب روز وارد کن:",
                reply_markup=ForceReply(input_field_placeholder="مثلاً: 7", selective=True)
            )
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="لطفاً تعداد روز را وارد کنید:",
                reply_markup={"input_field_content_type": "number"}
            )
            return DETAILS_DEADLINE
        elif text == "💰 بودجه":
            context.user_data['state'] = DETAILS_BUDGET
            await update.message.reply_text(
                "💰 بودجه رو به تومان وارد کن:",
                reply_markup=ForceReply(input_field_placeholder="مثلاً: 500000", selective=True)
            )
            context.bot.send_message(
                chat_id=update.effective_chat.id, 
                text="لطفاً مبلغ را وارد کنید:",
                reply_markup={"input_field_content_type": "number"}
            )
            return DETAILS_BUDGET
        elif text == "📏 مقدار و واحد":
            context.user_data['state'] = DETAILS_QUANTITY
            await update.message.reply_text("📏 مقدار و واحد رو وارد کن (مثلاً 2 عدد):")
            return DETAILS_QUANTITY
        else:
            await update.message.reply_text("❌ گزینه نامعتبر! لطفاً یکی از دکمه‌ها رو انتخاب کن.")
            return DETAILS

    elif current_state == DETAILS_DATE:
        if text == "⬅️ بازگشت":
            context.user_data['state'] = DETAILS
            await update.message.reply_text(
                f"📋 جزئیات درخواست:",
                reply_markup=create_dynamic_keyboard(context)
            )
            return DETAILS
        elif text == "✏️ تاریخ دلخواه":
            await update.message.reply_text("📅 تاریخ دلخواه رو وارد کن (مثلاً 1403/10/15):")
            return DETAILS_DATE
        else:
            today = JalaliDatetime(datetime.now()).strftime('%Y/%m/%d')
            tomorrow = JalaliDatetime(datetime.now() + timedelta(days=1)).strftime('%Y/%m/%d')
            day_after = JalaliDatetime(datetime.now() + timedelta(days=2)).strftime('%Y/%m/%d')
            if text in [f"📅 امروز ({today})", f"📅 فردا ({tomorrow})", f"📅 پس‌فردا ({day_after})"]:
                date_str = text.split('(')[1].rstrip(')')
                context.user_data['need_date'] = date_str
                context.user_data['state'] = DETAILS
                await update.message.reply_text(
                    f"📅 تاریخ نیاز ثبت شد: {date_str}",
                    reply_markup=create_dynamic_keyboard(context)
                )
            elif validate_date(text):
                input_date = JalaliDatetime.strptime(text, '%Y/%m/%d')
                if input_date < JalaliDatetime(datetime.now()):
                    await update.message.reply_text("❌ تاریخ باید از امروز به بعد باشه!")
                else:
                    context.user_data['need_date'] = text
                    context.user_data['state'] = DETAILS
                    await update.message.reply_text(
                        f"📅 تاریخ نیاز ثبت شد: {text}",
                        reply_markup=create_dynamic_keyboard(context)
                    )
            else:
                await update.message.reply_text("❌ تاریخ نامعتبر! لطفاً به فرمت 1403/10/15 وارد کن و از امروز به بعد باشه.")
            return DETAILS_DATE

    elif current_state == DETAILS_DEADLINE:
        if text == "⬅️ بازگشت":
            context.user_data['state'] = DETAILS
            await update.message.reply_text(
                f"📋 جزئیات درخواست:",
                reply_markup=create_dynamic_keyboard(context)
            )
            return DETAILS
        deadline = validate_deadline(text)
        if deadline:
            context.user_data['deadline'] = deadline
            context.user_data['state'] = DETAILS
            await update.message.reply_text(
                f"⏳ مهلت انجام ثبت شد: {deadline} روز",
                reply_markup=create_dynamic_keyboard(context)
            )
        else:
            await update.message.reply_text("❌ مهلت نامعتبر! لطفاً یه عدد وارد کن (مثلاً 7).")
        return DETAILS_DEADLINE

    elif current_state == DETAILS_BUDGET:
        if text == "⬅️ بازگشت":
            context.user_data['state'] = DETAILS
            await update.message.reply_text(
                f"📋 جزئیات درخواست:",
                reply_markup=create_dynamic_keyboard(context)
            )
            return DETAILS
            
        budget = clean_budget(text)
        if budget:
            formatted_budget = format_price(budget)
            context.user_data['budget'] = budget
            context.user_data['state'] = DETAILS
            await update.message.reply_text(
                f"💰 بودجه ثبت شد: {formatted_budget} تومان",
                reply_markup=create_dynamic_keyboard(context)
            )
        else:
            await update.message.reply_text(
                "❌ بودجه نامعتبر! لطفاً فقط عدد وارد کن (مثلاً 500000).",
                reply_markup=ForceReply(selective=True)
            )
        return DETAILS_BUDGET

    elif current_state == DETAILS_QUANTITY:
        if text == "⬅️ بازگشت":
            context.user_data['state'] = DETAILS
            await update.message.reply_text(
                f"📋 جزئیات درخواست:",
                reply_markup=create_dynamic_keyboard(context)
            )
            return DETAILS
        context.user_data['quantity'] = text
        context.user_data['state'] = DETAILS
        await update.message.reply_text(
            f"📏 مقدار و واحد ثبت شد: {text}",
            reply_markup=create_dynamic_keyboard(context)
        )
        return DETAILS

    return current_state