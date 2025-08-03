#!/usr/bin/env python3
"""
Debug script to directly examine LanceDB tables and their contents
without going through the manager abstractions.
"""

import asyncio
import sys
import os
import lancedb
import pandas as pd

async def debug_raw_lancedb():
    print("=== Raw LanceDB Debug ===\n")
    
    # Connect directly to LanceDB
    db_path = './data/lancedb_jive'
    print(f"Connecting to: {os.path.abspath(db_path)}")
    
    try:
        db = lancedb.connect(db_path)
        tables = db.table_names()
        print(f"Tables found: {tables}\n")
        
        # Check each table
        for table_name in tables:
            print(f"=== Table: {table_name} ===")
            try:
                table = db.open_table(table_name)
                
                # Get table schema
                schema = table.schema
                print(f"Schema: {[field.name for field in schema]}")
                
                # Count total records
                df = table.search().limit(1000).to_pandas()
                print(f"Total records: {len(df)}")
                
                if len(df) > 0:
                    print(f"Columns: {list(df.columns)}")
                    print("Sample records:")
                    for i, (_, row) in enumerate(df.head(3).iterrows()):
                        print(f"  Record {i+1}:")
                        for col in ['id', 'item_id', 'title', 'description']:
                            if col in row:
                                value = row[col]
                                if isinstance(value, str) and len(value) > 50:
                                    value = value[:50] + "..."
                                print(f"    {col}: {value}")
                        print()
                else:
                    print("  No records found")
                    
            except Exception as e:
                print(f"  Error reading table: {e}")
            
            print()
    
    except Exception as e:
        print(f"Error connecting to database: {e}")
    
    # Also check if there are any other database locations
    print("=== Checking other potential database locations ===")
    other_paths = ['./data/lancedb', './.weaviate_data', './data/weaviate']
    
    for path in other_paths:
        if os.path.exists(path):
            print(f"\nFound: {os.path.abspath(path)}")
            try:
                if path.endswith('lancedb'):
                    db = lancedb.connect(path)
                    tables = db.table_names()
                    print(f"  Tables: {tables}")
                    
                    if 'WorkItem' in tables:
                        table = db.open_table('WorkItem')
                        df = table.search().limit(10).to_pandas()
                        print(f"  WorkItem records: {len(df)}")
                        if len(df) > 0:
                            for _, row in df.head(2).iterrows():
                                print(f"    - {row.get('id', 'N/A')}: {row.get('title', 'N/A')}")
                else:
                    print(f"  Directory contents: {os.listdir(path)}")
            except Exception as e:
                print(f"  Error: {e}")
        else:
            print(f"Not found: {path}")

if __name__ == "__main__":
    asyncio.run(debug_raw_lancedb())