"""Tests for MCP Client Tools.

Tests the comprehensive MCP tools for AI agents to interact with the MCP Jive system.
Covers task management, search and discovery, workflow execution, and progress tracking.
"""

import pytest
import json
import sys
import os
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Mock the mcp.server import before importing our modules
sys.modules['mcp'] = MagicMock()
sys.modules['mcp.server'] = MagicMock()
sys.modules['mcp.server.Server'] = MagicMock()
sys.modules['mcp.server.models'] = MagicMock()
sys.modules['mcp.server.models.InitializationOptions'] = MagicMock()
sys.modules['mcp.server.session'] = MagicMock()
sys.modules['mcp.server.session.ServerSession'] = MagicMock()
sys.modules['mcp.types'] = MagicMock()
sys.modules['mcp.shared'] = MagicMock()
sys.modules['mcp.shared.exceptions'] = MagicMock()

from mcp_server.tools.client_tools import MCPClientTools
from mcp_server.config import ServerConfig
from mcp_server.database import WeaviateManager
from mcp_server.models.workflow import WorkItem, WorkItemType, WorkItemStatus, Priority


@pytest.fixture
def mock_config():
    """Create a mock server configuration."""
    config = MagicMock(spec=ServerConfig)
    config.weaviate_url = "http://localhost:8080"
    config.weaviate_data_path = "/tmp/weaviate_test"
    return config


@pytest.fixture
def mock_weaviate_manager():
    """Create a mock Weaviate manager."""
    manager = AsyncMock(spec=WeaviateManager)
    return manager


@pytest.fixture
def client_tools(mock_config, mock_weaviate_manager):
    """Create MCP client tools instance."""
    return MCPClientTools(mock_config, mock_weaviate_manager)


@pytest.fixture
def sample_work_item_data():
    """Sample work item data for testing."""
    return {
        "id": "test-work-item-001",
        "type": "epic",
        "title": "User Authentication System",
        "description": "Implement secure user authentication with OAuth2",
        "status": "not_started",
        "priority": "high",
        "parent_id": "initiative-001",
        "acceptance_criteria": [
            "Users can register with email",
            "Password reset functionality works",
            "OAuth2 integration with Google and GitHub"
        ],
        "effort_estimate": 40.0,
        "tags": ["authentication", "security", "oauth2"],
        "created_at": "2024-12-19T10:00:00Z",
        "updated_at": "2024-12-19T15:30:00Z",
        "metadata": {
            "created_by": "mcp_client",
            "version": 1
        }
    }


class TestMCPClientToolsInitialization:
    """Test MCP client tools initialization."""
    
    @pytest.mark.asyncio
    async def test_initialization(self, client_tools):
        """Test client tools initialization."""
        await client_tools.initialize()
        # Should complete without errors
        
    @pytest.mark.asyncio
    async def test_get_tools(self, client_tools):
        """Test getting available tools."""
        tools = await client_tools.get_tools()
        
        assert len(tools) == 5
        tool_names = [tool.name for tool in tools]
        
        expected_tools = [
            "create_work_item",
            "get_work_item",
            "update_work_item",
            "list_work_items",
            "search_work_items"
        ]
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names
            
    @pytest.mark.asyncio
    async def test_cleanup(self, client_tools):
        """Test client tools cleanup."""
        await client_tools.cleanup()
        assert len(client_tools._execution_cache) == 0


