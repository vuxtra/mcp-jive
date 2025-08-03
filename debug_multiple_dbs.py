#!/usr/bin/env python3
"""
Debug script to check multiple LanceDB locations for data.
"""

import lancedb
import os

def check_lancedb_location(path):
    """Check a LanceDB location for data."""
    print(f"\n=== Checking {path} ===")
    
    if not os.path.exists(path):
        print(f"Path does not exist: {path}")
        return
    
    try:
        db = lancedb.connect(path)
        tables = db.table_names()
        print(f"Available tables: {tables}")
        
        if 'WorkItem' in tables:
            table = db.open_table('WorkItem')
            count = table.count_rows()
            print(f"WorkItem table has {count} rows")
            
            if count > 0:
                # Get first few records
                result = table.search().limit(5).to_arrow()
                df = result.to_pandas()
                print(f"\nFirst {len(df)} records:")
                for idx, row in df.iterrows():
                    print(f"  ID: {row.get('id', 'N/A')}")
                    print(f"  Title: {row.get('title', 'N/A')}")
                    print(f"  Parent ID: {row.get('parent_id', 'N/A')}")
                    print(f"  Type: {row.get('item_type', 'N/A')}")
                    print()
        else:
            print("No WorkItem table found")
            
    except Exception as e:
        print(f"Error accessing {path}: {e}")

def main():
    """Check multiple LanceDB locations."""
    locations = [
        "./data/lancedb",
        "./data/lancedb_jive",
        "./data/test_migration",
        "./data/debug_embedding"
    ]
    
    for location in locations:
        check_lancedb_location(location)

if __name__ == "__main__":
    main()