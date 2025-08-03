#!/usr/bin/env python3
"""
Category 3: Workflow Execution Tools Test Suite

Tests the 4 workflow execution tools:
- jive_execute_workflow
- jive_validate_workflow  
- jive_get_workflow_status
- jive_cancel_workflow
"""

import asyncio
import json
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mcp_jive.tools.workflow_execution import WorkflowExecutionTools
from mcp_jive.lancedb_manager import LanceDBManager, DatabaseConfig
from mcp_jive.config import ServerConfig

async def test_category_3_workflow_execution():
    """Test Category 3: Workflow Execution Tools."""
    print("\n=== Category 3: Workflow Execution Tools Test ===")
    
    try:
        # Initialize components
        server_config = ServerConfig()
        db_config = DatabaseConfig()
        lancedb_manager = LanceDBManager(db_config)
        await lancedb_manager.initialize()
        
        workflow_tools = WorkflowExecutionTools(server_config, lancedb_manager)
        await workflow_tools.initialize()
        
        # Test 3.1: jive_execute_workflow
        print("\n--- Test 3.1: jive_execute_workflow ---")
        workflow_args = {
            "workflow_name": "User Authentication Workflow",
            "description": "Complete user authentication system implementation",
            "tasks": [
                {
                    "id": "auth-001",
                    "title": "Design auth schema",
                    "description": "Design database schema for user authentication",
                    "dependencies": [],
                    "estimated_duration": 120,
                    "priority": "high"
                },
                {
                    "id": "auth-002", 
                    "title": "Implement auth API",
                    "description": "Implement authentication API endpoints",
                    "dependencies": ["auth-001"],
                    "estimated_duration": 240,
                    "priority": "high"
                },
                {
                    "id": "auth-003",
                    "title": "Add auth tests",
                    "description": "Add comprehensive tests for authentication",
                    "dependencies": ["auth-002"],
                    "estimated_duration": 180,
                    "priority": "medium"
                }
            ],
            "execution_mode": "dependency_based",
            "auto_start": True
        }
        
        result = await workflow_tools.handle_tool_call("jive_execute_workflow", workflow_args)
        response = json.loads(result[0].text)
        
        if response.get("success"):
            workflow_id = response.get("execution_id")
            print(f"✅ Test 3.1 PASSED: Workflow created with ID {workflow_id}")
        else:
            print(f"❌ Test 3.1 FAILED: {response.get('error', 'Unknown error')}")
            return False
            
        # Test 3.2: jive_validate_workflow
        print("\n--- Test 3.2: jive_validate_workflow ---")
        
        # Test valid workflow
        valid_workflow_args = {
            "tasks": [
                {
                    "id": "task-1",
                    "title": "First task",
                    "dependencies": []
                },
                {
                    "id": "task-2",
                    "title": "Second task", 
                    "dependencies": ["task-1"]
                }
            ],
            "check_circular_dependencies": True,
            "check_missing_dependencies": True
        }
        
        result = await workflow_tools.handle_tool_call("jive_validate_workflow", valid_workflow_args)
        response = json.loads(result[0].text)
        
        if response.get("success") and response.get("valid"):
            print("✅ Test 3.2a PASSED: Valid workflow validated successfully")
        else:
            print(f"❌ Test 3.2a FAILED: {response.get('error', 'Validation failed')}")
            return False
            
        # Test circular dependency detection
        circular_workflow_args = {
            "tasks": [
                {
                    "id": "task-a",
                    "title": "Task A",
                    "dependencies": ["task-b"]
                },
                {
                    "id": "task-b",
                    "title": "Task B",
                    "dependencies": ["task-a"]
                }
            ],
            "check_circular_dependencies": True
        }
        
        result = await workflow_tools.handle_tool_call("jive_validate_workflow", circular_workflow_args)
        response = json.loads(result[0].text)
        
        if response.get("success") and not response.get("valid"):
            print("✅ Test 3.2b PASSED: Circular dependency detected correctly")
        else:
            print(f"❌ Test 3.2b FAILED: Should have detected circular dependency")
            return False
            
        # Test 3.3: jive_get_workflow_status
        print("\n--- Test 3.3: jive_get_workflow_status ---")
        
        status_args = {
            "workflow_id": workflow_id,
            "include_task_details": True,
            "include_timeline": True
        }
        
        result = await workflow_tools.handle_tool_call("jive_get_workflow_status", status_args)
        response = json.loads(result[0].text)
        
        if response.get("success"):
            print(f"✅ Test 3.3 PASSED: Workflow status retrieved - Status: {response.get('status')}")
        else:
            print(f"❌ Test 3.3 FAILED: {response.get('error', 'Unknown error')}")
            return False
            
        # Test 3.4: jive_cancel_workflow
        print("\n--- Test 3.4: jive_cancel_workflow ---")
        
        cancel_args = {
            "workflow_id": workflow_id,
            "reason": "Testing cancellation functionality",
            "force": True
        }
        
        result = await workflow_tools.handle_tool_call("jive_cancel_workflow", cancel_args)
        response = json.loads(result[0].text)
        
        if response.get("success"):
            print("✅ Test 3.4 PASSED: Workflow cancelled successfully")
        else:
            print(f"❌ Test 3.4 FAILED: {response.get('error', 'Unknown error')}")
            return False
            
        print("\n🎉 All Category 3 tests (3.1, 3.2, 3.3, 3.4) completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Category 3 tests failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function."""
    try:
        success = await test_category_3_workflow_execution()
        if success:
            print("\n✅ Category 3: Workflow Execution Tools - All tests passed!")
        else:
            print("\n❌ Category 3: Workflow Execution Tools - Some tests failed!")
            return False
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)