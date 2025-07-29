"""Tests for Sync Engine.

Tests bidirectional synchronization between files and database.
"""

import pytest
import json
import os
import sys
import importlib.util
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import sync engine
spec = importlib.util.spec_from_file_location(
    "sync_engine", 
    os.path.join(os.path.dirname(__file__), '..', 'src', 'mcp_server', 'services', 'sync_engine.py')
)
sync_engine_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync_engine_module)

SyncEngine = sync_engine_module.SyncEngine
SyncDirection = sync_engine_module.SyncDirection
ConflictResolution = sync_engine_module.ConflictResolution
SyncStatus = sync_engine_module.SyncStatus
SyncResult = sync_engine_module.SyncResult

# Import file format handler
spec = importlib.util.spec_from_file_location(
    "file_format_handler", 
    os.path.join(os.path.dirname(__file__), '..', 'src', 'mcp_server', 'services', 'file_format_handler.py')
)
file_format_handler_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(file_format_handler_module)

WorkItemSchema = file_format_handler_module.WorkItemSchema

# Import config
spec = importlib.util.spec_from_file_location(
    "config", 
    os.path.join(os.path.dirname(__file__), '..', 'src', 'mcp_server', 'config.py')
)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)

ServerConfig = config_module.ServerConfig

# Import database
spec = importlib.util.spec_from_file_location(
    "database", 
    os.path.join(os.path.dirname(__file__), '..', 'src', 'mcp_server', 'database.py')
)
database_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(database_module)

WeaviateManager = database_module.WeaviateManager

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
def sync_engine(mock_config, mock_weaviate_manager):
    """Create SyncEngine instance with mocked dependencies."""
    return SyncEngine(mock_config, mock_weaviate_manager)

@pytest.fixture
def sample_work_item_data():
    """Sample work item data for testing."""
    return {
        "id": "task-001",
        "title": "Test Task",
        "description": "This is a test task",
        "type": "task",
        "status": "todo",
        "priority": "medium",
        "assignee": "john.doe",
        "parent_id": None,
        "children": [],
        "dependencies": [],
        "tags": ["test"],
        "metadata": {},
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-01T10:00:00Z",
        "estimated_hours": 8.0,
        "actual_hours": 0.0,
        "progress": 0.0
    }

@pytest.fixture
def sample_work_item(sample_work_item_data):
    """Create WorkItemSchema instance."""
    return WorkItemSchema(**sample_work_item_data)

