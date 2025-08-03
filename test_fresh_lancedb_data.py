#!/usr/bin/env python3
"""
Test creating fresh work items directly in LanceDB to verify workflow engine access.

This script will:
1. Create fresh work items directly in LanceDB
2. Test if workflow engine tools can access them
3. Verify the database path and schema alignment
"""

import asyncio
import sys
import uuid
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from mcp_server.lancedb_manager import LanceDBManager, DatabaseConfig
    from mcp_jive.lancedb_manager import LanceDBManager as JiveLanceDBManager
    from mcp_jive.lancedb_manager import DatabaseConfig as JiveDatabaseConfig
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

async def test_fresh_lancedb_data():
    """Test creating and accessing fresh work items in LanceDB."""
    print("🧪 Testing fresh LanceDB data creation and access...")
    
    # Test work item data
    test_work_item = {
        "id": str(uuid.uuid4()),
        "title": "Fresh Test Work Item",
        "description": "A test work item created directly in LanceDB",
        "type": "task",
        "status": "todo",
        "priority": "medium",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "tags": ["test", "fresh"],
        "metadata": '{"source": "test_script"}'  # String format
    }
    
    print(f"📝 Test work item: {test_work_item['title']} (ID: {test_work_item['id']})")
    
    # Test 1: MCP Jive LanceDB Manager
    print("\n=== Test 1: MCP Jive LanceDB Manager ===") 
    try:
        jive_config = JiveDatabaseConfig(data_path='./data/lancedb_jive')
        jive_manager = JiveLanceDBManager(jive_config)
        await jive_manager.initialize()
        
        # Store work item
        await jive_manager.store_work_item(test_work_item)
        print("✅ Work item stored in MCP Jive LanceDB")
        
        # Retrieve work item
        retrieved = await jive_manager.get_work_item(test_work_item['id'])
        if retrieved:
            print(f"✅ Work item retrieved from MCP Jive LanceDB: {retrieved.get('title')}")
        else:
            print("❌ Work item not found in MCP Jive LanceDB")
        
        # List all work items
        all_items = await jive_manager.list_work_items(limit=10)
        print(f"📊 Total work items in MCP Jive LanceDB: {len(all_items)}")
        
        await jive_manager.cleanup()
        
    except Exception as e:
        print(f"❌ Error with MCP Jive LanceDB: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: MCP Server LanceDB Manager (used by workflow engine)
    print("\n=== Test 2: MCP Server LanceDB Manager (Workflow Engine) ===")
    try:
        server_config = DatabaseConfig(data_path='./data/lancedb_jive')
        server_manager = LanceDBManager(server_config)
        await server_manager.initialize()
        
        # Try to retrieve the work item we just created
        retrieved = await server_manager.get_work_item(test_work_item['id'])
        if retrieved:
            print(f"✅ Work item found by MCP Server LanceDB: {retrieved.get('title')}")
        else:
            print("❌ Work item NOT found by MCP Server LanceDB")
        
        # List all work items
        all_items = await server_manager.list_work_items(limit=10)
        print(f"📊 Total work items seen by MCP Server LanceDB: {len(all_items)}")
        
        # Try to store a work item using server manager (with correct schema)
        server_test_item = {
            "id": str(uuid.uuid4()),
            "title": "Server Manager Test Item",
            "description": "Test item created by server manager",
            "type": "task",
            "status": "todo",
            "priority": "medium",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "tags": ["server-test"],
            "metadata": '{"source": "server_manager"}'  # String format for server schema
        }
        
        await server_manager.store_work_item(server_test_item)
        print(f"✅ Server manager stored work item: {server_test_item['title']}")
        
        # Check if jive manager can see server manager's item
        jive_manager2 = JiveLanceDBManager(JiveDatabaseConfig(data_path='./data/lancedb_jive'))
        await jive_manager2.initialize()
        
        server_item_from_jive = await jive_manager2.get_work_item(server_test_item['id'])
        if server_item_from_jive:
            print("✅ Jive manager can see server manager's work item")
        else:
            print("❌ Jive manager CANNOT see server manager's work item")
        
        await jive_manager2.cleanup()
        await server_manager.cleanup()
        
    except Exception as e:
        print(f"❌ Error with MCP Server LanceDB: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🎯 Test completed!")

if __name__ == "__main__":
    asyncio.run(test_fresh_lancedb_data())