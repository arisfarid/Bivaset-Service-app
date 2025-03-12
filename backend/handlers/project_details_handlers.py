from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from utils import clean_budget, validate_date, validate_deadline, create_dynamic_keyboard
from khayyam import JalaliDatetime
from datetime import datetime, timedelta
from .project_submission import submit_project

async def handle_project_details(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    state = context.user_data.get('state')

    if state == 'new_project_details':
        if text == "⬅️ بازگشت":
            context.user_data['state'] = 'new_project_location'
            keyboard = [
                [KeyboardButton("🏠 محل کارفرما"), KeyboardButton("🔧 محل مجری")],
                [KeyboardButton("💻 غیرحضوری"), KeyboardButton("⬅️ بازگشت")],
                [KeyboardButton("➡️ ادامه")]
            ]
            await update.message.reply_text(
                f"🌟 محل انجام خدماتت رو انتخاب کن:",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            return True
        elif text == "✅ ثبت درخواست":
            await submit_project(update, context)
            return True
        elif text == "📸 تصاویر یا فایل":
            context.user_data['state'] = 'new_project_details_files'
            await update.message.reply_text(
                "📸 لطفاً تصاویر رو یکی‌یکی بفرست (حداکثر ۵ تا). فقط عکس قبول می‌شه!"
            )
            return True
        elif text == "📅 تاریخ نیاز":
            context.user_data['state'] = 'new_project_details_date'
            today = JalaliDatetime(datetime.now()).strftime('%Y/%m/%d')
            tomorrow = JalaliDatetime(datetime.now() + timedelta(days=1)).strftime('%Y/%m/%d')
            day_after = JalaliDatetime(datetime.now() + timedelta(days=2)).strftime('%Y/%m/%d')
            keyboard = [
                [KeyboardButton(f"📅 امروز ({today})"), KeyboardButton(f"📅 فردا ({tomorrow})")],
                [KeyboardButton(f"📅 پس‌فردا ({day_after})"), KeyboardButton("⬅️ بازگشت")],
                [KeyboardButton("✏️ تاریخ دلخواه")]
            ]
            await update.message.reply_text(
                "📅 تاریخ نیاز رو انتخاب کن یا دستی وارد کن (مثلاً 1403/10/15):",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            return True
        elif text == "⏳ مهلت انجام":
            context.user_data['state'] = 'new_project_details_deadline'
            await update.message.reply_text("⏳ مهلت انجام رو به روز وارد کن (مثلاً 7):")
            return True
        elif text == "💰 بودجه":
            context.user_data['state'] = 'new_project_details_budget'
            await update.message.reply_text("💰 بودجه رو وارد کن (مثلاً 500000):")
            return True
        elif text == "📏 مقدار و واحد":
            context.user_data['state'] = 'new_project_details_quantity'
            await update.message.reply_text("📏 مقدار و واحد رو وارد کن (مثلاً 2 عدد):")
            return True
        else:
            await update.message.reply_text("❌ گزینه نامعتبر! لطفاً یکی از دکمه‌ها رو انتخاب کن.")
            return True

    elif state == 'new_project_details_files':
        if text == "🏁 اتمام ارسال تصاویر":
            context.user_data['state'] = 'new_project_details'
            await update.message.reply_text(
                f"📋 جزئیات درخواست:",
                reply_markup=create_dynamic_keyboard(context)
            )
            return True
        elif text == "⬅️ بازگشت":
            context.user_data['state'] = 'new_project_details'
            await update.message.reply_text(
                f"📋 جزئیات درخواست:",
                reply_markup=create_dynamic_keyboard(context)
            )
            return True
        else:
            await update.message.reply_text("❌ لطفاً فقط عکس بفرست! متن یا فرمت دیگه قبول نیست.")
            return True

    elif state == 'new_project_details_date':
        if text == "⬅️ بازگشت":
            context.user_data['state'] = 'new_project_details'
            await update.message.reply_text(
                f"📋 جزئیات درخواست:",
                reply_markup=create_dynamic_keyboard(context)
            )
            return True
        elif text == "✏️ تاریخ دلخواه":
            await update.message.reply_text("📅 تاریخ دلخواه رو وارد کن (مثلاً 1403/10/15):")
            return True
        else:
            today = JalaliDatetime(datetime.now()).strftime('%Y/%m/%d')
            tomorrow = JalaliDatetime(datetime.now() + timedelta(days=1)).strftime('%Y/%m/%d')
            day_after = JalaliDatetime(datetime.now() + timedelta(days=2)).strftime('%Y/%m/%d')
            if text in [f"📅 امروز ({today})", f"📅 فردا ({tomorrow})", f"📅 پس‌فردا ({day_after})"]:
                date_str = text.split('(')[1].rstrip(')')
                context.user_data['need_date'] = date_str
                context.user_data['state'] = 'new_project_details'
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
                    context.user_data['state'] = 'new_project_details'
                    await update.message.reply_text(
                        f"📅 تاریخ نیاز ثبت شد: {text}",
                        reply_markup=create_dynamic_keyboard(context)
                    )
            else:
                await update.message.reply_text("❌ تاریخ نامعتبر! لطفاً به فرمت 1403/10/15 وارد کن و از امروز به بعد باشه.")
            return True

    elif state == 'new_project_details_deadline':
        if text == "⬅️ بازگشت":
            context.user_data['state'] = 'new_project_details'
            await update.message.reply_text(
                f"📋 جزئیات درخواست:",
                reply_markup=create_dynamic_keyboard(context)
            )
            return True
        deadline = validate_deadline(text)
        if deadline:
            context.user_data['deadline'] = deadline
            context.user_data['state'] = 'new_project_details'
            await update.message.reply_text(
                f"⏳ مهلت انجام ثبت شد: {deadline} روز",
                reply_markup=create_dynamic_keyboard(context)
            )
        else:
            await update.message.reply_text("❌ مهلت نامعتبر! لطفاً یه عدد وارد کن (مثلاً 7).")
        return True

    elif state == 'new_project_details_budget':
        if text == "⬅️ بازگشت":
            context.user_data['state'] = 'new_project_details'
            await update.message.reply_text(
                f"📋 جزئیات درخواست:",
                reply_markup=create_dynamic_keyboard(context)
            )
            return True
        budget = clean_budget(text)
        if budget:
            context.user_data['budget'] = budget
            context.user_data['state'] = 'new_project_details'
            await update.message.reply_text(
                f"💰 بودجه ثبت شد: {budget} تومان",
                reply_markup=create_dynamic_keyboard(context)
            )
        else:
            await update.message.reply_text("❌ بودجه نامعتبر! لطفاً یه عدد وارد کن (مثلاً 500000).")
        return True

    elif state == 'new_project_details_quantity':
        if text == "⬅️ بازگشت":
            context.user_data['state'] = 'new_project_details'
            await update.message.reply_text(
                f"📋 جزئیات درخواست:",
                reply_markup=create_dynamic_keyboard(context)
            )
            return True
        context.user_data['quantity'] = text
        context.user_data['state'] = 'new_project_details'
        await update.message.reply_text(
            f"📏 مقدار و واحد ثبت شد: {text}",
            reply_markup=create_dynamic_keyboard(context)
        )
        return True

    return False