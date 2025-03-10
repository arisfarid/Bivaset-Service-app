import os
import sys
import time
from datetime import datetime, timedelta
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
import requests
import re
from khayyam import JalaliDatetime

TOKEN = '7998946498:AAGu847Zq6HYrHdnEwSw2xwJDLF2INd3f4g'
BASE_URL = 'http://185.204.171.107:8000/api/'
BOT_FILE = os.path.abspath(__file__)
TIMESTAMP_FILE = '/home/ubuntu/Bivaset-Service-app/backend/last_update.txt'
print("Synced and updated from GitHub!")

# توابع کمکی (بدون تغییر)
async def get_user_phone(telegram_id):
    try:
        response = requests.get(f"{BASE_URL}users/?telegram_id={telegram_id}")
        if response.status_code == 200 and response.json():
            return response.json()[0]['phone']
        return None
    except requests.exceptions.ConnectionError:
        return None

async def get_categories():
    try:
        response = requests.get(f"{BASE_URL}categories/")
        if response.status_code == 200:
            categories = response.json()
            cat_dict = {cat['id']: {'name': cat['name'], 'parent': cat['parent'], 'children': cat['children']} for cat in categories}
            return cat_dict
        return {}
    except requests.exceptions.ConnectionError:
        return {}

async def upload_files(file_ids, context):
    uploaded_urls = []
    for file_id in file_ids:
        try:
            file = await context.bot.get_file(file_id)
            file_data = await file.download_as_bytearray()
            files = {'file': ('image.jpg', file_data, 'image/jpeg')}
            response = requests.post(f"{BASE_URL}upload/", files=files)
            if response.status_code == 201:
                uploaded_urls.append(response.json().get('file_url'))
            else:
                uploaded_urls.append(None)
        except Exception as e:
            uploaded_urls.append(None)
    return uploaded_urls

def get_last_mod_time():
    return os.path.getmtime(BOT_FILE)

def save_timestamp():
    with open(TIMESTAMP_FILE, 'w') as f:
        f.write(str(get_last_mod_time()))

def load_timestamp():
    if os.path.exists(TIMESTAMP_FILE):
        with open(TIMESTAMP_FILE, 'r') as f:
            return float(f.read())
    return 0

async def check_for_updates(context: ContextTypes.DEFAULT_TYPE):
    last_mod_time = get_last_mod_time()
    saved_time = load_timestamp()
    if last_mod_time > saved_time:
        print("Code updated, restarting bot...")
        save_timestamp()
        for chat_id in context.bot_data.get('active_chats', []):
            await context.bot.send_message(
                chat_id=chat_id,
                text="🎉 ربات آپدیت شد! خدمات جدید رو امتحان کن.",
                disable_notification=True
            )
        os.execv(sys.executable, [sys.executable] + sys.argv)

def persian_to_english(text):
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    english_digits = '0123456789'
    translation_table = str.maketrans(persian_digits, english_digits)
    return text.translate(translation_table)

def clean_budget(budget_str):
    if not budget_str:
        return None
    budget_str = persian_to_english(budget_str)
    budget_str = ''.join(filter(str.isdigit, budget_str))
    return int(budget_str) if budget_str and budget_str.isdigit() else None

def validate_deadline(deadline_str):
    if not deadline_str:
        return None
    deadline_str = persian_to_english(deadline_str)
    if deadline_str.isdigit():
        return deadline_str
    return None

def validate_date(date_str):
    date_str = persian_to_english(date_str)
    pattern = r'^\d{4}/\d{2}/\d{2}$'
    if not re.match(pattern, date_str):
        return False
    try:
        year, month, day = map(int, date_str.split('/'))
        input_date = JalaliDatetime(year, month, day)
        today = JalaliDatetime.now()
        if input_date >= today:
            return True
        return False
    except ValueError:
        return False

