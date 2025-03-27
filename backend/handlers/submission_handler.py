from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from utils import generate_title, convert_deadline_to_date, log_chat, BASE_URL
import requests
import logging
from handlers.start_handler import start
from handlers.attachment_handler import upload_attachments

logger = logging.getLogger(__name__)

START, REGISTER, ROLE, EMPLOYER_MENU, CATEGORY, SUBCATEGORY, DESCRIPTION, LOCATION_TYPE, LOCATION_INPUT, DETAILS, DETAILS_FILES, DETAILS_DATE, DETAILS_DEADLINE, DETAILS_BUDGET, DETAILS_QUANTITY, SUBMIT, VIEW_PROJECTS, PROJECT_ACTIONS = range(18)

async def submit_project(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text != "✅ ثبت درخواست":
        return DETAILS

    location = context.user_data.get('location')
    location_data = [location['longitude'], location['latitude']] if location else None

    # آماده‌سازی داده‌های پروژه
    data = {
        'title': generate_title(context),
        'description': context.user_data.get('description', ''),
        'category': context.user_data.get('category_id', ''),
        'service_location': context.user_data.get('service_location', ''),
        'location': location_data,
        'user_telegram_id': str(update.effective_user.id)
    }
    if context.user_data.get('budget'):
        data['budget'] = context.user_data['budget']
    if context.user_data.get('need_date'):
        data['start_date'] = context.user_data['need_date']
    if context.user_data.get('deadline'):
        data['deadline_date'] = convert_deadline_to_date(context.user_data['deadline'])

    logger.info(f"Sending project data to API: {data}")
    await log_chat(update, context)

    try:
        # ثبت پروژه در API
        response = requests.post(f"{BASE_URL}projects/", json=data)
        if response.status_code == 201:
            project = response.json()
            project_id = project.get('id')
            context.user_data['project_id'] = project_id
            logger.info(f"Project created with ID: {project_id}")
            
            # آپلود فایل‌ها
            files = context.user_data.get('files', [])
            uploaded_files = []
            if files:
                uploaded_files = await upload_attachments(files, context)
                context.user_data['uploaded_files'] = uploaded_files
            
            # آماده‌سازی پیام نهایی
            message_lines = [
                f"🎉 تبریک! درخواست شما با کد {project_id} ثبت شد!",
                f"<b>📌 دسته‌بندی:</b> {context.user_data.get('categories', {}).get(context.user_data.get('category_id', ''), {}).get('name', 'نامشخص')}",
                f"<b>📝 توضیحات:</b> {context.user_data.get('description', '')}"
            ]
            if context.user_data.get('need_date'):
                message_lines.append(f"<b>📅 تاریخ نیاز:</b> {context.user_data['need_date']}")
            if context.user_data.get('deadline'):
                message_lines.append(f"<b>⏳ مهلت انجام:</b> {context.user_data['deadline']} روز")
            if context.user_data.get('budget'):
                message_lines.append(f"<b>💰 بودجه:</b> {context.user_data['budget']} تومان")
            if context.user_data.get('quantity'):
                message_lines.append(f"<b>📏 مقدار و واحد:</b> {context.user_data['quantity']}")
            
            location = context.user_data.get('location')
            if location:
                message_lines.append(f"<b>📍 لوکیشن:</b> <a href=\"https://maps.google.com/maps?q={location['latitude']},{location['longitude']}\">نمایش روی نقشه</a>")
            
            # فقط تعداد عکس‌ها را نمایش می‌دهیم، بدون نمایش کامند
            if files:
                message_lines.append(f"<b>📸 تعداد عکس‌ها:</b> {len(files)} عکس ارسال شده")
            
            message = "\n".join(message_lines)

            # دکمه‌های InlineKeyboard
            inline_keyboard = [
                [InlineKeyboardButton("✏️ ویرایش", callback_data=f"edit_{project_id}"),
                 InlineKeyboardButton("⛔ بستن", callback_data=f"close_{project_id}")],
                [InlineKeyboardButton("🗑 حذف", callback_data=f"delete_{project_id}"),
                 InlineKeyboardButton("⏰ تمدید", callback_data=f"extend_{project_id}")],
            ]
            
            # اضافه کردن دکمه نمایش عکس‌ها فقط اگر عکسی وجود داشته باشد
            if files:
                inline_keyboard.append([
                    InlineKeyboardButton("📸 نمایش عکس‌ها", callback_data=f"view_photos_{project_id}")
                ])
            
            inline_keyboard.append([
                InlineKeyboardButton("💡 پیشنهادها", callback_data=f"offers_{project_id}")
            ])

            # ارسال پیام نهایی
            if files:
                await update.message.reply_photo(
                    photo=files[0],
                    caption=message,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard),
                    parse_mode='HTML'
                )
            else:
                await update.message.reply_text(
                    message,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard),
                    parse_mode='HTML'
                )

            # پاک کردن context پس از ارسال پیام
            temp_project_id = project_id
            temp_uploaded_files = uploaded_files
            context.user_data.clear()
            context.user_data['current_project_id'] = temp_project_id
            context.user_data['uploaded_files'] = temp_uploaded_files
            
            await start(update, context)
            return ROLE

        else:
            logger.error(f"API error: {response.text}")
            await update.message.reply_text(f"❌ خطا در ثبت درخواست: {response.text[:50]}...")
            return DETAILS

    except Exception as e:
        logger.error(f"Error submitting project: {e}")
        await update.message.reply_text("❌ خطا در ثبت درخواست.")
        return DETAILS