"""Comprehensive tests for consolidated MCP tools.

Tests the new consolidated tools for functionality, performance,
and backward compatibility with legacy tools.
"""

import pytest
import asyncio
import json
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

# Import consolidated tools
from src.mcp_jive.tools.consolidated import (
    ConsolidatedToolRegistry,
    create_consolidated_registry,
    UnifiedWorkItemTool,
    UnifiedRetrievalTool,
    UnifiedSearchTool,
    UnifiedHierarchyTool,
    UnifiedExecutionTool,
    UnifiedProgressTool,
    UnifiedStorageTool,
    BackwardCompatibilityWrapper,
    CONSOLIDATED_TOOLS,
    LEGACY_TOOLS_REPLACED
)

from src.mcp_jive.tools.consolidated_registry import MCPConsolidatedToolRegistry
from src.mcp_jive.tools.tool_config import ToolConfiguration, ToolMode
# from src.mcp_jive.storage.work_item_storage import WorkItemStorage  # Module doesn't exist


class TestConsolidatedTools:
    """Test suite for consolidated tools functionality."""
    
    @pytest.fixture
    async def mock_storage(self):
        """Create a mock storage instance."""
        storage = Mock()  # Mock storage without specific spec
        storage.is_initialized = True
        storage.initialize = AsyncMock()
        storage.cleanup = AsyncMock()
        
        # Mock storage methods
        storage.create_work_item = AsyncMock(return_value={
            "id": "test-123",
            "title": "Test Item",
            "type": "task",
            "status": "todo",
            "created_at": datetime.now().isoformat()
        })
        
        storage.get_work_item = AsyncMock(return_value={
            "id": "test-123",
            "title": "Test Item",
            "type": "task",
            "status": "todo"
        })
        
        storage.update_work_item = AsyncMock(return_value={
            "id": "test-123",
            "title": "Updated Test Item",
            "type": "task",
            "status": "in_progress"
        })
        
        storage.delete_work_item = AsyncMock(return_value=True)
        
        storage.list_work_items = AsyncMock(return_value={
            "items": [
                {"id": "test-123", "title": "Test Item 1"},
                {"id": "test-456", "title": "Test Item 2"}
            ],
            "total": 2,
            "page": 1,
            "per_page": 10
        })
        
        storage.search_work_items = AsyncMock(return_value={
            "results": [
                {"id": "test-123", "title": "Test Item", "score": 0.95}
            ],
            "total": 1
        })
        
        return storage
    
    @pytest.fixture
    async def consolidated_registry(self, mock_storage):
        """Create a consolidated tool registry for testing."""
        registry = create_consolidated_registry(
            storage=mock_storage,
            enable_legacy_support=True
        )
        return registry
    
    @pytest.fixture
    async def mcp_registry(self, mock_storage):
        """Create an MCP consolidated tool registry for testing."""
        registry = MCPConsolidatedToolRegistry(
            enable_legacy_support=True,
            mode="consolidated"
        )
        registry.storage = mock_storage
        await registry.initialize()
        return registry


class TestUnifiedWorkItemTool:
    """Test the unified work item management tool."""
    
    @pytest.fixture
    def work_item_tool(self, mock_storage):
        return UnifiedWorkItemTool(mock_storage)
    
    @pytest.mark.asyncio
    async def test_create_work_item(self, work_item_tool, mock_storage):
        """Test creating a work item."""
        result = await work_item_tool.handle_tool_call("jive_manage_work_item", {
            "action": "create",
            "type": "task",
            "title": "Test Task",
            "description": "Test description",
            "priority": "high"
        })
        
        assert result["success"] is True
        assert "id" in result["data"]
        mock_storage.create_work_item.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_work_item(self, work_item_tool, mock_storage):
        """Test updating a work item."""
        result = await work_item_tool.handle_tool_call("jive_manage_work_item", {
            "action": "update",
            "work_item_id": "test-123",
            "title": "Updated Task",
            "status": "in_progress"
        })
        
        assert result["success"] is True
        mock_storage.update_work_item.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_work_item(self, work_item_tool, mock_storage):
        """Test deleting a work item."""
        result = await work_item_tool.handle_tool_call("jive_manage_work_item", {
            "action": "delete",
            "work_item_id": "test-123"
        })
        
        assert result["success"] is True
        mock_storage.delete_work_item.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_invalid_action(self, work_item_tool):
        """Test handling invalid action."""
        result = await work_item_tool.handle_tool_call("jive_manage_work_item", {
            "action": "invalid_action"
        })
        
        assert result["success"] is False
        assert "error" in result


