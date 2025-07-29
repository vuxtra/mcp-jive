"""Tests for Storage Sync Tools.

Tests the MCP tool integration for the Task Storage and Sync System.
"""

import sys
import os
from unittest.mock import MagicMock, AsyncMock, patch

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Mock mcp modules before importing
sys.modules['mcp'] = MagicMock()
sys.modules['mcp.types'] = MagicMock()
sys.modules['mcp.server'] = MagicMock()
sys.modules['mcp.server.models'] = MagicMock()
sys.modules['mcp.server.models.InitializationOptions'] = MagicMock()
sys.modules['mcp.server.session'] = MagicMock()
sys.modules['mcp.server.session.ServerSession'] = MagicMock()
sys.modules['mcp.shared'] = MagicMock()
sys.modules['mcp.shared.exceptions'] = MagicMock()
sys.modules['mcp.server.stdio'] = MagicMock()

# Create mock classes
class MockTool:
    def __init__(self, name, description, inputSchema):
        self.name = name
        self.description = description
        self.inputSchema = inputSchema

class MockTextContent:
    def __init__(self, type, text):
        self.type = type
        self.text = text

# Set up the mocks
sys.modules['mcp.types'].Tool = MockTool
sys.modules['mcp.types'].TextContent = MockTextContent

import pytest
import json
from mcp.types import Tool, TextContent

from src.mcp_server.tools.storage_sync import StorageSyncTools
from src.mcp_server.config import ServerConfig
from src.mcp_server.database import WeaviateManager
from src.mcp_server.services.sync_engine import SyncStatus, SyncResult

@pytest.fixture
def mock_config():
    """Mock ServerConfig."""
    config = MagicMock(spec=ServerConfig)
    config.weaviate_url = "http://localhost:8080"
    config.weaviate_api_key = "test-key"
    return config

@pytest.fixture
def mock_weaviate_manager():
    """Mock WeaviateManager."""
    manager = AsyncMock(spec=WeaviateManager)
    return manager

@pytest.fixture
def storage_sync_tools(mock_config, mock_weaviate_manager):
    """Create StorageSyncTools instance with mocked dependencies."""
    return StorageSyncTools(mock_config, mock_weaviate_manager)

@pytest.fixture
def sample_file_content():
    """Sample file content for testing."""
    return json.dumps({
        "id": "task-001",
        "title": "Test Task",
        "description": "This is a test task",
        "type": "task",
        "status": "todo",
        "priority": "medium",
        "assignee": None,
        "parent_id": None,
        "children": [],
        "dependencies": [],
        "tags": [],
        "metadata": {},
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-01T10:00:00Z",
        "estimated_hours": None,
        "actual_hours": None,
        "progress": 0.0
    }, indent=2)

class TestStorageSyncToolsInitialization:
    """Test StorageSyncTools initialization."""
    
    @pytest.mark.asyncio
    async def test_initialization(self, storage_sync_tools):
        """Test tool initialization."""
        await storage_sync_tools.initialize()
        
        assert storage_sync_tools.sync_engine is not None
        assert storage_sync_tools.file_handler is not None
        
    @pytest.mark.asyncio
    async def test_get_tools(self, storage_sync_tools):
        """Test getting available tools."""
        await storage_sync_tools.initialize()
        tools = await storage_sync_tools.get_tools()
        
        assert len(tools) == 3
        tool_names = [tool.name for tool in tools]
        assert "sync_file_to_database" in tool_names
        assert "sync_database_to_file" in tool_names
        assert "get_sync_status" in tool_names
        
        # Verify tool schemas
        for tool in tools:
            assert isinstance(tool, Tool)
            assert tool.name is not None
            assert tool.description is not None
            assert tool.inputSchema is not None
            
    @pytest.mark.asyncio
    async def test_cleanup(self, storage_sync_tools):
        """Test tool cleanup."""
        await storage_sync_tools.initialize()
        await storage_sync_tools.cleanup()
        
        # Should not raise any exceptions

