from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from utils import generate_title, convert_deadline_to_date, log_chat, BASE_URL
import requests
import logging
from handlers.start_handler import start
from handlers.attachment_handler import upload_attachments
from keyboards import EMPLOYER_MENU_KEYBOARD  # اضافه کردن import در بالای فایل

logger = logging.getLogger(__name__)

START, REGISTER, ROLE, EMPLOYER_MENU, CATEGORY, SUBCATEGORY, DESCRIPTION, LOCATION_TYPE, LOCATION_INPUT, DETAILS, DETAILS_FILES, DETAILS_DATE, DETAILS_DEADLINE, DETAILS_BUDGET, DETAILS_QUANTITY, SUBMIT, VIEW_PROJECTS, PROJECT_ACTIONS = range(18)

# در متد submit_project در submission_handler.py
async def submit_project(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text != "✅ ثبت درخواست":
        return DETAILS

    try:
        # آماده‌سازی داده‌های اولیه بدون location
        data = {
            'title': generate_title(context),
            'description': context.user_data.get('description', ''),
            'category': context.user_data.get('category_id', ''),
            'service_location': context.user_data.get('service_location', ''),
            'user_telegram_id': str(update.effective_user.id)
        }

        # مدیریت location براساس نوع خدمت
        service_location = context.user_data.get('service_location')
        if service_location == 'remote':
            # برای خدمات غیرحضوری، location را با یک آرایه خالی تنظیم می‌کنیم
            data['location'] = []
        elif service_location in ['client_site', 'contractor_site']:
            # برای خدمات حضوری، location را از context می‌گیریم
            if location := context.user_data.get('location'):
                data['location'] = [location['longitude'], location['latitude']]
            else:
                await update.message.reply_text("❌ برای خدمات حضوری، باید لوکیشن را وارد کنید.")
                return DETAILS

        # اضافه کردن فیلدهای اختیاری
        if context.user_data.get('budget'):
            data['budget'] = context.user_data['budget']
        if context.user_data.get('need_date'):
            data['start_date'] = context.user_data['need_date']
        if context.user_data.get('deadline'):
            data['deadline_date'] = convert_deadline_to_date(context.user_data['deadline'])

        logger.info(f"Sending project data to API: {data}")
        await log_chat(update, context)

        response = requests.post(f"{BASE_URL}projects/", json=data)
        logger.info(f"API Response: {response.status_code} - {response.text}")

        if response.status_code == 201:
            project_data = response.json()
            project_id = project_data.get('id')
            
            # آماده‌سازی پیام نهایی
            message = prepare_final_message(context, project_id)
            
            # آماده‌سازی دکمه‌های inline
            keyboard = prepare_inline_keyboard(project_id, bool(context.user_data.get('files', [])))

            # ارسال پیام نهایی
            await update.message.reply_text(
                text=message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )

            # نمایش منوی کارفرما
            await update.message.reply_text(
                text="لطفا انتخاب کنید:",
                reply_markup=EMPLOYER_MENU_KEYBOARD
            )

            # پاک کردن context
            context.user_data.clear()
            
            return EMPLOYER_MENU

        else:
            logger.error(f"Error from API: {response.status_code} - {response.text}")
            await update.message.reply_text("❌ خطا در ثبت درخواست.")
            return DETAILS

    except Exception as e:
        logger.error(f"Error in submit_project: {e}")
        await update.message.reply_text("❌ خطا در ثبت درخواست.")
        return DETAILS

def prepare_final_message(context, project_id):
    """آماده‌سازی پیام نهایی"""
    message_lines = [
        f"🎉 تبریک! درخواست شما با کد {project_id} ثبت شد!",
        f"<b>📌 دسته‌بندی:</b> {context.user_data.get('category_name', 'نامشخص')}",
        f"<b>📝 توضیحات:</b> {context.user_data.get('description', '')}"
    ]
    
    if context.user_data.get('need_date'):
        message_lines.append(f"<b>📅 تاریخ نیاز:</b> {context.user_data['need_date']}")
    if context.user_data.get('budget'):
        message_lines.append(f"<b>💰 بودجه:</b> {context.user_data['budget']} تومان")
    if context.user_data.get('location'):
        loc = context.user_data['location']
        message_lines.append(f"<b>📍 لوکیشن:</b> <a href=\"https://maps.google.com/maps?q={loc['latitude']},{loc['longitude']}\">نمایش روی نقشه</a>")
    
    return "\n".join(message_lines)

def prepare_inline_keyboard(project_id, has_files):
    """آماده‌سازی دکمه‌های inline"""
    keyboard = [
        [InlineKeyboardButton("✏️ ویرایش", callback_data=f"edit_{project_id}"),
         InlineKeyboardButton("⛔ بستن", callback_data=f"close_{project_id}")],
        [InlineKeyboardButton("🗑 حذف", callback_data=f"delete_{project_id}"),
         InlineKeyboardButton("⏰ تمدید", callback_data=f"extend_{project_id}")],
    ]
    
    if has_files:
        keyboard.append([
            InlineKeyboardButton("📸 نمایش عکس‌ها", callback_data=f"view_photos_{project_id}")
        ])
    
    keyboard.append([
        InlineKeyboardButton("💡 پیشنهادها", callback_data=f"offers_{project_id}")
    ])
    
    return keyboard