class TestCreateWorkItem:
    """Test create_work_item tool."""
    
    @pytest.mark.asyncio
    async def test_create_work_item_success(self, client_tools, mock_weaviate_manager):
        """Test successful work item creation."""
        # Setup mock
        mock_weaviate_manager.store_work_item.return_value = "test-id-123"
        
        arguments = {
            "type": "epic",
            "title": "Test Epic",
            "description": "Test epic description",
            "priority": "high",
            "acceptance_criteria": ["Criterion 1", "Criterion 2"],
            "effort_estimate": 20.0,
            "tags": ["test", "epic"]
        }
        
        result = await client_tools._create_work_item(arguments)
        
        assert len(result) == 1
        response_data = json.loads(result[0].text)
        
        assert response_data["success"] is True
        assert response_data["work_item"]["type"] == "epic"
        assert response_data["work_item"]["title"] == "Test Epic"
        assert response_data["work_item"]["priority"] == "high"
        assert response_data["work_item"]["status"] == "not_started"
        
        # Verify Weaviate was called
        mock_weaviate_manager.store_work_item.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_create_work_item_minimal_args(self, client_tools, mock_weaviate_manager):
        """Test work item creation with minimal arguments."""
        mock_weaviate_manager.store_work_item.return_value = "test-id-456"
        
        arguments = {
            "type": "task",
            "title": "Simple Task",
            "description": "A simple task"
        }
        
        result = await client_tools._create_work_item(arguments)
        
        assert len(result) == 1
        response_data = json.loads(result[0].text)
        
        assert response_data["success"] is True
        assert response_data["work_item"]["priority"] == "medium"  # Default
        assert response_data["work_item"]["acceptance_criteria"] == []  # Default
        assert response_data["work_item"]["tags"] == []  # Default
        
    @pytest.mark.asyncio
    async def test_create_work_item_error(self, client_tools, mock_weaviate_manager):
        """Test work item creation error handling."""
        mock_weaviate_manager.store_work_item.side_effect = Exception("Database error")
        
        arguments = {
            "type": "story",
            "title": "Test Story",
            "description": "Test story description"
        }
        
        result = await client_tools._create_work_item(arguments)
        
        assert len(result) == 1
        response_data = json.loads(result[0].text)
        
        assert response_data["success"] is False
        assert "Database error" in response_data["error"]


class TestGetWorkItem:
    """Test get_work_item tool."""
    
    @pytest.mark.asyncio
    async def test_get_work_item_success(self, client_tools, mock_weaviate_manager, sample_work_item_data):
        """Test successful work item retrieval."""
        mock_weaviate_manager.get_work_item.return_value = sample_work_item_data
        
        arguments = {
            "work_item_id": "test-work-item-001"
        }
        
        result = await client_tools._get_work_item(arguments)
        
        assert len(result) == 1
        response_data = json.loads(result[0].text)
        
        assert response_data["success"] is True
        assert response_data["work_item"]["id"] == "test-work-item-001"
        assert response_data["work_item"]["title"] == "User Authentication System"
        
        mock_weaviate_manager.get_work_item.assert_called_once_with("test-work-item-001")
        
    @pytest.mark.asyncio
    async def test_get_work_item_with_children(self, client_tools, mock_weaviate_manager, sample_work_item_data):
        """Test work item retrieval with children."""
        mock_weaviate_manager.get_work_item.return_value = sample_work_item_data
        mock_weaviate_manager.get_work_item_children.return_value = [
            {"id": "child-1", "title": "Child 1"},
            {"id": "child-2", "title": "Child 2"}
        ]
        
        arguments = {
            "work_item_id": "test-work-item-001",
            "include_children": True
        }
        
        result = await client_tools._get_work_item(arguments)
        
        assert len(result) == 1
        response_data = json.loads(result[0].text)
        
        assert response_data["success"] is True
        assert "children" in response_data
        assert len(response_data["children"]) == 2
        
        mock_weaviate_manager.get_work_item_children.assert_called_once_with("test-work-item-001")
        
    @pytest.mark.asyncio
    async def test_get_work_item_with_dependencies(self, client_tools, mock_weaviate_manager, sample_work_item_data):
        """Test work item retrieval with dependencies."""
        mock_weaviate_manager.get_work_item.return_value = sample_work_item_data
        mock_weaviate_manager.get_work_item_dependencies.return_value = [
            {"id": "dep-1", "title": "Dependency 1"}
        ]
        
        arguments = {
            "work_item_id": "test-work-item-001",
            "include_dependencies": True
        }
        
        result = await client_tools._get_work_item(arguments)
        
        assert len(result) == 1
        response_data = json.loads(result[0].text)
        
        assert response_data["success"] is True
        assert "dependencies" in response_data
        assert len(response_data["dependencies"]) == 1
        
        mock_weaviate_manager.get_work_item_dependencies.assert_called_once_with("test-work-item-001")
        
    @pytest.mark.asyncio
    async def test_get_work_item_not_found(self, client_tools, mock_weaviate_manager):
        """Test work item retrieval when item not found."""
        mock_weaviate_manager.get_work_item.return_value = None
        
        arguments = {
            "work_item_id": "nonexistent-item"
        }
        
        result = await client_tools._get_work_item(arguments)
        
        assert len(result) == 1
        response_data = json.loads(result[0].text)
        
        assert response_data["success"] is False
        assert "not found" in response_data["error"]


