#!/usr/bin/env python3
"""
Trace the exact location of the NumPy boolean evaluation error in MCP task update.
"""

import asyncio
import sys
import os
import traceback
import numpy as np
import json
import uuid

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mcp_server.config import ServerConfig
from mcp_server.lancedb_manager import LanceDBManager, DatabaseConfig
from mcp_server.tools.task_management import TaskManagementTools

async def create_test_task_with_numpy_data(manager):
    """
    Create a test task with potential NumPy data to trigger the error.
    """
    try:
        task_id = str(uuid.uuid4())
        
        # Create task data with some NumPy arrays that might cause issues
        task_data = {
            "id": task_id,
            "title": "Test Task with NumPy Data",
            "description": "This task contains NumPy data that might cause boolean evaluation errors",
            "priority": "medium",
            "status": "todo",
            "tags": np.array(["numpy-test", "boolean-debug"]),  # NumPy array!
            "metadata": json.dumps({"created_by": "debug_script", "test": True})
        }
        
        print(f"Creating test task with ID: {task_id}")
        print(f"Task data types:")
        for k, v in task_data.items():
            print(f"  {k}: {type(v)} = {repr(v)}")
        
        created_id = await manager.create_task(task_data)
        print(f"✅ Test task created: {created_id}")
        return task_id
        
    except Exception as e:
        print(f"❌ Failed to create test task: {e}")
        traceback.print_exc()
        return None

