import logging
from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest, TelegramError

logger = logging.getLogger(__name__)

class MenuManager:
    """مدیریت منوهای ربات و وضعیت گفتگو"""
    
    @staticmethod
    async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, 
                       keyboard: InlineKeyboardMarkup, clear_previous=True) -> int:
        """
        نمایش منو با حذف منوهای قبلی
        
        پارامترها:
        update - آبجکت Update تلگرام
        context - آبجکت Context تلگرام
        text - متن منو
        keyboard - کیبورد منو
        clear_previous - اگر True باشد، منوی قبلی را پاک می‌کند
        
        خروجی:
        شناسه پیام منوی جدید
        """
        query = update.callback_query
        chat_id = update.effective_chat.id
        
        # پاک کردن منوی قبلی
        if clear_previous and 'menu_history' in context.user_data:
            for msg_id in context.user_data['menu_history'][-5:]:  # فقط 5 منوی آخر را بررسی می‌کنیم
                try:
                    await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
                    logger.info(f"Deleted previous menu message {msg_id}")
                except (BadRequest, TelegramError) as e:
                    logger.warning(f"Could not delete menu message {msg_id}: {e}")
        
        # نمایش منوی جدید
        if query:
            try:
                # اگر callback query داریم، edit message
                message = await query.message.edit_text(text, reply_markup=keyboard, parse_mode='Markdown')
                menu_id = message.message_id
                logger.info(f"Edited message to show new menu with ID {menu_id}")
            except Exception as e:
                # اگر نتوانیم edit کنیم، پیام جدید می‌فرستیم
                logger.warning(f"Could not edit menu: {e}")
                message = await context.bot.send_message(chat_id=chat_id, text=text, 
                                                       reply_markup=keyboard, parse_mode='Markdown')
                menu_id = message.message_id
                logger.info(f"Sent new menu message with ID {menu_id} after edit failure")
        else:
            # ارسال پیام جدید
            message = await context.bot.send_message(chat_id=chat_id, text=text, 
                                                   reply_markup=keyboard, parse_mode='Markdown')
            menu_id = message.message_id
            logger.info(f"Sent new menu message with ID {menu_id}")
        
        # ذخیره تاریخچه منوها
        if 'menu_history' not in context.user_data:
            context.user_data['menu_history'] = []
        
        context.user_data['menu_history'].append(menu_id)
        context.user_data['current_menu_id'] = menu_id
        
        # محدود کردن تاریخچه به 10 منوی آخر
        if len(context.user_data['menu_history']) > 10:
            context.user_data['menu_history'] = context.user_data['menu_history'][-10:]
        
        return menu_id
    
    @staticmethod
    async def clear_menus(update: Update, context: ContextTypes.DEFAULT_TYPE, keep_current=False) -> None:
        """پاک کردن تمام منوهای قبلی"""
        if 'menu_history' not in context.user_data:
            return
        
        chat_id = update.effective_chat.id
        history = context.user_data['menu_history']
        
        # حفظ منوی فعلی اگر نیاز باشد
        if keep_current and 'current_menu_id' in context.user_data:
            current_id = context.user_data['current_menu_id']
            history = [msg_id for msg_id in history if msg_id != current_id]
        
        for msg_id in history:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
                logger.info(f"Deleted menu message {msg_id} during clear_menus")
            except (BadRequest, TelegramError) as e:
                logger.warning(f"Could not delete message {msg_id}: {e}")
        
        # ریست کردن تاریخچه
        if keep_current and 'current_menu_id' in context.user_data:
            context.user_data['menu_history'] = [context.user_data['current_menu_id']]
        else:
            context.user_data['menu_history'] = []
    
    @staticmethod
    async def disable_previous_menus(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """غیرفعال کردن منوهای قبلی بدون پاک کردن آنها"""
        if 'menu_history' not in context.user_data:
            return
        
        chat_id = update.effective_chat.id
        
        # فقط منوهای قبلی (نه منوی فعلی)
        if 'current_menu_id' in context.user_data:
            current_id = context.user_data['current_menu_id']
            history = [msg_id for msg_id in context.user_data['menu_history'] if msg_id != current_id]
        else:
            history = context.user_data['menu_history']
        
        for msg_id in history:
            try:
                await context.bot.edit_message_reply_markup(
                    chat_id=chat_id, 
                    message_id=msg_id,
                    reply_markup=None
                )
                logger.info(f"Disabled menu {msg_id} by removing keyboard")
            except (BadRequest, TelegramError) as e:
                logger.warning(f"Could not disable menu {msg_id}: {e}")