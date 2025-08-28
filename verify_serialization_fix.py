#!/usr/bin/env python3
"""Verify that the MCP serialization fix prevents tuple conversion."""

import json
import sys
import os

# Add the project root to the path
sys.path.insert(0, '/Users/fbrbovic/Dev/mcp-jive')

def test_serialization_fix():
    """Test that the serialization fix prevents tuple conversion."""
    try:
        # Import MCP types
        from mcp.types import ListToolsResult, Tool
        
        # Import and apply our fix
        from src.mcp_jive.mcp_serialization_fix import apply_all_fixes
        apply_all_fixes()
        
        print("✅ Successfully applied serialization fixes")
        
        # Create test objects
        tool = Tool(
            name="test_tool",
            description="A test tool",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
        
        result = ListToolsResult(
            tools=[tool],
            nextCursor=None
        )
        
        print(f"Created test objects: Tool and ListToolsResult")
        
        # Test 1: Check that tuple() doesn't work (should raise an error or return empty)
        try:
            tool_tuple = tuple(tool)
            if len(tool_tuple) == 0:
                print("✅ Tool.__iter__ successfully patched - tuple() returns empty")
            else:
                print(f"❌ Tool.__iter__ not properly patched - tuple() returned: {tool_tuple}")
                return False
        except Exception as e:
            print(f"✅ Tool.__iter__ successfully patched - tuple() raises: {type(e).__name__}")
        
        try:
            result_tuple = tuple(result)
            if len(result_tuple) == 0:
                print("✅ ListToolsResult.__iter__ successfully patched - tuple() returns empty")
            else:
                print(f"❌ ListToolsResult.__iter__ not properly patched - tuple() returned: {result_tuple}")
                return False
        except Exception as e:
            print(f"✅ ListToolsResult.__iter__ successfully patched - tuple() raises: {type(e).__name__}")
        
        # Test 2: Check that JSON serialization works
        try:
            tool_json = json.dumps(tool, default=str)
            print(f"✅ Tool JSON serialization works: {len(tool_json)} chars")
        except Exception as e:
            print(f"❌ Tool JSON serialization failed: {e}")
            return False
        
        try:
            result_json = json.dumps(result, default=str)
            print(f"✅ ListToolsResult JSON serialization works: {len(result_json)} chars")
        except Exception as e:
            print(f"❌ ListToolsResult JSON serialization failed: {e}")
            return False
        
        # Test 3: Check that model_dump works
        try:
            tool_dict = tool.model_dump()
            print(f"✅ Tool.model_dump() works: {len(tool_dict)} fields")
        except Exception as e:
            print(f"❌ Tool.model_dump() failed: {e}")
            return False
        
        try:
            result_dict = result.model_dump()
            print(f"✅ ListToolsResult.model_dump() works: {len(result_dict)} fields")
        except Exception as e:
            print(f"❌ ListToolsResult.model_dump() failed: {e}")
            return False
        
        # Test 4: Simulate what happens during MCP serialization
        try:
            # This is what the MCP library does internally
            serialized = result.model_dump_json()
            parsed_back = json.loads(serialized)
            
            if isinstance(parsed_back, dict) and "tools" in parsed_back:
                tools_list = parsed_back["tools"]
                if isinstance(tools_list, list) and len(tools_list) > 0:
                    first_tool = tools_list[0]
                    if isinstance(first_tool, dict) and "name" in first_tool:
                        print(f"✅ MCP-style serialization works: tool name = {first_tool['name']}")
                    else:
                        print(f"❌ MCP-style serialization failed: tool is not dict with name: {first_tool}")
                        return False
                else:
                    print(f"❌ MCP-style serialization failed: tools is not a proper list: {tools_list}")
                    return False
            else:
                print(f"❌ MCP-style serialization failed: result is not dict with tools: {parsed_back}")
                return False
        except Exception as e:
            print(f"❌ MCP-style serialization failed: {e}")
            return False
        
        print("\n🎉 ALL TESTS PASSED! Serialization fix is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Verifying MCP serialization fix...")
    success = test_serialization_fix()
    
    if success:
        print("\n✅ SUCCESS: MCP serialization fix is working!")
        sys.exit(0)
    else:
        print("\n❌ FAILED: MCP serialization fix has issues")
        sys.exit(1)