class TestSyncFileToDatabase:
    """Test sync_file_to_database tool."""
    
    @pytest.mark.asyncio
    async def test_sync_file_to_database_success(self, storage_sync_tools, sample_file_content):
        """Test successful file to database sync."""
        await storage_sync_tools.initialize()
        
        # Mock successful sync
        mock_result = SyncResult(
            status=SyncStatus.SUCCESS,
            message="Successfully synced file to database",
            file_path="test.json",
            work_item_id="task-001"
        )
        
        with patch.object(storage_sync_tools.sync_engine, 'sync_file_to_database', 
                         return_value=mock_result) as mock_sync:
            
            result = await storage_sync_tools.handle_tool_call(
                "sync_file_to_database",
                {
                    "file_path": "test.json",
                    "file_content": sample_file_content,
                    "conflict_resolution": "auto_merge"
                }
            )
            
            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], TextContent)
            
            # Parse result content
            result_data = json.loads(result[0].text)
            assert result_data["status"] == "success"
            assert result_data["file_path"] == "test.json"
            assert result_data["work_item_id"] == "task-001"
            
            # Verify sync engine was called correctly
            mock_sync.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_sync_file_to_database_invalid_content(self, storage_sync_tools):
        """Test file to database sync with invalid content."""
        await storage_sync_tools.initialize()
        
        result = await storage_sync_tools.handle_tool_call(
            "sync_file_to_database",
            {
                "file_path": "test.json",
                "file_content": "invalid json content",
                "conflict_resolution": "auto_merge"
            }
        )
        
        assert isinstance(result, list)
        result_data = json.loads(result[0].text)
        assert result_data["status"] == "error"
        assert "Invalid file content" in result_data["message"]
        
    @pytest.mark.asyncio
    async def test_sync_file_to_database_missing_params(self, storage_sync_tools):
        """Test file to database sync with missing parameters."""
        await storage_sync_tools.initialize()
        
        result = await storage_sync_tools.handle_tool_call(
            "sync_file_to_database",
            {
                "file_path": "test.json"
                # Missing file_content
            }
        )
        
        assert isinstance(result, list)
        result_data = json.loads(result[0].text)
        assert result_data["status"] == "error"
        assert "Missing required parameter" in result_data["message"]
        
    @pytest.mark.asyncio
    async def test_sync_file_to_database_conflict(self, storage_sync_tools, sample_file_content):
        """Test file to database sync with conflict."""
        await storage_sync_tools.initialize()
        
        # Mock conflict result
        mock_result = SyncResult(
            status=SyncStatus.CONFLICT,
            message="Manual resolution required",
            file_path="test.json",
            work_item_id="task-001",
            conflicts=["Field 'title' differs"]
        )
        
        with patch.object(storage_sync_tools.sync_engine, 'sync_file_to_database',
                         return_value=mock_result):
            
            result = await storage_sync_tools.handle_tool_call(
                "sync_file_to_database",
                {
                    "file_path": "test.json",
                    "file_content": sample_file_content,
                    "conflict_resolution": "manual_resolution"
                }
            )
            
            result_data = json.loads(result[0].text)
            assert result_data["status"] == "conflict"
            assert len(result_data["conflicts"]) > 0

class TestSyncDatabaseToFile:
    """Test sync_database_to_file tool."""
    
    @pytest.mark.asyncio
    async def test_sync_database_to_file_success(self, storage_sync_tools):
        """Test successful database to file sync."""
        await storage_sync_tools.initialize()
        
        # Mock successful sync
        mock_result = SyncResult(
            status=SyncStatus.SUCCESS,
            message="Successfully synced database to file",
            file_path=".jivedev/tasks/task/task-001_test_task.json",
            work_item_id="task-001",
            metadata={"file_content": '{"id": "task-001"}'}
        )
        
        with patch.object(storage_sync_tools.sync_engine, 'sync_database_to_file',
                         return_value=mock_result) as mock_sync:
            
            result = await storage_sync_tools.handle_tool_call(
                "sync_database_to_file",
                {
                    "work_item_id": "task-001",
                    "target_format": ".json",
                    "conflict_resolution": "auto_merge"
                }
            )
            
            assert isinstance(result, list)
            result_data = json.loads(result[0].text)
            assert result_data["status"] == "success"
            assert result_data["work_item_id"] == "task-001"
            assert "file_content" in result_data
            
            mock_sync.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_sync_database_to_file_not_found(self, storage_sync_tools):
        """Test database to file sync with missing work item."""
        await storage_sync_tools.initialize()
        
        # Mock not found result
        mock_result = SyncResult(
            status=SyncStatus.ERROR,
            message="Work item not found in database",
            work_item_id="nonexistent-task"
        )
        
        with patch.object(storage_sync_tools.sync_engine, 'sync_database_to_file',
                         return_value=mock_result):
            
            result = await storage_sync_tools.handle_tool_call(
                "sync_database_to_file",
                {
                    "work_item_id": "nonexistent-task",
                    "target_format": ".json"
                }
            )
            
            result_data = json.loads(result[0].text)
            assert result_data["status"] == "error"
            assert "not found" in result_data["message"]
            
    @pytest.mark.asyncio
    async def test_sync_database_to_file_invalid_format(self, storage_sync_tools):
        """Test database to file sync with invalid format."""
        await storage_sync_tools.initialize()
        
        result = await storage_sync_tools.handle_tool_call(
            "sync_database_to_file",
            {
                "work_item_id": "task-001",
                "target_format": ".invalid"
            }
        )
        
        result_data = json.loads(result[0].text)
        assert result_data["status"] == "error"
        assert "Unsupported target format" in result_data["message"]
        
    @pytest.mark.asyncio
    async def test_sync_database_to_file_missing_params(self, storage_sync_tools):
        """Test database to file sync with missing parameters."""
        await storage_sync_tools.initialize()
        
        result = await storage_sync_tools.handle_tool_call(
            "sync_database_to_file",
            {
                # Missing work_item_id
                "target_format": ".json"
            }
        )
        
        result_data = json.loads(result[0].text)
        assert result_data["status"] == "error"
        assert "Missing required parameter" in result_data["message"]

