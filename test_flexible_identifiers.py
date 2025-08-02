#!/usr/bin/env python3
"""
Test script for flexible identifier support in MCP Jive tools.

This script demonstrates the enhanced AI tool functionality that allows:
- Exact UUID matching
- Title-based lookup
- Keyword search with automatic selection

Run this after implementing the flexible identifier resolver.
"""

import asyncio
import json
import sys
import os
import uuid
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mcp_server.config import ServerConfig
from mcp_server.database import WeaviateManager
from mcp_server.utils.identifier_resolver import IdentifierResolver
from mcp_server.tools.client_tools import MCPClientTools
from mcp_server.tools.workflow_engine import WorkflowEngineTools


async def setup_test_environment():
    """Set up test environment with sample data."""
    print("🔧 Setting up test environment...")
    
    # Load configuration
    config = ServerConfig()
    
    # Initialize Weaviate
    weaviate_manager = WeaviateManager(config)
    await weaviate_manager.start()
    
    # Initialize tools
    client_tools = MCPClientTools(config, weaviate_manager)
    workflow_tools = WorkflowEngineTools(config, weaviate_manager)
    identifier_resolver = IdentifierResolver(weaviate_manager)
    
    print("   ✅ Environment initialized")
    
    return config, weaviate_manager, client_tools, workflow_tools, identifier_resolver


async def create_test_data(weaviate_manager):
    """Create test work items for demonstration."""
    print("\n📝 Creating test work items...")
    
    test_items = [
        {
            "id": str(uuid.uuid4()),
            "title": "E-commerce Platform Modernization",
            "description": "Modernize our legacy e-commerce platform to improve performance, scalability, and user experience",
            "type": "initiative",
            "status": "backlog",
            "priority": "high",
            "created_at": datetime.now().isoformat() + "Z",
            "updated_at": datetime.now().isoformat() + "Z",
            "metadata": '{"demo": true}'
        },
        {
            "id": str(uuid.uuid4()),
            "title": "User Authentication System",
            "description": "Implement secure user authentication with multi-factor authentication",
            "type": "epic",
            "status": "ready",
            "priority": "high",
            "created_at": datetime.now().isoformat() + "Z",
            "updated_at": datetime.now().isoformat() + "Z",
            "metadata": '{"demo": true}'
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Payment Gateway Integration",
            "description": "Integrate multiple payment gateways for better customer experience",
            "type": "feature",
            "status": "in_progress",
            "priority": "medium",
            "created_at": datetime.now().isoformat() + "Z",
            "updated_at": datetime.now().isoformat() + "Z",
            "metadata": '{"demo": true}'
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Shopping Cart Optimization",
            "description": "Optimize shopping cart performance and user experience",
            "type": "story",
            "status": "backlog",
            "priority": "low",
            "created_at": datetime.now().isoformat() + "Z",
            "updated_at": datetime.now().isoformat() + "Z",
            "metadata": '{"demo": true}'
        }
    ]
    
    stored_items = []
    for item in test_items:
        try:
            await weaviate_manager.store_work_item(item)
            stored_items.append(item)
            print(f"   ✅ Created: {item['title']} (ID: {item['id'][:8]}...)")
        except Exception as e:
            print(f"   ❌ Failed to create {item['title']}: {e}")
    
    print(f"   📊 Total items created: {len(stored_items)}")
    return stored_items


