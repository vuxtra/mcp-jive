#!/usr/bin/env python3
"""Diagnostic script to identify MCP client configuration issues."""

import requests
import json
import sys
import subprocess
import time
from typing import Dict, Any, Optional

def check_server_health() -> bool:
    """Check if MCP server is running and healthy."""
    print("🔍 Checking server health...")
    try:
        response = requests.get("http://localhost:3454/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Server is healthy: {data}")
            return True
        else:
            print(f"❌ Server health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Is it running on port 3454?")
        return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_mcp_initialization() -> Optional[str]:
    """Test MCP initialization and return session ID."""
    print("\n🔍 Testing MCP initialization...")
    
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "clientInfo": {
                "name": "diagnostic-client",
                "version": "1.0.0"
            },
            "capabilities": {}
        }
    }
    
    try:
        response = requests.post(
            "http://localhost:3454/mcp",
            json=init_request,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            session_id = response.headers.get("mcp-session-id")
            if session_id:
                print(f"✅ Initialization successful! Session ID: {session_id}")
                return session_id
            else:
                print("❌ No session ID in response headers")
                return None
        else:
            print(f"❌ Initialization failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        return None

def test_tools_list(session_id: str) -> bool:
    """Test tools/list with session ID."""
    print("\n🔍 Testing tools/list...")
    
    tools_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    
    try:
        response = requests.post(
            "http://localhost:3454/mcp",
            json=tools_request,
            headers={
                "Content-Type": "application/json",
                "Mcp-Session-Id": session_id
            },
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            tools = data.get("result", {}).get("tools", [])
            print(f"✅ Tools list successful! Found {len(tools)} tools")
            
            # List all tools
            for i, tool in enumerate(tools, 1):
                name = tool.get("name", "unknown")
                desc = tool.get("description", "no description")
                print(f"  {i}. {name} - {desc[:60]}{'...' if len(desc) > 60 else ''}")
            
            return True
        else:
            print(f"❌ Tools list failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Tools list error: {e}")
        return False

def test_without_session() -> None:
    """Test what happens when calling tools/list without session."""
    print("\n🔍 Testing tools/list without session (should fail)...")
    
    tools_request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/list",
        "params": {}
    }
    
    try:
        response = requests.post(
            "http://localhost:3454/mcp",
            json=tools_request,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 400:
            print("✅ Correctly rejected request without session")
        else:
            print("⚠️  Unexpected response for request without session")
            
    except Exception as e:
        print(f"❌ Error testing without session: {e}")

def check_server_process() -> bool:
    """Check if server process is running."""
    print("\n🔍 Checking for server process...")
    try:
        result = subprocess.run(
            ["lsof", "-ti:3454"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            print(f"✅ Server process(es) found on port 3454: {pids}")
            return True
        else:
            print("❌ No process found on port 3454")
            return False
            
    except Exception as e:
        print(f"❌ Error checking process: {e}")
        return False

def print_configuration_guide() -> None:
    """Print the correct configuration guide."""
    print("\n📋 CORRECT MCP CLIENT CONFIGURATION:")
    print("\nFor VSCode/Cursor (.vscode/settings.json or .cursor/settings.json):")
    config = {
        "mcp.servers": {
            "mcp-jive": {
                "transport": {
                    "type": "http",
                    "url": "http://localhost:3454/mcp"
                }
            }
        }
    }
    print(json.dumps(config, indent=2))
    
    print("\n🔧 ALTERNATIVE CONFIGURATIONS:")
    print("\nWebSocket transport:")
    ws_config = {
        "mcp.servers": {
            "mcp-jive": {
                "transport": {
                    "type": "websocket",
                    "url": "ws://localhost:3454/mcp"
                }
            }
        }
    }
    print(json.dumps(ws_config, indent=2))
    
    print("\nStdio transport (legacy):")
    stdio_config = {
        "mcp.servers": {
            "mcp-jive": {
                "command": "/path/to/mcp-jive/bin/mcp-jive",
                "args": ["server", "start", "--mode", "stdio"],
                "cwd": "/path/to/mcp-jive"
            }
        }
    }
    print(json.dumps(stdio_config, indent=2))

def main():
    """Run complete diagnostic."""
    print("🚀 MCP Client Diagnostic Tool")
    print("=" * 50)
    
    # Step 1: Check server health
    if not check_server_health():
        print("\n❌ DIAGNOSIS: Server is not running or not accessible")
        print("\n🔧 SOLUTION: Start the server with:")
        print("   ./bin/mcp-jive server start")
        return False
    
    # Step 2: Check server process
    check_server_process()
    
    # Step 3: Test initialization
    session_id = test_mcp_initialization()
    if not session_id:
        print("\n❌ DIAGNOSIS: MCP initialization failed")
        print("\n🔧 SOLUTION: Check server logs for errors")
        return False
    
    # Step 4: Test tools list with session
    if not test_tools_list(session_id):
        print("\n❌ DIAGNOSIS: Tools list failed with valid session")
        print("\n🔧 SOLUTION: Check server logs and tool registry")
        return False
    
    # Step 5: Test without session (should fail)
    test_without_session()
    
    # Step 6: Print configuration guide
    print_configuration_guide()
    
    print("\n✅ DIAGNOSIS COMPLETE")
    print("\n🎯 CONCLUSION:")
    print("   The MCP server is working correctly.")
    print("   If you're still getting 'fetch failed' errors,")
    print("   the issue is likely in your MCP client configuration.")
    print("\n📖 Next steps:")
    print("   1. Verify your MCP client configuration matches the examples above")
    print("   2. Restart your IDE/MCP client")
    print("   3. Check MCP client logs for specific error messages")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)