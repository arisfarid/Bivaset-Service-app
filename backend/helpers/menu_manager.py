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
        نمایش منو با حذف منوهای قبلی (در صورت نیاز)
        """
        query = update.callback_query
        chat_id = update.effective_chat.id
        
        logger.info(f"🎯 MenuManager.show_menu called")
        logger.info(f"📊 Parameters: clear_previous={clear_previous}")
        logger.info(f"🔍 Query exists: {query is not None}")
        logger.info(f"📜 Current menu_history: {context.user_data.get('menu_history', [])}")
        logger.info(f"🔢 Current menu_id: {context.user_data.get('current_menu_id', 'NOT_SET')}")        # ابتدا سعی کن منوی موجود را edit کن
        if query:
            logger.info(f"🔄 Attempting to edit existing menu via callback query")
            try:
                message = await query.message.edit_text(text, reply_markup=keyboard, parse_mode='Markdown')
                menu_id = message.message_id
                logger.info(f"✅ Successfully edited existing menu message to ID {menu_id}")
                  # ذخیره تاریخچه منوها
                if 'menu_history' not in context.user_data:
                    context.user_data['menu_history'] = []
                if menu_id not in context.user_data['menu_history']:
                    context.user_data['menu_history'].append(menu_id)
                    logger.info(f"📝 Added menu ID {menu_id} to history")
                context.user_data['current_menu_id'] = menu_id
                # ذخیره محتوای پیام برای مقایسه‌های بعدی
                context.user_data['last_menu_message'] = text
                logger.info(f"🎯 Set current_menu_id to {menu_id}")
                logger.info(f"📊 Final menu_history after edit: {context.user_data['menu_history']}")
                return menu_id
                
            except Exception as e:
                logger.error(f"❌ Could not edit menu via query: {e}")
                logger.error(f"🔍 Edit error type: {type(e).__name__}")
                  # اگر خطای "Message is not modified" است، یعنی محتوا تغییری نکرده
                if "Message is not modified" in str(e):
                    logger.info(f"📋 Menu content is identical - no need to edit, returning current menu ID")
                    # در این حالت، ID منوی فعلی را برگردان و تاریخچه را به‌روزرسانی کن
                    current_menu_id = query.message.message_id
                    if 'menu_history' not in context.user_data:
                        context.user_data['menu_history'] = []
                    if current_menu_id not in context.user_data['menu_history']:
                        context.user_data['menu_history'].append(current_menu_id)
                    context.user_data['current_menu_id'] = current_menu_id
                    # ذخیره محتوای پیام برای مقایسه‌های بعدی
                    context.user_data['last_menu_message'] = text
                    return current_menu_id
                
                # اگر edit نشد، ادامه به سناریوی ارسال پیام جدید

        # اگر clear_previous درخواست شده، پیام‌های قبلی را حذف کن
        if clear_previous and 'menu_history' in context.user_data:
            logger.info(f"🗑️ Clearing previous menus: {context.user_data['menu_history'][-5:]}")
            for msg_id in context.user_data['menu_history'][-5:]:
                try:
                    await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
                    logger.info(f"✅ Deleted previous menu message {msg_id}")
                except (BadRequest, TelegramError) as e:
                    logger.warning(f"⚠️ Could not delete menu message {msg_id}: {e}")
            # پاک کردن تاریخچه بعد از حذف
            context.user_data['menu_history'] = []
            logger.info(f"🧹 Cleared menu_history")

        # ارسال پیام جدید
        logger.info(f"📤 Sending new menu message")
        try:
            message = await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=keyboard, parse_mode='Markdown')
            menu_id = message.message_id
            logger.info(f"✅ Sent new menu message with ID {menu_id}")            # ذخیره تاریخچه منوها
            if 'menu_history' not in context.user_data:
                context.user_data['menu_history'] = []
            context.user_data['menu_history'].append(menu_id)
            context.user_data['current_menu_id'] = menu_id
            # ذخیره محتوای پیام برای مقایسه‌های بعدی
            context.user_data['last_menu_message'] = text
            if len(context.user_data['menu_history']) > 10:
                context.user_data['menu_history'] = context.user_data['menu_history'][-10:]
            
            logger.info(f"📝 Added new menu ID {menu_id} to history")
            logger.info(f"🎯 Set current_menu_id to {menu_id}")
            logger.info(f"📊 Final menu_history: {context.user_data['menu_history']}")
            return menu_id
        except Exception as send_error:
            logger.error(f"❌ Failed to send new menu message: {send_error}")
            logger.error(f"🔍 Send error type: {type(send_error).__name__}")
            raise
    
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
    async def clear_chat_history(update: Update, context: ContextTypes.DEFAULT_TYPE, message_count=30) -> None:
        """
        پاک کردن تعداد زیادی از پیام‌های قبلی در گفتگو
        
        پارامترها:
        update - آبجکت Update تلگرام
        context - آبجکت Context تلگرام
        message_count - تعداد پیام‌هایی که باید پاک شوند (به صورت پیش‌فرض 30 پیام)
        """
        chat_id = update.effective_chat.id
        current_message_id = update.message.message_id if update.message else (
            update.callback_query.message.message_id if update.callback_query else None
        )
        
        if not current_message_id:
            logger.warning("No message ID found to start clearing history")
            return
        
        # پاک کردن پیام‌های قبلی با استفاده از شناسه پیام فعلی به عنوان نقطه شروع
        deleted_count = 0
        for offset in range(1, message_count + 1):
            try:
                msg_id = current_message_id - offset
                if msg_id <= 0:  # اطمینان از اینکه ID پیام معتبر است
                    continue
                    
                await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
                deleted_count += 1
                logger.info(f"Deleted message {msg_id} during chat history cleanup")
            except (BadRequest, TelegramError) as e:
                logger.debug(f"Could not delete message {current_message_id - offset}: {e}")
                # اگر به خطای "پیام برای حذف خیلی قدیمی است" یا "پیام یافت نشد" برخوردیم، ادامه می‌دهیم
                continue
        
        logger.info(f"Cleared {deleted_count} messages from chat history")
        
        # همچنین منوهای ذخیره شده در تاریخچه را پاک کنیم
        await MenuManager.clear_menus(update, context)
    
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