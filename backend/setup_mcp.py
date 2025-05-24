#!/usr/bin/env python3
"""
Setup MCP Server for Bivaset - نصب و راه‌اندازی سرور MCP بیواست
"""

import os
import sys
import subprocess
import json
import django
from pathlib import Path

def setup_django():
    """تنظیم Django برای مهاجرت‌ها"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
    django.setup()

def check_requirements():
    """بررسی نیازمندی‌ها"""
    print("🔍 بررسی نیازمندی‌ها...")
    
    required_packages = [
        'django', 'djangorestframework', 'psycopg2', 
        'python-telegram-bot', 'mcp'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📦 نصب پکیج‌های مفقود: {', '.join(missing_packages)}")
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install"
            ] + missing_packages, check=True)
            print("✅ پکیج‌ها با موفقیت نصب شدند")
        except subprocess.CalledProcessError as e:
            print(f"❌ خطا در نصب پکیج‌ها: {e}")
            return False
    
    return True

def check_database():
    """بررسی اتصال دیتابیس"""
    print("🗄️  بررسی اتصال دیتابیس...")
    
    try:
        setup_django()
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        print("  ✅ اتصال دیتابیس موفق")
        return True
    except Exception as e:
        print(f"  ❌ خطا در اتصال دیتابیس: {e}")
        return False

def run_migrations():
    """اجرای مهاجرت‌های Django"""
    print("🔄 اجرای مهاجرت‌های Django...")
    
    try:
        subprocess.run([
            sys.executable, "manage.py", "migrate"
        ], check=True)
        print("  ✅ مهاجرت‌ها با موفقیت انجام شد")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ❌ خطا در اجرای مهاجرت‌ها: {e}")
        return False

def create_test_data():
    """ایجاد داده‌های تست (اختیاری)"""
    print("📝 ایجاد داده‌های تست...")
    
    try:
        setup_django()
        from app.models import Category, User, Project
        
        # ایجاد دسته‌بندی‌ها
        categories = [
            "طراحی وب", "توسعه اپلیکیشن", "طراحی گرافیک",
            "بازاریابی دیجیتال", "ترجمه", "خدمات مالی"
        ]
        
        for cat_name in categories:
            category, created = Category.objects.get_or_create(
                name=cat_name,
                defaults={'description': f'توضیحات {cat_name}'}
            )
            if created:
                print(f"  ✅ دسته‌بندی '{cat_name}' ایجاد شد")
        
        print("  ✅ داده‌های تست آماده شدند")
        return True
        
    except Exception as e:
        print(f"  ❌ خطا در ایجاد داده‌های تست: {e}")
        return False

def create_mcp_config():
    """ایجاد فایل پیکربندی MCP"""
    print("⚙️  ایجاد فایل پیکربندی MCP...")
    
    current_dir = Path(__file__).parent.absolute()
    config = {
        "mcpServers": {
            "bivaset-database": {
                "command": "python",
                "args": ["mcp_server.py"],
                "cwd": str(current_dir),
                "env": {
                    "DJANGO_SETTINGS_MODULE": "app.settings",
                    "PYTHONPATH": str(current_dir)
                }
            }
        }
    }
    
    try:
        with open("mcp_config.json", "w", encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"  ✅ فایل پیکربندی در {current_dir}/mcp_config.json ایجاد شد")
        return True
    except Exception as e:
        print(f"  ❌ خطا در ایجاد فایل پیکربندی: {e}")
        return False

def test_mcp_server():
    """تست سرور MCP"""
    print("🧪 تست سرور MCP...")
    
    try:
        # راه‌اندازی سرور
        subprocess.run([
            sys.executable, "mcp_manager.py", "start"
        ], check=True)
        
        # انتظار برای راه‌اندازی
        import time
        time.sleep(3)
        
        # تست سرور
        result = subprocess.run([
            sys.executable, "mcp_manager.py", "test"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("  ✅ تست سرور موفق")
        else:
            print("  ⚠️  تست سرور با مشکل مواجه شد")
            print(result.stderr)
        
        # توقف سرور
        subprocess.run([
            sys.executable, "mcp_manager.py", "stop"
        ], check=True)
        
        return True
        
    except Exception as e:
        print(f"  ❌ خطا در تست سرور: {e}")
        return False

def main():
    """تابع اصلی نصب"""
    print("🚀 راه‌اندازی سرور MCP بیواست")
    print("=" * 50)
    
    steps = [
        ("بررسی نیازمندی‌ها", check_requirements),
        ("بررسی دیتابیس", check_database),
        ("اجرای مهاجرت‌ها", run_migrations),
        ("ایجاد داده‌های تست", create_test_data),
        ("ایجاد فایل پیکربندی", create_mcp_config),
        ("تست سرور MCP", test_mcp_server)
    ]
    
    for step_name, step_func in steps:
        print(f"\n📋 {step_name}...")
        if not step_func():
            print(f"❌ خطا در {step_name}")
            print("⏹️  نصب متوقف شد")
            return False
    
    print("\n" + "=" * 50)
    print("🎉 نصب و راه‌اندازی سرور MCP با موفقیت انجام شد!")
    print("\n📖 دستورهای مفید:")
    print("  python mcp_manager.py start     - راه‌اندازی سرور")
    print("  python mcp_manager.py stop      - توقف سرور")
    print("  python mcp_manager.py status    - وضعیت سرور")
    print("  python mcp_manager.py test      - تست سرور")
    print("  python mcp_manager.py logs      - نمایش لاگ‌ها")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
