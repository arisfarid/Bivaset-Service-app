from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils import BASE_URL, log_chat
import requests
import logging
from .start_handler import start

logger = logging.getLogger(__name__)

async def handle_project_states(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    state = context.user_data.get('state')
    telegram_id = str(update.effective_user.id)

    await log_chat(update, context)

    if state in ['view_projects_initial', 'view_projects_list']:
        if text == "⬅️ بازگشت":
            context.user_data['state'] = None
            await start(update, context)
            return True
        if text in ["درخواست‌های باز", "درخواست‌های بسته"]:
            context.user_data['state'] = 'view_projects_list'
            status = 'open' if text == "درخواست‌های باز" else 'closed'
            offset = context.user_data.get('project_offset', 0)
            try:
                response = requests.get(f"{BASE_URL}projects/?user_telegram_id={telegram_id}&status={status}&ordering=-id&limit=10&offset={offset}")
                if response.status_code == 200:
                    projects = response.json()
                    if not projects:
                        await update.message.reply_text(f"📭 هیچ درخواست {text} پیدا نشد!")
                        keyboard = [
                            [KeyboardButton("درخواست‌های باز"), KeyboardButton("درخواست‌های بسته")],
                            [KeyboardButton("⬅️ بازگشت")]
                        ]
                        await update.message.reply_text(
                            "📊 ادامه بده یا برگرد:",
                            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                        )
                        return True
                    message = f"📋 برای مشاهده جزئیات و مدیریت هر کدام از {text} روی دکمه مربوطه ضربه بزنید:\n"
                    inline_keyboard = [
                        [InlineKeyboardButton(f"{project['title']} (کد: {project['id']})", callback_data=f"{project['id']}")]
                        for project in projects[:10]
                    ]
                    if len(projects) > 10:
                        context.user_data['project_offset'] = offset + 10
                        message += f"\nبرای دیدن ادامه، دوباره '{text}' رو بزن."
                    else:
                        context.user_data['project_offset'] = 0
                    await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(inline_keyboard))
                    keyboard = [
                        [KeyboardButton("درخواست‌های باز"), KeyboardButton("درخواست‌های بسته")],
                        [KeyboardButton("⬅️ بازگشت")]
                    ]
                    await update.message.reply_text(
                        "📊 ادامه بده یا برگرد:",
                        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                    )
                else:
                    await update.message.reply_text(f"❌ خطا در دریافت درخواست‌ها: {response.status_code}")
                    keyboard = [
                        [KeyboardButton("درخواست‌های باز"), KeyboardButton("درخواست‌های بسته")],
                        [KeyboardButton("⬅️ بازگشت")]
                    ]
                    await update.message.reply_text(
                        "📊 ادامه بده یا برگرد:",
                        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                    )
            except requests.exceptions.ConnectionError:
                await update.message.reply_text("❌ خطا: سرور بک‌اند در دسترس نیست.")
                keyboard = [
                    [KeyboardButton("درخواست‌های باز"), KeyboardButton("درخواست‌های بسته")],
                    [KeyboardButton("⬅️ بازگشت")]
                ]
                await update.message.reply_text(
                    "📊 ادامه بده یا برگرد:",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
            return True
        else:
            await update.message.reply_text("❌ گزینه نامعتبر! لطفاً یکی از دکمه‌ها رو انتخاب کن.")
            return True
    return False