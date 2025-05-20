import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ContextTypes, ConversationHandler
from utils import upload_files, log_chat, BASE_URL
import logging
from keyboards import (
    create_dynamic_keyboard, 
    get_file_management_menu_keyboard, 
    create_photo_management_keyboard
)
from django.conf import settings
import os
from handlers.states import START, REGISTER, ROLE, EMPLOYER_MENU, CATEGORY, SUBCATEGORY, DESCRIPTION, LOCATION_TYPE, LOCATION_INPUT, DETAILS, DETAILS_FILES, DETAILS_DATE, DETAILS_DEADLINE, DETAILS_BUDGET, DETAILS_QUANTITY, SUBMIT, VIEW_PROJECTS, PROJECT_ACTIONS, CHANGE_PHONE, VERIFY_CODE
from localization import get_message

logger = logging.getLogger(__name__)

# New interface functions for project_details_handler to use
async def init_photo_management(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Initialize photo management - centralized entry point for photo operations"""
    context.user_data['state'] = DETAILS_FILES
    files = context.user_data.get('files', [])
    message = update.message or update.callback_query.message
    
    if files:
        await message.reply_text(
            get_message("photos_uploaded", context, update),
            reply_markup=get_file_management_menu_keyboard(context, update)
        )
    else:
        await message.reply_text(
            get_message("photos_command", context, update),
            reply_markup=get_file_management_menu_keyboard(context, update)
        )
    return DETAILS_FILES

async def handle_photo_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str) -> int:
    """Handle navigation actions for photo management"""
    if action in ["finish_files", "back_to_details"]:
        context.user_data['state'] = DETAILS
        message = update.message or update.callback_query.message
        await message.reply_text(
            get_message("project_details", context, update),
            reply_markup=create_dynamic_keyboard(context, update)
        )
        if update.callback_query:
            await update.callback_query.answer(get_message("back_to_details", context, update))
        return DETAILS
    elif action == "manage_photos":
        return await init_photo_management(update, context)
    
    return DETAILS_FILES

async def handle_attachment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    current_state = context.user_data.get('state', DETAILS_FILES)
    telegram_id = str(update.effective_user.id)

    if update.message and update.message.video:
        await update.message.reply_text(get_message("video_not_supported", context, update))
        await log_chat(update, context)
        return current_state

    if current_state == 'replacing_photo' and update.message and update.message.photo:
        new_photo = update.message.photo[-1].file_id
        index = context.user_data.get('replace_index')
        files = context.user_data.get('files', [])
        if 0 <= index < len(files):
            if new_photo in files:
                await update.message.reply_text(get_message("photo_already_exists", context, update))
            else:
                old_photo = files[index]
                files[index] = new_photo
                logger.info(f"Replaced photo {old_photo} with {new_photo} at index {index}")
                await update.message.reply_text(get_message("photo_replaced", context, update))
            await show_photo_management(update, context)
            context.user_data['state'] = DETAILS_FILES
        return DETAILS_FILES

    if update.message and update.message.photo:
        new_photo = update.message.photo[-1].file_id
        if 'files' not in context.user_data:
            context.user_data['files'] = []
        files = context.user_data['files']
        if new_photo not in files:
            remaining_slots = 5 - len(files)
            if remaining_slots <= 0:
                await update.message.reply_text(
                    get_message("photo_upload_max", context, update),
                    reply_markup=get_file_management_menu_keyboard(context, update)
                )
            else:
                files.append(new_photo)
                logger.info(f"Photo received from {telegram_id}: {new_photo}")
                await update.message.reply_text(
                    get_message("photo_upload_success", context, update),
                    reply_markup=get_file_management_menu_keyboard(context, update)
                )
        else:
            await update.message.reply_text(
                get_message("photo_already_exists", context, update),
                reply_markup=get_file_management_menu_keyboard(context, update)
            )
        context.user_data['files'] = files
        await log_chat(update, context)
        return DETAILS_FILES

    text = update.message.text if update.message else None
    if current_state in [DETAILS_FILES, 'managing_photos']:
        if text == get_message("finish_photos", context, update):
            context.user_data['state'] = DETAILS
            await update.message.reply_text(
                get_message("project_details", context, update),
                reply_markup=create_dynamic_keyboard(context, update)
            )
            await log_chat(update, context)
            return DETAILS
        elif text == get_message("manage_photos", context, update):
            await show_photo_management(update, context)
            return DETAILS_FILES
        elif text == get_message("back", context, update):
            context.user_data['state'] = DETAILS
            await update.message.reply_text(
                get_message("project_details", context, update),
                reply_markup=create_dynamic_keyboard(context, update)
            )
            await log_chat(update, context)
            return DETAILS

    return current_state

async def show_photo_management(update: Update, context: ContextTypes.DEFAULT_TYPE):
    files = context.user_data.get('files', [])
    if not files:
        await update.message.reply_text(
            get_message("photo_list_empty", context, update),
            reply_markup=get_file_management_menu_keyboard(context, update)
        )
        await log_chat(update, context)
        return

    keyboard_markup = create_photo_management_keyboard(files, context, update)
    await update.message.reply_text(
        get_message("photo_management_title", context, update),
        reply_markup=keyboard_markup
    )
    context.user_data['state'] = DETAILS_FILES
    await log_chat(update, context)

async def handle_photos_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Starting handle_photos_command")
    
    try:
        # اگر از callback آمده
        if update.callback_query:
            project_id = context.user_data.get('current_project_id')
            chat_id = update.callback_query.message.chat_id
        # اگر از کامند مستقیم آمده
        else:
            command = update.message.text
            project_id = command.split("_")[2]
            chat_id = update.message.chat_id
            
        logger.info(f"Attempting to fetch photos for project {project_id} for chat {chat_id}")

        # دریافت اطلاعات فایل‌ها از API
        response = requests.get(f"{BASE_URL}projects/{project_id}/")
        logger.info(f"API Response: status={response.status_code}")
        
        if response.status_code == 200:
            project_data = response.json()
            project_files = project_data.get('files', [])
            logger.info(f"Found {len(project_files)} files for project")
            
            if not project_files:
                logger.warning("No files found for project")
                message = get_message("no_images_found", context, update)
                if update.callback_query:
                    await update.callback_query.message.reply_text(message)
                else:
                    await update.message.reply_text(message)
                return

            # آماده‌سازی لیست عکس‌ها برای ارسال به صورت آلبوم
            media_group = []
            base_url = BASE_URL.rstrip('/api').rstrip('/')
            
            for i, file_path in enumerate(project_files):
                full_url = f"{base_url}/media/{file_path}"
                logger.info(f"Processing file {i+1}: {full_url}")
                
                try:
                    photo_response = requests.get(full_url)
                    if photo_response.status_code == 200:
                        media_group.append(InputMediaPhoto(
                            media=photo_response.content,
                            caption=get_message("original_image", context, update) if i == 0 else ""
                        ))
                        logger.info(f"Successfully added file {i+1} to media group")
                    else:
                        logger.error(f"Failed to download photo {i+1}. Status: {photo_response.status_code}")
                except Exception as e:
                    logger.error(f"Error processing photo {i+1}: {e}")

            if media_group:
                # ارسال عکس‌ها
                if update.callback_query:
                    await context.bot.send_media_group(chat_id=chat_id, media=media_group)
                else:
                    await update.message.reply_media_group(media=media_group)
                logger.info("Successfully sent all photos")
            else:
                message = get_message("error_loading_images", context, update)
                if update.callback_query:
                    await update.callback_query.message.reply_text(message)
                else:
                    await update.message.reply_text(message)
                logger.error("No photos were successfully processed")
        else:
            logger.error(f"Failed to fetch project data. Status: {response.status_code}")
            message = get_message("error_fetching_project", context, update)
            if update.callback_query:
                await update.callback_query.message.reply_text(message)
            else:
                await update.message.reply_text(message)
                
    except Exception as e:
        logger.error(f"Error in handle_photos_command: {e}")
        message = get_message("error_processing_request", context, update)
        if update.callback_query:
            await update.callback_query.message.reply_text(message)
        else:
            await update.message.reply_text(message)