async def debug_update_task_step_by_step(task_id, task_tools):
    """
    Manually step through the _update_task method to find the exact error location.
    """
    try:
        print(f"\n=== STEP-BY-STEP DEBUG OF _update_task (ID: {task_id}) ===")
        
        # Prepare arguments that might contain NumPy arrays
        arguments = {
            "task_id": task_id,
            "status": "completed",
            "tags": np.array(["mcp-test", "final-fix"]),  # NumPy array!
            "priority": "high"
        }
        
        print(f"Arguments prepared:")
        for k, v in arguments.items():
            print(f"  {k}: {type(v)} = {repr(v)}")
        
        # Access the LanceDB manager directly
        manager = task_tools.lancedb_manager
        
        print("\n🔍 Step 1: Getting table...")
        table = manager.get_table("Task")
        print("✅ Table retrieved successfully")
        
        print("\n🔍 Step 2: Searching for existing task...")
        result = table.search().where(f"id = '{task_id}'").limit(1).to_pandas()
        print(f"✅ Search completed, found {len(result)} results")
        
        if result.empty:
            print("❌ Task not found")
            return False
        
        print("\n🔍 Step 3: Converting result to dict...")
        existing_task_raw = result.iloc[0].to_dict()
        print("✅ Converted to dict successfully")
        
        print("\n🔍 Step 4: Processing existing task fields...")
        existing_task = {}
        
        for k, v in existing_task_raw.items():
            print(f"\n  Processing field '{k}': {type(v)}")
            try:
                if k == "vector":
                    print(f"    Skipping vector field")
                    continue
                elif isinstance(v, np.ndarray):
                    print(f"    Converting numpy array with shape {v.shape}")
                    existing_task[k] = v.tolist()
                elif isinstance(v, (np.integer, np.floating, np.bool_)):
                    print(f"    Converting numpy scalar")
                    existing_task[k] = v.item()
                elif k in ['created_at', 'updated_at'] and hasattr(v, 'to_pydatetime'):
                    print(f"    Converting datetime")
                    existing_task[k] = v.to_pydatetime()
                elif hasattr(v, 'isoformat'):
                    print(f"    Converting to ISO format")
                    existing_task[k] = v.isoformat()
                elif hasattr(v, 'tolist') and not isinstance(v, (str, list)):
                    print(f"    Converting array-like to list")
                    existing_task[k] = v.tolist()
                else:
                    print(f"    Using value as-is")
                    existing_task[k] = v
                    
                print(f"    ✅ Field '{k}' processed successfully")
                
            except Exception as field_error:
                print(f"    ❌ Error processing field '{k}': {field_error}")
                existing_task[k] = None
        
        print("\n🔍 Step 5: Processing existing tags...")
        existing_tags = existing_task.get("tags", [])
        print(f"  existing_tags: {type(existing_tags)} = {repr(existing_tags)}")
        
        try:
            if hasattr(existing_tags, 'tolist'):
                print(f"  Converting existing_tags with tolist()")
                existing_tags = existing_tags.tolist()
            elif not isinstance(existing_tags, list):
                print(f"  Converting existing_tags to list")
                if existing_tags is not None and existing_tags is not False:
                    try:
                        existing_tags = list(existing_tags)
                    except (TypeError, ValueError) as e:
                        print(f"    List conversion failed: {e}")
                        existing_tags = []
                else:
                    existing_tags = []
            print(f"  ✅ existing_tags processed: {existing_tags}")
        except Exception as tags_error:
            print(f"  ❌ Error processing existing_tags: {tags_error}")
            existing_tags = []
        
        print("\n🔍 Step 6: Processing arguments tags...")
        # This is where the error might occur - arguments.get() with existing_tags as default
        print(f"  About to call arguments.get('tags', existing_tags)")
        print(f"  existing_tags type: {type(existing_tags)}")
        print(f"  existing_tags value: {repr(existing_tags)}")
        
        try:
            # Test the exact call that might be causing the issue
            if "tags" in arguments:
                args_tags = arguments["tags"]
                print(f"  Using arguments['tags']: {type(args_tags)} = {repr(args_tags)}")
            else:
                print(f"  Using existing_tags as default")
                args_tags = existing_tags
                
            print(f"  ✅ args_tags obtained: {type(args_tags)} = {repr(args_tags)}")
        except Exception as args_tags_error:
            print(f"  ❌ Error getting args_tags: {args_tags_error}")
            traceback.print_exc()
            return False
        
        print("\n🔍 Step 7: Converting args_tags...")
        try:
            if hasattr(args_tags, 'tolist'):
                print(f"  Converting args_tags with tolist()")
                args_tags = args_tags.tolist()
            elif not isinstance(args_tags, list):
                print(f"  Converting args_tags to list")
                if args_tags is not None and args_tags is not False:
                    try:
                        args_tags = list(args_tags)
                    except (TypeError, ValueError) as e:
                        print(f"    List conversion failed: {e}")
                        args_tags = []
                else:
                    args_tags = []
            print(f"  ✅ args_tags processed: {args_tags}")
        except Exception as args_tags_error:
            print(f"  ❌ Error processing args_tags: {args_tags_error}")
            traceback.print_exc()
            return False
        
        print("\n🔍 Step 8: Creating update_data...")
        try:
            # Test each field assignment individually
            update_data = {}
            
            print(f"  Setting id...")
            update_data["id"] = task_id
            
            print(f"  Setting title...")
            if "title" in arguments:
                update_data["title"] = arguments["title"]
            else:
                update_data["title"] = existing_task.get("title")
            
            print(f"  Setting description...")
            if "description" in arguments:
                update_data["description"] = arguments["description"]
            else:
                update_data["description"] = existing_task.get("description")
            
            print(f"  Setting priority...")
            if "priority" in arguments:
                update_data["priority"] = arguments["priority"]
            else:
                update_data["priority"] = existing_task.get("priority")
            
            print(f"  Setting status...")
            if "status" in arguments:
                update_data["status"] = arguments["status"]
            else:
                update_data["status"] = existing_task.get("status")
            
            print(f"  Setting tags...")
            update_data["tags"] = args_tags
            
            print(f"  ✅ update_data created successfully")
            
        except Exception as update_error:
            print(f"  ❌ Error creating update_data: {update_error}")
            traceback.print_exc()
            return False
        
        print("\n🔍 Step 9: Final safety check...")
        try:
            for key, value in update_data.items():
                print(f"  Checking {key}: {type(value)}")
                if hasattr(value, 'tolist'):
                    print(f"    Converting {key} with tolist()")
                    update_data[key] = value.tolist()
                elif hasattr(value, 'item'):
                    print(f"    Converting {key} with item()")
                    update_data[key] = value.item()
            print(f"  ✅ Final safety check completed")
        except Exception as safety_error:
            print(f"  ❌ Error in final safety check: {safety_error}")
            traceback.print_exc()
            return False
        
        print("\n🔍 Step 10: Deleting old record...")
        try:
            table.delete(f"id = '{task_id}'")
            print(f"  ✅ Old record deleted")
        except Exception as delete_error:
            print(f"  ❌ Error deleting old record: {delete_error}")
            traceback.print_exc()
            return False
        
        print("\n🔍 Step 11: Creating new task...")
        try:
            await manager.create_task(update_data)
            print(f"  ✅ New task created successfully!")
            return True
        except Exception as create_error:
            print(f"  ❌ Error creating new task: {create_error}")
            traceback.print_exc()
            return False
        
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

async def main():
    """
    Main test function with step-by-step debugging.
    """
    print("🔍 STEP-BY-STEP NUMPY BOOLEAN EVALUATION ERROR DEBUG")
    print("=" * 70)
    
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
        
        # Create a test task with NumPy data
        task_id = await create_test_task_with_numpy_data(manager)
        if not task_id:
            print("❌ Failed to create test task. Exiting.")
            return
        
        # Debug the update process step by step
        success = await debug_update_task_step_by_step(task_id, task_tools)
        
        print("\n" + "=" * 70)
        print("📊 DEBUG RESULTS:")
        print(f"  Manual step-by-step update: {'✅ SUCCESS' if success else '❌ FAILED'}")
        
        if success:
            print("\n🎉 Manual update succeeded! Now testing actual MCP call...")
            
            # Test the actual MCP call
            arguments = {
                "task_id": task_id,
                "status": "in_progress",
                "tags": np.array(["final-test"]),  # NumPy array!
            }
            
            try:
                result = await task_tools._update_task(arguments)
                print(f"✅ MCP call also succeeded: {result}")
            except Exception as mcp_error:
                print(f"❌ MCP call failed: {mcp_error}")
                traceback.print_exc()
        
    except Exception as e:
        print(f"❌ Fatal error in main: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
