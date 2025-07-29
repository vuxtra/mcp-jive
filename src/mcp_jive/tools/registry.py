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

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for all MCP Jive tools."""
    
    def __init__(self, database=None, ai_orchestrator=None, config=None):
        """Initialize tool registry.
        
        Args:
            database: Weaviate database manager instance.
            ai_orchestrator: AI orchestrator instance.
            config: Configuration object.
        """
        self.database = database
        self.ai_orchestrator = ai_orchestrator
        self.config = config
        self.tools: Dict[str, Tool] = {}
        self.tool_instances: Dict[str, BaseTool] = {}
        
    async def initialize(self) -> None:
        """Initialize all tools and register them."""
        logger.info("Initializing MCP Jive tool registry...")
        
        try:
            # Register AI orchestration tools
            await self._register_ai_orchestration_tools()
            
            # TODO: Register other tool categories as they are implemented
            # - Work Item Management Tools
            # - Hierarchy Management Tools
            # - Execution Control Tools
            # - Storage & Sync Tools
            # - Validation Tools
            
            logger.info(f"Initialized {len(self.tools)} MCP tools: {list(self.tools.keys())}")
            
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