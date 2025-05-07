# keyboards.py
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from localization import get_message
from khayyam import JalaliDatetime
from datetime import datetime, timedelta
from handlers.navigation_utils import SERVICE_REQUEST_FLOW
from handlers.states import DESCRIPTION

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
def create_photo_management_keyboard(files_list, lang="fa", edit_mode=False, edit_index=None):
    """Create keyboard for managing uploaded photos, with optional edit mode for delete/replace"""
    keyboard = []
    if edit_mode and edit_index is not None:
        # Edit mode: show delete and replace buttons for the selected photo
        keyboard = [
            [
                InlineKeyboardButton(get_message("delete_with_icon", lang=lang), callback_data=f"delete_photo_{edit_index}"),
                InlineKeyboardButton(get_message("replace_with_icon", lang=lang), callback_data=f"replace_photo_{edit_index}")
            ],
            [InlineKeyboardButton(get_message("back", lang=lang), callback_data="back_to_management")]
        ]
    else:
        # Normal mode: show view and edit buttons for each photo
        keyboard = [
            [
                InlineKeyboardButton(f"📸 تصویر {i+1}", callback_data=f"view_photo_{i}"),
                InlineKeyboardButton(get_message("edit", lang=lang), callback_data=f"edit_photo_{i}")
            ]
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

# تابع ایجاد کیبورد انتخاب تاریخ نیاز
def get_date_selection_keyboard(lang="fa"):
    """ایجاد کیبورد انتخاب تاریخ نیاز با تاریخ‌های پیش‌فرض و گزینه دلخواه"""
    today = JalaliDatetime(datetime.now()).strftime('%Y/%m/%d')
    tomorrow = JalaliDatetime(datetime.now() + timedelta(days=1)).strftime('%Y/%m/%d')
    day_after = JalaliDatetime(datetime.now() + timedelta(days=2)).strftime('%Y/%m/%d')
    keyboard = [
        [InlineKeyboardButton(get_message("today_date", lang=lang, today=today), callback_data=f"date_today_{today}")],
        [InlineKeyboardButton(get_message("tomorrow_date", lang=lang, tomorrow=tomorrow), callback_data=f"date_tomorrow_{tomorrow}")],
        [InlineKeyboardButton(get_message("day_after_date", lang=lang, day_after=day_after), callback_data=f"date_day_after_{day_after}")],
        [InlineKeyboardButton(get_message("custom_date", lang=lang), callback_data="date_custom")],
        [InlineKeyboardButton(get_message("back", lang=lang), callback_data="back_to_details")]
    ]
    return InlineKeyboardMarkup(keyboard)

# تابع ایجاد کیبورد انتخاب مهلت انجام
def get_deadline_selection_keyboard(lang="fa"):
    """ایجاد کیبورد انتخاب مهلت انجام با گزینه‌های پیش‌فرض و دلخواه"""
    keyboard = [
        [
            InlineKeyboardButton(f"1 {get_message('day_unit', lang=lang)}", callback_data="deadline_1"),
            InlineKeyboardButton(f"2 {get_message('days_unit', lang=lang)}", callback_data="deadline_2"),
            InlineKeyboardButton(f"3 {get_message('days_unit', lang=lang)}", callback_data="deadline_3")
        ],
        [
            InlineKeyboardButton(f"5 {get_message('days_unit', lang=lang)}", callback_data="deadline_5"),
            InlineKeyboardButton(f"7 {get_message('days_unit', lang=lang)}", callback_data="deadline_7"),
            InlineKeyboardButton(f"10 {get_message('days_unit', lang=lang)}", callback_data="deadline_10")
        ],
        [
            InlineKeyboardButton(f"14 {get_message('days_unit', lang=lang)}", callback_data="deadline_14"),
            InlineKeyboardButton(f"30 {get_message('days_unit', lang=lang)}", callback_data="deadline_30")
        ],
        [InlineKeyboardButton(get_message("custom_amount", lang=lang), callback_data="deadline_custom")],
        [InlineKeyboardButton(get_message("back", lang=lang), callback_data="back_to_details")]
    ]
    return InlineKeyboardMarkup(keyboard)

# تابع ایجاد کیبورد انتخاب بودجه
def get_budget_selection_keyboard(lang="fa"):
    """ایجاد کیبورد انتخاب بودجه با گزینه‌های پیش‌فرض و دلخواه"""
    keyboard = [
        [
            InlineKeyboardButton(f"100,000 {get_message('toman_unit', lang=lang)}", callback_data="budget_100000"),
            InlineKeyboardButton(f"200,000 {get_message('toman_unit', lang=lang)}", callback_data="budget_200000")
        ],
        [
            InlineKeyboardButton(f"500,000 {get_message('toman_unit', lang=lang)}", callback_data="budget_500000"),
            InlineKeyboardButton(f"1,000,000 {get_message('toman_unit', lang=lang)}", callback_data="budget_1000000")
        ],
        [
            InlineKeyboardButton(f"2,000,000 {get_message('toman_unit', lang=lang)}", callback_data="budget_2000000"),
            InlineKeyboardButton(f"5,000,000 {get_message('toman_unit', lang=lang)}", callback_data="budget_5000000")
        ],
        [InlineKeyboardButton(get_message("custom_amount", lang=lang), callback_data="budget_custom")],
        [InlineKeyboardButton(get_message("back", lang=lang), callback_data="back_to_details")]
    ]
    return InlineKeyboardMarkup(keyboard)

# تابع ایجاد کیبورد انتخاب مقدار و واحد
def get_quantity_selection_keyboard(lang="fa"):
    """ایجاد کیبورد انتخاب مقدار و واحد با گزینه‌های پیش‌فرض و دلخواه"""
    keyboard = [
        [
            InlineKeyboardButton(f"1 {get_message('piece_unit', lang=lang)}", callback_data="quantity_1_عدد"),
            InlineKeyboardButton(f"2 {get_message('pieces_unit', lang=lang)}", callback_data="quantity_2_عدد"),
            InlineKeyboardButton(f"3 {get_message('pieces_unit', lang=lang)}", callback_data="quantity_3_عدد")
        ],
        [
            InlineKeyboardButton(f"1 {get_message('meter_unit', lang=lang)}", callback_data="quantity_1_متر"),
            InlineKeyboardButton(f"5 {get_message('meters_unit', lang=lang)}", callback_data="quantity_5_متر"),
            InlineKeyboardButton(f"10 {get_message('meters_unit', lang=lang)}", callback_data="quantity_10_متر")
        ],
        [
            InlineKeyboardButton(f"1 {get_message('day_unit', lang=lang)}", callback_data="quantity_1_روز"),
            InlineKeyboardButton(f"1 {get_message('hour_unit', lang=lang)}", callback_data="quantity_1_ساعت")
        ],
        [InlineKeyboardButton(get_message("custom_amount", lang=lang), callback_data="quantity_custom")],
        [InlineKeyboardButton(get_message("back", lang=lang), callback_data="back_to_details")]
    ]
    return InlineKeyboardMarkup(keyboard)

# تابع ایجاد کیبورد برای ورودی دلخواه (با دکمه بازگشت)
def get_custom_input_keyboard(lang="fa"):
    """ایجاد کیبورد برای ورودی دلخواه با دکمه بازگشت"""
    keyboard = [
        [InlineKeyboardButton(get_message("back", lang=lang), callback_data="back_to_details")]
    ]
    return InlineKeyboardMarkup(keyboard)

# تابع ایجاد کیبورد ناوبری برای جریان درخواست خدمات
def create_service_flow_navigation_keyboard(current_state, context, lang="fa"):
    """Create navigation keyboard with back and next buttons based on the current state for service request flow"""
    keyboard = []
    
    # Find current position in flow
    try:
        if current_state in SERVICE_REQUEST_FLOW:
            current_index = SERVICE_REQUEST_FLOW.index(current_state)
            row = []
            
            # Add back button if not at the beginning
            if current_index > 0 or context.user_data.get('previous_state') is not None:
                row.append(InlineKeyboardButton(get_message("back", lang=lang), callback_data="navigate_back"))
            
            # Add next button if not at the end and not in DESCRIPTION state
            if current_index < len(SERVICE_REQUEST_FLOW) - 1:
                # For description, only show next if description is entered
                if current_state == DESCRIPTION and 'description' not in context.user_data:
                    pass
                else:
                    row.append(InlineKeyboardButton(get_message("continue", lang=lang), callback_data="navigate_next"))
            
            # Add the navigation row if it has buttons
            if row:
                keyboard.append(row)
            
            # Add menu button only if not in DESCRIPTION state
            if current_state != DESCRIPTION:
                keyboard.append([InlineKeyboardButton(get_message("main_menu_with_icon", lang=lang), callback_data="back_to_employer_menu")])
        else:
            # For states outside the flow, just add back to menu button
            keyboard.append([InlineKeyboardButton(get_message("main_menu_with_icon", lang=lang), callback_data="back_to_employer_menu")])
    except Exception as e:
        # Fallback to basic navigation
        keyboard.append([InlineKeyboardButton(get_message("main_menu_with_icon", lang=lang), callback_data="back_to_employer_menu")])
    
    return InlineKeyboardMarkup(keyboard)