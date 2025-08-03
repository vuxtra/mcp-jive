#!/usr/bin/env python3
"""
Analyze both databases to understand data migration requirements.
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mcp_jive.lancedb_manager import LanceDBManager as JiveLanceDBManager, DatabaseConfig as JiveConfig
from mcp_server.lancedb_manager import LanceDBManager as ServerLanceDBManager, DatabaseConfig as ServerConfig

async def analyze_databases():
    """Analyze both databases for consolidation planning."""
    
    print("=== Database Consolidation Analysis ===")
    print()
    
    # Analyze MCP Jive database (target)
    print("1. MCP Jive Database (TARGET - ./data/lancedb_jive):")
    try:
        jive_config = JiveConfig(data_path='./data/lancedb_jive')
        jive_manager = JiveLanceDBManager(jive_config)
        await jive_manager.initialize()
        
        # Get all tables
        jive_tables = jive_manager.list_tables()
        print(f"   Tables: {jive_tables}")
        
        for table_name in jive_tables:
            table = jive_manager.get_table(table_name)
            record_count = table.count_rows()
            schema_fields = [field.name for field in table.schema]
            print(f"   {table_name}: {record_count} records, fields: {schema_fields}")
        
        await jive_manager.cleanup()
        
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    
    # Analyze MCP Server database (source)
    print("2. MCP Server Database (SOURCE - ./data/lancedb):")
    try:
        server_config = ServerConfig(data_path='./data/lancedb')
        server_manager = ServerLanceDBManager(server_config)
        await server_manager.initialize()
        
        # Get all tables
        server_tables = server_manager.list_tables()
        print(f"   Tables: {server_tables}")
        
        for table_name in server_tables:
            table = server_manager.get_table(table_name)
            record_count = table.count_rows()
            schema_fields = [field.name for field in table.schema]
            print(f"   {table_name}: {record_count} records, fields: {schema_fields}")
            
            # If there are records, show sample data
            if record_count > 0:
                df = table.search().limit(3).to_pandas()
                print(f"   Sample data columns: {list(df.columns)}")
                if 'title' in df.columns:
                    print(f"   Sample titles: {df['title'].tolist()[:3]}")
        
        await server_manager.cleanup()
        
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    print("=== Migration Strategy ===")
    print("- MCP Jive database will be the target (has complete schema)")
    print("- MCP Server database data will be migrated to MCP Jive")
    print("- After migration, MCP Server database will be removed")
    print("- All code will use only MCP Jive components")

if __name__ == "__main__":
    asyncio.run(analyze_databases())