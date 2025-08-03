#!/usr/bin/env python3
"""
Simple database schema comparison.
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mcp_jive.lancedb_manager import LanceDBManager as JiveLanceDBManager, DatabaseConfig as JiveConfig
from mcp_server.lancedb_manager import LanceDBManager as ServerLanceDBManager, DatabaseConfig as ServerConfig

async def check_schemas():
    """Check schemas of both databases."""
    
    print("=== Database Schema Comparison ===\n")
    
    # Check MCP Jive database (./data/lancedb_jive)
    print("1. MCP Jive Database (./data/lancedb_jive):")
    try:
        jive_config = JiveConfig(data_path='./data/lancedb_jive')
        jive_manager = JiveLanceDBManager(jive_config)
        await jive_manager.initialize()
        
        jive_table = jive_manager.get_table('WorkItem')
        jive_fields = [field.name for field in jive_table.schema]
        print(f"   Fields: {jive_fields}")
        print(f"   Has 'item_id': {'item_id' in jive_fields}")
        print(f"   Records: {jive_table.count_rows()}")
        
        await jive_manager.cleanup()
        
    except Exception as e:
        print(f"   Error: {e}")
    
    # Check MCP Server database (./data/lancedb)
    print("\n2. MCP Server Database (./data/lancedb):")
    try:
        server_config = ServerConfig(data_path='./data/lancedb')
        server_manager = ServerLanceDBManager(server_config)
        await server_manager.initialize()
        
        server_table = server_manager.get_table('WorkItem')
        server_fields = [field.name for field in server_table.schema]
        print(f"   Fields: {server_fields}")
        print(f"   Has 'item_id': {'item_id' in server_fields}")
        print(f"   Records: {server_table.count_rows()}")
        
        await server_manager.cleanup()
        
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n=== Analysis ===\n")
    print("The MCP Server is likely using the wrong database!")
    print("- MCP Jive database has 'item_id' field")
    print("- MCP Server database does NOT have 'item_id' field")
    print("- Client tools are sending data with 'item_id' to MCP Server database")
    print("- This causes the schema mismatch error")

if __name__ == "__main__":
    asyncio.run(check_schemas())