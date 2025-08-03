#!/usr/bin/env python3
"""
Debug script to test numpy conversion logic directly
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import pandas as pd
import numpy as np
import asyncio
from mcp_jive.lancedb_manager import LanceDBManager, DatabaseConfig
from mcp_jive.config import ServerConfig

async def test_numpy_conversion():
    """Test the exact numpy conversion issue"""
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
            
        print("=== TESTING NUMPY CONVERSION ===")
        
        # Get the raw task data
        existing_task_raw = result.iloc[0].to_dict()
        
        print("\nRaw task data types:")
        for k, v in existing_task_raw.items():
            print(f"  {k}: {type(v)} = {repr(v)}")
            
            # Test the problematic conversion
            if hasattr(v, 'item') and hasattr(v, 'shape'):
                print(f"    Shape: {v.shape}")
                if v.shape == ():
                    print(f"    Can use .item(): {v.item()}")
                else:
                    print(f"    Should use .tolist(): {v.tolist()}")
                    try:
                        # This is where the error likely occurs
                        scalar_attempt = v.item()
                        print(f"    ERROR: .item() worked on array: {scalar_attempt}")
                    except Exception as e:
                        print(f"    EXPECTED ERROR with .item(): {e}")
        
        # Test the conversion logic
        print("\n=== TESTING CONVERSION LOGIC ===")
        existing_task = {}
        
        for k, v in existing_task_raw.items():
            try:
                if k == "vector":
                    continue
                elif isinstance(v, np.ndarray):
                    print(f"Converting numpy array {k} with shape {v.shape}")
                    existing_task[k] = v.tolist()
                elif isinstance(v, (np.integer, np.floating, np.bool_)):
                    print(f"Converting numpy scalar {k}")
                    existing_task[k] = v.item()
                elif hasattr(v, 'item') and hasattr(v, 'shape'):
                    if v.shape == ():
                        print(f"Converting zero-dim array {k}")
                        existing_task[k] = v.item()
                    else:
                        print(f"Converting multi-dim array {k}")
                        existing_task[k] = v.tolist()
                elif pd.isna(v):
                    existing_task[k] = None
                else:
                    existing_task[k] = v
                    
                print(f"  {k}: {type(existing_task[k])} = {repr(existing_task[k])}")
                
            except Exception as e:
                print(f"ERROR converting {k}: {e}")
                print(f"  Type: {type(v)}, Value: {repr(v)}")
                if hasattr(v, 'shape'):
                    print(f"  Shape: {v.shape}")
                    
        print("\n=== CONVERSION COMPLETE ===")
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_numpy_conversion())