class TestUnifiedRetrievalTool:
    """Test the unified retrieval tool."""
    
    @pytest.fixture
    def retrieval_tool(self, mock_storage):
        return UnifiedRetrievalTool(mock_storage)
    
    @pytest.mark.asyncio
    async def test_get_single_work_item(self, retrieval_tool, mock_storage):
        """Test retrieving a single work item."""
        result = await retrieval_tool.handle_tool_call("jive_get_work_item", {
            "work_item_id": "test-123"
        })
        
        assert result["success"] is True
        assert result["data"]["id"] == "test-123"
        mock_storage.get_work_item.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_list_work_items(self, retrieval_tool, mock_storage):
        """Test listing work items with filters."""
        result = await retrieval_tool.handle_tool_call("jive_get_work_item", {
            "filters": {
                "type": "task",
                "status": "todo"
            },
            "limit": 10
        })
        
        assert result["success"] is True
        assert "items" in result["data"]
        assert len(result["data"]["items"]) == 2
        mock_storage.list_work_items.assert_called_once()


class TestUnifiedSearchTool:
    """Test the unified search tool."""
    
    @pytest.fixture
    def search_tool(self, mock_storage):
        return UnifiedSearchTool(mock_storage)
    
    @pytest.mark.asyncio
    async def test_semantic_search(self, search_tool, mock_storage):
        """Test semantic search functionality."""
        result = await search_tool.handle_tool_call("jive_search_content", {
            "query": "authentication feature",
            "search_type": "semantic",
            "content_types": ["work_item", "description"],
            "limit": 5
        })
        
        assert result["success"] is True
        assert "results" in result["data"]
        mock_storage.search_work_items.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_keyword_search(self, search_tool, mock_storage):
        """Test keyword search functionality."""
        result = await search_tool.handle_tool_call("jive_search_content", {
            "query": "test task",
            "search_type": "keyword",
            "content_types": ["title"],
            "limit": 10
        })
        
        assert result["success"] is True
        assert "results" in result["data"]


class TestBackwardCompatibility:
    """Test backward compatibility with legacy tools."""
    
    @pytest.fixture
    def compatibility_wrapper(self, consolidated_registry):
        return BackwardCompatibilityWrapper(consolidated_registry)
    
    @pytest.mark.asyncio
    async def test_legacy_create_work_item(self, compatibility_wrapper):
        """Test legacy jive_create_work_item mapping."""
        result = await compatibility_wrapper.handle_legacy_call(
            "jive_create_work_item",
            {
                "title": "Legacy Task",
                "type": "task",
                "description": "Created via legacy API"
            }
        )
        
        assert result["success"] is True
        assert "mapped_to" in result
        assert result["mapped_to"] == "jive_manage_work_item"
    
    @pytest.mark.asyncio
    async def test_legacy_get_work_item(self, compatibility_wrapper):
        """Test legacy jive_get_work_item mapping."""
        result = await compatibility_wrapper.handle_legacy_call(
            "jive_get_work_item",
            {"work_item_id": "test-123"}
        )
        
        assert result["success"] is True
        assert "mapped_to" in result
        assert result["mapped_to"] == "jive_get_work_item"
    
    @pytest.mark.asyncio
    async def test_legacy_search_work_items(self, compatibility_wrapper):
        """Test legacy jive_search_work_items mapping."""
        result = await compatibility_wrapper.handle_legacy_call(
            "jive_search_work_items",
            {
                "query": "test search",
                "limit": 5
            }
        )
        
        assert result["success"] is True
        assert "mapped_to" in result
        assert result["mapped_to"] == "jive_search_content"
    
    def test_get_migration_info(self, compatibility_wrapper):
        """Test getting migration information for legacy tools."""
        info = compatibility_wrapper.get_migration_info("jive_create_work_item")
        
        assert info is not None
        assert "new_tool" in info
        assert "parameter_mapping" in info
        assert "description" in info
        assert info["new_tool"] == "jive_manage_work_item"


