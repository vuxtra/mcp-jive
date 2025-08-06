"""Pytest configuration and shared fixtures for MCP Jive tests."""

import pytest
import pytest_asyncio
import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import AsyncGenerator, Generator, Dict, Any
from unittest.mock import AsyncMock, MagicMock
import os
import sys

# Add src to Python path for testing
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Test configuration
pytest_plugins = ["pytest_asyncio"]


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture
def project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def test_data_dir(project_root):
    """Get the test data directory."""
    return project_root / "tests" / "data"


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def mock_env():
    """Provide a clean environment for testing."""
    original_env = os.environ.copy()
    
    # Set test environment variables
    test_env = {
        "MCP_ENV": "test",
        "MCP_LOG_LEVEL": "DEBUG",
        "MCP_DEV_MODE": "true",
        "LANCEDB_USE_EMBEDDED": "true",
        "MCP_SERVER_HOST": "localhost",
        "MCP_SERVER_PORT": "0",  # Use random port for testing
        "MCP_AUTH_ENABLED": "false",
        "MCP_RATE_LIMIT_ENABLED": "false",
    }
    
    # Update environment
    os.environ.update(test_env)
    
    yield test_env
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest_asyncio.fixture
async def mock_lancedb_client():
    """Mock LanceDB client for testing."""
    mock_client = AsyncMock()
    
    # Mock common LanceDB operations
    mock_client.is_ready.return_value = True
    mock_client.table_names.return_value = []
    mock_client.create_table.return_value = AsyncMock()
    mock_client.open_table.return_value = AsyncMock()
    mock_client.drop_table.return_value = None
    
    # Mock query operations
    mock_table = AsyncMock()
    mock_table.search.return_value.to_list.return_value = []
    mock_table.add.return_value = None
    mock_table.update.return_value = None
    mock_table.delete.return_value = None
    mock_client.open_table.return_value = mock_table
    
    return mock_client


@pytest_asyncio.fixture
async def mock_mcp_server():
    """Mock MCP server for testing."""
    mock_server = AsyncMock()
    
    # Mock server lifecycle
    mock_server.start.return_value = None
    mock_server.stop.return_value = None
    mock_server.is_running.return_value = True
    
    # Mock tool registration
    mock_server.register_tool.return_value = None
    mock_server.list_tools.return_value = []
    
    # Mock request handling
    mock_server.handle_request.return_value = {
        "jsonrpc": "2.0",
        "id": "test-id",
        "result": {"success": True}
    }
    
    return mock_server


@pytest.fixture
def sample_work_item():
    """Sample work item for testing."""
    return {
        "id": "test-work-item-1",
        "title": "Test Work Item",
        "description": "A test work item for unit testing",
        "type": "task",
        "status": "pending",
        "priority": "medium",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "metadata": {
            "tags": ["test", "unit-test"],
            "estimated_effort": "2h"
        },
        "dependencies": [],
        "children": []
    }


@pytest.fixture
def sample_task_data():
    """Sample task data for testing."""
    return {
        "id": "task-001",
        "title": "Sample Task",
        "description": "A sample task for testing",
        "status": "pending",
        "priority": "medium",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "assignee": "test-user",
        "tags": ["test", "sample"],
        "estimated_hours": 4,
        "actual_hours": 0,
        "progress": 0
    }


@pytest_asyncio.fixture
async def task_manager(mock_lancedb_client):
    """Create a TaskManager instance for testing."""
    from unittest.mock import AsyncMock
    # This will be implemented when the actual TaskManager is created
    # return TaskManager(database=mock_lancedb_client)
    return AsyncMock()


@pytest.fixture
def sample_hierarchy():
    """Sample work item hierarchy for testing."""
    return {
        "root": {
            "id": "root",
            "title": "Root Work Item",
            "type": "epic",
            "status": "in_progress",
            "children": ["child-1", "child-2"]
        },
        "child-1": {
            "id": "child-1",
            "title": "Child Work Item 1",
            "type": "story",
            "status": "completed",
            "parent": "root",
            "children": ["grandchild-1"]
        },
        "child-2": {
            "id": "child-2",
            "title": "Child Work Item 2",
            "type": "story",
            "status": "pending",
            "parent": "root",
            "children": []
        },
        "grandchild-1": {
            "id": "grandchild-1",
            "title": "Grandchild Work Item 1",
            "type": "task",
            "status": "completed",
            "parent": "child-1",
            "children": []
        }
    }


