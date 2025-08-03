#!/usr/bin/env python3
"""
Debug script to check the schema mismatch between existing data and current LanceDB manager.
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    import lancedb
    import pandas as pd
except ImportError as e:
    print(f"Missing dependencies: {e}")
    sys.exit(1)

async def debug_schema():
    """Debug the schema mismatch."""
    try:
        # Connect directly to LanceDB
        print("🔍 Connecting to lancedb_jive database...")
        db = lancedb.connect("./data/lancedb_jive")
        
        # Check WorkItem table schema
        print("\n📊 Checking WorkItem table...")
        try:
            work_item_table = db.open_table("WorkItem")
            print(f"✅ WorkItem table found with {work_item_table.count_rows()} rows")
            
            # Get schema
            schema = work_item_table.schema
            print(f"\n📋 Current schema:")
            for field in schema:
                print(f"  - {field.name}: {field.type}")
            
            # Try to read a few rows to see the actual data structure
            print("\n📄 Sample data (first 2 rows):")
            sample_data = work_item_table.to_pandas().head(2)
            for col in sample_data.columns:
                if col != 'vector':  # Skip vector column for readability
                    print(f"  {col}: {sample_data[col].tolist()}")
                    
        except Exception as e:
            print(f"❌ Error accessing WorkItem table: {e}")
            
        # Check what tables exist
        print(f"\n📚 Available tables: {db.table_names()}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_schema())