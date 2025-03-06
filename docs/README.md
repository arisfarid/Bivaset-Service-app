# Bivaset Service App - راهنمای نصب و اجرا

## پیش‌نیازها
- سیستم شما: ویندوز  
- سرور: Ubuntu 22.04 در ابر آروان (دیتاسنتر آلمان)  
- IP سرور: `185.204.171.107`  
- دامنه: `service.bivaset.com`  
- کلید SSH: فایل `.ppk` 
- **IP سرور:** `185.204.171.107`  
- **دامنه:** `service.bivaset.com`  
- **کلید SSH:** فایل `.ppk`  

### نصب ابزارها
1. **Python:**  
   - از [python.org](https://www.python.org/downloads/) نسخه 3.10 یا بالاتر را دانلود و نصب کنید.  
   - در Command Prompt چک کنید:  
     ```cmd
     python --version
     ```  
2. **Node.js:**  
   - از [nodejs.org](https://nodejs.org/) نسخه LTS را دانلود و نصب کنید.  
   - چک کنید:  
     ```cmd
     node -v
     ```  
3. **PuTTY:**  
   - از [putty.org](https://www.putty.org/) دانلود و نصب کنید برای اتصال SSH.  
4. **فونت IranSans:**  
   - از [fontiran.com](https://fontiran.com) یا یک منبع آزاد، فایل `IRANSans.woff2` را دانلود کنید و در `frontend/public/fonts/` قرار دهید.

---

## نصب و اجرای محلی (برای تست)
### بک‌اند
1. به پوشه `backend` بروید:  
   ```cmd
   cd backend
   ```
2. پکیج‌ها را نصب کنید:  
   ```cmd
   pip install -r requirements.txt
   ```
3. دیتابیس را مهاجرت کنید:  
   ```cmd
   python manage.py migrate
   ```
4. سرور را اجرا کنید:  
   ```cmd
   python manage.py runserver
   ```
   - بک‌اند در `http://localhost:8000` اجرا می‌شود.

### فرانت‌اند
1. به پوشه `frontend` بروید:  
   ```cmd
   cd frontend
   ```
2. پکیج‌ها را نصب کنید:  
   ```cmd
   npm install
   ```
3. سرور را اجرا کنید:  
   ```cmd
   npm start
   ```
   - فرانت‌اند در `http://localhost:3000` باز می‌شود.

---

## اجرا روی سرور
### 1. اتصال به سرور
- PuTTY را باز کنید:  
  - **Host Name:** `185.204.171.107`  
  - **Port:** 22  
  - **Connection > SSH > Auth > Credentials > Private key file:** فایل `.ppk` خود را انتخاب کنید.  
  - "Open" را بزنید و با کاربر `ubuntu` وارد شوید.

### 2. آپلود فایل‌ها
- در ویندوز، Command Prompt را باز کنید و به پوشه پروژه بروید:  
  ```cmd
  cd path\to\Bivaset-Service-app
  ```
- با `pscp` (از PuTTY) فایل‌ها را آپلود کنید:  
  ```cmd
  pscp -i path\to\your-key.ppk -r . ubuntu@185.204.171.107:/home/ubuntu/Bivaset-Service-app
  ```
  - جایگزین `path\to\your-key.ppk` با مسیر فایل `.ppk` خودت کن (مثلاً `C:\Users\YourName\key.ppk`).

### 3. نصب وابستگی‌ها روی سرور
- در PuTTY به سرور وصل شوید و دستورات زیر را اجرا کنید:  
  ```bash
  sudo apt update
  sudo apt install python3-pip python3-dev libpq-dev
  cd /home/ubuntu/Bivaset-Service-app/backend
  pip3 install -r requirements.txt
  python3 manage.py migrate
  ```

### 4. اجرای بک‌اند
- در سرور:  
  ```bash
  python3 manage.py runserver 0.0.0.0:8000
  ```
  - بک‌اند در `http://185.204.171.107:8000` یا `http://service.bivaset.com:8000` اجرا می‌شود.

### 5. نصب و اجرای فرانت‌اند
- در سرور:  
  ```bash
  sudo apt install nodejs npm
  cd /home/ubuntu/Bivaset-Service-app/frontend
  npm install
  npm start
  ```
  - فرانت‌اند در `http://185.204.171.107:3000` یا `http://service.bivaset.com:3000` باز می‌شود.

---

## رفع اشکال
- **پورت کار نمی‌کند:** در سرور چک کنید پورت‌ها باز باشن:  
  ```bash
  sudo ufw allow 8000
  sudo ufw allow 3000
  ```
- **دامنه کار نمی‌کند:** مطمئن شوید A Record دامنه به `185.204.171.107` اشاره می‌کند و DNS آپدیت شده:  
  ```cmd
  ping service.bivaset.com
  ```

---

## نکات
- این نسخه ساده برای تست اولیه است و کاربران نمونه (ID 1 و 2) داره. بعداً باید سیستم ورود کاربر اضافه بشه.
- برای محیط تولید، از Gunicorn و Nginx استفاده کنید تا عملکرد بهتر بشه.
