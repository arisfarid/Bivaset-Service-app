from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from typing import Dict, List, Any, Optional, Tuple
from handlers.states import START, REGISTER, ROLE, EMPLOYER_MENU, CATEGORY, SUBCATEGORY, DESCRIPTION, LOCATION_TYPE, LOCATION_INPUT, DETAILS, DETAILS_FILES, DETAILS_DATE, DETAILS_DEADLINE, DETAILS_BUDGET, DETAILS_QUANTITY, SUBMIT, VIEW_PROJECTS, PROJECT_ACTIONS, CHANGE_PHONE, VERIFY_CODE
import logging

logger = logging.getLogger(__name__)

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

def add_navigation_to_message(text: str, current_state: int, user_data: Dict[str, Any]) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """
    Adds navigation info to a message and returns updated text and keyboard
    """
    keyboard = get_navigation_keyboard(current_state, user_data)

    # اگر کاربر غیرحضوری انتخاب کرده و در مرحله توضیحات است، پیام مرحله و navigation اضافه نشود
    if not (current_state == DESCRIPTION and user_data.get('service_location') == 'remote'):
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