"""Consolidated Tool Registry for MCP Jive.

This registry provides the new consolidated tools as the primary interface
while maintaining backward compatibility with legacy tools during transition.
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
    class MockTool(dict):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.name = self.get('name', '')
            self.description = self.get('description', '')
            self.inputSchema = self.get('inputSchema', {})
    
    class MockTextContent(dict):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.type = self.get('type', 'text')
            self.text = self.get('text', '')
    
    Tool = MockTool
    TextContent = MockTextContent

from .base import BaseTool, ToolExecutionContext
from .consolidated import (
    ConsolidatedToolRegistry,
    create_consolidated_registry,
    CONSOLIDATED_TOOLS,
    LEGACY_TOOLS_REPLACED
)
from ..config import ServerConfig
from ..lancedb_manager import LanceDBManager
from ..storage import WorkItemStorage

logger = logging.getLogger(__name__)


class MCPConsolidatedToolRegistry:
    """MCP Tool Registry using consolidated tools.
    
    This registry provides the new consolidated tools as the primary interface
    while maintaining backward compatibility with legacy tools.
    """
    
    def __init__(self, 
                 config: Optional[ServerConfig] = None,
                 lancedb_manager: Optional[LanceDBManager] = None):
        """Initialize the consolidated tool registry.
        
        Args:
            config: Server configuration
            lancedb_manager: Database manager instance
        """
        self.config = config or ServerConfig()
        self.lancedb_manager = lancedb_manager
        
        # Initialize storage with LanceDB backend
        self.storage = WorkItemStorage(lancedb_manager=lancedb_manager)
        
        # Initialize consolidated registry
        self.consolidated_registry: Optional[ConsolidatedToolRegistry] = None
        
        # Tool tracking
        self.tools: Dict[str, Tool] = {}
        self.tool_instances: Dict[str, Any] = {}
        self.is_initialized = False
        
        # Performance metrics
        self.call_count = 0
        self.error_count = 0
        self.legacy_call_count = 0
        self.start_time = datetime.now()
        
    async def initialize(self) -> None:
        """Initialize the registry and all tools."""
        if self.is_initialized:
            return
            
        logger.info("Initializing MCP Consolidated Tool Registry...")
        
        try:
            # Initialize storage if available
            if self.storage is not None:
                await self.storage.initialize()
            
            # Create consolidated registry with legacy support disabled by default
            self.consolidated_registry = create_consolidated_registry(
                storage=self.storage,
                enable_legacy_support=False
            )
            
            # Register only the 7 consolidated tools
            await self._register_consolidated_tools()
                
            self.is_initialized = True
            logger.info(f"Registry initialized with {len(self.tools)} tools")
            
        except Exception as e:
            logger.error(f"Failed to initialize registry: {e}")
            raise
    
    async def _register_consolidated_tools(self) -> None:
        """Register only the 7 consolidated tools."""
        logger.info("Registering consolidated tools...")
        
        # Get tool schemas from consolidated registry
        tool_schemas = self.consolidated_registry.get_tool_schemas()
        
        for tool_name in CONSOLIDATED_TOOLS:
            if tool_name in tool_schemas:
                schema = tool_schemas[tool_name]
                self.tools[tool_name] = self._create_mcp_tool_schema(tool_name, schema)
                self.tool_instances[tool_name] = self.consolidated_registry
                
        logger.info(f"Registered {len(CONSOLIDATED_TOOLS)} consolidated tools")
    

    
    def _create_mcp_tool_schema(self, tool_name: str, schema: Dict[str, Any]) -> Tool:
        """Create MCP Tool schema from consolidated tool schema."""
        return Tool(
            name=tool_name,
            description=schema.get("description", f"Consolidated tool: {tool_name}"),
            inputSchema=schema.get("inputSchema", {})
        )
    

    
    async def list_tools(self) -> List[Tool]:
        """List all available tools."""
        if not self.is_initialized:
            await self.initialize()
            
        return list(self.tools.values())
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Call a tool by name with arguments."""
        if not self.is_initialized:
            await self.initialize()
            
        self.call_count += 1
        
        # Track legacy calls
        if name not in CONSOLIDATED_TOOLS:
            self.legacy_call_count += 1
        
        try:
            # Check if tool exists
            if name not in self.tools:
                raise ValueError(f"Tool '{name}' not found")
            
            # Execute through consolidated registry
            result = await self.consolidated_registry.handle_tool_call(name, arguments)
            
            # Format result for MCP
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, default=str)
            )]
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Tool call failed for {name}: {e}")
            
            # Return error as text content
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": str(e),
                    "tool": name,
                    "arguments": arguments
                }, indent=2)
            )]
    
    async def handle_tool_call(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a tool call and return the result directly (for HTTP API)."""
        if not self.is_initialized:
            await self.initialize()
            
        self.call_count += 1
        
        # Track legacy calls
        if name not in CONSOLIDATED_TOOLS:
            self.legacy_call_count += 1
        
        try:
            # Check if tool exists
            if name not in self.tools:
                raise ValueError(f"Tool '{name}' not found")
            
            # Execute through consolidated registry
            result = await self.consolidated_registry.handle_tool_call(name, arguments)
            return result
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Tool call failed for {name}: {e}")
            
            # Return error as dict
            return {
                "success": False,
                "error": str(e),
                "tool": name,
                "arguments": arguments
            }
    
    async def get_tool_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a tool."""
        if not self.is_initialized:
            await self.initialize()
            
        if name not in self.tools:
            return None
            
        tool_schema = self.tools[name]
        info = {
            "name": name,
            "description": tool_schema.description,
            "schema": tool_schema.inputSchema,
            "is_consolidated": name in CONSOLIDATED_TOOLS
        }
                
        return info
    
    async def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry performance and usage statistics."""
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        stats = {
            "initialized": self.is_initialized,
            "uptime_seconds": uptime,
            "tools": {
                "total": len(self.tools),
                "consolidated": len([t for t in self.tools if t in CONSOLIDATED_TOOLS])
            },
            "calls": {
                "total": self.call_count,
                "legacy": self.legacy_call_count,
                "errors": self.error_count,
                "success_rate": (self.call_count - self.error_count) / max(self.call_count, 1) * 100
            },
            "performance": {
                "calls_per_second": self.call_count / max(uptime, 1)
            },
            "features": {
                "storage_initialized": self.storage.is_initialized if self.storage else False
            }
        }
        
        # Add consolidated registry stats if available
        if self.consolidated_registry:
            consolidated_stats = self.consolidated_registry.get_tool_statistics()
            stats["consolidated_registry"] = consolidated_stats
            
        return stats
    

    
    async def cleanup(self) -> None:
        """Cleanup registry resources."""
        logger.info("Cleaning up consolidated tool registry...")
        
        try:
            if self.consolidated_registry:
                # Consolidated registry cleanup if needed
                pass
                
            if self.storage:
                await self.storage.cleanup()
                
        except Exception as e:
            logger.error(f"Error during registry cleanup: {e}")
        
        self.is_initialized = False
        logger.info("Registry cleanup completed")


# Factory function for easy creation
def create_mcp_consolidated_registry(
    config: Optional[ServerConfig] = None,
    lancedb_manager: Optional[LanceDBManager] = None
) -> MCPConsolidatedToolRegistry:
    """Create a new MCP consolidated tool registry.
    
    Args:
        config: Server configuration
        lancedb_manager: Database manager
        
    Returns:
        Configured registry instance
    """
    return MCPConsolidatedToolRegistry(
        config=config,
        lancedb_manager=lancedb_manager
    )