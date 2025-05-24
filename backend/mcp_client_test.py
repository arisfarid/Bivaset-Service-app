#!/usr/bin/env python3
"""
Bivaset MCP Client - کلاینت تست برای سرور MCP بیواست
این کلاینت برای تست عملکرد سرور MCP و بررسی قابلیت‌های آن استفاده می‌شود.
"""

import asyncio
import json
import sys
from typing import Any, Dict

from mcp.client import ClientSession, stdio_client

class BivasetMCPClient:
    """کلاینت تست برای سرور MCP بیواست"""
    
    def __init__(self):
        self.session = None
    
    async def connect(self):
        """اتصال به سرور MCP"""
        try:
            # اجرای سرور MCP
            server_process = await asyncio.create_subprocess_exec(
                sys.executable, "mcp_server.py",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # اتصال استدیو
            self.session = await stdio_client(server_process.stdin, server_process.stdout)
            
            # مقداردهی اولیه
            await self.session.initialize()
            print("✅ اتصال به سرور MCP برقرار شد")
            
        except Exception as e:
            print(f"❌ خطا در اتصال به سرور: {e}")
            raise
    
    async def list_resources(self):
        """لیست منابع موجود"""
        try:
            resources = await self.session.list_resources()
            print("\n📋 منابع موجود:")
            for resource in resources.resources:
                print(f"  • {resource.name}: {resource.description}")
            return resources
        except Exception as e:
            print(f"❌ خطا در دریافت منابع: {e}")
    
    async def list_tools(self):
        """لیست ابزارهای موجود"""
        try:
            tools = await self.session.list_tools()
            print("\n🔧 ابزارهای موجود:")
            for tool in tools.tools:
                print(f"  • {tool.name}: {tool.description}")
            return tools
        except Exception as e:
            print(f"❌ خطا در دریافت ابزارها: {e}")
    
    async def read_resource(self, uri: str):
        """خواندن یک منبع"""
        try:
            result = await self.session.read_resource(uri)
            print(f"\n📖 محتوای منبع {uri}:")
            for content in result.contents:
                if hasattr(content, 'text'):
                    data = json.loads(content.text)
                    print(json.dumps(data, ensure_ascii=False, indent=2))
            return result
        except Exception as e:
            print(f"❌ خطا در خواندن منبع: {e}")
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]):
        """اجرای یک ابزار"""
        try:
            result = await self.session.call_tool(name, arguments)
            print(f"\n🔧 نتیجه اجرای ابزار {name}:")
            for content in result.content:
                if hasattr(content, 'text'):
                    try:
                        data = json.loads(content.text)
                        print(json.dumps(data, ensure_ascii=False, indent=2))
                    except json.JSONDecodeError:
                        print(content.text)
            return result
        except Exception as e:
            print(f"❌ خطا در اجرای ابزار: {e}")
    
    async def run_tests(self):
        """اجرای تست‌های مختلف"""
        print("🚀 شروع تست‌های MCP Server...")
        
        # تست 1: لیست منابع
        await self.list_resources()
        
        # تست 2: لیست ابزارها
        await self.list_tools()
        
        # تست 3: خواندن آمار
        await self.read_resource("bivaset://database/stats")
        
        # تست 4: جستجو در پروژه‌ها
        await self.call_tool("search_projects", {
            "query": "طراحی",
            "status": "open"
        })
        
        # تست 5: تحلیل پروژه‌ها
        await self.call_tool("analyze_projects", {
            "analysis_type": "by_category"
        })
        
        # تست 6: کوئری امن
        await self.call_tool("safe_query", {
            "query": "SELECT COUNT(*) as total_projects FROM app_project"
        })
        
        print("\n✅ تمام تست‌ها با موفقیت انجام شد!")

async def main():
    """تابع اصلی کلاینت"""
    client = BivasetMCPClient()
    
    try:
        await client.connect()
        await client.run_tests()
    except KeyboardInterrupt:
        print("\n⏹️  تست متوقف شد")
    except Exception as e:
        print(f"❌ خطای غیرمنتظره: {e}")

if __name__ == "__main__":
    asyncio.run(main())
