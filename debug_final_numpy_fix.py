#!/usr/bin/env python3
"""
Final comprehensive debug script to isolate and fix the NumPy boolean evaluation error.
"""

import asyncio
import sys
import os
import traceback
import numpy as np
import pandas as pd
import json
import uuid

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mcp_jive.config import ServerConfig
from mcp_jive.lancedb_manager import LanceDBManager, DatabaseConfig
from mcp_jive.tools.task_management import TaskManagementTools

def safe_numpy_conversion(value, field_name="unknown"):
    """
    Safely convert NumPy values to Python types to avoid boolean evaluation errors.
    """
    try:
        if isinstance(value, np.ndarray):
            if value.size == 0:
                return []
            elif value.size == 1:
                return value.item()
            else:
                return value.tolist()
        elif isinstance(value, (np.integer, np.floating, np.bool_)):
            return value.item()
        elif hasattr(value, 'tolist') and not isinstance(value, (str, list)):
            return value.tolist()
        elif hasattr(value, 'item') and not isinstance(value, (str, list, dict)):
            return value.item()
        else:
            return value
    except Exception as e:
        print(f"⚠️  Error converting {field_name}: {e}")
        return None

async def create_test_task(manager):
    """
    Create a test task to work with.
    """
    try:
        task_id = str(uuid.uuid4())
        task_data = {
            "id": task_id,
            "title": "Test Task for NumPy Debug",
            "description": "This task is created to test NumPy boolean evaluation fixes",
            "priority": "medium",
            "status": "todo",
            "tags": ["test", "numpy-debug"],
            "metadata": json.dumps({"created_by": "debug_script", "test": True})
        }
        
        print(f"Creating test task with ID: {task_id}")
        created_id = await manager.create_task(task_data)
        print(f"✅ Test task created: {created_id}")
        return task_id
        
    except Exception as e:
        print(f"❌ Failed to create test task: {e}")
        traceback.print_exc()
        return None

async def test_direct_task_update(task_id, manager):
    """
    Test task update with direct database operations to isolate the error.
    """
    try:
        print(f"\n=== DIRECT TASK UPDATE TEST (ID: {task_id}) ===")
        
        # Get the task table
        table = manager.get_table("Task")
        
        # Search for the specific task
        print(f"Searching for task: {task_id}")
        
        result = table.search().where(f"id = '{task_id}'").limit(1).to_pandas()
        
        if result.empty:
            print("❌ Task not found")
            return False
            
        print("✅ Task found, analyzing data types...")
        
        # Get the raw task data
        existing_task_raw = result.iloc[0].to_dict()
        
        # Safely convert all fields
        existing_task = {}
        for k, v in existing_task_raw.items():
            if k == "vector":
                continue  # Skip vector field
            
            print(f"Processing field {k}: {type(v)} = {repr(v)}")
            existing_task[k] = safe_numpy_conversion(v, k)
            print(f"  Converted to: {type(existing_task[k])} = {repr(existing_task[k])}")
        
        # Prepare update data with explicit field handling
        update_data = {
            "id": task_id,
            "title": existing_task.get("title", "Updated Task"),
            "description": existing_task.get("description", "Updated description"),
            "priority": "high",  # New value
            "status": "completed",  # New value
            "tags": ["numpy-fix-final", "boolean-evaluation-resolved"],  # New value
            "metadata": json.dumps({"updated_by": "debug_script", "test": True})
        }
        
        print("\nUpdate data prepared:")
        for k, v in update_data.items():
            print(f"  {k}: {type(v)} = {repr(v)}")
        
        # Delete the old record
        print("\nDeleting old record...")
        table.delete(f"id = '{task_id}'")
        print("✅ Old record deleted")
        
        # Create new task with updated data
        print("\nCreating updated task...")
        new_task_id = await manager.create_task(update_data)
        print(f"✅ Task updated successfully with ID: {new_task_id}")
        
        return True
        
    except ValueError as e:
        if "truth value of an array" in str(e):
            print(f"\n❌ CAUGHT NUMPY BOOLEAN EVALUATION ERROR: {e}")
            print("\n=== DETAILED STACK TRACE ===")
            traceback.print_exc()
            return False
        else:
            print(f"❌ Other ValueError: {e}")
            traceback.print_exc()
            return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        traceback.print_exc()
        return False