class TestGetSyncStatus:
    """Test get_sync_status tool."""
    
    @pytest.mark.asyncio
    async def test_get_sync_status_synced(self, storage_sync_tools):
        """Test getting sync status for synced item."""
        await storage_sync_tools.initialize()
        
        # Mock sync status
        mock_status = {
            "identifier": "task-001",
            "status": "synced",
            "last_sync": "2024-01-01T10:00:00Z",
            "work_item_id": "task-001",
            "file_path": "test.json"
        }
        
        with patch.object(storage_sync_tools.sync_engine, 'get_sync_status',
                         return_value=mock_status) as mock_get_status:
            
            result = await storage_sync_tools.handle_tool_call(
                "get_sync_status",
                {"identifier": "task-001"}
            )
            
            assert isinstance(result, list)
            result_data = json.loads(result[0].text)
            assert result_data["identifier"] == "task-001"
            assert result_data["status"] == "synced"
            assert "last_sync" in result_data
            
            mock_get_status.assert_called_once_with("task-001")
            
    @pytest.mark.asyncio
    async def test_get_sync_status_not_found(self, storage_sync_tools):
        """Test getting sync status for unknown identifier."""
        await storage_sync_tools.initialize()
        
        # Mock not found status
        mock_status = {
            "identifier": "unknown-id",
            "status": "not_found",
            "message": "No sync information found"
        }
        
        with patch.object(storage_sync_tools.sync_engine, 'get_sync_status',
                         return_value=mock_status):
            
            result = await storage_sync_tools.handle_tool_call(
                "get_sync_status",
                {"identifier": "unknown-id"}
            )
            
            result_data = json.loads(result[0].text)
            assert result_data["status"] == "not_found"
            assert "No sync information found" in result_data["message"]
            
    @pytest.mark.asyncio
    async def test_get_sync_status_missing_params(self, storage_sync_tools):
        """Test getting sync status with missing parameters."""
        await storage_sync_tools.initialize()
        
        result = await storage_sync_tools.handle_tool_call(
            "get_sync_status",
            {}  # Missing identifier
        )
        
        result_data = json.loads(result[0].text)
        assert result_data["status"] == "error"
        assert "Missing required parameter" in result_data["message"]

class TestToolValidation:
    """Test tool input validation."""
    
    @pytest.mark.asyncio
    async def test_validate_file_content_json(self, storage_sync_tools):
        """Test JSON file content validation."""
        await storage_sync_tools.initialize()
        
        # Valid JSON
        valid_json = '{"id": "test", "title": "Test"}'
        assert await storage_sync_tools._validate_file_content(valid_json, "test.json")
        
        # Invalid JSON
        invalid_json = '{"id": "test", "title":}'
        assert not await storage_sync_tools._validate_file_content(invalid_json, "test.json")
        
    @pytest.mark.asyncio
    async def test_validate_file_content_yaml(self, storage_sync_tools):
        """Test YAML file content validation."""
        await storage_sync_tools.initialize()
        
        # Valid YAML
        valid_yaml = 'id: test\ntitle: Test'
        assert await storage_sync_tools._validate_file_content(valid_yaml, "test.yaml")
        
        # Invalid YAML
        invalid_yaml = 'id: test\ntitle: ['
        assert not await storage_sync_tools._validate_file_content(invalid_yaml, "test.yaml")
        
    @pytest.mark.asyncio
    async def test_validate_file_content_unsupported(self, storage_sync_tools):
        """Test validation of unsupported file format."""
        await storage_sync_tools.initialize()
        
        content = "some content"
        assert not await storage_sync_tools._validate_file_content(content, "test.txt")
        
    @pytest.mark.asyncio
    async def test_validate_work_item_data(self, storage_sync_tools):
        """Test work item data validation."""
        await storage_sync_tools.initialize()
        
        # Valid work item data
        valid_data = {
            "id": "task-001",
            "title": "Test Task",
            "description": "Test description",
            "type": "task",
            "status": "todo",
            "priority": "medium",
            "created_at": "2024-01-01T10:00:00Z",
            "updated_at": "2024-01-01T10:00:00Z"
        }
        
        assert await storage_sync_tools._validate_work_item_data(valid_data)
        
        # Invalid work item data - missing required fields
        invalid_data = {"id": "task-001", "title": "Test"}
        assert not await storage_sync_tools._validate_work_item_data(invalid_data)

