#!/usr/bin/env python3
"""
Category 5: Workflow Engine Tools Test Suite

Tests the 6 workflow engine tools:
- jive_get_work_item_children
- jive_get_work_item_dependencies
- jive_validate_dependencies
- jive_execute_work_item
- jive_get_execution_status
- jive_cancel_execution
"""

import asyncio
import json
import sys
import os
import uuid
from datetime import datetime, timedelta

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mcp_jive.tools.workflow_engine import WorkflowEngineTools
from mcp_jive.tools.task_management import TaskManagementTools
from mcp_jive.lancedb_manager import LanceDBManager, DatabaseConfig
from mcp_jive.config import ServerConfig

async def test_category_5_workflow_engine():
    """Test Category 5: Workflow Engine Tools."""
    print("\n=== Category 5: Workflow Engine Tools Test ===")
    
    try:
        # Initialize components
        server_config = ServerConfig()
        db_config = DatabaseConfig()
        lancedb_manager = LanceDBManager(db_config)
        await lancedb_manager.initialize()
        
        workflow_engine = WorkflowEngineTools(server_config, lancedb_manager)
        await workflow_engine.initialize()
        
        task_management = TaskManagementTools(server_config, lancedb_manager)
        await task_management.initialize()
        
        # Create test work items for hierarchy testing
        print("\n--- Setting up test work items ---")
        
        # Create test work items directly in LanceDB with required fields
        initiative_uuid = str(uuid.uuid4())
        initiative_id = await lancedb_manager.create_work_item({
            "id": initiative_uuid,
            "item_id": "init-001",
            "title": "Digital Transformation Initiative",
            "description": "Complete digital transformation of customer experience",
            "item_type": "initiative",
            "priority": "high",
            "status": "in_progress",
            "assignee": "test_user",
            "estimated_hours": 240.0,
            "actual_hours": 0.0,
            "tags": ["test", "initiative"],
            "metadata": json.dumps({
                "reporter": "test_user",
                "project_id": "test_project_001"
            })
        })
        print(f"Created initiative: {initiative_id}")
        
        epic_uuid = str(uuid.uuid4())
        epic_id = await lancedb_manager.create_work_item({
            "id": epic_uuid,
            "item_id": "epic-001",
            "title": "Customer Portal Epic",
            "description": "Build comprehensive customer portal",
            "item_type": "epic",
            "status": "in_progress",
            "priority": "high",
            "parent_id": initiative_id,
            "assignee": "test_user",
            "estimated_hours": 120.0,
            "actual_hours": 0.0,
            "tags": ["test", "epic"],
            "metadata": json.dumps({
                "reporter": "test_user",
                "project_id": "test_project_001"
            })
        })
        print(f"Created epic: {epic_id}")
        
        # Create features under the epic
        feature1_uuid = str(uuid.uuid4())
        feature1_id = await lancedb_manager.create_work_item({
            "id": feature1_uuid,
            "item_id": "feature-001",
            "title": "User Authentication Feature",
            "description": "Implement secure user authentication",
            "item_type": "feature",
            "status": "ready",
            "priority": "high",
            "parent_id": epic_id,
            "assignee": "test_user",
            "estimated_hours": 40.0,
            "actual_hours": 0.0,
            "autonomous_executable": True,
            "execution_instructions": "Implement user authentication feature with login, logout, password reset, and session management",
            "tags": ["test", "feature"],
            "metadata": json.dumps({
                "reporter": "test_user",
                "project_id": "test_project_001"
            })
        })
        print(f"Created feature 1: {feature1_id}")
        
        feature2_uuid = str(uuid.uuid4())
        feature2_id = await lancedb_manager.create_work_item({
            "id": feature2_uuid,
            "item_id": "feature-002",
            "title": "Dashboard Feature",
            "description": "Customer dashboard with analytics",
            "item_type": "feature",
            "status": "backlog",
            "priority": "medium",
            "parent_id": epic_id,
            "dependencies": [feature1_id],
            "assignee": "test_user",
            "estimated_hours": 60.0,
            "actual_hours": 0.0,
            "autonomous_executable": True,
            "execution_instructions": "Implement customer dashboard with analytics, charts, and data visualization components",
            "tags": ["test", "feature"],
            "metadata": json.dumps({
                "reporter": "test_user",
                "project_id": "test_project_001"
            })
        })
        print(f"Created feature 2: {feature2_id}")
        
        # Create stories under features
        story1_uuid = str(uuid.uuid4())
        story1_id = await lancedb_manager.create_work_item({
            "id": story1_uuid,
            "item_id": "story-001",
            "title": "Login API Story",
            "description": "Implement login API endpoint",
            "item_type": "story",
            "status": "ready",
            "priority": "high",
            "parent_id": feature1_id,
            "assignee": "test_user",
            "estimated_hours": 16.0,
            "actual_hours": 0.0,
            "autonomous_executable": True,
            "execution_instructions": "Implement login API endpoint with authentication, validation, and session management",
            "tags": ["test", "story"],
            "metadata": json.dumps({
                "reporter": "test_user",
                "project_id": "test_project_001"
            })
        })
        print(f"Created story 1: {story1_id}")
        
        story2_uuid = str(uuid.uuid4())
        story2_id = await lancedb_manager.create_work_item({
            "id": story2_uuid,
            "item_id": "story-002",
            "title": "User Profile Story",
            "description": "User profile management",
            "item_type": "story",
            "status": "backlog",
            "priority": "medium",
            "parent_id": feature2_id,
            "dependencies": [story1_id],
            "assignee": "test_user",
            "estimated_hours": 24.0,
            "actual_hours": 0.0,
            "autonomous_executable": True,
            "execution_instructions": "Implement user profile management with CRUD operations, profile validation, and data persistence",
            "tags": ["test", "story"],
            "metadata": json.dumps({
                "reporter": "test_user",
                "project_id": "test_project_001"
            })
        })
        print(f"Created story 2: {story2_id}")
        
        # Test 5.1: jive_get_work_item_children
        print("\n--- Test 5.1: jive_get_work_item_children ---")
        print(f"Using epic_id: {epic_id}")
        
        # Test 5.1a: Get direct children of epic
        children_args = {
            "work_item_id": epic_id,  # This is the UUID returned from create_work_item
            "include_metadata": True,
            "recursive": False
        }
        
        result = await workflow_engine.handle_tool_call("jive_get_work_item_children", children_args)
        response = json.loads(result[0].text)
        
        if response.get("success"):
            children_count = len(response.get("children", []))
            print(f"✅ Test 5.1a PASSED: Found {children_count} direct children of epic")
        else:
            print(f"❌ Test 5.1a FAILED: {response.get('error', 'Unknown error')}")
            print(f"Response: {json.dumps(response, indent=2)}")
            return False
            
        # Test 5.1b: Get all descendants of initiative (recursive)
        recursive_args = {
            "work_item_id": initiative_id,
            "include_metadata": True,
            "recursive": True
        }
        
        result = await workflow_engine.handle_tool_call("jive_get_work_item_children", recursive_args)
        response = json.loads(result[0].text)
        
        if response.get("success"):
            total_descendants = len(response.get("children", []))
            print(f"✅ Test 5.1b PASSED: Found {total_descendants} total descendants of initiative")
        else:
            print(f"❌ Test 5.1b FAILED: {response.get('error', 'Unknown error')}")
            return False
            
        # Test 5.2: jive_get_work_item_dependencies
        print("\n--- Test 5.2: jive_get_work_item_dependencies ---")
        
        # Test 5.2a: Get dependencies for feature2 (should depend on feature1)
        deps_args = {
            "work_item_id": feature2_id,  # This is already a UUID
            "include_transitive": True,
            "only_blocking": True
        }
        
        result = await workflow_engine.handle_tool_call("jive_get_work_item_dependencies", deps_args)
        response = json.loads(result[0].text)
        
        if response.get("success"):
            deps_count = len(response.get("dependencies", []))
            print(f"✅ Test 5.2a PASSED: Found {deps_count} dependencies for feature2")
        else:
            print(f"❌ Test 5.2a FAILED: {response.get('error', 'Unknown error')}")
            print(f"Response: {json.dumps(response, indent=2)}")
            return False
            
        # Test 5.2b: Get dependencies for story2 (should include transitive deps)
        transitive_args = {
            "work_item_id": story2_id,  # This is already a UUID
            "include_transitive": True,
            "only_blocking": False
        }
        
        result = await workflow_engine.handle_tool_call("jive_get_work_item_dependencies", transitive_args)
        response = json.loads(result[0].text)
        
        if response.get("success"):
            all_deps_count = len(response.get("dependencies", []))
            print(f"✅ Test 5.2b PASSED: Found {all_deps_count} total dependencies for story2")
        else:
            print(f"❌ Test 5.2b FAILED: {response.get('error', 'Unknown error')}")
            print(f"Response: {json.dumps(response, indent=2)}")
            return False
            
        # Test 5.3: jive_validate_dependencies
        print("\n--- Test 5.3: jive_validate_dependencies ---")
        
        # Test 5.3a: Validate all work items (should pass)
        validate_args = {
            "work_item_ids": [],  # Empty means all
            "check_circular": True,
            "check_missing": True,
            "suggest_fixes": True
        }
        
        result = await workflow_engine.handle_tool_call("jive_validate_dependencies", validate_args)
        response = json.loads(result[0].text)
        
        if response.get("success"):
            is_valid = response.get("is_valid", False)
            issues_count = len(response.get("issues", []))
            print(f"✅ Test 5.3a PASSED: Validation complete - Valid: {is_valid}, Issues: {issues_count}")
        else:
            print(f"❌ Test 5.3a FAILED: {response.get('error', 'Unknown error')}")
            print(f"Response: {json.dumps(response, indent=2)}")
            return False
            
        # Test 5.3b: Validate specific work items
        specific_validate_args = {
            "work_item_ids": [feature1_id, feature2_id, story1_id, story2_id],  # These are already UUIDs
            "check_circular": True,
            "check_missing": True,
            "suggest_fixes": False
        }
        
        result = await workflow_engine.handle_tool_call("jive_validate_dependencies", specific_validate_args)
        response = json.loads(result[0].text)
        
        if response.get("success"):
            print(f"✅ Test 5.3b PASSED: Specific validation completed successfully")
        else:
            print(f"❌ Test 5.3b FAILED: {response.get('error', 'Unknown error')}")
            print(f"Response: {json.dumps(response, indent=2)}")
            return False
            
        # Test 5.4: jive_execute_work_item
        print("\n--- Test 5.4: jive_execute_work_item ---")
        
        # Test 5.4a: Execute story1 (no dependencies)
        execute_args = {
            "work_item_id": story1_id,  # This is already a UUID
            "execution_mode": "dependency_based",
            "agent_context": {
                "project_path": "/tmp/test_project",
                "environment": "development",
                "constraints": ["Use TypeScript", "Follow REST API standards"]
            },
            "validate_before_execution": True
        }
        
        result = await workflow_engine.handle_tool_call("jive_execute_work_item", execute_args)
        response = json.loads(result[0].text)
        
        if response.get("success"):
            execution_id_1 = response.get("execution_id")
            print(f"✅ Test 5.4a PASSED: Started execution of story1 with ID {execution_id_1}")
        else:
            print(f"❌ Test 5.4a FAILED: {response.get('error', 'Unknown error')}")
            print(f"Response: {json.dumps(response, indent=2)}")
            return False
            
        # Test 5.4b: Execute feature1 in parallel mode
        parallel_execute_args = {
            "work_item_id": feature1_id,  # This is already a UUID
            "execution_mode": "parallel",
            "validate_before_execution": False
        }
        
        result = await workflow_engine.handle_tool_call("jive_execute_work_item", parallel_execute_args)
        response = json.loads(result[0].text)
        
        if response.get("success"):
            execution_id_2 = response.get("execution_id")
            print(f"✅ Test 5.4b PASSED: Started parallel execution of feature1 with ID {execution_id_2}")
        else:
            print(f"❌ Test 5.4b FAILED: {response.get('error', 'Unknown error')}")
            print(f"Response: {json.dumps(response, indent=2)}")
            return False
            
        # Test 5.5: jive_get_execution_status
        print("\n--- Test 5.5: jive_get_execution_status ---")
        
        # Test 5.5a: Get status with logs
        status_args = {
            "execution_id": execution_id_1,
            "include_logs": True,
            "include_artifacts": True,
            "include_validation_results": True
        }
        
        result = await workflow_engine.handle_tool_call("jive_get_execution_status", status_args)
        response = json.loads(result[0].text)
        
        if response.get("success"):
            status = response.get("status")
            print(f"✅ Test 5.5a PASSED: Retrieved execution status: {status}")
        else:
            print(f"❌ Test 5.5a FAILED: {response.get('error', 'Unknown error')}")
            print(f"Response: {json.dumps(response, indent=2)}")
            return False
            
        # Test 5.5b: Get status without logs
        minimal_status_args = {
            "execution_id": execution_id_2,
            "include_logs": False,
            "include_artifacts": False,
            "include_validation_results": False
        }
        
        result = await workflow_engine.handle_tool_call("jive_get_execution_status", minimal_status_args)
        response = json.loads(result[0].text)
        
        if response.get("success"):
            print(f"✅ Test 5.5b PASSED: Retrieved minimal execution status successfully")
        else:
            print(f"❌ Test 5.5b FAILED: {response.get('error', 'Unknown error')}")
            print(f"Response: {json.dumps(response, indent=2)}")
            return False
            
        # Test 5.6: jive_cancel_execution
        print("\n--- Test 5.6: jive_cancel_execution ---")
        
        # Test 5.6a: Cancel execution with rollback
        cancel_args = {
            "execution_id": execution_id_1,
            "reason": "Requirements changed - need to update API specification",
            "rollback_changes": True,
            "force": False
        }
        
        result = await workflow_engine.handle_tool_call("jive_cancel_execution", cancel_args)
        response = json.loads(result[0].text)
        
        if response.get("success"):
            print(f"✅ Test 5.6a PASSED: Cancelled execution with rollback")
        else:
            print(f"❌ Test 5.6a FAILED: {response.get('error', 'Unknown error')}")
            print(f"Response: {json.dumps(response, indent=2)}")
            return False
            
        # Test 5.6b: Force cancel execution without rollback
        force_cancel_args = {
            "execution_id": execution_id_2,
            "reason": "Emergency stop - critical bug detected",
            "rollback_changes": False,
            "force": True
        }
        
        result = await workflow_engine.handle_tool_call("jive_cancel_execution", force_cancel_args)
        response = json.loads(result[0].text)
        
        if response.get("success"):
            print(f"✅ Test 5.6b PASSED: Force cancelled execution without rollback")
        else:
            print(f"❌ Test 5.6b FAILED: {response.get('error', 'Unknown error')}")
            print(f"Response: {json.dumps(response, indent=2)}")
            return False
            
        print("\n🎉 All Category 5 tests (5.1, 5.2, 5.3, 5.4, 5.5, 5.6) completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Category 5 tests failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function."""
    try:
        success = await test_category_5_workflow_engine()
        if success:
            print("\n✅ Category 5: Workflow Engine Tools - All tests passed!")
        else:
            print("\n❌ Category 5: Workflow Engine Tools - Some tests failed!")
            return False
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)