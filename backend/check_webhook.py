import os
import asyncio
import sys
sys.path.insert(0, '/home/ubuntu/Bivaset-Service-app/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
import django
django.setup()
from telegram.ext import Application

async def check_webhook():
    bot_token = '7998946498:AAGu847Zq6HYrHdnEwSw2xwJDLF2INd3f4g'
    app = Application.builder().token(bot_token).build()
    try:
        webhook_info = await app.bot.get_webhook_info()
        print(f'Webhook URL: {webhook_info.url}')
        print(f'Has custom cert: {webhook_info.has_custom_certificate}')
        print(f'Pending updates: {webhook_info.pending_update_count}')
        if webhook_info.url:
            print('Deleting webhook...')
            await app.bot.delete_webhook()
            print('Webhook deleted successfully')
        else:
            print('No webhook is set')
    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    asyncio.run(check_webhook())
