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

from .config import Config, ServerConfig
from .lancedb_manager import LanceDBManager, DatabaseConfig
from .tools import ToolRegistry
from .ai_orchestrator import AIOrchestrator
from .health import HealthMonitor
from .tools.registry import MCPToolRegistry

logger = logging.getLogger(__name__)


class MCPServer:
    """Main MCP Jive Server implementation."""
    
    def __init__(self, config: Optional[ServerConfig] = None, lancedb_manager: Optional[LanceDBManager] = None):
        self.config = config or ServerConfig()
        self.server = Server("mcp-jive-server")
        self.lancedb_manager = lancedb_manager
        self.health_monitor: Optional[HealthMonitor] = None
        self.tool_registry: Optional[MCPToolRegistry] = None
        self.is_running = False
        self.start_time: Optional[datetime] = None
        
        # Initialize shutdown event
        self._shutdown_event = asyncio.Event()
        
        # Setup signal handlers
        self._setup_signal_handlers()
        
        # Register MCP handlers
        self._register_handlers()
        
    def _setup_signal_handlers(self) -> None:
        """Setup graceful shutdown signal handlers."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            if hasattr(self, '_shutdown_event'):
                try:
                    loop = asyncio.get_running_loop()
                    loop.call_soon_threadsafe(self._shutdown_event.set)
                except RuntimeError:
                    self._shutdown_event.set()
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
    def _register_handlers(self) -> None:
        """Register MCP protocol handlers."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """Handle list_tools request."""
            if not self.tool_registry:
                return []
            return await self.tool_registry.list_tools()
            
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle call_tool request."""
            if not self.tool_registry:
                raise RuntimeError("Tool registry not initialized")
            return await self.tool_registry.call_tool(name, arguments)
            
    async def start(self) -> None:
        """Start the MCP server and all components."""
        logger.info("Starting MCP Jive Server...")
        self.start_time = datetime.now()
        
        try:
            # Initialize LanceDB if not provided
            if not self.lancedb_manager:
                db_config = DatabaseConfig(data_path='./data/lancedb_jive')
                self.lancedb_manager = LanceDBManager(db_config)
                await self.lancedb_manager.initialize()
            
            # Initialize health monitor
            self.health_monitor = HealthMonitor(self.config, self.lancedb_manager)
            
            # Initialize tool registry
            self.tool_registry = MCPToolRegistry(lancedb_manager=self.lancedb_manager)
            
            self.is_running = True
            logger.info(f"MCP Jive Server started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            await self.stop()
            raise
            
    async def stop(self) -> None:
        """Stop the MCP server and all components."""
        if not self.is_running:
            return
            
        logger.info("Stopping MCP Jive Server...")
        self.is_running = False
        
        try:
            if self.tool_registry:
                await self.tool_registry.cleanup()
            if self.lancedb_manager:
                await self.lancedb_manager.cleanup()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    async def run_stdio(self) -> None:
        """Run the MCP server using stdio transport."""
        logger.info("Starting MCP server with stdio transport...")
        
        try:
            # Start the server components
            await self.start()
            
            # Run the MCP server with stdio transport
            if stdio_server:
                server_task = None
                shutdown_task = None
                stdio_context = None
                
                try:
                    # Create the stdio context manager
                    stdio_context = stdio_server()
                    
                    # Use stdio_server as an async context manager
                    async with stdio_context as (read_stream, write_stream):
                        # Create a task for the server run
                        server_task = asyncio.create_task(
                            self.server.run(
                                read_stream,
                                write_stream,
                                self.server.create_initialization_options()
                            )
                        )
                        
                        # Create a task for shutdown event
                        shutdown_task = asyncio.create_task(self._shutdown_event.wait())
                        
                        # Wait for either the server to complete or shutdown signal
                        done, pending = await asyncio.wait(
                            [server_task, shutdown_task],
                            return_when=asyncio.FIRST_COMPLETED
                        )
                        
                        # If shutdown was triggered, cancel server task and force exit
                        if shutdown_task in done:
                            logger.info("Shutdown signal received, stopping server...")
                            server_task.cancel()
                            try:
                                await server_task
                            except asyncio.CancelledError:
                                logger.info("Server task cancelled successfully")
                            # Force immediate exit since stdio context manager hangs
                            logger.info("Forcing immediate process exit...")
                            import os
                            os._exit(0)
                        
                        # If server task completed, check for exceptions
                        elif server_task in done and not server_task.cancelled():
                            try:
                                await server_task
                            except Exception as e:
                                logger.error(f"Server task error: {e}")
                                raise
                                
                except Exception as e:
                    logger.error(f"Error in stdio context: {e}")
                    # Don't re-raise if it's due to shutdown
                    if not self._shutdown_event.is_set():
                        raise
                finally:
                    # Clean up any remaining tasks
                    for task in [server_task, shutdown_task]:
                        if task and not task.done():
                            task.cancel()
                            try:
                                await task
                            except asyncio.CancelledError:
                                pass
                        
            else:
                logger.error("stdio_server not available. Install MCP package.")
                raise RuntimeError("MCP stdio server not available")
                
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Error running stdio server: {e}")
            # Don't re-raise if it's due to shutdown
            if not self._shutdown_event.is_set():
                raise
        finally:
            logger.info("Shutting down MCP server...")
            await self.stop()
            logger.info("MCP server shutdown complete")
            # Force process exit if shutdown was requested
            if self._shutdown_event.is_set():
                logger.info("Shutdown complete, exiting process...")
                import sys
                sys.exit(0)
    
    async def run_websocket(self) -> None:
        """Run the MCP server using websocket transport."""
        logger.info("WebSocket transport not yet implemented")
        raise NotImplementedError("WebSocket transport not yet implemented")
    
    async def run_http(self) -> None:
        """Run the MCP server using HTTP transport."""
        logger.info("HTTP transport not yet implemented")
        raise NotImplementedError("HTTP transport not yet implemented")


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