#!/usr/bin/env python3
"""
Debug script to list all tasks in the database.
"""

import asyncio
import sys
import os
import traceback
import numpy as np
import pandas as pd
import json

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mcp_jive.config import ServerConfig
from mcp_jive.lancedb_manager import LanceDBManager, DatabaseConfig

async def list_all_tasks():
    """List all tasks in the database."""
    try:
        # Initialize config and LanceDB manager
        server_config = ServerConfig()
        config = DatabaseConfig(
            data_path=getattr(server_config, 'lancedb_data_path', './data/lancedb'),
            embedding_model=getattr(server_config, 'lancedb_embedding_model', 'all-MiniLM-L6-v2'),
            device=getattr(server_config, 'lancedb_device', 'cpu')
        )
        
        manager = LanceDBManager(config)
        await manager.initialize()
        
        print("=== LISTING ALL TASKS ===\n")
        
        # Get the Task table
        table = manager.get_table("Task")
        print(f"Table: {table}")
        
        # Try different ways to get all tasks
        print("\nMethod 1: Using to_pandas()...")
        try:
            all_tasks = table.to_pandas()
            print(f"Found {len(all_tasks)} tasks")
            if len(all_tasks) > 0:
                print("Task IDs:")
                for idx, row in all_tasks.iterrows():
                    print(f"  - {row.get('id', 'NO_ID')}: {row.get('title', 'NO_TITLE')}")
            else:
                print("No tasks found")
        except Exception as e:
            print(f"Method 1 failed: {e}")
            
        print("\nMethod 2: Using search().limit(10)...")
        try:
            search_result = table.search().limit(10).to_pandas()
            print(f"Found {len(search_result)} tasks")
            if len(search_result) > 0:
                print("Task IDs:")
                for idx, row in search_result.iterrows():
                    print(f"  - {row.get('id', 'NO_ID')}: {row.get('title', 'NO_TITLE')}")
            else:
                print("No tasks found")
        except Exception as e:
            print(f"Method 2 failed: {e}")
            
        print("\nMethod 3: Using head()...")
        try:
            head_result = table.head(10)
            print(f"Head result type: {type(head_result)}")
            if hasattr(head_result, 'to_pandas'):
                head_df = head_result.to_pandas()
                print(f"Found {len(head_df)} tasks")
                if len(head_df) > 0:
                    print("Task IDs:")
                    for idx, row in head_df.iterrows():
                        print(f"  - {row.get('id', 'NO_ID')}: {row.get('title', 'NO_TITLE')}")
            else:
                print(f"Head result: {head_result}")
        except Exception as e:
            print(f"Method 3 failed: {e}")
            
        print("\nMethod 4: Count rows...")
        try:
            count = table.count_rows()
            print(f"Total rows in table: {count}")
        except Exception as e:
            print(f"Method 4 failed: {e}")
            
    except Exception as e:
        print(f"Error during listing: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(list_all_tasks())