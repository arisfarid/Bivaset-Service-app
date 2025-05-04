# keyboards.py
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from localization import get_message

# تابع ایجاد منوی اصلی با قابلیت لوکالایزیشن
def get_main_menu_keyboard(lang="fa"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(get_message("role_employer", lang=lang), callback_data="employer")],
        [InlineKeyboardButton(get_message("role_contractor", lang=lang), callback_data="contractor")]
    ])

# تابع ایجاد منوی کارفرما با قابلیت لوکالایزیشن
def get_employer_menu_keyboard(lang="fa"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(get_message("employer_new_request", lang=lang), callback_data="new_request")],
        [InlineKeyboardButton(get_message("employer_view_projects", lang=lang), callback_data="view_projects")],
        [InlineKeyboardButton(get_message("back", lang=lang), callback_data="main_menu")]
    ])

# تابع ایجاد منوی مجری با قابلیت لوکالایزیشن
def get_contractor_menu_keyboard(lang="fa"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(get_message("contractor_view_requests", lang=lang), callback_data="view_requests")],
        [InlineKeyboardButton(get_message("contractor_offer_work", lang=lang), callback_data="offer_work")],
        [InlineKeyboardButton(get_message("back", lang=lang), callback_data="main_menu")]
    ])

# تابع ایجاد کیبورد انتخاب محل خدمات با قابلیت لوکالایزیشن
def get_location_type_keyboard(lang="fa"):
    """ایجاد کیبورد انتخاب محل خدمات با قابلیت لوکالایزیشن"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(get_message("location_type_client", lang=lang), callback_data="location_client")],
        [InlineKeyboardButton(get_message("location_type_contractor", lang=lang), callback_data="location_contractor")],
        [InlineKeyboardButton(get_message("location_type_remote", lang=lang), callback_data="location_remote")],
        [InlineKeyboardButton(get_message("back", lang=lang), callback_data="back_to_categories")]
    ])

# تابع ایجاد کیبورد ارسال لوکیشن با قابلیت لوکالایزیشن
def get_location_input_keyboard(lang="fa"):
    """ایجاد کیبورد ارسال لوکیشن با قابلیت لوکالایزیشن"""
    return ReplyKeyboardMarkup([
        [KeyboardButton(get_message("send_current_location", lang=lang), request_location=True)],
        [KeyboardButton(get_message("back", lang=lang))]
    ], resize_keyboard=True)

# کیبورد حذف (برای برداشتن کیبوردهای معمولی)
REMOVE_KEYBOARD = ReplyKeyboardRemove()

# کیبورد بازگشت به منوی انتخاب محل
BACK_TO_LOCATION_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton(get_message("back", lang="fa"), callback_data="back_to_location_type")]
])

# تابع ایجاد کیبورد بازگشت به توضیحات با قابلیت لوکالایزیشن
def get_back_to_description_keyboard(lang="fa"):
    """ایجاد کیبورد بازگشت به توضیحات با قابلیت لوکالایزیشن"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(get_message("back", lang=lang), callback_data="back_to_location_type")]
    ])

# منوی مدیریت فایل‌ها
FILE_MANAGEMENT_MENU_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton(get_message("finish_photos", lang="fa"), callback_data="finish_files")],
    [InlineKeyboardButton(get_message("manage_photos", lang="fa"), callback_data="manage_photos")],
    [InlineKeyboardButton(get_message("back", lang="fa"), callback_data="back_to_details")]
])

# Photo management keyboards
def create_photo_management_keyboard(files_list, lang="fa"):
    """Create keyboard for managing uploaded photos"""
    keyboard = [
        [InlineKeyboardButton(f"📸 تصویر {i+1}", callback_data=f"view_photo_{i}"),
         InlineKeyboardButton(get_message("edit", lang=lang), callback_data=f"edit_photo_{i}")]
        for i in range(len(files_list))
    ]
    keyboard.append([InlineKeyboardButton(get_message("back", lang=lang), callback_data="back_to_upload")])
    return InlineKeyboardMarkup(keyboard)

# منوی مشاهده پروژه‌ها
VIEW_PROJECTS_MENU_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("درخواست‌های باز", callback_data="open_projects")],
    [InlineKeyboardButton("درخواست‌های بسته", callback_data="closed_projects")],
    [InlineKeyboardButton(get_message("back", lang="fa"), callback_data="back_to_employer_menu")]
])

# منوی ثبت‌نام با KeyboardButton برای ارسال شماره تماس
REGISTER_MENU = ReplyKeyboardMarkup([
    [KeyboardButton("📱 به اشتراک گذاشتن شماره تماس", request_contact=True)]
], resize_keyboard=True)

# تنظیم کیبورد ثبت شماره به صورت یک دکمه ساده
REGISTER_MENU_KEYBOARD = ReplyKeyboardMarkup(
    [[KeyboardButton("📱 به اشتراک گذاشتن شماره تماس", request_contact=True)]],
    resize_keyboard=True,
    one_time_keyboard=True
)

# منوی اینلاین کارفرما
EMPLOYER_INLINE_MENU_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton(get_message("employer_new_request", lang="fa"), callback_data='new_project')],
    [InlineKeyboardButton(get_message("employer_view_projects", lang="fa"), callback_data='view_projects')],
])

