from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from utils import BASE_URL, log_chat, ensure_active_chat, delete_previous_messages
from keyboards import get_main_menu_keyboard, get_register_menu_keyboard, get_employer_menu_keyboard, get_contractor_menu_keyboard, create_dynamic_keyboard, create_category_keyboard
from handlers.phone_handler import check_phone
from helpers.menu_manager import MenuManager
from handlers.states import START, REGISTER, ROLE, EMPLOYER_MENU, CATEGORY, SUBCATEGORY, DESCRIPTION, LOCATION_TYPE, LOCATION_INPUT, DETAILS, DETAILS_FILES, DETAILS_DATE, DETAILS_DEADLINE, DETAILS_BUDGET, DETAILS_QUANTITY, SUBMIT, VIEW_PROJECTS, PROJECT_ACTIONS, CHANGE_PHONE, VERIFY_CODE, CONTRACTOR_MENU
import logging
from localization import get_message

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation with the bot."""
    logger.info(f"=== Entering start function - User: {update.effective_user.id} ===")
    logger.info(f"Current context state: {context.user_data.get('state')}")
    
    # بررسی وضعیت فعلی
    current_state = context.user_data.get('state')
    
    # اگر کاربر در وسط یک فرآیند است (به جز حالت‌های اولیه)
    # اما اگر درخواست restart داشته باشیم، فرآیند را مجدد شروع می‌کنیم
    is_restart = False
    args = context.args
    if args and args[0] == "restart":
        is_restart = True
        logger.info(f"Restart command detected via URL for user {update.effective_user.id}")
    
    if not is_restart and current_state not in [None, START, REGISTER, ROLE]:
        # پاک کردن منوهای قبلی و غیرفعال کردن آنها
        await MenuManager.disable_previous_menus(update, context)
        
        # ارسال پیام هشدار با لوکالایزیشن
        text = get_message("process_active_prompt", context, update)
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(get_message("restart_yes", context, update), callback_data="confirm_restart")],
            [InlineKeyboardButton(get_message("restart_no", context, update), callback_data="continue_current")]
        ])
        await update.message.reply_text(text, reply_markup=keyboard)
        return current_state
    
    # اگر این یک restart است یا در مرحله اولیه هستیم
    await ensure_active_chat(update, context)
    
    # اگر این یک restart است، پیام‌های قبلی را پاک کن
    if is_restart:
        try:
            # با استفاده از متد جدید، پاک کردن پیام‌های قبلی
            await MenuManager.clear_chat_history(update, context)
            logger.info(f"Cleared chat history for user {update.effective_user.id} during restart")
        except Exception as e:
            logger.error(f"Error cleaning chat history during restart: {e}")
    else:
        # پاک کردن تمام منوهای قبلی
        await MenuManager.clear_menus(update, context)
    
    message = update.callback_query.message if update.callback_query else update.message
    if not message:
        logger.error("No message object found in update")
        return REGISTER

    # بررسی وجود شماره تلفن
    has_phone = await check_phone(update, context)
    
    # پاک کردن context کاربر در هنگام راه‌اندازی مجدد یا شروع جدید
    if is_restart:
        context.user_data.clear()
        context.user_data['state'] = REGISTER
    
    if (has_phone):
        # اگر شماره داشت، نمایش منوی اصلی
        context.user_data['state'] = ROLE
        welcome_message = get_message("welcome", context, update)
        # حذف کیبورد تایپ قبل از نمایش منو
        sent = await update.message.reply_text(
            get_message("select_from_buttons", context, update),
            reply_markup=ReplyKeyboardRemove()
        )
        await delete_previous_messages(sent, context, n=3)
        # استفاده از MenuManager برای نمایش منو
        await MenuManager.show_menu(
            update,
            context,
            welcome_message,
            get_main_menu_keyboard(context, update)
        )
        return ROLE
    else:
        # اگر شماره نداشت، درخواست ثبت شماره
        sent = await message.reply_text(
            get_message("share_phone_prompt", context, update),
            reply_markup=get_register_menu_keyboard(context, update)
        )
        await delete_previous_messages(sent, context, n=3)
        return REGISTER

async def handle_confirm_restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle restart confirmation"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "confirm_restart":
        # پاک کردن وضعیت قبلی
        context.user_data.clear()
        await query.message.delete()
        
        try:
            # پاک کردن تاریخچه چت با استفاده از متد جدید
            await MenuManager.clear_chat_history(update, context)
            logger.info(f"Cleared chat history for user {update.effective_user.id} during confirmed restart")
        except Exception as e:
            logger.error(f"Error cleaning chat history during confirmed restart: {e}")
            # در صورت خطا، از روش قبلی استفاده کنیم
            await MenuManager.clear_menus(update, context)
        
        # نمایش منوی اصلی
        welcome_message = get_message("welcome", context, update)
        
        # استفاده از MenuManager برای نمایش منو
        await MenuManager.show_menu(
            update, 
            context, 
            welcome_message,
            get_main_menu_keyboard(context, update)
        )
        
        context.user_data['state'] = ROLE
        return ROLE
        
    elif query.data == "continue_current":
        # ادامه فرآیند فعلی
        await query.message.delete()
        
        # بازگشت به وضعیت فعلی
        return context.user_data.get('state')

async def handle_role(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle role selection."""
    logger.info(f"=== Entering handle_role - User: {update.effective_user.id} ===")
    logger.info(f"Message text: {update.message.text if update.message else 'None'}")
    logger.info(f"Current state: {context.user_data.get('state')}")
    text = update.message.text if update.message else None
    
    if text == get_message("role_employer", context, update):
        context.user_data['state'] = EMPLOYER_MENU
        
        # پاک کردن تاریخچه چت با استفاده از متد جدید
        try:
            await MenuManager.clear_chat_history(update, context, message_count=15)  # تعداد کمتری پیام را پاک می‌کنیم
            logger.info(f"Cleared partial chat history for user {update.effective_user.id} during role change")
        except Exception as e:
            logger.error(f"Error cleaning chat history during role change: {e}")
            # در صورت خطا، از روش قبلی استفاده کنیم
            await MenuManager.clear_menus(update, context)
        
        employer_message = get_message("employer_menu_prompt", context, update)
        
        # حذف کیبورد تایپ قبل از نمایش منو
        sent = await update.message.reply_text(
            get_message("select_from_buttons", context, update),
            reply_markup=ReplyKeyboardRemove()
        )
        await delete_previous_messages(sent, context, n=3)
        # استفاده از MenuManager برای نمایش منو
        await MenuManager.show_menu(
            update, 
            context, 
            employer_message,
            get_employer_menu_keyboard(context, update)
        )
        return EMPLOYER_MENU
    elif text == get_message("role_contractor", context, update):
        # مشابه حالت کارفرما برای پیمانکار
        context.user_data['state'] = CONTRACTOR_MENU
        # نمایش منوی مجری
        sent2 = await update.message.reply_text(
            get_message("select_from_buttons", context, update),
            reply_markup=ReplyKeyboardRemove()
        )
        await delete_previous_messages(sent2, context, n=3)
        await MenuManager.show_menu(
            update,
            context,
            get_message("contractor_menu_prompt", context, update),
            get_contractor_menu_keyboard(context, update)
        )
        return CONTRACTOR_MENU
    
    # اگر پیام غیرمجاز ارسال شد
    sent = await update.message.reply_text(
        get_message("only_select_from_buttons", context, update),
        reply_markup=ReplyKeyboardRemove()
    )
    await delete_previous_messages(sent, context, n=3)
    # نمایش مجدد منوی نقش
    sent2 = await update.message.reply_text(
        get_message("role_select", context, update),
        reply_markup=get_main_menu_keyboard(context, update)
    )
    await delete_previous_messages(sent2, context, n=3)
    return ROLE

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle cancel with confirmation dialog"""
    logger.info(f"=== Cancel function called ===")
    logger.info(f"Update type: {'callback_query' if update.callback_query else 'message'}")
    
    query = update.callback_query
    
    if query:
        logger.info(f"Callback query data: {query.data}")
        await query.answer()
          # Check if this is a cancel confirmation response
        if query.data == "cancel_confirmed":
            logger.info("User confirmed cancellation - clearing data and ending conversation")
              # Store all messages before clearing context
            cancellation_message = get_message("operation_cancelled", context, update)
            back_to_main_text = get_message("back_to_main_menu", context, update)
            start_new_request_text = get_message("start_new_request", context, update)
            logger.info(f"Got cancellation message: {cancellation_message}")
            
            # پاک کردن تاریخچه چت با استفاده از متد جدید
            try:
                await MenuManager.clear_chat_history(update, context)
                logger.info(f"Cleared chat history for user {update.effective_user.id} during cancel")
            except Exception as e:
                logger.error(f"Error cleaning chat history during cancel: {e}")
                # در صورت خطا، از روش قبلی استفاده کنیم
                try:
                    await MenuManager.clear_menus(update, context)
                    logger.info("Fallback: cleared menus successfully")
                except Exception as e2:
                    logger.error(f"Error in fallback clear_menus: {e2}")
                    
            # Clear user data after getting the messages
            context.user_data.clear()
            logger.info("Cleared user data")
            
            # Create restart keyboard using pre-stored messages
            restart_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(back_to_main_text, callback_data="restart_to_main")],
                [InlineKeyboardButton(start_new_request_text, callback_data="restart_to_new_request")]
            ])
            
            # Edit message with the stored cancellation message and restart options
            try:
                await query.edit_message_text(
                    cancellation_message, 
                    reply_markup=restart_keyboard
                )
                logger.info("Successfully edited message with cancellation text and restart buttons")
            except Exception as e:
                logger.error(f"Error editing message with cancellation: {e}")
                # Fallback: try to send a new message
                try:
                    await query.message.reply_text(
                        cancellation_message,
                        reply_markup=restart_keyboard
                    )
                    logger.info("Fallback: sent new message with cancellation text and restart buttons")
                except Exception as e2:
                    logger.error(f"Error in fallback message send: {e2}")
            
            logger.info("Successfully cancelled and ended conversation")
            return ConversationHandler.END
        
        elif query.data == "cancel_declined":
            logger.info("User declined cancellation - returning to current state")
            # Get current state and redirect back
            current_state = context.user_data.get('state', START)
            logger.info(f"Current state: {current_state}")
            logger.info(f"User data: {context.user_data}")
            
            # بجای نمایش پیام ساده، باید کاربر را به state مناسب برگردانیم
            if current_state == DESCRIPTION:
                # برگرداندن کاربر به مرحله توضیحات
                from handlers.project_details_handler import description_handler
                await description_handler(query.message, context, update)
                logger.info("Returned user to DESCRIPTION state")
                return DESCRIPTION
            elif current_state == DETAILS:
                # برگرداندن کاربر به مرحله جزئیات
                message_text = get_message("project_details", context, update)
                await query.edit_message_text(
                    message_text, 
                    reply_markup=create_dynamic_keyboard(context, update)
                )
                logger.info("Returned user to DETAILS state")
                return DETAILS
            elif current_state == CATEGORY:
                # برگرداندن کاربر به انتخاب دسته‌بندی
                await query.edit_message_text(
                    get_message("category_main_select", context, update),
                    reply_markup=create_category_keyboard(context, update)
                )
                logger.info("Returned user to CATEGORY state")
                return CATEGORY
            elif current_state == ROLE:
                # برگرداندن کاربر به انتخاب نقش
                await query.edit_message_text(
                    get_message("role_select", context, update),
                    reply_markup=get_main_menu_keyboard(context, update)
                )
                logger.info("Returned user to ROLE state")
                return ROLE
            else:
                # برای سایر حالات، نمایش منوی اصلی
                await query.edit_message_text(
                    get_message("welcome", context, update),
                    reply_markup=get_main_menu_keyboard(context, update)
                )
                logger.info(f"Returned user to main menu from state: {current_state}")
                return ROLE
        
        else:
            logger.info("Showing cancel confirmation dialog")
            # Show cancel confirmation dialog
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(get_message("cancel_yes", context, update), callback_data="cancel_confirmed")],
                [InlineKeyboardButton(get_message("cancel_no", context, update), callback_data="cancel_declined")]
            ])
            
            await query.edit_message_text(
                get_message("cancel_confirmation", context, update),
                reply_markup=keyboard
            )
            logger.info("Cancel confirmation dialog shown")
            return context.user_data.get('state', START)
    else:
        logger.info("Text message cancel - ending conversation directly")
        # Handle text message cancel (should not happen with inline keyboard)
        context.user_data.clear()
        await update.message.reply_text(get_message("operation_cancelled", context, update))
        return ConversationHandler.END

async def handle_restart_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle restart to main menu after cancellation"""
    query = update.callback_query
    await query.answer()
    
    logger.info("User chose to restart to main menu after cancellation")
    
    # Clear any existing data
    context.user_data.clear()
    
    # Check if user has phone
    has_phone = await check_phone(update, context)
    
    if has_phone:
        # Show main menu
        context.user_data['state'] = ROLE
        welcome_message = get_message("welcome", context, update)
        
        await MenuManager.show_menu(
            update,
            context,
            welcome_message,
            get_main_menu_keyboard(context, update)
        )
        return ROLE
    else:
        # Need to register phone first
        context.user_data['state'] = REGISTER
        await query.edit_message_text(
            get_message("share_phone_prompt", context, update),
            reply_markup=get_register_menu_keyboard(context, update)
        )
        return REGISTER

