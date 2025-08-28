#!/usr/bin/env python3
"""Direct verification of MCP server response format."""

import asyncio
import json
import sys
import os
from typing import List, Dict, Any

# Ensure we're in the right directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import ListToolsRequest, ListToolsResult, Tool

# Import our server components
from src.mcp_jive.server import create_tool_registry
from src.mcp_jive.config import ServerConfig
from src.mcp_jive.lancedb_manager import LanceDBManager, DatabaseConfig

# Import and apply fixes
from src.mcp_jive.mcp_serialization_fix import apply_all_fixes
apply_all_fixes()


async def test_server_response():
    """Test what the server actually returns for tools/list."""
    
    print("🧪 Testing MCP Server Response Format")
    print("=" * 50)
    
    # Create server components
    config = ServerConfig()
    db_config = DatabaseConfig(data_path='./data/lancedb_jive')
    lancedb_manager = LanceDBManager(db_config)
    
    # Create tool registry
    tool_registry = create_tool_registry(config, lancedb_manager)
    
    # Create MCP server
    server = Server("mcp-jive-test")
    
    # Register handlers
    @server.list_tools()
    async def handle_list_tools() -> ListToolsResult:
        """Handle tools/list request."""
        tools = tool_registry.list_tools()
        print(f"🔍 Server found {len(tools)} tools")
        
        # Print first tool details
        if tools:
            first_tool = tools[0]
            print(f"🔍 First tool type: {type(first_tool)}")
            print(f"🔍 First tool name: {first_tool.name}")
            
            # Test serialization
            try:
                dumped = first_tool.model_dump()
                print(f"🔍 Serialized type: {type(dumped)}")
                print(f"🔍 Serialized keys: {list(dumped.keys())}")
            except Exception as e:
                print(f"❌ Serialization error: {e}")
        
        result = ListToolsResult(tools=tools)
        print(f"🔍 Result type: {type(result)}")
        print(f"🔍 Result tools type: {type(result.tools)}")
        print(f"🔍 Result tools count: {len(result.tools)}")
        
        # Test full serialization
        try:
            serialized = result.model_dump_json()
            parsed = json.loads(serialized)
            print(f"🔍 Full response JSON length: {len(serialized)}")
            print(f"🔍 Parsed tools count: {len(parsed.get('tools', []))}")
            
            if parsed.get('tools'):
                first_parsed = parsed['tools'][0]
                print(f"🔍 First parsed tool type: {type(first_parsed)}")
                print(f"🔍 First parsed tool name: {first_parsed.get('name')}")
        except Exception as e:
            print(f"❌ Full serialization error: {e}")
        
        return result
    
    # Start server and test
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(test_server_response())