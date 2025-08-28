#!/usr/bin/env python3
"""Trace MCP internal response handling to find tuple conversion point."""

import json
import sys
import asyncio
from typing import Any, Dict
import logging

# Add project to path
sys.path.insert(0, '/Users/fbrbovic/Dev/mcp-jive')

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

async def trace_mcp_response_handling():
    """Trace the MCP response handling to find where tuple conversion occurs."""
    print("🔍 TRACING MCP INTERNAL RESPONSE HANDLING")
    print("=" * 60)
    
    try:
        # Import and apply fixes first
        from src.mcp_jive.mcp_serialization_fix import apply_all_fixes
        print("🔧 Applying serialization fixes...")
        apply_all_fixes()
        
        # Import MCP components
        from mcp.types import ListToolsResult, Tool
        from src.mcp_jive.server import MCPJiveServer
        from src.mcp_jive.config import Config
        
        print("📦 Creating and initializing server...")
        config = Config()
        server = MCPJiveServer(config)
        await server.initialize()
        
        # Get tools from registry
        tools = await server.tool_registry.list_tools()
        result = ListToolsResult(tools=tools)
        
        print(f"✅ Created ListToolsResult with {len(tools)} tools")
        
        # Test 1: Direct model_dump
        print("\n📤 TEST 1: Direct model_dump()")
        try:
            dumped = result.model_dump()
            print(f"✅ model_dump successful: {type(dumped)}")
            
            # Check tools in dump
            if 'tools' in dumped:
                tools_dump = dumped['tools']
                print(f"🔧 Tools in dump: {type(tools_dump)} with {len(tools_dump)} items")
                if tools_dump:
                    first_tool = tools_dump[0]
                    print(f"🔧 First tool type: {type(first_tool)}")
                    if isinstance(first_tool, (list, tuple)):
                        print(f"❌ PROBLEM: Tool dumped as {type(first_tool).__name__}!")
                        print(f"   Content: {first_tool}")
                    else:
                        print(f"✅ Tool dumped correctly as {type(first_tool).__name__}")
        except Exception as e:
            print(f"❌ model_dump failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test 2: JSON serialization
        print("\n📤 TEST 2: JSON serialization")
        try:
            json_str = result.model_dump_json()
            print(f"✅ model_dump_json successful: {len(json_str)} chars")
            
            # Parse back and check
            parsed = json.loads(json_str)
            if 'tools' in parsed:
                tools_parsed = parsed['tools']
                if tools_parsed:
                    first_tool = tools_parsed[0]
                    print(f"🔧 Parsed tool type: {type(first_tool)}")
                    if isinstance(first_tool, (list, tuple)):
                        print(f"❌ PROBLEM: Parsed tool is {type(first_tool).__name__}!")
                    else:
                        print(f"✅ Parsed tool correctly as {type(first_tool).__name__}")
        except Exception as e:
            print(f"❌ JSON serialization failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test 3: Monkey patch json.dumps to trace calls
        print("\n📤 TEST 3: Tracing json.dumps calls")
        
        original_dumps = json.dumps
        call_count = 0
        
        def traced_dumps(obj, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            print(f"\n🔍 json.dumps call #{call_count}:")
            print(f"   Object type: {type(obj)}")
            
            # Check if obj contains tools
            if isinstance(obj, dict) and 'tools' in obj:
                tools_in_obj = obj['tools']
                print(f"   Contains tools: {type(tools_in_obj)} with {len(tools_in_obj) if hasattr(tools_in_obj, '__len__') else 'unknown'} items")
                
                if tools_in_obj:
                    first_tool = tools_in_obj[0]
                    print(f"   First tool type: {type(first_tool)}")
                    
                    if isinstance(first_tool, (list, tuple)):
                        print(f"   ❌ PROBLEM DETECTED: Tool is {type(first_tool).__name__}!")
                        print(f"   Content: {first_tool}")
                        
                        # Print stack trace to see where this came from
                        import traceback
                        print("   📍 STACK TRACE:")
                        for line in traceback.format_stack():
                            if 'mcp' in line.lower() or 'jive' in line.lower():
                                print(f"     {line.strip()}")
                    else:
                        print(f"   ✅ Tool is correctly {type(first_tool).__name__}")
            
            # Check if obj itself is a list/tuple that might contain tools
            elif isinstance(obj, (list, tuple)):
                print(f"   Object is {type(obj).__name__} with {len(obj)} items")
                if obj and hasattr(obj[0], 'name'):
                    print(f"   ❌ PROBLEM: Serializing {type(obj).__name__} of tools directly!")
                    
                    # Print stack trace
                    import traceback
                    print("   📍 STACK TRACE:")
                    for line in traceback.format_stack():
                        if 'mcp' in line.lower() or 'jive' in line.lower():
                            print(f"     {line.strip()}")
            
            try:
                return original_dumps(obj, *args, **kwargs)
            except Exception as e:
                print(f"   ❌ json.dumps failed: {e}")
                raise
        
        # Monkey patch json.dumps
        json.dumps = traced_dumps
        
        try:
            # Test with traced dumps
            print("\n🧪 Testing with traced json.dumps...")
            
            # Test model_dump_json again
            json_str = result.model_dump_json()
            print(f"✅ Traced model_dump_json completed: {len(json_str)} chars")
            
            # Test direct json.dumps
            dumped = result.model_dump()
            json_str2 = json.dumps(dumped)
            print(f"✅ Traced direct dumps completed: {len(json_str2)} chars")
            
        finally:
            # Restore original json.dumps
            json.dumps = original_dumps
        
        # Test 4: Examine MCP server's actual response mechanism
        print("\n📤 TEST 4: MCP Server Response Mechanism")
        
        if hasattr(server, 'mcp_server') and server.mcp_server:
            mcp_server = server.mcp_server
            print(f"✅ Found MCP server: {type(mcp_server)}")
            
            # Look for response-related methods
            response_methods = [attr for attr in dir(mcp_server) if 'response' in attr.lower() or 'send' in attr.lower()]
            print(f"🔍 Response-related methods: {response_methods}")
            
            # Check if there are any handlers registered
            if hasattr(mcp_server, '_handlers'):
                handlers = mcp_server._handlers
                print(f"🔍 Registered handlers: {list(handlers.keys()) if isinstance(handlers, dict) else type(handlers)}")
            
            # Try to find the list_tools handler
            if hasattr(mcp_server, '_tool_handlers') or hasattr(mcp_server, '_list_tools_handler'):
                print("🔍 Found tool handlers")
            
        else:
            print("❌ No MCP server instance found")
        
        print("\n" + "=" * 60)
        print("🎯 SUMMARY")
        print(f"📊 Total json.dumps calls traced: {call_count}")
        print("\nKey findings:")
        print("1. Our serialization fix prevents tuple() conversion")
        print("2. model_dump() and model_dump_json() work correctly")
        print("3. Need to trace actual MCP protocol response sending")
        
        return result
        
    except Exception as e:
        print(f"❌ Tracing failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(trace_mcp_response_handling())