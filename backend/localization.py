# localization.py
from typing import Optional
from telegram import Update
from telegram.ext import ContextTypes

def get_message(key: str, context: ContextTypes.DEFAULT_TYPE = None, update: Update = None, **kwargs) -> str:
    """
    دریافت پیام با توجه به کلید و استخراج خودکار زبان و متغیرهای پارامتریک از context
    """
    messages = {
        "fa": {
            # پیام‌های خوش‌آمدگویی و منوی اصلی
            "welcome": "👋 سلام {name}! به سامانه خدمات بی‌واسط خوش آمدید.\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            "bot_updated": "🔄 *ربات بی‌واسط به‌روزرسانی شد!*\n\n✨ امکانات جدید اضافه شده\n🛠 بهبود عملکرد و رفع باگ‌ها\n\nبرای استفاده از نسخه جدید، لطفاً روی دکمه زیر کلیک کنید. این دکمه شما را به صفحه اصلی ربات منتقل می‌کند و می‌توانید از ابتدا استفاده از ربات را شروع کنید:",
            "role_employer": "👔 درخواست خدمات | کارفرما",
            "role_contractor": "🦺 پیشنهاد قیمت | مجری",
            "main_menu_button": "منوی اصلی",
            "main_menu_with_icon": "🏠 منوی اصلی",

            # پیام‌های منوی کارفرما
            "employer_menu_prompt": "🎉 خوش آمدید {name}! چه کاری می‌خواهید انجام دهید؟",
            "employer_new_request": "📋 ثبت درخواست جدید",
            "employer_view_projects": "📊 مشاهده درخواست‌های من",

            # پیام‌های منوی مجری
            "contractor_menu_prompt": "🎉 خوش آمدید {name}! چه کاری می‌خواهید انجام دهید؟",
            "contractor_view_requests": "📋 مشاهده درخواست‌های موجود",
            "contractor_offer_work": "💡 پیشنهاد خدمات",

            # پیام‌های ناوبری
            "back": "⬅️ بازگشت",
            "back_to_previous": "⬅️ بازگشت به مرحله قبل",
            "back_to_details": "بازگشت به منوی جزئیات",
            "continue": "✅ ادامه",
            "continue_to_next_step": "✅ ادامه به مرحله بعد",
            "confirm_and_continue": "✅ تأیید و ادامه",
            "revise_description": "✏️ اصلاح توضیحات",
            "edit": "✏️ ویرایش",
            "cancel": "❌ لغو",
            "skip": "رد کردن »",
            "progress_indicator": "📊 مرحله {current_step} از {total_steps}",
            "back_instruction": "می‌توانید از دکمه «قبلی» برای بازگشت استفاده کنید",

            # پیام‌های دسته‌بندی
            "category_main_select": "🌟 لطفاً دسته‌بندی خدمات موردنیاز خود را انتخاب کنید:",
            "select_subcategory": "📋 لطفاً زیرمجموعه «{category_name}» را انتخاب کنید:",
            "category_selected": "✅ دسته‌بندی انتخاب شد",
            "category_submit_or_back": "برای ادامه ثبت درخواست، دکمه «ثبت» را بزنید یا برای بازگشت، دکمه «بازگشت» را انتخاب کنید。",
            "category_confirmation": "دسته‌بندی '{category_name}' انتخاب شد. برای ادامه ثبت درخواست، دکمه «ثبت» را بزنید یا برای بازگشت، دکمه «بازگشت» را انتخاب کنید。",
            "invalid_category": "❌ دسته‌بندی نامعتبر است",
            "category_select_first": "❌ لطفاً ابتدا یک دسته‌بندی انتخاب کنید。",
            "invalid_subcategory": "❌ زیردسته نامعتبر است",
            "only_select_from_buttons": "❌ لطفاً فقط از دکمه‌های منو انتخاب کنید و پیام یا فایل ارسال نکنید。",
            "step_error": "❌ خطا در نمایش مرحله بعد. لطفاً دوباره تلاش کنید。",
            "error_fetching_categories": "❌ خطا در دریافت دسته‌بندی‌ها",

            # پیام‌های توضیحات پروژه
            "description_guidance": "✍️ لطفاً توضیحات کامل و دقیقی درباره خدمات موردنیاز خود بنویسید تا مجریان بتوانند بهتر و سریع‌تر به شما کمک کنند!\n\nبهتر است به این موارد اشاره کنید:\n• نوع و جزئیات دقیق خدمت موردنیاز\n• توضیح دقیق مشکل یا انتظارات شما از مجری\n• شرایط خاص یا نیازمندی‌های ویژه\n• جزئیات فنی یا ویژگی‌های مهم مدنظرتان\n• اگر مهارت یا ابزار خاصی لازم است\n\nمثال توضیح کامل:\n«سلام، نیاز به تعمیر کولر گازی در منزل دارم. کولر مدل ال‌جی است و باد گرم می‌زند. محل نصب طبقه سوم آپارتمان است. لطفاً هزینه و زمان انجام کار را اعلام کنید. اگر قطعه نیاز به تعویض دارد، لطفاً اطلاع دهید.»\n\nهرچه توضیحات شما کامل‌تر باشد، قیمت و زمان دقیق‌تری دریافت خواهید کرد! 😊",
            "write_description_prompt": "لطفاً توضیحات خود را بنویسید:",
            "description_too_short": "⚠️ توضیحات شما کوتاه به نظر می‌رسد.\n\nتوضیحات کامل‌تر به مجریان کمک می‌کند تا پیشنهاد دقیق‌تری ارائه دهند.\nآیا می‌خواهید توضیحات بیشتری اضافه کنید؟\n\nاگر توضیحات کامل است، می‌توانید به مرحله بعد بروید。",
            "details_prev_description": "🌟 توضیحات قبلی:\n{last_description}\n\nمی‌توانید توضیحات را ویرایش کنید:",
            "previous_description_with_confirm": "✍️ توضیحات قبلی شما:\n{last_description}\n\nمی‌توانید آن را ویرایش کنید یا همین را تایید کنید:",
            "previous_description_edit": "🌟 توضیحات قبلی:\n{last_description}\n\nمی‌تونی توضیحات رو ویرایش کنی:",
            "description_only_text": "❌ لطفاً فقط متن توضیحات را وارد کنید.\n\nدر این مرحله، نیاز داریم توضیحات متنی دقیقی از خدمات موردنیاز شما دریافت کنیم.\nلطفاً توضیحات خود را به صورت متن بنویسید。",
            "description_required": "⚠️ لطفاً ابتدا توضیحات خدمات را وارد کنید!",

            # پیام‌های انتخاب محل خدمات
            "location_type_guidance": "🌟 لطفاً محل انجام خدمات را انتخاب کنید:\n\n🏠 *محل من*: مجری برای انجام خدمات به محل شما مراجعه می‌کند\n      مانند: نظافت، تعمیرات منزل، باغبانی و خدمات سیار\n\n🔧 *محل مجری*: شما برای دریافت خدمات به محل کار مجری مراجعه می‌کنید\n      مانند: کارواش، تعمیرگاه، آرایشگاه و خدمات کارگاهی\n\n💻 *غیرحضوری*: خدمات بدون نیاز به حضور فیزیکی و از راه دور انجام می‌شود\n      مانند: مشاوره، آموزش، طراحی، برنامه‌نویسی",
            "location_type_client": "🏠 محل من",
            "location_type_contractor": "🔧 محل مجری",
            "location_type_remote": "💻 غیرحضوری",
            "location_request": "📍 برای ارتباط با نزدیک‌ترین مجری، لطفاً موقعیت مکانی خود را مشخص کنید:\n\n📱 اگر در محل مورد نظر برای دریافت خدمات هستید، از دکمه «ارسال موقعیت فعلی» استفاده کنید یا\n📎 روی آیکون پیوست (📎) کلیک کرده و با گزینه «Location» موقعیت دلخواه خود را انتخاب کنید。",
            "location_success": "✅ موقعیت مکانی شما با موفقیت دریافت شد!",
            "location_invalid_type": "❌ پیام ارسالی موقعیت مکانی نیست.\n\nلطفاً *فقط موقعیت مکانی* خود را ارسال کنید. این اطلاعات برای یافتن نزدیک‌ترین مجری ضروری است.\n\n📱 از دکمه «ارسال موقعیت فعلی» استفاده کنید یا\n📎 روی آیکون پیوست (📎) کلیک کرده و گزینه «Location» را انتخاب کنید。",
            "location_required": "❌ لطفاً *موقعیت مکانی* خود را ارسال کنید.\n\nبرای خدمات در {service_location_name} نیاز به دانستن موقعیت شما داریم تا مجری مناسب را پیدا کنیم.\n\n📱 از دکمه «ارسال موقعیت فعلی» استفاده کنید یا\n📎 روی آیکون پیوست (📎) کلیک کرده و گزینه «Location» را انتخاب کنید。",
            "send_current_location": "📍 ارسال موقعیت فعلی",
            "location_saved": "📍 موقعیت با موفقیت ذخیره شد!",
            "remote_service_selected": "🌐 خدمات از راه دور انتخاب شد!",
            "remote_service_confirmation": "🌐 خدمات از راه دور انتخاب شد!\n\n✍️ لطفاً توضیحات کامل و دقیقی درباره خدمات موردنیاز خود بنویسید تا مجریان بتوانند بهتر و سریع‌تر به شما کمک کنند!\n\nبهتر است به این موارد اشاره کنید:\n• نوع و جزئیات دقیق خدمت موردنیاز\n• توضیح دقیق مشکل یا انتظارات شما از مجری\n• شرایط خاص یا نیازمندی‌های ویژه\n• جزئیات فنی یا ویژگی‌های مهم مدنظرتان\n• اگر مهارت یا ابزار خاصی لازم است\n\nمثال توضیح کامل:\n«سلام، نیاز به طراحی لوگو برای یک شرکت دارم. لوگو باید حرفه‌ای و ساده باشد. لطفاً نمونه‌کارهای خود را ارسال کنید و هزینه و زمان تحویل را اعلام کنید.»\n\nهرچه توضیحات شما کامل‌تر باشد، پیشنهاد دقیق‌تری دریافت خواهید کرد! 😊",
            "location_map_link": "<a href=\"https://maps.google.com/maps?q={latitude},{longitude}\">نمایش روی نقشه</a>",

            # پیام‌های جزئیات پروژه
            "project_details": "📋 جزئیات درخواست:\nمی‌توانید برای راهنمایی بهتر مجریان، اطلاعات تکمیلی زیر را وارد کنید:",
            "images_button": "📸 تصاویر و فایل‌ها",
            "need_date_button": "📅 تاریخ نیاز",
            "deadline_button": "⏳ مهلت انجام",
            "budget_button": "💰 بودجه",
            "quantity_button": "📏 مقدار و واحد",
            "submit_project_button": "✅ ثبت نهایی درخواست",

            # پیام‌های تاریخ نیاز
            "select_need_date_prompt": "📅 تاریخ نیاز رو انتخاب کن یا دستی وارد کن (مثلاً 1403/10/15):",
            "select_need_date_short_prompt": "📅 تاریخ نیاز خود را به صورت 'ماه/روز' وارد کنید (مثال: 05/15):",
            "today_date": "📅 امروز ({today})",
            "tomorrow_date": "📅 فردا ({tomorrow})",
            "day_after_date": "📅 پس‌فردا ({day_after})",
            "custom_date": "✏️ تاریخ دلخواه",
            "enter_custom_date_prompt": "📅 لطفاً تاریخ مورد نظر خود را به فرمت 1403/10/15 وارد کنید:",
            "need_date_saved": "📅 تاریخ نیاز ثبت شد: {date_str}",
            "date_saved_success": "✅ تاریخ با موفقیت ثبت شد!",
            "invalid_date_format": "❌ فرمت تاریخ نامعتبر است! لطفاً تاریخ را به صورت YYYY/MM/DD (مثال: 1403/10/15) وارد کنید و مطمئن شوید از امروز به بعد است。",
            "date_must_be_future": "❌ تاریخ باید امروز یا پس از امروز باشد!",

            # پیام‌های مهلت انجام
            "select_deadline_prompt": "⏳ مهلت انجام (بر حسب روز) را انتخاب کنید:",
            "select_deadline_short_prompt": "⏳ مهلت انجام خدمات را به صورت 'ماه/روز' وارد کنید (مثال: 06/20):",
            "enter_custom_deadline_prompt": "⏳ لطفاً مهلت انجام مورد نظر خود را به روز وارد کنید (مثلاً: 7):",
            "deadline_saved": "⏳ مهلت انجام ثبت شد: {deadline} روز",
            "deadline_saved_success": "✅ مهلت انجام با موفقیت ثبت شد!",
            "invalid_deadline": "❌ مهلت نامعتبر است! لطفاً یک عدد وارد کنید (مثال: 7).",

            # پیام‌های بودجه
            "select_budget_prompt": "💰 بودجه‌ای که برای این خدمات در نظر دارید را انتخاب کنید:",
            "enter_custom_budget_prompt": "💰 لطفاً بودجه مورد نظر خود را به تومان وارد کنید (مثلاً: 500000):",
            "budget_saved": "💰 بودجه ثبت شد: {formatted_budget} تومان",
            "budget_saved_success": "✅ بودجه با موفقیت ثبت شد!",
            "invalid_budget": "❌ بودجه نامعتبر است! لطفاً فقط عدد وارد کنید (مثال: 500000).",

            # پیام‌های مقدار و واحد
            "select_quantity_prompt": "📏 مقدار و واحد مورد نیاز را انتخاب کنید:",
            "enter_custom_quantity_prompt": "📏 لطفاً مقدار و واحد مورد نظر خود را وارد کنید (مثلاً: 2 عدد، 5 متر مربع، 3 ساعت):",
            "quantity_saved": "📏 مقدار و واحد ثبت شد: {quantity}",
            "quantity_saved_success": "✅ مقدار و واحد با موفقیت ثبت شد!",

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
            "custom_amount": "✏️ مقدار دلخواه",
            "invalid_option": "❌ گزینه نامعتبر! لطفاً یکی از دکمه‌های منو را انتخاب کنید。",
            "submitting_request": "در حال ثبت درخواست شما...",
            "submit": "✅ ثبت درخواست",
            "operation_cancelled": "عملیات لغو شد. دوباره شروع کن!",
            "general_error": "خطایی رخ داد. لطفاً دوباره تلاش کنید.",

            # پیام‌های مدیریت فایل
            "photos_command": "📸 تصاویر را یکی‌یکی ارسال کنید (حداکثر ۵ تصویر). فقط عکس پذیرفته می‌شود!",
            "photos_uploaded": "📸 تصاویر ارسال‌شده ({count} از 5)",
            "photo_upload_success": "✅ تصویر با موفقیت اضافه شد ({count} از 5)",
            "photo_upload_max": "❌ حداکثر تعداد تصاویر مجاز (5) ارسال شده است. برای مدیریت تصاویر از گزینه «مدیریت تصاویر» استفاده کنید。",
            "photo_already_exists": "❌ این تصویر قبلاً ارسال شده است",
            "photo_replaced": "🔄 تصویر با موفقیت جایگزین شد",
            "photo_list_empty": "📭 هنوز تصویری ارسال نکرده‌اید",
            "photo_management_title": "📸 تصاویر ارسال‌شده:",
            "video_not_supported": "❌ فقط عکس پشتیبانی می‌شود. ویدیو قابل ثبت نیست。",
            "no_images_found": "❌ برای این درخواست تصویری یافت نشد",
            "original_image": "تصویر اصلی",
            "error_loading_images": "❌ خطا در بارگیری تصاویر",
            "error_fetching_project": "❌ خطا در دریافت اطلاعات درخواست",
            "error_processing_request": "❌ خطا در پردازش درخواست",
            "finish_photos": "🏁 پایان ارسال تصاویر",
            "manage_photos": "📋 مدیریت تصاویر",
            "delete_with_icon": "🗑 حذف",
            "replace_with_icon": "🔄 جایگزینی",

            # پیام‌های ثبت‌نام
            "share_phone_prompt": "⚠️ برای استفاده از ربات، لطفاً شماره تلفن خود را به اشتراک بگذارید:\nاز دکمه زیر استفاده کنید:",
            "phone_registered": "✅ شماره تلفن شما با موفقیت ثبت شد!",
            "phone_already_registered": "⚠️ این شماره قبلاً ثبت شده است!",
            "invalid_phone": "⚠️ فرمت شماره نامعتبر است!\nلطفاً شماره را به فرمت 09123456789 وارد کنید。",
            "phone_required": "برای ادامه نیاز به ثبت شماره تلفن است",
            "share_phone_instruction": "از دکمه زیر برای به اشتراک‌گذاری مستقیم شماره استفاده کنید:",
            "enter_new_phone_prompt": "📱 لطفاً شماره تلفن جدید خود را وارد کنید:\nمثال: 09123456789",
            "verification_code_sent": "📤 کد تأیید 4 رقمی به شماره شما ارسال شد.\n⏰ مهلت وارد کردن کد: 2 دقیقه\n📱 شماره: {phone}",
            "error_sending_verification_code": "❌ خطا در ارسال کد تأیید.\nلطفاً دوباره تلاش کنید。",
            "invalid_verification_info": "❌ اطلاعات تأیید نامعتبر است。",
            "max_attempts_reached": "❌ تعداد تلاش‌های مجاز به پایان رسید.\nلطفاً دوباره درخواست کد کنید。",
            "verification_code_expired": "⏰ کد تأیید منقضی شده است.\nلطفاً دوباره درخواست کد کنید。",
            "incorrect_verification_code": "❌ کد وارد شده اشتباه است.\nتعداد تلاش‌های باقیمانده: {remaining}",
            "error_registering_phone": "❌ خطا در ثبت شماره تلفن.\nلطفاً دوباره تلاش کنید.",

            # پیام‌های نقش
            "role_select": "🌟 لطفاً نقش خود را انتخاب کنید:",

            # پیام‌های فرآیند فعال
            "process_active_prompt": "⚠️ شما در حال انجام یک فرآیند هستید.\nآیا می‌خواهید از فرآیند فعلی خارج شوید و دوباره شروع کنید؟",
            "restart_yes": "✅ بله، شروع مجدد",
            "restart_no": "❌ خیر، ادامه فرآیند فعلی",

            # پیام‌های انتخاب
            "select_from_buttons": "لطفاً از دکمه‌های زیر انتخاب کنید.",

            # پیام‌های جدید برای submission_handler
            "location_required_for_onsite": "❌ برای خدمات حضوری، باید لوکیشن را وارد کنید。",
            "submit_request_error": "❌ خطا در ثبت درخواست\n",
            "budget_too_large": "❌ مبلغ وارد شده خیلی بزرگ است. لطفاً مبلغ کمتری وارد کنید。",
            "submit_request_general_error": "❌ خطا در ثبت درخواست. لطفاً دوباره تلاش کنید。",
            "submit_project_summary_template": "🎉 تبریک! درخواست شما با کد {project_id} ثبت شد!\n<b>📌 دسته‌بندی:</b> {category_name}\n<b>📝 توضیحات:</b> {description}\n<b>📍 محل خدمات:</b> {location_text}",
            "photos_count": "<b>📸 تعداد عکس‌ها:</b> {count}",
            "close_project": "بستن",
            "extend_project": "تمدید",
            "view_photos": "نمایش عکس‌ها",
            "view_offers": "پیشنهادها",

            # پیام‌های جدید برای view_handler
            "no_projects_registered": "📭 هنوز درخواستی ثبت نکردی!",
            "continue_or_return": "📊 ادامه بده یا برگرد:",
            "error_fetching_projects": "❌ خطا در دریافت درخواست‌ها: {status_code}",
            "backend_unavailable": "❌ خطا: سرور بک‌اند در دسترس نیست。",
            "view_projects_prompt": "📋 برای مشاهده جزئیات و مدیریت هر کدام از درخواست‌ها روی دکمه مربوطه ضربه بزنید:\n",
            "project_summary_template": "📋 *درخواست {project_id}*\n📌 *دسته‌بندی*: {category_name}\n📝 *توضیحات*: {description}\n📍 *موقعیت*: {location}\n",
            "project_images_template": "📸 *تصاویر*:\n{images}",
            "error_fetching_project_details": "❌ خطا در دریافت اطلاعات: {status_code}",

            # پیام‌های جدید برای state_handler
            "error_restart_prompt": "❌ خطایی رخ داد. لطفاً دوباره شروع کنید با /start"
        },
        "en": {
            # پیام‌های خوش‌آمدگویی و منوی اصلی
            "welcome": "👋 Hello {name}! Welcome to Bivaset Service Platform.\nPlease choose one of the options below:",
            "bot_updated": "🔄 *Bivaset Bot Updated!*\n\n✨ New features added\n🛠 Performance improvements and bug fixes\n\nTo use the new version, please click the button below. This will take you to the main menu, and you can start using the bot from the beginning:",
            "role_employer": "👔 Request service | Client",
            "role_contractor": "🦺 Provide service | Contractor",
            "main_menu_button": "Main Menu",
            "main_menu_with_icon": "🏠 Main Menu",

            # پیام‌های منوی کارفرما
            "employer_menu_prompt": "🎉 Welcome, {name}! What would you like to do?",
            "employer_new_request": "📋 New service request",
            "employer_view_projects": "📊 View my requests",

            # پیام‌های منوی مجری
            "contractor_menu_prompt": "🎉 Welcome, {name}! What would you like to do?",
            "contractor_view_requests": "📋 View available requests",
            "contractor_offer_work": "💡 Offer services",

            # پیام‌های ناوبری
            "back": "⬅️ Back",
            "back_to_previous": "⬅️ Back to previous step",
            "back_to_details": "Return to details menu",
            "continue": "✅ Continue",
            "continue_to_next_step": "✅ Continue to next step",
            "confirm_and_continue": "✅ Confirm and continue",
            "revise_description": "✏️ Revise description",
            "edit": "✏️ Edit",
            "cancel": "❌ Cancel",
            "skip": "Skip »",
            "progress_indicator": "📊 Step {current_step} of {total_steps}",
            "back_instruction": "You can use the 'Back' button to return",

            # پیام‌های دسته‌بندی
            "category_main_select": "🌟 Please select your service category:",
            "select_subcategory": "📋 Please select a subcategory of \"{category_name}\":",
            "category_selected": "✅ Category selected",
            "category_submit_or_back": "To continue, press 'Submit' or select 'Back' to return.",
            "category_confirmation": "Category '{category_name}' selected. To continue, press 'Submit' or select 'Back' to return.",
            "invalid_category": "❌ Invalid category",
            "category_select_first": "❌ Please select a category first.",
            "invalid_subcategory": "❌ Invalid subcategory",
            "only_select_from_buttons": "❌ Please only select from the menu buttons and do not send messages or files.",
            "step_error": "❌ Error displaying the next step. Please try again.",
            "error_fetching_categories": "❌ Error fetching categories",

            # پیام‌های توضیحات پروژه
            "description_guidance": "✍️ Please write a detailed description of the service you need so providers can help you better and faster!\n\nIt's best to mention:\n• The exact type and details of the service you need\n• A clear explanation of the problem or your expectations\n• Any special_conditions or requirements\n• Technical details or important features you are looking for\n• If special skills or tools are required\n\nExample of a complete description:\n'Hello, I need my LG air conditioner repaired at home. It's blowing warm air. The unit is on the third floor. Please let me know the cost and time estimate. If any parts need replacement, please inform me.'\n\nThe more complete your description, the more accurate price and timing you'll receive! 😊",
            "write_description_prompt": "Please write your description:",
            "description_too_short": "⚠️ Your description seems too short.\n\nA more complete description helps service providers give a more accurate quote.\nWould you like to add more details?\n\nIf your description is complete, you can proceed to the next step.",
            "details_prev_description": "🌟 Previous description:\n{last_description}\n\nYou can edit your description:",
            "previous_description_with_confirm": "✍️ Your previous description:\n{last_description}\n\nYou can edit it or confirm it as is:",
            "previous_description_edit": "🌟 Previous description:\n{last_description}\n\nYou can edit the description:",
            "description_only_text": "❌ Please enter only text for the description.\n\nAt this step, we need a precise text description of the service you require.\nPlease write your description as text only.",
            "description_required": "⚠️ Please enter the service description first!",

            # پیام‌های انتخاب محل خدمات
            "location_type_guidance": "🌟 Please select where the service should be performed:\n\n🏠 *My location*: The service provider will come to your place\n      Examples: cleaning, home repairs, gardening, mobile services\n\n🔧 *Provider's location*: You go to the provider's workplace\n      Examples: car wash, repair shop, salon, workshop services\n\n💻 *Remote service*: The service is done remotely without physical presence\n      Examples: consulting, teaching, design, programming",
            "location_type_client": "🏠 My location",
            "location_type_contractor": "🔧 Provider's location",
            "location_type_remote": "💻 Remote service",
            "location_request": "📍 To connect with the nearest service provider, please specify your location:\n\n📱 If you are at the desired location, use the 'Send current location' button or\n📎 click the attachment (📎) icon and select 'Location' to choose your position on the map.",
            "location_success": "✅ Your location was successfully received!",
            "location_invalid_type": "❌ The sent message is not a location.\n\nPlease *only send your location*. This is necessary to find the nearest service provider.\n\n📱 Use the 'Send current location' button or\n📎 click the attachment (📎) icon and select 'Location'.",
            "location_required": "❌ Please send your *location*.\n\nFor services at {service_location_name}, we need your location to find the right service provider.\n\n📱 Use the 'Send current location' button or\n📎 click the attachment (📎) icon and select 'Location'.",
            "send_current_location": "📍 Send current location",
            "location_saved": "📍 Location saved successfully!",
            "remote_service_selected": "🌐 Remote service selected!",
            "remote_service_confirmation": "🌐 Remote service selected!\n\n✍️ Please write a detailed description of the service you need so providers can help you better and faster!\n\nIt's best to mention:\n• The exact type and details of the service you need\n• A clear explanation of the problem or your expectations\n• Any special conditions or requirements\n• Technical details or important features you are looking for\n• If special skills or tools are required\n\nExample of a complete description:\n'Hello, I need a logo designed for my company. The logo should be professional and simple. Please send your portfolio and provide cost and delivery time.'\n\nThe more complete your description, the more accurate quote you'll receive! 😊",
            "location_map_link": "<a href=\"https://maps.google.com/maps?q={latitude},{longitude}\">View on map</a>",

            # پیام‌های جزئیات پروژه
            "project_details": "📋 Request details:\nYou can provide the following additional information to help service providers:",
            "images_button": "📸 Images & Files",
            "need_date_button": "📅 Required date",
            "deadline_button": "⏳ Deadline",
            "budget_button": "💰 Budget",
            "quantity_button": "📏 Quantity & Unit",
            "submit_project_button": "✅ Submit request",

            # پیام‌های تاریخ نیاز
            "select_need_date_prompt": "📅 Select the required date or enter it manually (e.g., 2024/10/15):",
            "select_need_date_short_prompt": "📅 Enter the required date in 'MM/DD' format (e.g., 05/15):",
            "today_date": "📅 Today ({today})",
            "tomorrow_date": "📅 Tomorrow ({tomorrow})",
            "day_after_date": "📅 Day after tomorrow ({day_after})",
            "custom_date": "✏️ Custom date",
            "enter_custom_date_prompt": "📅 Please enter your desired date in the format 2024/10/15:",
            "need_date_saved": "📅 Required date saved: {date_str}",
            "date_saved_success": "✅ Date saved successfully!",
            "invalid_date_format": "❌ Invalid date format! Please enter the date in YYYY/MM/DD format (e.g., 2024/10/15) and make sure it's today or later.",
            "date_must_be_future": "❌ The date must be today or a future date!",

            # پیام‌های مهلت انجام
            "select_deadline_prompt": "⏳ Select the deadline (in days):",
            "select_deadline_short_prompt": "⏳ Enter the service deadline in 'MM/DD' format (e.g., 06/20):",
            "enter_custom_deadline_prompt": "⏳ Please enter your desired deadline in days (e.g., 7):",
            "deadline_saved": "⏳ Deadline saved: {deadline} days",
            "deadline_saved_success": "✅ Deadline saved successfully!",
            "invalid_deadline": "❌ Invalid deadline! Please enter a number (e.g., 7).",

            # پیام‌های بودجه
            "select_budget_prompt": "💰 Select the budget for this service:",
            "enter_custom_budget_prompt": "💰 Please enter your desired budget in Tomans (e.g., 500000):",
            "budget_saved": "💰 Budget saved: {formatted_budget} Tomans",
            "budget_saved_success": "✅ Budget saved successfully!",
            "invalid_budget": "❌ Invalid budget! Please enter only a number (e.g., 500000).",

            # پیام‌های مقدار و واحد
            "select_quantity_prompt": "📏 Select the required quantity and unit:",
            "enter_custom_quantity_prompt": "📏 Please enter your desired quantity and unit (e.g., 2 pieces, 5 square meters, 3 hours):",
            "quantity_saved": "📏 Quantity and unit saved: {quantity}",
            "quantity_saved_success": "✅ Quantity and unit saved successfully!",

            # واحدهای اندازه‌گیری
            "day_unit": "day",
            "days_unit": "days",
            "toman_unit": "Tomans",
            "piece_unit": "piece",
            "pieces_unit": "pieces",
            "meter_unit": "meter",
            "meters_unit": "meters",
            "hour_unit": "hour",
            "hours_unit": "hours",

            # پیام‌های عمومی
            "custom_amount": "✏️ Custom amount",
            "invalid_option": "❌ Invalid option! Please select one of the menu buttons.",
            "submitting_request": "Submitting your request...",
            "submit": "✅ Submit request",
            "operation_cancelled": "Operation cancelled. Start again!",
            "general_error": "An error occurred. Please try again.",

            # پیام‌های مدیریت فایل
            "photos_command": "📸 Please send photos one by one (maximum 5 photos). Only images are accepted!",
            "photos_uploaded": "📸 Uploaded images ({count} of 5)",
            "photo_upload_success": "✅ Image successfully added ({count} of 5)",
            "photo_upload_max": "❌ Maximum number of images (5) reached. Use 'Manage images' to modify your uploads.",
            "photo_already_exists": "❌ This image has already been uploaded",
            "photo_replaced": "🔄 Image successfully replaced",
            "photo_list_empty": "📭 No images uploaded yet",
            "photo_management_title": "📸 Uploaded images:",
            "video_not_supported": "❌ Only images are supported. Videos cannot be processed.",
            "no_images_found": "❌ No images found for this request",
            "original_image": "Main image",
            "error_loading_images": "❌ Error loading images",
            "error_fetching_project": "❌ Error fetching request information",
            "error_processing_request": "❌ Error processing request",
            "finish_photos": "🏁 Finish uploading images",
            "manage_photos": "📋 Manage images",
            "delete_with_icon": "🗑 Delete",
            "replace_with_icon": "🔄 Replace",

            # پیام‌های ثبت‌نام
            "share_phone_prompt": "⚠️ To use the bot, please share your phone number:\nUse the button below:",
            "phone_registered": "✅ Your phone number has been successfully registered!",
            "phone_already_registered": "⚠️ This phone number is already registered!",
            "invalid_phone": "⚠️ Invalid phone format!\nPlease enter the number in the format 09123456789.",
            "phone_required": "Phone number registration is required to continue",
            "share_phone_instruction": "Use the button below to share your phone number directly:",
            "enter_new_phone_prompt": "📱 Please enter your new phone number:\nExample: 09123456789",
            "verification_code_sent": "📤 A 4-digit verification code has been sent to your number.\n⏰ Code entry deadline: 2 minutes\n📱 Number: {phone}",
            "error_sending_verification_code": "❌ Error sending verification code.\nPlease try again.",
            "invalid_verification_info": "❌ Invalid verification information.",
            "max_attempts_reached": "❌ Maximum allowed attempts reached.\nPlease request a new code.",
            "verification_code_expired": "⏰ Verification code has expired.\nPlease request a new code.",
            "incorrect_verification_code": "❌ Incorrect code entered.\nRemaining attempts: {remaining}",
            "error_registering_phone": "❌ Error registering phone number.\nPlease try again.",

            # پیام‌های نقش
            "role_select": "🌟 Please select your role:",

            # پیام‌های فرآیند فعال
            "process_active_prompt": "⚠️ You are currently in an active process.\nWould you like to exit and restart?",
            "restart_yes": "✅ Yes, restart",
            "restart_no": "❌ No, continue current process",

            # پیام‌های انتخاب
            "select_from_buttons": "Please select from the buttons below.",

            # پیام‌های جدید برای submission_handler
            "location_required_for_onsite": "❌ For onsite services, you must provide a location.",
            "submit_request_error": "❌ Error submitting request\n",
            "budget_too_large": "❌ The entered budget is too large. Please enter a smaller amount.",
            "submit_request_general_error": "❌ Error submitting request. Please try again.",
            "submit_project_summary_template": "🎉 Congratulations! Your request with ID {project_id} has been registered!\n<b>📌 Category:</b> {category_name}\n<b>📝 Description:</b> {description}\n<b>📍 Service location:</b> {location_text}",
            "photos_count": "<b>📸 Number of photos:</b> {count}",
            "close_project": "Close",
            "extend_project": "Extend",
            "view_photos": "View photos",
            "view_offers": "Offers",

            # پیام‌های جدید برای view_handler
            "no_projects_registered": "📭 You haven't registered any requests yet!",
            "continue_or_return": "📊 Continue or return:",
            "error_fetching_projects": "❌ Error fetching requests: {status_code}",
            "backend_unavailable": "❌ Error: Backend server is unavailable.",
            "view_projects_prompt": "📋 To view details and manage each request, tap the corresponding button:\n",
            "project_summary_template": "📋 *Request {project_id}*\n📌 *Category*: {category_name}\n📝 *Description*: {description}\n📍 *Location*: {location}\n",
            "project_images_template": "📸 *Images*:\n{images}",
            "error_fetching_project_details": "❌ Error fetching details: {status_code}",

            # پیام‌های جدید برای state_handler
            "error_restart_prompt": "❌ An error occurred. Please start again with /start"
        }
    }
    
    try:
        # استخراج زبان از context
        lang = context.user_data.get('lang', 'fa') if context else 'fa'
        
        # دریافت پیام از دیکشنری پیام‌ها
        message = messages.get(lang, messages["fa"]).get(key, "پیام یافت نشد!")
        
        # اگر پیام نیازی به قالب‌بندی نداشته باشد، مستقیم برگردان
        if '{' not in message or '}' not in message:
            return message
            
        # استخراج متغیرهای پارامتریک از context
        params = dict(kwargs)  # Start with provided keyword arguments
        
        # Skip context-related extraction if context is None
        if context is None:
            return message.format(**params)
            
        # نام کاربر
        if '{name}' in message and update:
            params['name'] = update.effective_user.first_name or ''            
        # نام دسته‌بندی
        if '{category_name}' in message:
            # Use the category_name from kwargs if provided, otherwise look it up
            if 'category_name' in params:
                # Already passed directly as a parameter, don't override
                pass
            else:
                # Try to get from category_id or category_group
                category_id = context.user_data.get('category_id')
                category_group = context.user_data.get('category_group')
                categories = context.user_data.get('categories', {})
                
                if category_id and category_id in categories:
                    params['category_name'] = categories.get(category_id, {}).get('name', '')
                elif category_group and category_group in categories:
                    params['category_name'] = categories.get(category_group, {}).get('name', '')
            
        # توضیحات قبلی
        if '{last_description}' in message:
            params['last_description'] = context.user_data.get('description', '')
            
        # نام محل خدمات
        if '{service_location_name}' in message:
            params['service_location_name'] = context.user_data.get('service_location', '')
              # نشانگر پیشرفت
        if '{current_step}' in message or '{total_steps}' in message:
            # اگر current_step و total_steps از kwargs ارسال شده‌اند، از آن‌ها استفاده کن
            # وگرنه از context.user_data بگیر
            if 'current_step' not in params:
                params['current_step'] = context.user_data.get('current_step', '')
            if 'total_steps' not in params:
                params['total_steps'] = context.user_data.get('total_steps', '')
        # مختصات موقعیت
        if '{latitude}' in message or '{longitude}' in message:
            location = context.user_data.get('location', {})
            params['latitude'] = str(location.get('latitude', '')) if location else ''
            params['longitude'] = str(location.get('longitude', '')) if location else ''
            
        # تاریخ‌ها
        if '{date_str}' in message:
            params['date_str'] = context.user_data.get('need_date', '')
        if '{today}' in message:
            params['today'] = context.user_data.get('today', '')
        if '{tomorrow}' in message:
            params['tomorrow'] = context.user_data.get('tomorrow', '')
        if '{day_after}' in message:
            params['day_after'] = context.user_data.get('day_after', '')
            
        # مهلت انجام
        if '{deadline}' in message:
            params['deadline'] = context.user_data.get('deadline', '')
            
        # بودجه
        if '{formatted_budget}' in message:
            params['formatted_budget'] = context.user_data.get('budget', '')
            
        # مقدار و واحد
        if '{quantity}' in message:
            params['quantity'] = context.user_data.get('quantity', '')            
        # تعداد (مثلاً تعداد عکس‌ها)
        if '{count}' in message:
            params['count'] = str(len(context.user_data.get('files', [])))
            
        # شماره تلفن
        if '{phone}' in message:
            params['phone'] = context.user_data.get('phone', '')
            
        # تعداد تلاش‌های باقی‌مانده
        if '{remaining}' in message:
            params['remaining'] = context.user_data.get('remaining_attempts', '')
            
        # شناسه درخواست
        if '{project_id}' in message:
            params['project_id'] = context.user_data.get('project_id', '')
            
        # توضیحات درخواست
        if '{description}' in message:
            params['description'] = context.user_data.get('description', '')
            
        # متن موقعیت
        if '{location_text}' in message:
            params['location_text'] = context.user_data.get('location_text', '')
            
        # موقعیت
        if '{location}' in message:
            params['location'] = context.user_data.get('location', '')
            
        # تصاویر
        if '{images}' in message:
            params['images'] = context.user_data.get('images', '')
            
        # کد وضعیت خطا
        if '{status_code}' in message:
            params['status_code'] = context.user_data.get('status_code', '')
        
        # قالب‌بندی پیام با متغیرهای استخراج‌شده
        return message.format(**params)
        
    except KeyError:
        # در صورت نبود کلید، پیام پیش‌فرض
        return "پیام یافت نشد!"
    except Exception as e:
        # لاگ خطا برای دیباگ
        print(f"Error in get_message: {e}")
        return "خطا در دریافت پیام!"