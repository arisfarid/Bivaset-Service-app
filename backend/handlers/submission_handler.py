from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from utils import generate_title, convert_deadline_to_date, log_chat, BASE_URL
import requests
import logging
from handlers.start_handler import start
from handlers.attachment_handler import upload_attachments
from keyboards import EMPLOYER_MENU_KEYBOARD  # اضافه کردن import در بالای فایل

logger = logging.getLogger(__name__)

START, REGISTER, ROLE, EMPLOYER_MENU, CATEGORY, SUBCATEGORY, DESCRIPTION, LOCATION_TYPE, LOCATION_INPUT, DETAILS, DETAILS_FILES, DETAILS_DATE, DETAILS_DEADLINE, DETAILS_BUDGET, DETAILS_QUANTITY, SUBMIT, VIEW_PROJECTS, PROJECT_ACTIONS = range(18)

# در متد submit_project در submission_handler.py
async def submit_project(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text != "✅ ثبت درخواست":
        return DETAILS

    try:
        # آماده‌سازی داده‌های پروژه
        category_id = context.user_data.get('category_id')
        category_name = context.user_data.get('categories', {}).get(category_id, {}).get('name', 'نامشخص')
        
        data = {
            'title': generate_title(context),
            'description': context.user_data.get('description', ''),
            'category': category_id,  # حتماً باید category_id باشد
            'service_location': context.user_data.get('service_location', ''),
            'user_telegram_id': str(update.effective_user.id)
        }

        # مدیریت location براساس نوع خدمت
        service_location = context.user_data.get('service_location')
        if service_location == 'remote':
            # برای خدمات غیرحضوری، location را با یک آرایه خالی تنظیم می‌کنیم
            data['location'] = []
        elif service_location in ['client_site', 'contractor_site']:
            # برای خدمات حضوری، location را از context می‌گیریم
            if location := context.user_data.get('location'):
                data['location'] = [location['longitude'], location['latitude']]
            else:
                await update.message.reply_text("❌ برای خدمات حضوری، باید لوکیشن را وارد کنید.")
                return DETAILS

        # اضافه کردن فیلدهای اختیاری
        if context.user_data.get('budget'):
            data['budget'] = context.user_data['budget']
        if context.user_data.get('need_date'):
            data['start_date'] = context.user_data['need_date']
        if context.user_data.get('deadline'):
            data['deadline_date'] = convert_deadline_to_date(context.user_data['deadline'])

        logger.info(f"Sending project data to API: {data}")
        await log_chat(update, context)

        response = requests.post(f"{BASE_URL}projects/", json=data)
        logger.info(f"API Response: {response.status_code} - {response.text}")

        if response.status_code == 201:
            project_data = response.json()
            project_id = project_data.get('id')
            context.user_data['project_id'] = project_id  # ذخیره project_id
            
            # آپلود فایل‌ها
            files = context.user_data.get('files', [])
            if files:
                uploaded_files = await upload_attachments(files, context)
                context.user_data['uploaded_files'] = uploaded_files
                logger.info(f"Uploaded files: {uploaded_files}")
            
            # آماده‌سازی پیام نهایی و دکمه‌ها
            message = prepare_final_message(context, project_id)
            keyboard = prepare_inline_keyboard(project_id, bool(files))

            # ارسال پیام نهایی با عکس اول (اگر وجود داشته باشد)
            if files:
                try:
                    # ارسال عکس اول با کپشن و دکمه‌ها
                    await update.message.reply_photo(
                        photo=files[0],  # استفاده از اولین عکس
                        caption=message,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode='HTML'
                    )
                except Exception as e:
                    logger.error(f"Error sending photo message: {e}")
                    # اگر ارسال عکس با خطا مواجه شد، پیام متنی ارسال می‌کنیم
                    await update.message.reply_text(
                        text=message,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode='HTML'
                    )
            else:
                await update.message.reply_text(
                    text=message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='HTML'
                )

            # نمایش دکمه‌های اینلاین برای هدایت کاربر
            navigation_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("👀 مشاهده درخواست", callback_data=f"view_{project_id}")],
                [InlineKeyboardButton("📋 ثبت درخواست جدید", callback_data="new_request"),
                 InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]
            ])

            await update.message.reply_text(
                "✅ درخواست شما با موفقیت ثبت شد.\n"
                "می‌توانید:",
                reply_markup=navigation_keyboard
            )
            
            # ارسال ایموجی متحرک برای گیمیفیکیشن
            await update.message.reply_animation(
                animation="CgACAgQAAxkBAAMmZWcJ4M7DAAEn2Wv3H8QE3qwWxjcAAgsAA0d1_FNjwrcbKHUhHjAE",  # ایموجی متحرک مناسب
                caption="🎊 درخواست شما با موفقیت ثبت شد!"
            )

            # پاک کردن داده‌های قبلی
            context.user_data.clear()
            
            return ConversationHandler.END

        else:
            error_msg = "❌ خطا در ثبت درخواست\n"
            if response.status_code == 400:
                try:
                    errors = response.json()
                    if 'budget' in errors:
                        error_msg = "❌ مبلغ وارد شده خیلی بزرگ است. لطفاً مبلغ کمتری وارد کنید."
                        context.user_data['state'] = DETAILS_BUDGET
                        await update.message.reply_text(
                            error_msg,
                            reply_markup=create_dynamic_keyboard(context)
                        )
                        return DETAILS_BUDGET
                except:
                    pass
            
            await update.message.reply_text(
                error_msg,
                reply_markup=create_dynamic_keyboard(context)
            )
            return DETAILS

    except Exception as e:
        logger.error(f"Error in submit_project: {e}")
        await update.message.reply_text(
            "❌ خطا در ثبت درخواست. لطفاً دوباره تلاش کنید.",
            reply_markup=create_dynamic_keyboard(context)
        )
        return DETAILS

