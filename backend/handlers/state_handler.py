from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler, MessageHandler, CallbackQueryHandler, 
    ConversationHandler, filters, ContextTypes
)
import logging
from typing import Dict, List, Any, Optional, Tuple
from handlers.start_handler import start, handle_role, cancel, handle_confirm_restart
from handlers.phone_handler import handle_contact
from handlers.message_handler import handle_message
from handlers.category_handler import handle_category_selection
from handlers.location_handler import handle_location
from handlers.attachment_handler import handle_attachment, handle_photos_command
from handlers.project_details_handler import handle_project_details
from handlers.view_handler import handle_view_projects
from handlers.callback_handler import handle_callback
from keyboards import REGISTER_MENU_KEYBOARD

logger = logging.getLogger(__name__)

# Define conversation states for tracking
START, REGISTER, ROLE, EMPLOYER_MENU, CATEGORY, SUBCATEGORY, DESCRIPTION, \
LOCATION_TYPE, LOCATION_INPUT, DETAILS, DETAILS_FILES, DETAILS_DATE, \
DETAILS_DEADLINE, DETAILS_BUDGET, DETAILS_QUANTITY, SUBMIT, VIEW_PROJECTS, \
PROJECT_ACTIONS, CHANGE_PHONE, VERIFY_CODE = range(20)

# Define the standard service request flow for navigation purposes
SERVICE_REQUEST_FLOW = [
    CATEGORY, 
    SUBCATEGORY, 
    DESCRIPTION, 
    LOCATION_TYPE, 
    LOCATION_INPUT, 
    DETAILS, 
    DETAILS_FILES, 
    DETAILS_DATE, 
    DETAILS_DEADLINE, 
    DETAILS_BUDGET, 
    DETAILS_QUANTITY, 
    SUBMIT
]

# Map state numbers to readable names for logging
STATE_NAMES = {
    START: "شروع",
    REGISTER: "ثبت‌نام",
    ROLE: "انتخاب نقش",
    EMPLOYER_MENU: "منوی کارفرما",
    CATEGORY: "انتخاب دسته‌بندی",
    SUBCATEGORY: "انتخاب زیردسته",
    DESCRIPTION: "توضیحات",
    LOCATION_TYPE: "نوع موقعیت",
    LOCATION_INPUT: "ورود موقعیت",
    DETAILS: "جزئیات",
    DETAILS_FILES: "ارسال فایل",
    DETAILS_DATE: "تاریخ",
    DETAILS_DEADLINE: "مهلت",
    DETAILS_BUDGET: "بودجه",
    DETAILS_QUANTITY: "تعداد",
    SUBMIT: "ارسال درخواست",
    VIEW_PROJECTS: "مشاهده پروژه‌ها",
    PROJECT_ACTIONS: "عملیات پروژه",
    CHANGE_PHONE: "تغییر شماره تلفن",
    VERIFY_CODE: "تأیید کد"
}

from handlers.submission_handler import submit_project
from handlers.phone_handler import change_phone, handle_new_phone, verify_new_phone

def get_navigation_keyboard(current_state: int, user_data: Dict[str, Any]) -> Optional[InlineKeyboardMarkup]:
    """
    Creates a navigation keyboard with back/next buttons based on the current state in the flow
    """
    # Skip navigation for certain states
    if current_state in [START, REGISTER, ROLE, EMPLOYER_MENU, VIEW_PROJECTS, PROJECT_ACTIONS]:
        return None
        
    # Find position in the flow
    if current_state in SERVICE_REQUEST_FLOW:
        current_index = SERVICE_REQUEST_FLOW.index(current_state)
        
        # Create keyboard
        keyboard = []
        row = []
        
        # Back button (if not first state)
        if current_index > 0:
            prev_state = SERVICE_REQUEST_FLOW[current_index - 1]
            row.append(InlineKeyboardButton("« قبلی", callback_data=f"nav_to_{prev_state}"))
        
        # Add cancel button in the middle
        row.append(InlineKeyboardButton("❌ لغو", callback_data="cancel"))
        
        # Skip button (if form data already present for this state)
        if has_data_for_state(current_state, user_data) and current_index < len(SERVICE_REQUEST_FLOW) - 1:
            next_state = SERVICE_REQUEST_FLOW[current_index + 1]
            row.append(InlineKeyboardButton("رد کردن »", callback_data=f"nav_to_{next_state}"))
        
        keyboard.append(row)
        return InlineKeyboardMarkup(keyboard)
    
    return None

