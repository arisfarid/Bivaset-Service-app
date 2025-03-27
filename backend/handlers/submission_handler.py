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

async def submit_project(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text != "✅ ثبت درخواست":
        return DETAILS

    try:
        # تنظیم عنوان بر اساس محل خدمات
        service_location = context.user_data.get('service_location', '')
        title_suffix = {
            'remote': '(غیرحضوری)',
            'client_site': f"در {context.user_data.get('location_name', 'محل مشتری')}",
            'contractor_site': 'در محل مجری'
        }.get(service_location, '')

        # آماده‌سازی داده‌های پروژه
        data = {
            'title': f"{context.user_data.get('category_name', '')}: {context.user_data.get('description', '')} {title_suffix}",
            'description': context.user_data.get('description', ''),
            'category': context.user_data.get('category_id', ''),
            'service_location': service_location,
            'user_telegram_id': str(update.effective_user.id)
        }

        # اضافه کردن location فقط برای حالت client_site
        if service_location == 'client_site' and context.user_data.get('location'):
            data['location'] = [
                context.user_data['location']['longitude'],
                context.user_data['location']['latitude']
            ]
        else:
            data['location'] = None

        # اضافه کردن فیلدهای اختیاری
        optional_fields = {
            'budget': 'budget',
            'need_date': 'start_date',
            'deadline': 'deadline_date'
        }

        for context_key, api_key in optional_fields.items():
            if value := context.user_data.get(context_key):
                data[api_key] = value if api_key != 'deadline_date' else convert_deadline_to_date(value)

        logger.info(f"Sending project data to API: {data}")
        await log_chat(update, context)

        response = requests.post(f"{BASE_URL}projects/", json=data)
        
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