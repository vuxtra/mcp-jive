#!/usr/bin/env python3
"""
Test script for MCP Jive tools
This script tests the jive tools directly through the MCP server
"""

import json
import sys
import os
import asyncio

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mcp_jive.tools.task_management import TaskManagementTools
from mcp_jive.config import ServerConfig
from mcp_jive.lancedb_manager import LanceDBManager, DatabaseConfig

async def test_category_1_task_management():
    """Test Category 1: Task Management Tools"""
    print("\n=== TESTING CATEGORY 1: TASK MANAGEMENT TOOLS ===")
    
    # Initialize the tools
    server_config = ServerConfig()
    db_config = DatabaseConfig(
        data_path='./data/lancedb_jive',
        embedding_model='all-MiniLM-L6-v2',
        device='cpu'
    )
    
    lancedb_manager = LanceDBManager(db_config)
    await lancedb_manager.initialize()
    
    task_tools = TaskManagementTools(server_config, lancedb_manager)
    
    # Test 1.1: jive_create_task
    print("\n--- Test 1.1: jive_create_task ---")
    
    try:
        # Create first task
        task1_args = {
            "title": "Implement user authentication API",
            "description": "Create REST API endpoints for user login, logout, and token validation",
            "priority": "high",
            "tags": ["backend", "security", "api"]
        }
        
        result1 = await task_tools.handle_tool_call("jive_create_task", task1_args)
        result1_text = result1[0].text if result1 else "No response"
        result1_data = json.loads(result1_text)
        print(f"✅ Task 1 created: {json.dumps(result1_data, indent=2)}")
        task1_id = result1_data.get('task_id')
        
        # Create second task
        task2_args = {
            "title": "Design user dashboard wireframes",
            "description": "Create wireframes for the main user dashboard interface",
            "priority": "medium",
            "tags": ["frontend", "design", "ui"]
        }
        
        result2 = await task_tools.handle_tool_call("jive_create_task", task2_args)
        result2_text = result2[0].text if result2 else "No response"
        result2_data = json.loads(result2_text)
        print(f"✅ Task 2 created: {json.dumps(result2_data, indent=2)}")
        task2_id = result2_data.get('task_id')
        
        # Create third task
        task3_args = {
            "title": "Fix critical security vulnerability",
            "description": "Patch SQL injection vulnerability in user input validation",
            "priority": "urgent",
            "tags": ["security", "bugfix", "critical"]
        }
        
        result3 = await task_tools.handle_tool_call("jive_create_task", task3_args)
        result3_text = result3[0].text if result3 else "No response"
        result3_data = json.loads(result3_text)
        print(f"✅ Task 3 created: {json.dumps(result3_data, indent=2)}")
        task3_id = result3_data.get('task_id')
        
        print("\n✅ Test 1.1 (jive_create_task) PASSED")
        
        # Test 1.2: jive_update_task
        print("\n--- Test 1.2: jive_update_task ---")
        
        # Update the first task
        update_args = {
            "task_id": task1_id,
            "title": "Implement user authentication API - Updated",
            "description": "Create REST API endpoints for user login, logout, token validation, and password reset",
            "priority": "urgent",
            "status": "in_progress",
            "tags": ["backend", "security", "api", "authentication"]
        }
        
        result_update = await task_tools.handle_tool_call("jive_update_task", update_args)
        result_update_text = result_update[0].text if result_update else "No response"
        result_update_data = json.loads(result_update_text)
        print(f"✅ Task updated: {json.dumps(result_update_data, indent=2)}")
        
        print("\n✅ Test 1.2 (jive_update_task) PASSED")
        
        # Test 1.3: jive_get_task
        print("\n--- Test 1.3: jive_get_task ---")
        
        # Get the updated task to verify the changes
        get_data = {
            "task_id": task1_id,
            "include_subtasks": False
        }
        
        try:
            result = await task_tools.handle_tool_call("jive_get_task", get_data)
            result_text = result[0].text
            result_json = json.loads(result_text)
            
            if result_json.get("success"):
                task_data = result_json.get("task")
                print(f"✅ Task retrieved: {json.dumps(task_data, indent=2)}")
                
                # Verify the updated fields
                if (task_data.get("title") == "Implement user authentication API - Updated" and
                    task_data.get("priority") == "urgent" and
                    task_data.get("status") == "in_progress"):
                    print("✅ Task data verification passed - all updated fields correct")
                    print("\n✅ Test 1.3 (jive_get_task) PASSED")
                else:
                    print(f"❌ Task data verification failed - fields don't match expected values")
                    return None
            else:
                print(f"❌ Task retrieval failed: {result_text}")
                return None
                
        except Exception as e:
            print(f"❌ Error retrieving task: {e}")
            import traceback
            traceback.print_exc()
            return None
        
        # Test 1.4: jive_delete_task
        print("\n--- Test 1.4: jive_delete_task ---")
        
        # Delete the third task (security vulnerability task)
        delete_data = {
            "task_id": task3_id,
            "delete_subtasks": False
        }
        
        try:
            result = await task_tools.handle_tool_call("jive_delete_task", delete_data)
            result_text = result[0].text
            result_json = json.loads(result_text)
            
            if result_json.get("success"):
                print(f"✅ Task deleted: {result_text}")
                
                # Verify the task is actually deleted by trying to retrieve it
                verify_data = {"task_id": task3_id, "include_subtasks": False}
                verify_result = await task_tools.handle_tool_call("jive_get_task", verify_data)
                verify_text = verify_result[0].text
                verify_json = json.loads(verify_text)
                
                if not verify_json.get("success") and "not found" in verify_json.get("error", "").lower():
                    print("✅ Task deletion verification passed - task no longer exists")
                    print("\n✅ Test 1.4 (jive_delete_task) PASSED")
                else:
                    print(f"❌ Task deletion verification failed - task still exists")
                    return None
            else:
                print(f"❌ Task deletion failed: {result_text}")
                return None
                
        except Exception as e:
            print(f"❌ Error deleting task: {e}")
            import traceback
            traceback.print_exc()
            return None

        return {
            'task1_id': task1_id,
            'task2_id': task2_id, 
            'task3_id': task3_id
        }
        
    except Exception as e:
        print(f"❌ Test 1.1/1.2/1.3/1.4 FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    """Main test execution function"""
    print("🚀 Starting MCP Jive Tools Test Suite")
    
    task_ids = await test_category_1_task_management()
    
    if task_ids:
        print(f"\n🎉 Category 1 ALL TESTS (1.1, 1.2, 1.3, 1.4) completed successfully!")
        print(f"Created task IDs: {task_ids}")
    else:
        print(f"\n❌ Category 1 Tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())