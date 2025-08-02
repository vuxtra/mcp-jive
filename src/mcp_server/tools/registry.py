"""MCP Tool Registry.

Manages registration and execution of all MCP tools.
Implements the 16 essential MCP tools as specified in the PRD.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import json

from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

from ..config import ServerConfig
from ..lancedb_manager import LanceDBManager
from .task_management import TaskManagementTools
from .search_discovery import SearchDiscoveryTools
from .workflow_execution import WorkflowExecutionTools
from .progress_tracking import ProgressTrackingTools
from .workflow_engine import WorkflowEngineTools
from .storage_sync import StorageSyncTools
from .validation_tools import ValidationTools
from .client_tools import MCPClientTools

logger = logging.getLogger(__name__)


class MCPToolRegistry:
    """Registry for all MCP tools."""
    
    def __init__(self, config: ServerConfig, lancedb_manager: LanceDBManager):
        self.config = config
        self.lancedb_manager = lancedb_manager
        self.tools: Dict[str, Tool] = {}
        self.tool_handlers: Dict[str, Callable] = {}
        
        # Tool category instances
        self.task_tools: Optional[TaskManagementTools] = None
        self.search_tools: Optional[SearchDiscoveryTools] = None
        self.workflow_tools: Optional[WorkflowExecutionTools] = None
        self.progress_tools: Optional[ProgressTrackingTools] = None
        self.workflow_engine_tools: Optional[WorkflowEngineTools] = None
        self.storage_sync_tools: Optional[StorageSyncTools] = None
        self.validation_tools: Optional[ValidationTools] = None
        self.client_tools: Optional[MCPClientTools] = None
        
    async def initialize(self) -> None:
        """Initialize all tool categories and register tools."""
        logger.info("Initializing MCP tool registry...")
        
        try:
            # Initialize tool categories
            self.task_tools = TaskManagementTools(self.config, self.lancedb_manager)
            self.search_tools = SearchDiscoveryTools(self.config, self.lancedb_manager)
            self.workflow_tools = WorkflowExecutionTools(self.config, self.lancedb_manager)
            self.progress_tools = ProgressTrackingTools(self.config, self.lancedb_manager)
            self.workflow_engine_tools = WorkflowEngineTools(self.config, self.lancedb_manager)
            self.storage_sync_tools = StorageSyncTools(self.config, self.lancedb_manager)
            self.validation_tools = ValidationTools(self.config, self.lancedb_manager)
            self.client_tools = MCPClientTools(self.config, self.lancedb_manager)
            
            # Initialize each category
            await self.task_tools.initialize()
            await self.search_tools.initialize()
            await self.workflow_tools.initialize()
            await self.progress_tools.initialize()
            await self.workflow_engine_tools.initialize()
            await self.storage_sync_tools.initialize()
            await self.validation_tools.initialize()
            await self.client_tools.initialize()
            
            # Register all tools
            await self._register_all_tools()
            
            logger.info(f"Initialized {len(self.tools)} MCP tools")
            
        except Exception as e:
            logger.error(f"Failed to initialize tool registry: {e}")
            raise
            
    async def _register_all_tools(self) -> None:
        """Register tools based on configuration mode (minimal or full)."""
        
        if self.config.tool_mode == "minimal":
            await self._register_minimal_tools()
        else:  # full mode
            await self._register_full_tools()
            
        logger.info(f"Registered {len(self.tools)} tools in {self.config.tool_mode} mode: {list(self.tools.keys())}")
        
    async def _register_minimal_tools(self) -> None:
        """Register the 16 essential tools for AI agents."""
        
        # Define the 16 minimal tools based on MCPTools.md specification
        minimal_tool_names = {
            # Core Work Item Management (5 tools)
            "jive_create_work_item",
            "jive_get_work_item", 
            "jive_update_work_item",
            "jive_list_work_items",
            "jive_search_work_items",
            
            # Simple Hierarchy & Dependencies (3 tools)
            "jive_get_work_item_children",
            "jive_get_work_item_dependencies", 
            "jive_validate_dependencies",
            
            # Execution Control (3 tools)
            "jive_execute_work_item",
            "jive_get_execution_status",
            "jive_cancel_execution",
            
            # Storage & Sync (3 tools)
            "jive_sync_file_to_database",
            "jive_sync_database_to_file",
            "jive_get_sync_status",
            
            # Validation (2 tools)
            "jive_validate_task_completion",
            "jive_approve_completion"
        }
        
        # Register tools from all categories but filter to minimal set
        await self._register_filtered_tools(minimal_tool_names)
        
    async def _register_full_tools(self) -> None:
        """Register all 35 tools from all categories."""
        
        # Task Management Tools (4 tools)
        task_tools = await self.task_tools.get_tools()
        for tool in task_tools:
            self.tools[tool.name] = tool
            self.tool_handlers[tool.name] = self.task_tools.handle_tool_call
            
        # Search and Discovery Tools (4 tools)
        search_tools = await self.search_tools.get_tools()
        for tool in search_tools:
            self.tools[tool.name] = tool
            self.tool_handlers[tool.name] = self.search_tools.handle_tool_call
            
        # Workflow Execution Tools (4 tools)
        workflow_tools = await self.workflow_tools.get_tools()
        for tool in workflow_tools:
            self.tools[tool.name] = tool
            self.tool_handlers[tool.name] = self.workflow_tools.handle_tool_call
            
        # Progress Tracking Tools (4 tools)
        progress_tools = await self.progress_tools.get_tools()
        for tool in progress_tools:
            self.tools[tool.name] = tool
            self.tool_handlers[tool.name] = self.progress_tools.handle_tool_call
            
        # Workflow Engine Tools (6 tools)
        workflow_engine_tools = await self.workflow_engine_tools.get_tools()
        for tool in workflow_engine_tools:
            self.tools[tool.name] = tool
            self.tool_handlers[tool.name] = self.workflow_engine_tools.handle_tool_call
            
        # Storage Sync Tools (3 tools)
        storage_sync_tools = await self.storage_sync_tools.get_tools()
        for tool in storage_sync_tools:
            self.tools[tool.name] = tool
            self.tool_handlers[tool.name] = self.storage_sync_tools.handle_tool_call
            
        # Validation Tools (5 tools)
        validation_tools = await self.validation_tools.get_tools()
        for tool in validation_tools:
            self.tools[tool.name] = tool
            self.tool_handlers[tool.name] = self.validation_tools.handle_tool_call
            
        # MCP Client Tools (5 tools)
        client_tools = await self.client_tools.get_tools()
        for tool in client_tools:
            self.tools[tool.name] = tool
            self.tool_handlers[tool.name] = self.client_tools.handle_tool_call
            
    async def _register_filtered_tools(self, allowed_tool_names: set) -> None:
        """Register only tools that are in the allowed set."""
        
        # Get all tools from all categories
        all_tool_categories = [
            (await self.task_tools.get_tools(), self.task_tools.handle_tool_call),
            (await self.search_tools.get_tools(), self.search_tools.handle_tool_call),
            (await self.workflow_tools.get_tools(), self.workflow_tools.handle_tool_call),
            (await self.progress_tools.get_tools(), self.progress_tools.handle_tool_call),
            (await self.workflow_engine_tools.get_tools(), self.workflow_engine_tools.handle_tool_call),
            (await self.storage_sync_tools.get_tools(), self.storage_sync_tools.handle_tool_call),
            (await self.validation_tools.get_tools(), self.validation_tools.handle_tool_call),
            (await self.client_tools.get_tools(), self.client_tools.handle_tool_call),
        ]
        
        # Register only allowed tools
        registered_tools = set()
        for tools, handler in all_tool_categories:
            for tool in tools:
                if tool.name in allowed_tool_names:
                    self.tools[tool.name] = tool
                    self.tool_handlers[tool.name] = handler
                    registered_tools.add(tool.name)
                    
        # Log any missing tools from the minimal set
        missing_tools = allowed_tool_names - registered_tools
        if missing_tools:
            logger.warning(f"Missing tools from minimal set: {missing_tools}")
            logger.warning("These tools may need to be implemented or have different names")
        
    async def list_tools(self) -> List[Tool]:
        """List all available tools."""
        return list(self.tools.values())
        
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> List[TextContent | ImageContent | EmbeddedResource]:
        """Call a specific tool with arguments."""
        if name not in self.tools:
            raise ValueError(f"Unknown tool: {name}")
            
        if name not in self.tool_handlers:
            raise RuntimeError(f"No handler registered for tool: {name}")
            
        try:
            logger.debug(f"Calling tool {name} with arguments: {arguments}")
            
            # Call the appropriate handler
            handler = self.tool_handlers[name]
            result = await handler(name, arguments)
            
            # Ensure result is in the correct format
            if isinstance(result, str):
                return [TextContent(type="text", text=result)]
            elif isinstance(result, dict):
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            elif isinstance(result, list) and all(isinstance(item, (TextContent, ImageContent, EmbeddedResource)) for item in result):
                return result
            else:
                # Convert to JSON string
                return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
                
        except Exception as e:
            logger.error(f"Error calling tool {name}: {e}")
            error_response = {
                "error": str(e),
                "tool": name,
                "arguments": arguments,
                "timestamp": datetime.now().isoformat()
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
            
    async def get_tool_info(self, name: str) -> Optional[Tool]:
        """Get information about a specific tool."""
        return self.tools.get(name)
        
    async def validate_tool_arguments(self, name: str, arguments: Dict[str, Any]) -> bool:
        """Validate arguments for a specific tool."""
        if name not in self.tools:
            return False
            
        tool = self.tools[name]
        
        # Basic validation - check required parameters
        if hasattr(tool, 'inputSchema') and tool.inputSchema:
            schema = tool.inputSchema
            if 'required' in schema:
                required_params = schema['required']
                for param in required_params:
                    if param not in arguments:
                        logger.warning(f"Missing required parameter '{param}' for tool '{name}'")
                        return False
                        
        return True
        
    async def get_tool_stats(self) -> Dict[str, Any]:
        """Get statistics about tool usage."""
        stats = {
            "total_tools": len(self.tools),
            "categories": {
                "task_management": len(await self.task_tools.get_tools()) if self.task_tools else 0,
                "search_discovery": len(await self.search_tools.get_tools()) if self.search_tools else 0,
                "workflow_execution": len(await self.workflow_tools.get_tools()) if self.workflow_tools else 0,
                "progress_tracking": len(await self.progress_tools.get_tools()) if self.progress_tools else 0,
                "workflow_engine": len(await self.workflow_engine_tools.get_tools()) if self.workflow_engine_tools else 0,
                "storage_sync": len(await self.storage_sync_tools.get_tools()) if self.storage_sync_tools else 0,
                "client_tools": len(await self.client_tools.get_tools()) if self.client_tools else 0,
            },
            "tool_names": list(self.tools.keys()),
            "initialized_at": datetime.now().isoformat()
        }
        
        return stats
        
    async def cleanup(self) -> None:
        """Cleanup tool registry and all tool categories."""
        logger.info("Cleaning up tool registry...")
        
        try:
            # Cleanup tool categories
            if self.task_tools:
                await self.task_tools.cleanup()
                
            if self.search_tools:
                await self.search_tools.cleanup()
                
            if self.workflow_tools:
                await self.workflow_tools.cleanup()
                
            if self.progress_tools:
                await self.progress_tools.cleanup()
                
            if self.workflow_engine_tools:
                await self.workflow_engine_tools.cleanup()
                
            if self.storage_sync_tools:
                await self.storage_sync_tools.cleanup()
                
            if self.client_tools:
                await self.client_tools.cleanup()
                
            # Clear registries
            self.tools.clear()
            self.tool_handlers.clear()
            
            logger.info("Tool registry cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during tool registry cleanup: {e}")