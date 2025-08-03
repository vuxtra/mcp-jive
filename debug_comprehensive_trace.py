#!/usr/bin/env python3
"""
Comprehensive debug script to trace the exact location of the NumPy boolean evaluation error.
This script will catch the ValueError and analyze the stack trace.
"""

import sys
import traceback
import asyncio
import os

# Add the src directory to Python path
sys.path.insert(0, '/Users/fbrbovic/Dev/mcp-jive/src')

from mcp_jive.config import ServerConfig
from mcp_jive.lancedb_manager import LanceDBManager
from mcp_jive.tools.task_management import TaskManagementTools

async def test_update_with_detailed_trace():
    """Test task update with detailed error tracing."""
    try:
        print("Initializing LanceDB...")
        config = ServerConfig()
        manager = LanceDBManager(config.lancedb)
        await manager.initialize()
        
        print("Initializing TaskManagementTools...")
        tools = TaskManagementTools(config, manager)
        
        print("Attempting task update...")
        result = await tools._update_task({
            "task_id": "c64b39b3-eb4c-44df-84f8-f3b38b7035a9",
            "status": "completed",
            "tags": ["test", "boolean-fix", "comprehensive-trace"]
        })
        
        print(f"Update result: {result}")
        return result
        
    except ValueError as e:
        if "truth value of an array" in str(e):
            print(f"\n=== CAUGHT NUMPY BOOLEAN EVALUATION ERROR ===")
            print(f"Error: {e}")
            print("\n=== DETAILED STACK TRACE ===")
            
            # Get the current exception info
            exc_type, exc_value, exc_traceback = sys.exc_info()
            
            # Print detailed stack trace
            stack_summary = traceback.extract_tb(exc_traceback)
            
            for i, frame in enumerate(stack_summary):
                print(f"\nFrame {i + 1}:")
                print(f"  File: {frame.filename}")
                print(f"  Line: {frame.lineno}")
                print(f"  Function: {frame.name}")
                print(f"  Code: {frame.line}")
                
                # If this is in our codebase, show more context
                if '/mcp-jive/src/' in frame.filename:
                    print(f"  *** THIS IS IN OUR CODEBASE ***")
                    try:
                        with open(frame.filename, 'r') as f:
                            lines = f.readlines()
                            start_line = max(0, frame.lineno - 3)
                            end_line = min(len(lines), frame.lineno + 2)
                            print(f"  Context (lines {start_line + 1}-{end_line}):")
                            for line_num in range(start_line, end_line):
                                marker = ">>>" if line_num + 1 == frame.lineno else "   "
                                print(f"  {marker} {line_num + 1:3d}: {lines[line_num].rstrip()}")
                    except Exception as file_error:
                        print(f"  Could not read file context: {file_error}")
                
                print("-" * 60)
            
            # Find the most likely culprit (last frame in our codebase)
            our_frames = [f for f in stack_summary if '/mcp-jive/src/' in f.filename]
            if our_frames:
                last_our_frame = our_frames[-1]
                print(f"\n=== MOST LIKELY CULPRIT ===")
                print(f"File: {last_our_frame.filename}")
                print(f"Line: {last_our_frame.lineno}")
                print(f"Function: {last_our_frame.name}")
                print(f"Code: {last_our_frame.line}")
            
            raise
        else:
            print(f"Different ValueError: {e}")
            raise
    
    except Exception as e:
        print(f"\nCaught different exception: {type(e).__name__}: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        raise

if __name__ == "__main__":
    print("Starting comprehensive NumPy boolean evaluation trace...")
    try:
        result = asyncio.run(test_update_with_detailed_trace())
        print(f"\nSuccess! Final result: {result}")
    except Exception as e:
        print(f"\nFinal exception: {type(e).__name__}: {e}")
        sys.exit(1)