class TestMCPConsolidatedRegistry:
    """Test the MCP consolidated tool registry."""
    
    @pytest.mark.asyncio
    async def test_registry_initialization(self, mcp_registry):
        """Test registry initialization."""
        assert mcp_registry.is_initialized
        assert mcp_registry.mode == "consolidated"
        assert len(mcp_registry.tools) >= len(CONSOLIDATED_TOOLS)
    
    @pytest.mark.asyncio
    async def test_list_tools(self, mcp_registry):
        """Test listing available tools."""
        tools = await mcp_registry.list_tools()
        
        assert len(tools) >= len(CONSOLIDATED_TOOLS)
        tool_names = [tool.name for tool in tools]
        
        # Check that all consolidated tools are present
        for tool_name in CONSOLIDATED_TOOLS:
            assert tool_name in tool_names
    
    @pytest.mark.asyncio
    async def test_call_consolidated_tool(self, mcp_registry):
        """Test calling a consolidated tool."""
        result = await mcp_registry.call_tool("jive_manage_work_item", {
            "action": "create",
            "type": "task",
            "title": "Test via MCP Registry"
        })
        
        assert len(result) == 1
        assert result[0].type == "text"
        
        # Parse the JSON response
        response_data = json.loads(result[0].text)
        assert response_data["success"] is True
    
    @pytest.mark.asyncio
    async def test_call_legacy_tool(self, mcp_registry):
        """Test calling a legacy tool through compatibility layer."""
        result = await mcp_registry.call_tool("jive_create_work_item", {
            "title": "Legacy Test",
            "type": "task"
        })
        
        assert len(result) == 1
        response_data = json.loads(result[0].text)
        assert response_data["success"] is True
    
    @pytest.mark.asyncio
    async def test_get_registry_stats(self, mcp_registry):
        """Test getting registry statistics."""
        # Make some tool calls first
        await mcp_registry.call_tool("jive_manage_work_item", {
            "action": "create", "type": "task", "title": "Test"
        })
        await mcp_registry.call_tool("jive_create_work_item", {
            "title": "Legacy Test", "type": "task"
        })
        
        stats = await mcp_registry.get_registry_stats()
        
        assert "mode" in stats
        assert "tools" in stats
        assert "calls" in stats
        assert "performance" in stats
        assert stats["calls"]["total"] >= 2
        assert stats["calls"]["legacy"] >= 1
    
    @pytest.mark.asyncio
    async def test_disable_legacy_support(self, mcp_registry):
        """Test disabling legacy support."""
        # Verify legacy tools are initially available
        tools_before = await mcp_registry.list_tools()
        legacy_tools_before = [t for t in tools_before if t.name in LEGACY_TOOLS_REPLACED]
        assert len(legacy_tools_before) > 0
        
        # Disable legacy support
        await mcp_registry.disable_legacy_support()
        
        # Verify legacy tools are removed
        tools_after = await mcp_registry.list_tools()
        legacy_tools_after = [t for t in tools_after if t.name in LEGACY_TOOLS_REPLACED]
        assert len(legacy_tools_after) == 0
        
        # Verify consolidated tools are still available
        consolidated_tools_after = [t for t in tools_after if t.name in CONSOLIDATED_TOOLS]
        assert len(consolidated_tools_after) == len(CONSOLIDATED_TOOLS)


