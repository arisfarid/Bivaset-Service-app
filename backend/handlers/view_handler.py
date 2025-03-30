from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import requests
import logging
from utils import BASE_URL, log_chat
from keyboards import VIEW_PROJECTS_MENU_KEYBOARD  # اضافه شده

logger = logging.getLogger(__name__)

START, REGISTER, ROLE, EMPLOYER_MENU, CATEGORY, SUBCATEGORY, DESCRIPTION, LOCATION_TYPE, LOCATION_INPUT, DETAILS, DETAILS_FILES, DETAILS_DATE, DETAILS_DEADLINE, DETAILS_BUDGET, DETAILS_QUANTITY, SUBMIT, VIEW_PROJECTS, PROJECT_ACTIONS = range(18)

async def handle_view_projects(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['state'] = VIEW_PROJECTS
    telegram_id = str(update.effective_user.id)
    try:
        response = requests.get(f"{BASE_URL}projects/?user_telegram_id={telegram_id}&ordering=-id&limit=5")
        if response.status_code == 200:
            projects = response.json()
            if not projects:
                await update.message.reply_text("📭 هنوز درخواستی ثبت نکردی!")
                await update.message.reply_text(
                    "📊 ادامه بده یا برگرد:",
                    reply_markup=VIEW_PROJECTS_MENU_KEYBOARD  # استفاده از VIEW_PROJECTS_MENU_KEYBOARD
                )
                return VIEW_PROJECTS
            message = "📋 برای مشاهده جزئیات و مدیریت هر کدام از درخواست‌ها روی دکمه مربوطه ضربه بزنید:\n"
            inline_keyboard = [
                [InlineKeyboardButton(f"{project['title']} (کد: {project['id']})", callback_data=f"{project['id']}")]
                for project in projects
            ]
            await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(inline_keyboard))
            await update.message.reply_text(
                "📊 ادامه بده یا برگرد:",
                reply_markup=VIEW_PROJECTS_MENU_KEYBOARD  # استفاده از VIEW_PROJECTS_MENU_KEYBOARD
            )
        else:
            await update.message.reply_text(f"❌ خطا در دریافت درخواست‌ها: {response.status_code}")
    except requests.exceptions.ConnectionError:
        await update.message.reply_text("❌ خطا: سرور بک‌اند در دسترس نیست.")
    await log_chat(update, context)
    return VIEW_PROJECTS

async def handle_view_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    project_id = query.data
    try:
        response = requests.get(f"{BASE_URL}projects/{project_id}/")
        if response.status_code == 200:
            project = response.json()
            cat_name = context.user_data['categories'][project['category']]['name']
            summary = f"📋 *درخواست {project['id']}*\n" \
                      f"📌 *دسته‌بندی*: {cat_name}\n" \
                      f"📝 *توضیحات*: {project['description']}\n" \
                      f"📍 *موقعیت*: {'غیرحضوری' if project['service_location'] == 'remote' else 'نمایش روی نقشه'}\n"
            if project.get('budget'):
                summary += f"💰 *بودجه*: {project['budget']} تومان\n"
            if project.get('deadline_date'):
                summary += f"⏳ *مهلت*: {project['deadline_date']}\n"
            if project.get('start_date'):
                summary += f"📅 *شروع*: {project['start_date']}\n"
            if project.get('files'):
                summary += "📸 *تصاویر*:\n" + "\n".join([f"- [عکس]({f})" for f in project['files']])
            inline_keyboard = [
                [InlineKeyboardButton("✏️ ویرایش", callback_data=f"edit_{project_id}"),
                 InlineKeyboardButton("⏰ تمدید", callback_data=f"extend_{project_id}")],
                [InlineKeyboardButton("🗑 حذف", callback_data=f"delete_{project_id}"),
                 InlineKeyboardButton("✅ بستن", callback_data=f"close_{project_id}")],
                [InlineKeyboardButton("💬 پیشنهادها", callback_data=f"proposals_{project_id}")]
            ]
            await query.edit_message_text(summary, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(inline_keyboard))
        else:
            await query.edit_message_text(f"❌ خطا در دریافت اطلاعات: {response.status_code}")
    except requests.exceptions.ConnectionError:
        await query.edit_message_text("❌ خطا: سرور بک‌اند در دسترس نیست.")
    await log_chat(update, context)
    return PROJECT_ACTIONS