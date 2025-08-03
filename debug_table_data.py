#!/usr/bin/env python3
"""
Debug the actual data being sent to LanceDB and examine existing records.
"""

import asyncio
import sys
import os
import uuid
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mcp_jive.lancedb_manager import LanceDBManager, DatabaseConfig, WorkItemModel

async def debug_table_data():
    """Debug the table data and test insertion."""
    
    print("=== Debugging LanceDB Table Data ===\n")
    
    # Initialize MCP Jive LanceDB manager
    config = DatabaseConfig(data_path='./data/lancedb_jive')
    manager = LanceDBManager(config)
    await manager.initialize()
    
    try:
        # Get the WorkItem table
        table = manager.get_table('WorkItem')
        
        # Check existing records
        print("=== Existing Records ===")
        try:
            df = table.to_pandas()
            print(f"Records found: {len(df)}")
            if len(df) > 0:
                print("Columns:", list(df.columns))
                print("First record:")
                for col in df.columns:
                    if col != 'vector':  # Skip vector for readability
                        print(f"  {col}: {df.iloc[0][col]}")
        except Exception as e:
            print(f"Error reading existing records: {e}")
        
        print("\n=== Testing WorkItemModel Creation ===")
        
        # Test creating a WorkItemModel directly
        test_data = {
            "id": str(uuid.uuid4()),
            "item_id": str(uuid.uuid4()),
            "title": "Test Work Item",
            "description": "Testing direct model creation",
            "item_type": "task",
            "status": "not_started",
            "priority": "medium",
            "tags": [],
            "dependencies": [],
            "progress": 0.0,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "metadata": "{}"
        }
        
        print(f"Test data keys: {list(test_data.keys())}")
        
        # Generate embedding
        text_content = f"{test_data['title']} {test_data['description']}"
        vector = manager._generate_embedding(text_content)
        test_data['vector'] = vector
        
        print(f"Generated vector length: {len(vector)}")
        
        # Try to create WorkItemModel
        try:
            work_item = WorkItemModel(**test_data)
            print("✅ WorkItemModel created successfully")
            print(f"Model dict keys: {list(work_item.dict().keys())}")
            
            # Try to add to table
            print("\n=== Testing Table Addition ===")
            try:
                table.add([work_item.dict()])
                print("✅ Successfully added to table")
            except Exception as e:
                print(f"❌ Failed to add to table: {e}")
                import traceback
                traceback.print_exc()
                
        except Exception as e:
            print(f"❌ Failed to create WorkItemModel: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    await manager.cleanup()

if __name__ == "__main__":
    asyncio.run(debug_table_data())