from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import requests
from utils import BASE_URL
import logging

logger = logging.getLogger(__name__)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    logger.info(f"Callback data received: {data}")
    
    if data.isdigit():  # انتخاب دسته‌بندی
        context.user_data['category_id'] = int(data)
        project = {
            'category': context.user_data['category_id']
        }
        cat_name = context.user_data.get('categories', {}).get(project['category'], {}).get('name', 'نامشخص')
        keyboard = [
            [InlineKeyboardButton("✅ ثبت", callback_data="submit_project")],
            [InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_categories")]
        ]
        await query.edit_message_text(
            f"دسته‌بندی انتخاب‌شده: {cat_name}\nحالا می‌تونی ثبت کنی یا برگردی:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    elif data == 'new_project':
        handle_new_project(update, context)
    elif data == 'view_projects':
        handle_view_projects(update, context)
    elif data.startswith('project_details_'):
        handle_project_details(update, context)
    else:
        await query.edit_message_text(text="Unknown callback data.")
    
    project_id = data
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