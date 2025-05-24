#!/usr/bin/env python3
"""
Standalone Bivaset MCP Server - Model Context Protocol Server for AI Database Access
سرور MCP مستقل بیواست - سرور پروتکل زمینه مدل برای دسترسی هوش مصنوعی به دیتابیس

این سرور بدون وابستگی به Django مستقیماً به دیتابیس متصل می‌شود.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, date
from decimal import Decimal
from typing import Any, Dict, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

from mcp.server import Server
from mcp.types import (
    Resource, Tool, TextContent, 
    CallToolResult, ListResourcesResult, ListToolsResult, ReadResourceResult
)

# تنظیم لاگ‌گیری
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mcp_server.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# تنظیمات اتصال دیتابیس
DATABASE_CONFIG = {
    'host': 'localhost',
    'database': 'bivaset_db',
    'user': 'bivaset_user',
    'password': 'bivaset123',
    'port': 5432
}

# محدودیت‌های امنیتی
MAX_QUERY_RESULTS = 100
ALLOWED_TABLES = ['app_user', 'app_project', 'app_category', 'app_proposal', 'app_projectfile']
READONLY_MODE = True  # تنها خواندن - برای امنیت بیشتر

class StandaloneBivasetMCPServer:
    """سرور MCP مستقل برای دسترسی هوش مصنوعی به دیتابیس بیواست"""
    
    def __init__(self):
        self.server = Server("bivaset-mcp-server")
        self.db_config = DATABASE_CONFIG
        self.setup_handlers()
        logger.info("🚀 Standalone Bivaset MCP Server initialized")
        
    def get_db_connection(self):
        """ایجاد اتصال جدید به دیتابیس"""
        try:
            conn = psycopg2.connect(**self.db_config)
            return conn
        except Exception as e:
            logger.error(f"❌ Database connection error: {e}")
            raise
    
    def setup_handlers(self):
        """تنظیم handler های سرور"""
        
        # Resource handlers
        @self.server.list_resources()
        async def list_resources() -> ListResourcesResult:
            """لیست منابع موجود"""
            resources = [
                Resource(
                    uri="bivaset://database/users",
                    name="کاربران سیستم",
                    description="اطلاعات کاربران شامل کارفرما و مجری",
                    mimeType="application/json"
                ),
                Resource(
                    uri="bivaset://database/projects",
                    name="پروژه‌های سیستم",
                    description="تمام پروژه‌های ثبت‌شده در سیستم",
                    mimeType="application/json"
                ),
                Resource(
                    uri="bivaset://database/categories",
                    name="دسته‌بندی خدمات",
                    description="دسته‌بندی‌های مختلف خدمات",
                    mimeType="application/json"
                ),
                Resource(
                    uri="bivaset://database/proposals",
                    name="پیشنهادات مجریان",
                    description="پیشنهادات ارسالی مجریان برای پروژه‌ها",
                    mimeType="application/json"
                ),
                Resource(
                    uri="bivaset://database/stats",
                    name="آمار سیستم",
                    description="آمار کلی و تحلیلی سیستم",
                    mimeType="application/json"
                )
            ]
            return ListResourcesResult(resources=resources)

        @self.server.read_resource()
        async def read_resource(uri: str) -> ReadResourceResult:
            """خواندن محتوای منابع"""
            logger.info(f"📖 Reading resource: {uri}")
            
            try:
                if uri == "bivaset://database/users":
                    data = await self.get_users_data()
                elif uri == "bivaset://database/projects":
                    data = await self.get_projects_data()
                elif uri == "bivaset://database/categories":
                    data = await self.get_categories_data()
                elif uri == "bivaset://database/proposals":
                    data = await self.get_proposals_data()
                elif uri == "bivaset://database/stats":
                    data = await self.get_stats_data()
                else:
                    raise ValueError(f"Unknown resource: {uri}")
                
                return ReadResourceResult(
                    contents=[
                        TextContent(
                            type="text",
                            text=json.dumps(data, ensure_ascii=False, indent=2, default=str)
                        )
                    ]
                )
            
            except Exception as e:
                logger.error(f"❌ Error reading resource {uri}: {e}")
                return ReadResourceResult(
                    contents=[
                        TextContent(
                            type="text",
                            text=f"خطا در خواندن منبع: {str(e)}"
                        )
                    ]
                )

        # Tool handlers
        @self.server.list_tools()
        async def list_tools() -> ListToolsResult:
            """لیست ابزارهای موجود"""
            tools = [
                Tool(
                    name="query_database",
                    description="اجرای کوئری امن روی دیتابیس (فقط SELECT)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "کوئری SQL برای اجرا (فقط SELECT مجاز است)"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="get_project_details",
                    description="دریافت جزئیات کامل یک پروژه",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": {
                                "type": "integer",
                                "description": "شناسه پروژه"
                            }
                        },
                        "required": ["project_id"]
                    }
                ),
                Tool(
                    name="search_projects",
                    description="جستجو در پروژه‌ها",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "متن جستجو"
                            },
                            "status": {
                                "type": "string",
                                "description": "وضعیت پروژه (اختیاری)",
                                "enum": ["ACTIVE", "COMPLETED", "CANCELLED"]
                            },
                            "category": {
                                "type": "string",
                                "description": "دسته‌بندی (اختیاری)"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="get_user_activity",
                    description="دریافت فعالیت‌های یک کاربر",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "integer",
                                "description": "شناسه کاربر"
                            }
                        },
                        "required": ["user_id"]
                    }
                )
            ]
            return ListToolsResult(tools=tools)

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """اجرای ابزارها"""
            logger.info(f"🔧 Calling tool: {name} with args: {arguments}")
            
            try:
                if name == "query_database":
                    result = await self.execute_safe_query(arguments["query"])
                elif name == "get_project_details":
                    result = await self.get_project_details(arguments["project_id"])
                elif name == "search_projects":
                    result = await self.search_projects(
                        arguments["query"],
                        arguments.get("status"),
                        arguments.get("category")
                    )
                elif name == "get_user_activity":
                    result = await self.get_user_activity(arguments["user_id"])
                else:
                    raise ValueError(f"Unknown tool: {name}")
                
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=json.dumps(result, ensure_ascii=False, indent=2, default=str)
                        )
                    ],
                    isError=False
                )
            
            except Exception as e:
                logger.error(f"❌ Error calling tool {name}: {e}")
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"خطا در اجرای ابزار: {str(e)}"
                        )
                    ],
                    isError=True
                )

    async def execute_safe_query(self, query: str) -> Dict[str, Any]:
        """اجرای کوئری امن"""
        # بررسی امنیت کوئری
        query_lower = query.lower().strip()
        
        # فقط SELECT مجاز است
        if not query_lower.startswith('select'):
            raise ValueError("فقط کوئری‌های SELECT مجاز هستند")
        
        # کلمات ممنوع
        forbidden_words = ['drop', 'delete', 'update', 'insert', 'alter', 'create', 'truncate']
        if any(word in query_lower for word in forbidden_words):
            raise ValueError("کوئری حاوی عملیات غیرمجاز است")
        
        # محدودیت جداول
        table_found = False
        for table in ALLOWED_TABLES:
            if table in query_lower:
                table_found = True
                break
        
        if not table_found:
            raise ValueError(f"فقط جداول مجاز قابل دسترسی هستند: {', '.join(ALLOWED_TABLES)}")
        
        # اجرای کوئری
        conn = self.get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query)
                rows = cursor.fetchmany(MAX_QUERY_RESULTS)
                
                return {
                    'query': query,
                    'rows': [dict(row) for row in rows],
                    'count': len(rows),
                    'limited': len(rows) == MAX_QUERY_RESULTS,
                    'timestamp': datetime.now().isoformat()
                }
        finally:
            conn.close()

    async def get_users_data(self) -> Dict[str, Any]:
        """دریافت داده‌های کاربران"""
        query = """
        SELECT id, name, phone, user_type, created_at, is_active 
        FROM app_user 
        ORDER BY created_at DESC 
        LIMIT %s
        """
        
        conn = self.get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (MAX_QUERY_RESULTS,))
                rows = cursor.fetchall()
                
                users = [dict(row) for row in rows]
                
                return {
                    'users': users,
                    'total_count': len(users),
                    'timestamp': datetime.now().isoformat()
                }
        finally:
            conn.close()

    async def get_projects_data(self) -> Dict[str, Any]:
        """دریافت داده‌های پروژه‌ها"""
        query = """
        SELECT p.id, p.title, p.description, p.budget, p.status, 
               p.service_location, p.created_at, p.deadline_date,
               u.name as user_name, u.phone as user_phone,
               c.name as category_name
        FROM app_project p
        LEFT JOIN app_user u ON p.user_id = u.id
        LEFT JOIN app_category c ON p.category_id = c.id
        ORDER BY p.created_at DESC 
        LIMIT %s
        """
        
        conn = self.get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (MAX_QUERY_RESULTS,))
                rows = cursor.fetchall()
                
                projects = [dict(row) for row in rows]
                
                return {
                    'projects': projects,
                    'total_count': len(projects),
                    'timestamp': datetime.now().isoformat()
                }
        finally:
            conn.close()

    async def get_categories_data(self) -> Dict[str, Any]:
        """دریافت داده‌های دسته‌بندی‌ها"""
        query = """
        SELECT id, name, description, created_at,
               (SELECT COUNT(*) FROM app_project WHERE category_id = app_category.id) as project_count
        FROM app_category 
        ORDER BY name
        """
        
        conn = self.get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                
                categories = [dict(row) for row in rows]
                
                return {
                    'categories': categories,
                    'total_count': len(categories),
                    'timestamp': datetime.now().isoformat()
                }
        finally:
            conn.close()

    async def get_proposals_data(self) -> Dict[str, Any]:
        """دریافت داده‌های پیشنهادات"""
        query = """
        SELECT pr.id, pr.proposed_price, pr.description, pr.delivery_time,
               pr.status, pr.created_at,
               p.title as project_title, p.budget as project_budget,
               u.name as contractor_name, u.phone as contractor_phone
        FROM app_proposal pr
        LEFT JOIN app_project p ON pr.project_id = p.id
        LEFT JOIN app_user u ON pr.contractor_id = u.id
        ORDER BY pr.created_at DESC 
        LIMIT %s
        """
        
        conn = self.get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (MAX_QUERY_RESULTS,))
                rows = cursor.fetchall()
                
                proposals = [dict(row) for row in rows]
                
                return {
                    'proposals': proposals,
                    'total_count': len(proposals),
                    'timestamp': datetime.now().isoformat()
                }
        finally:
            conn.close()

    async def get_stats_data(self) -> Dict[str, Any]:
        """دریافت آمار سیستم"""
        stats_queries = {
            'total_users': "SELECT COUNT(*) FROM app_user",
            'active_users': "SELECT COUNT(*) FROM app_user WHERE is_active = true",
            'total_projects': "SELECT COUNT(*) FROM app_project",
            'active_projects': "SELECT COUNT(*) FROM app_project WHERE status = 'ACTIVE'",
            'completed_projects': "SELECT COUNT(*) FROM app_project WHERE status = 'COMPLETED'",
            'total_proposals': "SELECT COUNT(*) FROM app_proposal",
            'accepted_proposals': "SELECT COUNT(*) FROM app_proposal WHERE status = 'ACCEPTED'",
            'total_categories': "SELECT COUNT(*) FROM app_category"
        }
        
        conn = self.get_db_connection()
        try:
            stats = {}
            with conn.cursor() as cursor:
                for stat_name, query in stats_queries.items():
                    cursor.execute(query)
                    result = cursor.fetchone()
                    stats[stat_name] = result[0] if result else 0
            
            # آمار بودجه
            budget_query = """
            SELECT 
                AVG(budget) as avg_budget,
                MIN(budget) as min_budget,
                MAX(budget) as max_budget,
                SUM(budget) as total_budget
            FROM app_project 
            WHERE budget IS NOT NULL
            """
            
            with conn.cursor() as cursor:
                cursor.execute(budget_query)
                budget_row = cursor.fetchone()
                if budget_row:
                    stats.update({
                        'avg_budget': float(budget_row[0]) if budget_row[0] else 0,
                        'min_budget': float(budget_row[1]) if budget_row[1] else 0,
                        'max_budget': float(budget_row[2]) if budget_row[2] else 0,
                        'total_budget': float(budget_row[3]) if budget_row[3] else 0
                    })
            
            return {
                'stats': stats,
                'timestamp': datetime.now().isoformat()
            }
        finally:
            conn.close()

    async def get_project_details(self, project_id: int) -> Dict[str, Any]:
        """دریافت جزئیات کامل پروژه"""
        conn = self.get_db_connection()
        try:
            # اطلاعات اصلی پروژه
            project_query = """
            SELECT p.*, u.name as user_name, u.phone as user_phone, u.user_type,
                   c.name as category_name, c.description as category_description
            FROM app_project p
            LEFT JOIN app_user u ON p.user_id = u.id
            LEFT JOIN app_category c ON p.category_id = c.id
            WHERE p.id = %s
            """
            
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(project_query, (project_id,))
                row = cursor.fetchone()
                
                if not row:
                    raise ValueError(f"پروژه با شناسه {project_id} یافت نشد")
                
                project = dict(row)
            
            # پیشنهادات پروژه
            proposals_query = """
            SELECT pr.*, u.name as contractor_name, u.phone as contractor_phone
            FROM app_proposal pr
            LEFT JOIN app_user u ON pr.contractor_id = u.id
            WHERE pr.project_id = %s
            ORDER BY pr.created_at DESC
            """
            
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(proposals_query, (project_id,))
                proposal_rows = cursor.fetchall()
                proposals = [dict(row) for row in proposal_rows]
            
            # فایل‌های پروژه
            files_query = """
            SELECT * FROM app_projectfile 
            WHERE project_id = %s
            ORDER BY id
            """
            
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(files_query, (project_id,))
                file_rows = cursor.fetchall()
                files = [dict(row) for row in file_rows]
            
            return {
                'project': project,
                'proposals': proposals,
                'files': files,
                'timestamp': datetime.now().isoformat()
            }
        finally:
            conn.close()

    async def search_projects(self, query: str, status: Optional[str] = None, category: Optional[str] = None) -> Dict[str, Any]:
        """جستجو در پروژه‌ها"""
        where_conditions = ["(p.title ILIKE %s OR p.description ILIKE %s)"]
        params = [f"%{query}%", f"%{query}%"]
        
        if status:
            where_conditions.append("p.status = %s")
            params.append(status)
        
        if category:
            where_conditions.append("c.name ILIKE %s")
            params.append(f"%{category}%")
        
        search_query = f"""
        SELECT p.id, p.title, p.description, p.budget, p.status, 
               p.service_location, p.created_at, p.deadline_date,
               u.name as user_name, u.phone as user_phone,
               c.name as category_name
        FROM app_project p
        LEFT JOIN app_user u ON p.user_id = u.id
        LEFT JOIN app_category c ON p.category_id = c.id
        WHERE {' AND '.join(where_conditions)}
        ORDER BY p.created_at DESC 
        LIMIT %s
        """
        
        params.append(MAX_QUERY_RESULTS)
        
        conn = self.get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(search_query, params)
                rows = cursor.fetchall()
                projects = [dict(row) for row in rows]
            
            return {
                'search_query': query,
                'filters': {'status': status, 'category': category},
                'projects': projects,
                'total_found': len(projects),
                'timestamp': datetime.now().isoformat()
            }
        finally:
            conn.close()

    async def get_user_activity(self, user_id: int) -> Dict[str, Any]:
        """دریافت فعالیت‌های کاربر"""
        conn = self.get_db_connection()
        try:
            # اطلاعات کاربر
            user_query = "SELECT * FROM app_user WHERE id = %s"
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(user_query, (user_id,))
                user_row = cursor.fetchone()
                if not user_row:
                    raise ValueError(f"کاربر با شناسه {user_id} یافت نشد")
                user = dict(user_row)
            
            # پروژه‌های کاربر
            projects_query = """
            SELECT p.*, c.name as category_name
            FROM app_project p
            LEFT JOIN app_category c ON p.category_id = c.id
            WHERE p.user_id = %s
            ORDER BY p.created_at DESC
            """
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(projects_query, (user_id,))
                project_rows = cursor.fetchall()
                projects = [dict(row) for row in project_rows]
            
            # پیشنهادات کاربر (اگر مجری باشد)
            proposals_query = """
            SELECT pr.*, p.title as project_title
            FROM app_proposal pr
            LEFT JOIN app_project p ON pr.project_id = p.id
            WHERE pr.contractor_id = %s
            ORDER BY pr.created_at DESC
            """
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(proposals_query, (user_id,))
                proposal_rows = cursor.fetchall()
                proposals = [dict(row) for row in proposal_rows]
            
            return {
                'user': user,
                'projects': projects,
                'proposals': proposals,
                'activity_summary': {
                    'total_projects': len(projects),
                    'total_proposals': len(proposals),
                    'active_projects': len([p for p in projects if p['status'] == 'ACTIVE']),
                    'completed_projects': len([p for p in projects if p['status'] == 'COMPLETED'])
                },
                'timestamp': datetime.now().isoformat()
            }
        finally:
            conn.close()

    async def run(self):
        """اجرای سرور MCP"""
        logger.info("🎯 Starting Standalone Bivaset MCP Server...")
        
        # تست اتصال دیتابیس
        try:
            conn = self.get_db_connection()
            conn.close()
            logger.info("✅ Database connection successful")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return
        
        # اجرای سرور
        async with self.server.stdio_server() as streams:
            await self.server.run(*streams)

async def main():
    """تابع اصلی"""
    server = StandaloneBivasetMCPServer()
    await server.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
        sys.exit(1)
