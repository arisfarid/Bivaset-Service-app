# keyboards.py
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup

# منوی اصلی 
MAIN_MENU_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("درخواست خدمات | کارفرما 👔", callback_data="employer")],
    [InlineKeyboardButton("پیشنهاد قیمت | مجری 🦺", callback_data="contractor")],
])

# منوی کارفرما
EMPLOYER_MENU_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("📋 درخواست خدمات جدید", callback_data="new_request")],
    [InlineKeyboardButton("📊 مشاهده درخواست‌ها", callback_data="view_projects")],
    [InlineKeyboardButton("⬅️ بازگشت", callback_data="main_menu")]
])

# منوی مجری
CONTRACTOR_MENU_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("📋 مشاهده درخواست‌ها", callback_data="view_requests")],
    [InlineKeyboardButton("💡 پیشنهاد کار", callback_data="offer_work")],
    [InlineKeyboardButton("⬅️ بازگشت", callback_data="main_menu")]
])

# منوی انتخاب محل خدمات
LOCATION_TYPE_MENU_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("🏠 محل من", callback_data="loc_client")],
    [InlineKeyboardButton("🔧 محل مجری", callback_data="loc_contractor")],
    [InlineKeyboardButton("💻 غیرحضوری", callback_data="loc_remote")],
    [InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_desc")]
])

# منوی ارسال لوکیشن (از ReplyKeyboardMarkup استفاده می‌کنیم)
LOCATION_INPUT_MENU = ReplyKeyboardMarkup([
    [KeyboardButton("📲 ارسال موقعیت فعلی", request_location=True)],
    [KeyboardButton("⬅️ بازگشت")]
], resize_keyboard=True)

# منوی inline ارسال لوکیشن
LOCATION_INPUT_MENU_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("📍 انتخاب از نقشه", callback_data="send_location")],
    [InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_location_type")]
])

# منوی مدیریت فایل‌ها
FILE_MANAGEMENT_MENU_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("🏁 اتمام ارسال تصاویر", callback_data="finish_files")],
    [InlineKeyboardButton("📋 مدیریت عکس‌ها", callback_data="manage_photos")],
    [InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_details")]
])

# منوی مشاهده پروژه‌ها
VIEW_PROJECTS_MENU_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("درخواست‌های باز", callback_data="open_projects")],
    [InlineKeyboardButton("درخواست‌های بسته", callback_data="closed_projects")],
    [InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_employer_menu")]
])

# منوی ثبت‌نام با KeyboardButton برای ارسال شماره تماس
REGISTER_MENU = ReplyKeyboardMarkup([
    [KeyboardButton("ثبت شماره تلفن", request_contact=True)]
], resize_keyboard=True)

# تنظیم کیبورد ثبت شماره به صورت یک دکمه ساده
REGISTER_MENU_KEYBOARD = ReplyKeyboardMarkup(
    [[KeyboardButton("📱 به اشتراک گذاشتن شماره تماس", request_contact=True)]],
    resize_keyboard=True,
    one_time_keyboard=True
)

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
    """ساخت کیبورد دسته‌بندی‌ها با callback_data"""
    buttons = []
    for cat_id, cat in categories.items():
        if not cat['parent']:  # فقط دسته‌های اصلی
            buttons.append([
                InlineKeyboardButton(cat['name'], callback_data=f"cat_{cat_id}")
            ])
    buttons.append([InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(buttons)