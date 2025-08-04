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
    Tool = Dict[str, Any]
    TextContent = Dict[str, Any]

from .base import BaseTool, ToolExecutionContext
from .consolidated import (
    ConsolidatedToolRegistry,
    create_consolidated_registry,
    CONSOLIDATED_TOOLS,
    LEGACY_TOOLS_REPLACED
)
from ..config import ServerConfig
from ..lancedb_manager import LanceDBManager

logger = logging.getLogger(__name__)


class MCPConsolidatedToolRegistry:
    """MCP Tool Registry using consolidated tools.
    
    This registry provides the new consolidated tools as the primary interface
    while maintaining backward compatibility with legacy tools.
    """
    
    def __init__(self, 
                 config: Optional[ServerConfig] = None,
                 lancedb_manager: Optional[LanceDBManager] = None,
                 enable_legacy_support: bool = True,
                 mode: str = "consolidated"):
        """Initialize the consolidated tool registry.
        
        Args:
            config: Server configuration
            lancedb_manager: Database manager instance
            enable_legacy_support: Whether to support legacy tool calls
            mode: Registry mode - "consolidated", "minimal", or "full"
        """
        self.config = config or ServerConfig()
        self.lancedb_manager = lancedb_manager
        self.enable_legacy_support = enable_legacy_support
        self.mode = mode
        
        # Initialize storage (mock for now - will be replaced with actual implementation)
        # TODO: Implement proper WorkItemStorage class
        self.storage = None  # WorkItemStorage(lancedb_manager=lancedb_manager)
        
        # Initialize consolidated registry
        self.consolidated_registry: Optional[ConsolidatedToolRegistry] = None
        
        # Tool tracking
        self.tools: Dict[str, Tool] = {}
        self.tool_instances: Dict[str, Any] = {}
        self.is_initialized = False
        
        # Performance metrics
        self.call_count = 0
        self.legacy_call_count = 0
        self.error_count = 0
        self.start_time = datetime.now()
        
    async def initialize(self) -> None:
        """Initialize the registry and all tools."""
        if self.is_initialized:
            return
            
        logger.info(f"Initializing MCP Consolidated Tool Registry (mode: {self.mode})...")
        
        try:
            # Initialize storage if available
            if self.storage is not None:
                await self.storage.initialize()
            
            # Create consolidated registry
            self.consolidated_registry = create_consolidated_registry(
                storage=self.storage,
                enable_legacy_support=self.enable_legacy_support
            )
            
            # Register tools based on mode
            if self.mode == "consolidated":
                await self._register_consolidated_tools()
            elif self.mode == "minimal":
                await self._register_minimal_tools()
            elif self.mode == "full":
                await self._register_full_tools()
            else:
                raise ValueError(f"Unknown registry mode: {self.mode}")
                
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
                
        # Add legacy tools if enabled
        if self.enable_legacy_support:
            await self._register_legacy_compatibility()
            
        logger.info(f"Registered {len(CONSOLIDATED_TOOLS)} consolidated tools")
        if self.enable_legacy_support:
            logger.info(f"Legacy support enabled for {len(LEGACY_TOOLS_REPLACED)} tools")
    
    async def _register_minimal_tools(self) -> None:
        """Register minimal set of tools (consolidated + essential legacy)."""
        logger.info("Registering minimal tool set...")
        
        # Register consolidated tools first
        await self._register_consolidated_tools()
        
        # Add any essential tools not covered by consolidation
        # (Currently all essential functionality is covered by consolidated tools)
        
        logger.info(f"Registered {len(self.tools)} minimal tools")
    
    async def _register_full_tools(self) -> None:
        """Register full set of tools (consolidated + all legacy)."""
        logger.info("Registering full tool set...")
        
        # Register consolidated tools
        await self._register_consolidated_tools()
        
        # Add any additional specialized tools not covered by consolidation
        # (Future: could include specialized reporting, advanced analytics, etc.)
        
        logger.info(f"Registered {len(self.tools)} full tools")
    
    async def _register_legacy_compatibility(self) -> None:
        """Register legacy tool compatibility layer."""
        for legacy_tool in LEGACY_TOOLS_REPLACED:
            # Create a placeholder schema for legacy tools
            # The actual mapping is handled by the consolidated registry
            self.tools[legacy_tool] = self._create_legacy_tool_schema(legacy_tool)
            self.tool_instances[legacy_tool] = self.consolidated_registry
    
    def _create_mcp_tool_schema(self, tool_name: str, schema: Dict[str, Any]) -> Tool:
        """Create MCP Tool schema from consolidated tool schema."""
        return Tool(
            name=tool_name,
            description=schema.get("description", f"Consolidated tool: {tool_name}"),
            inputSchema=schema.get("parameters", {})
        )
    
    def _create_legacy_tool_schema(self, tool_name: str) -> Tool:
        """Create MCP Tool schema for legacy tool compatibility."""
        return Tool(
            name=tool_name,
            description=f"Legacy tool (mapped to consolidated): {tool_name}",
            inputSchema={"type": "object", "properties": {}, "additionalProperties": True}
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
        
        try:
            # Check if tool exists
            if name not in self.tools:
                raise ValueError(f"Tool '{name}' not found")
            
            # Track legacy calls
            if name in LEGACY_TOOLS_REPLACED:
                self.legacy_call_count += 1
                logger.debug(f"Legacy tool call: {name} -> consolidated mapping")
            
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
            "is_legacy": name in LEGACY_TOOLS_REPLACED,
            "is_consolidated": name in CONSOLIDATED_TOOLS
        }
        
        # Add migration info for legacy tools
        if name in LEGACY_TOOLS_REPLACED and self.consolidated_registry:
            migration_info = self.consolidated_registry.get_migration_info(name)
            if migration_info:
                info["migration"] = migration_info
                
        return info
    
    async def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry performance and usage statistics."""
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        stats = {
            "mode": self.mode,
            "initialized": self.is_initialized,
            "uptime_seconds": uptime,
            "tools": {
                "total": len(self.tools),
                "consolidated": len([t for t in self.tools if t in CONSOLIDATED_TOOLS]),
                "legacy": len([t for t in self.tools if t in LEGACY_TOOLS_REPLACED])
            },
            "calls": {
                "total": self.call_count,
                "legacy": self.legacy_call_count,
                "consolidated": self.call_count - self.legacy_call_count,
                "errors": self.error_count,
                "success_rate": (self.call_count - self.error_count) / max(self.call_count, 1) * 100
            },
            "performance": {
                "calls_per_second": self.call_count / max(uptime, 1),
                "legacy_percentage": self.legacy_call_count / max(self.call_count, 1) * 100
            },
            "features": {
                "legacy_support": self.enable_legacy_support,
                "storage_initialized": self.storage.is_initialized if self.storage else False
            }
        }
        
        # Add consolidated registry stats if available
        if self.consolidated_registry:
            consolidated_stats = self.consolidated_registry.get_statistics()
            stats["consolidated_registry"] = consolidated_stats
            
        return stats
    
    async def disable_legacy_support(self) -> None:
        """Disable legacy tool support (production mode)."""
        if not self.enable_legacy_support:
            return
            
        logger.info("Disabling legacy tool support...")
        
        # Remove legacy tools from registry
        legacy_tools_to_remove = [name for name in self.tools if name in LEGACY_TOOLS_REPLACED]
        for tool_name in legacy_tools_to_remove:
            del self.tools[tool_name]
            del self.tool_instances[tool_name]
            
        # Disable in consolidated registry
        if self.consolidated_registry:
            self.consolidated_registry.disable_legacy_support()
            
        self.enable_legacy_support = False
        logger.info(f"Removed {len(legacy_tools_to_remove)} legacy tools")
    
    async def enable_legacy_support(self) -> None:
        """Re-enable legacy tool support."""
        if self.enable_legacy_support:
            return
            
        logger.info("Enabling legacy tool support...")
        
        # Re-register legacy compatibility
        await self._register_legacy_compatibility()
        
        # Enable in consolidated registry
        if self.consolidated_registry:
            self.consolidated_registry.enable_legacy_support()
            
        self.enable_legacy_support = True
        logger.info(f"Added {len(LEGACY_TOOLS_REPLACED)} legacy tools")
    
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
    lancedb_manager: Optional[LanceDBManager] = None,
    mode: str = "consolidated",
    enable_legacy_support: bool = True
) -> MCPConsolidatedToolRegistry:
    """Create a new MCP consolidated tool registry.
    
    Args:
        config: Server configuration
        lancedb_manager: Database manager
        mode: Registry mode ("consolidated", "minimal", "full")
        enable_legacy_support: Whether to support legacy tools
        
    Returns:
        Configured registry instance
    """
    return MCPConsolidatedToolRegistry(
        config=config,
        lancedb_manager=lancedb_manager,
        enable_legacy_support=enable_legacy_support,
        mode=mode
    )