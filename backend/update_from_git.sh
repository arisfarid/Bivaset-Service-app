#!/bin/bash

PROJECT_DIR="/home/ubuntu/Bivaset-Service-app/backend"
VENV_PATH="$PROJECT_DIR/venv"
BOT_LOG="$PROJECT_DIR/bot.log"

# تابع برای چک کردن موفقیت دستورات
check_status() {
    if [ $? -ne 0 ]; then
        echo "Error: $1 failed!"
        exit 1
    fi
}

echo "Starting update process at $(date)..."

# آپدیت از GitHub
echo "Updating from GitHub..."
cd "$PROJECT_DIR" || { echo "Failed to enter project directory"; exit 1; }
git fetch origin
git reset --hard origin/main
check_status "Git update"
echo "# Updated at $(date)" >> bot.py
echo "Git repository updated."

# فعال‌سازی محیط مجازی
if [ -d "$VENV_PATH" ]; then
    source "$VENV_PATH/bin/activate"
    echo "Virtual environment activated."
else
    echo "Warning: Virtual environment not found at $VENV_PATH. Creating one..."
    python3 -m venv "$VENV_PATH"
    source "$VENV_PATH/bin/activate"
    check_status "Virtual environment creation"
fi

# آپدیت وابستگی‌ها
echo "Updating dependencies..."
pip install --upgrade -r requirements.txt
check_status "Dependencies update"

# اعمال migrations
echo "Applying database migrations..."
python3 manage.py migrate --noinput
check_status "Database migrations"

# ری‌استارت Gunicorn
echo "Restarting Gunicorn service..."
sudo systemctl restart gunicorn
check_status "Gunicorn restart"
sudo systemctl status gunicorn --no-pager | head -n 10

# ری‌استارت ربات
echo "Restarting bot..."
# کشتن همه پروسه‌های قبلی ربات با سیگنال قوی
pkill -9 -f "python3 bot.py" 2>/dev/null
# صبر برای اطمینان از بسته شدن پروسه‌ها
sleep 2
# پاک کردن لاگ قدیمی (اختیاری)
[ -f "$BOT_LOG" ] && > "$BOT_LOG"
# اجرای ربات در پس‌زمینه با لاگ
nohup python3 bot.py > "$BOT_LOG" 2>&1 &
check_status "Bot start"
# گرفتن PID پروسه جدید
BOT_PID=$!
echo "Bot started with PID $BOT_PID. Check $BOT_LOG for output."
# چک کردن اینکه ربات واقعاً اجرا شده
sleep 2
if ps -p "$BOT_PID" > /dev/null; then
    echo "Bot is running successfully."
else
    echo "Warning: Bot failed to start. Check $BOT_LOG for details."
fi

echo "Update and restart completed successfully at $(date)!"