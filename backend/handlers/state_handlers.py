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
            keyboard = [
                [KeyboardButton("درخواست‌های باز"), KeyboardButton("درخواست‌های بسته")],
                [KeyboardButton("⬅️ بازگشت")]
            ]
            await update.message.reply_text(
                "📊 وضعیت درخواست‌ها رو انتخاب کن یا برگرد:",
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

async def handle_project_details(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    telegram_id = str(update.effective_user.id)
    state = context.user_data.get('state')

    if state == 'new_project_category':
        if text == "⬅️ بازگشت":
            context.user_data['state'] = None
            await start(update, context)
            return
        categories = context.user_data['categories']
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
        else:
            await update.message.reply_text("❌ دسته‌بندی نامعتبر! دوباره انتخاب کن.")

    elif state == 'new_project_subcategory':
        if text == "⬅️ بازگشت":
            context.user_data['state'] = 'new_project_category'
            categories = context.user_data['categories']
            root_cats = [cat_id for cat_id, cat in categories.items() if cat['parent'] is None]
            keyboard = [[KeyboardButton(categories[cat_id]['name'])] for cat_id in root_cats] + [[KeyboardButton("⬅️ بازگشت")]]
            await update.message.reply_text(
                f"🌟 دسته‌بندی خدماتت رو انتخاب کن:",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            return
        categories = context.user_data['categories']
        selected_subcat = next((cat_id for cat_id, cat in categories.items() if cat['name'] == text and cat['parent'] == context.user_data['category_group']), None)
        if selected_subcat:
            context.user_data['category_id'] = selected_subcat
            context.user_data['state'] = 'new_project_desc'
            await update.message.reply_text(
                f"🌟 حالا توضیحات خدماتت رو بگو تا مجری بهتر بتونه قیمت بده.\n"
                "نمونه خوب: 'نصب 2 شیر پیسوار توی آشپزخونه، جنس استیل، تا آخر هفته نیاز دارم.'"
            )
        else:
            await update.message.reply_text("❌ زیرمجموعه نامعتبر! دوباره انتخاب کن.")

    elif state == 'new_project_desc':
        if text == "⬅️ بازگشت":
            context.user_data['state'] = 'new_project_subcategory'
            categories = context.user_data['categories']
            sub_cats = categories[context.user_data['category_group']]['children']
            keyboard = [[KeyboardButton(categories[cat_id]['name'])] for cat_id in sub_cats] + [[KeyboardButton("⬅️ بازگشت")]]
            await update.message.reply_text(
                f"📌 زیرمجموعه '{categories[context.user_data['category_group']]['name']}' رو انتخاب کن:",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            return
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

    elif state == 'new_project_location':
        if text == "⬅️ بازگشت":
            context.user_data['state'] = 'new_project_desc'
            await update.message.reply_text(
                f"🌟 توضیحات خدماتت رو بگو:"
            )
            return
        elif text == "➡️ ادامه":
            if context.user_data.get('service_location') == 'client_site' and 'location' not in context.user_data:
                await update.message.reply_text("❌ لطفاً لوکیشن رو ثبت کن!")
                return
            context.user_data['state'] = 'new_project_details'
            await update.message.reply_text(
                f"📋 جزئیات درخواست\n"
                "اگه بخوای می‌تونی برای راهنمایی بهتر مجری‌ها این اطلاعات رو هم وارد کنی:",
                reply_markup=create_dynamic_keyboard(context)
            )
        elif text in ["🏠 محل کارفرما", "🔧 محل مجری", "💻 غیرحضوری"]:
            context.user_data['service_location'] = {'🏠 محل کارفرما': 'client_site', '🔧 محل مجری': 'contractor_site', '💻 غیرحضوری': 'remote'}[text]
            if text == "🏠 محل کارفرما":
                context.user_data['state'] = 'new_project_location_input'
                keyboard = [
                    [KeyboardButton("📍 انتخاب از نقشه"), KeyboardButton("📲 ارسال موقعیت فعلی", request_location=True)],
                    [KeyboardButton("⬅️ بازگشت"), KeyboardButton("➡️ ادامه")]
                ]
                await update.message.reply_text(
                    f"📍 محل خدماتت رو چطور می‌خوای بفرستی؟",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
            else:
                context.user_data['location'] = None
                context.user_data['state'] = 'new_project_details'
                await update.message.reply_text(
                    f"📋 جزئیات درخواست:",
                    reply_markup=create_dynamic_keyboard(context)
                )

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
            return
        elif text == "➡️ ادامه":
            if 'location' not in context.user_data:
                await update.message.reply_text("❌ لطفاً لوکیشن رو ثبت کن!")
                return
            context.user_data['state'] = 'new_project_details'
            await update.message.reply_text(
                f"📋 جزئیات درخواست\n"
                "اگه بخوای می‌تونی برای راهنمایی بهتر مجری‌ها این اطلاعات رو هم وارد کنی:",
                reply_markup=create_dynamic_keyboard(context)
            )
        else:
            await update.message.reply_text("❌ گزینه نامعتبر! لطفاً لوکیشن بفرست یا ادامه بده.")

    elif state == 'new_project_details':
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
            return
        elif text == "✅ ثبت درخواست":
            await submit_project(update, context)
        elif text == "📸 تصاویر یا فایل":
            context.user_data['state'] = 'new_project_details_files'
            await update.message.reply_text("📸 لطفاً تصاویر یا فایل‌های خود را ارسال کنید (حداکثر 5 فایل).")
        elif text == "📅 تاریخ نیاز":
            context.user_data['state'] = 'new_project_details_date'
            await update.message.reply_text("📅 تاریخ نیاز به خدمات را وارد کنید (مثلاً 1403/10/15).")
        elif text == "⏳ مهلت انجام":
            context.user_data['state'] = 'new_project_details_deadline'
            await update.message.reply_text("⏳ مهلت انجام خدمات را به روز وارد کنید (مثلاً 7).")
        elif text == "💰 بودجه":
            context.user_data['state'] = 'new_project_details_budget'
            await update.message.reply_text("💰 بودجه خود را وارد کنید (مثلاً 500000).")
        elif text == "📏 مقدار و واحد":
            context.user_data['state'] = 'new_project_details_quantity'
            await update.message.reply_text("📏 مقدار و واحد خدمات را وارد کنید (مثلاً 2 عدد).")
        else:
            await update.message.reply_text("❌ گزینه نامعتبر! لطفاً یکی از دکمه‌ها را انتخاب کنید.")

    elif state == 'new_project_details_files':
        if text == "🏁 اتمام ارسال تصاویر":
            context.user_data['state'] = 'new_project_details'
            await update.message.reply_text(
                f"📋 جزئیات درخواست:",
                reply_markup=create_dynamic_keyboard(context)
            )
            return
        elif text == "⬅️ بازگشت":
            context.user_data['state'] = 'new_project_details'
            await update.message.reply_text(
                f"📋 جزئیات درخواست:",
                reply_markup=create_dynamic_keyboard(context)
            )
            return
        else:
            await update.message.reply_text("❌ لطفاً فقط تصاویر ارسال کنید یا 'اتمام ارسال تصاویر' را بزنید.")

    elif state == 'new_project_details_date':
        if text == "⬅️ بازگشت":
            context.user_data['state'] = 'new_project_details'
            await update.message.reply_text(
                f"📋 جزئیات درخواست:",
                reply_markup=create_dynamic_keyboard(context)
            )
            return
        if validate_date(text):
            context.user_data['need_date'] = text
            context.user_data['state'] = 'new_project_details'
            await update.message.reply_text(
                f"📅 تاریخ نیاز ثبت شد: {text}",
                reply_markup=create_dynamic_keyboard(context)
            )
        else:
            await update.message.reply_text("❌ تاریخ نامعتبر! لطفاً به فرمت 1403/10/15 وارد کنید.")

    elif state == 'new_project_details_deadline':
        if text == "⬅️ بازگشت":
            context.user_data['state'] = 'new_project_details'
            await update.message.reply_text(
                f"📋 جزئیات درخواست:",
                reply_markup=create_dynamic_keyboard(context)
            )
            return
        deadline = validate_deadline(text)
        if deadline:
            context.user_data['deadline'] = deadline
            context.user_data['state'] = 'new_project_details'
            await update.message.reply_text(
                f"⏳ مهلت انجام ثبت شد: {deadline} روز",
                reply_markup=create_dynamic_keyboard(context)
            )
        else:
            await update.message.reply_text("❌ مهلت نامعتبر! لطفاً یک عدد وارد کنید.")

    elif state == 'new_project_details_budget':
        if text == "⬅️ بازگشت":
            context.user_data['state'] = 'new_project_details'
            await update.message.reply_text(
                f"📋 جزئیات درخواست:",
                reply_markup=create_dynamic_keyboard(context)
            )
            return
        budget = clean_budget(text)
        if budget:
            context.user_data['budget'] = budget
            context.user_data['state'] = 'new_project_details'
            await update.message.reply_text(
                f"💰 بودجه ثبت شد: {budget} تومان",
                reply_markup=create_dynamic_keyboard(context)
            )
        else:
            await update.message.reply_text("❌ بودجه نامعتبر! لطفاً یک عدد وارد کنید.")

    elif state == 'new_project_details_quantity':
        if text == "⬅️ بازگشت":
            context.user_data['state'] = 'new_project_details'
            await update.message.reply_text(
                f"📋 جزئیات درخواست:",
                reply_markup=create_dynamic_keyboard(context)
            )
            return
        context.user_data['quantity'] = text
        context.user_data['state'] = 'new_project_details'
        await update.message.reply_text(
            f"📏 مقدار و واحد ثبت شد: {text}",
            reply_markup=create_dynamic_keyboard(context)
        )

    elif state == 'view_projects_initial' or state == 'view_projects_list':
        if text == "⬅️ بازگشت":
            context.user_data['state'] = None
            await start(update, context)
            return
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
                        return
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
        else:
            await update.message.reply_text("❌ گزینه نامعتبر! لطفاً یکی از دکمه‌ها را انتخاب کنید.")

async def submit_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = {
        'title': generate_title(context),
        'description': context.user_data.get('description', ''),
        'category': context.user_data.get('category_id', ''),
        'service_location': context.user_data.get('service_location', ''),
        'location': context.user_data.get('location', None),
        'budget': context.user_data.get('budget', None),
        'deadline_date': convert_deadline_to_date(context.user_data.get('deadline', None)),
        'start_date': context.user_data.get('need_date', None),
        'files': await upload_files(context.user_data.get('files', []), context),
        'user': {'telegram_id': str(update.effective_user.id)}
    }
    try:
        response = requests.post(f"{BASE_URL}projects/", json=data)
        if response.status_code == 201:
            await update.message.reply_text("🎉 درخواست شما ثبت شد! مجری‌ها به‌زودی پیشنهاد می‌دن.")
        else:
            await update.message.reply_text(f"❌ خطا در ثبت درخواست: {response.text[:50]}...")
    except requests.exceptions.ConnectionError:
        await update.message.reply_text("❌ خطا: سرور بک‌اند در دسترس نیست.")
    context.user_data.clear()
    await start(update, context)