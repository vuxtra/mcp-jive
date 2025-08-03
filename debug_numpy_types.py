#!/usr/bin/env python3
"""
Debug script to identify numpy types in LanceDB task data
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import pandas as pd
import numpy as np
import asyncio
from mcp_jive.lancedb_manager import LanceDBManager, DatabaseConfig

async def debug_task_data():
    """Debug the data types returned by LanceDB for tasks"""
    try:
        # Initialize config and LanceDB manager using EXACT same config as MCP server
        # From server.py: getattr(self.config, 'lancedb_data_path', './data/lancedb')
        from mcp_jive.config import ServerConfig
        
        server_config = ServerConfig()
        config = DatabaseConfig(
            data_path=getattr(server_config, 'lancedb_data_path', './data/lancedb'),
            embedding_model=getattr(server_config, 'lancedb_embedding_model', 'all-MiniLM-L6-v2'),
            device=getattr(server_config, 'lancedb_device', 'cpu')
        )
        
        print(f"Using database path: {config.data_path}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Absolute database path: {os.path.abspath(config.data_path)}")
        manager = LanceDBManager(config)
        await manager.initialize()
        
        # Check all tables and their contents
        print("\n=== CHECKING ALL TABLES ===")
        
        for table_name in ['Task', 'WorkItem', 'SearchIndex', 'ExecutionLog']:
            try:
                table = manager.get_table(table_name)
                result = table.search().limit(5).to_pandas()
                print(f"\n{table_name} table: {len(result)} records")
                
                if not result.empty:
                    print(f"Columns: {list(result.columns)}")
                    print(f"Sample data:")
                    for i, row in result.iterrows():
                        print(f"  Row {i}: {dict(row)}")
                        break  # Just show first row
                        
            except Exception as e:
                print(f"Error accessing {table_name} table: {e}")
        
        # Focus on Task table for detailed analysis
        try:
            table = manager.get_table("Task")
            result = table.search().limit(5).to_pandas()
            
            if result.empty:
                print("\nNo tasks found in Task table")
                print("\n=== TESTING TASK CREATION ===")
                
                # Try to create a task directly to reproduce the numpy error
                try:
                    import uuid
                    import json
                    
                    task_data = {
                        'id': str(uuid.uuid4()),
                        'title': 'Test numpy debug task',
                        'description': 'Testing numpy array conversion',
                        'priority': 'medium',
                        'status': 'todo',
                        'tags': [],
                        'metadata': json.dumps({'test': True})
                    }
                    
                    print("Creating task with data:")
                    for key, value in task_data.items():
                        print(f"  {key}: {value} (type: {type(value)})")
                    
                    # Use the same create_task method as the MCP server
                    task_id = await manager.create_task(task_data)
                    print(f"\n✅ Task created successfully with ID: {task_id}")
                    
                    # Now try to retrieve and update it to reproduce the error
                    print("\n=== TESTING TASK UPDATE ===")
                    
                    # Get the task back
                    table = manager.get_table("Task")
                    result = table.search().limit(1).to_pandas()
                    
                    if not result.empty:
                        print("Task retrieved successfully. Analyzing data types:")
                        first_task = result.iloc[0]
                        task_dict = first_task.to_dict()
                        
                        for field_name, value in task_dict.items():
                            value_type = type(value).__name__
                            module = type(value).__module__
                            is_numpy = module.startswith('numpy')
                            
                            print(f"  {field_name}: {value_type} (module: {module}) {'⚠️ NUMPY' if is_numpy else ''}")
                            
                            if is_numpy:
                                print(f"    Value: {value}")
                                if hasattr(value, 'shape'):
                                    print(f"    Shape: {value.shape}")
                                if hasattr(value, 'dtype'):
                                    print(f"    Dtype: {value.dtype}")
                    
                except Exception as e:
                    print(f"❌ Error during task creation/analysis: {e}")
                    import traceback
                    traceback.print_exc()
                
                return
        except Exception as e:
            print(f"Error accessing Task table: {e}")
            return
            
        print("=== TASK DATA TYPE ANALYSIS ===")
        print(f"Found {len(result)} tasks")
        print()
        
        # Analyze first task
        first_task = result.iloc[0]
        task_dict = first_task.to_dict()
        
        print("Field Types in Task Data:")
        print("-" * 50)
        
        for field_name, value in task_dict.items():
            value_type = type(value).__name__
            module = type(value).__module__
            
            # Check for numpy types
            is_numpy = module.startswith('numpy')
            is_pandas = module.startswith('pandas')
            
            print(f"{field_name:15} | {value_type:20} | {module:20} | {'NUMPY' if is_numpy else 'PANDAS' if is_pandas else 'PYTHON'}")
            
            # Special handling for arrays and scalars
            if hasattr(value, 'shape'):
                print(f"{'':15} | Shape: {value.shape} | Dtype: {getattr(value, 'dtype', 'N/A')}")
            elif hasattr(value, 'item'):
                print(f"{'':15} | Scalar value: {value} | Can convert: {hasattr(value, 'item')}")
            elif isinstance(value, (list, tuple)) and len(value) > 0:
                first_elem_type = type(value[0]).__name__ if value else 'empty'
                print(f"{'':15} | List/Tuple length: {len(value)} | First element type: {first_elem_type}")
            
            print()
        
        print("\n=== PROBLEMATIC FIELDS ANALYSIS ===")
        print("-" * 50)
        
        # Check specifically for numpy arrays and scalars
        problematic_fields = []
        
        for field_name, value in task_dict.items():
            if isinstance(value, np.ndarray):
                problematic_fields.append((field_name, 'numpy.ndarray', f"shape={value.shape}, dtype={value.dtype}"))
            elif isinstance(value, (np.integer, np.floating)):
                problematic_fields.append((field_name, 'numpy.scalar', f"value={value}, type={type(value)}"))
            elif hasattr(value, 'tolist') and not isinstance(value, (list, str)):
                problematic_fields.append((field_name, 'has_tolist', f"type={type(value)}, value={str(value)[:100]}"))
        
        if problematic_fields:
            print("Found potentially problematic fields:")
            for field, issue_type, details in problematic_fields:
                print(f"  {field}: {issue_type} - {details}")
        else:
            print("No obvious numpy arrays or scalars found")
            
        print("\n=== CONVERSION TEST ===")
        print("-" * 50)
        
        # Test conversion of each field
        for field_name, value in task_dict.items():
            if field_name == 'vector':
                continue  # Skip vector field
                
            try:
                # Try the conversion logic from the update method
                if hasattr(value, 'item'):  # numpy scalar
                    converted = value.item()
                    print(f"{field_name}: numpy scalar -> {type(converted).__name__} ✓")
                elif hasattr(value, 'tolist'):  # numpy array
                    converted = value.tolist()
                    print(f"{field_name}: numpy array -> {type(converted).__name__} ✓")
                elif pd.isna(value):  # pandas NaN
                    converted = None
                    print(f"{field_name}: pandas NaN -> None ✓")
                else:
                    converted = value
                    print(f"{field_name}: {type(value).__name__} -> no conversion needed ✓")
            except Exception as e:
                print(f"{field_name}: CONVERSION FAILED - {e} ❌")
                
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(debug_task_data())