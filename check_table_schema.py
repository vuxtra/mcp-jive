#!/usr/bin/env python3
"""
Check the current LanceDB table schema to understand the schema mismatch.
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mcp_jive.lancedb_manager import LanceDBManager, DatabaseConfig

async def check_schema():
    """Check the current WorkItem table schema."""
    
    print("=== Checking LanceDB Table Schema ===\n")
    
    # Initialize MCP Jive LanceDB manager
    config = DatabaseConfig(data_path='./data/lancedb_jive')
    manager = LanceDBManager(config)
    await manager.initialize()
    
    try:
        # Get the WorkItem table
        table = manager.get_table('WorkItem')
        
        print("Current WorkItem table schema:")
        print(table.schema)
        print("\n=== Field Names ===")
        for field in table.schema:
            print(f"- {field.name}: {field.type}")
            
        # Check if item_id exists
        field_names = [field.name for field in table.schema]
        print(f"\nHas 'item_id' field: {'item_id' in field_names}")
        print(f"Has 'id' field: {'id' in field_names}")
        
        # Count existing records
        try:
            count = table.count_rows()
            print(f"\nExisting records: {count}")
        except Exception as e:
            print(f"\nCould not count records: {e}")
            
    except Exception as e:
        print(f"Error accessing table: {e}")
        import traceback
        traceback.print_exc()
    
    await manager.cleanup()

if __name__ == "__main__":
    asyncio.run(check_schema())