async def handle_restart_to_new_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle restart to new request after cancellation"""
    query = update.callback_query
    await query.answer()
    
    logger.info("User chose to start new request after cancellation")
    
    # Clear any existing data
    context.user_data.clear()
    context.user_data['state'] = CATEGORY
    context.user_data['files'] = []
    
    # Check if user has phone
    has_phone = await check_phone(update, context)
    
    if not has_phone:
        # Need to register phone first
        context.user_data['state'] = REGISTER
        await query.edit_message_text(
            get_message("share_phone_prompt", context, update),
            reply_markup=get_register_menu_keyboard(context, update)
        )
        return REGISTER
    
    # Get categories and show category selection
    try:
        from utils import get_categories
        categories = await get_categories()
        if not categories:
            await query.edit_message_text(get_message("error_fetching_categories", context, update))
            return ROLE
            
        context.user_data['categories'] = categories
        
        # Show category selection menu
        await MenuManager.show_menu(
            update,
            context,
            get_message("category_main_select", context, update),
            create_category_keyboard(context, update)
        )
        
        return CATEGORY
        
    except Exception as e:
        logger.error(f"Error starting new request: {e}")
        # Fallback to main menu
        context.user_data['state'] = ROLE
        await MenuManager.show_menu(
            update,
            context,
            get_message("welcome", context, update),
            get_main_menu_keyboard(context, update)
        )
        return ROLE