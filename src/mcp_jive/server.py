"""MCP Jive server implementation.

Main MCP protocol server that handles client connections, tool registration,
and request routing as specified in the MCP Server Core Infrastructure PRD.
"""

import asyncio
import logging
import signal
import sys
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
import json
from datetime import datetime

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Tool,
        TextContent,
        CallToolRequest,
        CallToolResult,
        ListToolsRequest,
        ListToolsResult,
        GetPromptRequest,
        GetPromptResult,
        ListPromptsRequest,
        ListPromptsResult,
    )
except ImportError:
    # Mock MCP types if not available
    Server = None
    stdio_server = None
    Tool = None
    TextContent = None
    CallToolRequest = None
    CallToolResult = None
    ListToolsRequest = None
    ListToolsResult = None
    GetPromptRequest = None
    GetPromptResult = None
    ListPromptsRequest = None
    ListPromptsResult = None

from .config import Config
from .lancedb_manager import LanceDBManager, DatabaseConfig
from .tools import ToolRegistry
from .ai_orchestrator import AIOrchestrator

logger = logging.getLogger(__name__)


@dataclass
class ServerStats:
    """Server statistics and metrics."""
    start_time: datetime
    requests_handled: int = 0
    tools_called: int = 0
    errors_count: int = 0
    active_connections: int = 0
    
    @property
    def uptime_seconds(self) -> float:
        """Get server uptime in seconds."""
        return (datetime.now() - self.start_time).total_seconds()


