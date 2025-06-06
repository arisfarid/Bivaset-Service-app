from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import logging
from handlers.start_handler import start, check_phone
from handlers.category_handler import handle_category_callback
from handlers.edit_handler import handle_edit_callback
from handlers.view_handler import handle_view_callback
from handlers.attachment_handler import show_photo_management, handle_photos_command
from utils import log_chat, get_categories, ensure_active_chat, restart_chat
from keyboards import create_category_keyboard, get_custom_input_keyboard, create_photo_management_keyboard, get_employer_menu_keyboard, get_file_management_menu_keyboard, get_restart_inline_menu_keyboard, get_main_menu_keyboard, create_dynamic_keyboard, create_service_flow_navigation_keyboard
from helpers.menu_manager import MenuManager
import asyncio  # برای استفاده از sleep
from asyncio import Lock
from handlers.states import START, REGISTER, ROLE, EMPLOYER_MENU, CATEGORY, SUBCATEGORY, DESCRIPTION, LOCATION_TYPE, LOCATION_INPUT, DETAILS, DETAILS_FILES, DETAILS_DATE, DETAILS_DEADLINE, DETAILS_BUDGET, DETAILS_QUANTITY, SUBMIT, VIEW_PROJECTS, PROJECT_ACTIONS, CHANGE_PHONE, VERIFY_CODE, STATE_NAMES
from handlers.navigation_utils import SERVICE_REQUEST_FLOW
from localization import get_message

logger = logging.getLogger(__name__)

# ایجاد قفل سراسری
button_lock = Lock()

# این تابع برای ارسال عکس به همراه کپشن و کیبورد اینلاین استفاده می‌شود
async def send_photo_with_caption(context, chat_id, photo, caption, reply_markup=None):
    await context.bot.send_photo(
        chat_id=chat_id,
        photo=photo,
        caption=caption,
        reply_markup=reply_markup
    )

# این تابع برای ارسال پیام متنی به همراه کیبورد اینلاین استفاده می‌شود
async def send_message_with_keyboard(context, chat_id, text, reply_markup):
    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=reply_markup
    )

