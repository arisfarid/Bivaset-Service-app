#!/bin/bash

PROJECT_DIR="/home/ubuntu/Bivaset-Service-app/backend"

echo "Updating from GitHub..."
cd "$PROJECT_DIR" || { echo "Failed to enter project directory"; exit 1; }
python3 -c "from utils import save_timestamp; save_timestamp()"  # ذخیره timestamp قبل از هر تغییر
git fetch origin
git reset --hard origin/main
echo "# Updated at $(date)" >> bot.py  # تغییر زمان فایل bot.py
echo "Git repository updated."

# فعال‌سازی محیط مجازی
VENV_PATH="/home/ubuntu/Bivaset-Service-app/backend/venv"
if [ -d "$VENV_PATH" ]; then
    source "$VENV_PATH/bin/activate"
    echo "Virtual environment activated."
else
    echo "Warning: Virtual environment not found at $VENV_PATH. Creating one..."
    python3 -m venv "$VENV_PATH"
    source "$VENV_PATH/bin/activate"
fi

# نصب وابستگی‌ها
pip install -r requirements.txt
echo "Dependencies updated."

# اعمال migrations
echo "Applying database migrations..."
python3 manage.py migrate --noinput || { echo "Migration failed"; exit 1; }

# ری‌استارت Gunicorn
echo "Restarting backend service..."
sudo systemctl restart gunicorn || { echo "Failed to restart Gunicorn"; exit 1; }
sudo systemctl status gunicorn --no-pager | head -n 10

# ری‌استارت ربات
echo "Restarting bot..."
pkill -f "python3 bot.py"
nohup python3 bot.py > bot.log 2>&1 &
echo "Bot restarted. Check bot.log for output."

echo "Update and restart completed successfully!"