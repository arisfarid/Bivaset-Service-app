from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from utils import get_categories, log_chat
import logging
from handlers.start_handler import start
from keyboards import EMPLOYER_MENU_KEYBOARD,MAIN_MENU_KEYBOARD, create_category_keyboard # اضافه شده برای بازگشت به منوی اصلی
from handlers.phone_handler import require_phone

logger = logging.getLogger(__name__)

START, REGISTER, ROLE, EMPLOYER_MENU, CATEGORY, SUBCATEGORY, DESCRIPTION, LOCATION_TYPE, LOCATION_INPUT, DETAILS, DETAILS_FILES, DETAILS_DATE, DETAILS_DEADLINE, DETAILS_BUDGET, DETAILS_QUANTITY, SUBMIT, VIEW_PROJECTS, PROJECT_ACTIONS = range(18)
CHANGE_PHONE, VERIFY_CODE = range(20, 22)  # states جدید

@require_phone
async def handle_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle category and subcategory selection"""
    query = update.callback_query
    if not query:
        return CATEGORY

    try:
        data = query.data
        current_state = context.user_data.get('state', CATEGORY)
        logger.info(f"Category selection data: {data}")
        logger.info(f"Current state: {current_state}")
        logger.info(f"Current context data: {context.user_data}")

        # پردازش دکمه بازگشت به منوی کارفرما
        if data == "back_to_menu":
            logger.info("Returning to employer menu")
            context.user_data['state'] = EMPLOYER_MENU
            await query.message.edit_text(
                "🎉 عالیه! چه کاری برات انجام بدم؟",
                reply_markup=EMPLOYER_MENU_KEYBOARD
            )
            return EMPLOYER_MENU

        # پردازش انتخاب دسته‌بندی
        if data.startswith("cat_"):
            category_id = int(data.split("_")[1])
            logger.info(f"Selected main category: {category_id}")
            
            # دریافت مجدد دسته‌بندی‌ها برای اطمینان از به‌روز بودن
            categories = context.user_data.get('categories')
            if not categories:
                categories = await get_categories()
                if not categories:
                    logger.error("Failed to fetch categories")
                    await query.answer("❌ خطا در دریافت دسته‌بندی‌ها")
                    return CATEGORY

            context.user_data['categories'] = categories
            selected_category = categories.get(category_id)

            logger.info(f"Selected category data: {selected_category}")
            if not selected_category:
                await query.answer("❌ دسته‌بندی نامعتبر")
                return CATEGORY

            # بررسی زیرمجموعه‌ها
            children = selected_category.get('children', [])
            logger.info(f"Children for category {category_id}: {children}")

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
                
                keyboard.append([InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_categories")])
                
                await query.message.edit_text(
                    f"📋 زیرمجموعه {selected_category['name']} را انتخاب کنید:",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                context.user_data['state'] = SUBCATEGORY
                return SUBCATEGORY

            # اگر زیرمجموعه نداشت
            context.user_data['category_id'] = category_id
            context.user_data['state'] = DESCRIPTION
            await query.message.edit_text(
                "🌟 توضیحات خدماتت رو بگو:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_categories")]
                ])
            )
            return DESCRIPTION

        # پردازش انتخاب زیرمجموعه
        elif data.startswith("subcat_"):
            subcategory_id = int(data.split("_")[1])
            logger.info(f"Selected subcategory: {subcategory_id}")
            categories = context.user_data.get('categories')
            
            if not categories:
                categories = await get_categories()
                context.user_data['categories'] = categories

            selected_subcategory = categories.get(subcategory_id)
            logger.info(f"Selected subcategory data: {selected_subcategory}")

            if not selected_subcategory:
                await query.answer("❌ زیردسته نامعتبر")
                return SUBCATEGORY

            # بررسی وجود زیرمجموعه‌های بیشتر
            children = selected_subcategory.get('children', [])
            logger.info(f"Children for subcategory {subcategory_id}: {children}")

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
                keyboard.append([InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_categories")])
                
                await query.message.edit_text(
                    f"📋 زیرمجموعه {selected_subcategory['name']} را انتخاب کنید:",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                context.user_data['state'] = SUBCATEGORY
                return SUBCATEGORY

            # اگر زیرمجموعه نداشت
            context.user_data['category_id'] = subcategory_id
            context.user_data['state'] = DESCRIPTION
            await query.message.edit_text(
                f"🌟 شما {selected_subcategory['name']} را انتخاب کردید.\n"
                "لطفاً توضیحات خدمات مورد نیازتان را وارد کنید:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_categories")]
                ])
            )
            return DESCRIPTION

        # برگشت به لیست دسته‌بندی‌ها
        elif data == "back_to_categories":
            logger.info("Processing back to categories")
            categories = context.user_data.get('categories', {})
            current_state = context.user_data.get('state')
            category_group = context.user_data.get('category_group')
            
            logger.info(f"Back navigation - State: {current_state}, Category group: {category_group}")

            if category_group and categories.get(category_group):
                # برگشت به دسته‌بندی والد
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
                    keyboard.append([InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_categories")])
                    context.user_data['category_group'] = parent_id
                    await query.message.edit_text(
                        f"📋 زیرمجموعه {grandparent['name']} را انتخاب کنید:",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                else:
                    # اگر در بالاترین سطح هستیم، به منوی اصلی دسته‌بندی‌ها برمی‌گردیم
                    keyboard = create_category_keyboard(categories)
                    await query.message.edit_text(
                        "🌟 دسته‌بندی خدماتت رو انتخاب کن:",
                        reply_markup=keyboard
                    )
                    context.user_data['category_group'] = None
            else:
                # برگشت به منوی اصلی دسته‌بندی‌ها
                keyboard = create_category_keyboard(categories)
                await query.message.edit_text(
                    "🌟 دسته‌بندی خدماتت رو انتخاب کن:",
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
    keyboard = [
        [InlineKeyboardButton("✅ ثبت", callback_data="submit_project")],
        [InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_categories")]
    ]
    await query.edit_message_text(
        f"دسته‌بندی انتخاب‌شده: {cat_name}\nحالا می‌تونی ثبت کنی یا برگردی:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    await log_chat(update, context)
    return SUBMIT