# منوی اینلاین بازگشت
BACK_INLINE_MENU_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton(get_message("back", lang="fa"), callback_data="back_to_upload")]
])

# منوی راه‌اندازی مجدد - تغییر به URL دستور برای فراخوانی مستقیم /start
RESTART_INLINE_MENU_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("🔄 شروع مجدد", url="https://t.me/BivasetBot?start=restart")]
])

# منوی بازگشت به توضیحات
BACK_TO_DESCRIPTION_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton(get_message("back", lang="fa"), callback_data="back_to_location_type")]
])

# منوی اینلاین ثبت شماره تلفن
REGISTER_INLINE_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("📱 ثبت شماره تلفن", callback_data="register_phone")],
    [InlineKeyboardButton("🔄 شروع مجدد", url="https://t.me/BivasetBot?start=restart")]
])

# تابع ایجاد یک دکمه راه‌اندازی مجدد برای کاربران جدید
def create_restart_keyboard():
    """ایجاد کیبورد راه‌اندازی مجدد برای کاربران"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 شروع مجدد", url="https://t.me/BivasetBot?start=restart")],
    ])

# تابع ایجاد کیبورد دکمه‌های ادامه و بازگشت
def create_navigation_keyboard(back_callback, continue_callback=None, continue_enabled=False, continue_text="✅ ادامه"):
    """ایجاد کیبورد حاوی دکمه‌های بازگشت و ادامه برای ناوبری بین مراحل"""
    keyboard = []
    
    # اگر دکمه ادامه فعال باشد و آدرس کالبک آن مشخص شده باشد
    if continue_enabled and continue_callback:
        keyboard.append([
            InlineKeyboardButton(get_message("back", lang="fa"), callback_data=back_callback),
            InlineKeyboardButton(continue_text, callback_data=continue_callback)
        ])
    else:
        keyboard.append([InlineKeyboardButton(get_message("back", lang="fa"), callback_data=back_callback)])
    
    return InlineKeyboardMarkup(keyboard)

def create_dynamic_keyboard(context):
    buttons = []
    # همیشه دکمه تصاویر رو نشون بده
    buttons.append([InlineKeyboardButton(get_message("images_button", lang="fa"), callback_data="photo_management")])
    
    if 'need_date' not in context.user_data:
        buttons.append([InlineKeyboardButton(get_message("need_date_button", lang="fa"), callback_data="need_date")])
    if 'deadline' not in context.user_data:
        buttons.append([InlineKeyboardButton(get_message("deadline_button", lang="fa"), callback_data="deadline")])
    if 'budget' not in context.user_data:
        buttons.append([InlineKeyboardButton(get_message("budget_button", lang="fa"), callback_data="budget")])
    if 'quantity' not in context.user_data:
        buttons.append([InlineKeyboardButton(get_message("quantity_button", lang="fa"), callback_data="quantity")])
    buttons.append([
        InlineKeyboardButton(get_message("back", lang="fa"), callback_data="back_to_description"), 
        InlineKeyboardButton(get_message("submit_project_button", lang="fa"), callback_data="submit_project")
    ])
    return InlineKeyboardMarkup(buttons)

def create_category_keyboard(categories):
    """ساخت کیبورد دسته‌بندی‌ها"""
    root_cats = [cat_id for cat_id, cat in categories.items() if cat.get('parent') is None]
    keyboard = []
    
    for cat_id in root_cats:
        if cat_id in categories:
            keyboard.append([InlineKeyboardButton(categories[cat_id]['name'], callback_data=f"cat_{cat_id}")])
    
    keyboard.append([InlineKeyboardButton(get_message("back", lang="fa"), callback_data="back_to_menu")])
    return InlineKeyboardMarkup(keyboard)

# اضافه کردن تابع ایجاد کیبورد زیردسته‌ها
def create_subcategory_keyboard(categories: dict, parent_id: int, lang="fa") -> InlineKeyboardMarkup:
    """
    ایجاد کیبورد زیردسته‌ها برای دسته‌بندی مشخص
    """
    keyboard = []
    for child_id in categories.get(parent_id, {}).get('children', []):
        child = categories.get(child_id)
        if child:
            keyboard.append([
                InlineKeyboardButton(child['name'], callback_data=f"subcat_{child_id}")
            ])
    # دکمه بازگشت به دسته‌بندی
    keyboard.append([
        InlineKeyboardButton(get_message("back", lang=lang), callback_data="back_to_categories")
    ])
    return InlineKeyboardMarkup(keyboard)

def create_category_confirmation_keyboard(selected_category_name: str, lang: str = "fa") -> InlineKeyboardMarkup:
    """Creates a confirmation keyboard after category selection with continue and back buttons"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(get_message("back", lang=lang), callback_data="back_to_categories"),
            InlineKeyboardButton(get_message("continue", lang=lang), callback_data="continue_to_location")
        ]
    ])

def create_category_error_keyboard(lang: str = "fa") -> InlineKeyboardMarkup:
    """Creates an error keyboard with only back button for category selection"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(get_message("back", lang=lang), callback_data="back_to_categories")]
    ])

def get_description_short_buttons(lang="fa"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(get_message("continue", lang=lang), callback_data="continue_to_details")],
        [InlineKeyboardButton(get_message("edit", lang=lang), callback_data="back_to_description")]
    ])