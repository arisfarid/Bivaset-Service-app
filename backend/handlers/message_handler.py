from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils import get_user_phone, get_categories, clean_budget, generate_title, upload_files, convert_deadline_to_date, validate_date, persian_to_english, create_dynamic_keyboard
import requests
from .start_handler import start
from .state_handlers import handle_new_project, handle_view_projects, handle_project_details

BASE_URL = 'http://185.204.171.107:8000/api/'

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    name = update.effective_user.full_name or "کاربر"
    telegram_id = str(update.effective_user.id)
    if 'phone' not in context.user_data:
        context.user_data['phone'] = await get_user_phone(telegram_id)
    if 'categories' not in context.user_data:
        context.user_data['categories'] = await get_categories()

    if text == "📋 درخواست خدمات (کارفرما)":
        context.user_data['role'] = 'client'
        context.user_data['state'] = None
        keyboard = [
            [KeyboardButton("📋 درخواست خدمات جدید"), KeyboardButton("💬 مشاهده پیشنهادات")],
            [KeyboardButton("📊 مشاهده درخواست‌ها"), KeyboardButton("⬅️ بازگشت")]
        ]
        await update.message.reply_text(
            f"🎉 عالیه، {name}! می‌خوای خدمات جدید درخواست کنی یا پیشنهادات رو ببینی؟",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )

    elif text == "🔧 پیشنهاد قیمت (مجری)":
        context.user_data['role'] = 'contractor'
        context.user_data['state'] = None
        keyboard = [
            [KeyboardButton("📋 مشاهده درخواست‌های باز"), KeyboardButton("💡 ارسال پیشنهاد")],
            [KeyboardButton("📊 وضعیت پیشنهادات من"), KeyboardButton("⬅️ بازگشت")]
        ]
        await update.message.reply_text(
            f"🌟 خوبه، {name}! می‌خوای درخواست‌های موجود رو ببینی یا پیشنهاد کار بدی؟",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )

    elif text == "📋 درخواست خدمات جدید":
        await handle_new_project(update, context)

    elif text == "📊 مشاهده درخواست‌ها":
        await handle_view_projects(update, context)

    else:
        await handle_project_details(update, context, text)