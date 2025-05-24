#!/usr/bin/env python3
"""
Bivaset MCP Server - Model Context Protocol Server for AI Database Access
سرور MCP بیواست - سرور پروتکل زمینه مدل برای دسترسی هوش مصنوعی به دیتابیس

این سرور امکان دسترسی امن و کنترل‌شده هوش مصنوعی به دیتابیس بیواست را فراهم می‌کند.
شامل محدودیت‌های امنیتی، لاگ‌گیری کامل و کنترل دسترسی می‌باشد.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, date
from decimal import Decimal
from typing import Any, Dict, List, Optional

# اضافه کردن مسیر Django به sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# تنظیمات Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
import django
django.setup()

from django.db import connection
from django.contrib.gis.geos import Point
from app.models import User, Project, Category, Proposal, ProjectFile

from mcp.server import Server
from mcp.types import (
    Resource, Tool, TextContent, ImageContent, EmbeddedResource,
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

# محدودیت‌های امنیتی
MAX_QUERY_RESULTS = 100
ALLOWED_TABLES = ['app_user', 'app_project', 'app_category', 'app_proposal', 'app_projectfile']
READONLY_MODE = True  # تنها خواندن - برای امنیت بیشتر

class BivasetMCPServer:
    """سرور MCP برای دسترسی هوش مصنوعی به دیتابیس بیواست"""
    
    def __init__(self):
        self.server = Server("bivaset-mcp-server")
        self.setup_handlers()
        logger.info("🚀 Bivaset MCP Server initialized")
        
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
            """خواندن اطلاعات منابع"""
            try:
                if uri == "bivaset://database/users":
                    return await self._get_users_data()
                elif uri == "bivaset://database/projects":
                    return await self._get_projects_data()
                elif uri == "bivaset://database/categories":
                    return await self._get_categories_data()
                elif uri == "bivaset://database/proposals":
                    return await self._get_proposals_data()
                elif uri == "bivaset://database/stats":
                    return await self._get_stats_data()
                else:
                    raise ValueError(f"منبع پیدا نشد: {uri}")
                    
            except Exception as e:
                logger.error(f"خطا در خواندن منبع {uri}: {str(e)}")
                return ReadResourceResult(
                    contents=[TextContent(
                        type="text",
                        text=f"خطا در خواندن منبع: {str(e)}"
                    )]
                )
        
        # Tool handlers
        @self.server.list_tools()
        async def list_tools() -> ListToolsResult:
            """لیست ابزارهای موجود"""
            tools = [
                Tool(
                    name="search_projects",
                    description="جستجو در پروژه‌ها بر اساس عنوان، دسته‌بندی یا وضعیت",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "متن جستجو"
                            },
                            "category": {
                                "type": "string", 
                                "description": "دسته‌بندی پروژه"
                            },
                            "status": {
                                "type": "string",
                                "description": "وضعیت پروژه (open, in_progress, completed)"
                            },
                            "user_role": {
                                "type": "string",
                                "description": "نقش کاربر (client, contractor)"
                            }
                        }
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
                    name="get_user_projects",
                    description="دریافت پروژه‌های یک کاربر",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "integer",
                                "description": "شناسه کاربر"
                            },
                            "phone": {
                                "type": "string",
                                "description": "شماره تلفن کاربر"
                            }
                        }
                    }
                ),
                Tool(
                    name="analyze_projects",
                    description="تحلیل آماری پروژه‌ها",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "analysis_type": {
                                "type": "string",
                                "description": "نوع تحلیل (by_category, by_status, by_budget, by_location)",
                                "enum": ["by_category", "by_status", "by_budget", "by_location"]
                            }
                        },
                        "required": ["analysis_type"]
                    }
                ),
                Tool(
                    name="safe_query",
                    description="اجرای کوئری امن فقط خواندنی",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "کوئری SQL (فقط SELECT)"
                            }
                        },
                        "required": ["query"]
                    }
                )
            ]
            return ListToolsResult(tools=tools)
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """اجرای ابزارها"""
            try:
                logger.info(f"🔧 اجرای ابزار: {name} با پارامترهای: {arguments}")
                
                if name == "search_projects":
                    result = await self._search_projects(**arguments)
                elif name == "get_project_details":
                    result = await self._get_project_details(**arguments)
                elif name == "get_user_projects":
                    result = await self._get_user_projects(**arguments)
                elif name == "analyze_projects":
                    result = await self._analyze_projects(**arguments)
                elif name == "safe_query":
                    result = await self._safe_query(**arguments)
                else:
                    raise ValueError(f"ابزار نامعتبر: {name}")
                
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=json.dumps(result, ensure_ascii=False, indent=2, default=self._json_serializer)
                    )]
                )
                
            except Exception as e:
                logger.error(f"خطا در اجرای ابزار {name}: {str(e)}")
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"خطا در اجرای ابزار: {str(e)}"
                    )],
                    isError=True
                )
    
    async def _get_users_data(self) -> ReadResourceResult:
        """دریافت اطلاعات کاربران"""
        users = User.objects.all()[:MAX_QUERY_RESULTS]
        users_data = []
        
        for user in users:
            users_data.append({
                'id': user.id,
                'phone': user.phone,
                'name': user.name,
                'role': user.role,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'projects_count': user.project_set.count()
            })
        
        return ReadResourceResult(
            contents=[TextContent(
                type="text",
                text=json.dumps({
                    'total_users': len(users_data),
                    'users': users_data
                }, ensure_ascii=False, indent=2)
            )]
        )
    
    async def _get_projects_data(self) -> ReadResourceResult:
        """دریافت اطلاعات پروژه‌ها"""
        projects = Project.objects.select_related('user', 'category').all()[:MAX_QUERY_RESULTS]
        projects_data = []
        
        for project in projects:
            projects_data.append({
                'id': project.id,
                'title': project.title,
                'category': project.category.name if project.category else None,
                'user_phone': project.user.phone,
                'user_role': project.user.role,
                'status': project.status,
                'budget': project.budget,
                'service_location': project.service_location,
                'address': project.address,
                'created_at': project.created_at.isoformat() if project.created_at else None,
                'proposals_count': project.proposal_set.count()
            })
        
        return ReadResourceResult(
            contents=[TextContent(
                type="text",
                text=json.dumps({
                    'total_projects': len(projects_data),
                    'projects': projects_data
                }, ensure_ascii=False, indent=2)
            )]
        )
    
    async def _get_categories_data(self) -> ReadResourceResult:
        """دریافت اطلاعات دسته‌بندی‌ها"""
        categories = Category.objects.all()
        categories_data = []
        
        for category in categories:
            categories_data.append({
                'id': category.id,
                'name': category.name,
                'description': category.description,
                'parent_id': category.parent.id if category.parent else None,
                'projects_count': category.project_set.count()
            })
        
        return ReadResourceResult(
            contents=[TextContent(
                type="text",
                text=json.dumps({
                    'total_categories': len(categories_data),
                    'categories': categories_data
                }, ensure_ascii=False, indent=2)
            )]
        )
    
    async def _get_proposals_data(self) -> ReadResourceResult:
        """دریافت اطلاعات پیشنهادات"""
        proposals = Proposal.objects.select_related('project', 'contractor').all()[:MAX_QUERY_RESULTS]
        proposals_data = []
        
        for proposal in proposals:
            proposals_data.append({
                'id': proposal.id,
                'project_id': proposal.project.id,
                'project_title': proposal.project.title,
                'contractor_phone': proposal.contractor.phone,
                'price': proposal.price,
                'time': proposal.time,
                'submitted_at': proposal.submitted_at.isoformat() if proposal.submitted_at else None
            })
        
        return ReadResourceResult(
            contents=[TextContent(
                type="text",
                text=json.dumps({
                    'total_proposals': len(proposals_data),
                    'proposals': proposals_data
                }, ensure_ascii=False, indent=2)
            )]
        )
    
    async def _get_stats_data(self) -> ReadResourceResult:
        """دریافت آمار سیستم"""
        stats = {
            'users': {
                'total': User.objects.count(),
                'clients': User.objects.filter(role='client').count(),
                'contractors': User.objects.filter(role='contractor').count()
            },
            'projects': {
                'total': Project.objects.count(),
                'open': Project.objects.filter(status='open').count(),
                'in_progress': Project.objects.filter(status='in_progress').count(),
                'completed': Project.objects.filter(status='completed').count()
            },
            'proposals': {
                'total': Proposal.objects.count()
            },
            'categories': {
                'total': Category.objects.count()
            }
        }
        
        return ReadResourceResult(
            contents=[TextContent(
                type="text",
                text=json.dumps(stats, ensure_ascii=False, indent=2)
            )]
        )
    
    async def _search_projects(self, query: str = "", category: str = "", status: str = "", user_role: str = "") -> Dict[str, Any]:
        """جستجو در پروژه‌ها"""
        projects_qs = Project.objects.select_related('user', 'category').all()
        
        if query:
            projects_qs = projects_qs.filter(title__icontains=query)
        
        if category:
            projects_qs = projects_qs.filter(category__name__icontains=category)
        
        if status:
            projects_qs = projects_qs.filter(status=status)
        
        if user_role:
            projects_qs = projects_qs.filter(user__role=user_role)
        
        projects = projects_qs[:MAX_QUERY_RESULTS]
        
        results = []
        for project in projects:
            results.append({
                'id': project.id,
                'title': project.title,
                'category': project.category.name if project.category else None,
                'user_phone': project.user.phone,
                'user_role': project.user.role,
                'status': project.status,
                'budget': project.budget,
                'created_at': project.created_at.isoformat() if project.created_at else None
            })
        
        return {
            'query_params': {
                'query': query,
                'category': category,
                'status': status,
                'user_role': user_role
            },
            'total_found': len(results),
            'projects': results
        }
    
    async def _get_project_details(self, project_id: int) -> Dict[str, Any]:
        """دریافت جزئیات کامل پروژه"""
        try:
            project = Project.objects.select_related('user', 'category').get(id=project_id)
            proposals = project.proposal_set.select_related('contractor').all()
            
            project_data = {
                'id': project.id,
                'title': project.title,
                'description': project.description,
                'category': {
                    'id': project.category.id if project.category else None,
                    'name': project.category.name if project.category else None
                },
                'user': {
                    'id': project.user.id,
                    'phone': project.user.phone,
                    'name': project.user.name,
                    'role': project.user.role
                },
                'budget': project.budget,
                'service_location': project.service_location,
                'address': project.address,
                'status': project.status,
                'start_date': project.start_date,
                'deadline_date': project.deadline_date.isoformat() if project.deadline_date else None,
                'created_at': project.created_at.isoformat() if project.created_at else None,
                'proposals': []
            }
            
            for proposal in proposals:
                project_data['proposals'].append({
                    'id': proposal.id,
                    'contractor': {
                        'phone': proposal.contractor.phone,
                        'name': proposal.contractor.name
                    },
                    'price': proposal.price,
                    'time': proposal.time,
                    'submitted_at': proposal.submitted_at.isoformat() if proposal.submitted_at else None
                })
            
            return project_data
            
        except Project.DoesNotExist:
            raise ValueError(f"پروژه با شناسه {project_id} پیدا نشد")
    
    async def _get_user_projects(self, user_id: int = None, phone: str = None) -> Dict[str, Any]:
        """دریافت پروژه‌های یک کاربر"""
        try:
            if user_id:
                user = User.objects.get(id=user_id)
            elif phone:
                user = User.objects.get(phone=phone)
            else:
                raise ValueError("شناسه یا شماره تلفن کاربر الزامی است")
            
            projects = user.project_set.select_related('category').all()[:MAX_QUERY_RESULTS]
            
            user_data = {
                'user': {
                    'id': user.id,
                    'phone': user.phone,
                    'name': user.name,
                    'role': user.role
                },
                'projects': []
            }
            
            for project in projects:
                user_data['projects'].append({
                    'id': project.id,
                    'title': project.title,
                    'category': project.category.name if project.category else None,
                    'status': project.status,
                    'budget': project.budget,
                    'created_at': project.created_at.isoformat() if project.created_at else None,
                    'proposals_count': project.proposal_set.count()
                })
            
            return user_data
            
        except User.DoesNotExist:
            raise ValueError("کاربر پیدا نشد")
    
    async def _analyze_projects(self, analysis_type: str) -> Dict[str, Any]:
        """تحلیل آماری پروژه‌ها"""
        if analysis_type == "by_category":
            from django.db.models import Count
            analysis = list(Project.objects.values('category__name').annotate(count=Count('id')).order_by('-count'))
            return {
                'analysis_type': 'by_category',
                'data': analysis
            }
        
        elif analysis_type == "by_status":
            from django.db.models import Count
            analysis = list(Project.objects.values('status').annotate(count=Count('id')))
            return {
                'analysis_type': 'by_status',
                'data': analysis
            }
        
        elif analysis_type == "by_budget":
            from django.db.models import Avg, Min, Max, Count
            budget_stats = Project.objects.filter(budget__isnull=False).aggregate(
                avg_budget=Avg('budget'),
                min_budget=Min('budget'),
                max_budget=Max('budget'),
                count_with_budget=Count('budget')
            )
            return {
                'analysis_type': 'by_budget',
                'data': budget_stats
            }
        
        elif analysis_type == "by_location":
            from django.db.models import Count
            analysis = list(Project.objects.values('service_location').annotate(count=Count('id')))
            return {
                'analysis_type': 'by_location',
                'data': analysis
            }
        
        else:
            raise ValueError(f"نوع تحلیل نامعتبر: {analysis_type}")
    
    async def _safe_query(self, query: str) -> Dict[str, Any]:
        """اجرای کوئری امن فقط خواندنی"""
        # بررسی امنیتی کوئری
        query_lower = query.lower().strip()
        
        # تنها کوئری‌های SELECT مجاز هستند
        if not query_lower.startswith('select'):
            raise ValueError("تنها کوئری‌های SELECT مجاز هستند")
        
        # کلمات ممنوعه
        forbidden_words = ['delete', 'drop', 'insert', 'update', 'alter', 'create', 'truncate']
        for word in forbidden_words:
            if word in query_lower:
                raise ValueError(f"استفاده از کلمه {word} ممنوع است")
        
        # بررسی جداول مجاز
        tables_mentioned = []
        for table in ALLOWED_TABLES:
            if table in query_lower:
                tables_mentioned.append(table)
        
        if not tables_mentioned:
            raise ValueError("هیچ جدول مجاز در کوئری یافت نشد")
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(query)
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()[:MAX_QUERY_RESULTS]
                
            result = []
            for row in rows:
                result.append(dict(zip(columns, row)))
            
            return {
                'query': query,
                'columns': columns,
                'row_count': len(result),
                'data': result
            }
            
        except Exception as e:
            raise ValueError(f"خطا در اجرای کوئری: {str(e)}")
    
    def _json_serializer(self, obj):
        """سریالایزر برای انواع داده‌های خاص"""
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, Point):
            return {
                'latitude': obj.y,
                'longitude': obj.x
            }
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

async def main():
    """تابع اصلی سرور"""
    server_instance = BivasetMCPServer()
    
    # راه‌اندازی سرور
    async with server_instance.server.stdio() as streams:
        logger.info("🌟 Bivaset MCP Server is running...")
        await server_instance.server.run(
            streams[0], streams[1], server_instance.server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
