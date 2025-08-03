"""Tool Registry for MCP Jive.

Manages registration and execution of all MCP tools for the MCP Jive server.
Provides the refined minimal set of 16 essential tools plus AI orchestration tools.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import json

try:
    from mcp.types import Tool, TextContent
except ImportError:
    # Mock MCP types if not available
    Tool = Dict[str, Any]
    TextContent = Dict[str, Any]

from .base import BaseTool, ToolExecutionContext
from .ai_orchestration import AI_ORCHESTRATION_TOOLS
from ..config import ServerConfig
from ..lancedb_manager import LanceDBManager

logger = logging.getLogger(__name__)


class ClientToolWrapper(BaseTool):
    """Wrapper for client tools to make them compatible with BaseTool interface."""
    
    def __init__(self, tool_name: str, client_tools_instance=None, tool_schema=None, storage_sync_tools=None, validation_tools=None, workflow_tools=None):
        """Initialize the wrapper.
        
        Args:
            tool_name: Name of the tool
            client_tools_instance: Instance of MCPClientTools
            tool_schema: Tool schema from MCP client tools
            storage_sync_tools: StorageSyncTools instance for handling execution
            validation_tools: ValidationTools instance for handling execution
            workflow_tools: WorkflowEngineTools instance for handling execution
        """
        super().__init__()
        self._name = tool_name
        self.client_tools = client_tools_instance
        self._tool_schema = tool_schema
        self.storage_sync_tools = storage_sync_tools
        self.validation_tools = validation_tools
        self.workflow_tools = workflow_tools
    
    @property
    def name(self) -> str:
        """Tool name identifier."""
        return self._name
    
    @property
    def description(self) -> str:
        """Tool description for AI agents."""
        if self._tool_schema and hasattr(self._tool_schema, 'description'):
            return self._tool_schema.description
        return f"Client tool: {self._name}"
    
    @property
    def category(self):
        """Tool category."""
        from .base import ToolCategory
        return ToolCategory.WORK_ITEM_MANAGEMENT
    
    @property
    def parameters_schema(self):
        """Parameters schema for the tool."""
        if self._tool_schema and hasattr(self._tool_schema, 'inputSchema'):
            return self._tool_schema.inputSchema
        return {}
    
    async def execute(self, **kwargs):
        """Execute the wrapped client tool.
        
        Args:
            **kwargs: Tool arguments
            
        Returns:
            Tool execution result
        """
        from .base import ToolResult
        try:
            # Determine which handler to use based on available instances
            if self.client_tools:
                result = await self.client_tools.handle_tool_call(self._name, kwargs)
            elif self.storage_sync_tools:
                result = await self.storage_sync_tools.handle_tool_call(self._name, kwargs)
            elif self.validation_tools:
                result = await self.validation_tools.handle_tool_call(self._name, kwargs)
            elif self.workflow_tools:
                result = await self.workflow_tools.handle_tool_call(self._name, kwargs)
            else:
                raise ValueError(f"No handler available for tool {self._name}")
                
            return ToolResult(
                success=True,
                data=result,
                message=f"Successfully executed {self._name}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                message=f"Failed to execute {self._name}: {e}"
            )
    
    def get_schema(self):
        """Get tool schema - not needed for wrapper."""
        return self._tool_schema


class ToolRegistry:
    """Registry for all MCP Jive tools."""
    
    def __init__(self, database=None, ai_orchestrator=None, config=None, lancedb_manager=None):
        """Initialize tool registry.
        
        Args:
            database: Weaviate database manager instance.
            ai_orchestrator: AI orchestrator instance.
            config: Configuration object.
            lancedb_manager: LanceDB manager instance.
        """
        self.database = database
        self.ai_orchestrator = ai_orchestrator
        self.config = config
        self.lancedb_manager = lancedb_manager
        self.tools: Dict[str, Tool] = {}
        self.tool_instances: Dict[str, BaseTool] = {}
        
    async def initialize(self) -> None:
        """Initialize all tools and register them."""
        tool_mode = getattr(self.config, 'tools', None) and getattr(self.config.tools, 'tool_mode', 'minimal') or 'minimal'
        logger.info(f"Initializing MCP Jive tool registry in {tool_mode} mode...")
        
        try:
            if tool_mode == "minimal":
                await self._register_minimal_tools()
            else:  # full mode
                await self._register_full_tools()
            
            logger.info(f"Initialized {len(self.tools)} MCP tools in {tool_mode} mode: {list(self.tools.keys())}")
            
        except Exception as e:
            logger.error(f"Failed to initialize tool registry: {e}")
            raise
    
    async def _register_ai_orchestration_tools(self) -> None:
        """Register AI orchestration tools."""
        for tool_class in AI_ORCHESTRATION_TOOLS:
            try:
                # Create tool instance
                tool_instance = tool_class(
                    database=self.database,
                    ai_orchestrator=self.ai_orchestrator,
                    config=self.config
                )
                
                # Get tool schema
                tool_schema = tool_instance.get_schema()
                
                # Register tool
                self.tools[tool_instance.name] = tool_schema
                self.tool_instances[tool_instance.name] = tool_instance
                
                logger.debug(f"Registered AI orchestration tool: {tool_instance.name}")
                
            except Exception as e:
                logger.error(f"Failed to register tool {tool_class.__name__}: {e}")
                raise
    
    async def _register_storage_sync_tools(self) -> None:
        """Register storage and sync tools."""
        try:
            from .storage_sync import StorageSyncTools
            
            storage_sync_tools = StorageSyncTools(self.config, self.lancedb_manager)
            await storage_sync_tools.initialize()
            
            # Get the 3 storage sync tools
            tools = await storage_sync_tools.get_tools()
            
            for tool in tools:
                wrapper = ClientToolWrapper(
                    tool_name=tool.name,
                    storage_sync_tools=storage_sync_tools,
                    tool_schema=tool
                )
                self.tools[tool.name] = wrapper
                
            logger.debug(f"Registered {len(tools)} storage sync tools")
            
        except Exception as e:
            logger.error(f"Failed to register storage sync tools: {e}")
            raise
    
    async def _register_minimal_ai_orchestration_tools(self) -> None:
        """Register minimal set of AI orchestration tools."""
        try:
            from .ai_orchestration import AIOrchestrationTool, AIProviderStatusTool, AIConfigurationTool
            
            # Register only core AI orchestration tools for minimal mode (3 tools)
            ai_tools = [
                AIOrchestrationTool(self.ai_orchestrator),
                AIProviderStatusTool(self.ai_orchestrator), 
                AIConfigurationTool(self.ai_orchestrator)
            ]
            
            for tool in ai_tools:
                tool_schema = tool.get_schema()
                self.tools[tool.name] = tool_schema
                self.tool_instances[tool.name] = tool
                
            logger.debug(f"Registered {len(ai_tools)} minimal AI orchestration tools")
            
        except Exception as e:
            logger.error(f"Failed to register minimal AI orchestration tools: {e}")
            raise
    
    async def _register_minimal_validation_tools(self) -> None:
        """Register minimal set of validation tools."""
        try:
            from .validation_tools import ValidationTools
            
            validation_tools = ValidationTools(self.config, self.lancedb_manager)
            await validation_tools.initialize()
            
            # Get all validation tools and select minimal set (2 tools)
            all_tools = await validation_tools.get_tools()
            
            # Select only the core validation tools for minimal mode
            minimal_tool_names = [
                "jive_validate_task_completion",
                "jive_get_validation_status"
            ]
            
            for tool in all_tools:
                if tool.name in minimal_tool_names:
                    wrapper = ClientToolWrapper(
                        tool_name=tool.name,
                        validation_tools=validation_tools,
                        tool_schema=tool
                    )
                    self.tools[tool.name] = wrapper
                    
            logger.debug(f"Registered {len(minimal_tool_names)} minimal validation tools")
            
        except Exception as e:
            logger.error(f"Failed to register minimal validation tools: {e}")
            raise
    
    async def _register_hierarchy_tools(self) -> None:
        """Register hierarchy and dependency tools."""
        try:
            from .workflow_engine import WorkflowEngineTools
            
            workflow_tools = WorkflowEngineTools(self.config, self.lancedb_manager)
            await workflow_tools.initialize()
            
            # Get all workflow tools and select hierarchy-related ones (3 tools)
            all_tools = await workflow_tools.get_tools()
            
            # Select only the hierarchy and dependency tools for minimal mode
            hierarchy_tool_names = [
                "jive_get_work_item_children",
                "jive_get_work_item_dependencies", 
                "jive_validate_dependencies"
            ]
            
            for tool in all_tools:
                if tool.name in hierarchy_tool_names:
                    wrapper = ClientToolWrapper(
                        tool_name=tool.name,
                        workflow_tools=workflow_tools,
                        tool_schema=tool
                    )
                    self.tools[tool.name] = wrapper
                    
            logger.debug(f"Registered {len(hierarchy_tool_names)} hierarchy tools")
            
        except Exception as e:
            logger.error(f"Failed to register hierarchy tools: {e}")
            raise
    
    async def _register_client_tools(self) -> None:
        """Register MCP client tools for work item management."""
        from .client_tools import MCPClientTools
        
        try:
            # Create client tools instance
            client_tools = MCPClientTools(
                config=self.config,
                lancedb_manager=self.database
            )
            
            # Initialize client tools
            await client_tools.initialize()
            
            # Get tools from client tools
            tools = await client_tools.get_tools()
            
            # Register each tool
            for tool in tools:
                self.tools[tool.name] = tool
                # Create a wrapper for the tool handler
                self.tool_instances[tool.name] = ClientToolWrapper(
                    tool_name=tool.name,
                    client_tools_instance=client_tools,
                    tool_schema=tool
                )
                
                logger.debug(f"Registered client tool: {tool.name}")
                
        except Exception as e:
            logger.error(f"Failed to register client tools: {e}")
            # Don't raise here to allow partial functionality
    
    async def _register_minimal_tools(self) -> None:
        """Register minimal set of 16 essential tools for AI agents."""
        logger.info("Registering minimal tool set (16 tools)...")
        
        # Core Work Item Management (5 tools) - these are the jive_ prefixed tools
        await self._register_client_tools()
        
        # Storage & Sync (3 tools)
        await self._register_storage_sync_tools()
        
        # AI Orchestration (3 tools - limited set)
        await self._register_minimal_ai_orchestration_tools()
        
        # Validation (2 tools - limited set)
        await self._register_minimal_validation_tools()
        
        # Simple Hierarchy & Dependencies (3 tools)
        await self._register_hierarchy_tools()
        
        logger.info(f"Registered {len(self.tools)} minimal tools")
    
    async def _register_full_tools(self) -> None:
        """Register full set of 35+ tools for comprehensive workflows."""
        logger.info("Registering full tool set (35+ tools)...")
        
        # Register all tool categories
        await self._register_client_tools()
        await self._register_ai_orchestration_tools()
        
        # Additional tool categories for full mode
        await self._register_storage_sync_tools()
        await self._register_hierarchy_tools()
        
        # Full validation tools (8 tools instead of 2)
        await self._register_full_validation_tools()
        
        # Additional tool categories for full mode
        await self._register_task_management_tools()
        await self._register_search_discovery_tools()
        await self._register_workflow_execution_tools()
        await self._register_progress_tracking_tools()
        
        logger.info(f"Registered {len(self.tools)} full tools")
    
    async def _register_full_validation_tools(self) -> None:
        """Register full set of validation tools."""
        try:
            from .validation_tools import ValidationTools
            
            validation_tools = ValidationTools(self.config, self.lancedb_manager)
            await validation_tools.initialize()
            
            # Get all validation tools (8 tools)
            all_tools = await validation_tools.get_tools()
            
            for tool in all_tools:
                wrapper = ClientToolWrapper(
                    tool_name=tool.name,
                    validation_tools=validation_tools,
                    tool_schema=tool
                )
                self.tools[tool.name] = wrapper
                
            logger.debug(f"Registered {len(all_tools)} full validation tools")
            
        except Exception as e:
            logger.error(f"Failed to register full validation tools: {e}")
            raise
    
    async def _register_task_management_tools(self) -> None:
        """Register task management tools."""
        try:
            from .task_management import TaskManagementTools
            
            task_tools = TaskManagementTools(self.config, self.lancedb_manager)
            await task_tools.initialize()
            
            # Get all task management tools (4 tools)
            all_tools = await task_tools.get_tools()
            
            for tool in all_tools:
                wrapper = ClientToolWrapper(
                    tool_name=tool.name,
                    validation_tools=task_tools,  # Using validation_tools parameter for consistency
                    tool_schema=tool
                )
                self.tools[tool.name] = wrapper
                
            logger.debug(f"Registered {len(all_tools)} task management tools")
            
        except Exception as e:
            logger.error(f"Failed to register task management tools: {e}")
            raise
    
    async def _register_search_discovery_tools(self) -> None:
        """Register search and discovery tools."""
        try:
            from .search_discovery import SearchDiscoveryTools
            
            search_tools = SearchDiscoveryTools(self.config, self.lancedb_manager)
            await search_tools.initialize()
            
            # Get all search and discovery tools (4 tools)
            all_tools = await search_tools.get_tools()
            
            for tool in all_tools:
                wrapper = ClientToolWrapper(
                    tool_name=tool.name,
                    validation_tools=search_tools,  # Using validation_tools parameter for consistency
                    tool_schema=tool
                )
                self.tools[tool.name] = wrapper
                
            logger.debug(f"Registered {len(all_tools)} search and discovery tools")
            
        except Exception as e:
            logger.error(f"Failed to register search and discovery tools: {e}")
            raise
    
    async def _register_workflow_execution_tools(self) -> None:
        """Register workflow execution tools."""
        try:
            from .workflow_execution import WorkflowExecutionTools
            
            workflow_exec_tools = WorkflowExecutionTools(self.config, self.lancedb_manager)
            await workflow_exec_tools.initialize()
            
            # Get all workflow execution tools (4 tools)
            all_tools = await workflow_exec_tools.get_tools()
            
            for tool in all_tools:
                wrapper = ClientToolWrapper(
                    tool_name=tool.name,
                    validation_tools=workflow_exec_tools,  # Using validation_tools parameter for consistency
                    tool_schema=tool
                )
                self.tools[tool.name] = wrapper
                
            logger.debug(f"Registered {len(all_tools)} workflow execution tools")
            
        except Exception as e:
            logger.error(f"Failed to register workflow execution tools: {e}")
            raise
    
    async def _register_progress_tracking_tools(self) -> None:
        """Register progress tracking tools."""
        try:
            from .progress_tracking import ProgressTrackingTools
            
            progress_tools = ProgressTrackingTools(self.config, self.lancedb_manager)
            await progress_tools.initialize()
            
            # Get all progress tracking tools (4 tools)
            all_tools = await progress_tools.get_tools()
            
            for tool in all_tools:
                wrapper = ClientToolWrapper(
                    tool_name=tool.name,
                    validation_tools=progress_tools,  # Using validation_tools parameter for consistency
                    tool_schema=tool
                )
                self.tools[tool.name] = wrapper
                
            logger.debug(f"Registered {len(all_tools)} progress tracking tools")
            
        except Exception as e:
            logger.error(f"Failed to register progress tracking tools: {e}")
            raise
    
    async def list_tools(self) -> List[Tool]:
        """List all registered tools."""
        return list(self.tools.values())
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute a tool by name.
        
        Args:
            name: Tool name to execute.
            arguments: Tool arguments.
            
        Returns:
            List of TextContent responses.
            
        Raises:
            ValueError: If tool is not found.
        """
        if name not in self.tool_instances:
            raise ValueError(f"Tool '{name}' not found. Available tools: {list(self.tools.keys())}")
        
        tool_instance = self.tool_instances[name]
        
        # Create execution context
        context = ToolExecutionContext(
            database=self.database,
            ai_orchestrator=self.ai_orchestrator,
            config=self.config
        )
        
        try:
            # Execute tool
            result = await tool_instance.execute(context, **arguments)
            
            # Ensure result is a list of TextContent
            if not isinstance(result, list):
                result = [result]
            
            # Convert to TextContent if needed
            text_content = []
            for item in result:
                if isinstance(item, dict) and "type" in item and "text" in item:
                    text_content.append(item)
                elif hasattr(item, 'type') and hasattr(item, 'text'):
                    text_content.append(item)
                else:
                    # Create TextContent from string or other data
                    if isinstance(TextContent, type):
                        text_content.append(TextContent(type="text", text=str(item)))
                    else:
                        text_content.append({"type": "text", "text": str(item)})
            
            return text_content
            
        except Exception as e:
            logger.error(f"Tool execution failed for '{name}': {e}")
            # Return error as TextContent
            error_text = f"Error executing tool '{name}': {str(e)}"
            if isinstance(TextContent, type):
                return [TextContent(type="text", text=error_text)]
            else:
                return [{"type": "text", "text": error_text}]
    
    async def get_tool_info(self, name: str) -> Optional[Tool]:
        """Get information about a specific tool.
        
        Args:
            name: Tool name.
            
        Returns:
            Tool schema or None if not found.
        """
        return self.tools.get(name)
    
    async def shutdown(self) -> None:
        """Shutdown the tool registry and cleanup resources."""
        logger.info("Shutting down tool registry...")
        
        # Cleanup tool instances if they have cleanup methods
        for tool_instance in self.tool_instances.values():
            if hasattr(tool_instance, 'cleanup'):
                try:
                    await tool_instance.cleanup()
                except Exception as e:
                    logger.error(f"Error cleaning up tool {tool_instance.name}: {e}")
        
        self.tools.clear()
        self.tool_instances.clear()
        
        logger.info("Tool registry shutdown complete")


class MCPToolRegistry:
    """Registry for all MCP tools - consolidated version."""
    
    def __init__(self, config: Optional[ServerConfig] = None, lancedb_manager: Optional[LanceDBManager] = None):
        """Initialize the MCP tool registry."""
        self.config = config or ServerConfig()
        self.lancedb_manager = lancedb_manager
        self.tools: Dict[str, Tool] = {}
        self.tool_handlers: Dict[str, Callable] = {}
        
    async def initialize(self) -> None:
        """Initialize all tools."""
        logger.info("Initializing MCP tool registry...")
        # Basic initialization - can be expanded
        
    async def list_tools(self) -> List[Tool]:
        """List all available tools."""
        return list(self.tools.values())
        
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Call a tool by name."""
        if name not in self.tool_handlers:
            raise ValueError(f"Tool {name} not found")
            
        handler = self.tool_handlers[name]
        result = await handler(arguments)
        
        return [TextContent(type="text", text=str(result))]
        
    async def cleanup(self) -> None:
        """Cleanup registry resources."""
        logger.info("Cleaning up MCP tool registry...")
        self.tools.clear()
        self.tool_handlers.clear()