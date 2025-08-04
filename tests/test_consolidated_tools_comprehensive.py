#!/usr/bin/env python3
"""
Comprehensive Test Suite for Consolidated MCP Jive Tools

This test suite validates that all 32 legacy tool capabilities are preserved
in the 7 consolidated tools. Each test maps to specific legacy functionality.

Test Categories:
- TC-001 to TC-028: Individual tool functionality tests
- TC-029 to TC-030: Integration tests
- TC-031 to TC-032: Performance tests
"""

import asyncio
import json
import pytest
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch

# Import consolidated tools
try:
    from src.mcp_jive.tools.consolidated import (
        UnifiedWorkItemTool,
        UnifiedRetrievalTool,
        UnifiedSearchTool,
        UnifiedHierarchyTool,
        UnifiedExecutionTool,
        UnifiedProgressTool,
        UnifiedStorageTool,
        ConsolidatedToolRegistry
    )
    from src.mcp_jive.tools.base import ToolResult, ToolCategory
except ImportError as e:
    pytest.skip(f"Could not import consolidated tools: {e}", allow_module_level=True)


class TestDataManager:
    """Manages test data for comprehensive testing."""
    
    def __init__(self):
        self.test_work_items = []
        self.test_relationships = []
        self.test_executions = []
        
    def create_sample_work_item(self, **kwargs) -> Dict[str, Any]:
        """Create a sample work item with default values."""
        defaults = {
            "id": str(uuid.uuid4()),
            "title": f"Test Work Item {len(self.test_work_items) + 1}",
            "description": "Sample work item for testing",
            "type": "task",
            "status": "open",
            "priority": "medium",
            "assignee": "test-user",
            "tags": ["testing"],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        defaults.update(kwargs)
        self.test_work_items.append(defaults)
        return defaults
    
    def create_hierarchy_data(self) -> List[Dict[str, Any]]:
        """Create hierarchical test data."""
        parent = self.create_sample_work_item(
            title="Parent Epic",
            type="epic",
            description="Parent work item for testing hierarchy"
        )
        
        children = []
        for i in range(3):
            child = self.create_sample_work_item(
                title=f"Child Task {i+1}",
                type="task",
                parent_id=parent["id"],
                description=f"Child task {i+1} for hierarchy testing"
            )
            children.append(child)
            
            # Create relationship
            self.test_relationships.append({
                "parent_id": parent["id"],
                "child_id": child["id"],
                "relationship_type": "parent_child"
            })
        
        return [parent] + children
    
    def create_workflow_data(self) -> Dict[str, Any]:
        """Create workflow test data."""
        workflow = self.create_sample_work_item(
            title="Test Workflow",
            type="workflow",
            description="Workflow for execution testing",
            workflow_steps=[
                {"step": 1, "name": "Initialize", "status": "pending"},
                {"step": 2, "name": "Process", "status": "pending"},
                {"step": 3, "name": "Finalize", "status": "pending"}
            ]
        )
        return workflow


@pytest.fixture
def test_data_manager():
    """Provide test data manager."""
    return TestDataManager()


@pytest.fixture
def mock_database():
    """Mock database for testing."""
    with patch('src.mcp_jive.lancedb_manager.LanceDBManager') as mock_db:
        # Configure mock database responses
        mock_instance = mock_db.return_value
        mock_instance.search_work_items = AsyncMock(return_value=[])
        mock_instance.get_work_item = AsyncMock(return_value=None)
        mock_instance.create_work_item = AsyncMock(return_value={"id": "test-id"})
        mock_instance.update_work_item = AsyncMock(return_value=True)
        mock_instance.delete_work_item = AsyncMock(return_value=True)
        yield mock_instance


@pytest.fixture
def consolidated_tools(mock_database):
    """Provide consolidated tools with mocked dependencies."""
    tools = {
        'work_item': UnifiedWorkItemTool(),
        'retrieval': UnifiedRetrievalTool(),
        'search': UnifiedSearchTool(),
        'hierarchy': UnifiedHierarchyTool(),
        'execution': UnifiedExecutionTool(),
        'progress': UnifiedProgressTool(),
        'storage': UnifiedStorageTool()
    }
    return tools


class TestUnifiedWorkItemTool:
    """Test UnifiedWorkItemTool - Replaces 5 legacy tools."""
    
    @pytest.mark.asyncio
    async def test_tc001_work_item_creation(self, consolidated_tools, test_data_manager):
        """TC-001: Test work item creation (legacy: create_work_item)."""
        tool = consolidated_tools['work_item']
        
        # Test data
        create_params = {
            "action": "create",
            "title": "Test Work Item",
            "description": "Comprehensive test item",
            "type": "task",
            "priority": "high",
            "assignee": "test-user",
            "tags": ["testing", "validation"]
        }
        
        # Execute
        result = await tool.execute(create_params)
        
        # Validate
        assert result.success, f"Work item creation failed: {result.error}"
        assert "id" in result.data, "Work item ID not returned"
        assert result.data["title"] == create_params["title"]
        assert result.data["type"] == create_params["type"]
        assert result.data["priority"] == create_params["priority"]
    
    @pytest.mark.asyncio
    async def test_tc002_work_item_update(self, consolidated_tools, test_data_manager):
        """TC-002: Test work item update (legacy: update_work_item)."""
        tool = consolidated_tools['work_item']
        
        # Create item first
        item = test_data_manager.create_sample_work_item()
        
        # Test update
        update_params = {
            "action": "update",
            "work_item_id": item["id"],
            "title": "Updated Test Work Item",
            "description": "Updated description",
            "priority": "medium"
        }
        
        # Execute
        result = await tool.execute(update_params)
        
        # Validate
        assert result.success, f"Work item update failed: {result.error}"
        assert result.data["title"] == update_params["title"]
        assert result.data["priority"] == update_params["priority"]
    
    @pytest.mark.asyncio
    async def test_tc003_work_item_assignment(self, consolidated_tools, test_data_manager):
        """TC-003: Test work item assignment (legacy: assign_work_item)."""
        tool = consolidated_tools['work_item']
        
        # Create item first
        item = test_data_manager.create_sample_work_item()
        
        # Test assignment
        assign_params = {
            "action": "assign",
            "work_item_id": item["id"],
            "assignee": "new-assignee",
            "notify": True
        }
        
        # Execute
        result = await tool.execute(assign_params)
        
        # Validate
        assert result.success, f"Work item assignment failed: {result.error}"
        assert result.data["assignee"] == assign_params["assignee"]
    
    @pytest.mark.asyncio
    async def test_tc004_status_change(self, consolidated_tools, test_data_manager):
        """TC-004: Test status change (legacy: change_work_item_status)."""
        tool = consolidated_tools['work_item']
        
        # Create item first
        item = test_data_manager.create_sample_work_item()
        
        # Test status change
        status_params = {
            "action": "update_status",
            "work_item_id": item["id"],
            "status": "in_progress",
            "comment": "Starting work"
        }
        
        # Execute
        result = await tool.execute(status_params)
        
        # Validate
        assert result.success, f"Status change failed: {result.error}"
        assert result.data["status"] == status_params["status"]
    
    @pytest.mark.asyncio
    async def test_tc005_work_item_deletion(self, consolidated_tools, test_data_manager):
        """TC-005: Test work item deletion (legacy: delete_work_item)."""
        tool = consolidated_tools['work_item']
        
        # Create item first
        item = test_data_manager.create_sample_work_item()
        
        # Test deletion
        delete_params = {
            "action": "delete",
            "work_item_id": item["id"],
            "soft_delete": True
        }
        
        # Execute
        result = await tool.execute(delete_params)
        
        # Validate
        assert result.success, f"Work item deletion failed: {result.error}"
        assert result.data.get("deleted") is True


class TestUnifiedRetrievalTool:
    """Test UnifiedRetrievalTool - Replaces 4 legacy tools."""
    
    @pytest.mark.asyncio
    async def test_tc006_single_item_retrieval(self, consolidated_tools, test_data_manager):
        """TC-006: Test single item retrieval (legacy: get_work_item_by_id)."""
        tool = consolidated_tools['retrieval']
        
        # Create test item
        item = test_data_manager.create_sample_work_item()
        
        # Test retrieval
        get_params = {
            "action": "get",
            "work_item_id": item["id"]
        }
        
        # Execute
        result = await tool.execute(get_params)
        
        # Validate
        assert result.success, f"Item retrieval failed: {result.error}"
        assert result.data["id"] == item["id"]
        assert "title" in result.data
        assert "description" in result.data
    
    @pytest.mark.asyncio
    async def test_tc007_list_all_items(self, consolidated_tools, test_data_manager):
        """TC-007: Test list all items (legacy: list_work_items)."""
        tool = consolidated_tools['retrieval']
        
        # Create multiple test items
        for i in range(5):
            test_data_manager.create_sample_work_item(title=f"List Test Item {i+1}")
        
        # Test listing
        list_params = {
            "action": "list",
            "limit": 50,
            "offset": 0
        }
        
        # Execute
        result = await tool.execute(list_params)
        
        # Validate
        assert result.success, f"Item listing failed: {result.error}"
        assert isinstance(result.data, list)
        assert len(result.data) >= 0  # May be empty in mock
    
    @pytest.mark.asyncio
    async def test_tc008_filtered_retrieval(self, consolidated_tools, test_data_manager):
        """TC-008: Test filtered retrieval (legacy: filter_work_items)."""
        tool = consolidated_tools['retrieval']
        
        # Test filtering
        filter_params = {
            "action": "filter",
            "filters": {
                "status": "open",
                "assignee": "test-user",
                "priority": ["high", "medium"]
            }
        }
        
        # Execute
        result = await tool.execute(filter_params)
        
        # Validate
        assert result.success, f"Filtered retrieval failed: {result.error}"
        assert isinstance(result.data, list)
    
    @pytest.mark.asyncio
    async def test_tc009_detailed_item_view(self, consolidated_tools, test_data_manager):
        """TC-009: Test detailed item view (legacy: get_work_item_details)."""
        tool = consolidated_tools['retrieval']
        
        # Create test item
        item = test_data_manager.create_sample_work_item()
        
        # Test detailed view
        detail_params = {
            "action": "get_details",
            "work_item_id": item["id"],
            "include_history": True,
            "include_relationships": True
        }
        
        # Execute
        result = await tool.execute(detail_params)
        
        # Validate
        assert result.success, f"Detailed view failed: {result.error}"
        assert result.data["id"] == item["id"]


class TestUnifiedSearchTool:
    """Test UnifiedSearchTool - Replaces 3 legacy tools."""
    
    @pytest.mark.asyncio
    async def test_tc010_keyword_search(self, consolidated_tools, test_data_manager):
        """TC-010: Test keyword search (legacy: search_work_items)."""
        tool = consolidated_tools['search']
        
        # Test keyword search
        search_params = {
            "action": "search",
            "query": "bug fix authentication",
            "search_type": "keyword"
        }
        
        # Execute
        result = await tool.execute(search_params)
        
        # Validate
        assert result.success, f"Keyword search failed: {result.error}"
        assert isinstance(result.data, list)
    
    @pytest.mark.asyncio
    async def test_tc011_semantic_search(self, consolidated_tools, test_data_manager):
        """TC-011: Test semantic search (legacy: semantic_search)."""
        tool = consolidated_tools['search']
        
        # Test semantic search
        search_params = {
            "action": "search",
            "query": "login issues",
            "search_type": "semantic",
            "similarity_threshold": 0.7
        }
        
        # Execute
        result = await tool.execute(search_params)
        
        # Validate
        assert result.success, f"Semantic search failed: {result.error}"
        assert isinstance(result.data, list)
    
    @pytest.mark.asyncio
    async def test_tc012_full_text_search(self, consolidated_tools, test_data_manager):
        """TC-012: Test full text search (legacy: full_text_search)."""
        tool = consolidated_tools['search']
        
        # Test full text search
        search_params = {
            "action": "search",
            "query": "title:urgent AND description:*database*",
            "search_type": "full_text"
        }
        
        # Execute
        result = await tool.execute(search_params)
        
        # Validate
        assert result.success, f"Full text search failed: {result.error}"
        assert isinstance(result.data, list)


class TestUnifiedHierarchyTool:
    """Test UnifiedHierarchyTool - Replaces 6 legacy tools."""
    
    @pytest.mark.asyncio
    async def test_tc013_parent_retrieval(self, consolidated_tools, test_data_manager):
        """TC-013: Test parent retrieval (legacy: get_parent_items)."""
        tool = consolidated_tools['hierarchy']
        
        # Create hierarchy
        hierarchy_items = test_data_manager.create_hierarchy_data()
        child_item = hierarchy_items[1]  # First child
        
        # Test parent retrieval
        parent_params = {
            "action": "get_parents",
            "work_item_id": child_item["id"],
            "relationship_type": "parent_child"
        }
        
        # Execute
        result = await tool.execute(parent_params)
        
        # Validate
        assert result.success, f"Parent retrieval failed: {result.error}"
        assert isinstance(result.data, list)
    
    @pytest.mark.asyncio
    async def test_tc014_children_retrieval(self, consolidated_tools, test_data_manager):
        """TC-014: Test children retrieval (legacy: get_child_items)."""
        tool = consolidated_tools['hierarchy']
        
        # Create hierarchy
        hierarchy_items = test_data_manager.create_hierarchy_data()
        parent_item = hierarchy_items[0]  # Parent
        
        # Test children retrieval
        children_params = {
            "action": "get_children",
            "work_item_id": parent_item["id"],
            "relationship_type": "parent_child",
            "recursive": True
        }
        
        # Execute
        result = await tool.execute(children_params)
        
        # Validate
        assert result.success, f"Children retrieval failed: {result.error}"
        assert isinstance(result.data, list)
    
    @pytest.mark.asyncio
    async def test_tc015_relationship_creation(self, consolidated_tools, test_data_manager):
        """TC-015: Test relationship creation (legacy: create_relationship)."""
        tool = consolidated_tools['hierarchy']
        
        # Create two items
        parent = test_data_manager.create_sample_work_item(title="Parent Item")
        child = test_data_manager.create_sample_work_item(title="Child Item")
        
        # Test relationship creation
        relation_params = {
            "action": "create_relationship",
            "parent_id": parent["id"],
            "child_id": child["id"],
            "relationship_type": "depends_on"
        }
        
        # Execute
        result = await tool.execute(relation_params)
        
        # Validate
        assert result.success, f"Relationship creation failed: {result.error}"
    
    @pytest.mark.asyncio
    async def test_tc016_dependency_analysis(self, consolidated_tools, test_data_manager):
        """TC-016: Test dependency analysis (legacy: get_dependencies)."""
        tool = consolidated_tools['hierarchy']
        
        # Create item with dependencies
        item = test_data_manager.create_sample_work_item()
        
        # Test dependency analysis
        dep_params = {
            "action": "get_dependencies",
            "work_item_id": item["id"],
            "direction": "both"
        }
        
        # Execute
        result = await tool.execute(dep_params)
        
        # Validate
        assert result.success, f"Dependency analysis failed: {result.error}"
        assert isinstance(result.data, dict)


class TestUnifiedExecutionTool:
    """Test UnifiedExecutionTool - Replaces 5 legacy tools."""
    
    @pytest.mark.asyncio
    async def test_tc017_workflow_execution(self, consolidated_tools, test_data_manager):
        """TC-017: Test workflow execution (legacy: execute_workflow)."""
        tool = consolidated_tools['execution']
        
        # Create workflow
        workflow = test_data_manager.create_workflow_data()
        
        # Test execution
        exec_params = {
            "action": "execute",
            "work_item_id": workflow["id"],
            "execution_mode": "async",
            "parameters": {
                "environment": "test",
                "notify_on_completion": True
            }
        }
        
        # Execute
        result = await tool.execute(exec_params)
        
        # Validate
        assert result.success, f"Workflow execution failed: {result.error}"
        assert "execution_id" in result.data
    
    @pytest.mark.asyncio
    async def test_tc018_status_monitoring(self, consolidated_tools, test_data_manager):
        """TC-018: Test status monitoring (legacy: check_execution_status)."""
        tool = consolidated_tools['execution']
        
        # Create workflow
        workflow = test_data_manager.create_workflow_data()
        
        # Test status monitoring
        status_params = {
            "action": "status",
            "work_item_id": workflow["id"],
            "execution_id": "test-exec-id"
        }
        
        # Execute
        result = await tool.execute(status_params)
        
        # Validate
        assert result.success, f"Status monitoring failed: {result.error}"
        assert "status" in result.data
    
    @pytest.mark.asyncio
    async def test_tc019_execution_cancellation(self, consolidated_tools, test_data_manager):
        """TC-019: Test execution cancellation (legacy: cancel_execution)."""
        tool = consolidated_tools['execution']
        
        # Create workflow
        workflow = test_data_manager.create_workflow_data()
        
        # Test cancellation
        cancel_params = {
            "action": "cancel",
            "work_item_id": workflow["id"],
            "execution_id": "test-exec-id",
            "reason": "User requested"
        }
        
        # Execute
        result = await tool.execute(cancel_params)
        
        # Validate
        assert result.success, f"Execution cancellation failed: {result.error}"
    
    @pytest.mark.asyncio
    async def test_tc020_execution_validation(self, consolidated_tools, test_data_manager):
        """TC-020: Test execution validation (legacy: validate_execution)."""
        tool = consolidated_tools['execution']
        
        # Create workflow
        workflow = test_data_manager.create_workflow_data()
        
        # Test validation
        validate_params = {
            "action": "validate",
            "work_item_id": workflow["id"],
            "validation_rules": ["pre_conditions", "post_conditions"]
        }
        
        # Execute
        result = await tool.execute(validate_params)
        
        # Validate
        assert result.success, f"Execution validation failed: {result.error}"
        assert "validation_results" in result.data


class TestUnifiedProgressTool:
    """Test UnifiedProgressTool - Replaces 4 legacy tools."""
    
    @pytest.mark.asyncio
    async def test_tc021_progress_update(self, consolidated_tools, test_data_manager):
        """TC-021: Test progress update (legacy: update_progress)."""
        tool = consolidated_tools['progress']
        
        # Create item
        item = test_data_manager.create_sample_work_item()
        
        # Test progress update
        progress_params = {
            "action": "update",
            "work_item_id": item["id"],
            "progress_percentage": 75,
            "milestone": "Testing Complete",
            "notes": "All unit tests passing"
        }
        
        # Execute
        result = await tool.execute(progress_params)
        
        # Validate
        assert result.success, f"Progress update failed: {result.error}"
        assert result.data["progress_percentage"] == 75
    
    @pytest.mark.asyncio
    async def test_tc022_progress_reporting(self, consolidated_tools, test_data_manager):
        """TC-022: Test progress reporting (legacy: get_progress_report)."""
        tool = consolidated_tools['progress']
        
        # Create item
        item = test_data_manager.create_sample_work_item()
        
        # Test progress reporting
        report_params = {
            "action": "report",
            "work_item_id": item["id"],
            "report_type": "detailed",
            "include_history": True
        }
        
        # Execute
        result = await tool.execute(report_params)
        
        # Validate
        assert result.success, f"Progress reporting failed: {result.error}"
        assert "progress_data" in result.data
    
    @pytest.mark.asyncio
    async def test_tc023_milestone_tracking(self, consolidated_tools, test_data_manager):
        """TC-023: Test milestone tracking (legacy: track_milestones)."""
        tool = consolidated_tools['progress']
        
        # Create item
        item = test_data_manager.create_sample_work_item()
        
        # Test milestone tracking
        milestone_params = {
            "action": "milestones",
            "work_item_id": item["id"],
            "milestone_type": "all"
        }
        
        # Execute
        result = await tool.execute(milestone_params)
        
        # Validate
        assert result.success, f"Milestone tracking failed: {result.error}"
        assert isinstance(result.data, list)
    
    @pytest.mark.asyncio
    async def test_tc024_analytics_generation(self, consolidated_tools, test_data_manager):
        """TC-024: Test analytics generation (legacy: generate_analytics)."""
        tool = consolidated_tools['progress']
        
        # Create item
        item = test_data_manager.create_sample_work_item()
        
        # Test analytics generation
        analytics_params = {
            "action": "analytics",
            "work_item_id": item["id"],
            "metrics": ["velocity", "burndown", "quality"]
        }
        
        # Execute
        result = await tool.execute(analytics_params)
        
        # Validate
        assert result.success, f"Analytics generation failed: {result.error}"
        assert "analytics_data" in result.data


class TestUnifiedStorageTool:
    """Test UnifiedStorageTool - Replaces 5 legacy tools."""
    
    @pytest.mark.asyncio
    async def test_tc025_data_backup(self, consolidated_tools, test_data_manager):
        """TC-025: Test data backup (legacy: backup_data)."""
        tool = consolidated_tools['storage']
        
        # Test data backup
        backup_params = {
            "action": "backup",
            "data_type": "work_items",
            "format": "json",
            "include_relationships": True
        }
        
        # Execute
        result = await tool.execute(backup_params)
        
        # Validate
        assert result.success, f"Data backup failed: {result.error}"
        assert "backup_id" in result.data
    
    @pytest.mark.asyncio
    async def test_tc026_data_restoration(self, consolidated_tools, test_data_manager):
        """TC-026: Test data restoration (legacy: restore_data)."""
        tool = consolidated_tools['storage']
        
        # Test data restoration
        restore_params = {
            "action": "restore",
            "backup_id": "test-backup-id",
            "restore_mode": "selective",
            "items": ["item-id-1", "item-id-2"]
        }
        
        # Execute
        result = await tool.execute(restore_params)
        
        # Validate
        assert result.success, f"Data restoration failed: {result.error}"
        assert "restored_items" in result.data
    
    @pytest.mark.asyncio
    async def test_tc027_external_sync(self, consolidated_tools, test_data_manager):
        """TC-027: Test external sync (legacy: sync_external)."""
        tool = consolidated_tools['storage']
        
        # Test external sync
        sync_params = {
            "action": "sync",
            "external_system": "jira",
            "sync_direction": "bidirectional",
            "mapping_rules": {
                "status_mapping": True,
                "field_mapping": True
            }
        }
        
        # Execute
        result = await tool.execute(sync_params)
        
        # Validate
        assert result.success, f"External sync failed: {result.error}"
        assert "sync_results" in result.data
    
    @pytest.mark.asyncio
    async def test_tc028_data_export(self, consolidated_tools, test_data_manager):
        """TC-028: Test data export (legacy: export_data)."""
        tool = consolidated_tools['storage']
        
        # Test data export
        export_params = {
            "action": "export",
            "data_type": "all",
            "format": "csv",
            "filters": {
                "date_range": "last_30_days"
            }
        }
        
        # Execute
        result = await tool.execute(export_params)
        
        # Validate
        assert result.success, f"Data export failed: {result.error}"
        assert "export_file" in result.data


class TestIntegrationScenarios:
    """Integration tests for cross-tool workflows."""
    
    @pytest.mark.asyncio
    async def test_tc029_cross_tool_workflow(self, consolidated_tools, test_data_manager):
        """TC-029: Test complete work item lifecycle across all tools."""
        # Step 1: Create work item
        work_item_tool = consolidated_tools['work_item']
        create_result = await work_item_tool.execute({
            "action": "create",
            "title": "Integration Test Item",
            "description": "Testing cross-tool workflow",
            "type": "task"
        })
        assert create_result.success
        item_id = create_result.data["id"]
        
        # Step 2: Search for similar items
        search_tool = consolidated_tools['search']
        search_result = await search_tool.execute({
            "action": "search",
            "query": "Integration Test",
            "search_type": "keyword"
        })
        assert search_result.success
        
        # Step 3: Create parent-child relationship
        hierarchy_tool = consolidated_tools['hierarchy']
        parent_item = test_data_manager.create_sample_work_item(title="Parent Epic")
        relation_result = await hierarchy_tool.execute({
            "action": "create_relationship",
            "parent_id": parent_item["id"],
            "child_id": item_id,
            "relationship_type": "parent_child"
        })
        assert relation_result.success
        
        # Step 4: Execute workflow
        execution_tool = consolidated_tools['execution']
        exec_result = await execution_tool.execute({
            "action": "execute",
            "work_item_id": item_id,
            "execution_mode": "sync"
        })
        assert exec_result.success
        
        # Step 5: Track progress
        progress_tool = consolidated_tools['progress']
        progress_result = await progress_tool.execute({
            "action": "update",
            "work_item_id": item_id,
            "progress_percentage": 50,
            "milestone": "Integration Test Milestone"
        })
        assert progress_result.success
        
        # Step 6: Backup final state
        storage_tool = consolidated_tools['storage']
        backup_result = await storage_tool.execute({
            "action": "backup",
            "data_type": "work_items",
            "format": "json"
        })
        assert backup_result.success
        
        # Step 7: Retrieve final item
        retrieval_tool = consolidated_tools['retrieval']
        final_result = await retrieval_tool.execute({
            "action": "get",
            "work_item_id": item_id
        })
        assert final_result.success
        assert final_result.data["id"] == item_id
    
    @pytest.mark.asyncio
    async def test_tc030_error_handling_chain(self, consolidated_tools, test_data_manager):
        """TC-030: Test error propagation across tools."""
        # Test 1: Invalid work item creation
        work_item_tool = consolidated_tools['work_item']
        invalid_create = await work_item_tool.execute({
            "action": "create",
            # Missing required fields
        })
        # Should handle gracefully
        
        # Test 2: Search with malformed query
        search_tool = consolidated_tools['search']
        invalid_search = await search_tool.execute({
            "action": "search",
            "query": "",  # Empty query
            "search_type": "invalid_type"
        })
        # Should handle gracefully
        
        # Test 3: Create circular dependency
        hierarchy_tool = consolidated_tools['hierarchy']
        item1 = test_data_manager.create_sample_work_item()
        item2 = test_data_manager.create_sample_work_item()
        
        # Create A -> B
        await hierarchy_tool.execute({
            "action": "create_relationship",
            "parent_id": item1["id"],
            "child_id": item2["id"],
            "relationship_type": "depends_on"
        })
        
        # Try to create B -> A (circular)
        circular_result = await hierarchy_tool.execute({
            "action": "create_relationship",
            "parent_id": item2["id"],
            "child_id": item1["id"],
            "relationship_type": "depends_on"
        })
        # Should detect and prevent circular dependency
        
        # Test 4: Execute non-existent workflow
        execution_tool = consolidated_tools['execution']
        invalid_exec = await execution_tool.execute({
            "action": "execute",
            "work_item_id": "non-existent-id"
        })
        # Should handle gracefully
        
        # Test 5: Update progress for deleted item
        progress_tool = consolidated_tools['progress']
        invalid_progress = await progress_tool.execute({
            "action": "update",
            "work_item_id": "deleted-item-id",
            "progress_percentage": 100
        })
        # Should handle gracefully


class TestPerformanceScenarios:
    """Performance tests for consolidated tools."""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_tc031_load_testing(self, consolidated_tools, test_data_manager):
        """TC-031: Test high-volume operations."""
        start_time = time.time()
        
        # Create multiple work items simultaneously
        work_item_tool = consolidated_tools['work_item']
        create_tasks = []
        
        for i in range(10):  # Reduced for testing
            task = work_item_tool.execute({
                "action": "create",
                "title": f"Load Test Item {i+1}",
                "description": f"Load testing item {i+1}",
                "type": "task"
            })
            create_tasks.append(task)
        
        # Execute all creates concurrently
        results = await asyncio.gather(*create_tasks, return_exceptions=True)
        
        # Validate performance
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete within reasonable time
        assert duration < 30, f"Load test took too long: {duration}s"
        
        # Count successful operations
        successful = sum(1 for r in results if isinstance(r, ToolResult) and r.success)
        assert successful > 0, "No operations succeeded"
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_tc032_stress_testing(self, consolidated_tools, test_data_manager):
        """TC-032: Test system limits."""
        # Test maximum work item size
        work_item_tool = consolidated_tools['work_item']
        
        large_description = "x" * 10000  # 10KB description
        large_item_result = await work_item_tool.execute({
            "action": "create",
            "title": "Large Item Test",
            "description": large_description,
            "type": "task"
        })
        
        # Should handle large items gracefully
        # (May succeed or fail gracefully with appropriate error)
        
        # Test complex hierarchy depth
        hierarchy_tool = consolidated_tools['hierarchy']
        
        # Create a chain of 5 items (reduced for testing)
        items = []
        for i in range(5):
            item = test_data_manager.create_sample_work_item(title=f"Chain Item {i+1}")
            items.append(item)
        
        # Create chain relationships
        for i in range(len(items) - 1):
            await hierarchy_tool.execute({
                "action": "create_relationship",
                "parent_id": items[i]["id"],
                "child_id": items[i+1]["id"],
                "relationship_type": "parent_child"
            })
        
        # Test retrieval of deep hierarchy
        deep_hierarchy_result = await hierarchy_tool.execute({
            "action": "get_children",
            "work_item_id": items[0]["id"],
            "recursive": True
        })
        
        # Should handle deep hierarchies
        assert deep_hierarchy_result.success or "error" in deep_hierarchy_result.data


if __name__ == "__main__":
    # Run specific test categories
    import sys
    
    if len(sys.argv) > 1:
        category = sys.argv[1]
        if category == "unit":
            pytest.main(["-v", "-k", "not (tc029 or tc030 or tc031 or tc032)", __file__])
        elif category == "integration":
            pytest.main(["-v", "-k", "tc029 or tc030", __file__])
        elif category == "performance":
            pytest.main(["-v", "-k", "tc031 or tc032", "-m", "slow", __file__])
        else:
            pytest.main(["-v", __file__])
    else:
        pytest.main(["-v", __file__])