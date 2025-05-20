from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler
import requests
import logging
from utils import BASE_URL, log_chat
from keyboards import VIEW_PROJECTS_MENU_KEYBOARD
from handlers.phone_handler import require_phone
from handlers.states import START, REGISTER, ROLE, EMPLOYER_MENU, CATEGORY, SUBCATEGORY, DESCRIPTION, LOCATION_TYPE, LOCATION_INPUT, DETAILS, DETAILS_FILES, DETAILS_DATE, DETAILS_DEADLINE, DETAILS_BUDGET, DETAILS_QUANTITY, SUBMIT, VIEW_PROJECTS, PROJECT_ACTIONS, CHANGE_PHONE, VERIFY_CODE
from localization import get_message

logger = logging.getLogger(__name__)

@require_phone
async def handle_view_projects(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['state'] = VIEW_PROJECTS
    telegram_id = str(update.effective_user.id)
    try:
        response = requests.get(f"{BASE_URL}projects/?user_telegram_id={telegram_id}&ordering=-id&limit=5")
        if response.status_code == 200:
            projects = response.json()
            if not projects:
                await update.message.reply_text(get_message("no_projects_registered", context, update))
                await update.message.reply_text(
                    get_message("continue_or_return", context, update),
                    reply_markup=VIEW_PROJECTS_MENU_KEYBOARD
                )
                return VIEW_PROJECTS
            message = get_message("view_projects_prompt", context, update)
            inline_keyboard = [
                [InlineKeyboardButton(f"{project['title']} (کد: {project['id']})", callback_data=f"{project['id']}")]
                for project in projects
            ]
            await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(inline_keyboard))
            await update.message.reply_text(
                get_message("continue_or_return", context, update),
                reply_markup=VIEW_PROJECTS_MENU_KEYBOARD
            )
        else:
            context.user_data['status_code'] = response.status_code
            await update.message.reply_text(get_message("error_fetching_projects", context, update))
    except requests.exceptions.ConnectionError:
        await update.message.reply_text(get_message("backend_unavailable", context, update))
    await log_chat(update, context)
    return VIEW_PROJECTS

@require_phone
async def handle_view_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    project_id = query.data
    try:
        response = requests.get(f"{BASE_URL}projects/{project_id}/")
        if response.status_code == 200:
            project = response.json()
            cat_name = context.user_data['categories'][project['category']]['name']
            location = 'غیرحضوری' if project['service_location'] == 'remote' else get_message("location_map_link", context, update)
            summary = get_message(
                "project_summary_template",
                context,
                update
            )
            if project.get('budget'):
                summary += get_message("budget_saved", context, update) + "\n"
            if project.get('deadline_date'):
                summary += get_message("deadline_saved", context, update) + "\n"
            if project.get('start_date'):
                summary += get_message("need_date_saved", context, update) + "\n"
            if project.get('files'):
                images = "\n".join([f"- [عکس]({f})" for f in project['files']])
                summary += get_message("project_images_template", context, update)
            inline_keyboard = [
                [
                    InlineKeyboardButton(get_message("edit", context, update), callback_data=f"edit_{project_id}"),
                    InlineKeyboardButton(f"⏰ {get_message('extend_project', context, update)}", callback_data=f"extend_{project_id}")
                ],
                [
                    InlineKeyboardButton(get_message("delete_with_icon", context, update), callback_data=f"delete_{project_id}"),
                    InlineKeyboardButton(f"✅ {get_message('close_project', context, update)}", callback_data=f"close_{project_id}")
                ],
                [
                    InlineKeyboardButton(f"💬 {get_message('view_offers', context, update)}", callback_data=f"proposals_{project_id}")
                ]
            ]
            await query.edit_message_text(summary, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(inline_keyboard))
        else:
            context.user_data['status_code'] = response.status_code
            await query.edit_message_text(get_message("error_fetching_project_details", context, update))
    except requests.exceptions.ConnectionError:
        await query.edit_message_text(get_message("backend_unavailable", context, update))
    await log_chat(update, context)
    return PROJECT_ACTIONS