"""Main MCP Server implementation.

Core MCP server that implements the Model Context Protocol,
manages connections, and orchestrates all server components.
"""

import logging
import asyncio
import signal
import sys
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import json

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource, Tool, TextContent, ImageContent, EmbeddedResource,
    CallToolRequest, CallToolResult, ListResourcesRequest, ListResourcesResult,
    ListToolsRequest, ListToolsResult, ReadResourceRequest, ReadResourceResult
)

from .config import ServerConfig
from .database import WeaviateManager
from .health import HealthMonitor
from .tools import MCPToolRegistry

logger = logging.getLogger(__name__)


class MCPServer:
    """Main MCP Jive Server implementation."""
    
    def __init__(self, config: Optional[ServerConfig] = None):
        self.config = config or ServerConfig()
        self.server = Server("mcp-jive-server")
        self.weaviate_manager: Optional[WeaviateManager] = None
        self.health_monitor: Optional[HealthMonitor] = None
        self.tool_registry: Optional[MCPToolRegistry] = None
        self.is_running = False
        self.start_time: Optional[datetime] = None
        
        # Setup signal handlers
        self._setup_signal_handlers()
        
        # Register MCP handlers
        self._register_handlers()
        
    def _setup_signal_handlers(self) -> None:
        """Setup graceful shutdown signal handlers."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            asyncio.create_task(self.stop())
            
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
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent | ImageContent | EmbeddedResource]:
            """Handle call_tool request."""
            if not self.tool_registry:
                raise RuntimeError("Tool registry not initialized")
                
            return await self.tool_registry.call_tool(name, arguments)
            
        @self.server.list_resources()
        async def handle_list_resources() -> List[Resource]:
            """Handle list_resources request."""
            # Return available resources (health, metrics, etc.)
            resources = [
                Resource(
                    uri="health://status",
                    name="Health Status",
                    description="Current health status of all server components",
                    mimeType="application/json"
                ),
                Resource(
                    uri="metrics://current",
                    name="Current Metrics",
                    description="Current system and server metrics",
                    mimeType="application/json"
                ),
                Resource(
                    uri="config://current",
                    name="Server Configuration",
                    description="Current server configuration (sanitized)",
                    mimeType="application/json"
                )
            ]
            
            return resources
            
        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> str:
            """Handle read_resource request."""
            if uri == "health://status":
                if self.health_monitor:
                    health_data = await self.health_monitor.get_overall_health()
                    return json.dumps(health_data, indent=2)
                else:
                    return json.dumps({"status": "unhealthy", "message": "Health monitor not available"})
                    
            elif uri == "metrics://current":
                if self.health_monitor:
                    metrics_data = await self.health_monitor.get_metrics()
                    return json.dumps(metrics_data, indent=2)
                else:
                    return json.dumps({"error": "Metrics not available"})
                    
            elif uri == "config://current":
                config_data = self.config.to_dict()
                return json.dumps(config_data, indent=2)
                
            else:
                raise ValueError(f"Unknown resource URI: {uri}")
                
    async def start(self) -> None:
        """Start the MCP server and all components."""
        logger.info("Starting MCP Jive Server...")
        self.start_time = datetime.now()
        
        try:
            # Initialize Weaviate database
            logger.info("Initializing Weaviate database...")
            self.weaviate_manager = WeaviateManager(self.config)
            await self.weaviate_manager.start()
            
            # Initialize health monitor
            logger.info("Initializing health monitor...")
            self.health_monitor = HealthMonitor(self.config, self.weaviate_manager)
            
            # Initialize tool registry
            logger.info("Initializing MCP tool registry...")
            self.tool_registry = MCPToolRegistry(self.config, self.weaviate_manager)
            await self.tool_registry.initialize()
            
            # Perform initial health check
            logger.info("Performing initial health check...")
            health_status = await self.health_monitor.get_overall_health()
            logger.info(f"Initial health status: {health_status['status']}")
            
            self.is_running = True
            logger.info(f"MCP Jive Server started successfully on {self.config.server_url}")
            
            # Log startup summary
            await self._log_startup_summary()
            
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
            # Stop tool registry
            if self.tool_registry:
                await self.tool_registry.cleanup()
                
            # Stop Weaviate
            if self.weaviate_manager:
                await self.weaviate_manager.stop()
                
            # Log shutdown summary
            if self.start_time:
                uptime = datetime.now() - self.start_time
                logger.info(f"Server stopped after {uptime} uptime")
                
            logger.info("MCP Jive Server stopped successfully")
            
        except Exception as e:
            logger.error(f"Error during server shutdown: {e}")
            
    async def run_stdio(self) -> None:
        """Run the server using stdio transport."""
        logger.info("Starting MCP server with stdio transport...")
        
        # Start all components
        await self.start()
        
        try:
            # Run the stdio server
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name="mcp-jive-server",
                        server_version="0.1.0",
                        capabilities={
                            "tools": {},
                            "resources": {},
                            "logging": {}
                        }
                    )
                )
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise
        finally:
            await self.stop()
            
    async def _log_startup_summary(self) -> None:
        """Log startup summary information."""
        try:
            summary = {
                "server_version": "0.1.0",
                "environment": self.config.environment,
                "debug_mode": self.config.debug,
                "server_url": self.config.server_url,
                "weaviate_url": self.config.weaviate_url,
                "start_time": self.start_time.isoformat() if self.start_time else None,
            }
            
            # Add tool count
            if self.tool_registry:
                tools = await self.tool_registry.list_tools()
                summary["available_tools"] = len(tools)
                summary["tool_names"] = [tool.name for tool in tools]
                
            # Add health status
            if self.health_monitor:
                health = await self.health_monitor.get_overall_health()
                summary["initial_health"] = health["status"]
                
            logger.info(f"Startup Summary: {json.dumps(summary, indent=2)}")
            
        except Exception as e:
            logger.warning(f"Failed to generate startup summary: {e}")
            
    async def get_status(self) -> Dict[str, Any]:
        """Get current server status."""
        status = {
            "is_running": self.is_running,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
            "environment": self.config.environment,
            "server_url": self.config.server_url,
        }
        
        # Add component status
        if self.health_monitor:
            health = await self.health_monitor.get_overall_health()
            status["health"] = health
            
        if self.tool_registry:
            tools = await self.tool_registry.list_tools()
            status["tools_count"] = len(tools)
            
        if self.weaviate_manager:
            weaviate_health = await self.weaviate_manager.health_check()
            status["weaviate"] = weaviate_health
            
        return status


async def main():
    """Main entry point for the MCP server."""
    try:
        # Load configuration
        config = ServerConfig()
        
        # Create and start server
        server = MCPServer(config)
        await server.run_stdio()
        
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Server failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())