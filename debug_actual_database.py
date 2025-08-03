#!/usr/bin/env python3
"""
Debug which database is actually being used during work item creation.
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mcp_jive.tools.client_tools import MCPClientTools
from mcp_jive.config import ServerConfig
from mcp_jive.lancedb_manager import LanceDBManager, DatabaseConfig

async def debug_actual_database():
    """Debug which database is actually being used."""
    
    print("=== Debugging Actual Database Usage ===\n")
    
    # Initialize the same way the MCP Server does
    config = ServerConfig()
    
    # Create LanceDB configuration (same as server)
    db_config = DatabaseConfig(
        data_path=getattr(config, 'lancedb_data_path', './data/lancedb_jive'),
        embedding_model=getattr(config, 'lancedb_embedding_model', 'all-MiniLM-L6-v2'),
        device=getattr(config, 'lancedb_device', 'cpu')
    )
    
    print(f"Database path: {db_config.data_path}")
    
    # Initialize LanceDB manager
    lancedb_manager = LanceDBManager(db_config)
    await lancedb_manager.initialize()
    
    # Check WorkItem table schema
    table = lancedb_manager.get_table('WorkItem')
    field_names = [field.name for field in table.schema]
    
    print(f"WorkItem table fields: {field_names}")
    print(f"Has 'item_id': {'item_id' in field_names}")
    
    # Initialize client tools (same as server)
    client_tools = MCPClientTools(config, lancedb_manager)
    await client_tools.initialize()
    
    # Test work item creation directly
    print("\nTesting work item creation directly...")
    try:
        result = await client_tools.create_work_item({
            "type": "task",
            "title": "Direct Test Work Item",
            "description": "Testing direct work item creation",
            "priority": "medium"
        })
        print(f"Success: {result}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Check if the work item was actually created
    print("\nChecking if work item was created...")
    try:
        work_items = await lancedb_manager.list_work_items(limit=5)
        print(f"Total work items: {len(work_items)}")
        for item in work_items[-2:]:
            print(f"  - {item.get('title', 'No title')} (ID: {item.get('id', 'No ID')})")
    except Exception as e:
        print(f"Error listing work items: {e}")
    
    await lancedb_manager.cleanup()

if __name__ == "__main__":
    asyncio.run(debug_actual_database())