class TestSyncResult:
    """Test SyncResult functionality."""
    
    def test_sync_result_creation(self):
        """Test creating SyncResult."""
        result = SyncResult(
            status=SyncStatus.SUCCESS,
            message="Test message",
            file_path="test.json",
            work_item_id="task-001"
        )
        
        assert result.status == SyncStatus.SUCCESS
        assert result.message == "Test message"
        assert result.file_path == "test.json"
        assert result.work_item_id == "task-001"
        assert result.conflicts == []
        assert result.metadata == {}
        assert result.timestamp is not None
        
    def test_sync_result_to_dict(self):
        """Test converting SyncResult to dictionary."""
        result = SyncResult(
            status=SyncStatus.CONFLICT,
            message="Conflict detected",
            conflicts=["Field 'title' differs"],
            metadata={"test": "value"}
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["status"] == "conflict"
        assert result_dict["message"] == "Conflict detected"
        assert result_dict["conflicts"] == ["Field 'title' differs"]
        assert result_dict["metadata"] == {"test": "value"}
        assert "timestamp" in result_dict

class TestSyncEngine:
    """Test SyncEngine core functionality."""
    
    @pytest.mark.asyncio
    async def test_initialize(self, sync_engine):
        """Test sync engine initialization."""
        await sync_engine.initialize()
        
        assert sync_engine.sync_state == {}
        assert sync_engine.active_syncs == {}
        
    @pytest.mark.asyncio
    async def test_calculate_checksum(self, sync_engine):
        """Test checksum calculation."""
        content = "test content"
        checksum1 = await sync_engine._calculate_checksum(content)
        checksum2 = await sync_engine._calculate_checksum(content)
        
        assert checksum1 == checksum2
        assert len(checksum1) == 64  # SHA256 hex length
        
        # Different content should produce different checksum
        different_checksum = await sync_engine._calculate_checksum("different content")
        assert checksum1 != different_checksum
        
    @pytest.mark.asyncio
    async def test_generate_file_path(self, sync_engine, sample_work_item):
        """Test file path generation."""
        file_path = await sync_engine._generate_file_path(sample_work_item, ".json")
        
        assert file_path.startswith(".jivedev/tasks/")
        assert file_path.endswith(".json")
        assert "task-001" in file_path
        assert "test_task" in file_path.lower()
        
    @pytest.mark.asyncio
    async def test_update_sync_state(self, sync_engine):
        """Test sync state update."""
        file_path = "test.json"
        work_item_id = "task-001"
        content = "test content"
        
        await sync_engine._update_sync_state(file_path, work_item_id, content)
        
        # Check file path entry
        assert file_path in sync_engine.sync_state
        state = sync_engine.sync_state[file_path]
        assert state["work_item_id"] == work_item_id
        assert state["file_path"] == file_path
        assert "checksum" in state
        assert "last_sync" in state
        
        # Check work item ID entry
        assert work_item_id in sync_engine.sync_state
        assert sync_engine.sync_state[work_item_id] == state

class TestFileToDatabase:
    """Test file to database synchronization."""
    
    @pytest.mark.asyncio
    async def test_sync_file_to_database_success(self, sync_engine, sample_work_item_data):
        """Test successful file to database sync."""
        file_path = "test.json"
        file_content = json.dumps(sample_work_item_data)
        
        # Mock no existing item in database
        sync_engine._get_work_item_from_db = AsyncMock(return_value=None)
        sync_engine._update_work_item_in_db = AsyncMock()
        
        result = await sync_engine.sync_file_to_database(file_path, file_content)
        
        assert result.status == SyncStatus.SUCCESS
        assert result.file_path == file_path
        assert result.work_item_id == "task-001"
        assert "Successfully synced" in result.message
        
        # Verify database update was called
        sync_engine._update_work_item_in_db.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_sync_file_to_database_parse_error(self, sync_engine):
        """Test file to database sync with parse error."""
        file_path = "test.json"
        file_content = "invalid json content"
        
        result = await sync_engine.sync_file_to_database(file_path, file_content)
        
        assert result.status == SyncStatus.ERROR
        assert "Failed to parse" in result.message
        assert result.file_path == file_path
        
    @pytest.mark.asyncio
    async def test_sync_file_to_database_with_conflict(self, sync_engine, sample_work_item_data):
        """Test file to database sync with conflict resolution."""
        file_path = "test.json"
        file_content = json.dumps(sample_work_item_data)
        
        # Mock existing item with different data
        existing_item = sample_work_item_data.copy()
        existing_item["title"] = "Different Title"
        existing_item["updated_at"] = "2024-01-01T09:00:00Z"  # Earlier timestamp
        
        sync_engine._get_work_item_from_db = AsyncMock(return_value=existing_item)
        sync_engine._update_work_item_in_db = AsyncMock()
        
        result = await sync_engine.sync_file_to_database(
            file_path, file_content, ConflictResolution.FILE_WINS
        )
        
        assert result.status == SyncStatus.SUCCESS
        assert "Successfully synced" in result.message
        
    @pytest.mark.asyncio
    async def test_sync_file_to_database_manual_conflict(self, sync_engine, sample_work_item_data):
        """Test file to database sync requiring manual conflict resolution."""
        file_path = "test.json"
        file_content = json.dumps(sample_work_item_data)
        
        # Mock existing item with different data
        existing_item = sample_work_item_data.copy()
        existing_item["title"] = "Different Title"
        
        sync_engine._get_work_item_from_db = AsyncMock(return_value=existing_item)
        
        result = await sync_engine.sync_file_to_database(
            file_path, file_content, ConflictResolution.MANUAL_RESOLUTION
        )
        
        assert result.status == SyncStatus.CONFLICT
        assert "Manual resolution required" in result.message
        assert len(result.conflicts) > 0

class TestDatabaseToFile:
    """Test database to file synchronization."""
    
    @pytest.mark.asyncio
    async def test_sync_database_to_file_success(self, sync_engine, sample_work_item_data):
        """Test successful database to file sync."""
        work_item_id = "task-001"
        
        # Mock database item
        sync_engine._get_work_item_from_db = AsyncMock(return_value=sample_work_item_data)
        sync_engine._get_existing_file_content = AsyncMock(return_value=None)
        
        result = await sync_engine.sync_database_to_file(work_item_id, ".json")
        
        assert result.status == SyncStatus.SUCCESS
        assert result.work_item_id == work_item_id
        assert "Successfully synced" in result.message
        assert "file_content" in result.metadata
        
        # Verify file content is valid JSON
        file_content = result.metadata["file_content"]
        parsed_data = json.loads(file_content)
        assert parsed_data["id"] == work_item_id
        
    @pytest.mark.asyncio
    async def test_sync_database_to_file_not_found(self, sync_engine):
        """Test database to file sync with missing work item."""
        work_item_id = "nonexistent-task"
        
        sync_engine._get_work_item_from_db = AsyncMock(return_value=None)
        
        result = await sync_engine.sync_database_to_file(work_item_id)
        
        assert result.status == SyncStatus.ERROR
        assert "not found in database" in result.message
        assert result.work_item_id == work_item_id
        
    @pytest.mark.asyncio
    async def test_sync_database_to_file_with_existing_file(self, sync_engine, sample_work_item_data):
        """Test database to file sync with existing file conflict."""
        work_item_id = "task-001"
        
        # Mock database item
        sync_engine._get_work_item_from_db = AsyncMock(return_value=sample_work_item_data)
        
        # Mock existing file with different content
        existing_data = sample_work_item_data.copy()
        existing_data["title"] = "Different Title"
        existing_file_content = json.dumps(existing_data)
        sync_engine._get_existing_file_content = AsyncMock(return_value=existing_file_content)
        
        result = await sync_engine.sync_database_to_file(
            work_item_id, ".json", ConflictResolution.DATABASE_WINS
        )
        
        assert result.status == SyncStatus.SUCCESS
        assert "Successfully synced" in result.message

class TestConflictResolution:
    """Test conflict detection and resolution."""
    
    @pytest.mark.asyncio
    async def test_detect_conflicts(self, sync_engine):
        """Test conflict detection between work items."""
        item1 = {
            "id": "task-001",
            "title": "Title 1",
            "description": "Description 1",
            "status": "todo",
            "updated_at": "2024-01-01T10:00:00Z"
        }
        
        item2 = {
            "id": "task-001",
            "title": "Title 2",  # Different
            "description": "Description 1",  # Same
            "status": "in_progress",  # Different
            "updated_at": "2024-01-01T11:00:00Z"  # Different
        }
        
        conflicts = await sync_engine._detect_conflicts(item1, item2)
        
        assert len(conflicts) >= 2  # At least title and status conflicts
        assert any("title" in conflict for conflict in conflicts)
        assert any("status" in conflict for conflict in conflicts)
        
    @pytest.mark.asyncio
    async def test_auto_merge_strategy(self, sync_engine):
        """Test auto-merge conflict resolution."""
        # Item with earlier timestamp
        item1 = {
            "id": "task-001",
            "title": "Old Title",
            "tags": ["tag1", "tag2"],
            "children": ["child1"],
            "updated_at": "2024-01-01T10:00:00Z"
        }
        
        # Item with later timestamp
        item2 = {
            "id": "task-001",
            "title": "New Title",
            "tags": ["tag2", "tag3"],
            "children": ["child2"],
            "updated_at": "2024-01-01T11:00:00Z"
        }
        
        merged = await sync_engine._auto_merge(item1, item2)
        
        # Should use newer item as base
        assert merged["title"] == "New Title"
        
        # Should merge arrays
        assert set(merged["tags"]) == {"tag1", "tag2", "tag3"}
        assert set(merged["children"]) == {"child1", "child2"}
        
        # Should update timestamp
        assert merged["updated_at"] > item2["updated_at"]
        
    @pytest.mark.asyncio
    async def test_handle_conflict_file_wins(self, sync_engine, sample_work_item):
        """Test conflict resolution with FILE_WINS strategy."""
        existing_item = sample_work_item.dict()
        existing_item["title"] = "Different Title"
        
        result = await sync_engine._handle_conflict(
            sample_work_item, existing_item, 
            ConflictResolution.FILE_WINS, SyncDirection.FILE_TO_DB
        )
        
        assert result.status == SyncStatus.SUCCESS
        assert result.metadata["resolved_item"]["title"] == sample_work_item.title
        
    @pytest.mark.asyncio
    async def test_handle_conflict_database_wins(self, sync_engine, sample_work_item):
        """Test conflict resolution with DATABASE_WINS strategy."""
        existing_item = sample_work_item.dict()
        existing_item["title"] = "Database Title"
        
        result = await sync_engine._handle_conflict(
            sample_work_item, existing_item,
            ConflictResolution.DATABASE_WINS, SyncDirection.FILE_TO_DB
        )
        
        assert result.status == SyncStatus.SUCCESS
        assert result.metadata["resolved_item"]["title"] == "Database Title"

class TestSyncStatus:
    """Test sync status tracking."""
    
    @pytest.mark.asyncio
    async def test_get_sync_status_synced_file(self, sync_engine):
        """Test getting sync status for synced file."""
        file_path = "test.json"
        work_item_id = "task-001"
        
        # Add to sync state
        sync_engine.sync_state[file_path] = {
            "work_item_id": work_item_id,
            "file_path": file_path,
            "checksum": "abc123",
            "last_sync": "2024-01-01T10:00:00Z",
            "sync_direction": "bidirectional"
        }
        
        status = await sync_engine.get_sync_status(file_path)
        
        assert status["identifier"] == file_path
        assert status["status"] == "synced"
        assert status["work_item_id"] == work_item_id
        assert status["last_sync"] == "2024-01-01T10:00:00Z"
        
    @pytest.mark.asyncio
    async def test_get_sync_status_active_sync(self, sync_engine):
        """Test getting sync status for active sync operation."""
        work_item_id = "task-001"
        
        # Add to active syncs
        sync_engine.active_syncs[work_item_id] = {
            "started_at": "2024-01-01T10:00:00Z",
            "operation": "sync_to_file"
        }
        
        status = await sync_engine.get_sync_status(work_item_id)
        
        assert status["identifier"] == work_item_id
        assert status["status"] == "syncing"
        assert status["started_at"] == "2024-01-01T10:00:00Z"
        assert status["operation"] == "sync_to_file"
        
    @pytest.mark.asyncio
    async def test_get_sync_status_database_only(self, sync_engine, sample_work_item_data):
        """Test getting sync status for database-only item."""
        work_item_id = "task-001"
        
        sync_engine._get_work_item_from_db = AsyncMock(return_value=sample_work_item_data)
        
        status = await sync_engine.get_sync_status(work_item_id)
        
        assert status["identifier"] == work_item_id
        assert status["status"] == "database_only"
        assert status["work_item_id"] == work_item_id
        
    @pytest.mark.asyncio
    async def test_get_sync_status_not_found(self, sync_engine):
        """Test getting sync status for unknown identifier."""
        sync_engine._get_work_item_from_db = AsyncMock(return_value=None)
        
        status = await sync_engine.get_sync_status("unknown-id")
        
        assert status["identifier"] == "unknown-id"
        assert status["status"] == "not_found"
        assert "No sync information found" in status["message"]

class TestErrorHandling:
    """Test error handling scenarios."""
    
    @pytest.mark.asyncio
    async def test_sync_file_to_database_exception(self, sync_engine, sample_work_item_data):
        """Test exception handling in file to database sync."""
        file_path = "test.json"
        file_content = json.dumps(sample_work_item_data)
        
        # Mock database error
        sync_engine._get_work_item_from_db = AsyncMock(side_effect=Exception("Database error"))
        
        result = await sync_engine.sync_file_to_database(file_path, file_content)
        
        assert result.status == SyncStatus.ERROR
        assert "Database error" in result.message
        
    @pytest.mark.asyncio
    async def test_sync_database_to_file_exception(self, sync_engine):
        """Test exception handling in database to file sync."""
        work_item_id = "task-001"
        
        # Mock database error
        sync_engine._get_work_item_from_db = AsyncMock(side_effect=Exception("Database error"))
        
        result = await sync_engine.sync_database_to_file(work_item_id)
        
        assert result.status == SyncStatus.ERROR
        assert "Database error" in result.message
        
    @pytest.mark.asyncio
    async def test_get_sync_status_exception(self, sync_engine):
        """Test exception handling in get sync status."""
        sync_engine._get_work_item_from_db = AsyncMock(side_effect=Exception("Database error"))
        
        status = await sync_engine.get_sync_status("task-001")
        
        assert status["status"] == "error"
        assert "Database error" in status["message"]

class TestCleanup:
    """Test cleanup functionality."""
    
    @pytest.mark.asyncio
    async def test_cleanup(self, sync_engine):
        """Test sync engine cleanup."""
        # Add some state
        sync_engine.active_syncs["test"] = {"operation": "test"}
        
        await sync_engine.cleanup()
        
        assert len(sync_engine.active_syncs) == 0