from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import requests
import logging
from utils import BASE_URL, log_chat  # Added log_chat import

logger = logging.getLogger(__name__)

async def handle_view_projects(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['state'] = 'view_projects_initial'
    telegram_id = str(update.effective_user.id)
    try:
        response = requests.get(f"{BASE_URL}projects/?user_telegram_id={telegram_id}&ordering=-id&limit=5")
        if response.status_code == 200:
            projects = response.json()
            if not projects:
                await update.message.reply_text("📭 هنوز درخواستی ثبت نکردی!")
                return
            message = "📋 برای مشاهده جزئیات و مدیریت هر کدام از درخواست‌ها روی دکمه مربوطه ضربه بزنید:\n"
            inline_keyboard = [
                [InlineKeyboardButton(f"{project['title']} (کد: {project['id']})", callback_data=f"{project['id']}")]
                for project in projects
            ]
            await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(inline_keyboard))
        else:
            await update.message.reply_text(f"❌ خطا در دریافت درخواست‌ها: {response.status_code}")
    except requests.exceptions.ConnectionError:
        await update.message.reply_text("❌ خطا: سرور بک‌اند در دسترس نیست.")
    await log_chat(update, context)  # Added log_chat call

async def handle_view_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    await log_chat(update, context)  # Added log_chat call