class TestUpdateWorkItem:
    """Test update_work_item tool."""
    
    @pytest.mark.asyncio
    async def test_update_work_item_success(self, client_tools, mock_weaviate_manager, sample_work_item_data):
        """Test successful work item update."""
        updated_data = sample_work_item_data.copy()
        updated_data["title"] = "Updated Title"
        updated_data["status"] = "in_progress"
        
        mock_weaviate_manager.update_work_item.return_value = updated_data
        
        arguments = {
            "work_item_id": "test-work-item-001",
            "updates": {
                "title": "Updated Title",
                "status": "in_progress",
                "priority": "critical"
            }
        }
        
        result = await client_tools._update_work_item(arguments)
        
        assert len(result) == 1
        response_data = json.loads(result[0].text)
        
        assert response_data["success"] is True
        assert response_data["work_item"]["title"] == "Updated Title"
        
        # Verify update was called with updated_at timestamp
        call_args = mock_weaviate_manager.update_work_item.call_args
        assert call_args[0][0] == "test-work-item-001"
        assert "updated_at" in call_args[0][1]
        
    @pytest.mark.asyncio
    async def test_update_work_item_not_found(self, client_tools, mock_weaviate_manager):
        """Test work item update when item not found."""
        mock_weaviate_manager.update_work_item.return_value = None
        
        arguments = {
            "work_item_id": "nonexistent-item",
            "updates": {"title": "New Title"}
        }
        
        result = await client_tools._update_work_item(arguments)
        
        assert len(result) == 1
        response_data = json.loads(result[0].text)
        
        assert response_data["success"] is False
        assert "not found" in response_data["error"]


class TestListWorkItems:
    """Test list_work_items tool."""
    
    @pytest.mark.asyncio
    async def test_list_work_items_success(self, client_tools, mock_weaviate_manager, sample_work_item_data):
        """Test successful work items listing."""
        work_items = [sample_work_item_data, sample_work_item_data.copy()]
        work_items[1]["id"] = "test-work-item-002"
        work_items[1]["title"] = "Second Work Item"
        
        mock_weaviate_manager.list_work_items.return_value = work_items
        
        arguments = {
            "limit": 10,
            "offset": 0,
            "sort_by": "created_at",
            "sort_order": "asc"
        }
        
        result = await client_tools._list_work_items(arguments)
        
        assert len(result) == 1
        response_data = json.loads(result[0].text)
        
        assert response_data["success"] is True
        assert response_data["count"] == 2
        assert len(response_data["work_items"]) == 2
        assert response_data["pagination"]["limit"] == 10
        assert response_data["pagination"]["sort_by"] == "created_at"
        
        mock_weaviate_manager.list_work_items.assert_called_once_with(
            filters={},
            limit=10,
            offset=0,
            sort_by="created_at",
            sort_order="asc"
        )
        
    @pytest.mark.asyncio
    async def test_list_work_items_with_filters(self, client_tools, mock_weaviate_manager):
        """Test work items listing with filters."""
        mock_weaviate_manager.list_work_items.return_value = []
        
        arguments = {
            "filters": {
                "type": ["epic", "feature"],
                "status": ["in_progress"],
                "priority": ["high", "critical"]
            },
            "limit": 25
        }
        
        result = await client_tools._list_work_items(arguments)
        
        assert len(result) == 1
        response_data = json.loads(result[0].text)
        
        assert response_data["success"] is True
        assert response_data["filters"] == arguments["filters"]
        
        mock_weaviate_manager.list_work_items.assert_called_once_with(
            filters=arguments["filters"],
            limit=25,
            offset=0,
            sort_by="updated_at",
            sort_order="desc"
        )


