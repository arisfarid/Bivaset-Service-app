from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import logging
from handlers.start_handler import start
from handlers.category_handler import handle_category_callback
from handlers.edit_handler import handle_edit_callback
from handlers.view_handler import handle_view_callback
from handlers.attachment_handler import show_photo_management, handle_photos_command
from utils import log_chat,get_categories
from keyboards import EMPLOYER_MENU_KEYBOARD, FILE_MANAGEMENT_MENU_KEYBOARD, RESTART_INLINE_MENU_KEYBOARD, BACK_INLINE_MENU_KEYBOARD, MAIN_MENU_KEYBOARD
import asyncio  # برای استفاده از sleep
from asyncio import Lock

logger = logging.getLogger(__name__)

START, REGISTER, ROLE, EMPLOYER_MENU, CATEGORY, SUBCATEGORY, DESCRIPTION, LOCATION_TYPE, LOCATION_INPUT, DETAILS, DETAILS_FILES, DETAILS_DATE, DETAILS_DEADLINE, DETAILS_BUDGET, DETAILS_QUANTITY, SUBMIT, VIEW_PROJECTS, PROJECT_ACTIONS = range(18)

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

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    data = query.data
    
    if data == "restart":
        try:
            # پاک کردن context کاربر
            context.user_data.clear()
            
            # پاک کردن پیام آپدیت
            await query.message.delete()
            
            # ارسال منوی اصلی با پیام جدید
            await query.message.reply_text(
                "🌟 چی می‌خوای امروز؟",
                reply_markup=MAIN_MENU_KEYBOARD
            )
            
            await query.answer("✅ راه‌اندازی مجدد انجام شد")
            return ROLE
            
        except Exception as e:
            logger.error(f"Error in restart handler: {e}")
            return ROLE

    elif data == "new_request":
        # تنظیم context برای درخواست جدید
        context.user_data.clear()
        context.user_data['categories'] = await get_categories()
        keyboard = create_categories_keyboard(context.user_data['categories'])
        
        await query.message.edit_text(
            "🌟 دسته‌بندی خدماتت رو انتخاب کن:",
            reply_markup=keyboard
        )
        return CATEGORY
    
    # ... سایر callback ها

    return ROLE

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
        keyboard = [[KeyboardButton(categories[cat_id]['name'])] for cat_id in root_cats]
        keyboard.append([KeyboardButton("⬅️ بازگشت")])
        
        # حذف پیام‌های قبلی
        await query.message.delete()
        
        # ارسال منوی جدید
        await query.message.reply_text(
            "🌟 دسته‌بندی خدماتت رو انتخاب کن:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
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