# هندلر ناوبری برای مدیریت دکمه‌های قبلی/بعدی در جریان ثبت درخواست
# این تابع با توجه به state فعلی، کاربر را به مرحله قبلی یا بعدی هدایت می‌کند
# و منوهای مناسب را نمایش می‌دهد
async def handle_navigation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle navigation callbacks for moving back and forth in the conversation flow"""
    query = update.callback_query
    data = query.data
    current_state = context.user_data.get('state')
    
    logger.info(f"Navigation callback: {data} from state {STATE_NAMES.get(current_state, current_state)}")
    
    try:
        if data == "navigate_back":
            # If we're in the standard flow
            if current_state in SERVICE_REQUEST_FLOW:
                current_index = SERVICE_REQUEST_FLOW.index(current_state)
                if current_index > 0:
                    # Move to previous state in flow
                    previous_state = SERVICE_REQUEST_FLOW[current_index - 1]
                    context.user_data['previous_state'] = current_state
                    context.user_data['state'] = previous_state
                    logger.info(f"Moving back to {STATE_NAMES.get(previous_state, previous_state)}")
                    
                    # Handle specific states for back navigation
                    if previous_state == CATEGORY:
                        from handlers.category_handler import show_category_selection
                        await show_category_selection(update, context)
                    elif previous_state == SUBCATEGORY:
                        from handlers.category_handler import show_subcategories
                        # Get the selected category from context
                        category_id = context.user_data.get('selected_category')
                        if category_id:
                            await show_subcategories(update, context, category_id)
                        else:
                            from handlers.category_handler import show_category_selection
                            await show_category_selection(update, context)
                    elif previous_state == LOCATION_TYPE:
                        from handlers.location_handler import select_location_type
                        await select_location_type(update, context)
                    elif previous_state == DESCRIPTION:
                        await MenuManager.show_menu(
                            update,
                            context,
                            get_message("write_description_prompt", context, update),
                            create_service_flow_navigation_keyboard(previous_state, context)
                        )
                    await query.answer()
                    return previous_state
                else:
                    # We're at the beginning of the flow, go back to employer menu
                    context.user_data['previous_state'] = current_state
                    context.user_data['state'] = EMPLOYER_MENU
                    await MenuManager.show_menu(
                        update,
                        context,
                        get_message("employer_menu_prompt", context, update),
                        get_employer_menu_keyboard()
                    )
                    await query.answer()
                    return EMPLOYER_MENU
            else:
                # For states outside of flow, use the stored previous state
                previous_state = context.user_data.get('previous_state')
                if previous_state is not None:
                    context.user_data['state'] = previous_state
                    context.user_data['previous_state'] = current_state
                    logger.info(f"Moving to stored previous state: {STATE_NAMES.get(previous_state, previous_state)}")
                    
                    # Handle specific previous states
                    if previous_state == EMPLOYER_MENU:
                        await MenuManager.show_menu(
                            update,
                            context,
                            get_message("employer_menu_prompt", context, update),
                            get_employer_menu_keyboard()
                        )
                    elif previous_state == DETAILS:
                        await MenuManager.show_menu(
                            update,
                            context,
                            get_message("project_details", context, update),
                            create_dynamic_keyboard(context)
                        )
                    await query.answer()
                    return previous_state
                else:
                    # Default to employer menu if no previous state
                    context.user_data['state'] = EMPLOYER_MENU
                    await MenuManager.show_menu(
                        update,
                        context,
                        get_message("employer_menu_prompt", context, update),
                        get_employer_menu_keyboard()
                    )
                    await query.answer()
                    return EMPLOYER_MENU
        
        elif data == "navigate_next":
            # If we're in the standard flow
            if current_state in SERVICE_REQUEST_FLOW:
                current_index = SERVICE_REQUEST_FLOW.index(current_state)
                if current_index < len(SERVICE_REQUEST_FLOW) - 1:
                    # Move to next state in flow
                    next_state = SERVICE_REQUEST_FLOW[current_index + 1]
                    context.user_data['previous_state'] = current_state
                    context.user_data['state'] = next_state
                    logger.info(f"Moving forward to {STATE_NAMES.get(next_state, next_state)}")
                    
                    # Handle specific states for next navigation
                    if next_state == SUBCATEGORY:
                        from handlers.category_handler import show_subcategories
                        # Get the selected category from context
                        category_id = context.user_data.get('selected_category')
                        if category_id:
                            await show_subcategories(update, context, category_id)
                        else:
                            from handlers.category_handler import show_category_selection
                            await show_category_selection(update, context)
                    elif next_state == LOCATION_TYPE:
                        from handlers.location_handler import select_location_type
                        await select_location_type(update, context)
                    elif next_state == DESCRIPTION:
                        await MenuManager.show_menu(
                            update,
                            context,
                            get_message("write_description_prompt", context, update),
                            create_service_flow_navigation_keyboard(next_state, context)
                        )
                    elif next_state == DETAILS:
                        await MenuManager.show_menu(
                            update,
                            context,
                            get_message("project_details", context, update),
                            create_dynamic_keyboard(context)
                        )
                    await query.answer()
                    return next_state
            
            await query.answer()
            return current_state
    
    except Exception as e:
        logger.error(f"Error in navigation handler: {e}", exc_info=True)
        await query.answer(get_message("step_error", context, update))
        return current_state

# هندلر اصلی callback برای مدیریت همه callback ها و ناوبری کلی
# این تابع بر اساس داده callback و state فعلی، منو یا مرحله مناسب را نمایش می‌دهد
# و همچنین خطاها را مدیریت می‌کند
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return START

    logger.info(f"[handle_callback] user_id={update.effective_user.id} | state={context.user_data.get('state')} | prev_state={context.user_data.get('previous_state')} | context.user_data={context.user_data}")
    try:
        data = query.data
        current_state = context.user_data.get('state', ROLE)
        previous_state = context.user_data.get('previous_state')
        logger.info(f"Handling callback: {data}")
        logger.info(f"Current state: {current_state}")
        logger.info(f"Previous state: {previous_state}")
        logger.info(f"context.user_data: {context.user_data}")
        
        # handle continue_to_location: go to location selection directly
        if data == "continue_to_location":
            # set previous and current state for navigation
            context.user_data['previous_state'] = context.user_data.get('state')
            context.user_data['state'] = LOCATION_TYPE
            from handlers.location_handler import handle_location
            await query.answer()
            return await handle_location(update, context)
        
        # Handle continue_to_description callback (from location input to description)
        if data == "continue_to_description":
            logger.info("User continuing from location to description")
            context.user_data['previous_state'] = current_state
            context.user_data['state'] = DESCRIPTION
            await MenuManager.show_menu(
                update,
                context,
                get_message("write_description_prompt", context, update),
                create_service_flow_navigation_keyboard(DESCRIPTION, context)
            )
            await query.answer()
            return DESCRIPTION

        # Universal back navigation patterns
        if data == "back" or data == "back_to_previous":
            if previous_state is not None:
                logger.info(f"User navigating back to previous state: {previous_state}")
                # Store current state as the next previous state
                context.user_data['previous_state'] = current_state
                context.user_data['state'] = previous_state
                
                # Handle back navigation to specific states
                if previous_state == EMPLOYER_MENU:
                    await MenuManager.show_menu(
                        update,
                        context,
                        get_message("employer_menu_prompt", context, update),
                        get_employer_menu_keyboard()
                    )
                    await query.answer()
                    return EMPLOYER_MENU
                elif previous_state == ROLE:
                    await MenuManager.show_menu(
                        update,
                        context,
                        get_message("welcome", context, update),
                        get_main_menu_keyboard()
                    )
                    await query.answer()
                    return ROLE
                elif previous_state == CATEGORY:
                    from handlers.category_handler import show_category_selection
                    return await show_category_selection(update, context)
                elif previous_state == DETAILS:
                    await MenuManager.show_menu(
                        update,
                        context,
                        get_message("project_details", context, update),
                        create_dynamic_keyboard(context)
                    )
                    await query.answer()
                    return DETAILS
                # Let the conversation handler handle other states
                return previous_state
            else:
                # If no previous state, try to determine logical previous state
                if current_state == CATEGORY:
                    context.user_data['state'] = EMPLOYER_MENU
                    await MenuManager.show_menu(
                        update,
                        context,
                        get_message("employer_menu_prompt", context, update),
                        get_employer_menu_keyboard()
                    )
                    await query.answer()
                    return EMPLOYER_MENU
                elif current_state in SERVICE_REQUEST_FLOW:
                    # Find current position in flow
                    current_index = SERVICE_REQUEST_FLOW.index(current_state)
                    if current_index > 0:
                        # Go to previous state in flow
                        prev_state = SERVICE_REQUEST_FLOW[current_index - 1]
                        context.user_data['state'] = prev_state
                        logger.info(f"No previous state stored, navigating to previous in flow: {prev_state}")
                        return await handle_navigation_callback(update, context)
        
        # Specific back patterns from callback_handler
        if data == "back_to_details":
            logger.info("User returning to details menu")
            context.user_data['previous_state'] = current_state
            context.user_data['state'] = DETAILS
            # استفاده از MenuManager
            await MenuManager.show_menu(
                update,
                context,
                get_message("project_details", context, update),
                create_dynamic_keyboard(context)
            )
            await query.answer(get_message("back_to_details", context, update))
            return DETAILS

        if data == "back_to_menu":
            logger.info("Processing back to menu")
            # اگر در مرحله انتخاب دسته‌بندی هستیم
            context.user_data['previous_state'] = current_state
            if current_state == CATEGORY:
                context.user_data['state'] = EMPLOYER_MENU
                # استفاده از MenuManager
                await MenuManager.show_menu(
                    update,
                    context,
                    get_message("employer_menu_prompt", context, update),
                    get_employer_menu_keyboard()
                )
                await query.answer()
                return EMPLOYER_MENU
        if data == "deadline":
            logger.info("User clicked deadline button")
            context.user_data['state'] = DETAILS_DEADLINE
            # استفاده از MenuManager
            await MenuManager.show_menu(
                update,
                context,
                get_message("select_deadline_prompt", context, update),
                get_custom_input_keyboard()
            )
            await query.answer()
            return DETAILS_DEADLINE
            
        # پردازش برای دکمه بودجه
        if data == "budget":
            logger.info("User clicked budget button")
            context.user_data['state'] = DETAILS_BUDGET
            # استفاده از MenuManager
            await MenuManager.show_menu(
                update,
                context,
                get_message("enter_custom_budget_prompt", context, update),
                get_custom_input_keyboard()
            )
            await query.answer()
            return DETAILS_BUDGET
            
        # پردازش برای دکمه مقدار و واحد
        if data == "quantity":
            logger.info("User clicked quantity button")
            context.user_data['state'] = DETAILS_QUANTITY
            # استفاده از MenuManager
            await MenuManager.show_menu(
                update,
                context,
                get_message("enter_custom_quantity_prompt", context, update),
                get_custom_input_keyboard()
            )
            await query.answer()
            return DETAILS_QUANTITY
        
        # پردازش برای دکمه ثبت نهایی
        if data == "submit_final":
            logger.info("User clicked submit_final button")
            from handlers.submission_handler import submit_project
            return await submit_project(update, context)
            
        # پردازش برای بازگشت به آپلود
        if data == "back_to_upload":
            logger.info("User returning to file upload")
            # استفاده از MenuManager
            await MenuManager.show_menu(
                update,
                context,
                get_message("photos_command", context, update),
                get_file_management_menu_keyboard(context, update)
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
                # استفاده از MenuManager
                await MenuManager.show_menu(
                    update,
                    context,
                    get_message("employer_menu_prompt", context, update),
                    get_employer_menu_keyboard()
                )
                await query.answer()
                return EMPLOYER_MENU
            # اگر در منوی کارفرما هستیم    
            elif current_state == EMPLOYER_MENU:
                context.user_data['state'] = ROLE
                # استفاده از MenuManager
                await MenuManager.show_menu(
                    update,
                    context,
                    get_message("welcome", context, update),
                    get_main_menu_keyboard()
                )
                await query.answer()
                return ROLE        # بازگشت به منوی اصلی (از منوی کارفرما به انتخاب نقش)
        if data == "main_menu":
            logger.info("Processing main_menu callback - returning to role selection")
            context.user_data['state'] = ROLE
            # استفاده از MenuManager
            await MenuManager.show_menu(
                update,
                context,
                get_message("welcome", context, update),
                get_main_menu_keyboard(context, update)
            )
            await query.answer()
            return ROLE

        # بازگشت به منوی کارفرما
        if data == "back_to_employer_menu":
            logger.info("Processing back to employer menu")
            # ذخیره state قبلی
            context.user_data['previous_state'] = current_state
            context.user_data['state'] = EMPLOYER_MENU
            # استفاده از MenuManager
            await MenuManager.show_menu(
                update,
                context,
                get_message("employer_menu_prompt", context, update),
                get_employer_menu_keyboard()
            )
            await query.answer()
            return EMPLOYER_MENU

        # پردازش دسته‌بندی
        if data.startswith(('cat_', 'subcat_')):
            logger.info(f"[handle_callback] category selection: {data} | context.user_data={context.user_data}")
            from handlers.category_handler import handle_category_selection
            context.user_data['previous_state'] = EMPLOYER_MENU
            context.user_data['state'] = CATEGORY
            categories = await get_categories()
            if not categories:
                logger.error("Failed to fetch categories")
                await query.answer(get_message("error_fetching_categories", context, update))
                return EMPLOYER_MENU
            
            context.user_data['categories'] = categories
            return await handle_category_selection(update, context)

        # بررسی وضعیت ثبت‌نام کاربر
        if not await check_phone(update, context):
            logger.info("User needs to register phone first")
            await query.answer(get_message("share_phone_prompt", context, update))
            return REGISTER
            
        # پردازش دکمه ثبت شماره تلفن از طریق کیبورد اینلاین
        if data == "register_phone":
            logger.info("User clicked register_phone button")
            await query.answer(get_message("share_phone_prompt", context, update))
            from keyboards import get_register_menu_keyboard
            await query.message.reply_text(
                get_message("share_phone_prompt", context, update),
                reply_markup=get_register_menu_keyboard(context, update)
            )
            context.user_data['state'] = REGISTER
            return REGISTER

        # ادامه پردازش callback
        if data == "employer":
            try:
                context.user_data['state'] = EMPLOYER_MENU
                # استفاده از MenuManager
                await MenuManager.show_menu(
                    update,
                    context,
                    get_message("employer_menu_prompt", context, update),
                    get_employer_menu_keyboard()
                )
                await query.answer()
                return EMPLOYER_MENU
            except Exception as e:
                logger.error(f"Error editing message for employer menu: {e}")
                await query.answer(get_message("step_error", context, update))
                return context.user_data.get('state')
        elif data == "new_request":
            logger.info("Processing new request")
            # Clear user data to ensure no previous data persists
            context.user_data.clear()
            context.user_data['files'] = []
            context.user_data['state'] = CATEGORY
            
            categories = await get_categories()
            keyboard = create_category_keyboard(categories, context, update)
            
            # استفاده از MenuManager
            await MenuManager.show_menu(
                update,
                context,
                get_message("category_main_select", context, update),
                keyboard
            )
            await query.answer()
            return CATEGORY
        
        # Handle restart callbacks after cancellation
        elif data == "restart_to_main":
            logger.info("Processing restart to main menu")
            from handlers.start_handler import handle_restart_to_main
            return await handle_restart_to_main(update, context)
            
        elif data == "restart_to_new_request":
            logger.info("Processing restart to new request")
            from handlers.start_handler import handle_restart_to_new_request
            return await handle_restart_to_new_request(update, context)
            
        await query.answer()
        return context.user_data.get('state', START)
        
    except Exception as e:
        logger.error(f"Error in callback handler: {e}", exc_info=True)
        try:
            await query.answer(get_message("step_error", context, update))
        except Exception:
            pass
        return START

# هندلر شروع درخواست جدید (new_request)
# این تابع context کاربر را پاک می‌کند و منوی دسته‌بندی‌ها را نمایش می‌دهد
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
            await query.message.reply_text(get_message("error_fetching_categories", context, update))
            return EMPLOYER_MENU
            
        context.user_data['categories'] = categories
        # نمایش منوی دسته‌بندی‌ها
        keyboard = create_category_keyboard(categories, context, update)
        
        # حذف پیام‌های قبلی
        await query.message.delete()
        
        # ارسال منوی جدید
        await query.message.reply_text(
            get_message("category_main_select", context, update),
            reply_markup=keyboard
        )
        
        await query.answer()
        return CATEGORY
    except Exception as e:
        logger.error(f"Error in new_request handler: {e}")
        await query.message.reply_text(
            get_message("step_error", context, update),
            reply_markup=get_employer_menu_keyboard(context, update)
        )
        return EMPLOYER_MENU

# هندلر بازگشت به منوی اصلی
async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    # بازگشت به منوی اصلی
    await query.message.reply_text(
        get_message("welcome", context, update), 
        reply_markup=get_main_menu_keyboard(context, update)
    )
    return ROLE

# هندلر مدیریت عکس‌ها (نمایش، حذف، جایگزینی)
# این تابع برای مدیریت عکس‌های پروژه در مراحل مختلف استفاده می‌شود
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
            await query.answer(get_message("error_processing_request", context, update))
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
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=files[index],
                    caption=f"📸 عکس {index+1} از {len(files)}",
                    reply_markup=create_photo_management_keyboard(files, edit_mode=True, edit_index=index)
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
                    text=get_message("photo_replaced", context, update),
                )
            return DETAILS_FILES
    except Exception as e:
        logger.error(f"Error processing photo management callback: {e}")
        await query.answer(get_message("error_processing_request", context, update))
        return DETAILS_FILES