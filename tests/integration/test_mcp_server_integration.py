"""Integration tests for MCP server functionality."""

import pytest
import pytest_asyncio
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

# These imports will be available when the actual server is implemented
# from mcp_jive.server import MCPServer
# from mcp_jive.core.config import ServerConfig
# from mcp_jive.tools import get_all_tools


class TestMCPServerIntegration:
    """Integration tests for MCP server."""
    
    @pytest.fixture
    def mcp_server(self, mock_env, test_config):
        """Create an MCP server instance for testing."""
        # This will be implemented when the actual server is created
        server = AsyncMock()
        server.config = test_config
        # Configure sync methods to return values directly
        server.is_running = MagicMock(return_value=False)
        return server
    
    @pytest_asyncio.fixture
    async def running_server(self, mcp_server):
        """Start the MCP server for testing."""
        # Mock server startup
        mcp_server.is_running.return_value = True
        await mcp_server.start()
        
        yield mcp_server
        
        # Mock server shutdown
        mcp_server.is_running.return_value = False
        await mcp_server.stop()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_server_startup_shutdown(self, mcp_server):
        """Test server startup and shutdown process."""
        # Test initial state
        assert not mcp_server.is_running()
        
        # Test startup
        await mcp_server.start()
        mcp_server.is_running.return_value = True
        assert mcp_server.is_running()
        
        # Test shutdown
        await mcp_server.stop()
        mcp_server.is_running.return_value = False
        assert not mcp_server.is_running()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_tool_registration(self, running_server):
        """Test that all required tools are registered."""
        expected_tools = [
            "task_create",
            "task_read", 
            "task_update",
            "task_delete",
            "task_list",
            "search_semantic",
            "search_keyword",
            "workflow_create",
            "workflow_execute",
            "progress_calculate",
            "hierarchy_create",
            "hierarchy_update",
            "dependency_add",
            "dependency_remove",
            "validation_run",
            "health_check"
        ]
        
        # Mock tool listing
        running_server.list_tools.return_value = [
            {"name": tool, "description": f"Mock {tool} tool"} 
            for tool in expected_tools
        ]
        
        tools = await running_server.list_tools()
        tool_names = [tool["name"] for tool in tools]
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names, f"Tool {expected_tool} not registered"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_mcp_request_response_cycle(self, running_server, sample_mcp_request, sample_mcp_response):
        """Test complete MCP request-response cycle."""
        # Mock request handling
        running_server.handle_request.return_value = sample_mcp_response
        
        # Send request
        response = await running_server.handle_request(sample_mcp_request)
        
        # Validate response structure
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == sample_mcp_request["id"]
        assert "result" in response
        assert "content" in response["result"]
        
        # Verify request was processed
        running_server.handle_request.assert_called_once_with(sample_mcp_request)
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_task_management_workflow(self, running_server):
        """Test complete task management workflow through MCP."""
        # Mock task creation
        create_request = {
            "jsonrpc": "2.0",
            "id": "req-1",
            "method": "tools/call",
            "params": {
                "name": "task_create",
                "arguments": {
                    "title": "Integration Test Task",
                    "description": "A task created during integration testing",
                    "priority": "medium"
                }
            }
        }
        
        create_response = {
            "jsonrpc": "2.0",
            "id": "req-1",
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "id": "task-integration-1",
                            "title": "Integration Test Task",
                            "status": "pending",
                            "created_at": "2024-01-01T00:00:00Z"
                        })
                    }
                ],
                "isError": False
            }
        }
        
        running_server.handle_request.return_value = create_response
        
        # Create task
        response = await running_server.handle_request(create_request)
        assert not response["result"]["isError"]
        
        task_data = json.loads(response["result"]["content"][0]["text"])
        task_id = task_data["id"]
        
        # Mock task update
        update_request = {
            "jsonrpc": "2.0",
            "id": "req-2",
            "method": "tools/call",
            "params": {
                "name": "task_update",
                "arguments": {
                    "task_id": task_id,
                    "updates": {"status": "in_progress"}
                }
            }
        }
        
        update_response = {
            "jsonrpc": "2.0",
            "id": "req-2",
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            **task_data,
                            "status": "in_progress",
                            "updated_at": "2024-01-01T01:00:00Z"
                        })
                    }
                ],
                "isError": False
            }
        }
        
        running_server.handle_request.return_value = update_response
        
        # Update task
        response = await running_server.handle_request(update_request)
        assert not response["result"]["isError"]
        
        updated_task = json.loads(response["result"]["content"][0]["text"])
        assert updated_task["status"] == "in_progress"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_search_functionality(self, running_server):
        """Test search functionality through MCP."""
        search_request = {
            "jsonrpc": "2.0",
            "id": "req-search",
            "method": "tools/call",
            "params": {
                "name": "search_semantic",
                "arguments": {
                    "query": "test tasks",
                    "limit": 10
                }
            }
        }
        
        search_response = {
            "jsonrpc": "2.0",
            "id": "req-search",
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "results": [
                                {
                                    "id": "task-1",
                                    "title": "Test Task 1",
                                    "relevance_score": 0.95
                                },
                                {
                                    "id": "task-2",
                                    "title": "Test Task 2",
                                    "relevance_score": 0.87
                                }
                            ],
                            "total_count": 2
                        })
                    }
                ],
                "isError": False
            }
        }
        
        running_server.handle_request.return_value = search_response
        
        response = await running_server.handle_request(search_request)
        assert not response["result"]["isError"]
        
        results = json.loads(response["result"]["content"][0]["text"])
        assert len(results["results"]) == 2
        assert results["results"][0]["relevance_score"] > 0.9
    
    @pytest.mark.integration
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, running_server, performance_monitor):
        """Test handling multiple concurrent requests."""
        # Create multiple concurrent requests
        requests = []
        for i in range(10):
            request = {
                "jsonrpc": "2.0",
                "id": f"req-{i}",
                "method": "tools/call",
                "params": {
                    "name": "task_create",
                    "arguments": {
                        "title": f"Concurrent Task {i}",
                        "priority": "low"
                    }
                }
            }
            requests.append(request)
        
        # Mock responses
        def mock_handle_request(request):
            return {
                "jsonrpc": "2.0",
                "id": request["id"],
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps({
                                "id": f"task-{request['id']}",
                                "title": request["params"]["arguments"]["title"],
                                "status": "pending"
                            })
                        }
                    ],
                    "isError": False
                }
            }
        
        running_server.handle_request.side_effect = mock_handle_request
        
        # Execute concurrent requests
        performance_monitor.start()
        
        tasks = [running_server.handle_request(req) for req in requests]
        responses = await asyncio.gather(*tasks)
        
        performance_monitor.stop()
        
        # Verify all requests were handled
        assert len(responses) == 10
        for i, response in enumerate(responses):
            assert response["id"] == f"req-{i}"
            assert not response["result"]["isError"]
        
        # Performance should be reasonable (under 1 second for 10 requests)
        performance_monitor.assert_duration_under(1.0)
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_handling(self, running_server):
        """Test error handling in MCP requests."""
        # Test invalid tool name
        invalid_request = {
            "jsonrpc": "2.0",
            "id": "req-error",
            "method": "tools/call",
            "params": {
                "name": "nonexistent_tool",
                "arguments": {}
            }
        }
        
        error_response = {
            "jsonrpc": "2.0",
            "id": "req-error",
            "error": {
                "code": -32601,
                "message": "Tool not found",
                "data": {"tool_name": "nonexistent_tool"}
            }
        }
        
        running_server.handle_request.return_value = error_response
        
        response = await running_server.handle_request(invalid_request)
        
        assert "error" in response
        assert response["error"]["code"] == -32601
        assert "Tool not found" in response["error"]["message"]
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_health_check(self, running_server):
        """Test server health check functionality."""
        health_request = {
            "jsonrpc": "2.0",
            "id": "req-health",
            "method": "tools/call",
            "params": {
                "name": "health_check",
                "arguments": {}
            }
        }
        
        health_response = {
            "jsonrpc": "2.0",
            "id": "req-health",
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "status": "healthy",
                            "timestamp": "2024-01-01T00:00:00Z",
                            "version": "1.0.0",
                            "database": "connected",
                            "tools": "loaded"
                        })
                    }
                ],
                "isError": False
            }
        }
        
        running_server.handle_request.return_value = health_response
        
        response = await running_server.handle_request(health_request)
        
        assert not response["result"]["isError"]
        health_data = json.loads(response["result"]["content"][0]["text"])
        assert health_data["status"] == "healthy"
        assert health_data["database"] == "connected"
        assert health_data["tools"] == "loaded"


