#!/usr/bin/env python3
"""
Bivaset MCP Manager - مدیریت سرور MCP بیواست
این اسکریپت برای راه‌اندازی، توقف و مدیریت سرور MCP استفاده می‌شود.
"""

import os
import sys
import subprocess
import signal
import time
import json
import logging
from pathlib import Path

# تنظیم لاگ‌گیری
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mcp_manager.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MCPManager:
    """مدیریت سرور MCP"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.pid_file = self.base_dir / "mcp_server.pid"
        self.log_file = self.base_dir / "mcp_server.log"
        
    def is_server_running(self):
        """بررسی وضعیت اجرای سرور"""
        if not self.pid_file.exists():
            return False
        
        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # بررسی وجود پروسه
            os.kill(pid, 0)
            return True
        except (OSError, ValueError):
            # حذف فایل PID نامعتبر
            if self.pid_file.exists():
                self.pid_file.unlink()
            return False
    
    def start_server(self):
        """راه‌اندازی سرور MCP"""
        if self.is_server_running():
            logger.warning("⚠️  سرور MCP از قبل در حال اجرا است")
            return False
        
        try:
            logger.info("🚀 راه‌اندازی سرور MCP...")
            
            # راه‌اندازی سرور در پس‌زمینه
            process = subprocess.Popen(
                [sys.executable, "mcp_server.py"],
                stdout=open(self.log_file, 'w', encoding='utf-8'),
                stderr=subprocess.STDOUT,
                cwd=self.base_dir
            )
            
            # ذخیره PID
            with open(self.pid_file, 'w') as f:
                f.write(str(process.pid))
            
            # انتظار برای راه‌اندازی
            time.sleep(2)
            
            if self.is_server_running():
                logger.info(f"✅ سرور MCP با موفقیت راه‌اندازی شد (PID: {process.pid})")
                return True
            else:
                logger.error("❌ خطا در راه‌اندازی سرور MCP")
                return False
                
        except Exception as e:
            logger.error(f"❌ خطا در راه‌اندازی: {e}")
            return False
    
    def stop_server(self):
        """توقف سرور MCP"""
        if not self.is_server_running():
            logger.warning("⚠️  سرور MCP در حال اجرا نیست")
            return True
        
        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            logger.info(f"⏹️  توقف سرور MCP (PID: {pid})...")
            
            # ارسال سیگنال توقف
            os.kill(pid, signal.SIGTERM)
            
            # انتظار برای توقف
            for _ in range(10):
                if not self.is_server_running():
                    break
                time.sleep(1)
            
            # اگر هنوز اجرا است، توقف اجباری
            if self.is_server_running():
                logger.warning("🔧 توقف اجباری سرور...")
                os.kill(pid, signal.SIGKILL)
                time.sleep(2)
            
            # حذف فایل PID
            if self.pid_file.exists():
                self.pid_file.unlink()
            
            logger.info("✅ سرور MCP با موفقیت متوقف شد")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطا در توقف سرور: {e}")
            return False
    
    def restart_server(self):
        """راه‌اندازی مجدد سرور"""
        logger.info("🔄 راه‌اندازی مجدد سرور MCP...")
        self.stop_server()
        time.sleep(2)
        return self.start_server()
    
    def status_server(self):
        """وضعیت سرور"""
        if self.is_server_running():
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            logger.info(f"✅ سرور MCP در حال اجرا است (PID: {pid})")
        else:
            logger.info("❌ سرور MCP متوقف است")
    
    def view_logs(self, lines=50):
        """نمایش لاگ‌های سرور"""
        if self.log_file.exists():
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    log_lines = f.readlines()
                    recent_logs = log_lines[-lines:] if len(log_lines) > lines else log_lines
                    
                print(f"\n📋 آخرین {len(recent_logs)} خط از لاگ سرور:")
                print("-" * 50)
                for line in recent_logs:
                    print(line.rstrip())
                print("-" * 50)
                    
            except Exception as e:
                logger.error(f"❌ خطا در خواندن لاگ: {e}")
        else:
            logger.warning("⚠️  فایل لاگ وجود ندارد")
    
    def install_dependencies(self):
        """نصب وابستگی‌های مورد نیاز"""
        logger.info("📦 نصب وابستگی‌های MCP...")
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
            ], check=True, cwd=self.base_dir)
            logger.info("✅ وابستگی‌ها با موفقیت نصب شدند")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ خطا در نصب وابستگی‌ها: {e}")
            return False
    
    def test_server(self):
        """تست سرور MCP"""
        if not self.is_server_running():
            logger.error("❌ سرور MCP در حال اجرا نیست")
            return False
        
        try:
            logger.info("🧪 تست سرور MCP...")
            result = subprocess.run([
                sys.executable, "mcp_client_test.py"
            ], capture_output=True, text=True, cwd=self.base_dir, encoding='utf-8')
            
            if result.returncode == 0:
                logger.info("✅ تست سرور موفقیت‌آمیز بود")
                print(result.stdout)
                return True
            else:
                logger.error("❌ تست سرور ناموفق")
                print(result.stderr)
                return False
                
        except Exception as e:
            logger.error(f"❌ خطا در تست سرور: {e}")
            return False

def main():
    """تابع اصلی مدیریت"""
    manager = MCPManager()
    
    if len(sys.argv) < 2:
        print("""
🛠️  Bivaset MCP Manager

استفاده:
  python mcp_manager.py <command>

دستورها:
  start      - راه‌اندازی سرور MCP
  stop       - توقف سرور MCP
  restart    - راه‌اندازی مجدد سرور
  status     - نمایش وضعیت سرور
  logs       - نمایش لاگ‌های سرور
  test       - تست سرور MCP
  install    - نصب وابستگی‌ها
        """)
        return
    
    command = sys.argv[1].lower()
    
    if command == "start":
        manager.start_server()
    elif command == "stop":
        manager.stop_server()
    elif command == "restart":
        manager.restart_server()
    elif command == "status":
        manager.status_server()
    elif command == "logs":
        lines = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        manager.view_logs(lines)
    elif command == "test":
        manager.test_server()
    elif command == "install":
        manager.install_dependencies()
    else:
        print(f"❌ دستور نامعتبر: {command}")

if __name__ == "__main__":
    main()