async def test_identifier_resolution(identifier_resolver, test_items):
    """Test the identifier resolver directly."""
    print("\n🔍 Testing Identifier Resolution...")
    
    test_cases = [
        # Test 1: Exact UUID
        {
            "name": "Exact UUID",
            "identifier": test_items[0]["id"],
            "expected_title": test_items[0]["title"]
        },
        # Test 2: Exact title
        {
            "name": "Exact Title",
            "identifier": "E-commerce Platform Modernization",
            "expected_title": "E-commerce Platform Modernization"
        },
        # Test 3: Partial title (keyword search)
        {
            "name": "Keyword Search",
            "identifier": "authentication system",
            "expected_title": "User Authentication System"
        },
        # Test 4: Case insensitive
        {
            "name": "Case Insensitive",
            "identifier": "payment gateway",
            "expected_title": "Payment Gateway Integration"
        },
        # Test 5: Invalid identifier
        {
            "name": "Invalid Identifier",
            "identifier": "nonexistent-work-item",
            "expected_title": None
        }
    ]
    
    results = []
    for test_case in test_cases:
        print(f"\n   🧪 Test: {test_case['name']}")
        print(f"      Input: '{test_case['identifier']}'")
        
        try:
            # Test resolution
            resolved_id = await identifier_resolver.resolve_work_item_id(test_case["identifier"])
            
            if resolved_id:
                # Get the work item to verify
                work_item = await identifier_resolver.weaviate_manager.get_work_item(resolved_id)
                actual_title = work_item.get("title") if work_item else None
                
                if actual_title == test_case["expected_title"]:
                    print(f"      ✅ PASS: Resolved to '{actual_title}' (ID: {resolved_id[:8]}...)")
                    results.append(True)
                else:
                    print(f"      ❌ FAIL: Expected '{test_case['expected_title']}', got '{actual_title}'")
                    results.append(False)
            else:
                if test_case["expected_title"] is None:
                    print(f"      ✅ PASS: Correctly failed to resolve invalid identifier")
                    results.append(True)
                else:
                    print(f"      ❌ FAIL: Expected to resolve to '{test_case['expected_title']}', got None")
                    results.append(False)
                    
            # Get detailed resolution info
            resolution_info = await identifier_resolver.get_resolution_info(test_case["identifier"])
            print(f"      📋 Method: {resolution_info.get('resolution_method', 'failed')}")
            if resolution_info.get("candidates"):
                print(f"      🎯 Candidates: {len(resolution_info['candidates'])}")
                
        except Exception as e:
            print(f"      ❌ ERROR: {e}")
            results.append(False)
    
    passed = sum(results)
    total = len(results)
    print(f"\n   📊 Resolution Tests: {passed}/{total} passed")
    return passed == total


async def test_tool_integration(client_tools, workflow_tools, test_items):
    """Test the tools with flexible identifiers."""
    print("\n🛠️ Testing Tool Integration...")
    
    test_cases = [
        {
            "name": "Get Work Item by UUID",
            "tool": "jive_get_work_item",
            "handler": client_tools,
            "args": {"work_item_id": test_items[0]["id"]}
        },
        {
            "name": "Get Work Item by Title",
            "tool": "jive_get_work_item",
            "handler": client_tools,
            "args": {"work_item_id": "User Authentication System"}
        },
        {
            "name": "Get Work Item by Keywords",
            "tool": "jive_get_work_item",
            "handler": client_tools,
            "args": {"work_item_id": "payment gateway"}
        },
        {
            "name": "Update Work Item by Title",
            "tool": "jive_update_work_item",
            "handler": client_tools,
            "args": {
                "work_item_id": "Shopping Cart Optimization",
                "updates": {"priority": "medium"}
            }
        },
        {
            "name": "Get Children by Keywords",
            "tool": "jive_get_work_item_children",
            "handler": workflow_tools,
            "args": {"work_item_id": "ecommerce platform"}
        }
    ]
    
    results = []
    for test_case in test_cases:
        print(f"\n   🧪 Test: {test_case['name']}")
        print(f"      Tool: {test_case['tool']}")
        print(f"      Identifier: '{test_case['args']['work_item_id']}'")
        
        try:
            # Call the tool
            if test_case['tool'] == 'jive_get_work_item':
                result = await test_case['handler']._get_work_item(test_case['args'])
            elif test_case['tool'] == 'jive_update_work_item':
                result = await test_case['handler']._update_work_item(test_case['args'])
            elif test_case['tool'] == 'jive_get_work_item_children':
                result = await test_case['handler']._get_work_item_children(test_case['args'])
            else:
                print(f"      ❌ Unknown tool: {test_case['tool']}")
                results.append(False)
                continue
            
            # Parse response
            response_data = json.loads(result[0].text)
            
            if response_data.get("success"):
                print(f"      ✅ PASS: Tool executed successfully")
                if "resolved_from" in response_data and response_data["resolved_from"]:
                    print(f"      🔄 Resolved from: '{response_data['resolved_from']}'")
                if "work_item" in response_data:
                    print(f"      📄 Title: {response_data['work_item'].get('title', 'Unknown')}")
                results.append(True)
            else:
                print(f"      ❌ FAIL: {response_data.get('error', 'Unknown error')}")
                if "suggestions" in response_data:
                    print(f"      💡 Suggestions: {response_data['suggestions']}")
                results.append(False)
                
        except Exception as e:
            print(f"      ❌ ERROR: {e}")
            results.append(False)
    
    passed = sum(results)
    total = len(results)
    print(f"\n   📊 Tool Integration Tests: {passed}/{total} passed")
    return passed == total


