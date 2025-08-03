#!/usr/bin/env python3
"""
Debug script to investigate LanceDB data access issues.
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from mcp_jive.lancedb_manager import LanceDBManager, DatabaseConfig
import lancedb

async def debug_lancedb_data():
    """Debug LanceDB data access."""
    
    print("=== Debugging LanceDB Data Access ===")
    
    # Initialize LanceDB manager
    config = DatabaseConfig()
    manager = LanceDBManager(config)
    await manager.initialize()
    
    print(f"Database path: {config.data_path}")
    
    # Check if database exists
    try:
        db = lancedb.connect(config.data_path)
        tables = db.table_names()
        print(f"Available tables: {tables}")
        
        if 'WorkItem' in tables:
            table = db.open_table('WorkItem')
            print(f"\nWorkItem table schema: {table.schema}")
            
            # Try to get data directly from table
            try:
                # Get all records using to_arrow()
                arrow_result = table.search().limit(10).to_arrow()
                print(f"\nDirect arrow query returned {len(arrow_result)} records")
                
                # Convert to pandas to see data
                if len(arrow_result) > 0:
                    df = arrow_result.to_pandas()
                    print(f"\nDataFrame shape: {df.shape}")
                    print(f"Columns: {list(df.columns)}")
                    
                    if not df.empty:
                        print("\nFirst few records:")
                        for idx, row in df.head().iterrows():
                            print(f"  ID: {row.get('id', 'N/A')}")
                            print(f"  Title: {row.get('title', 'N/A')}")
                            print(f"  Parent ID: {row.get('parent_id', 'N/A')}")
                            print(f"  Type: {row.get('item_type', 'N/A')}")
                            print()
                else:
                    print("Arrow result is empty")
                    
            except Exception as e:
                print(f"Error with direct arrow query: {e}")
                import traceback
                traceback.print_exc()
                
            # Try to get count
            try:
                count_result = table.count_rows()
                print(f"\nTotal rows in WorkItem table: {count_result}")
            except Exception as e:
                print(f"Error getting row count: {e}")
                
        else:
            print("WorkItem table not found!")
            
    except Exception as e:
        print(f"Error accessing database: {e}")
        import traceback
        traceback.print_exc()
    
    # Test the manager's list_work_items method with debug
    print(f"\n=== Testing LanceDBManager.list_work_items ===")
    try:
        items = await manager.list_work_items(limit=10)
        print(f"Manager returned {len(items)} items")
        
        for item in items:
            print(f"  ID: {item.get('id', 'N/A')}")
            print(f"  Title: {item.get('title', 'N/A')}")
            print(f"  Parent ID: {item.get('parent_id', 'N/A')}")
            print(f"  Type: {item.get('item_type', 'N/A')}")
            print()
            
    except Exception as e:
        print(f"Error with manager.list_work_items: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_lancedb_data())