class TestSearchWorkItems:
    """Test search_work_items tool."""
    
    @pytest.mark.asyncio
    async def test_search_work_items_semantic(self, client_tools, mock_weaviate_manager, sample_work_item_data):
        """Test semantic search for work items."""
        search_results = [
            {
                "work_item": sample_work_item_data,
                "relevance_score": 0.95,
                "match_highlights": ["authentication", "OAuth2"]
            }
        ]
        
        mock_weaviate_manager.search_work_items.return_value = search_results
        
        arguments = {
            "query": "user authentication OAuth2",
            "search_type": "semantic",
            "limit": 5
        }
        
        result = await client_tools._search_work_items(arguments)
        
        assert len(result) == 1
        response_data = json.loads(result[0].text)
        
        assert response_data["success"] is True
        assert response_data["query"] == "user authentication OAuth2"
        assert response_data["search_type"] == "semantic"
        assert response_data["count"] == 1
        assert len(response_data["results"]) == 1
        
        mock_weaviate_manager.search_work_items.assert_called_once_with(
            query="user authentication OAuth2",
            search_type="semantic",
            filters={},
            limit=5
        )
        
    @pytest.mark.asyncio
    async def test_search_work_items_keyword(self, client_tools, mock_weaviate_manager):
        """Test keyword search for work items."""
        mock_weaviate_manager.search_work_items.return_value = []
        
        arguments = {
            "query": "authentication",
            "search_type": "keyword",
            "filters": {
                "type": ["epic"],
                "status": ["not_started", "in_progress"]
            }
        }
        
        result = await client_tools._search_work_items(arguments)
        
        assert len(result) == 1
        response_data = json.loads(result[0].text)
        
        assert response_data["success"] is True
        assert response_data["search_type"] == "keyword"
        assert response_data["filters"] == arguments["filters"]
        
        mock_weaviate_manager.search_work_items.assert_called_once_with(
            query="authentication",
            search_type="keyword",
            filters=arguments["filters"],
            limit=10
        )


class TestToolCallHandling:
    """Test tool call handling and routing."""
    
    @pytest.mark.asyncio
    async def test_handle_tool_call_routing(self, client_tools, mock_weaviate_manager):
        """Test that tool calls are routed to correct handlers."""
        mock_weaviate_manager.store_work_item.return_value = "test-id"
        
        # Test create_work_item routing
        result = await client_tools.handle_tool_call(
            "create_work_item",
            {
                "type": "task",
                "title": "Test Task",
                "description": "Test description"
            }
        )
        
        assert len(result) == 1
        response_data = json.loads(result[0].text)
        assert response_data["success"] is True
        
    @pytest.mark.asyncio
    async def test_handle_unknown_tool(self, client_tools):
        """Test handling of unknown tool calls."""
        with pytest.raises(ValueError, match="Unknown MCP client tool"):
            await client_tools.handle_tool_call("unknown_tool", {})


class TestIntegration:
    """Integration tests for MCP client tools."""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, client_tools, mock_weaviate_manager):
        """Test a complete workflow: create, get, update, search."""
        # Setup mocks for the workflow
        work_item_data = {
            "id": "workflow-test-001",
            "type": "feature",
            "title": "Payment Integration",
            "description": "Integrate Stripe payment processing",
            "status": "not_started",
            "priority": "high"
        }
        
        mock_weaviate_manager.store_work_item.return_value = "workflow-test-001"
        mock_weaviate_manager.get_work_item.return_value = work_item_data
        mock_weaviate_manager.update_work_item.return_value = work_item_data
        mock_weaviate_manager.search_work_items.return_value = [
            {
                "work_item": work_item_data,
                "relevance_score": 0.9,
                "match_highlights": ["payment", "Stripe"]
            }
        ]
        
        # 1. Create work item
        create_result = await client_tools.handle_tool_call(
            "create_work_item",
            {
                "type": "feature",
                "title": "Payment Integration",
                "description": "Integrate Stripe payment processing",
                "priority": "high"
            }
        )
        
        create_data = json.loads(create_result[0].text)
        assert create_data["success"] is True
        
        # 2. Get work item
        get_result = await client_tools.handle_tool_call(
            "get_work_item",
            {"work_item_id": "workflow-test-001"}
        )
        
        get_data = json.loads(get_result[0].text)
        assert get_data["success"] is True
        assert get_data["work_item"]["title"] == "Payment Integration"
        
        # 3. Update work item
        update_result = await client_tools.handle_tool_call(
            "update_work_item",
            {
                "work_item_id": "workflow-test-001",
                "updates": {"status": "in_progress"}
            }
        )
        
        update_data = json.loads(update_result[0].text)
        assert update_data["success"] is True
        
        # 4. Search for work items
        search_result = await client_tools.handle_tool_call(
            "search_work_items",
            {
                "query": "payment integration",
                "search_type": "semantic"
            }
        )
        
        search_data = json.loads(search_result[0].text)
        assert search_data["success"] is True
        assert search_data["count"] == 1
        
        # Verify all Weaviate methods were called
        mock_weaviate_manager.store_work_item.assert_called_once()
        mock_weaviate_manager.get_work_item.assert_called_once()
        mock_weaviate_manager.update_work_item.assert_called_once()
        mock_weaviate_manager.search_work_items.assert_called_once()