#!/usr/bin/env python3
try:
    from mcp.server import Server
    from mcp.types import Resource, Tool, TextContent, CallToolResult, ListResourcesResult, ListToolsResult, ReadResourceResult
    print("✅ All MCP imports successful")
    
    # Test basic server creation
    server = Server("test-server")
    print("✅ Server creation successful")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Other error: {e}")
