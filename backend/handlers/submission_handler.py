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
    if update.message.text != get_message("submit", context, update):
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
                await update.message.reply_text(get_message("location_required_for_onsite", context, update))
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
            message = prepare_final_message(context, project_id, update)
            keyboard = prepare_inline_keyboard(project_id, bool(files), context, update)
            
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
                get_message("employer_menu_prompt", context, update),
                reply_markup=get_main_menu_keyboard(context, update)
            )

            # پاک کردن داده‌های قبلی
            context.user_data.clear()
            
            return ROLE

        else:
            error_msg = get_message("submit_request_error", context, update)
            if response.status_code == 400:
                try:
                    errors = response.json()
                    if 'budget' in errors:
                        error_msg = get_message("budget_too_large", context, update)
                        context.user_data['state'] = DETAILS_BUDGET
                        await update.message.reply_text(
                            error_msg,
                            reply_markup=create_dynamic_keyboard(context, update)
                        )
                        return DETAILS_BUDGET
                except:
                    pass
            
            await update.message.reply_text(
                error_msg,
                reply_markup=get_main_menu_keyboard(context, update)
            )
            return ROLE

    except Exception as e:
        logger.error(f"Error in submit_project: {e}")
        await update.message.reply_text(
            get_message("submit_request_general_error", context, update),
            reply_markup=get_main_menu_keyboard(context, update)
        )
        return ROLE

def prepare_final_message(context: ContextTypes.DEFAULT_TYPE, project_id: int, update: Update) -> str:
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
        get_message("submit_project_summary_template", context, update)
    ]

    # اضافه کردن لینک لوکیشن اگر غیرحضوری نیست
    if service_location in ['client_site', 'contractor_site'] and context.user_data.get('location'):
        location = context.user_data['location']
        message_lines.append(
            f"<b>📍 موقعیت:</b> {get_message('location_map_link', context, update)}"
        )
    
    # اضافه کردن اطلاعات عکس‌ها
    files = context.user_data.get('files', [])
    if files:
        message_lines.append(get_message("photos_count", context, update))
    
    # سایر اطلاعات
    if context.user_data.get('need_date'):
        message_lines.append(get_message("need_date_saved", context, update))
    if context.user_data.get('budget'):
        message_lines.append(get_message("budget_saved", context, update))
    if context.user_data.get('deadline'):
        message_lines.append(get_message("deadline_saved", context, update))
    if context.user_data.get('quantity'):
        message_lines.append(get_message("quantity_saved", context, update))
    
    return "\n".join(message_lines)

def prepare_inline_keyboard(project_id: int, has_files: bool, context: ContextTypes.DEFAULT_TYPE, update: Update) -> list:
    """آماده‌سازی دکمه‌های inline"""
    keyboard = [
        [
            InlineKeyboardButton(get_message("edit", context, update), callback_data=f"edit_{project_id}"),
            InlineKeyboardButton(f"⛔ {get_message('close_project', context, update)}", callback_data=f"close_{project_id}")
        ],
        [
            InlineKeyboardButton(get_message("delete_with_icon", context, update), callback_data=f"delete_{project_id}"),
            InlineKeyboardButton(f"⏰ {get_message('extend_project', context, update)}", callback_data=f"extend_{project_id}")
        ]
    ]
    
    if has_files:
        keyboard.append([
            InlineKeyboardButton(f"📸 {get_message('view_photos', context, update)}", callback_data=f"view_photos_{project_id}")
        ])
    
    keyboard.append([
        InlineKeyboardButton(f"💡 {get_message('view_offers', context, update)}", callback_data=f"offers_{project_id}")
    ])
    
    return keyboard