class TestErrorHandling:
    """Test error handling scenarios."""
    
    @pytest.mark.asyncio
    async def test_handle_unknown_tool(self, storage_sync_tools):
        """Test handling unknown tool call."""
        await storage_sync_tools.initialize()
        
        result = await storage_sync_tools.handle_tool_call(
            "unknown_tool",
            {"param": "value"}
        )
        
        assert isinstance(result, list)
        result_data = json.loads(result[0].text)
        assert result_data["status"] == "error"
        assert "Unknown tool" in result_data["message"]
        
    @pytest.mark.asyncio
    async def test_handle_tool_call_exception(self, storage_sync_tools, sample_file_content):
        """Test handling exceptions during tool calls."""
        await storage_sync_tools.initialize()
        
        # Mock sync engine to raise exception
        with patch.object(storage_sync_tools.sync_engine, 'sync_file_to_database',
                         side_effect=Exception("Test exception")):
            
            result = await storage_sync_tools.handle_tool_call(
                "sync_file_to_database",
                {
                    "file_path": "test.json",
                    "file_content": sample_file_content
                }
            )
            
            result_data = json.loads(result[0].text)
            assert result_data["status"] == "error"
            assert "Test exception" in result_data["message"]

class TestConflictResolutionMapping:
    """Test conflict resolution strategy mapping."""
    
    @pytest.mark.asyncio
    async def test_valid_conflict_resolution_strategies(self, storage_sync_tools, sample_file_content):
        """Test all valid conflict resolution strategies."""
        await storage_sync_tools.initialize()
        
        valid_strategies = [
            "auto_merge", "file_wins", "database_wins", 
            "manual_resolution", "create_branch"
        ]
        
        for strategy in valid_strategies:
            # Mock successful sync for each strategy
            mock_result = SyncResult(
                status=SyncStatus.SUCCESS,
                message=f"Success with {strategy}",
                file_path="test.json",
                work_item_id="task-001"
            )
            
            with patch.object(storage_sync_tools.sync_engine, 'sync_file_to_database',
                             return_value=mock_result):
                
                result = await storage_sync_tools.handle_tool_call(
                    "sync_file_to_database",
                    {
                        "file_path": "test.json",
                        "file_content": sample_file_content,
                        "conflict_resolution": strategy
                    }
                )
                
                result_data = json.loads(result[0].text)
                assert result_data["status"] == "success"
                
    @pytest.mark.asyncio
    async def test_invalid_conflict_resolution_strategy(self, storage_sync_tools, sample_file_content):
        """Test invalid conflict resolution strategy."""
        await storage_sync_tools.initialize()
        
        result = await storage_sync_tools.handle_tool_call(
            "sync_file_to_database",
            {
                "file_path": "test.json",
                "file_content": sample_file_content,
                "conflict_resolution": "invalid_strategy"
            }
        )
        
        result_data = json.loads(result[0].text)
        assert result_data["status"] == "error"
        assert "Invalid conflict resolution strategy" in result_data["message"]

class TestTargetFormatValidation:
    """Test target format validation."""
    
    @pytest.mark.asyncio
    async def test_valid_target_formats(self, storage_sync_tools):
        """Test all valid target formats."""
        await storage_sync_tools.initialize()
        
        valid_formats = [".json", ".yaml", ".yml", ".md"]
        
        for format_type in valid_formats:
            # Mock successful sync for each format
            mock_result = SyncResult(
                status=SyncStatus.SUCCESS,
                message=f"Success with {format_type}",
                file_path=f"test{format_type}",
                work_item_id="task-001",
                metadata={"file_content": "test content"}
            )
            
            with patch.object(storage_sync_tools.sync_engine, 'sync_database_to_file',
                             return_value=mock_result):
                
                result = await storage_sync_tools.handle_tool_call(
                    "sync_database_to_file",
                    {
                        "work_item_id": "task-001",
                        "target_format": format_type
                    }
                )
                
                result_data = json.loads(result[0].text)
                assert result_data["status"] == "success"