#!/usr/bin/env python3
"""Intercept and analyze actual JSON being transmitted over MCP protocol."""

import json
import sys
import subprocess
import time
import threading
import queue
import os

# Add project to path
sys.path.insert(0, '/Users/fbrbovic/Dev/mcp-jive')

def capture_mcp_communication():
    """Capture the actual JSON communication between MCP client and server."""
    process = None
    try:
        print("🔍 Starting MCP server to intercept JSON communication...")
        
        # Start MCP server process
        process = subprocess.Popen(
            [sys.executable, '-m', 'src.mcp_jive.server', '--stdio'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0,
            cwd='/Users/fbrbovic/Dev/mcp-jive'
        )
        
        # Give server time to start
        time.sleep(3)
        
        print("📤 Sending MCP initialization sequence...")
        
        # Step 1: Initialize
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "debug-client", "version": "1.0.0"}
            }
        }
        
        init_json = json.dumps(init_request, indent=2) + "\n"
        print(f"📤 SENDING INIT:\n{init_json}")
        
        process.stdin.write(init_json)
        process.stdin.flush()
        
        # Read init response
        time.sleep(1)
        
        # Step 2: Initialized notification
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        }
        
        initialized_json = json.dumps(initialized_notification) + "\n"
        print(f"📤 SENDING INITIALIZED:\n{initialized_json}")
        
        process.stdin.write(initialized_json)
        process.stdin.flush()
        
        time.sleep(1)
        
        # Step 3: List tools request
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        tools_json = json.dumps(tools_request, indent=2) + "\n"
        print(f"📤 SENDING TOOLS REQUEST:\n{tools_json}")
        
        process.stdin.write(tools_json)
        process.stdin.flush()
        
        # Wait for response
        time.sleep(2)
        
        # Read all available output
        print("\n📥 READING SERVER RESPONSES...")
        
        # Set non-blocking mode for stdout
        import fcntl
        import os
        fd = process.stdout.fileno()
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
        
        responses = []
        try:
            while True:
                try:
                    line = process.stdout.readline()
                    if not line:
                        break
                    if line.strip():
                        responses.append(line.strip())
                except:
                    break
        except:
            pass
        
        print(f"\n📥 RECEIVED {len(responses)} RESPONSE LINES:")
        
        for i, response in enumerate(responses):
            print(f"\n--- RESPONSE {i+1} ---")
            print(response)
            
            # Try to parse and analyze
            if response.startswith('{'):
                try:
                    parsed = json.loads(response)
                    print(f"✅ PARSED JSON: {type(parsed)}")
                    
                    if parsed.get('id') == 2:  # This is our tools/list response
                        print("🎯 FOUND TOOLS LIST RESPONSE!")
                        
                        if 'result' in parsed:
                            result = parsed['result']
                            print(f"📋 Result type: {type(result)}")
                            print(f"📋 Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
                            
                            if 'tools' in result:
                                tools = result['tools']
                                print(f"🔧 Tools type: {type(tools)}")
                                print(f"🔧 Tools length: {len(tools) if hasattr(tools, '__len__') else 'No length'}")
                                
                                if isinstance(tools, list) and len(tools) > 0:
                                    first_tool = tools[0]
                                    print(f"🔧 First tool type: {type(first_tool)}")
                                    print(f"🔧 First tool content: {first_tool}")
                                    
                                    if isinstance(first_tool, (list, tuple)):
                                        print("❌ PROBLEM FOUND: Tool is a list/tuple instead of dict!")
                                        print(f"❌ Tuple content: {list(first_tool)}")
                                    elif isinstance(first_tool, dict):
                                        print(f"✅ Tool is dict with keys: {list(first_tool.keys())}")
                                        if 'name' in first_tool:
                                            print(f"✅ Tool name: {first_tool['name']}")
                                        else:
                                            print("❌ Tool dict missing 'name' key")
                                    else:
                                        print(f"❌ Tool is unexpected type: {type(first_tool)}")
                                        
                                # Check all tools
                                print(f"\n🔧 ANALYZING ALL {len(tools)} TOOLS:")
                                for j, tool in enumerate(tools[:3]):  # Check first 3
                                    print(f"  Tool {j}: {type(tool)} - {tool if not isinstance(tool, dict) else f'dict with keys: {list(tool.keys())}'}")                                    
                            else:
                                print("❌ No 'tools' key in result")
                        else:
                            print("❌ No 'result' key in response")
                            if 'error' in parsed:
                                print(f"❌ Error in response: {parsed['error']}")
                                
                except json.JSONDecodeError as e:
                    print(f"❌ Failed to parse JSON: {e}")
                    print(f"Raw response: {response[:200]}...")
        
        # Get stderr
        try:
            stderr_output = process.stderr.read()
            if stderr_output:
                print(f"\n📥 STDERR OUTPUT:\n{stderr_output}")
        except:
            pass
            
        return responses
        
    except Exception as e:
        print(f"❌ Exception during interception: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        if process and process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                process.kill()

def analyze_serialization_pathway():
    """Analyze the MCP serialization pathway to understand tuple conversion."""
    print("\n🔬 ANALYZING MCP SERIALIZATION PATHWAY...")
    
    try:
        from mcp.types import ListToolsResult, Tool
        from src.mcp_jive.mcp_serialization_fix import apply_all_fixes
        
        print("📦 Creating test objects...")
        
        # Create test tool
        tool = Tool(
            name="test_tool",
            description="A test tool",
            inputSchema={"type": "object", "properties": {}, "required": []}
        )
        
        # Create test result
        result = ListToolsResult(tools=[tool], nextCursor=None)
        
        print(f"✅ Created Tool: {type(tool)}")
        print(f"✅ Created ListToolsResult: {type(result)}")
        
        # Test before fixes
        print("\n🧪 TESTING BEFORE FIXES:")
        try:
            tool_tuple = tuple(tool)
            print(f"❌ Tool tuple conversion works: {len(tool_tuple)} items")
            print(f"   First few items: {list(tool_tuple)[:3]}")
        except Exception as e:
            print(f"✅ Tool tuple conversion fails: {e}")
        
        # Apply fixes
        print("\n🔧 APPLYING FIXES...")
        apply_all_fixes()
        
        # Test after fixes
        print("\n🧪 TESTING AFTER FIXES:")
        try:
            tool_tuple = tuple(tool)
            print(f"❌ Tool tuple conversion still works: {len(tool_tuple)} items")
        except Exception as e:
            print(f"✅ Tool tuple conversion now fails: {e}")
        
        # Test JSON serialization
        print("\n📤 TESTING JSON SERIALIZATION:")
        
        # Method 1: model_dump_json
        try:
            json_output = result.model_dump_json()
            print(f"✅ model_dump_json works: {len(json_output)} chars")
            
            # Parse it back
            parsed = json.loads(json_output)
            tools_in_json = parsed.get('tools', [])
            if tools_in_json:
                first_tool_in_json = tools_in_json[0]
                print(f"📋 First tool in JSON: {type(first_tool_in_json)}")
                print(f"📋 First tool content: {first_tool_in_json}")
                
                if isinstance(first_tool_in_json, (list, tuple)):
                    print("❌ PROBLEM: Tool serialized as list/tuple!")
                elif isinstance(first_tool_in_json, dict):
                    print(f"✅ Tool serialized as dict with keys: {list(first_tool_in_json.keys())}")
            
        except Exception as e:
            print(f"❌ model_dump_json failed: {e}")
        
        # Method 2: json.dumps with default
        try:
            json_output = json.dumps(result, default=str)
            print(f"✅ json.dumps works: {len(json_output)} chars")
        except Exception as e:
            print(f"❌ json.dumps failed: {e}")
            
    except Exception as e:
        print(f"❌ Serialization analysis failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 MCP JSON INTERCEPTION AND ANALYSIS")
    print("=" * 50)
    
    # First analyze the serialization pathway
    analyze_serialization_pathway()
    
    print("\n" + "=" * 50)
    
    # Then capture actual MCP communication
    responses = capture_mcp_communication()
    
    print("\n" + "=" * 50)
    print("🎯 SUMMARY")
    print(f"📥 Captured {len(responses)} responses")
    print("\nNext steps:")
    print("1. Check if tools are serialized as tuples in the JSON")
    print("2. Verify if our fixes are actually being applied")
    print("3. Identify the exact point where tuple conversion happens")