# Add this function to ensure consistent navigation keyboards across all handlers
def get_universal_navigation_keyboard(context, additional_buttons=None):
    """
    Creates a universal navigation keyboard that can be used across all handlers
    
    Parameters:
    - context: The conversation context
    - additional_buttons: Optional list of additional InlineKeyboardButton rows to add
    
    Returns:
    - InlineKeyboardMarkup with navigation buttons
    """
    current_state = context.user_data.get('state')
    previous_state = context.user_data.get('previous_state')
    keyboard = []
    
    # Navigation row with back button
    nav_row = []
    if previous_state is not None:
        nav_row.append(InlineKeyboardButton("◀️ قبلی", callback_data="navigate_back"))
    
    # Add next button if in the service request flow and not at the end
    if current_state in SERVICE_REQUEST_FLOW:
        current_index = SERVICE_REQUEST_FLOW.index(current_state)
        if current_index < len(SERVICE_REQUEST_FLOW) - 1:
            nav_row.append(InlineKeyboardButton("بعدی ▶️", callback_data="navigate_next"))
    
    # Add navigation row if it has buttons
    if nav_row:
        keyboard.append(nav_row)
    
    # Add any additional buttons
    if additional_buttons:
        keyboard.extend(additional_buttons)
    
    # Always add a way to get back to the main menu
    keyboard.append([InlineKeyboardButton("🏠 منوی اصلی", callback_data="back_to_employer_menu")])
    
    return InlineKeyboardMarkup(keyboard)

def has_data_for_state(state: int, user_data: Dict[str, Any]) -> bool:
    """
    Checks if the user already has data for the given state
    """
    if state == CATEGORY:
        return 'category_id' in user_data
    elif state == SUBCATEGORY:
        return 'subcategory_id' in user_data
    elif state == DESCRIPTION:
        return 'description' in user_data
    elif state == LOCATION_TYPE:
        return 'location_type' in user_data
    elif state == LOCATION_INPUT:
        return 'location' in user_data or 'address' in user_data
    elif state == DETAILS_FILES:
        return 'photos' in user_data
    elif state == DETAILS_DATE:
        return 'date' in user_data
    elif state == DETAILS_DEADLINE:
        return 'deadline' in user_data
    elif state == DETAILS_BUDGET:
        return 'budget' in user_data
    elif state == DETAILS_QUANTITY:
        return 'quantity' in user_data
    
    return False

