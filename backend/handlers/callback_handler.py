from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import logging
from handlers.start_handler import start, check_phone
from handlers.category_handler import handle_category_callback
from handlers.edit_handler import handle_edit_callback
from handlers.view_handler import handle_view_callback
from handlers.attachment_handler import show_photo_management, handle_photos_command
from utils import log_chat, get_categories, ensure_active_chat, restart_chat
from keyboards import create_category_keyboard, EMPLOYER_MENU_KEYBOARD, FILE_MANAGEMENT_MENU_KEYBOARD, RESTART_INLINE_MENU_KEYBOARD, BACK_INLINE_MENU_KEYBOARD, MAIN_MENU_KEYBOARD
import asyncio  # برای استفاده از sleep
from asyncio import Lock

logger = logging.getLogger(__name__)

START, REGISTER, ROLE, EMPLOYER_MENU, CATEGORY, SUBCATEGORY, DESCRIPTION, LOCATION_TYPE, LOCATION_INPUT, DETAILS, DETAILS_FILES, DETAILS_DATE, DETAILS_DEADLINE, DETAILS_BUDGET, DETAILS_QUANTITY, SUBMIT, VIEW_PROJECTS, PROJECT_ACTIONS = range(18)
CHANGE_PHONE, VERIFY_CODE = range(20, 22)  # states جدید

# ایجاد قفل سراسری
button_lock = Lock()

async def send_photo_with_caption(context, chat_id, photo, caption, reply_markup=None):
    await context.bot.send_photo(
        chat_id=chat_id,
        photo=photo,
        caption=caption,
        reply_markup=reply_markup
    )