class MCPJiveServer:
    """Main MCP Jive server implementation.
    
    Provides MCP protocol server with embedded Weaviate database,
    AI model orchestration, and the refined minimal set of 16 essential tools.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize MCP Jive server.
        
        Args:
            config: Server configuration. If None, loads from environment.
        """
        self.config = config or Config()
        self.database: Optional[LanceDBManager] = None
        self.ai_orchestrator: Optional[AIOrchestrator] = None
        self.tool_registry: Optional[ToolRegistry] = None
        self.mcp_server: Optional[Server] = None
        self.stats = ServerStats(start_time=datetime.now())
        self._shutdown_event = asyncio.Event()
        self._running = False
        
        # Setup logging
        self._setup_logging()
        
        if not Server:
            logger.warning("MCP server not available. Install with: pip install mcp")
    
    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_level = getattr(logging, self.config.server.log_level.upper())
        
        # Configure root logger
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # Set specific logger levels
        if self.config.development.enable_debug_logging:
            logging.getLogger('mcp_jive').setLevel(logging.DEBUG)
            logging.getLogger('lancedb').setLevel(logging.DEBUG)
        
        logger.info(f"Logging configured at {self.config.server.log_level} level")
    
    async def initialize(self) -> None:
        """Initialize all server components."""
        logger.info("Initializing MCP Jive server...")
        
        try:
            # Initialize database
            # Create LanceDB configuration
            db_config = DatabaseConfig(
                data_path=getattr(self.config.database, 'lancedb_data_path', './data/lancedb_jive'),
                embedding_model=getattr(self.config.database, 'lancedb_embedding_model', 'all-MiniLM-L6-v2'),
                device=getattr(self.config.database, 'lancedb_device', 'cpu')
            )
            
            self.database = LanceDBManager(db_config)
            await self.database.initialize()
            
            # Initialize AI orchestrator
            self.ai_orchestrator = AIOrchestrator(self.config.ai)
            await self.ai_orchestrator.initialize()
            
            # Initialize tool registry
            self.tool_registry = ToolRegistry(
                database=self.database,
                ai_orchestrator=self.ai_orchestrator,
                config=self.config
            )
            await self.tool_registry.initialize()
            
            # Initialize MCP server
            await self._initialize_mcp_server()
            
            logger.info("MCP Jive server initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize server: {e}")
            await self.shutdown()
            raise
    
    async def _initialize_mcp_server(self) -> None:
        """Initialize the MCP protocol server."""
        if not Server:
            raise ImportError("MCP server not available. Install with: pip install mcp")
        
        logger.info("Initializing MCP protocol server...")
        
        # Create MCP server instance
        self.mcp_server = Server("mcp-jive")
        
        # Register tool handlers
        await self._register_tool_handlers()
        
        # Register prompt handlers (if needed)
        await self._register_prompt_handlers()
        
        logger.info("MCP protocol server initialized")
    
    async def _register_tool_handlers(self) -> None:
        """Register MCP tool handlers."""
        if not self.mcp_server or not self.tool_registry:
            return
        
        # List tools handler
        @self.mcp_server.list_tools()
        async def list_tools() -> ListToolsResult:
            """List available tools."""
            try:
                tools = await self.tool_registry.list_tools()
                self.stats.requests_handled += 1
                return ListToolsResult(tools=tools)
            except Exception as e:
                logger.error(f"Error listing tools: {e}")
                self.stats.errors_count += 1
                raise
        
        # Call tool handler
        @self.mcp_server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Handle tool execution requests."""
            try:
                logger.debug(f"Calling tool '{name}' with arguments: {arguments}")
                
                result = await self.tool_registry.call_tool(name, arguments)
                
                self.stats.requests_handled += 1
                self.stats.tools_called += 1
                
                # Format result as MCP response
                if isinstance(result, str):
                    content = [TextContent(type="text", text=result)]
                elif isinstance(result, dict):
                    content = [TextContent(type="text", text=json.dumps(result, indent=2))]
                else:
                    content = [TextContent(type="text", text=str(result))]
                
                return CallToolResult(content=content)
                
            except Exception as e:
                logger.error(f"Error calling tool '{name}': {e}")
                self.stats.errors_count += 1
                
                # Return error as content
                error_content = [TextContent(
                    type="text",
                    text=f"Error executing tool '{name}': {str(e)}"
                )]
                return CallToolResult(content=error_content, isError=True)
    
    async def _register_prompt_handlers(self) -> None:
        """Register MCP prompt handlers."""
        if not self.mcp_server:
            return
        
        # List prompts handler
        @self.mcp_server.list_prompts()
        async def list_prompts() -> ListPromptsResult:
            """List available prompts."""
            # For now, return empty list - prompts can be added later
            return ListPromptsResult(prompts=[])
    
    async def start(self) -> None:
        """Start the MCP server."""
        if not self.mcp_server:
            raise RuntimeError("Server not initialized. Call initialize() first.")
        
        logger.info(f"Starting MCP Jive server on {self.config.server.host}:{self.config.server.port}")
        
        try:
            self._running = True
            
            # Setup signal handlers for graceful shutdown
            self._setup_signal_handlers()
            
            # Start the MCP server with stdio transport
            async with stdio_server() as (read_stream, write_stream):
                logger.info("MCP server started with stdio transport")
                self.stats.active_connections = 1
                
                # Run the server
                await self.mcp_server.run(
                    read_stream,
                    write_stream,
                    self.config.server.debug
                )
                
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise
        finally:
            self._running = False
            self.stats.active_connections = 0
            logger.info("MCP server stopped")
    
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating shutdown...")
            asyncio.create_task(self.shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def shutdown(self) -> None:
        """Shutdown the server gracefully."""
        if not self._running:
            return
        
        logger.info("Shutting down MCP Jive server...")
        
        try:
            # Signal shutdown
            self._shutdown_event.set()
            
            # Shutdown components in reverse order
            if self.tool_registry:
                await self.tool_registry.shutdown()
            
            if self.ai_orchestrator:
                await self.ai_orchestrator.shutdown()
            
            if self.database:
                await self.database.shutdown()
            
            self._running = False
            
            # Log final stats
            logger.info(f"Server shutdown complete. Stats: {self.get_stats()}")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    def is_running(self) -> bool:
        """Check if server is running."""
        return self._running
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive server health status."""
        try:
            # Get component health
            database_health = self.database.get_health_status() if self.database else {"status": "not_initialized"}
            ai_health = self.ai_orchestrator.get_health_status() if self.ai_orchestrator else {"status": "not_initialized"}
            tools_health = self.tool_registry.get_health_status() if self.tool_registry else {"status": "not_initialized"}
            
            # Overall health determination
            overall_status = "healthy"
            if not self._running:
                overall_status = "stopped"
            elif database_health.get("status") != "connected":
                overall_status = "degraded"
            elif ai_health.get("status") != "ready":
                overall_status = "degraded"
            
            return {
                "status": overall_status,
                "running": self._running,
                "uptime_seconds": self.stats.uptime_seconds,
                "version": "0.1.0",
                "components": {
                    "database": database_health,
                    "ai_orchestrator": ai_health,
                    "tools": tools_health,
                },
                "stats": self.get_stats(),
                "config": {
                    "host": self.config.server.host,
                    "port": self.config.server.port,
                    "debug": self.config.server.debug,
                    "ai_provider": self.config.ai.default_provider,
                    "execution_mode": self.config.ai.execution_mode,
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "running": self._running,
                "error": str(e)
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get server statistics."""
        return {
            "start_time": self.stats.start_time.isoformat(),
            "uptime_seconds": self.stats.uptime_seconds,
            "requests_handled": self.stats.requests_handled,
            "tools_called": self.stats.tools_called,
            "errors_count": self.stats.errors_count,
            "active_connections": self.stats.active_connections,
            "error_rate": self.stats.errors_count / max(self.stats.requests_handled, 1),
        }
    
    async def reload_config(self) -> None:
        """Reload configuration from environment."""
        logger.info("Reloading server configuration...")
        
        try:
            # Reload config
            self.config.reload()
            
            # Update logging
            self._setup_logging()
            
            # Notify components of config changes
            if self.ai_orchestrator:
                await self.ai_orchestrator.update_config(self.config.ai)
            
            if self.tool_registry:
                await self.tool_registry.update_config(self.config)
            
            logger.info("Configuration reloaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")
            raise


# Convenience function for running the server
async def run_server(config: Optional[Config] = None) -> None:
    """Run the MCP Jive server.
    
    Args:
        config: Server configuration. If None, loads from environment.
    """
    server = MCPJiveServer(config)
    
    try:
        await server.initialize()
        await server.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Server failed: {e}")
        raise
    finally:
        await server.shutdown()


if __name__ == "__main__":
    # Allow running the server directly
    asyncio.run(run_server())