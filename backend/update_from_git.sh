#!/bin/bash

# مسیر پروژه
PROJECT_DIR="/home/ubuntu/Bivaset-Service-app/backend"

echo "Updating from GitHub..."
cd "$PROJECT_DIR" || { echo "Failed to enter project directory"; exit 1; }
git fetch origin
git reset --hard origin/main
echo "Git repository updated."

# نصب وابستگی‌ها (در صورت تغییر requirements.txt)
pip install -r requirements.txt
echo "Dependencies updated."

# اعمال migrations برای بک‌اند (Django)
echo "Applying database migrations..."
python3 manage.py migrate --noinput || { echo "Migration failed"; exit 1; }

# ری‌استارت سرویس بک‌اند (فرض می‌کنیم از Gunicorn و systemd استفاده می‌کنی)
echo "Restarting backend service..."
sudo systemctl restart gunicorn || { echo "Failed to restart Gunicorn"; exit 1; }
sudo systemctl status gunicorn --no-pager | head -n 10

# ری‌استارت ربات
echo "Restarting bot..."
pkill -f "python3 bot.py"
nohup python3 bot.py > bot.log 2>&1 &
echo "Bot restarted. Check bot.log for output."

echo "Update and restart completed successfully!"