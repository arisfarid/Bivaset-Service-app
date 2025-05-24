#!/usr/bin/env python3
"""
Bivaset MCP Production Server Manager
مدیریت سرور MCP بیواست برای محیط تولید

این اسکریپت سرور MCP را برای محیط تولید راه‌اندازی و مدیریت می‌کند.
"""

import os
import sys
import json
import logging
import subprocess
import signal
import time
from pathlib import Path
from typing import Dict, Any

# تنظیم لاگ‌گیری
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mcp_production.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BivasetMCPProductionManager:
    """مدیریت سرور MCP در محیط تولید"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.pid_file = self.base_dir / "mcp_production.pid"
        self.log_file = self.base_dir / "mcp_server_production.log"
        self.config_file = self.base_dir / "mcp_production_config.json"
        
        # پیکربندی پیش‌فرض
        self.default_config = {
            "server": {
                "name": "bivaset-mcp-production",
                "description": "Bivaset MCP Server for AI Database Access in Production",
                "version": "1.0.0",
                "max_connections": 10,
                "timeout": 30
            },
            "database": {
                "host": "localhost",
                "port": 5432,
                "name": "bivaset_db",
                "user": "bivaset_user",
                "password": "bivaset123"
            },
            "security": {
                "readonly_mode": True,
                "max_query_results": 100,
                "allowed_tables": [
                    "app_user", "app_project", "app_category", 
                    "app_proposal", "app_projectfile"
                ],
                "forbidden_operations": [
                    "DROP", "DELETE", "UPDATE", "INSERT", 
                    "ALTER", "CREATE", "TRUNCATE"
                ]
            },
            "logging": {
                "level": "INFO",
                "file": "mcp_server_production.log",
                "max_size_mb": 100,
                "backup_count": 5
            }
        }
    
    def create_config(self):
        """ایجاد فایل پیکربندی"""
        if not self.config_file.exists():
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.default_config, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ Created config file: {self.config_file}")
        else:
            logger.info(f"ℹ️  Config file already exists: {self.config_file}")
    
    def load_config(self) -> Dict[str, Any]:
        """بارگذاری پیکربندی"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info("✅ Configuration loaded successfully")
            return config
        except Exception as e:
            logger.warning(f"⚠️  Error loading config, using defaults: {e}")
            return self.default_config
    
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
    
    def test_database_connection(self, config: Dict[str, Any]):
        """تست اتصال دیتابیس"""
        try:
            import psycopg2
            db_config = config['database']
            
            conn = psycopg2.connect(
                host=db_config['host'],
                port=db_config['port'],
                database=db_config['name'],
                user=db_config['user'],
                password=db_config['password']
            )
            
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            conn.close()
            logger.info("✅ Database connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database connection test failed: {e}")
            return False
    
    def start_server(self):
        """راه‌اندازی سرور MCP"""
        if self.is_server_running():
            logger.warning("⚠️  MCP server is already running")
            return False
        
        # ایجاد پیکربندی
        self.create_config()
        config = self.load_config()
        
        # تست اتصال دیتابیس
        if not self.test_database_connection(config):
            logger.error("❌ Cannot start server due to database connection issues")
            return False
        
        try:
            logger.info("🚀 Starting MCP server in production mode...")
            
            # راه‌اندازی سرور در پس‌زمینه
            process = subprocess.Popen(
                [sys.executable, "mcp_server_standalone.py"],
                stdout=open(self.log_file, 'w', encoding='utf-8'),
                stderr=subprocess.STDOUT,
                cwd=self.base_dir
            )
            
            # ذخیره PID
            with open(self.pid_file, 'w') as f:
                f.write(str(process.pid))
            
            # انتظار برای راه‌اندازی
            time.sleep(3)
            
            if self.is_server_running():
                logger.info(f"✅ MCP server started successfully (PID: {process.pid})")
                logger.info(f"📋 Log file: {self.log_file}")
                logger.info(f"⚙️  Config file: {self.config_file}")
                return True
            else:
                logger.error("❌ Server failed to start")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error starting server: {e}")
            return False
    
    def stop_server(self):
        """توقف سرور MCP"""
        if not self.is_server_running():
            logger.warning("⚠️  MCP server is not running")
            return True
        
        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            logger.info(f"⏹️  Stopping MCP server (PID: {pid})...")
            
            # ارسال سیگنال توقف
            os.kill(pid, signal.SIGTERM)
            
            # انتظار برای توقف
            for _ in range(10):
                if not self.is_server_running():
                    break
                time.sleep(1)
            
            if self.is_server_running():
                # اجبار به توقف
                logger.warning("⚠️  Force stopping server...")
                os.kill(pid, signal.SIGKILL)
                time.sleep(2)
            
            # حذف فایل PID
            if self.pid_file.exists():
                self.pid_file.unlink()
            
            logger.info("✅ MCP server stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error stopping server: {e}")
            return False
    
    def restart_server(self):
        """راه‌اندازی مجدد سرور MCP"""
        logger.info("🔄 Restarting MCP server...")
        self.stop_server()
        time.sleep(2)
        return self.start_server()
    
    def get_server_status(self):
        """دریافت وضعیت سرور"""
        if self.is_server_running():
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # اطلاعات پروسه
            try:
                import psutil
                process = psutil.Process(pid)
                memory_mb = process.memory_info().rss / 1024 / 1024
                cpu_percent = process.cpu_percent()
                
                status = {
                    "running": True,
                    "pid": pid,
                    "memory_mb": round(memory_mb, 2),
                    "cpu_percent": cpu_percent,
                    "start_time": process.create_time()
                }
            except ImportError:
                status = {
                    "running": True,
                    "pid": pid,
                    "memory_mb": "N/A",
                    "cpu_percent": "N/A",
                    "start_time": "N/A"
                }
        else:
            status = {
                "running": False,
                "pid": None,
                "memory_mb": 0,
                "cpu_percent": 0,
                "start_time": None
            }
        
        return status
    
    def show_logs(self, lines=50):
        """نمایش لاگ‌های سرور"""
        try:
            if self.log_file.exists():
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    log_lines = f.readlines()
                
                print(f"\n📋 Last {lines} lines from {self.log_file}:")
                print("-" * 50)
                for line in log_lines[-lines:]:
                    print(line.rstrip())
                print("-" * 50)
            else:
                logger.warning("⚠️  Log file not found")
                
        except Exception as e:
            logger.error(f"❌ Error reading logs: {e}")
    
    def create_systemd_service(self):
        """ایجاد سرویس systemd (برای لینوکس)"""
        service_content = f"""[Unit]
Description=Bivaset MCP Server
After=network.target postgresql.service

[Service]
Type=simple
User=bivaset
WorkingDirectory={self.base_dir}
ExecStart={sys.executable} {self.base_dir}/mcp_server_standalone.py
Restart=always
RestartSec=10
StandardOutput=append:{self.log_file}
StandardError=append:{self.log_file}

[Install]
WantedBy=multi-user.target
"""
        
        service_file = Path("/etc/systemd/system/bivaset-mcp.service")
        try:
            with open(service_file, 'w') as f:
                f.write(service_content)
            
            logger.info(f"✅ Systemd service created: {service_file}")
            logger.info("To enable: sudo systemctl enable bivaset-mcp")
            logger.info("To start: sudo systemctl start bivaset-mcp")
            
        except PermissionError:
            logger.error("❌ Permission denied. Run as root or use sudo.")
        except Exception as e:
            logger.error(f"❌ Error creating systemd service: {e}")