def convert_deadline_to_date(deadline_str):
    if not deadline_str:
        return None
    deadline_str = persian_to_english(deadline_str)
    days = int(deadline_str)
    return (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')

def generate_title(context):
    desc = context.user_data.get('description', '')
    category_id = context.user_data.get('category_id', '')
    categories = context.user_data.get('categories', {})
    category_name = categories.get(category_id, {}).get('name', 'نامشخص')
    location = context.user_data.get('location', None)
    deadline = context.user_data.get('deadline', None)
    quantity = context.user_data.get('quantity', None)
    service_location = context.user_data.get('service_location', '')
    
    title = f"{category_name}: {desc[:20]}"
    if service_location == 'remote':
        title += " (غیرحضوری)"
    else:
        city = "تهران" if location else "محل نامشخص"
        title += f" در {city}"
    if deadline:
        title += f"، مهلت {deadline} روز"
    if quantity:
        title += f" ({quantity})"
    return title.strip()

# هندلرها
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.full_name or "کاربر"
    telegram_id = str(update.effective_user.id)
    phone = await get_user_phone(telegram_id)
    if phone and phone != f"tg_{telegram_id}":
        context.user_data['phone'] = phone
    keyboard = [
        [KeyboardButton("📋 درخواست خدمات (کارفرما)")],
        [KeyboardButton("🔧 پیشنهاد قیمت (مجری)")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"👋 سلام {name}! به خدمات بی‌واسط خوش اومدی!\n"
        "من اینجا کمکت می‌کنم کاملاً رایگان خدمات درخواست کنی یا کار پیدا کنی. چی می‌خوای امروز؟ ✨",
        reply_markup=reply_markup
    )
    if 'active_chats' not in context.bot_data:
        context.bot_data['active_chats'] = []
    if update.effective_chat.id not in context.bot_data['active_chats']:
        context.bot_data['active_chats'].append(update.effective_chat.id)

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    phone = contact.phone_number
    name = update.effective_user.full_name or "کاربر"
    telegram_id = str(update.effective_user.id)
    url = BASE_URL + 'users/'
    data = {'phone': phone, 'telegram_id': telegram_id, 'name': name, 'role': context.user_data.get('role', 'client')}
    try:
        response = requests.post(url, json=data)
        context.user_data['phone'] = phone
        if response.status_code in [200, 201]:
            message = f"🎉 ثبت‌نام شد، {name}!"
        elif response.status_code == 400 and "phone" in response.text:
            message = f"👋 خوش اومدی، {name}! شماره‌ات قبلاً ثبت شده."
        else:
            message = f"❌ خطا در ثبت‌نام: {response.text[:50]}..."
        await update.message.reply_text(message)
        await start(update, context)
    except requests.exceptions.ConnectionError:
        await update.message.reply_text("❌ خطا: سرور بک‌اند در دسترس نیست.")

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    location = update.message.location
    context.user_data['location'] = {'longitude': location.longitude, 'latitude': location.latitude}
    context.user_data['state'] = 'new_project_details'
    await update.message.reply_text(
        f"📋 جزئیات درخواست\n"
        "اگه بخوای می‌تونی برای راهنمایی بهتر مجری‌ها این اطلاعات رو هم وارد کنی:",
        reply_markup=create_dynamic_keyboard(context)
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('state') != 'new_project_details_files':
        await update.message.reply_text("❌ لطفاً اول '📸 تصاویر یا فایل' رو انتخاب کن!")
        return
    if 'files' not in context.user_data:
        context.user_data['files'] = []
    
    if len(context.user_data['files']) >= 5:
        await update.message.reply_text("📸 تعداد تصاویر قابل ارسال پر شده. عکس جدید جایگزین اولین عکس شد.")
        context.user_data['files'].pop(0)
    
    photo = update.message.photo[-1]
    context.user_data['files'].append(photo.file_id)
    await update.message.reply_text(f"📸 عکس {len(context.user_data['files'])} از 5 دریافت شد.")
    
    keyboard = [
        [KeyboardButton("🏁 اتمام ارسال تصاویر"), KeyboardButton("⬅️ بازگشت")]
    ]
    await update.message.reply_text(
        "📸 اگه دیگه عکسی نداری، 'اتمام ارسال تصاویر' رو بزن:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

    if len(context.user_data['files']) >= 5:
        context.user_data['state'] = 'new_project_details'
        await update.message.reply_text(
            f"📋 جزئیات درخواست\n"
            "اگه بخوای می‌تونی برای راهنمایی بهتر مجری‌ها این اطلاعات رو هم وارد کنی:",
            reply_markup=create_dynamic_keyboard(context)
        )

def create_dynamic_keyboard(context):
    buttons = []
    if 'files' not in context.user_data:
        buttons.append([KeyboardButton("📸 تصاویر یا فایل")])
    if 'need_date' not in context.user_data:
        buttons.append([KeyboardButton("📅 تاریخ نیاز")])
    if 'deadline' not in context.user_data:
        buttons.append([KeyboardButton("⏳ مهلت انجام")])
    if 'budget' not in context.user_data:
        buttons.append([KeyboardButton("💰 بودجه")])
    if 'quantity' not in context.user_data:
        buttons.append([KeyboardButton("📏 مقدار و واحد")])
    buttons.append([KeyboardButton("⬅️ بازگشت"), KeyboardButton("✅ ثبت درخواست")])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

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
        context.user_data.clear()  # ریست کردن داده‌ها
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

    elif context.user_data.get('state') == 'new_project_category':
        if text == "⬅️ بازگشت":
            context.user_data['state'] = None
            await start(update, context)
        else:
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

    elif context.user_data.get('state') == 'new_project_subcategory':
        if text == "⬅️ بازگشت":
            context.user_data['state'] = 'new_project_category'
            categories = context.user_data['categories']
            root_cats = [cat_id for cat_id, cat in categories.items() if cat['parent'] is None]
            keyboard = [[KeyboardButton(categories[cat_id]['name'])] for cat_id in root_cats] + [[KeyboardButton("⬅️ بازگشت")]]
            await update.message.reply_text(
                f"🌟 دسته‌بندی خدماتت رو انتخاب کن:",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
        else:
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

    elif context.user_data.get('state') == 'new_project_desc':
        if text == "⬅️ بازگشت":
            context.user_data['state'] = 'new_project_subcategory'
            categories = context.user_data['categories']
            sub_cats = categories[context.user_data['category_group']]['children']
            keyboard = [[KeyboardButton(categories[cat_id]['name'])] for cat_id in sub_cats] + [[KeyboardButton("⬅️ بازگشت")]]
            await update.message.reply_text(
                f"📌 زیرمجموعه '{categories[context.user_data['category_group']]['name']}' رو انتخاب کن:",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
        else:
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

    elif context.user_data.get('state') == 'new_project_location':
        if text == "⬅️ بازگشت":
            context.user_data['state'] = 'new_project_desc'
            await update.message.reply_text(
                f"🌟 حالا توضیحات خدماتت رو بگو تا مجری بهتر بتونه قیمت بده.\n"
                "نمونه خوب: 'نصب 2 شیر پیسوار توی آشپزخونه، جنس استیل، تا آخر هفته نیاز دارم.'"
            )
        elif text == "➡️ ادامه":
            if context.user_data.get('service_location') == 'client_site' and 'location' not in context.user_data:
                await update.message.reply_text("❌ لطفاً اول لوکیشن رو ثبت کن!")
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
                    f"📍 انتخاب محل از روی نقشه باعث می‌شه مجریان نزدیک‌تر با قیمت مناسب‌تر بهت پیشنهاد بدن.\n"
                    "محل خدماتت رو چطور می‌خوای بفرستی؟\n"
                    "- 'انتخاب از نقشه': توی تلگرام روی گیره (📎) بزن، 'Location' رو انتخاب کن، بعد از نقشه پین کن.\n"
                    "- 'ارسال موقعیت فعلی': دکمه زیر رو بزن.",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
            else:
                context.user_data['location'] = None
                context.user_data['state'] = 'new_project_details'
                await update.message.reply_text(
                    f"📋 جزئیات درخواست\n"
                    "اگه بخوای می‌تونی برای راهنمایی بهتر مجری‌ها این اطلاعات رو هم وارد کنی:",
                    reply_markup=create_dynamic_keyboard(context)
                )
        else:
            await update.message.reply_text("❌ گزینه نامعتبر! لطفاً از منو انتخاب کن.")

    elif context.user_data.get('state') == 'new_project_location_input':
        if text == "⬅️ بازگشت":
            context.user_data['state'] = 'new_project_location'
            keyboard = [
                [KeyboardButton("🏠 محل کارفرما"), KeyboardButton("🔧 محل مجری"), KeyboardButton("💻 غیرحضوری")],
                [KeyboardButton("⬅️ بازگشت"), KeyboardButton("➡️ ادامه")]
            ]
            await update.message.reply_text(
                f"🌟 محل انجام خدماتت رو انتخاب کن:",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
        elif text == "➡️ ادامه":
            if 'location' not in context.user_data:
                await update.message.reply_text("❌ لطفاً اول لوکیشن رو ثبت کن!")
                return
            context.user_data['state'] = 'new_project_details'
            await update.message.reply_text(
                f"📋 جزئیات درخواست\n"
                "اگه بخوای می‌تونی برای راهنمایی بهتر مجری‌ها این اطلاعات رو هم وارد کنی:",
                reply_markup=create_dynamic_keyboard(context)
            )
        elif text == "📍 انتخاب از نقشه":
            await update.message.reply_text(
                f"📍 توی تلگرام روی گیره (📎) بزن، 'Location' رو انتخاب کن، بعد از نقشه لوکیشن خدماتت رو پین کن و بفرست."
            )
        else:
            await update.message.reply_text(
                f"❌ لطفاً فقط لوکیشن بفرست! از 'انتخاب از نقشه' یا 'ارسال موقعیت فعلی' استفاده کن یا لوکیشن رو مستقیم از تلگرام بفرست."
            )

    elif context.user_data.get('state') == 'new_project_details':
        if text == "⬅️ بازگشت":
            if context.user_data.get('service_location') == 'client_site':
                context.user_data['state'] = 'new_project_location_input'
                keyboard = [
                    [KeyboardButton("📍 انتخاب از نقشه"), KeyboardButton("📲 ارسال موقعیت فعلی", request_location=True)],
                    [KeyboardButton("⬅️ بازگشت"), KeyboardButton("➡️ ادامه")]
                ]
                await update.message.reply_text(
                    f"📍 انتخاب محل از روی نقشه باعث می‌شه مجریان نزدیک‌تر با قیمت مناسب‌تر بهت پیشنهاد بدن.\n"
                    "محل خدماتت رو چطور می‌خوای بفرستی؟\n"
                    "- 'انتخاب از نقشه': توی تلگرام روی گیره (📎) بزن، 'Location' رو انتخاب کن، بعد از نقشه پین کن.\n"
                    "- 'ارسال موقعیت فعلی': دکمه زیر رو بزن.",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
            else:
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
        elif text == "📸 تصاویر یا فایل":
            context.user_data['state'] = 'new_project_details_files'
            if 'files' not in context.user_data:
                context.user_data['files'] = []
            await update.message.reply_text(
                f"📸 تا 5 عکس می‌تونی بفرستی. لطفاً تصاویر مربوط به خدماتت رو بفرست:"
            )
        elif text == "📅 تاریخ نیاز":
            context.user_data['state'] = 'new_project_details_date'
            await update.message.reply_text(
                f"📅 تاریخی که می‌خوای خدماتت شروع بشه رو بگو (مثلاً '1403/12/20'):"
            )
        elif text == "⏳ مهلت انجام":
            context.user_data['state'] = 'new_project_details_deadline'
            await update.message.reply_text(
                f"⏳ مهلت انجام خدماتت رو فقط با عدد روز بگو (مثلاً '3'):"
            )
        elif text == "💰 بودجه":
            context.user_data['state'] = 'new_project_details_budget'
            await update.message.reply_text(
                f"💰 بودجه پیشنهادی خدماتت رو به تومان و فقط عدد بگو (مثلاً '500000'):"
            )
        elif text == "📏 مقدار و واحد":
            context.user_data['state'] = 'new_project_details_quantity'
            await update.message.reply_text(
                f"📏 مقدار و واحد خدماتت رو بگو (مثلاً '2 عدد'):"
            )
        elif text == "✅ ثبت درخواست":
            if 'description' not in context.user_data or (context.user_data.get('service_location') == 'client_site' and 'location' not in context.user_data):
                await update.message.reply_text("❌ لطفاً اطلاعات اجباری (توضیحات و لوکیشن در صورت لزوم) رو تکمیل کن!")
                return
            context.user_data['project_title'] = generate_title(context)
            url = BASE_URL + 'projects/'
            data = {
                'user_telegram_id': telegram_id,
                'title': context.user_data['project_title'],
                'category': context.user_data['category_id'],
                'service_location': context.user_data['service_location'],
                'budget': clean_budget(context.user_data.get('budget')),
                'description': context.user_data['description'],
                'address': ''
            }
            if 'location' in context.user_data and context.user_data['location'] is not None:
                data['location'] = f"POINT({context.user_data['location']['longitude']} {context.user_data['location']['latitude']})"
            if 'deadline' in context.user_data:
                data['deadline_date'] = convert_deadline_to_date(context.user_data['deadline'])
            if 'need_date' in context.user_data:
                data['start_date'] = context.user_data['need_date']
            try:
                if 'files' in context.user_data and context.user_data['files']:
                    file_urls = await upload_files(context.user_data['files'], context)
                    data['files'] = [url for url in file_urls if url]  # فقط URLهای موفق
                if 'files' in data and data['files']:
                    files_to_upload = [(f"files[{i}]", (None, url)) for i, url in enumerate(data['files'])]
                    response = requests.post(url, data=data, files=files_to_upload)
                else:
                    response = requests.post(url, json=data)
                if response.status_code == 201:
                    project_data = response.json()
                    project_id = project_data.get('id', 'نامشخص')
                    category_name = context.user_data['categories'][context.user_data['category_id']]['name']
                    summary = f"✅ درخواست شما ثبت شد!\n\n" \
                              f"📋 *کد درخواست*: {project_id}\n" \
                              f"📌 *دسته‌بندی*: {category_name}\n" \
                              f"📝 *توضیحات*: {context.user_data.get('description', 'ندارد')}\n"
                    if 'need_date' in context.user_data:
                        summary += f"📅 *تاریخ شروع*: {context.user_data['need_date']}\n"
                    if 'deadline' in context.user_data:
                        summary += f"⏳ *مهلت انجام*: {context.user_data['deadline']} روز\n"
                    if 'budget' in context.user_data:
                        budget = clean_budget(context.user_data['budget'])
                        summary += f"💰 *بودجه*: {budget} تومان\n"
                    if 'quantity' in context.user_data:
                        summary += f"📏 *مقدار*: {context.user_data['quantity']}\n"
                    if 'location' in context.user_data and context.user_data['location'] is not None and context.user_data['service_location'] != 'remote':
                        lat, lon = context.user_data['location']['latitude'], context.user_data['location']['longitude']
                        summary += f"📍 *موقعیت*: [نمایش روی نقشه](https://maps.google.com/maps?q={lat},{lon})\n"
                    else:
                        summary += f"📍 *موقعیت*: غیرحضوری\n"
                    if 'files' in context.user_data and context.user_data['files']:
                        file_urls = await upload_files(context.user_data['files'], context)
                        summary += "📸 *تصاویر*:\n"
                        for i, url in enumerate(file_urls, 1):
                            if url:
                                summary += f"- [عکس {i}]({url})\n"
                            else:
                                summary += f"- عکس {i} (خطا در آپلود)\n"

                    inline_keyboard = [
                        [InlineKeyboardButton("✏️ ویرایش", callback_data=f"edit_{project_id}"), InlineKeyboardButton("⏰ تمدید", callback_data=f"extend_{project_id}")],
                        [InlineKeyboardButton("🗑 حذف", callback_data=f"delete_{project_id}"), InlineKeyboardButton("✅ بستن", callback_data=f"close_{project_id}")],
                        [InlineKeyboardButton("💬 مشاهده پیشنهادها", callback_data=f"proposals_{project_id}")]
                    ]
                    if 'files' in context.user_data and context.user_data['files']:
                        await update.message.reply_photo(
                            photo=context.user_data['files'][0],
                            caption=summary,
                            parse_mode='Markdown',
                            reply_markup=InlineKeyboardMarkup(inline_keyboard)
                        )
                    else:
                        await update.message.reply_text(
                            summary,
                            parse_mode='Markdown',
                            reply_markup=InlineKeyboardMarkup(inline_keyboard)
                        )
                    # پاک کردن داده‌ها بعد از ثبت
                    context.user_data.clear()
                    context.user_data['categories'] = await get_categories()  # دوباره لود کردن دسته‌بندی‌ها
                    # بردن به منوی "مشاهده درخواست‌ها"
                    keyboard = [
                        [KeyboardButton("📋 درخواست خدمات جدید"), KeyboardButton("💬 مشاهده پیشنهادات")],
                        [KeyboardButton("📊 مشاهده درخواست‌ها"), KeyboardButton("⬅️ بازگشت")]
                    ]
                    await update.message.reply_text(
                        f"🎉 عالیه، {name}! می‌خوای خدمات جدید درخواست کنی یا پیشنهادات رو ببینی؟",
                        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                    )
                    context.user_data['state'] = None
                else:
                    await update.message.reply_text(f"❌ خطا در ثبت خدمات: {response.status_code} - {response.text[:50]}...")
            except requests.exceptions.ConnectionError:
                await update.message.reply_text("❌ خطا: سرور بک‌اند در دسترس نیست.")
            context.user_data['state'] = None

    elif context.user_data.get('state') == 'new_project_details_files':
        if text == "⬅️ بازگشت" or text == "🏁 اتمام ارسال تصاویر":
            context.user_data['state'] = 'new_project_details'
            await update.message.reply_text(
                f"📋 جزئیات درخواست\n"
                "اگه بخوای می‌تونی برای راهنمایی بهتر مجری‌ها این اطلاعات رو هم وارد کنی:",
                reply_markup=create_dynamic_keyboard(context)
            )
        else:
            await update.message.reply_text("📸 لطفاً فقط عکس بفرست، متن قبول نیست!")

    elif context.user_data.get('state') == 'new_project_details_date':
        if text == "⬅️ بازگشت":
            context.user_data['state'] = 'new_project_details'
            await update.message.reply_text(
                f"📋 جزئیات درخواست\n"
                "اگه بخوای می‌تونی برای راهنمایی بهتر مجری‌ها این اطلاعات رو هم وارد کنی:",
                reply_markup=create_dynamic_keyboard(context)
            )
        elif text in ["امروز", "فردا", "پس‌فردا"]:
            today = JalaliDatetime.now()
            if text == "امروز":
                date_str = today.strftime('%Y/%m/%d')
            elif text == "فردا":
                date_str = (today + timedelta(days=1)).strftime('%Y/%m/%d')
            else:  # پس‌فردا
                date_str = (today + timedelta(days=2)).strftime('%Y/%m/%d')
            context.user_data['need_date'] = date_str
            await update.message.reply_text(f"📅 تاریخ نیاز ({text}) ثبت شد.")
            context.user_data['state'] = 'new_project_details'
            await update.message.reply_text(
                f"📋 جزئیات درخواست\n"
                "اگه بخوای می‌تونی برای راهنمایی بهتر مجری‌ها این اطلاعات رو هم وارد کنی:",
                reply_markup=create_dynamic_keyboard(context)
            )
        else:
            if validate_date(text):
                context.user_data['need_date'] = text
                await update.message.reply_text("📅 تاریخ نیاز ثبت شد.")
                context.user_data['state'] = 'new_project_details'
                await update.message.reply_text(
                    f"📋 جزئیات درخواست\n"
                    "اگه بخوای می‌تونی برای راهنمایی بهتر مجری‌ها این اطلاعات رو هم وارد کنی:",
                    reply_markup=create_dynamic_keyboard(context)
                )
            else:
                await update.message.reply_text(
                    "❌ فرمت تاریخ اشتباهه یا تاریخ قبل از امروزه! لطفاً به شکل '1403/12/20' وارد کن یا یکی از دکمه‌ها رو انتخاب کن:",
                    reply_markup=ReplyKeyboardMarkup([
                        [KeyboardButton("امروز"), KeyboardButton("فردا"), KeyboardButton("پس‌فردا")],
                        [KeyboardButton("⬅️ بازگشت")]
                    ], resize_keyboard=True)
                )

    elif context.user_data.get('state') == 'new_project_details_deadline':
        if text == "⬅️ بازگشت":
            context.user_data['state'] = 'new_project_details'
            await update.message.reply_text(
                f"📋 جزئیات درخواست\n"
                "اگه بخوای می‌تونی برای راهنمایی بهتر مجری‌ها این اطلاعات رو هم وارد کنی:",
                reply_markup=create_dynamic_keyboard(context)
            )
        else:
            # استخراج عدد از متن
            numbers = ''.join(filter(str.isdigit, persian_to_english(text)))
            if numbers:
                context.user_data['deadline'] = numbers
                await update.message.reply_text(f"⏳ مهلت انجام ({numbers} روز) ثبت شد.")
                context.user_data['state'] = 'new_project_details'
                await update.message.reply_text(
                    f"📋 جزئیات درخواست\n"
                    "اگه بخوای می‌تونی برای راهنمایی بهتر مجری‌ها این اطلاعات رو هم وارد کنی:",
                    reply_markup=create_dynamic_keyboard(context)
                )
            else:
                await update.message.reply_text("❌ لطفاً یه عدد برای روز وارد کن (مثلاً '3' یا '3 روز')!")

    elif context.user_data.get('state') == 'new_project_details_budget':
        if text == "⬅️ بازگشت":
            context.user_data['state'] = 'new_project_details'
            await update.message.reply_text(
                f"📋 جزئیات درخواست\n"
                "اگه بخوای می‌تونی برای راهنمایی بهتر مجری‌ها این اطلاعات رو هم وارد کنی:",
                reply_markup=create_dynamic_keyboard(context)
            )
        else:
            budget = clean_budget(text)
            if budget is not None:
                context.user_data['budget'] = str(budget)
                await update.message.reply_text("💰 بودجه ثبت شد.")
                context.user_data['state'] = 'new_project_details'
                await update.message.reply_text(
                    f"📋 جزئیات درخواست\n"
                    "اگه بخوای می‌تونی برای راهنمایی بهتر مجری‌ها این اطلاعات رو هم وارد کنی:",
                    reply_markup=create_dynamic_keyboard(context)
                )
            else:
                await update.message.reply_text("❌ لطفاً فقط عدد به تومان وارد کن (مثلاً '500000')!")

    elif context.user_data.get('state') == 'new_project_details_quantity':
        if text == "⬅️ بازگشت":
            context.user_data['state'] = 'new_project_details'
            await update.message.reply_text(
                f"📋 جزئیات درخواست\n"
                "اگه بخوای می‌تونی برای راهنمایی بهتر مجری‌ها این اطلاعات رو هم وارد کنی:",
                reply_markup=create_dynamic_keyboard(context)
            )
        else:
            context.user_data['quantity'] = text
            await update.message.reply_text("📏 مقدار و واحد ثبت شد.")
            context.user_data['state'] = 'new_project_details'
            await update.message.reply_text(
                f"📋 جزئیات درخواست\n"
                "اگه بخوای می‌تونی برای راهنمایی بهتر مجری‌ها این اطلاعات رو هم وارد کنی:",
                reply_markup=create_dynamic_keyboard(context)
            )

    elif text == "📊 مشاهده درخواست‌ها":
        context.user_data['state'] = 'view_projects_initial'
        telegram_id = str(update.effective_user.id)
        try:
            response = requests.get(f"{BASE_URL}projects/?user_telegram_id={telegram_id}&ordering=-id&limit=5")
            if response.status_code == 200:
                projects = response.json()[:5]  # فقط 5 تا آخر
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

    elif context.user_data.get('state') in ['view_projects_initial', 'view_projects_list'] and text in ["درخواست‌های باز", "درخواست‌های بسته"]:
        context.user_data['state'] = 'view_projects_list'
        status = 'open' if text == "درخواست‌های باز" else 'closed'
        offset = context.user_data.get('project_offset', 0)
        try:
            response = requests.get(f"{BASE_URL}projects/?user_telegram_id={telegram_id}&status={status}&ordering=-id&limit=10&offset={offset}")
            if response.status_code == 200:
                projects = response.json()[:10]  # فقط 10 تا
                if not projects:
                    await update.message.reply_text(f"📭 هیچ درخواست {text} پیدا نشد!")
                    return
                message = f"📋 لیست {text} (حداکثر ۱۰ تا):\nبرای مشاهده جزئیات یا مدیریت، روی درخواست ضربه بزنید:\n\n"
                inline_keyboard = []
                for i, project in enumerate(projects, 1):
                    message += f"{i}. {project['title']} (کد: {project['id']})\n"
                    inline_keyboard.append([InlineKeyboardButton(f"{project['title']} (کد: {project['id']})", callback_data=f"{project['id']}")])
                if len(response.json()) > 10:  # چک کردن اگر بیشتر از 10 تا هست
                    context.user_data['project_offset'] = offset + 10
                    message += f"\nبرای دیدن ادامه، دوباره '{text}' رو بزن."
                else:
                    context.user_data['project_offset'] = 0  # ریست
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
        except requests.exceptions.ConnectionError:
            await update.message.reply_text("❌ خطا: سرور بک‌اند در دسترس نیست.")

    elif text == "⬅️ بازگشت" and context.user_data.get('state') in [None, 'view_projects_initial', 'view_projects_list']:
        context.user_data['state'] = None
        await start(update, context)

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
                summary += "📸 *تصاویر*:\n" + "\n.join([f"- [عکس]({f})" for f in project['files']])
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

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    app.add_handler(MessageHandler(filters.LOCATION, handle_location))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.job_queue.run_repeating(check_for_updates, interval=10)
    save_timestamp()
    app.run_polling()

if __name__ == '__main__':
    main()
```