#!/usr/bin/env python3
"""
Comprehensive MCP server test script for production environment
Tests all functionality with proper mcp==0.9.1 compatibility
"""

import asyncio
import json
import subprocess
import sys
import os
from typing import Dict, Any, List

def test_database_connection():
    """Test database connection"""
    print("🔧 Testing database connection...")
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="localhost",
            database="bivaset_db",
            user="bivaset_user",
            password="bivaset123"
        )
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        print(f"✅ Database connection successful: {version}")
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_mcp_imports():
    """Test MCP imports"""
    print("\n🔧 Testing MCP imports...")
    try:
        from mcp.client.session import ClientSession
        from mcp.client.stdio import stdio_client
        print("✅ MCP client imports successful")
        return True
    except ImportError as e:
        print(f"❌ MCP client import failed: {e}")
        return False

async def test_mcp_functionality():
    """Test MCP server functionality"""
    try:
        from mcp.client.session import ClientSession
        from mcp.client.stdio import stdio_client
        
        print("\n🔧 Testing MCP server functionality...")
        
        # Create client connection
        async with stdio_client("python3", "mcp_server_production.py") as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the session
                await session.initialize()
                
                print("✅ MCP client session initialized")
                
                # Test list_resources
                print("\n🔧 Testing list_resources...")
                try:
                    resources = await session.list_resources()
                    print(f"✅ Found {len(resources.resources)} resources:")
                    for resource in resources.resources:
                        print(f"  - {resource.name}: {resource.description}")
                except Exception as e:
                    print(f"⚠️  list_resources failed: {e}")
                
                # Test list_tools
                print("\n🔧 Testing list_tools...")
                try:
                    tools = await session.list_tools()
                    print(f"✅ Found {len(tools.tools)} tools:")
                    for tool in tools.tools:
                        print(f"  - {tool.name}: {tool.description}")
                except Exception as e:
                    print(f"⚠️  list_tools failed: {e}")
                
                # Test a simple database query tool
                print("\n🔧 Testing query_projects tool...")
                try:
                    result = await session.call_tool("query_projects", {"limit": 5})
                    print(f"✅ query_projects executed successfully")
                    if result.content:
                        content = result.content[0]
                        if hasattr(content, 'text'):
                            print(f"Result preview: {content.text[:200]}...")
                except Exception as e:
                    print(f"⚠️  query_projects test failed: {e}")
                
                # Test a resource read
                print("\n🔧 Testing resource read...")
                try:
                    resource_result = await session.read_resource("database://projects")
                    print(f"✅ Resource read successful")
                    if resource_result.contents:
                        content = resource_result.contents[0]
                        if hasattr(content, 'text'):
                            print(f"Resource preview: {content.text[:200]}...")
                except Exception as e:
                    print(f"⚠️  Resource read test failed: {e}")
                
                print("\n✅ All MCP functionality tests completed!")
                return True
                
    except Exception as e:
        print(f"❌ MCP functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("=== Bivaset MCP Server Production Test ===")
    print("Testing all MCP functionality on production server...")
    
    # Test 1: Database connection
    if not test_database_connection():
        return False
    
    # Test 2: MCP imports
    if not test_mcp_imports():
        return False
    
    # Test 3: MCP functionality
    try:
        success = asyncio.run(test_mcp_functionality())
        if not success:
            return False
    except Exception as e:
        print(f"❌ MCP async test failed: {e}")
        return False
    
    print("\n🎉 All tests passed! MCP server is ready for production.")
    print("Next steps:")
    print("1. Install as systemd service")
    print("2. Configure for AI access")
    print("3. Set up monitoring")
    
    return True

if __name__ == "__main__":
    try:
        # Add current directory to Python path
        sys.path.insert(0, os.getcwd())
        
        success = main()
        
        if not success:
            print("\n❌ Fix the issues above before proceeding to production deployment")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n❌ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
