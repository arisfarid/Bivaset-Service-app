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
                keyboard.append([InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_categories")])
                await query.message.edit_text(
                    f"📋 زیرمجموعه {selected_category['name']} را انتخاب کنید:",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return SUBCATEGORY

            # اگر زیرمجموعه نداشت، رفتن به مرحله انتخاب نوع مکان
            context.user_data['category_id'] = category_id
            context.user_data['state'] = LOCATION_TYPE
            keyboard = [
                [InlineKeyboardButton("🏠 محل من", callback_data="location_client")],
                [InlineKeyboardButton("🔧 محل مجری", callback_data="location_contractor")],
                [InlineKeyboardButton("💻 غیرحضوری", callback_data="location_remote")],
                [InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_categories")]
            ]
            await query.message.edit_text(
                "🌟 محل انجام خدماتت رو انتخاب کن:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return LOCATION_TYPE

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
                keyboard.append([InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_categories")])
                await query.message.edit_text(
                    f"📋 زیرمجموعه {selected_subcategory['name']} را انتخاب کنید:",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return SUBCATEGORY

            # اگر زیرمجموعه نداشت، رفتن به مرحله انتخاب نوع مکان
            context.user_data['category_id'] = subcategory_id
            context.user_data['state'] = LOCATION_TYPE
            keyboard = [
                [InlineKeyboardButton("🏠 محل من", callback_data="location_client")],
                [InlineKeyboardButton("🔧 محل مجری", callback_data="location_contractor")],
                [InlineKeyboardButton("💻 غیرحضوری", callback_data="location_remote")],
                [InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_categories")]
            ]
            await query.message.edit_text(
                "🌟 محل انجام خدماتت رو انتخاب کن:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return LOCATION_TYPE

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
                    keyboard.append([InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_menu")])
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