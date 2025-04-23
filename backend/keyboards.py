# keyboards.py
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

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
    [InlineKeyboardButton("🏠 محل من", callback_data="location_client")],
    [InlineKeyboardButton("🔧 محل مجری", callback_data="location_contractor")],
    [InlineKeyboardButton("💻 غیرحضوری", callback_data="location_remote")],
    [InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_categories")]
])

# منوی ارسال لوکیشن با دکمه درخواست موقعیت مکانی
LOCATION_INPUT_KEYBOARD = ReplyKeyboardMarkup([
    [KeyboardButton("📲 ارسال موقعیت فعلی", request_location=True)],
    [KeyboardButton("⬅️ بازگشت")]
], resize_keyboard=True)

# منوی inline ارسال لوکیشن
LOCATION_INPUT_MENU_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("📍 انتخاب از نقشه", callback_data="send_location")],
    [InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_location_type")]
])

# کیبورد حذف (برای برداشتن کیبوردهای معمولی)
REMOVE_KEYBOARD = ReplyKeyboardRemove()

# کیبورد بازگشت به منوی انتخاب محل
BACK_TO_LOCATION_KEYBOARD = InlineKeyboardMarkup([
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

# منوی راه‌اندازی مجدد - تغییر به URL دستور برای فراخوانی مستقیم /start
RESTART_INLINE_MENU_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("🔄 راه‌اندازی مجدد", url="https://t.me/BivasetBot?start=restart")]
])

# منوی بازگشت به توضیحات
BACK_TO_DESCRIPTION_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_location_type")]
])

# منوی اینلاین ثبت شماره تلفن
REGISTER_INLINE_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("📱 ثبت شماره تلفن", callback_data="register_phone")],
    [InlineKeyboardButton("🔄 شروع مجدد", callback_data="restart")]
])

# تابع ایجاد یک دکمه راه‌اندازی مجدد برای کاربران جدید
def create_restart_keyboard():
    """ایجاد کیبورد راه‌اندازی مجدد برای کاربران"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 شروع مجدد", callback_data="restart")],
    ])

def create_dynamic_keyboard(context):
    buttons = []
    # همیشه دکمه تصاویر رو نشون بده
    buttons.append([InlineKeyboardButton("📸 تصاویر یا فایل", callback_data="photo_management")])
    
    if 'need_date' not in context.user_data:
        buttons.append([InlineKeyboardButton("📅 تاریخ نیاز", callback_data="need_date")])
    if 'deadline' not in context.user_data:
        buttons.append([InlineKeyboardButton("⏳ مهلت انجام", callback_data="deadline")])
    if 'budget' not in context.user_data:
        buttons.append([InlineKeyboardButton("💰 بودجه", callback_data="budget")])
    if 'quantity' not in context.user_data:
        buttons.append([InlineKeyboardButton("📏 مقدار و واحد", callback_data="quantity")])
    buttons.append([InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_description"), InlineKeyboardButton("✅ ثبت درخواست", callback_data="submit_project")])
    return InlineKeyboardMarkup(buttons)

def create_category_keyboard(categories):
    """ساخت کیبورد دسته‌بندی‌ها"""
    root_cats = [cat_id for cat_id, cat in categories.items() if cat.get('parent') is None]
    keyboard = []
    
    for cat_id in root_cats:
        if cat_id in categories:
            keyboard.append([InlineKeyboardButton(categories[cat_id]['name'], callback_data=f"cat_{cat_id}")])
    
    keyboard.append([InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(keyboard)