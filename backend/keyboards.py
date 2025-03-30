# keyboards.py
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

# منوی اصلی
MAIN_MENU_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("درخواست خدمات | کارفرما 👔")],
    [InlineKeyboardButton("پیشنهاد قیمت | مجری 🦺")]
], resize_keyboard=True, one_time_keyboard=True)

# منوی کارفرما
EMPLOYER_MENU_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("📋 درخواست خدمات جدید"), InlineKeyboardButton("📊 مشاهده درخواست‌ها")],
    [InlineKeyboardButton("⬅️ بازگشت")]
], resize_keyboard=True)

# منوی مجری
CONTRACTOR_MENU_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("📋 مشاهده درخواست‌ها"), InlineKeyboardButton("💡 پیشنهاد کار")],
    [InlineKeyboardButton("⬅️ بازگشت")]
], resize_keyboard=True)

# منوی انتخاب محل خدمات
LOCATION_TYPE_MENU_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("🏠 محل من"), InlineKeyboardButton("🔧 محل مجری")],
    [InlineKeyboardButton("💻 غیرحضوری"), InlineKeyboardButton("⬅️ بازگشت")],
    [InlineKeyboardButton("➡️ ادامه")]
], resize_keyboard=True)

# منوی ارسال لوکیشن
LOCATION_INPUT_MENU_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("📍 انتخاب از نقشه", request_location=True), InlineKeyboardButton("📲 ارسال موقعیت فعلی", request_location=True)],
    [InlineKeyboardButton("⬅️ بازگشت"), InlineKeyboardButton("➡️ ادامه")]
], resize_keyboard=True)

# منوی مدیریت فایل‌ها
FILE_MANAGEMENT_MENU_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("🏁 اتمام ارسال تصاویر"), InlineKeyboardButton("📋 مدیریت عکس‌ها")],
    [InlineKeyboardButton("⬅️ بازگشت")]
], resize_keyboard=True)

# منوی مشاهده پروژه‌ها
VIEW_PROJECTS_MENU_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("درخواست‌های باز"), InlineKeyboardButton("درخواست‌های بسته")],
    [InlineKeyboardButton("⬅️ بازگشت")]
], resize_keyboard=True)

# منوی ثبت‌نام
REGISTER_MENU_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("ثبت شماره تلفن", request_contact=True)]
], resize_keyboard=True, one_time_keyboard=True)

# منوی اینلاین کارفرما
EMPLOYER_INLINE_MENU_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("📋 درخواست خدمات جدید", callback_data='new_project')],
    [InlineKeyboardButton("👀 مشاهده درخواست‌ها", callback_data='view_projects')],
])

# منوی اینلاین بازگشت
BACK_INLINE_MENU_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("⬅️ برگشت به ارسال", callback_data="back_to_upload")]
])

# منوی اینلاین مجری
CONTRACTOR_INLINE_MENU_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("📋 مشاهده درخواست‌ها", callback_data='view_requests')],
    [InlineKeyboardButton("💡 پیشنهاد کار", callback_data='offer_work')],
])

# منوی اینلاین ریستارت
RESTART_INLINE_MENU_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("🔄 راه‌اندازی مجدد", callback_data='restart')]
])

def create_dynamic_keyboard(context):
    buttons = []
    # همیشه دکمه تصاویر رو نشون بده
    buttons.append([InlineKeyboardButton("📸 تصاویر یا فایل")])
    
    if 'need_date' not in context.user_data:
        buttons.append([InlineKeyboardButton("📅 تاریخ نیاز")])
    if 'deadline' not in context.user_data:
        buttons.append([InlineKeyboardButton("⏳ مهلت انجام")])
    if 'budget' not in context.user_data:
        buttons.append([InlineKeyboardButton("💰 بودجه")])
    if 'quantity' not in context.user_data:
        buttons.append([InlineKeyboardButton("📏 مقدار و واحد")])
    buttons.append([InlineKeyboardButton("⬅️ بازگشت"), InlineKeyboardButton("✅ ثبت درخواست")])
    return InlineKeyboardMarkup(buttons, resize_keyboard=True)

def create_category_keyboard(categories):
    """ساخت کیبورد دسته‌بندی‌ها"""
    root_cats = [cat_id for cat_id, cat in categories.items() if cat['parent'] is None]
    keyboard = [[InlineKeyboardButton(categories[cat_id]['name'])] for cat_id in root_cats]
    keyboard.append([InlineKeyboardButton("⬅️ بازگشت")])
    return InlineKeyboardMarkup(keyboard, resize_keyboard=True)