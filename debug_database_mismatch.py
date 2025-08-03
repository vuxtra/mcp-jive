#!/usr/bin/env python3
"""
Debug script to identify which LanceDB instance contains the work items
and resolve the database mismatch between MCP Jive and MCP Server managers.
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from mcp_server.lancedb_manager import LanceDBManager as ServerLanceDBManager, DatabaseConfig as ServerDatabaseConfig
from mcp_jive.lancedb_manager import LanceDBManager as JiveLanceDBManager, DatabaseConfig as JiveDatabaseConfig

async def debug_database_mismatch():
    print("=== Database Mismatch Debug ===\n")
    
    # Check MCP Server Database (used by workflow engine)
    print("1. MCP Server Database (./data/lancedb_jive):")
    try:
        server_config = ServerDatabaseConfig(
            data_path='./data/lancedb_jive',
            embedding_model='all-MiniLM-L6-v2',
            device='cpu'
        )
        server_mgr = ServerLanceDBManager(server_config)
        await server_mgr.initialize()
        
        print(f"   Tables: {server_mgr.list_tables()}")
        
        # Check WorkItem table
        if 'WorkItem' in server_mgr.list_tables():
            work_items = await server_mgr.list_work_items(limit=10)
            print(f"   Work items found: {len(work_items)}")
            if work_items:
                for item in work_items[:3]:
                    print(f"     - {item.get('id', 'N/A')}: {item.get('title', 'N/A')}")
        
        await server_mgr.cleanup()
    except Exception as e:
        print(f"   Error: {e}")
    
    # Check MCP Jive Database (used by client tools)
    print("\n2. MCP Jive Database (./data/lancedb_jive):")
    try:
        jive_config = JiveDatabaseConfig(
            data_path='./data/lancedb_jive',
            embedding_model='all-MiniLM-L6-v2',
            device='cpu'
        )
        jive_mgr = JiveLanceDBManager(jive_config)
        await jive_mgr.initialize()
        
        print(f"   Tables: {jive_mgr.list_tables()}")
        
        # Check WorkItem table
        if 'WorkItem' in jive_mgr.list_tables():
            # Get table directly and query
            table = jive_mgr.get_table('WorkItem')
            df = table.search().limit(10).to_pandas()
            print(f"   Work items found: {len(df)}")
            if len(df) > 0:
                for _, row in df.head(3).iterrows():
                    print(f"     - {row.get('id', 'N/A')}: {row.get('title', 'N/A')}")
        
        await jive_mgr.cleanup()
    except Exception as e:
        print(f"   Error: {e}")
    
    # Check if there's a schema mismatch
    print("\n3. Schema Comparison:")
    print("   MCP Server WorkItem schema: id, title, description, vector, item_type, status, priority, assignee, tags, estimated_hours, actual_hours, progress, parent_id, dependencies, acceptance_criteria, created_at, updated_at, metadata")
    print("   MCP Jive WorkItem schema: id, item_id, title, description, vector, item_type, status, priority, assignee, tags, estimated_hours, actual_hours, progress, parent_id, dependencies, acceptance_criteria, created_at, updated_at, metadata")
    print("   Key difference: MCP Jive has 'item_id' field, MCP Server doesn't")
    
    print("\n=== Analysis ===\n")
    print("The issue is that:")
    print("1. Client tools use mcp_jive.lancedb_manager.LanceDBManager")
    print("2. Workflow engine tools use mcp_server.lancedb_manager.LanceDBManager")
    print("3. Both connect to ./data/lancedb_jive but have different schemas")
    print("4. Work items are stored with MCP Jive schema (with item_id field)")
    print("5. Workflow engine expects MCP Server schema (without item_id field)")
    
    print("\n=== Solution ===\n")
    print("Option 1: Migrate work items from MCP Jive schema to MCP Server schema")
    print("Option 2: Update workflow engine to use MCP Jive LanceDB manager")
    print("Option 3: Standardize on one schema across both managers")

if __name__ == "__main__":
    asyncio.run(debug_database_mismatch())