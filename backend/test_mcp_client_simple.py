#!/usr/bin/env python3
"""
Simple MCP Client Test
"""

import asyncio
import json
import subprocess
import sys
from typing import Any, Dict

async def test_mcp_server():
    """Test the MCP server using subprocess communication"""
    
    # Start the MCP server process
    process = subprocess.Popen(
        [sys.executable, "mcp_server_production.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # Send initialize request
        initialize_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "roots": {
                        "listChanged": True
                    },
                    "sampling": {}
                },
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        request_str = json.dumps(initialize_request) + "\n"
        print(f"Sending request: {request_str.strip()}")
        
        # Send the request
        process.stdin.write(request_str)
        process.stdin.flush()
        
        # Wait for response with timeout
        try:
            stdout, stderr = process.communicate(timeout=10)
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            print(f"Return code: {process.returncode}")
        except subprocess.TimeoutExpired:
            print("Process timed out")
            process.kill()
            stdout, stderr = process.communicate()
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            
    except Exception as e:
        print(f"Error: {e}")
        process.kill()

if __name__ == "__main__":
    asyncio.run(test_mcp_server())