async def test_error_handling(identifier_resolver):
    """Test error handling and edge cases."""
    print("\n⚠️ Testing Error Handling...")
    
    test_cases = [
        {
            "name": "Empty String",
            "identifier": ""
        },
        {
            "name": "Invalid UUID",
            "identifier": "not-a-valid-uuid"
        },
        {
            "name": "Nonexistent Title",
            "identifier": "This Work Item Does Not Exist"
        },
        {
            "name": "Special Characters",
            "identifier": "@#$%^&*()"
        }
    ]
    
    results = []
    for test_case in test_cases:
        print(f"\n   🧪 Test: {test_case['name']}")
        print(f"      Input: '{test_case['identifier']}'")
        
        try:
            resolved_id = await identifier_resolver.resolve_work_item_id(test_case["identifier"])
            
            if resolved_id is None:
                print(f"      ✅ PASS: Correctly returned None for invalid input")
                results.append(True)
            else:
                print(f"      ❌ FAIL: Unexpectedly resolved to {resolved_id}")
                results.append(False)
                
        except Exception as e:
            print(f"      ✅ PASS: Correctly handled exception: {type(e).__name__}")
            results.append(True)
    
    passed = sum(results)
    total = len(results)
    print(f"\n   📊 Error Handling Tests: {passed}/{total} passed")
    return passed == total


async def main():
    """Run all tests."""
    print("🚀 Starting Flexible Identifier Tests\n")
    
    try:
        # Setup
        config, weaviate_manager, client_tools, workflow_tools, identifier_resolver = await setup_test_environment()
        
        # Create test data
        test_items = await create_test_data(weaviate_manager)
        
        if not test_items:
            print("❌ No test data created. Exiting.")
            return False
        
        # Run tests
        test_results = []
        
        test_results.append(await test_identifier_resolution(identifier_resolver, test_items))
        test_results.append(await test_tool_integration(client_tools, workflow_tools, test_items))
        test_results.append(await test_error_handling(identifier_resolver))
        
        # Summary
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        
        print(f"\n📊 Final Results:")
        print(f"   Tests Passed: {passed_tests}/{total_tests}")
        
        if passed_tests == total_tests:
            print("\n🎉 All tests passed! Flexible identifier support is working correctly.")
            print("\n📋 Benefits for AI Agents:")
            print("   • No more UUID lookup required")
            print("   • Can use human-readable work item titles")
            print("   • Keyword search automatically finds relevant items")
            print("   • Better error messages with suggestions")
            print("   • Seamless fallback from exact match to search")
        else:
            print(f"\n⚠️ {total_tests - passed_tests} test(s) failed. Please check the implementation.")
        
        return passed_tests == total_tests
        
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)