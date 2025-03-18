# keyboards.py
from telegram import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup

# منوی اصلی
MAIN_MENU = ReplyKeyboardMarkup([
    ["درخواست خدمات | کارفرما 👔"],
    ["پیشنهاد قیمت | مجری 🦺"]
], resize_keyboard=True, one_time_keyboard=True)

# منوی کارفرما
EMPLOYER_MENU = ReplyKeyboardMarkup([
    [KeyboardButton("📋 درخواست خدمات جدید"), KeyboardButton("📊 مشاهده درخواست‌ها")],
    [KeyboardButton("⬅️ بازگشت")]
], resize_keyboard=True)

# منوی مجری
CONTRACTOR_MENU = ReplyKeyboardMarkup([
    [KeyboardButton("📋 مشاهده درخواست‌ها"), KeyboardButton("💡 پیشنهاد کار")],
    [KeyboardButton("⬅️ بازگشت")]
], resize_keyboard=True)

# منوی انتخاب محل خدمات
LOCATION_TYPE_MENU = ReplyKeyboardMarkup([
    [KeyboardButton("🏠 محل من"), KeyboardButton("🔧 محل مجری")],
    [KeyboardButton("💻 غیرحضوری"), KeyboardButton("⬅️ بازگشت")],
    [KeyboardButton("➡️ ادامه")]
], resize_keyboard=True)

# منوی ارسال لوکیشن
LOCATION_INPUT_MENU = ReplyKeyboardMarkup([
    [KeyboardButton("📍 انتخاب از نقشه", request_location=True), KeyboardButton("📲 ارسال موقعیت فعلی", request_location=True)],
    [KeyboardButton("⬅️ بازگشت"), KeyboardButton("➡️ ادامه")]
], resize_keyboard=True)

# منوی مدیریت فایل‌ها
FILE_MANAGEMENT_MENU = ReplyKeyboardMarkup([
    [KeyboardButton("🏁 اتمام ارسال تصاویر"), KeyboardButton("📋 مدیریت عکس‌ها")],
    [KeyboardButton("⬅️ بازگشت")]
], resize_keyboard=True)

# منوی مشاهده پروژه‌ها
VIEW_PROJECTS_MENU = ReplyKeyboardMarkup([
    [KeyboardButton("درخواست‌های باز"), KeyboardButton("درخواست‌های بسته")],
    [KeyboardButton("⬅️ بازگشت")]
], resize_keyboard=True)

# منوی ثبت‌نام
REGISTER_MENU = ReplyKeyboardMarkup([
    [KeyboardButton("ثبت شماره تلفن", request_contact=True)]
], resize_keyboard=True, one_time_keyboard=True)

# منوی اینلاین کارفرما
EMPLOYER_INLINE_MENU = InlineKeyboardMarkup([
    [InlineKeyboardButton("📋 درخواست خدمات جدید", callback_data='new_project')],
    [InlineKeyboardButton("👀 مشاهده درخواست‌ها", callback_data='view_projects')],
])

# منوی اینلاین بازگشت
BACK_INLINE_MENU = InlineKeyboardMarkup([
    [InlineKeyboardButton("⬅️ برگشت به ارسال", callback_data="back_to_upload")]
])

# منوی اینلاین ریستارت
RESTART_INLINE_MENU = InlineKeyboardMarkup([
    [InlineKeyboardButton("🔄 شروع دوباره", callback_data='restart')]
])