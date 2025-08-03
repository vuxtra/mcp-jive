#!/usr/bin/env python3
"""
Test which database the MCP Server is actually using.
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mcp_jive.server import MCPServer
from mcp_jive.config import ServerConfig

async def test_mcp_server_database():
    """Test which database the MCP Server is actually using."""
    
    print("=== Testing MCP Server Database Configuration ===\n")
    
    # Initialize MCP Server the same way as main.py
    config = ServerConfig()
    server = MCPServer(config)
    
    try:
        # Start the server (this initializes the database)
        await server.start()
        
        # Check the database configuration
        if server.lancedb_manager:
            print(f"LanceDB Manager Type: {type(server.lancedb_manager)}")
            print(f"Database Path: {server.lancedb_manager.config.data_path}")
            
            # Check WorkItem table schema
            table = server.lancedb_manager.get_table('WorkItem')
            field_names = [field.name for field in table.schema]
            
            print(f"WorkItem table fields: {field_names}")
            print(f"Has 'item_id': {'item_id' in field_names}")
            print(f"Record count: {table.count_rows()}")
            
            # Test work item creation through the server's tools
            if server.tool_registry and server.tool_registry.client_tools:
                print("\nTesting work item creation through MCP Server tools...")
                try:
                    result = await server.tool_registry.client_tools.handle_tool_call(
                        "jive_create_work_item",
                        {
                            "type": "task",
                            "title": "MCP Server Test Work Item",
                            "description": "Testing work item creation through MCP Server",
                            "priority": "medium"
                        }
                    )
                    print(f"Success: {result[0].text[:200]}...")
                except Exception as e:
                    print(f"Error: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print("\nTool registry or client tools not available")
        else:
            print("LanceDB Manager not initialized")
            
    except Exception as e:
        print(f"Error initializing MCP Server: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        try:
            await server.shutdown()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(test_mcp_server_database())