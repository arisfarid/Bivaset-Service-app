from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import requests
from utils import BASE_URL

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
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