@pytest.fixture
def sample_mcp_request():
    """Sample MCP request for testing."""
    return {
        "jsonrpc": "2.0",
        "id": "test-request-1",
        "method": "tools/call",
        "params": {
            "name": "task_create",
            "arguments": {
                "title": "Test Task",
                "description": "A test task",
                "priority": "medium"
            }
        }
    }


@pytest.fixture
def sample_mcp_response():
    """Sample MCP response for testing."""
    return {
        "jsonrpc": "2.0",
        "id": "test-request-1",
        "result": {
            "content": [
                {
                    "type": "text",
                    "text": "Task created successfully"
                }
            ],
            "isError": False
        }
    }


@pytest.fixture
def mock_ai_client():
    """Mock AI client for testing."""
    mock_client = AsyncMock()
    
    # Mock text generation
    mock_client.generate_text.return_value = "Generated test response"
    mock_client.generate_embedding.return_value = [0.1] * 1536  # Mock embedding vector
    
    # Mock streaming
    async def mock_stream():
        yield "Chunk 1"
        yield "Chunk 2"
        yield "Chunk 3"
    
    mock_client.stream_text.return_value = mock_stream()
    
    return mock_client


@pytest.fixture
def performance_monitor():
    """Performance monitoring fixture for tests."""
    import time
    
    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            
        def start(self):
            self.start_time = time.perf_counter()
            
        def stop(self):
            self.end_time = time.perf_counter()
            
        @property
        def duration(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
            
        def assert_duration_under(self, max_seconds: float):
            assert self.duration is not None, "Performance monitor not properly started/stopped"
            assert self.duration < max_seconds, f"Operation took {self.duration:.3f}s, expected under {max_seconds}s"
    
    return PerformanceMonitor()


@pytest.fixture
def test_config():
    """Test configuration fixture."""
    return {
        "server": {
            "host": "localhost",
            "port": 0,  # Random port
            "dev_mode": True,
            "log_level": "DEBUG"
        },
        "database": {
            "use_embedded": True,
            "host": "localhost",
            "port": 8080,
            "timeout": 10
        },
        "ai": {
            "provider": "mock",
            "model": "test-model",
            "max_tokens": 1000
        },
        "tools": {
            "task_management": {
                "enabled": True,
                "max_tasks": 100
            },
            "search": {
                "enabled": True,
                "max_results": 50
            }
        }
    }


# Test markers
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.mcp = pytest.mark.mcp
pytest.mark.performance = pytest.mark.performance
pytest.mark.slow = pytest.mark.slow


# Custom assertions
def assert_mcp_response_valid(response: Dict[str, Any]):
    """Assert that an MCP response is valid."""
    assert "jsonrpc" in response
    assert response["jsonrpc"] == "2.0"
    assert "id" in response
    assert "result" in response or "error" in response
    
    if "result" in response:
        result = response["result"]
        assert "content" in result
        assert isinstance(result["content"], list)
        

def assert_work_item_valid(work_item: Dict[str, Any]):
    """Assert that a work item is valid."""
    required_fields = ["id", "title", "type", "status", "created_at"]
    for field in required_fields:
        assert field in work_item, f"Missing required field: {field}"
        
    assert work_item["type"] in ["epic", "story", "task", "bug"]
    assert work_item["status"] in ["pending", "in_progress", "completed", "cancelled"]


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "mcp: mark test as an MCP protocol test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on file location."""
    for item in items:
        # Add markers based on test file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "mcp" in str(item.fspath):
            item.add_marker(pytest.mark.mcp)
            
        # Add slow marker for tests that might be slow
        if any(keyword in item.name.lower() for keyword in ["performance", "load", "stress"]):
            item.add_marker(pytest.mark.slow)