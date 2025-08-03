#!/usr/bin/env python3
import sys
import asyncio
import os
sys.path.append('src')

from mcp_jive.lancedb_manager import LanceDBManager, DatabaseConfig

async def check_databases():
    print("=== Comprehensive Database Check ===")
    print(f"Current working directory: {os.getcwd()}")
    
    # Check MCP Server DB (./data/lancedb)
    print("\n=== MCP Server DB (./data/lancedb) ===")
    try:
        config1 = DatabaseConfig(data_path='./data/lancedb')
        print(f"Database path: {config1.data_path}")
        print(f"Absolute path: {os.path.abspath(config1.data_path)}")
        
        mgr1 = LanceDBManager(config1)
        await mgr1.initialize()
        
        # Check if tables exist
        tables = mgr1.list_tables()
        print(f"Available tables: {tables}")
        
        if 'WorkItem' in tables:
            # Try to get table directly
            table = mgr1.get_table('WorkItem')
            df = table.search().limit(10).to_pandas()
            print(f"Direct table query - Work items: {len(df)}")
            
            if len(df) > 0:
                print("Sample work items:")
                for _, row in df.head(3).iterrows():
                    print(f"  - {row.get('id', 'N/A')}: {row.get('title', 'N/A')}")
        
        # Try list_work_items method
        items1 = await mgr1.list_work_items(limit=10)
        print(f"list_work_items() result: {len(items1)}")
        
        await mgr1.cleanup()
    except Exception as e:
        print(f"Error with MCP Server DB: {e}")
        import traceback
        traceback.print_exc()
    
    # Check MCP Jive DB (./data/lancedb_jive)
    print("\n=== MCP Jive DB (./data/lancedb_jive) ===")
    try:
        config2 = DatabaseConfig(data_path='./data/lancedb_jive')
        print(f"Database path: {config2.data_path}")
        print(f"Absolute path: {os.path.abspath(config2.data_path)}")
        
        mgr2 = LanceDBManager(config2)
        await mgr2.initialize()
        
        # Check if tables exist
        tables = mgr2.list_tables()
        print(f"Available tables: {tables}")
        
        if 'WorkItem' in tables:
            # Try to get table directly
            table = mgr2.get_table('WorkItem')
            df = table.search().limit(10).to_pandas()
            print(f"Direct table query - Work items: {len(df)}")
        
        # Try list_work_items method
        items2 = await mgr2.list_work_items(limit=10)
        print(f"list_work_items() result: {len(items2)}")
        
        await mgr2.cleanup()
    except Exception as e:
        print(f"Error with MCP Jive DB: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_databases())
