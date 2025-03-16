from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
import logging
from utils import get_categories, log_chat  # Added log_chat import
from .start_handler import start

logger = logging.getLogger(__name__)

async def handle_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    categories = context.user_data.get('categories', {})
    state = context.user_data.get('state')

    if state == 'new_project_category':
        if text == "⬅️ بازگشت":
            context.user_data['state'] = None
            await start(update, context)
            await log_chat(update, context)  # Added log_chat call
            return True
        selected_cat = next((cat_id for cat_id, cat in categories.items() if cat['name'] == text and cat['parent'] is None), None)
        if selected_cat:
            context.user_data['category_group'] = selected_cat
            sub_cats = categories[selected_cat]['children']
            if sub_cats:
                context.user_data['state'] = 'new_project_subcategory'
                keyboard = [[KeyboardButton(categories[cat_id]['name'])] for cat_id in sub_cats] + [[KeyboardButton("⬅️ بازگشت")]]
                await update.message.reply_text(
                    f"📌 زیرمجموعه '{text}' رو انتخاب کن:",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
            else:
                context.user_data['category_id'] = selected_cat
                context.user_data['state'] = 'new_project_desc'
                await update.message.reply_text(
                    f"🌟 حالا توضیحات خدماتت رو بگو تا مجری بهتر بتونه قیمت بده.\n"
                    "نمونه خوب: 'نصب 2 شیر پیسوار توی آشپزخونه، جنس استیل، تا آخر هفته نیاز دارم.'"
                )
            await log_chat(update, context)  # Added log_chat call
            return True
        else:
            await update.message.reply_text("❌ دسته‌بندی نامعتبر! دوباره انتخاب کن.")
            await log_chat(update, context)  # Added log_chat call
            return True

    elif state == 'new_project_subcategory':
        if text == "⬅️ بازگشت":
            context.user_data['state'] = 'new_project_category'
            root_cats = [cat_id for cat_id, cat in categories.items() if cat['parent'] is None]
            keyboard = [[KeyboardButton(categories[cat_id]['name'])] for cat_id in root_cats] + [[KeyboardButton("⬅️ بازگشت")]]
            await update.message.reply_text(
                f"🌟 دسته‌بندی خدماتت رو انتخاب کن:",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            await log_chat(update, context)  # Added log_chat call
            return True
        selected_subcat = next((cat_id for cat_id, cat in categories.items() if cat['name'] == text and cat['parent'] == context.user_data['category_group']), None)
        if selected_subcat:
            context.user_data['category_id'] = selected_subcat
            context.user_data['state'] = 'new_project_desc'
            await update.message.reply_text(
                f"🌟 حالا توضیحات خدماتت رو بگو تا مجری بهتر بتونه قیمت بده.\n"
                "نمونه خوب: 'نصب 2 شیر پیسوار توی آشپزخونه، جنس استیل، تا آخر هفته نیاز دارم.'"
            )
            await log_chat(update, context)  # Added log_chat call
            return True
        else:
            await update.message.reply_text("❌ زیرمجموعه نامعتبر! دوباره انتخاب کن.")
            await log_chat(update, context)  # Added log_chat call
            return True
    return False

async def handle_category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    context.user_data['category_id'] = int(data)
    project = {'category': context.user_data['category_id']}
    cat_name = context.user_data.get('categories', {}).get(project['category'], {}).get('name', 'نامشخص')
    keyboard = [
        [InlineKeyboardButton("✅ ثبت", callback_data="submit_project")],
        [InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_categories")]
    ]
    await query.edit_message_text(
        f"دسته‌بندی انتخاب‌شده: {cat_name}\nحالا می‌تونی ثبت کنی یا برگردی:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    await log_chat(update, context)  # Added log_chat call