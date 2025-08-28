#!/usr/bin/env python3
"""Simple test to verify MCP server handles requests without tuple errors."""

import json
import sys
import subprocess
import time
import threading
import queue

def read_output(process, output_queue):
    """Read output from process in a separate thread."""
    try:
        while True:
            line = process.stdout.readline()
            if not line:
                break
            output_queue.put(line.strip())
    except Exception as e:
        output_queue.put(f"ERROR: {e}")

def test_mcp_with_initialization():
    """Test MCP server with proper initialization handshake."""
    process = None
    try:
        # Start MCP server process
        process = subprocess.Popen(
            [sys.executable, '-m', 'src.mcp_jive.server', '--stdio'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0,  # Unbuffered
            cwd='/Users/fbrbovic/Dev/mcp-jive'
        )
        
        # Set up output reading thread
        output_queue = queue.Queue()
        output_thread = threading.Thread(target=read_output, args=(process, output_queue))
        output_thread.daemon = True
        output_thread.start()
        
        # Give the server a moment to start
        time.sleep(3)
        
        # Step 1: Send initialization request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        init_json = json.dumps(init_request) + "\n"
        print(f"Sending initialization...")
        
        # Send initialization
        process.stdin.write(init_json)
        process.stdin.flush()
        
        # Wait for initialization response
        time.sleep(2)
        
        # Step 2: Send initialized notification
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        }
        
        initialized_json = json.dumps(initialized_notification) + "\n"
        print(f"Sending initialized notification...")
        
        process.stdin.write(initialized_json)
        process.stdin.flush()
        
        time.sleep(1)
        
        # Step 3: Send list_tools request
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        tools_json = json.dumps(tools_request) + "\n"
        print(f"Sending tools request...")
        
        process.stdin.write(tools_json)
        process.stdin.flush()
        
        # Wait for responses and collect output
        time.sleep(3)
        
        # Collect all output
        responses = []
        while not output_queue.empty():
            try:
                line = output_queue.get_nowait()
                if line and line.strip():
                    responses.append(line)
            except queue.Empty:
                break
        
        # Get stderr
        stderr_output = ""
        try:
            # Non-blocking read of stderr
            process.stderr.settimeout(0.1)
            stderr_output = process.stderr.read()
        except:
            pass
        
        print(f"\nReceived {len(responses)} response lines")
        if stderr_output:
            print(f"Stderr: {stderr_output}")
        
        # Check for tuple errors in stderr
        if stderr_output and "tuple" in stderr_output.lower() and "attribute" in stderr_output.lower():
            print("❌ FAILED: Tuple error detected in stderr")
            return False
        
        # Parse responses
        tools_response = None
        for response_line in responses:
            if response_line.startswith('{'):
                try:
                    response = json.loads(response_line)
                    if response.get('id') == 2:  # This is our tools/list response
                        tools_response = response
                        break
                except json.JSONDecodeError:
                    continue
        
        if tools_response:
            if "error" in tools_response:
                print(f"❌ FAILED: MCP Error - {tools_response['error']}")
                return False
            elif "result" in tools_response and "tools" in tools_response["result"]:
                tools = tools_response["result"]["tools"]
                print(f"✅ SUCCESS: Received {len(tools)} tools")
                
                # Check first few tools
                for i, tool in enumerate(tools[:3]):
                    if isinstance(tool, dict) and "name" in tool:
                        print(f"  Tool {i+1}: {tool['name']}")
                    else:
                        print(f"❌ FAILED: Tool {i+1} has invalid structure: {tool}")
                        return False
                
                return True
            else:
                print(f"❌ FAILED: Unexpected response structure: {tools_response}")
                return False
        else:
            print("❌ FAILED: No tools response found")
            print(f"All responses: {responses}")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: Exception - {e}")
        return False
    finally:
        if process and process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                process.kill()

if __name__ == "__main__":
    print("Testing MCP server with proper initialization...")
    result = test_mcp_with_initialization()
    
    if result:
        print("\n🎉 SUCCESS: MCP server is working correctly!")
        sys.exit(0)
    else:
        print("\n❌ FAILED: MCP server has issues")
        sys.exit(1)