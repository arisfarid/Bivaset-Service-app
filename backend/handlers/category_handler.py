from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from utils import get_categories, log_chat, delete_previous_messages
import logging
from handlers.start_handler import start
from keyboards import (
    create_category_keyboard,
    get_employer_menu_keyboard,
    create_navigation_keyboard,
    create_subcategory_keyboard,
    create_category_confirmation_keyboard,
    create_category_error_keyboard,
    get_location_type_keyboard
)
from handlers.phone_handler import require_phone
from localization import get_message
from handlers.states import START, REGISTER, ROLE, EMPLOYER_MENU, CATEGORY, SUBCATEGORY, DESCRIPTION, LOCATION_TYPE, LOCATION_INPUT, DETAILS, DETAILS_FILES, DETAILS_DATE, DETAILS_DEADLINE, DETAILS_BUDGET, DETAILS_QUANTITY, SUBMIT, VIEW_PROJECTS, PROJECT_ACTIONS, CHANGE_PHONE, VERIFY_CODE
import asyncio

logger = logging.getLogger(__name__)

@require_phone
async def handle_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.debug(f"[handle_category_selection] user_id={update.effective_user.id} | state={context.user_data.get('state')}")
    """Handle category and subcategory selection"""
    query = update.callback_query
    message = update.message
    if not query:
        # اگر کاربر پیام غیرمجاز (متن، عکس و ...) ارسال کرد
        sent = await message.reply_text(
            get_message("only_select_from_buttons", context, update),
            reply_markup=ReplyKeyboardRemove()
        )
        await delete_previous_messages(sent, context, n=3)
        # نمایش مجدد منوی دسته‌بندی اصلی
        sent2 = await message.reply_text(
            get_message("category_main_select", context, update),
            reply_markup=create_category_keyboard(context.user_data.get('categories', {}), context, update)
        )
        await delete_previous_messages(sent2, context, n=3)
        return CATEGORY

    try:
        data = query.data
        current_state = context.user_data.get('state', CATEGORY)
        previous_state = context.user_data.get('previous_state')
        logger.info(f"Category selection - Data: {data}, State: {current_state}, Previous: {previous_state}")

        # برگشت به منوی کارفرما
        if data == "back_to_menu":
            logger.info("Returning to employer menu")
            context.user_data['state'] = EMPLOYER_MENU
            # نمایش مجدد منوی کارفرما
            sent = await query.message.reply_text(
                get_message("employer_menu_prompt", context, update),
                reply_markup=get_employer_menu_keyboard(context, update)
            )
            await delete_previous_messages(sent, context, n=3)
            return EMPLOYER_MENU

        # رفتن به مرحله بعد (انتخاب لوکیشن)
        if data == "continue_to_location":
            logger.info(f"[handle_category_selection] continue_to_location pressed | context.user_data={context.user_data}")
            if context.user_data.get('category_id'):
                context.user_data['state'] = LOCATION_TYPE
                logger.info(f"[handle_category_selection] state changed to LOCATION_TYPE | context.user_data={context.user_data}")
                await query.answer()  # پاسخ به callback
                # Instead of directly calling handle_location, we'll show the location type guidance
                await query.message.edit_text(
                    get_message("location_type_guidance", context, update),
                    reply_markup=get_location_type_keyboard(context, update),
                    parse_mode="Markdown"
                )
                return LOCATION_TYPE
            else:
                logger.warning("Cannot proceed to location: No category selected")
                await query.answer(get_message("category_select_first", context, update))
                return CATEGORY

        # پردازش انتخاب دسته‌بندی اصلی
        if data.startswith("cat_"):
            category_id = int(data.split("_")[1])
            categories = context.user_data.get('categories')
            if not categories:
                categories = await get_categories()
                context.user_data['categories'] = categories

            selected_category = categories.get(category_id)
            if not selected_category:
                await query.answer(get_message("category_error", context, update))
                return CATEGORY
                
            children = selected_category.get('children', [])
            if children:
                context.user_data['category_group'] = category_id
                sent = await query.message.edit_text(
                    get_message("select_subcategory", context, update, category_name=selected_category['name']),
                    reply_markup=create_subcategory_keyboard(categories, category_id, context, update)
                )
                return SUBCATEGORY

            # اگر زیرمجموعه نداشت، ذخیره دسته بندی و ادامه به مرحله بعدی
            context.user_data['category_id'] = category_id
            context.user_data['category_name'] = selected_category['name']
            
            # نمایش پیام تایید با دکمه‌های بازگشت و ادامه
            await query.message.edit_text(
                get_message("category_confirmation", context, update),
                reply_markup=create_category_confirmation_keyboard(selected_category['name'], context, update)
            )
            return CATEGORY

        # پردازش انتخاب زیرمجموعه
        elif data.startswith("subcat_"):
            subcategory_id = int(data.split("_")[1])
            categories = context.user_data.get('categories')
            if not categories:
                categories = await get_categories()
                context.user_data['categories'] = categories

            selected_subcategory = categories.get(subcategory_id)
            if not selected_subcategory:
                await query.answer(get_message("invalid_subcategory", context, update))
                return SUBCATEGORY
                
            children = selected_subcategory.get('children', [])
            if children:
                context.user_data['category_group'] = subcategory_id
                sent = await query.message.edit_text(
                    get_message("select_subcategory", context, update, category_name=selected_subcategory['name']),
                    reply_markup=create_subcategory_keyboard(categories, subcategory_id, context, update)
                )
                return SUBCATEGORY

            # اگر زیرمجموعه نداشت، ذخیره دسته بندی و ادامه به مرحله بعدی
            context.user_data['category_id'] = subcategory_id
            context.user_data['category_name'] = selected_subcategory['name']
            
            # نمایش پیام تایید با دکمه‌های بازگشت و ادامه
            await query.message.edit_text(
                get_message("category_confirmation", context, update),
                reply_markup=create_category_confirmation_keyboard(selected_subcategory['name'], context, update)
            )
            return CATEGORY

        # برگشت به لیست دسته‌بندی‌ها
        elif data == "back_to_categories":
            categories = context.user_data.get('categories', {})
            category_group = context.user_data.get('category_group')
            if category_group and categories.get(category_group):
                parent = categories[category_group]
                parent_id = parent.get('parent')
                
                if parent_id is not None:                    # تعیین grandparent برای نمایش نام دسته بالادستی
                    grandparent = categories.get(parent_id)
                    # نمایش کیبورد زیردسته‌های والد از طریق تابع متمرکز
                    sent = await query.message.edit_text(
                        get_message("select_subcategory", context, update, category_name=grandparent['name']),
                        reply_markup=create_subcategory_keyboard(categories, parent_id, context, update)
                    )
                    context.user_data['category_group'] = parent_id
                else:
                    # اگر در بالاترین سطح هستیم، به منوی اصلی دسته‌بندی‌ها برمی‌گردیم
                    keyboard = create_category_keyboard(categories, context, update)
                    await query.message.edit_text(
                        get_message("category_main_select", context, update),
                        reply_markup=keyboard
                    )
                    context.user_data['category_group'] = None
            else:
                # برگشت به منوی اصلی دسته‌بندی‌ها
                keyboard = create_category_keyboard(categories, context, update)
                await query.message.edit_text(
                    get_message("category_main_select", context, update),
                    reply_markup=keyboard
                )
                context.user_data['category_group'] = None
            
            context.user_data['state'] = CATEGORY
            await query.answer()
            return CATEGORY

    except Exception as e:
        logger.error(f"Error in handle_category_selection: {e}", exc_info=True)
        sent = await query.message.reply_text(
            get_message("step_error", context, update),
            reply_markup=create_category_error_keyboard(context, update)
        )
        await delete_previous_messages(sent, context, n=3)
        return CATEGORY

    return CATEGORY

@require_phone
async def handle_category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    data = query.data
    context.user_data['category_id'] = int(data)
    project = {'category': context.user_data['category_id']}
    cat_name = context.user_data.get('categories', {}).get(project['category'], {}).get('name', 'نامشخص')
    
    msg = await query.edit_message_text(
        get_message("category_confirmation", context, update),
        reply_markup=create_category_confirmation_keyboard(cat_name, context, update)
    )
    await log_chat(update, context)
    return SUBMIT