class TestToolConfiguration:
    """Test tool configuration management."""
    
    def test_default_configuration(self):
        """Test default configuration values."""
        config = ToolConfiguration()
        
        assert config.mode == ToolMode.CONSOLIDATED
        assert config.enable_legacy_support is True
        assert config.enable_ai_orchestration is False
        assert config.enable_quality_gates is False
    
    def test_production_configuration(self):
        """Test production configuration."""
        from src.mcp_jive.tools.tool_config import get_production_config
        
        config = get_production_config()
        
        assert config.mode == ToolMode.CONSOLIDATED
        assert config.enable_legacy_support is False
        assert config.legacy_deprecation_warnings is False
        assert config.migration_mode is False
    
    def test_migration_configuration(self):
        """Test migration configuration."""
        from src.mcp_jive.tools.tool_config import get_migration_config
        
        config = get_migration_config()
        
        assert config.mode == ToolMode.MINIMAL
        assert config.enable_legacy_support is True
        assert config.legacy_deprecation_warnings is True
        assert config.migration_mode is True
    
    def test_configuration_validation(self):
        """Test configuration validation."""
        # Valid configuration
        config = ToolConfiguration()
        issues = config.validate()
        assert len(issues) == 0
        
        # Invalid configuration
        config = ToolConfiguration(
            mode=ToolMode.CONSOLIDATED,
            enable_ai_orchestration=True,  # Not allowed in consolidated mode
            cache_ttl_seconds=-1  # Invalid value
        )
        issues = config.validate()
        assert len(issues) > 0
        assert any("AI Orchestration" in issue for issue in issues)
        assert any("cache TTL" in issue for issue in issues)


class TestPerformance:
    """Test performance characteristics of consolidated tools."""
    
    @pytest.mark.asyncio
    async def test_concurrent_tool_calls(self, mcp_registry):
        """Test handling concurrent tool calls."""
        # Create multiple concurrent tool calls
        tasks = []
        for i in range(10):
            task = mcp_registry.call_tool("jive_manage_work_item", {
                "action": "create",
                "type": "task",
                "title": f"Concurrent Task {i}"
            })
            tasks.append(task)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all calls succeeded
        for result in results:
            assert not isinstance(result, Exception)
            assert len(result) == 1
            response_data = json.loads(result[0].text)
            assert response_data["success"] is True
    
    @pytest.mark.asyncio
    async def test_tool_call_timing(self, mcp_registry):
        """Test tool call response times."""
        start_time = datetime.now()
        
        await mcp_registry.call_tool("jive_get_work_item", {
            "work_item_id": "test-123"
        })
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Tool call should complete within reasonable time
        assert duration < 1.0  # Less than 1 second


class TestErrorHandling:
    """Test error handling in consolidated tools."""
    
    @pytest.mark.asyncio
    async def test_invalid_tool_name(self, mcp_registry):
        """Test calling non-existent tool."""
        result = await mcp_registry.call_tool("invalid_tool_name", {})
        
        assert len(result) == 1
        response_data = json.loads(result[0].text)
        assert "error" in response_data
        assert "not found" in response_data["error"].lower()
    
    @pytest.mark.asyncio
    async def test_invalid_parameters(self, mcp_registry):
        """Test calling tool with invalid parameters."""
        result = await mcp_registry.call_tool("jive_manage_work_item", {
            "action": "invalid_action"
        })
        
        assert len(result) == 1
        response_data = json.loads(result[0].text)
        assert response_data["success"] is False
        assert "error" in response_data
    
    @pytest.mark.asyncio
    async def test_storage_error_handling(self, mcp_registry):
        """Test handling storage errors gracefully."""
        # Mock storage to raise an exception
        mcp_registry.storage.get_work_item = AsyncMock(side_effect=Exception("Storage error"))
        
        result = await mcp_registry.call_tool("jive_get_work_item", {
            "work_item_id": "test-123"
        })
        
        assert len(result) == 1
        response_data = json.loads(result[0].text)
        assert "error" in response_data


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])