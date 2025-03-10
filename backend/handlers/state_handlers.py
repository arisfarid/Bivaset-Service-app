from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils import get_categories, clean_budget, generate_title, upload_files, convert_deadline_to_date, validate_date, persian_to_english, create_dynamic_keyboard
import requests
from .start_handler import start

BASE_URL = 'http://185.204.171.107:8000/api/'

async def handle_new_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data['categories'] = await get_categories()
    context.user_data['state'] = 'new_project_category'
    categories = context.user_data['categories']
    if not categories:
        await update.message.reply_text("❌ خطا: دسته‌بندی‌ها در دسترس نیست! احتمالاً سرور API مشکل داره.")
        return
    root_cats = [cat_id for cat_id, cat in categories.items() if cat['parent'] is None]
    keyboard = [[KeyboardButton(categories[cat_id]['name'])] for cat_id in root_cats] + [[KeyboardButton("⬅️ بازگشت")]]
    await update.message.reply_text(
        f"🌟 اول دسته‌بندی خدماتت رو انتخاب کن:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def handle_view_projects(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['state'] = 'view_projects_initial'
    telegram_id = str(update.effective_user.id)
    try:
        response = requests.get(f"{BASE_URL}projects/?user_telegram_id={telegram_id}&ordering=-created_at")
        if response.status_code == 200:
            projects = response.json()[:5]
            if not projects:
                await update.message.reply_text("📭 هنوز درخواستی ثبت نکردی!")
                return
            message = "📋 لیست 5 درخواست اخیر شما به شرح زیر است، می‌توانید با ضربه زدن روی هرکدام جزئیات بیشتر مشاهده و درخواست را مدیریت کنید:\n\n"
            inline_keyboard = []
            for i, project in enumerate(projects, 1):
                message += f"{i}. {project['title']} (کد: {project['id']})\n"
                inline_keyboard.append([InlineKeyboardButton(f"{project['title']} (کد: {project['id']})", callback_data=f"{project['id']}")])
            await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(inline_keyboard))
            keyboard = [
                [KeyboardButton("درخواست‌های باز"), KeyboardButton("درخواست‌های بسته")],
                [KeyboardButton("⬅️ بازگشت")]
            ]
            await update.message.reply_text(
                "📊 وضعیت درخواست‌ها رو انتخاب کن یا برگرد:",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
        else:
            await update.message.reply_text(f"❌ خطا در دریافت درخواست‌ها: {response.status_code}")
    except requests.exceptions.ConnectionError:
        await update.message.reply_text("❌ خطا: سرور بک‌اند در دسترس نیست.")

async def handle_project_details(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    # Handle different states related to project details
    # ...existing code for handling project details...
    pass
