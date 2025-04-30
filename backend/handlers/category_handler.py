from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from utils import get_categories, log_chat, delete_message_later
import logging
from handlers.start_handler import start
from keyboards import EMPLOYER_MENU_KEYBOARD, MAIN_MENU_KEYBOARD, create_category_keyboard
from handlers.phone_handler import require_phone
from handlers.location_handler import handle_location
import asyncio

logger = logging.getLogger(__name__)

START, REGISTER, ROLE, EMPLOYER_MENU, CATEGORY, SUBCATEGORY, DESCRIPTION, LOCATION_TYPE, LOCATION_INPUT, DETAILS, DETAILS_FILES, DETAILS_DATE, DETAILS_DEADLINE, DETAILS_BUDGET, DETAILS_QUANTITY, SUBMIT, VIEW_PROJECTS, PROJECT_ACTIONS = range(18)
CHANGE_PHONE, VERIFY_CODE = range(20, 22)  # states جدید

@require_phone
async def handle_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle category and subcategory selection"""
    query = update.callback_query
    message = update.message
    from localization import get_message
    lang = context.user_data.get('lang', 'fa')
    if not query:
        # اگر کاربر پیام غیرمجاز (متن، عکس و ...) ارسال کرد
        await message.reply_text(
            get_message("only_select_from_buttons", lang=lang),
            reply_markup=ReplyKeyboardRemove()
        )
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
            await query.message.edit_text(
                "🎉 عالیه! چه کاری برات انجام بدم؟",
                reply_markup=EMPLOYER_MENU_KEYBOARD
            )
            return EMPLOYER_MENU

        # رفتن به مرحله بعد (انتخاب لوکیشن)
        if data == "continue_to_location":
            logger.info(f"Processing continue to location. Category ID: {context.user_data.get('category_id')}")
            if context.user_data.get('category_id'):
                context.user_data['state'] = LOCATION_TYPE
                await query.answer()  # پاسخ به callback
                return await handle_location(update, context)
            else:
                logger.warning("Cannot proceed to location: No category selected")
                await query.answer("❌ لطفاً ابتدا یک دسته‌بندی انتخاب کنید.")
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
                await query.answer("❌ دسته‌بندی نامعتبر")
                return CATEGORY

            children = selected_category.get('children', [])
            if children:
                context.user_data['category_group'] = category_id
                keyboard = []
                for child_id in children:
                    child = categories.get(child_id)
                    if child:
                        keyboard.append([
                            InlineKeyboardButton(
                                child['name'],
                                callback_data=f"subcat_{child_id}"
                            )
                        ])
                # استفاده از لوکالایزیشن برای دکمه بازگشت
                keyboard.append([InlineKeyboardButton(get_message("back", lang=lang), callback_data="back_to_categories")])
                await query.message.edit_text(
                    f"📋 زیرمجموعه {selected_category['name']} را انتخاب کنید:",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return SUBCATEGORY

            # اگر زیرمجموعه نداشت، ذخیره دسته بندی و ادامه به مرحله بعدی
            context.user_data['category_id'] = category_id
            context.user_data['category_name'] = selected_category['name']
            
            # نمایش پیام تایید با دکمه‌های بازگشت و ادامه
            from keyboards import create_navigation_keyboard
            await query.message.edit_text(
                f"✅ دسته‌بندی «{selected_category['name']}» انتخاب شد.\n\n"
                "می‌توانید به مرحله بعدی (انتخاب محل خدمات) بروید یا برای تغییر دسته‌بندی به مرحله قبل بازگردید.",
                reply_markup=create_navigation_keyboard(
                    back_callback="back_to_categories", 
                    continue_callback="continue_to_location", 
                    continue_enabled=True
                )
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
                await query.answer("❌ زیردسته نامعتبر")
                return SUBCATEGORY

            children = selected_subcategory.get('children', [])
            if children:
                context.user_data['category_group'] = subcategory_id
                keyboard = []
                for child_id in children:
                    child = categories.get(child_id)
                    if child:
                        keyboard.append([
                            InlineKeyboardButton(
                                child['name'],
                                callback_data=f"subcat_{child_id}"
                            )
                        ])
                keyboard.append([InlineKeyboardButton(get_message("back", lang=lang), callback_data="back_to_categories")])
                await query.message.edit_text(
                    f"📋 زیرمجموعه {selected_subcategory['name']} را انتخاب کنید:",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return SUBCATEGORY

            # اگر زیرمجموعه نداشت، ذخیره دسته بندی و ادامه به مرحله بعدی
            context.user_data['category_id'] = subcategory_id
            context.user_data['category_name'] = selected_subcategory['name']
            
            # نمایش پیام تایید با دکمه‌های بازگشت و ادامه
            from keyboards import create_navigation_keyboard
            await query.message.edit_text(
                f"✅ دسته‌بندی «{selected_subcategory['name']}» انتخاب شد.\n\n"
                "می‌توانید به مرحله بعدی (انتخاب محل خدمات) بروید یا برای تغییر دسته‌بندی به مرحله قبل بازگردید.",
                reply_markup=create_navigation_keyboard(
                    back_callback="back_to_categories", 
                    continue_callback="continue_to_location", 
                    continue_enabled=True
                )
            )
            return CATEGORY

        # برگشت به لیست دسته‌بندی‌ها
        elif data == "back_to_categories":
            categories = context.user_data.get('categories', {})
            category_group = context.user_data.get('category_group')
            if category_group and categories.get(category_group):
                parent = categories[category_group]
                parent_id = parent.get('parent')
                
                if parent_id is not None:
                    # اگر والد وجود دارد، به منوی آن برمی‌گردیم
                    grandparent = categories.get(parent_id)
                    keyboard = []
                    for child_id in grandparent.get('children', []):
                        child = categories.get(child_id)
                        if child:
                            keyboard.append([
                                InlineKeyboardButton(
                                    child['name'],
                                    callback_data=f"subcat_{child_id}"
                                )
                            ])
                    keyboard.append([InlineKeyboardButton(get_message("back", lang=lang), callback_data="back_to_menu")])
                    context.user_data['category_group'] = parent_id
                    await query.message.edit_text(
                        f"📋 زیرمجموعه {grandparent['name']} را انتخاب کنید:",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                else:
                    # اگر در بالاترین سطح هستیم، به منوی اصلی دسته‌بندی‌ها برمی‌گردیم
                    keyboard = create_category_keyboard(categories)
                    await query.message.edit_text(
                        get_message("category_main_select", lang=lang),
                        reply_markup=keyboard
                    )
                    context.user_data['category_group'] = None
            else:
                # برگشت به منوی اصلی دسته‌بندی‌ها
                keyboard = create_category_keyboard(categories)
                await query.message.edit_text(
                    get_message("category_main_select", lang=lang),
                    reply_markup=keyboard
                )
                context.user_data['category_group'] = None
            
            context.user_data['state'] = CATEGORY
            await query.answer()
            return CATEGORY

    except Exception as e:
        logger.error(f"Error in handle_category_selection: {e}", exc_info=True)
        await query.message.reply_text("❌ خطا در انتخاب دسته‌بندی. لطفاً دوباره تلاش کنید.")
        return CATEGORY

    return CATEGORY

@require_phone
async def handle_category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    data = query.data
    context.user_data['category_id'] = int(data)
    project = {'category': context.user_data['category_id']}
    cat_name = context.user_data.get('categories', {}).get(project['category'], {}).get('name', 'نامشخص')
    from localization import get_message
    lang = context.user_data.get('lang', 'fa')
    keyboard = [
        [InlineKeyboardButton(get_message("submit", lang=lang), callback_data="submit_project")],
        [InlineKeyboardButton(get_message("back", lang=lang), callback_data="back_to_categories")]
    ]
    msg = await query.edit_message_text(
        f"{get_message('category_selected', lang=lang)}: {cat_name}\n{get_message('category_submit_or_back', lang=lang)}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    asyncio.create_task(delete_message_later(context.bot, msg.chat_id, msg.message_id))
    await log_chat(update, context)
    return SUBMIT