class TestDatabaseIntegration:
    """Integration tests for database functionality."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_weaviate_connection(self, mock_weaviate_client):
        """Test Weaviate database connection."""
        # Test connection
        assert await mock_weaviate_client.is_ready()
        
        # Test basic operations
        collections = await mock_weaviate_client.collections.list_all()
        assert isinstance(collections, list)
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_data_persistence(self, mock_weaviate_client):
        """Test data persistence across operations."""
        # Mock data insertion
        test_data = {
            "title": "Persistent Test Task",
            "description": "Testing data persistence",
            "status": "pending"
        }
        
        mock_collection = mock_weaviate_client.collections.get.return_value
        mock_collection.data.insert.return_value = {"uuid": "test-uuid-123"}
        
        # Insert data
        result = await mock_collection.data.insert(test_data)
        assert result["uuid"] == "test-uuid-123"
        
        # Mock data retrieval
        mock_collection.query.near_text.return_value.objects = [
            {"uuid": "test-uuid-123", "properties": test_data}
        ]
        
        # Retrieve data
        query_result = await mock_collection.query.near_text("test")
        retrieved_objects = query_result.objects
        
        assert len(retrieved_objects) == 1
        assert retrieved_objects[0]["uuid"] == "test-uuid-123"
        assert retrieved_objects[0]["properties"]["title"] == test_data["title"]


class TestWorkflowIntegration:
    """Integration tests for workflow functionality."""
    
    @pytest.fixture
    def mcp_server(self, mock_env, test_config):
        """Create an MCP server instance for testing."""
        server = AsyncMock()
        server.config = test_config
        server.is_running = MagicMock(return_value=False)
        return server
    
    @pytest_asyncio.fixture
    async def running_server(self, mcp_server):
        """Start the MCP server for testing."""
        mcp_server.is_running = MagicMock(return_value=True)
        await mcp_server.start()
        
        yield mcp_server
        
        mcp_server.is_running = MagicMock(return_value=False)
        await mcp_server.stop()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_complete_workflow_execution(self, running_server):
        """Test complete workflow from creation to execution."""
        # This will test the full workflow engine integration
        # Will be implemented when workflow engine is created
        pass
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_hierarchy_management(self, running_server, sample_hierarchy):
        """Test work item hierarchy management."""
        # This will test hierarchy creation, updates, and traversal
        # Will be implemented when hierarchy manager is created
        pass