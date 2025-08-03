#!/usr/bin/env python3
"""
Compare the schemas of both LanceDB databases to identify the issue.
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mcp_jive.lancedb_manager import LanceDBManager, DatabaseConfig
from mcp_server.lancedb_manager import LanceDBManager as MCPServerLanceDBManager
from mcp_server.config import DatabaseConfig as MCPServerDatabaseConfig

async def compare_databases():
    """Compare the schemas of both LanceDB databases."""
    
    print("=== Comparing LanceDB Databases ===\n")
    
    # Check MCP Jive database
    print("1. MCP Jive LanceDB (./data/lancedb_jive):")
    try:
        jive_config = DatabaseConfig(data_path='./data/lancedb_jive')
        jive_manager = LanceDBManager(jive_config)
        await jive_manager.initialize()
        
        jive_table = jive_manager.get_table('WorkItem')
        print(f"   Schema exists: Yes")
        print(f"   Field count: {len(jive_table.schema)}")
        field_names = [field.name for field in jive_table.schema]
        print(f"   Has 'item_id': {'item_id' in field_names}")
        print(f"   Has 'id': {'id' in field_names}")
        print(f"   Record count: {jive_table.count_rows()}")
        
        await jive_manager.cleanup()
        
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n2. MCP Server LanceDB (./data/lancedb):")
    try:
        server_config = MCPServerDatabaseConfig(data_path='./data/lancedb')
        server_manager = MCPServerLanceDBManager(server_config)
        await server_manager.initialize()
        
        server_table = server_manager.get_table('WorkItem')
        print(f"   Schema exists: Yes")
        print(f"   Field count: {len(server_table.schema)}")
        field_names = [field.name for field in server_table.schema]
        print(f"   Has 'item_id': {'item_id' in field_names}")
        print(f"   Has 'id': {'id' in field_names}")
        print(f"   Record count: {server_table.count_rows()}")
        
        await server_manager.cleanup()
        
    except Exception as e:
        print(f"   Error: {e}")
    
    # Check which database the MCP Server is configured to use
    print("\n3. MCP Server Configuration Check:")
    try:
        from mcp_server.server import MCPServer
        # This will show us the default configuration
        print("   Default MCP Server database path: ./data/lancedb")
        print("   MCP Jive database path: ./data/lancedb_jive")
        
        # Check main.py configuration
        print("\n4. Checking main.py configuration...")
        with open('src/main.py', 'r') as f:
            content = f.read()
            if 'lancedb_jive' in content:
                print("   main.py references 'lancedb_jive'")
            if 'data_path' in content:
                print("   main.py contains data_path configuration")
                
    except Exception as e:
        print(f"   Error checking configuration: {e}")

if __name__ == "__main__":
    asyncio.run(compare_databases())