async def handle_navigation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles navigation callbacks (back/next/skip)
    """
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    if callback_data.startswith("nav_to_"):
        try:
            next_state = int(callback_data.split("_")[-1])
            
            # Update user state
            context.user_data['previous_state'] = context.user_data.get('state')
            context.user_data['state'] = next_state
            logger.info(f"User {update.effective_user.id} navigated to state {next_state} ({STATE_NAMES.get(next_state, 'Unknown')})")
            
            # Handle navigation to specific states
            if next_state == CATEGORY:
                from handlers.category_handler import show_category_selection
                return await show_category_selection(update, context)
                
            elif next_state == SUBCATEGORY:
                from handlers.category_handler import show_subcategory_selection
                return await show_subcategory_selection(update, context)
                
            elif next_state == DESCRIPTION:
                from handlers.project_details_handler import send_description_guidance
                await send_description_guidance(query.message, context)
                return DESCRIPTION
                
            elif next_state == LOCATION_TYPE:
                from handlers.location_handler import show_location_type_selection
                return await show_location_type_selection(update, context)
                
            elif next_state == LOCATION_INPUT:
                from handlers.location_handler import request_location_input
                return await request_location_input(update, context)
                
            elif next_state == DETAILS:
                from helpers.menu_manager import MenuManager
                from keyboards import create_dynamic_keyboard
                await MenuManager.show_menu(
                    update,
                    context,
                    "📋 جزئیات درخواست:\nاگه بخوای می‌تونی برای راهنمایی بهتر مجری‌ها این اطلاعات رو هم وارد کنی:",
                    create_dynamic_keyboard(context)
                )
                return DETAILS
                
            elif next_state == DETAILS_FILES:
                from handlers.attachment_handler import show_file_upload
                return await show_file_upload(update, context)
                
            elif next_state == DETAILS_DATE:
                from helpers.menu_manager import MenuManager
                await MenuManager.show_menu(
                    update,
                    context,
                    "📅 تاریخ نیاز خود را به صورت 'ماه/روز' وارد کنید (مثال: 05/15):",
                    InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_details")]])
                )
                return DETAILS_DATE
                
            elif next_state == DETAILS_DEADLINE:
                from helpers.menu_manager import MenuManager
                await MenuManager.show_menu(
                    update,
                    context,
                    "⏳ مهلت انجام خدمات را به صورت 'ماه/روز' وارد کنید (مثال: 06/20):",
                    InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_details")]])
                )
                return DETAILS_DEADLINE
                
            elif next_state == DETAILS_BUDGET:
                from helpers.menu_manager import MenuManager
                await MenuManager.show_menu(
                    update,
                    context,
                    "💰 بودجه مورد نظر خود را به تومان وارد کنید (فقط عدد):",
                    InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_details")]])
                )
                return DETAILS_BUDGET
                
            elif next_state == DETAILS_QUANTITY:
                from helpers.menu_manager import MenuManager
                await MenuManager.show_menu(
                    update,
                    context,
                    "📏 مقدار و واحد مورد نظر را وارد کنید (مثال: 5 متر، 2 عدد):",
                    InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_details")]])
                )
                return DETAILS_QUANTITY
                
            elif next_state == SUBMIT:
                from handlers.submission_handler import submit_project
                return await submit_project(update, context)
                
            # Default: just return the next state
            return next_state
            
        except (ValueError, IndexError) as e:
            logger.error(f"Error processing navigation callback: {e}")
    
    # Default: stay in current state
    return context.user_data.get('state', ROLE)

def add_navigation_to_message(text: str, current_state: int, user_data: Dict[str, Any]) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """
    Adds navigation info to a message and returns updated text and keyboard
    """
    keyboard = get_navigation_keyboard(current_state, user_data)
    
    # Add progress indicator for certain flows
    if current_state in SERVICE_REQUEST_FLOW:
        current_index = SERVICE_REQUEST_FLOW.index(current_state)
        total_steps = len(SERVICE_REQUEST_FLOW)
        progress = f"\n\n📊 مرحله {current_index + 1} از {total_steps}"
        
        # Add ability to go back info if applicable
        if current_index > 0:
            progress += " | می‌توانید از دکمه «قبلی» برای بازگشت استفاده کنید"
            
        text += progress
    
    return text, keyboard

async def handle_non_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"=== Entering handle_non_contact - User: {update.effective_user.id} ===")
    logger.info(f"Message type: {type(update.message)}")
    logger.info(f"Message text: {update.message.text if update.message else 'None'}")
    logger.info(f"Current state: {context.user_data.get('state')}")
    logger.info("=== Non-contact message received in REGISTER state ===")
    current_state = context.user_data.get('state')
    logger.info(f"Current state: {current_state}")
    
    if current_state != REGISTER:
        return current_state
        
    message = update.callback_query.message if update.callback_query else update.message
    if not message:
        logger.error("No message object found in update")
        return REGISTER
        
    logger.info(f"User {update.effective_user.id} sent non-contact message in REGISTER state")
    await message.reply_text(
        "⚠️ برای استفاده از ربات، باید شماره تلفن خود را به اشتراک بگذارید.\n"
        "لطفاً از دکمه زیر استفاده کنید:",
        reply_markup=REGISTER_MENU_KEYBOARD
    )
    context.user_data['state'] = REGISTER
    return REGISTER

def get_conversation_handler() -> ConversationHandler:
    """ایجاد مدیریت کننده مکالمه با بهینه‌سازی جریان گفتگو"""
    logger.info("=== Initializing ConversationHandler ===")
    
    # هندلر دکمه‌های تأیید/رد شروع مجدد
    restart_handler = CallbackQueryHandler(handle_confirm_restart, pattern="^(confirm_restart|continue_current)$")
    
    # هندلر برای ناوبری در مراحل مختلف (قبلی/بعدی/رد کردن)
    navigation_handler = CallbackQueryHandler(handle_navigation_callback, pattern="^nav_to_[0-9]+$")
    
    # هندلر برای لغو گفتگو
    cancel_callback_handler = CallbackQueryHandler(cancel, pattern="^cancel$")
    
    return ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            REGISTER: [
                MessageHandler(filters.CONTACT, handle_contact),
                MessageHandler(~filters.CONTACT & ~filters.COMMAND, handle_non_contact),
                CommandHandler("start", start),
                restart_handler,
                navigation_handler,
                cancel_callback_handler,
                CallbackQueryHandler(handle_callback)
            ],
            ROLE: [
                MessageHandler(filters.TEXT, handle_role),
                restart_handler,
                navigation_handler,
                cancel_callback_handler,
                CallbackQueryHandler(handle_callback)
            ],
            EMPLOYER_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message),
                restart_handler,
                navigation_handler,
                cancel_callback_handler,
                CallbackQueryHandler(handle_callback)
            ],
            CATEGORY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_category_selection),
                restart_handler,
                navigation_handler,
                cancel_callback_handler,
                CallbackQueryHandler(handle_category_selection)
            ],
            SUBCATEGORY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_category_selection),
                restart_handler,
                navigation_handler,
                cancel_callback_handler,
                CallbackQueryHandler(handle_category_selection)
            ],
            LOCATION_TYPE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_location),
                restart_handler,
                navigation_handler,
                cancel_callback_handler,
                CallbackQueryHandler(handle_location)
            ],
            LOCATION_INPUT: [
                MessageHandler(filters.LOCATION, handle_location),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_location),
                restart_handler,
                navigation_handler,
                cancel_callback_handler,
                CallbackQueryHandler(handle_location)
            ],
            DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_project_details),
                restart_handler,
                navigation_handler,
                cancel_callback_handler,
                CallbackQueryHandler(handle_project_details)
            ],
            DETAILS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_project_details),
                restart_handler,
                navigation_handler,
                cancel_callback_handler,
                CallbackQueryHandler(handle_project_details)
            ],
            DETAILS_FILES: [
                MessageHandler(filters.PHOTO, handle_attachment),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_attachment),
                restart_handler,
                navigation_handler,
                cancel_callback_handler,
                CallbackQueryHandler(handle_attachment)
            ],
            # اضافه کردن هندلرهای مربوط به جزئیات درخواست
            DETAILS_DATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_project_details),
                restart_handler,
                navigation_handler,
                cancel_callback_handler,
                CallbackQueryHandler(handle_project_details)
            ],
            DETAILS_DEADLINE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_project_details),
                restart_handler,
                navigation_handler,
                cancel_callback_handler,
                CallbackQueryHandler(handle_project_details)
            ],
            DETAILS_BUDGET: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_project_details),
                restart_handler,
                navigation_handler,
                cancel_callback_handler,
                CallbackQueryHandler(handle_project_details)
            ],
            DETAILS_QUANTITY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_project_details),
                restart_handler,
                navigation_handler,
                cancel_callback_handler,
                CallbackQueryHandler(handle_project_details)
            ],
            SUBMIT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, submit_project),
                restart_handler,
                navigation_handler,
                cancel_callback_handler,
                CallbackQueryHandler(submit_project)
            ],
            CHANGE_PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_phone),
                restart_handler,
                navigation_handler,
                cancel_callback_handler
            ],
            VERIFY_CODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, verify_new_phone),
                restart_handler,
                navigation_handler,
                cancel_callback_handler
            ],
            VIEW_PROJECTS: [
                restart_handler,
                navigation_handler,
                cancel_callback_handler,
                CallbackQueryHandler(handle_view_projects)
            ],
            PROJECT_ACTIONS: [
                restart_handler,
                navigation_handler,
                cancel_callback_handler,
                CallbackQueryHandler(handle_view_projects)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(filters.ALL, handle_non_contact)
        ],
        name="main_conversation",
        persistent=True,
        allow_reentry=True
    )

async def log_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لاگ کردن state فعلی"""
    current_state = context.user_data.get('state', START)
    logger.info(f"Processing message for user {update.effective_user.id}, current state: {current_state}")
    return current_state

async def handle_error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """مدیریت خطاهای کلی"""
    logger.error(f"Exception while handling an update: {context.error}")
    
    try:
        if context and context.user_data:
            context.user_data.clear()
            if update.effective_user:
                await context.application.persistence.update_user_data(
                    user_id=update.effective_user.id, 
                    data=context.user_data
                )
        
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ خطایی رخ داد. لطفاً دوباره شروع کنید با /start"
            )
            
    except Exception as e:
        logger.error(f"Error in error handler: {e}")