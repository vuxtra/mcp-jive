#!/usr/bin/env python3
"""
Debug script to use the exact same configuration as the MCP server.
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from mcp_jive.config import ServerConfig
from mcp_jive.lancedb_manager import LanceDBManager, DatabaseConfig

async def debug_server_config():
    """Debug using the exact same config as the MCP server."""
    
    print("=== Using MCP Server Configuration ===")
    
    # Create the same config as the server
    server_config = ServerConfig()
    
    # Create LanceDB configuration exactly like the server does
    db_config = DatabaseConfig(
        data_path=getattr(server_config, 'lancedb_data_path', './data/lancedb'),
        embedding_model=getattr(server_config, 'lancedb_embedding_model', 'all-MiniLM-L6-v2'),
        device=getattr(server_config, 'lancedb_device', 'cpu')
    )
    
    print(f"Database path: {db_config.data_path}")
    print(f"Embedding model: {db_config.embedding_model}")
    print(f"Device: {db_config.device}")
    print(f"Current working directory: {os.getcwd()}")
    
    # Initialize LanceDB manager exactly like the server
    manager = LanceDBManager(db_config)
    await manager.initialize()
    
    # Test list_work_items
    print(f"\n=== Testing list_work_items ===")
    try:
        items = await manager.list_work_items(limit=10)
        print(f"Found {len(items)} work items")
        
        for item in items:
            print(f"  ID: {item.get('id', 'N/A')}")
            print(f"  Title: {item.get('title', 'N/A')}")
            print(f"  Parent ID: {item.get('parent_id', 'N/A')}")
            print(f"  Type: {item.get('item_type', 'N/A')}")
            print()
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test get_work_item_children
    print(f"\n=== Testing get_work_item_children ===")
    target_parent_id = "0b6cdcfc-3d1e-400d-9e75-dcd254cde8b0"
    try:
        children = await manager.get_work_item_children(target_parent_id)
        print(f"Found {len(children)} children for {target_parent_id}")
        
        for child in children:
            print(f"  - {child.get('title')} ({child.get('id')})")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_server_config())