async def send_message_with_keyboard(context, chat_id, text, reply_markup):
    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=reply_markup
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main callback handler with improved error handling"""
    query = update.callback_query
    if not query:
        return START

    try:
        data = query.data
        current_state = context.user_data.get('state', ROLE)
        previous_state = context.user_data.get('previous_state')
        logger.info(f"Handling callback: {data}")
        logger.info(f"Current state: {current_state}")
        logger.info(f"Previous state: {previous_state}")

        # پردازش برای دکمه اتمام ارسال تصاویر
        if data == "finish_files":
            logger.info("User clicked finish_files button")
            context.user_data['state'] = DETAILS
            # ویرایش پیام موجود و نمایش منوی جزئیات
            from keyboards import create_dynamic_keyboard
            await query.message.edit_text(
                "📋 جزئیات درخواست:",
                reply_markup=create_dynamic_keyboard(context)
            )
            await query.answer()
            return DETAILS
            
        # پردازش برای دکمه مدیریت عکس‌ها
        if data == "manage_photos":
            logger.info("User clicked manage_photos button")
            await show_photo_management(update, context)
            await query.answer()
            return DETAILS_FILES
            
        # پردازش برای بازگشت به آپلود
        if data == "back_to_upload":
            logger.info("User returning to file upload")
            await query.message.edit_text(
                "📸 می‌تونی تا ۵ تا عکس ارسال کنی یا یکی از گزینه‌ها رو انتخاب کنی:",
                reply_markup=FILE_MANAGEMENT_MENU_KEYBOARD
            )
            await query.answer()
            return DETAILS_FILES
            
        # پردازش برای بازگشت به مدیریت عکس‌ها
        if data == "back_to_management":
            logger.info("User returning to photo management")
            await show_photo_management(update, context)
            await query.answer()
            return DETAILS_FILES

        # بازگشت به منوی قبلی بر اساس state فعلی
        if data == "back_to_menu":
            logger.info("Processing back to menu")
            # اگر در مرحله انتخاب دسته‌بندی هستیم
            if current_state == CATEGORY:
                context.user_data['state'] = EMPLOYER_MENU
                await query.message.edit_text(
                    "🎉 عالیه! چه کاری برات انجام بدم؟",
                    reply_markup=EMPLOYER_MENU_KEYBOARD
                )
                await query.answer()
                return EMPLOYER_MENU
            # اگر در منوی کارفرما هستیم    
            elif current_state == EMPLOYER_MENU:
                context.user_data['state'] = ROLE
                await query.message.edit_text(
                    "🌟 لطفاً یکی از گزینه‌ها را انتخاب کنید:",
                    reply_markup=MAIN_MENU_KEYBOARD
                )
                await query.answer()
                return ROLE

        # بازگشت به منوی کارفرما
        if data == "back_to_employer_menu":
            logger.info("Processing back to employer menu")
            # ذخیره state قبلی
            context.user_data['previous_state'] = current_state
            context.user_data['state'] = EMPLOYER_MENU
            await query.message.edit_text(
                "🎉 عالیه! چه کاری برات انجام بدم؟",
                reply_markup=EMPLOYER_MENU_KEYBOARD
            )
            await query.answer()
            return EMPLOYER_MENU

        # پردازش دسته‌بندی
        if data.startswith(('cat_', 'subcat_')):
            logger.info(f"Processing category selection: {data}")
            from handlers.category_handler import handle_category_selection
            context.user_data['previous_state'] = EMPLOYER_MENU
            context.user_data['state'] = CATEGORY
            categories = await get_categories()
            if not categories:
                logger.error("Failed to fetch categories")
                await query.answer("❌ خطا در دریافت دسته‌بندی‌ها")
                return EMPLOYER_MENU
            
            context.user_data['categories'] = categories
            return await handle_category_selection(update, context)

        # بررسی وضعیت ثبت‌نام کاربر
        if not await check_phone(update, context):
            logger.info("User needs to register phone first")
            await query.answer("لطفا ابتدا شماره تلفن خود را ثبت کنید")
            return REGISTER
            
        # پردازش دکمه ثبت شماره تلفن از طریق کیبورد اینلاین
        if data == "register_phone":
            logger.info("User clicked register_phone button")
            await query.answer("لطفا شماره تلفن خود را به اشتراک بگذارید")
            from keyboards import REGISTER_MENU_KEYBOARD
            await query.message.reply_text(
                "📱 برای ثبت شماره تلفن، لطفا روی دکمه زیر کلیک کنید:",
                reply_markup=REGISTER_MENU_KEYBOARD
            )
            context.user_data['state'] = REGISTER
            return REGISTER
            
        # دکمه شروع مجدد
        if data == "restart":
            logger.info("User requested restart")
            await query.answer("در حال راه‌اندازی مجدد...")
            await restart_chat(update, context)
            return START

        # ادامه پردازش callback
        if data == "employer":
            try:
                await query.message.edit_text(
                    "🎉 عالیه! چه کاری برات انجام بدم؟",
                    reply_markup=EMPLOYER_MENU_KEYBOARD
                )
                context.user_data['state'] = EMPLOYER_MENU
                await query.answer()
                return EMPLOYER_MENU
            except Exception as e:
                logger.error(f"Error editing message for employer menu: {e}")
                await query.answer("❌ خطا در نمایش منو")
                return context.user_data.get('state')
            
        elif data == "new_request":
            logger.info("Processing new request")
            # Clear user data to ensure no previous data persists
            context.user_data.clear()
            context.user_data['files'] = []
            context.user_data['state'] = CATEGORY
            
            categories = await get_categories()
            keyboard = create_category_keyboard(categories)
            await query.edit_message_text(
                "🌟 دسته‌بندی خدماتت رو انتخاب کن:",
                reply_markup=keyboard
            )
            await query.answer()
            return CATEGORY
            
        await query.answer()
        return context.user_data.get('state', START)
        
    except Exception as e:
        logger.error(f"Error in callback handler: {e}", exc_info=True)
        try:
            await query.answer("❌ خطایی رخ داد!")
        except Exception:
            pass
        return START

async def handle_new_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    try:
        # پاک کردن context کاربر
        context.user_data.clear()
        
        # تنظیم state جدید
        context.user_data['state'] = CATEGORY
        context.user_data['files'] = []
        
        # دریافت دسته‌بندی‌ها
        categories = await get_categories()
        if not categories:
            await query.message.reply_text("❌ خطا: دسته‌بندی‌ها در دسترس نیست!")
            return EMPLOYER_MENU
            
        context.user_data['categories'] = categories
        
        # نمایش منوی دسته‌بندی‌ها
        root_cats = [cat_id for cat_id, cat in categories.items() if cat['parent'] is None]
        keyboard = [[InlineKeyboardButton(categories[cat_id]['name'])] for cat_id in root_cats]
        keyboard.append([InlineKeyboardButton("⬅️ بازگشت")])
        
        # حذف پیام‌های قبلی
        await query.message.delete()
        
        # ارسال منوی جدید
        await query.message.reply_text(
            "🌟 دسته‌بندی خدماتت رو انتخاب کن:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        await query.answer()
        return CATEGORY
        
    except Exception as e:
        logger.error(f"Error in new_request handler: {e}")
        await query.message.reply_text(
            "❌ خطا در شروع درخواست جدید. لطفاً دوباره تلاش کنید.",
            reply_markup=EMPLOYER_MENU_KEYBOARD
        )
        return EMPLOYER_MENU

async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    # بازگشت به منوی اصلی
    await query.message.reply_text(
        "🌟 چی می‌خوای امروز؟", 
        reply_markup=MAIN_MENU_KEYBOARD
    )
    return ROLE

async def handle_photos_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    data = query.data
    logger.info(f"Received callback data: {data}")  # لاگ اولیه

    if data.startswith('view_photos_'):
        try:
            project_id = data.split('_')[2]
            logger.info(f"Processing view_photos callback for project {project_id}")  # لاگ پردازش
            
            # اجرای دستور view_photos
            context.user_data['current_project_id'] = project_id
            logger.info(f"Set current_project_id to {project_id}")  # لاگ تنظیم project_id
            
            # اجرای مستقیم تابع handle_photos_command
            await handle_photos_command(update, context)
            logger.info("Finished handling photos command")  # لاگ اتمام پردازش
            
            await query.answer()
            return PROJECT_ACTIONS
            
        except Exception as e:
            logger.error(f"Error processing view_photos callback: {e}")  # لاگ خطا
            await query.answer("خطا در نمایش عکس‌ها")
            return PROJECT_ACTIONS

    await query.answer()
    data = query.data
    logger.info(f"Callback data received: {data}")
    await log_chat(update, context)

    chat_id = update.effective_chat.id

    try:
        if data.startswith('view_photo_'):
            index = int(data.split('_')[2])
            files = context.user_data.get('files', [])
            if 0 <= index < len(files):
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=files[index],
                    caption=f"📸 عکس {index+1} از {len(files)}"
                )
            return DETAILS_FILES

        elif data.startswith('edit_photo_'):
            index = int(data.split('_')[2])
            files = context.user_data.get('files', [])
            if 0 <= index < len(files):
                keyboard = [
                    [InlineKeyboardButton("🗑 حذف", callback_data=f"delete_photo_{index}"),
                     InlineKeyboardButton("🔄 جایگزینی", callback_data=f"replace_photo_{index}")],
                    [InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_management")]
                ]
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=files[index],
                    caption=f"📸 عکس {index+1} از {len(files)}",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            return DETAILS_FILES

        elif data.startswith('delete_photo_'):
            index = int(data.split('_')[2])
            files = context.user_data.get('files', [])
            if 0 <= index < len(files):
                deleted_file = files.pop(index)
                logger.info(f"Deleted photo {deleted_file} at index {index}")
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="🗑 عکس حذف شد! دوباره مدیریت کن یا ادامه بده.",
                )
            return DETAILS_FILES
    except Exception as e:
        logger.error(f"Error processing photo management callback: {e}")
        await query.answer("خطا در مدیریت عکس‌ها")
        return DETAILS_FILES