def prepare_final_message(context, project_id):
    """آماده‌سازی پیام نهایی"""
    category_id = context.user_data.get('category_id')
    category_name = context.user_data.get('categories', {}).get(str(category_id), {}).get('name') or \
                   context.user_data.get('categories', {}).get(category_id, {}).get('name', 'نامشخص')
    
    # نمایش نوع محل خدمات و لوکیشن
    service_location = context.user_data.get('service_location')
    location_text = {
        'remote': 'غیرحضوری',
        'client_site': 'محل من',
        'contractor_site': 'محل مجری'
    }.get(service_location, 'نامشخص')
    
    message_lines = [
        f"🎉 تبریک! درخواست شما با کد {project_id} ثبت شد!",
        f"<b>📌 دسته‌بندی:</b> {category_name}",
        f"<b>📝 توضیحات:</b> {context.user_data.get('description', '')}",
        f"<b>📍 محل خدمات:</b> {location_text}"
    ]

    # اضافه کردن لینک لوکیشن اگر غیرحضوری نیست
    if service_location in ['client_site', 'contractor_site'] and context.user_data.get('location'):
        location = context.user_data['location']
        message_lines.append(
            f"<b>📍 موقعیت:</b> <a href=\"https://maps.google.com/maps?q={location['latitude']},{location['longitude']}\">نمایش روی نقشه</a>"
        )
    
    # اضافه کردن اطلاعات عکس‌ها
    files = context.user_data.get('files', [])
    if files:
        message_lines.append(f"<b>📸 تعداد عکس‌ها:</b> {len(files)}")
    
    # سایر اطلاعات
    if context.user_data.get('need_date'):
        message_lines.append(f"<b>📅 تاریخ نیاز:</b> {context.user_data['need_date']}")
    if context.user_data.get('budget'):
        message_lines.append(f"<b>💰 بودجه:</b> {context.user_data['budget']} تومان")
    if context.user_data.get('deadline'):
        message_lines.append(f"<b>⏳ مهلت انجام:</b> {context.user_data['deadline']} روز")
    if context.user_data.get('quantity'):
        message_lines.append(f"<b>📏 مقدار و واحد:</b> {context.user_data['quantity']}")
    
    return "\n".join(message_lines)

def prepare_inline_keyboard(project_id, has_files):
    """آماده‌سازی دکمه‌های inline"""
    keyboard = [
        [InlineKeyboardButton("✏️ ویرایش", callback_data=f"edit_{project_id}"),
         InlineKeyboardButton("⛔ بستن", callback_data=f"close_{project_id}")],
        [InlineKeyboardButton("🗑 حذف", callback_data=f"delete_{project_id}"),
         InlineKeyboardButton("⏰ تمدید", callback_data=f"extend_{project_id}")]
    ]
    
    # فقط اگر عکس داشته باشیم، دکمه نمایش عکس‌ها را اضافه می‌کنیم
    if has_files:
        keyboard.append([
            InlineKeyboardButton("📸 نمایش عکس‌ها", callback_data=f"view_photos_{project_id}")
        ])
    
    keyboard.append([
        InlineKeyboardButton("💡 پیشنهادها", callback_data=f"offers_{project_id}")
    ])
    
    return keyboard