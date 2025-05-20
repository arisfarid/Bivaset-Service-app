from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from utils import generate_title, convert_deadline_to_date, log_chat, BASE_URL, upload_files
import requests
import logging
from handlers.start_handler import start
from keyboards import create_dynamic_keyboard, get_main_menu_keyboard
import asyncio
from handlers.phone_handler import require_phone
from localization import get_message
from handlers.states import START, REGISTER, ROLE, EMPLOYER_MENU, CATEGORY, SUBCATEGORY, DESCRIPTION, LOCATION_TYPE, LOCATION_INPUT, DETAILS, DETAILS_FILES, DETAILS_DATE, DETAILS_DEADLINE, DETAILS_BUDGET, DETAILS_QUANTITY, SUBMIT, VIEW_PROJECTS, PROJECT_ACTIONS, CHANGE_PHONE, VERIFY_CODE

logger = logging.getLogger(__name__)

@require_phone
async def submit_project(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get('lang', 'fa')
    if update.message.text != get_message("submit", lang=lang):
        return DETAILS

    try:
        # آماده‌سازی داده‌های پروژه
        category_id = context.user_data.get('category_id')
        category_name = context.user_data.get('categories', {}).get(category_id, {}).get('name', 'نامشخص')
        
        data = {
            'title': generate_title(context),
            'description': context.user_data.get('description', ''),
            'category': category_id,
            'service_location': context.user_data.get('service_location', ''),
            'user_telegram_id': str(update.effective_user.id)
        }

        # مدیریت location براساس نوع خدمت
        service_location = context.user_data.get('service_location')
        if service_location == 'remote':
            data['location'] = []
        elif service_location in ['client_site', 'contractor_site']:
            if location := context.user_data.get('location'):
                data['location'] = [location['longitude'], location['latitude']]
            else:
                await update.message.reply_text(get_message("location_required_for_onsite", lang=lang))
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
            context.user_data['project_id'] = project_id
            
            # آپلود فایل‌ها
            files = context.user_data.get('files', [])
            if files:
                uploaded_files = await upload_files(files, context)
                context.user_data['uploaded_files'] = uploaded_files
                logger.info(f"Uploaded files: {uploaded_files}")
            
            # ارسال ایموجی متحرک
            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="🎉",
                    parse_mode='HTML'
                )
                
                await asyncio.sleep(2)
                
                await context.bot.delete_message(
                    chat_id=update.effective_chat.id,
                    message_id=update.message.message_id + 1
                )
            except Exception as e:
                logger.error(f"Error handling animation: {e}")

            # آماده‌سازی و ارسال پیام نهایی
            message = prepare_final_message(context, project_id)
            keyboard = prepare_inline_keyboard(project_id, bool(files))
            
            if files:
                try:
                    await update.message.reply_photo(
                        photo=files[0],
                        caption=message,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode='HTML'
                    )
                except Exception as e:
                    logger.error(f"Error sending photo message: {e}")
                    await update.message.reply_text(
                        text=message,
                        parse_mode='HTML',
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
            else:
                await update.message.reply_text(
                    text=message,
                    parse_mode='HTML',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )

            # ارسال منوی اصلی به صورت کیبورد ساده
            await update.message.reply_text(
                get_message("employer_menu_prompt", lang=lang, name=update.effective_user.full_name),
                reply_markup=get_main_menu_keyboard(lang)
            )

            # پاک کردن داده‌های قبلی
            context.user_data.clear()
            
            return ROLE

        else:
            error_msg = get_message("submit_request_error", lang=lang)
            if response.status_code == 400:
                try:
                    errors = response.json()
                    if 'budget' in errors:
                        error_msg = get_message("budget_too_large", lang=lang)
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
                reply_markup=get_main_menu_keyboard(lang)
            )
            return ROLE

    except Exception as e:
        logger.error(f"Error in submit_project: {e}")
        await update.message.reply_text(
            get_message("submit_request_general_error", lang=lang),
            reply_markup=get_main_menu_keyboard(lang)
        )
        return ROLE

def prepare_final_message(context, project_id):
    """آماده‌سازی پیام نهایی"""
    lang = context.user_data.get('lang', 'fa')
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
        get_message("submit_project_summary_template", lang=lang, project_id=project_id, category_name=category_name,
                    description=context.user_data.get('description', ''), location_text=location_text)
    ]

    # اضافه کردن لینک لوکیشن اگر غیرحضوری نیست
    if service_location in ['client_site', 'contractor_site'] and context.user_data.get('location'):
        location = context.user_data['location']
        message_lines.append(
            f"<b>📍 موقعیت:</b> {get_message('location_map_link', lang=lang, latitude=location['latitude'], longitude=location['longitude'])}"
        )
    
    # اضافه کردن اطلاعات عکس‌ها
    files = context.user_data.get('files', [])
    if files:
        message_lines.append(get_message("photos_count", lang=lang, count=len(files)))
    
    # سایر اطلاعات
    if context.user_data.get('need_date'):
        message_lines.append(get_message("need_date_saved", lang=lang, date_str=context.user_data['need_date']))
    if context.user_data.get('budget'):
        message_lines.append(get_message("budget_saved", lang=lang, formatted_budget=context.user_data['budget']))
    if context.user_data.get('deadline'):
        message_lines.append(get_message("deadline_saved", lang=lang, deadline=context.user_data['deadline']))
    if context.user_data.get('quantity'):
        message_lines.append(get_message("quantity_saved", lang=lang, quantity=context.user_data['quantity']))
    
    return "\n".join(message_lines)

def prepare_inline_keyboard(project_id, has_files):
    """آماده‌سازی دکمه‌های inline"""
    lang = 'fa'  # زبان پیش‌فرض
    keyboard = [
        [
            InlineKeyboardButton(get_message("edit", lang=lang), callback_data=f"edit_{project_id}"),
            InlineKeyboardButton(f"⛔ {get_message('close_project', lang=lang)}", callback_data=f"close_{project_id}")
        ],
        [
            InlineKeyboardButton(get_message("delete_with_icon", lang=lang), callback_data=f"delete_{project_id}"),
            InlineKeyboardButton(f"⏰ {get_message('extend_project', lang=lang)}", callback_data=f"extend_{project_id}")
        ]
    ]
    
    if has_files:
        keyboard.append([
            InlineKeyboardButton(f"📸 {get_message('view_photos', lang=lang)}", callback_data=f"view_photos_{project_id}")
        ])
    
    keyboard.append([
        InlineKeyboardButton(f"💡 {get_message('view_offers', lang=lang)}", callback_data=f"offers_{project_id}")
    ])
    
    return keyboard