async def test_mcp_task_update(task_id, task_tools):
    """
    Test the MCP task update method directly.
    """
    try:
        print(f"\n=== MCP TASK UPDATE TEST (ID: {task_id}) ===")
        
        # Test the exact MCP call
        arguments = {
            "task_id": task_id,
            "status": "completed",
            "tags": ["mcp-test", "final-fix"]
        }
        
        print(f"Testing MCP update with arguments: {arguments}")
        
        result = await task_tools._update_task(arguments)
        print(f"MCP update result: {result}")
        
        # Check if the result indicates success
        if result and len(result) > 0:
            result_text = result[0].text
            result_data = json.loads(result_text)
            if result_data.get("success"):
                print("✅ MCP update successful")
                return True
            else:
                print(f"❌ MCP update failed: {result_data.get('error')}")
                return False
        else:
            print("❌ No result from MCP update")
            return False
        
    except ValueError as e:
        if "truth value of an array" in str(e):
            print(f"\n❌ CAUGHT NUMPY BOOLEAN EVALUATION ERROR IN MCP: {e}")
            print("\n=== DETAILED STACK TRACE ===")
            traceback.print_exc()
            return False
        else:
            print(f"❌ Other ValueError in MCP: {e}")
            traceback.print_exc()
            return False
    except Exception as e:
        print(f"❌ Unexpected error in MCP: {e}")
        traceback.print_exc()
        return False

async def main():
    """
    Main test function.
    """
    print("🔍 FINAL NUMPY BOOLEAN EVALUATION ERROR DEBUG")
    print("=" * 60)
    
    try:
        # Initialize components
        server_config = ServerConfig()
        db_config = DatabaseConfig(
            data_path=getattr(server_config, 'lancedb_data_path', './data/lancedb'),
            embedding_model=getattr(server_config, 'lancedb_embedding_model', 'all-MiniLM-L6-v2'),
            device=getattr(server_config, 'lancedb_device', 'cpu')
        )
        
        manager = LanceDBManager(db_config)
        await manager.initialize()
        
        task_tools = TaskManagementTools(server_config, manager)
        
        # Step 1: Create a test task
        task_id = await create_test_task(manager)
        if not task_id:
            print("❌ Failed to create test task. Exiting.")
            return
        
        # Step 2: Test direct database operations
        direct_success = await test_direct_task_update(task_id, manager)
        
        # Step 3: Create another test task for MCP test (since direct test deletes the task)
        if direct_success:
            task_id_2 = await create_test_task(manager)
            if task_id_2:
                mcp_success = await test_mcp_task_update(task_id_2, task_tools)
            else:
                mcp_success = False
        else:
            # If direct test failed, try MCP test with the same task
            mcp_success = await test_mcp_task_update(task_id, task_tools)
        
        print("\n" + "=" * 60)
        print("📊 FINAL RESULTS:")
        print(f"  Direct database update: {'✅ SUCCESS' if direct_success else '❌ FAILED'}")
        print(f"  MCP task update: {'✅ SUCCESS' if mcp_success else '❌ FAILED'}")
        
        if direct_success and mcp_success:
            print("\n🎉 ALL TESTS PASSED! NumPy boolean evaluation error appears to be resolved.")
        elif direct_success and not mcp_success:
            print("\n⚠️  Direct update works but MCP update fails. Issue is in MCP layer.")
        elif not direct_success and not mcp_success:
            print("\n❌ Both tests failed. NumPy boolean evaluation error persists.")
        else:
            print("\n🤔 Unexpected result pattern.")
            
    except Exception as e:
        print(f"❌ Fatal error in main: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())