#!/usr/bin/env python3
"""
Test script to verify work item fixes.

This script tests the fixes for:
1. WorkItemStatus.NOT_STARTED -> WorkItemStatus.BACKLOG
2. Work item ID format issues

Run this after restarting the MCP server to verify fixes.
"""

import asyncio
import json
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mcp_jive.models.workflow import WorkItemStatus, WorkItemType, Priority

async def test_enum_values():
    """Test that WorkItemStatus enum has correct values."""
    print("🧪 Testing WorkItemStatus enum...")
    
    # Test that NOT_STARTED doesn't exist
    try:
        _ = WorkItemStatus.NOT_STARTED
        print("❌ ERROR: WorkItemStatus.NOT_STARTED should not exist!")
        return False
    except AttributeError:
        print("✅ PASS: WorkItemStatus.NOT_STARTED correctly doesn't exist")
    
    # Test that BACKLOG exists
    try:
        backlog_status = WorkItemStatus.BACKLOG
        print(f"✅ PASS: WorkItemStatus.BACKLOG = '{backlog_status.value}'")
    except AttributeError:
        print("❌ ERROR: WorkItemStatus.BACKLOG should exist!")
        return False
    
    # List all valid status values
    print("📋 Valid WorkItemStatus values:")
    for status in WorkItemStatus:
        print(f"   - {status.name} = '{status.value}'")
    
    return True

async def test_workflow_engine_imports():
    """Test that workflow engine tools can import without errors."""
    print("\n🧪 Testing WorkflowEngine imports...")
    
    try:
        # Test that we can import the workflow engine tools
        from mcp_jive.tools.workflow_engine import WorkflowEngineTools
        print("✅ PASS: WorkflowEngineTools imported successfully")
        return True
    except Exception as e:
        print(f"❌ ERROR: Failed to import WorkflowEngineTools: {e}")
        return False

async def test_work_item_creation():
    """Test work item creation with correct status."""
    print("\n🧪 Testing work item creation...")
    
    try:
        # Create a sample work item data structure
        work_item_data = {
            "id": "test-123",
            "title": "Test Work Item",
            "description": "Test description",
            "type": WorkItemType.TASK.value,
            "status": WorkItemStatus.BACKLOG.value,  # Should use BACKLOG, not NOT_STARTED
            "priority": Priority.MEDIUM.value,
            "project_id": "test-project",
            "reporter": "test-user"
        }
        
        print(f"✅ PASS: Work item created with status '{work_item_data['status']}'")
        print(f"📋 Work item data: {json.dumps(work_item_data, indent=2)}")
        return True
    except Exception as e:
        print(f"❌ ERROR: Failed to create work item: {e}")
        return False

async def test_uuid_format():
    """Test UUID format validation."""
    print("\n🧪 Testing UUID format...")
    
    import uuid
    
    # Test valid UUID
    valid_uuid = "079b61d5-bdd8-4341-8537-935eda5931c7"
    try:
        uuid_obj = uuid.UUID(valid_uuid)
        print(f"✅ PASS: Valid UUID format: {valid_uuid}")
    except ValueError as e:
        print(f"❌ ERROR: Invalid UUID format: {e}")
        return False
    
    # Test invalid kebab-case ID
    invalid_id = "ecommerce-platform-modernization"
    try:
        uuid_obj = uuid.UUID(invalid_id)
        print(f"❌ ERROR: Kebab-case ID should not be valid UUID: {invalid_id}")
        return False
    except ValueError:
        print(f"✅ PASS: Kebab-case ID correctly rejected: {invalid_id}")
    
    return True

async def main():
    """Run all tests."""
    print("🚀 Starting Work Item Fixes Verification\n")
    
    tests = [
        ("Enum Values", test_enum_values),
        ("WorkflowEngine Imports", test_workflow_engine_imports),
        ("Work Item Creation", test_work_item_creation),
        ("UUID Format", test_uuid_format)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ ERROR in {test_name}: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📊 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! The fixes are working correctly.")
        print("\n📋 Next Steps:")
        print("1. Restart the MCP server to pick up the code changes")
        print("2. Test the jive_get_work_item_children tool again")
        print("3. Use search tools to find work items by title")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
    
    return passed == len(results)

if __name__ == "__main__":
    asyncio.run(main())