def main():
    """تابع اصلی"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Bivaset MCP Production Manager")
    parser.add_argument('action', choices=['start', 'stop', 'restart', 'status', 'logs', 'config', 'systemd'],
                      help='Action to perform')
    parser.add_argument('--lines', type=int, default=50,
                      help='Number of log lines to show (for logs action)')
    
    args = parser.parse_args()
    
    manager = BivasetMCPProductionManager()
    
    if args.action == 'start':
        success = manager.start_server()
        sys.exit(0 if success else 1)
        
    elif args.action == 'stop':
        success = manager.stop_server()
        sys.exit(0 if success else 1)
        
    elif args.action == 'restart':
        success = manager.restart_server()
        sys.exit(0 if success else 1)
        
    elif args.action == 'status':
        status = manager.get_server_status()
        print(f"\n📊 MCP Server Status:")
        print(f"   Running: {'✅ Yes' if status['running'] else '❌ No'}")
        if status['running']:
            print(f"   PID: {status['pid']}")
            print(f"   Memory: {status['memory_mb']} MB")
            print(f"   CPU: {status['cpu_percent']}%")
        print()
        
    elif args.action == 'logs':
        manager.show_logs(args.lines)
        
    elif args.action == 'config':
        manager.create_config()
        config = manager.load_config()
        print(f"\n⚙️  Current Configuration:")
        print(json.dumps(config, indent=2, ensure_ascii=False))
        
    elif args.action == 'systemd':
        manager.create_systemd_service()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)
