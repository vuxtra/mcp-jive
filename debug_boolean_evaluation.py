#!/usr/bin/env python3
"""
Debug script to identify boolean evaluation issues with NumPy arrays.
"""

import asyncio
import sys
import os
import traceback
import numpy as np
import pandas as pd

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mcp_jive.config import ServerConfig
from mcp_jive.lancedb_manager import LanceDBManager, DatabaseConfig

async def debug_boolean_evaluation():
    """Debug boolean evaluation issues."""
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
        
        # Get a task from the database
        table = manager.get_table("Task")
        result = table.search().limit(1).to_pandas()
        
        if result.empty:
            print("No tasks found in database")
            return
            
        print("=== TESTING BOOLEAN EVALUATION SCENARIOS ===\n")
        
        # Get the raw task data
        existing_task_raw = result.iloc[0].to_dict()
        
        print("Testing boolean evaluation scenarios:")
        for k, v in existing_task_raw.items():
            print(f"\nField: {k}")
            print(f"  Type: {type(v)}")
            print(f"  Value: {repr(v)}")
            
            # Test various boolean evaluation scenarios
            try:
                # Test 1: Direct boolean evaluation
                print(f"  Direct bool(): ", end="")
                bool_result = bool(v)
                print(f"✓ {bool_result}")
            except Exception as e:
                print(f"❌ {e}")
                
            try:
                # Test 2: if v: evaluation
                print(f"  if v: ", end="")
                if v:
                    result = "True"
                else:
                    result = "False"
                print(f"✓ {result}")
            except Exception as e:
                print(f"❌ {e}")
                
            try:
                # Test 3: v if condition else default
                print(f"  v if condition: ", end="")
                result = list(v) if v is not None else []
                print(f"✓ converted to list")
            except Exception as e:
                print(f"❌ {e}")
                
            try:
                # Test 4: v and something
                print(f"  v and True: ", end="")
                result = v and True
                print(f"✓ {result}")
            except Exception as e:
                print(f"❌ {e}")
                
            try:
                # Test 5: v or something
                print(f"  v or []: ", end="")
                result = v or []
                print(f"✓ {type(result)}")
            except Exception as e:
                print(f"❌ {e}")
                
        print("\n=== TESTING SPECIFIC PROBLEMATIC PATTERNS ===\n")
        
        # Test the specific patterns we've been using
        tags = existing_task_raw.get('tags', [])
        print(f"Tags field: {type(tags)} = {repr(tags)}")
        
        # Test the problematic patterns
        patterns = [
            ("list(tags) if tags else []", lambda: list(tags) if tags else []),
            ("list(tags) if tags is not None else []", lambda: list(tags) if tags is not None else []),
            ("tags and list(tags)", lambda: tags and list(tags)),
            ("tags or []", lambda: tags or []),
        ]
        
        for pattern_name, pattern_func in patterns:
            try:
                print(f"\nTesting: {pattern_name}")
                result = pattern_func()
                print(f"  ✓ Success: {type(result)} = {repr(result)}")
            except Exception as e:
                print(f"  ❌ Error: {e}")
                print(f"  Traceback: {traceback.format_exc()}")
                
    except Exception as e:
        print(f"Error during analysis: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_boolean_evaluation())