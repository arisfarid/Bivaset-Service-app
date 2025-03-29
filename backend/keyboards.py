# keyboards.py
from telegram import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup

# منوی اصلی
MAIN_MENU_KEYBOARD = ReplyKeyboardMarkup([
    ["درخواست خدمات | کارفرما 👔"],
    ["پیشنهاد قیمت | مجری 🦺"]
], resize_keyboard=True, one_time_keyboard=True)

# منوی کارفرما
EMPLOYER_MENU_KEYBOARD = ReplyKeyboardMarkup([
    [KeyboardButton("📋 درخواست خدمات جدید"), KeyboardButton("📊 مشاهده درخواست‌ها")],
    [KeyboardButton("⬅️ بازگشت")]
], resize_keyboard=True)

# منوی مجری
CONTRACTOR_MENU_KEYBOARD = ReplyKeyboardMarkup([
    [KeyboardButton("📋 مشاهده درخواست‌ها"), KeyboardButton("💡 پیشنهاد کار")],
    [KeyboardButton("⬅️ بازگشت")]
], resize_keyboard=True)

# منوی انتخاب محل خدمات
LOCATION_TYPE_MENU_KEYBOARD = ReplyKeyboardMarkup([
    [KeyboardButton("🏠 محل من"), KeyboardButton("🔧 محل مجری")],
    [KeyboardButton("💻 غیرحضوری"), KeyboardButton("⬅️ بازگشت")],
    [KeyboardButton("➡️ ادامه")]
], resize_keyboard=True)

# منوی ارسال لوکیشن
LOCATION_INPUT_MENU_KEYBOARD = ReplyKeyboardMarkup([
    [KeyboardButton("📍 انتخاب از نقشه", request_location=True), KeyboardButton("📲 ارسال موقعیت فعلی", request_location=True)],
    [KeyboardButton("⬅️ بازگشت"), KeyboardButton("➡️ ادامه")]
], resize_keyboard=True)

# منوی مدیریت فایل‌ها
FILE_MANAGEMENT_MENU_KEYBOARD = ReplyKeyboardMarkup([
    [KeyboardButton("🏁 اتمام ارسال تصاویر"), KeyboardButton("📋 مدیریت عکس‌ها")],
    [KeyboardButton("⬅️ بازگشت")]
], resize_keyboard=True)

# منوی مشاهده پروژه‌ها
VIEW_PROJECTS_MENU_KEYBOARD = ReplyKeyboardMarkup([
    [KeyboardButton("درخواست‌های باز"), KeyboardButton("درخواست‌های بسته")],
    [KeyboardButton("⬅️ بازگشت")]
], resize_keyboard=True)

# منوی ثبت‌نام
REGISTER_MENU_KEYBOARD = ReplyKeyboardMarkup([
    [KeyboardButton("ثبت شماره تلفن", request_contact=True)]
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

def create_category_keyboard(categories):
    """ساخت کیبورد دسته‌بندی‌ها"""
    root_cats = [cat_id for cat_id, cat in categories.items() if cat['parent'] is None]
    keyboard = [[KeyboardButton(categories[cat_id]['name'])] for cat_id in root_cats]
    keyboard.append([KeyboardButton("⬅️ بازگشت")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)