from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
import logging
from .category_handler import handle_category_selection
from .location_handler import handle_location
from .attachment_handler import handle_attachment
from .project_details_handler import handle_project_details
from .state_handler import handle_project_states
from .view_handler import handle_view_projects
from utils import get_categories, get_user_phone

logger = logging.getLogger(__name__)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    telegram_id = str(update.effective_user.id)
    
    # چک کردن ثبت‌نام کاربر
    phone = await get_user_phone(telegram_id)
    logger.info(f"Checking phone in handle_message for {telegram_id}: {phone}")
    if not phone or phone == f"tg_{telegram_id}":
        keyboard = [[KeyboardButton("ثبت شماره تلفن", request_contact=True)]]
        await update.message.reply_text(
            "😊 برای استفاده از ربات، لطفاً اول شماره تلفنت رو ثبت کن!",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        )
        return

    # بقیه منطق پیام‌ها
    if text == "درخواست خدمات | کارفرما 👔":
        keyboard = [
            [KeyboardButton("📋 درخواست خدمات جدید"), KeyboardButton("📊 مشاهده درخواست‌ها")],
            [KeyboardButton("⬅️ بازگشت")]
        ]
        await update.message.reply_text(
            "🎉 عالیه، {}! می‌خوای خدمات جدید درخواست کنی یا پیشنهادات رو ببینی؟".format(update.effective_user.full_name),
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return
    elif text == "پیشنهاد قیمت | مجری 🦺":
        keyboard = [
            [KeyboardButton("📋 مشاهده درخواست‌ها"), KeyboardButton("💡 پیشنهاد کار")],
            [KeyboardButton("⬅️ بازگشت")]
        ]
        await update.message.reply_text(
            "🌟 خوبه، {}! می‌خوای درخواست‌های موجود رو ببینی یا پیشنهاد کار بدی؟".format(update.effective_user.full_name),
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return
    elif text == "📋 درخواست خدمات جدید":
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
        return
    elif text == "📊 مشاهده درخواست‌ها":
        await handle_view_projects(update, context)
        return
    
    # بررسی حالت‌ها
    if await handle_category_selection(update, context):
        return
    if await handle_location(update, context):
        return
    if await handle_attachment(update, context):
        return
    if await handle_project_details(update, context):
        return
    if await handle_project_states(update, context):
        return
    
    await update.message.reply_text("❌ گزینه نامعتبر! لطفاً از منو انتخاب کن.")