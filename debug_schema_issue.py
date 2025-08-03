#!/usr/bin/env python3
"""
Debug script to test work item creation directly.
"""

import asyncio
import sys
import os
import uuid
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mcp_jive.lancedb_manager import LanceDBManager, DatabaseConfig

async def test_work_item_creation():
    """Test work item creation directly."""
    
    print("=== Testing Work Item Creation ===\n")
    
    # Initialize MCP Jive LanceDB manager
    config = DatabaseConfig(data_path='./data/lancedb_jive')
    manager = LanceDBManager(config)
    await manager.initialize()
    
    # Test data that matches what the client tools send
    test_data = {
        "id": str(uuid.uuid4()),
        "item_id": str(uuid.uuid4()),  # This should be included
        "type": "task",  # This will be converted to item_type
        "title": "Debug Test Work Item",
        "description": "Testing schema compatibility",
        "priority": "medium",
        "status": "not_started",
        "tags": [],
        "acceptance_criteria": [],
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "metadata": "{}"
    }
    
    print(f"Test data: {test_data}\n")
    
    try:
        # Test create_work_item
        result_id = await manager.create_work_item(test_data)
        print(f"✅ Successfully created work item: {result_id}")
        
        # Verify it was created
        retrieved = await manager.get_work_item(result_id)
        if retrieved:
            print(f"✅ Successfully retrieved work item: {retrieved.get('title')}")
        else:
            print("❌ Could not retrieve created work item")
            
    except Exception as e:
        print(f"❌ Error creating work item: {e}")
        import traceback
        traceback.print_exc()
    
    await manager.cleanup()

if __name__ == "__main__":
    asyncio.run(test_work_item_creation())