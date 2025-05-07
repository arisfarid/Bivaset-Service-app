# localization.py
from typing import Optional

def get_message(key: str, lang: str = "fa", **kwargs) -> str:
    """
    دریافت پیام با توجه به کلید و زبان مورد نظر با پشتیبانی از قالب‌بندی پویا
    """
    messages = {
        "fa": {
            # پیام‌های خوش‌آمدگویی و منوی اصلی
            "welcome": "🌟 به بات بی‌واسط خوش اومدی! لطفاً یکی از گزینه‌ها رو انتخاب کن:",
            "role_employer": "👷 کارفرما",
            "role_contractor": "🛠 مجری",
            "main_menu_button": "منوی اصلی",
            "main_menu_with_icon": "🏠 منوی اصلی",

            # پیام‌های منوی کارفرما
            "employer_menu": "🎉 عالیه! چه کاری برات انجام بدم؟",
            "employer_new_request": "📝 درخواست جدید",
            "employer_view_projects": "📋 مشاهده پروژه‌ها",

            # پیام‌های منوی مجری
            "contractor_menu": "🛠 به عنوان مجری چه کاری می‌تونی انجام بدی؟",
            "contractor_view_requests": "📋 مشاهده درخواست‌ها",
            "contractor_offer_work": "💼 پیشنهاد کار",

            # پیام‌های ناوبری
            "back": "⬅️ بازگشت",
            "continue": "✅ ادامه",
            "continue_to_next_step": "➡️ ادامه به مرحله بعد",
            "confirm_and_continue": "✅ تأیید و ادامه",
            "revise_description": "✏️ ویرایش توضیحات",
            "edit": "✏️ ویرایش",

            # پیام‌های دسته‌بندی
            "select_category": "🌟 دسته‌بندی خدماتت رو انتخاب کن:",
            "select_subcategory": "📚 زیرمجموعه رو انتخاب کن:",
            "category_selected": "دسته‌بندی '{category_name}' انتخاب شد. ادامه می‌خوای یا تغییر؟",
            "category_error": "❌ لطفاً یک دسته‌بندی معتبر انتخاب کنید!",

            # پیام‌های توضیحات پروژه
            "description_guidance": "📝 لطفاً توضیحات کامل درخواستت رو بنویس (مثال: نوع خدمات، جزئیات کار، مواد مورد نیاز و ...).\n\nحداقل 20 کاراکتر بنویس تا بتونیم ادامه بدیم.",
            "description_too_short": "⚠️ توضیحات خیلی کوتاهه! لطفاً بیشتر توضیح بده یا ادامه بده.",
            "write_description_prompt": "✏️ توضیحاتت رو اینجا بنویس:",
            "previous_description_with_confirm": "\n\nتوضیحات قبلی:\n'{last_description}'\n\nاگه اوکیه، می‌تونی تأیید کنی یا دوباره بنویسی.",
            "previous_description_edit": "توضیحات قبلی:\n'{last_description}'\n\nلطفاً توضیحات جدید رو بنویس یا برای بازگشت گزینه رو انتخاب کن:",
            "description_only_text": "⚠️ لطفاً فقط متن بنویس! (عکس، ویدیو یا چیز دیگه قبول نیست)",
            "description_required": "⚠️ لطفاً ابتدا توضیحات درخواست رو وارد کنید!",

            # پیام‌های انتخاب محل خدمات
            "location_type_guidance": "📍 محل انجام خدمات رو مشخص کن:",
            "location_type_client": "🏠 محل کارفرما",
            "location_type_contractor": "🏭 محل مجری",
            "location_type_remote": "🌐 از راه دور",
            "send_current_location": "📍 ارسال موقعیت فعلی",
            "location_saved": "📍 موقعیت با موفقیت ذخیره شد!",

            # پیام‌های جزئیات پروژه
            "project_details": "📋 حالا جزئیات درخواستت رو مشخص کن:",
            "images_button": "📸 تصاویر",
            "need_date_button": "📅 تاریخ نیاز",
            "deadline_button": "⏳ مهلت انجام",
            "budget_button": "💰 بودجه",
            "quantity_button": "📏 مقدار و واحد",
            "submit_project_button": "✅ ثبت درخواست",

            # پیام‌های تاریخ نیاز
            "select_need_date_prompt": "📅 تاریخ نیاز به خدمات رو انتخاب کن (مثال: 1403/06/20):",
            "today_date": "امروز ({today})",
            "tomorrow_date": "فردا ({tomorrow})",
            "day_after_date": "پس‌فردا ({day_after})",
            "custom_date": "📅 تاریخ دلخواه",
            "enter_custom_date_prompt": "📅 تاریخ دلخواه رو به صورت 'سال/ماه/روز' وارد کن (مثال: 1403/06/20):",
            "need_date_saved": "📅 تاریخ نیاز ذخیره شد: {date_str}",
            "date_saved_success": "✅ تاریخ با موفقیت ذخیره شد!",
            "invalid_date_format": "⚠️ فرمت تاریخ اشتباهه! لطفاً به صورت 'سال/ماه/روز' وارد کن (مثال: 1403/06/20).",
            "date_must_be_future": "⚠️ تاریخ باید در آینده باشه! لطفاً تاریخ معتبر وارد کن.",

            # پیام‌های مهلت انجام
            "select_deadline_prompt": "⏳ مهلت انجام خدمات رو انتخاب کن:",
            "enter_custom_deadline_prompt": "⏳ مهلت دلخواه رو به تعداد روز وارد کن (مثال: 5):",
            "deadline_saved": "⏳ مهلت انجام ذخیره شد: {deadline} روز",
            "deadline_saved_success": "✅ مهلت با موفقیت ذخیره شد!",
            "invalid_deadline": "⚠️ مهلت نامعتبره! لطفاً عدد مثبتی وارد کن (مثال: 5).",

            # پیام‌های بودجه
            "select_budget_prompt": "💰 بودجه مورد نظرت رو انتخاب کن:",
            "enter_custom_budget_prompt": "💰 بودجه دلخواه رو به تومان وارد کن (مثال: 1000000):",
            "budget_saved": "💰 بودجه ذخیره شد: {formatted_budget} تومان",
            "budget_saved_success": "✅ بودجه با موفقیت ذخیره شد!",
            "invalid_budget": "⚠️ بودجه نامعتبره! لطفاً فقط عدد وارد کن (مثال: 1000000).",

            # پیام‌های مقدار و واحد
            "select_quantity_prompt": "📏 مقدار و واحد مورد نظرت رو انتخاب کن:",
            "enter_custom_quantity_prompt": "📏 مقدار و واحد دلخواه رو وارد کن (مثال: 5 متر):",
            "quantity_saved": "📏 مقدار ذخیره شد: {quantity}",
            "quantity_saved_success": "✅ مقدار با موفقیت ذخیره شد!",

            # واحدهای اندازه‌گیری
            "day_unit": "روز",
            "days_unit": "روز",
            "toman_unit": "تومان",
            "piece_unit": "عدد",
            "pieces_unit": "عدد",
            "meter_unit": "متر",
            "meters_unit": "متر",
            "hour_unit": "ساعت",
            "hours_unit": "ساعت",

            # پیام‌های عمومی
            "custom_amount": "🔢 مقدار دلخواه",
            "invalid_option": "⚠️ گزینه نامعتبر! لطفاً یکی از گزینه‌های موجود رو انتخاب کن.",
            "submitting_request": "📤 در حال ثبت درخواست...",

            # پیام‌های مدیریت فایل
            "finish_photos": "✅ اتمام بارگذاری",
            "manage_photos": "🖼 مدیریت تصاویر",
            "delete_with_icon": "🗑 حذف",
            "replace_with_icon": "🔄 جایگزینی",

            # پیام‌های ثبت‌نام
            "phone_share_prompt": "📱 لطفاً شماره تلفن خود را به اشتراک بگذارید:",
            "phone_registered": "✅ شماره تلفن شما با موفقیت ثبت شد!",
            "phone_already_registered": "⚠️ این شماره قبلاً ثبت شده است!",
            "invalid_phone": "⚠️ شماره تلفن نامعتبر است! لطفاً دوباره تلاش کنید.",
        },
        "en": {
            # Welcome and main menu messages
            "welcome": "🌟 Welcome to the Bivaset Bot! Please select an option:",
            "role_employer": "👷 Employer",
            "role_contractor": "🛠 Contractor",
            "main_menu_button": "Main Menu",
            "main_menu_with_icon": "🏠 Main Menu",

            # Employer menu messages
            "employer_menu": "🎉 Great! What can I do for you?",
            "employer_new_request": "📝 New Request",
            "employer_view_projects": "📋 View Projects",

            # Contractor menu messages
            "contractor_menu": "🛠 As a contractor, what can you do?",
            "contractor_view_requests": "📋 View Requests",
            "contractor_offer_work": "💼 Offer Work",

            # Navigation messages
            "back": "⬅️ Back",
            "continue": "✅ Continue",
            "continue_to_next_step": "➡️ Continue to Next Step",
            "confirm_and_continue": "✅ Confirm and Continue",
            "revise_description": "✏️ Revise Description",
            "edit": "✏️ Edit",

            # Category messages
            "select_category": "🌟 Select the service category:",
            "select_subcategory": "📚 Select a subcategory:",
            "category_selected": "Category '{category_name}' selected. Continue or change?",
            "category_error": "❌ Please select a valid category!",

            # Project description messages
            "description_guidance": "📝 Please provide a detailed description of your request (e.g., type of service, work details, required materials, etc.).\n\nWrite at least 20 characters to proceed.",
            "description_too_short": "⚠️ Description is too short! Please provide more details or continue.",
            "write_description_prompt": "✏️ Write your description here:",
            "previous_description_with_confirm": "\n\nPrevious description:\n'{last_description}'\n\nIf it's okay, you can confirm or rewrite.",
            "previous_description_edit": "Previous description:\n'{last_description}'\n\nPlease write a new description or select back:",
            "description_only_text": "⚠️ Please send only text! (Photos, videos, or other content are not accepted)",
            "description_required": "⚠️ Please enter the request description first!",

            # Location selection messages
            "location_type_guidance": "📍 Specify the service location:",
            "location_type_client": "🏠 Employer's Location",
            "location_type_contractor": "🏭 Contractor's Location",
            "location_type_remote": "🌐 Remote",
            "send_current_location": "📍 Send Current Location",
            "location_saved": "📍 Location saved successfully!",

            # Project details messages
            "project_details": "📋 Now specify the details of your request:",
            "images_button": "📸 Images",
            "need_date_button": "📅 Required Date",
            "deadline_button": "⏳ Deadline",
            "budget_button": "💰 Budget",
            "quantity_button": "📏 Quantity and Unit",
            "submit_project_button": "✅ Submit Request",

            # Required date messages
            "select_need_date_prompt": "📅 Select the required date (e.g., 2024/09/10):",
            "today_date": "Today ({today})",
            "tomorrow_date": "Tomorrow ({tomorrow})",
            "day_after_date": "Day After ({day_after})",
            "custom_date": "📅 Custom Date",
            "enter_custom_date_prompt": "📅 Enter the custom date in 'YYYY/MM/DD' format (e.g., 2024/09/10):",
            "need_date_saved": "📅 Required date saved: {date_str}",
            "date_saved_success": "✅ Date saved successfully!",
            "invalid_date_format": "⚠️ Invalid date format! Please enter in 'YYYY/MM/DD' format (e.g., 2024/09/10).",
            "date_must_be_future": "⚠️ Date must be in the future! Please enter a valid date.",

            # Deadline messages
            "select_deadline_prompt": "⏳ Select the deadline for the service:",
            "enter_custom_deadline_prompt": "⏳ Enter the custom deadline in days (e.g., 5):",
            "deadline_saved": "⏳ Deadline saved: {deadline} days",
            "deadline_saved_success": "✅ Deadline saved successfully!",
            "invalid_deadline": "⚠️ Invalid deadline! Please enter a positive number (e.g., 5).",

            # Budget messages
            "select_budget_prompt": "💰 Select your budget:",
            "enter_custom_budget_prompt": "💰 Enter the custom budget in Toman (e.g., 1000000):",
            "budget_saved": "💰 Budget saved: {formatted_budget} Toman",
            "budget_saved_success": "✅ Budget saved successfully!",
            "invalid_budget": "⚠️ Invalid budget! Please enter only numbers (e.g., 1000000).",

            # Quantity and unit messages
            "select_quantity_prompt": "📏 Select the quantity and unit:",
            "enter_custom_quantity_prompt": "📏 Enter the custom quantity and unit (e.g., 5 meters):",
            "quantity_saved": "📏 Quantity saved: {quantity}",
            "quantity_saved_success": "✅ Quantity saved successfully!",

            # Unit messages
            "day_unit": "day",
            "days_unit": "days",
            "toman_unit": "Toman",
            "piece_unit": "piece",
            "pieces_unit": "pieces",
            "meter_unit": "meter",
            "meters_unit": "meters",
            "hour_unit": "hour",
            "hours_unit": "hours",

            # General messages
            "custom_amount": "🔢 Custom Amount",
            "invalid_option": "⚠️ Invalid option! Please select one of the available options.",
            "submitting_request": "📤 Submitting request...",

            # File management messages
            "finish_photos": "✅ Finish Uploading",
            "manage_photos": "🖼 Manage Images",
            "delete_with_icon": "🗑 Delete",
            "replace_with_icon": "🔄 Replace",

            # Registration messages
            "phone_share_prompt": "📱 Please share your phone number:",
            "phone_registered": "✅ Your phone number has been successfully registered!",
            "phone_already_registered": "⚠️ This phone number is already registered!",
            "invalid_phone": "⚠️ Invalid phone number! Please try again.",
        }
    }

    try:
        # دریافت پیام از دیکشنری پیام‌ها
        message = messages.get(lang, messages["fa"]).get(key, "پیام یافت نشد!")
        # قالب‌بندی پیام با متغیرهای ارسالی
        return message.format(**kwargs) if kwargs else message
    except KeyError:
        # در صورت نبود کلید، پیام پیش‌فرض
        return "پیام یافت نشد!"
    except Exception as e:
        # لاگ خطا برای دیباگ
        print(f"Error in get_message: {e}")
        return "خطا در دریافت پیام!"