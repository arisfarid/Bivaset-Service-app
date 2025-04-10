from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from utils import get_categories, log_chat
import logging
from handlers.start_handler import start
from keyboards import EMPLOYER_MENU_KEYBOARD, create_category_keyboard # اضافه شده برای بازگشت به منوی اصلی
from handlers.phone_handler import require_phone

logger = logging.getLogger(__name__)

START, REGISTER, ROLE, EMPLOYER_MENU, CATEGORY, SUBCATEGORY, DESCRIPTION, LOCATION_TYPE, LOCATION_INPUT, DETAILS, DETAILS_FILES, DETAILS_DATE, DETAILS_DEADLINE, DETAILS_BUDGET, DETAILS_QUANTITY, SUBMIT, VIEW_PROJECTS, PROJECT_ACTIONS = range(18)
CHANGE_PHONE, VERIFY_CODE = range(20, 22)  # states جدید

@require_phone
async def handle_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle category and subcategory selection recursively"""
    query = update.callback_query
    if not query:
        return CATEGORY

    try:
        data = query.data
        logger.info(f"Category selection data: {data}")

        if 'categories' not in context.user_data:
            categories = await get_categories()
            if not categories:
                await query.answer("❌ خطا در دریافت دسته‌بندی‌ها")
                return CATEGORY
            context.user_data['categories'] = categories
        
        categories = context.user_data['categories']

        # برگشت به منوی کارفرما
        if data == "back_to_menu":
            await query.message.edit_text(
                "🎉 عالیه! می‌خوای خدمات جدید درخواست کنی یا پیشنهادات رو ببینی؟",
                reply_markup=EMPLOYER_MENU_KEYBOARD
            )
            return EMPLOYER_MENU

        # پردازش انتخاب دسته‌بندی
        if data.startswith(("cat_", "subcat_")):
            category_id = data.split("_")[1]
            selected_category = categories.get(category_id)
            
            logger.info(f"Looking for category {category_id} in categories")
            logger.info(f"Selected category: {selected_category}")
            
            if not selected_category:
                await query.answer("❌ دسته‌بندی نامعتبر")
                return CATEGORY

            # بررسی وجود زیرمجموعه‌ها
            subcategories = []
            for cat_id, cat in categories.items():
                if cat.get('parent') == int(category_id):
                    subcategories.append(cat_id)
            
            logger.info(f"Found subcategories: {subcategories}")

            # اگر زیرمجموعه داشت
            if subcategories:
                context.user_data['current_category'] = category_id
                keyboard = []
                
                # ساخت دکمه‌های زیرمجموعه‌ها
                for sub_id in subcategories:
                    sub_cat = categories[sub_id]
                    keyboard.append([
                        InlineKeyboardButton(
                            sub_cat['name'], 
                            callback_data=f"subcat_{sub_id}"
                        )
                    ])
                
                keyboard.append([InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_categories")])
                
                await query.message.edit_text(
                    f"📋 زیرمجموعه {selected_category['name']} را انتخاب کنید:",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return SUBCATEGORY

            # اگر زیرمجموعه نداشت - انتخاب نهایی
            context.user_data['selected_category'] = category_id
            context.user_data['category_path'] = context.user_data.get('category_path', []) + [category_id]
            
            await query.message.edit_text(
                f"🌟 شما {selected_category['name']} را انتخاب کردید.\n"
                "لطفاً توضیحات خدمات مورد نیازتان را وارد کنید:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_categories")]
                ])
            )
            return DESCRIPTION

        # برگشت به لیست دسته‌بندی‌ها
        elif data == "back_to_categories":
            # برگشت به دسته‌بندی قبلی اگر در مسیر زیرمجموعه‌ها هستیم
            category_path = context.user_data.get('category_path', [])
            if category_path:
                category_path.pop()  # حذف آخرین دسته‌بندی
                if category_path:
                    # برگشت به دسته‌بندی قبلی
                    last_category = category_path[-1]
                    return await handle_category_selection(
                        update, 
                        context, 
                        data=f"cat_{last_category}"
                    )

            # برگشت به لیست اصلی دسته‌بندی‌ها
            keyboard = create_category_keyboard(categories)
            await query.message.edit_text(
                "🌟 دسته‌بندی خدماتت رو انتخاب کن:",
                reply_markup=keyboard
            )
            context.user_data['category_path'] = []
            return CATEGORY

    except Exception as e:
        logger.error(f"Error in handle_category_selection: {e}")
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