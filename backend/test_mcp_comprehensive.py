#!/usr/bin/env python3
"""
Bivaset MCP Client Test - کلاینت تست برای سرور MCP بیواست
این کلاینت برای تست عملکرد سرور MCP و بررسی قابلیت‌های آن استفاده می‌شود.
"""

import asyncio
import json
import sys
import logging
from typing import Any, Dict

# تنظیم لاگ‌گیری
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from mcp.client import ClientSession, stdio_client
except ImportError:
    print("❌ MCP client not available. Installing...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "mcp==0.9.1"], check=True)
    from mcp.client import ClientSession, stdio_client

class BivasetMCPClient:
    """کلاینت تست برای سرور MCP بیواست"""
    
    def __init__(self):
        self.session = None
        self.server_process = None
    
    async def connect(self, server_script="mcp_server_standalone.py"):
        """اتصال به سرور MCP"""
        try:
            print(f"🔌 Connecting to MCP server: {server_script}")
            
            # اجرای سرور MCP
            self.server_process = await asyncio.create_subprocess_exec(
                sys.executable, server_script,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # اتصال استدیو
            self.session = await stdio_client(
                self.server_process.stdin, 
                self.server_process.stdout
            )
            
            # مقداردهی اولیه
            await self.session.initialize()
            print("✅ Connected to MCP server successfully")
            
        except Exception as e:
            print(f"❌ Error connecting to server: {e}")
            raise
    
    async def disconnect(self):
        """قطع اتصال از سرور"""
        if self.session:
            await self.session.close()
        if self.server_process:
            self.server_process.terminate()
            await self.server_process.wait()
        print("🔌 Disconnected from MCP server")
    
    async def list_resources(self):
        """لیست منابع موجود"""
        try:
            print("\n📋 Listing available resources...")
            resources = await self.session.list_resources()
            print(f"Found {len(resources.resources)} resources:")
            for resource in resources.resources:
                print(f"  • {resource.name}: {resource.description}")
                print(f"    URI: {resource.uri}")
            return resources
        except Exception as e:
            print(f"❌ Error listing resources: {e}")
            return None
    
    async def read_resource(self, uri: str):
        """خواندن یک منبع"""
        try:
            print(f"\n📖 Reading resource: {uri}")
            result = await self.session.read_resource(uri)
            
            if result.contents:
                content = result.contents[0].text
                data = json.loads(content)
                
                # نمایش خلاصه
                if 'users' in data:
                    print(f"  Users count: {data['total_count']}")
                elif 'projects' in data:
                    print(f"  Projects count: {data['total_count']}")
                elif 'categories' in data:
                    print(f"  Categories count: {data['total_count']}")
                elif 'proposals' in data:
                    print(f"  Proposals count: {data['total_count']}")
                elif 'stats' in data:
                    stats = data['stats']
                    print(f"  Total users: {stats.get('total_users', 0)}")
                    print(f"  Total projects: {stats.get('total_projects', 0)}")
                    print(f"  Active projects: {stats.get('active_projects', 0)}")
                
                return data
            else:
                print("  No content returned")
                return None
                
        except Exception as e:
            print(f"❌ Error reading resource {uri}: {e}")
            return None
    
    async def list_tools(self):
        """لیست ابزارهای موجود"""
        try:
            print("\n🔧 Listing available tools...")
            tools = await self.session.list_tools()
            print(f"Found {len(tools.tools)} tools:")
            for tool in tools.tools:
                print(f"  • {tool.name}: {tool.description}")
            return tools
        except Exception as e:
            print(f"❌ Error listing tools: {e}")
            return None
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]):
        """فراخوانی یک ابزار"""
        try:
            print(f"\n🔧 Calling tool: {name}")
            print(f"   Arguments: {arguments}")
            
            result = await self.session.call_tool(name, arguments)
            
            if result.isError:
                print(f"❌ Tool error: {result.content[0].text}")
                return None
            else:
                content = result.content[0].text
                data = json.loads(content)
                print(f"✅ Tool executed successfully")
                
                # نمایش خلاصه نتایج
                if name == "query_database":
                    print(f"   Query returned {data.get('count', 0)} rows")
                elif name == "get_project_details":
                    project = data.get('project', {})
                    print(f"   Project: {project.get('title', 'Unknown')}")
                    print(f"   Proposals: {len(data.get('proposals', []))}")
                elif name == "search_projects":
                    print(f"   Found {data.get('total_found', 0)} projects")
                elif name == "get_user_activity":
                    activity = data.get('activity_summary', {})
                    print(f"   User projects: {activity.get('total_projects', 0)}")
                    print(f"   User proposals: {activity.get('total_proposals', 0)}")
                
                return data
                
        except Exception as e:
            print(f"❌ Error calling tool {name}: {e}")
            return None
    
    async def run_comprehensive_test(self):
        """اجرای تست جامع"""
        print("🚀 Starting comprehensive MCP server test...")
        print("=" * 50)
        
        try:
            # 1. لیست منابع
            await self.list_resources()
            
            # 2. خواندن منابع
            resources_to_test = [
                "bivaset://database/stats",
                "bivaset://database/categories",
                "bivaset://database/users",
                "bivaset://database/projects"
            ]
            
            for uri in resources_to_test:
                await self.read_resource(uri)
            
            # 3. لیست ابزارها
            await self.list_tools()
            
            # 4. تست ابزارها
            
            # تست کوئری ساده
            await self.call_tool("query_database", {
                "query": "SELECT COUNT(*) as total FROM app_user"
            })
            
            # تست جستجوی پروژه‌ها
            await self.call_tool("search_projects", {
                "query": "طراحی",
                "status": "ACTIVE"
            })
            
            # تست دریافت جزئیات پروژه (اگر پروژه‌ای وجود دارد)
            projects_data = await self.read_resource("bivaset://database/projects")
            if projects_data and projects_data.get('projects'):
                first_project = projects_data['projects'][0]
                await self.call_tool("get_project_details", {
                    "project_id": first_project['id']
                })
            
            # تست فعالیت کاربر (اگر کاربری وجود دارد)
            users_data = await self.read_resource("bivaset://database/users")
            if users_data and users_data.get('users'):
                first_user = users_data['users'][0]
                await self.call_tool("get_user_activity", {
                    "user_id": first_user['id']
                })
            
            print("\n" + "=" * 50)
            print("✅ Comprehensive test completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")

async def main():
    """تابع اصلی"""
    client = BivasetMCPClient()
    
    try:
        # اتصال به سرور
        await client.connect()
        
        # اجرای تست
        await client.run_comprehensive_test()
        
    except Exception as e:
        print(f"❌ Client error: {e}")
    finally:
        # قطع اتصال
        await client.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Test stopped by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
