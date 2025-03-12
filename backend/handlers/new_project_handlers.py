from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from utils import get_categories
from .start_handler import start

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

async def handle_new_project_states(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    state = context.user_data.get('state')
    categories = context.user_data.get('categories', {})

    if state == 'new_project_category':
        if text == "⬅️ بازگشت":
            context.user_data['state'] = None
            await start(update, context)
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
            return True
        else:
            await update.message.reply_text("❌ دسته‌بندی نامعتبر! دوباره انتخاب کن.")
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
            return True
        selected_subcat = next((cat_id for cat_id, cat in categories.items() if cat['name'] == text and cat['parent'] == context.user_data['category_group']), None)
        if selected_subcat:
            context.user_data['category_id'] = selected_subcat
            context.user_data['state'] = 'new_project_desc'
            await update.message.reply_text(
                f"🌟 حالا توضیحات خدماتت رو بگو تا مجری بهتر بتونه قیمت بده.\n"
                "نمونه خوب: 'نصب 2 شیر پیسوار توی آشپزخونه، جنس استیل، تا آخر هفته نیاز دارم.'"
            )
            return True
        else:
            await update.message.reply_text("❌ زیرمجموعه نامعتبر! دوباره انتخاب کن.")
            return True

    elif state == 'new_project_desc':
        if text == "⬅️ بازگشت":
            context.user_data['state'] = 'new_project_subcategory'
            sub_cats = categories[context.user_data['category_group']]['children']
            keyboard = [[KeyboardButton(categories[cat_id]['name'])] for cat_id in sub_cats] + [[KeyboardButton("⬅️ بازگشت")]]
            await update.message.reply_text(
                f"📌 زیرمجموعه '{categories[context.user_data['category_group']]['name']}' رو انتخاب کن:",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            return True
        context.user_data['description'] = text
        context.user_data['state'] = 'new_project_location'
        keyboard = [
            [KeyboardButton("🏠 محل کارفرما"), KeyboardButton("🔧 محل مجری")],
            [KeyboardButton("💻 غیرحضوری"), KeyboardButton("⬅️ بازگشت")],
            [KeyboardButton("➡️ ادامه")]
        ]
        await update.message.reply_text(
            f"🌟 محل انجام خدماتت رو انتخاب کن:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return True

    elif state == 'new_project_location':
        if text == "⬅️ بازگشت":
            context.user_data['state'] = 'new_project_desc'
            await update.message.reply_text(
                f"🌟 توضیحات خدماتت رو بگو:"
            )
            return True
        elif text == "➡️ ادامه":
            if context.user_data.get('service_location') == 'client_site' and 'location' not in context.user_data:
                await update.message.reply_text("❌ لطفاً لوکیشن رو ثبت کن!")
                return True
            context.user_data['state'] = 'new_project_details'
            from .project_details_handlers import create_dynamic_keyboard
            await update.message.reply_text(
                f"📋 جزئیات درخواست\n"
                "اگه بخوای می‌تونی برای راهنمایی بهتر مجری‌ها این اطلاعات رو هم وارد کنی:",
                reply_markup=create_dynamic_keyboard(context)
            )
            return True
        elif text in ["🏠 محل کارفرما", "🔧 محل مجری", "💻 غیرحضوری"]:
            context.user_data['service_location'] = {'🏠 محل کارفرما': 'client_site', '🔧 محل مجری': 'contractor_site', '💻 غیرحضوری': 'remote'}[text]
            if text == "🏠 محل کارفرما":
                context.user_data['state'] = 'new_project_location_input'
                keyboard = [
                    [KeyboardButton("📍 انتخاب از نقشه", request_location=True), KeyboardButton("📲 ارسال موقعیت فعلی", request_location=True)],
                    [KeyboardButton("⬅️ بازگشت"), KeyboardButton("➡️ ادامه")]
                ]
                await update.message.reply_text(
                    f"📍 برای دریافت قیمت از نزدیک‌ترین مجری، محل انجام خدمات رو از نقشه انتخاب کن:",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
            else:
                context.user_data['location'] = None
                context.user_data['state'] = 'new_project_details'
                from .project_details_handlers import create_dynamic_keyboard
                await update.message.reply_text(
                    f"📋 جزئیات درخواست:",
                    reply_markup=create_dynamic_keyboard(context)
                )
            return True
        return False

    elif state == 'new_project_location_input':
        if text == "⬅️ بازگشت":
            context.user_data['state'] = 'new_project_location'
            keyboard = [
                [KeyboardButton("🏠 محل کارفرما"), KeyboardButton("🔧 محل مجری")],
                [KeyboardButton("💻 غیرحضوری"), KeyboardButton("⬅️ بازگشت")],
                [KeyboardButton("➡️ ادامه")]
            ]
            await update.message.reply_text(
                f"🌟 محل انجام خدماتت رو انتخاب کن:",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            return True
        elif text == "➡️ ادامه":
            if 'location' not in context.user_data:
                await update.message.reply_text("❌ لطفاً لوکیشن رو ثبت کن!")
                return True
            context.user_data['state'] = 'new_project_details'
            from .project_details_handlers import create_dynamic_keyboard
            await update.message.reply_text(
                f"📋 جزئیات درخواست\n"
                "اگه بخوای می‌تونی برای راهنمایی بهتر مجری‌ها این اطلاعات رو هم وارد کنی:",
                reply_markup=create_dynamic_keyboard(context)
            )
            return True
        return False

    return False