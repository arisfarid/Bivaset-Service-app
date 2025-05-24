# 🤖 سرور MCP بیواست - راهنمای کامل

## 📋 فهرست مطالب

1. [معرفی](#معرفی)
2. [نصب و راه‌اندازی](#نصب-و-راه‌اندازی)
3. [استفاده از سرور](#استفاده-از-سرور)
4. [امکانات و قابلیت‌ها](#امکانات-و-قابلیت‌ها)
5. [امنیت](#امنیت)
6. [عیب‌یابی](#عیب‌یابی)
7. [توسعه](#توسعه)

## 🚀 معرفی

سرور MCP (Model Context Protocol) بیواست امکان دسترسی امن و کنترل‌شده هوش مصنوعی به دیتابیس پروژه را فراهم می‌کند. این سرور طراحی شده تا:

- **امنیت بالا**: دسترسی فقط خواندنی با محدودیت‌های امنیتی
- **عملکرد بهینه**: کش و محدودیت تعداد نتایج
- **لاگ‌گیری کامل**: ثبت تمام عملیات برای نظارت
- **API ساده**: رابط کاربری آسان برای AI ها

## 🔧 نصب و راه‌اندازی

### 1. نصب خودکار (پیشنهادی)

```bash
cd backend
python setup_mcp.py
```

این اسکریپت تمام موارد زیر را بررسی و نصب می‌کند:
- پکیج‌های مورد نیاز
- اتصال دیتابیس
- مهاجرت‌های Django
- داده‌های تست
- فایل‌های پیکربندی

### 2. نصب دستی

#### نصب پکیج‌ها
```bash
pip install -r requirements.txt
```

#### اجرای مهاجرت‌ها
```bash
python manage.py migrate
```

#### ایجاد فایل پیکربندی
```bash
python -c "import json; json.dump({'mcpServers': {'bivaset-database': {'command': 'python', 'args': ['mcp_server.py']}}}, open('mcp_config.json', 'w'), indent=2)"
```

## 🎯 استفاده از سرور

### مدیریت سرور

```bash
# راه‌اندازی سرور
python mcp_manager.py start

# توقف سرور  
python mcp_manager.py stop

# راه‌اندازی مجدد
python mcp_manager.py restart

# بررسی وضعیت
python mcp_manager.py status

# نمایش لاگ‌ها
python mcp_manager.py logs

# تست سرور
python mcp_manager.py test
```

### اتصال AI کلاینت‌ها

سرور MCP بر روی استاندارد stdio کار می‌کند و با کلاینت‌های مختلف AI قابل استفاده است:

#### Claude Desktop
فایل پیکربندی را در `claude_desktop_config.json` اضافه کنید:

```json
{
  "mcpServers": {
    "bivaset-database": {
      "command": "python",
      "args": ["c:\\path\\to\\backend\\mcp_server.py"],
      "env": {
        "DJANGO_SETTINGS_MODULE": "app.settings"
      }
    }
  }
}
```

#### Python Client
```python
from mcp.client import ClientSession, stdio_client

# اتصال به سرور
session = await stdio_client("python", ["mcp_server.py"])
await session.initialize()

# استفاده از منابع
resources = await session.list_resources()
tools = await session.list_tools()
```

## 🛠️ امکانات و قابلیت‌ها

### منابع (Resources)

| منبع | توضیح |
|------|-------|
| `bivaset://database/users` | اطلاعات کاربران |
| `bivaset://database/projects` | پروژه‌ها |
| `bivaset://database/categories` | دسته‌بندی‌ها |
| `bivaset://database/proposals` | پیشنهادات |
| `bivaset://database/stats` | آمار کلی |

### ابزارها (Tools)

#### 1. جستجو در پروژه‌ها
```json
{
  "name": "search_projects",
  "arguments": {
    "query": "طراحی وب",
    "category": "طراحی",
    "status": "open",
    "user_role": "client"
  }
}
```

#### 2. جزئیات پروژه
```json
{
  "name": "get_project_details", 
  "arguments": {
    "project_id": 123
  }
}
```

#### 3. پروژه‌های کاربر
```json
{
  "name": "get_user_projects",
  "arguments": {
    "user_id": 456,
    "phone": "09123456789"
  }
}
```

#### 4. تحلیل آماری
```json
{
  "name": "analyze_projects",
  "arguments": {
    "analysis_type": "by_category"
  }
}
```

#### 5. کوئری امن
```json
{
  "name": "safe_query",
  "arguments": {
    "query": "SELECT COUNT(*) FROM app_project WHERE status='open'"
  }
}
```

## 🔒 امنیت

### محدودیت‌های امنیتی

- **فقط خواندن**: سرور تنها عملیات SELECT را مجاز می‌داند
- **جداول مجاز**: دسترسی محدود به جداول مشخص
- **محدودیت نتایج**: حداکثر 100 رکورد در هر درخواست
- **فیلتر کوئری**: بررسی و فیلتر کوئری‌های خطرناک
- **لاگ‌گیری**: ثبت تمام درخواست‌ها

### کلمات ممنوعه در کوئری
- DELETE, DROP, INSERT, UPDATE
- ALTER, CREATE, TRUNCATE

### جداول مجاز
- `app_user`
- `app_project` 
- `app_category`
- `app_proposal`
- `app_projectfile`

## 🔍 عیب‌یابی

### مشکلات رایج

#### 1. خطای اتصال دیتابیس
```bash
# بررسی تنظیمات Django
python manage.py check

# تست اتصال دیتابیس
python -c "import django; django.setup(); from django.db import connection; connection.cursor().execute('SELECT 1')"
```

#### 2. خطای پکیج mcp
```bash
# نصب مجدد پکیج
pip install mcp==1.0.0
```

#### 3. مشکل در راه‌اندازی سرور
```bash
# بررسی لاگ‌ها
python mcp_manager.py logs

# تست دستی
python mcp_server.py
```

### لاگ‌ها

لاگ‌های سرور در فایل‌های زیر ذخیره می‌شوند:
- `mcp_server.log` - لاگ‌های سرور اصلی
- `mcp_manager.log` - لاگ‌های مدیریت
- `backend.log` - لاگ‌های Django

## 🚀 توسعه

### اضافه کردن منبع جدید

```python
@self.server.read_resource()
async def read_resource(uri: str) -> ReadResourceResult:
    if uri == "bivaset://database/new_resource":
        return await self._get_new_resource_data()
```

### اضافه کردن ابزار جدید

```python
@self.server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    if name == "new_tool":
        result = await self._new_tool_function(**arguments)
```

### تست توسعه

```bash
# اجرای تست‌های کامل
python mcp_client_test.py

# تست ابزار خاص
python -c "
import asyncio
from mcp_client_test import BivasetMCPClient

async def test():
    client = BivasetMCPClient()
    await client.connect()
    await client.call_tool('search_projects', {'query': 'test'})

asyncio.run(test())
"
```

## 📊 نظارت و آمار

### آمار استفاده
```bash
# نمایش آمار از لاگ‌ها
grep "اجرای ابزار" mcp_server.log | wc -l

# پرکاربردترین ابزارها
grep "اجرای ابزار" mcp_server.log | cut -d: -f4 | sort | uniq -c | sort -nr
```

### نظارت سلامت
```bash
# بررسی دوره‌ای وضعیت
watch -n 30 "python mcp_manager.py status"

# نظارت لاگ‌های زنده
tail -f mcp_server.log
```

## 📞 پشتیبانی

در صورت مواجهه با مشکل:

1. بررسی لاگ‌ها: `python mcp_manager.py logs`
2. تست اتصالات: `python setup_mcp.py`
3. راه‌اندازی مجدد: `python mcp_manager.py restart`

---

**نکته**: این سرور برای محیط پروداکشن طراحی شده و شامل تمام ویژگی‌های امنیتی لازم می‌باشد.
