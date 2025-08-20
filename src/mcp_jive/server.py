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

# Try importing MCP with fallback handling
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
    MCP_AVAILABLE = True
except ImportError as e:
    # For testing purposes, let's try a different import approach
    import sys
    import subprocess
    import os
    
    # Try to install MCP if not available
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'mcp>=1.0.0'], 
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Try importing again after installation
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
        MCP_AVAILABLE = True
    except Exception:
        # Mock MCP types if all else fails
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
        MCP_AVAILABLE = False

from .config import Config, ServerConfig
from .lancedb_manager import LanceDBManager, DatabaseConfig
from .tools import ToolRegistry
from .health import HealthMonitor
from .tools.consolidated_registry import MCPConsolidatedToolRegistry, create_mcp_consolidated_registry

logger = logging.getLogger(__name__)


class MCPServer:
    """Main MCP Jive Server implementation."""
    
    def __init__(self, 
                 config: Optional[ServerConfig] = None, 
                 lancedb_manager: Optional[LanceDBManager] = None):
        self.config = config or ServerConfig()
        
        # Check if MCP is available
        if not MCP_AVAILABLE:
            raise ImportError("MCP library is not available. Please install it with: pip install mcp")
            
        self.server = Server("mcp-jive-server")
        self.lancedb_manager = lancedb_manager
        self.health_monitor: Optional[HealthMonitor] = None
        
        # Tool registry
        self.tool_registry: Optional[MCPConsolidatedToolRegistry] = None
        
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
            logger.info("Initializing tool registry")
            self.tool_registry = create_mcp_consolidated_registry(
                config=self.config,
                lancedb_manager=self.lancedb_manager
            )
            await self.tool_registry.initialize()
            
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
    
    # WebSocket functionality has been consolidated into run_combined method
    # Use run_combined() instead for HTTP server with integrated WebSocket support
    
    async def run_http(self) -> None:
        """Run the MCP server using HTTP transport."""
        logger.info("Starting MCP server with HTTP transport...")
        
        try:
            # Start the server components
            await self.start()
            
            # Import required modules for HTTP transport
            try:
                from fastapi import FastAPI, HTTPException, WebSocket
                from fastapi.responses import JSONResponse
                import uvicorn
                from pydantic import BaseModel
                from typing import Dict, Any, Optional
            except ImportError as e:
                logger.error(f"HTTP transport dependencies not available: {e}")
                logger.error("Please install: pip install fastapi uvicorn pydantic")
                raise RuntimeError("HTTP transport dependencies not available")
            
            # Create FastAPI app
            app = FastAPI(title="MCP Jive Server", version="1.0.0")
            
            # Add CORS middleware
            try:
                from fastapi.middleware.cors import CORSMiddleware
                
                app.add_middleware(
                    CORSMiddleware,
                    allow_origins=self.config.security.cors_origins if self.config.security.cors_enabled else [],
                    allow_credentials=True,
                    allow_methods=["*"],
                    allow_headers=["*"],
                )
                logger.info(f"CORS enabled with origins: {self.config.security.cors_origins}")
            except ImportError:
                logger.warning("CORS middleware not available - install fastapi[all]")
            
            # Request/Response models
            class ToolCallRequest(BaseModel):
                tool_name: str
                parameters: Dict[str, Any] = {}
            
            class ToolCallResponse(BaseModel):
                success: bool
                result: Optional[Dict[str, Any]] = None
                error: Optional[str] = None
            
            # Health check endpoint
            @app.get("/health")
            async def health_check():
                return {"status": "healthy", "timestamp": datetime.now().isoformat()}
            
            # List available tools
            @app.get("/tools")
            async def list_tools():
                if self.tool_registry:
                    tools = await self.tool_registry.list_tools()
                    tool_schemas = []
                    for tool in tools:
                        # tool is a Tool object, extract the name
                        tool_name = tool.name if hasattr(tool, 'name') else str(tool)
                        tool_instance = self.tool_registry.tools.get(tool_name)
                        if tool_instance and hasattr(tool_instance, 'get_schema'):
                            schema = tool_instance.get_schema()
                            tool_schemas.append(schema)
                        else:
                            # Fallback: use the Tool object's schema directly
                            tool_schemas.append({
                                "name": tool_name,
                                "description": tool.description if hasattr(tool, 'description') else "",
                                "inputSchema": tool.inputSchema if hasattr(tool, 'inputSchema') else {}
                            })
                    return {"tools": tool_schemas}
                return {"tools": []}
            
            # Execute tool endpoint
            @app.post("/tools/execute", response_model=ToolCallResponse)
            async def execute_tool(request: ToolCallRequest):
                try:
                    if not self.tool_registry:
                        raise HTTPException(status_code=500, detail="Registry not initialized")
                    
                    result = await self.tool_registry.handle_tool_call(
                        request.tool_name, 
                        request.parameters
                    )
                    return ToolCallResponse(success=True, result=result)
                    
                except Exception as e:
                    logger.error(f"Error executing tool {request.tool_name}: {e}")
                    return ToolCallResponse(success=False, error=str(e))
            
            # API routes for frontend compatibility removed - using the proper ToolCallRequest format below
            
            # WebSocket endpoint for frontend
            @app.websocket("/ws")
            async def websocket_endpoint(websocket: WebSocket):
                try:
                    await websocket.accept()
                    logger.info(f"WebSocket connection accepted from {websocket.client}")
                    
                    try:
                        while True:
                            data = await websocket.receive_text()
                            try:
                                message = json.loads(data)
                                logger.debug(f"Received WebSocket message: {message}")
                                
                                # Handle MCP protocol messages
                                if message.get("method") == "tools/list":
                                    if self.tool_registry:
                                        tools = await self.tool_registry.list_tools()
                                        tool_schemas = []
                                        for tool in tools:
                                            tool_name = tool.name if hasattr(tool, 'name') else str(tool)
                                            tool_instance = self.tool_registry.tools.get(tool_name)
                                            if tool_instance and hasattr(tool_instance, 'get_schema'):
                                                schema = tool_instance.get_schema()
                                                tool_schemas.append(schema)
                                        
                                        response = {
                                            "jsonrpc": "2.0",
                                            "id": message.get("id"),
                                            "result": {"tools": tool_schemas}
                                        }
                                    else:
                                        response = {
                                            "jsonrpc": "2.0",
                                            "id": message.get("id"),
                                            "result": {"tools": []}
                                        }
                                    
                                    await websocket.send_text(json.dumps(response))
                                
                                elif message.get("method") == "tools/call":
                                    tool_name = message.get("params", {}).get("name")
                                    arguments = message.get("params", {}).get("arguments", {})
                                    
                                    if self.tool_registry and tool_name:
                                        try:
                                            result = await self.tool_registry.handle_tool_call(tool_name, arguments)
                                            response = {
                                                "jsonrpc": "2.0",
                                                "id": message.get("id"),
                                                "result": {
                                                    "content": [{
                                                        "type": "text",
                                                        "text": json.dumps(result)
                                                    }],
                                                    "isError": False
                                                }
                                            }
                                        except Exception as e:
                                            response = {
                                                "jsonrpc": "2.0",
                                                "id": message.get("id"),
                                                "error": {
                                                    "code": -32603,
                                                    "message": f"Tool execution error: {str(e)}"
                                                }
                                            }
                                    else:
                                        response = {
                                            "jsonrpc": "2.0",
                                            "id": message.get("id"),
                                            "error": {
                                                "code": -32602,
                                                "message": "Invalid tool name or registry not available"
                                            }
                                        }
                                    
                                    await websocket.send_text(json.dumps(response))
                                
                            except json.JSONDecodeError:
                                logger.error("Invalid JSON received over WebSocket")
                            except Exception as e:
                                logger.error(f"Error processing WebSocket message: {e}")
                                
                    except Exception as e:
                        logger.error(f"WebSocket connection error: {e}")
                    finally:
                        logger.info("WebSocket connection closed")
                        
                except Exception as e:
                    logger.error(f"WebSocket endpoint error: {e}")
            
            # MCP protocol endpoint (for compatibility)
            @app.post("/mcp")
            async def mcp_protocol(request: Dict[str, Any]):
                try:
                    method = request.get("method")
                    params = request.get("params", {})
                    
                    if method == "tools/list":
                        if self.tool_registry:
                            tools = await self.tool_registry.list_tools()
                            tool_schemas = []
                            for tool_name in tools:
                                tool_instance = self.tool_registry.tools.get(tool_name)
                                if tool_instance and hasattr(tool_instance, 'get_schema'):
                                    schema = tool_instance.get_schema()
                                    tool_schemas.append(schema)
                            return {"tools": tool_schemas}
                        return {"tools": []}
                    
                    elif method == "tools/call":
                        tool_name = params.get("name")
                        arguments = params.get("arguments", {})
                        
                        if not self.tool_registry:
                            raise HTTPException(status_code=500, detail="Registry not initialized")
                        
                        result = await self.tool_registry.handle_tool_call(tool_name, arguments)
                        return {"content": [{"type": "text", "text": str(result)}]}
                    
                    else:
                        raise HTTPException(status_code=400, detail=f"Unknown method: {method}")
                        
                except Exception as e:
                    logger.error(f"MCP protocol error: {e}")
                    raise HTTPException(status_code=500, detail=str(e))
            
            # Configure server settings
            host = self.config.server.host or "localhost"
            port = self.config.server.port or 3454
            
            logger.info(f"HTTP server starting on http://{host}:{port}")
            logger.info(f"MCP endpoint will be available at http://{host}:{port}/mcp")
            
            # Create uvicorn configuration
            config = uvicorn.Config(
                app=app,
                host=host,
                port=port,
                log_level="info",
                access_log=False,  # Disable access logs to prevent stdout output
                loop="asyncio",
                use_colors=False,  # Disable colors to prevent ANSI codes
                log_config=None    # Use our existing logging configuration
            )
            
            server = uvicorn.Server(config)
            
            # Create tasks for server and shutdown monitoring
            server_task = asyncio.create_task(server.serve())
            shutdown_task = asyncio.create_task(self._shutdown_event.wait())
            
            logger.info(f"HTTP server running on http://{host}:{port}")
            
            # Wait for either server completion or shutdown signal
            done, pending = await asyncio.wait(
                [server_task, shutdown_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel pending tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                    
            # If shutdown was requested, stop the server
            if shutdown_task in done:
                logger.info("Shutdown requested, stopping HTTP server...")
                server.should_exit = True
                if not server_task.done():
                    await server_task
                
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Error running HTTP server: {e}")
            if not self._shutdown_event.is_set():
                raise
        finally:
            logger.info("Shutting down HTTP server...")
            await self.stop()
            logger.info("HTTP server shutdown complete")
    
    async def run_combined(self) -> None:
        """Run the MCP server using combined transport (stdio + http with embedded websocket)."""
        logger.info("Starting MCP server with combined transport (stdio + http with embedded websocket)...")
        
        try:
            # Start the server components
            await self.start()
            
            # Create tasks for transport modes
            tasks = []
            
            # Create HTTP server task (includes embedded WebSocket endpoint)
            http_task = asyncio.create_task(self._run_http_server())
            tasks.append(("HTTP", http_task))
            
            # Create stdio server task
            stdio_task = asyncio.create_task(self._run_stdio_server())
            tasks.append(("stdio", stdio_task))
            
            # Create shutdown monitoring task
            shutdown_task = asyncio.create_task(self._shutdown_event.wait())
            
            logger.info("All transport modes started successfully")
            logger.info(f"HTTP server available at http://{self.config.server.host or 'localhost'}:{self.config.server.port or 3454}")
            logger.info(f"WebSocket endpoint available at ws://{self.config.server.host or 'localhost'}:{self.config.server.port or 3454}/ws")
            logger.info("stdio transport available for direct MCP client connections")
            
            # Wait for shutdown signal or any task to complete
            all_tasks = [task for _, task in tasks] + [shutdown_task]
            done, pending = await asyncio.wait(
                all_tasks,
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel all pending tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            # Log which task completed first
            for name, task in tasks:
                if task in done:
                    if task.exception():
                        logger.error(f"{name} transport failed: {task.exception()}")
                    else:
                        logger.info(f"{name} transport completed")
                        
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Error running combined server: {e}")
            if not self._shutdown_event.is_set():
                raise
        finally:
            logger.info("Shutting down combined server...")
            await self.stop()
            logger.info("Combined server shutdown complete")
    
    async def _run_stdio_server(self) -> None:
        """Internal method to run stdio server for combined mode."""
        try:
            if stdio_server:
                async with stdio_server() as (read_stream, write_stream):
                    await self.server.run(
                        read_stream,
                        write_stream,
                        self.server.create_initialization_options()
                    )
            else:
                logger.error("stdio_server not available")
                raise RuntimeError("MCP stdio server not available")
        except Exception as e:
            logger.error(f"stdio server error in combined mode: {e}")
            raise
    
    async def _run_http_server(self) -> None:
        """Internal method to run HTTP server for combined mode."""
        try:
            from fastapi import FastAPI, HTTPException, WebSocket
            from fastapi.responses import JSONResponse
            import uvicorn
            from pydantic import BaseModel
            from typing import Dict, Any, Optional
        except ImportError as e:
            logger.error(f"HTTP transport dependencies not available: {e}")
            raise RuntimeError("HTTP transport dependencies not available")
        
        # Create FastAPI app (same as in run_http)
        app = FastAPI(title="MCP Jive Server", version="1.0.0")
        
        # Add CORS middleware
        from fastapi.middleware.cors import CORSMiddleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.security.cors_origins if self.config.security.cors_enabled else [],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        logger.info(f"CORS enabled with origins: {self.config.security.cors_origins}")
        
        # Request/Response models
        class ToolCallRequest(BaseModel):
            tool_name: str
            parameters: Dict[str, Any] = {}
        
        class ToolCallResponse(BaseModel):
            success: bool
            result: Optional[Dict[str, Any]] = None
            error: Optional[str] = None
        
        # Health check endpoint
        @app.get("/health")
        async def health_check():
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
        
        # List available tools
        @app.get("/tools")
        async def list_tools():
            if self.tool_registry:
                tools = await self.tool_registry.list_tools()
                tool_schemas = []
                for tool in tools:
                    tool_name = tool.name if hasattr(tool, 'name') else str(tool)
                    tool_instance = self.tool_registry.tools.get(tool_name)
                    if tool_instance and hasattr(tool_instance, 'get_schema'):
                        schema = tool_instance.get_schema()
                        tool_schemas.append(schema)
                    else:
                        tool_schemas.append({
                            "name": tool_name,
                            "description": tool.description if hasattr(tool, 'description') else "",
                            "inputSchema": tool.inputSchema if hasattr(tool, 'inputSchema') else {}
                        })
                return {"tools": tool_schemas}
            return {"tools": []}
        
        # Execute tool endpoint
        @app.post("/tools/execute", response_model=ToolCallResponse)
        async def execute_tool(request: ToolCallRequest):
            try:
                if not self.tool_registry:
                    raise HTTPException(status_code=500, detail="Registry not initialized")
                
                result = await self.tool_registry.handle_tool_call(
                    request.tool_name, 
                    request.parameters
                )
                return ToolCallResponse(success=True, result=result)
                
            except Exception as e:
                logger.error(f"Error executing tool {request.tool_name}: {e}")
                return ToolCallResponse(success=False, error=str(e))
        
        # Duplicate search endpoint removed - keeping the first one
        
        @app.post("/api/mcp/{tool_name}")
        async def mcp_tool_endpoint(tool_name: str, request: Dict[str, Any]):
            """Frontend MCP tool endpoint."""
            try:
                parameters = request.get("parameters", {})
                
                if not self.tool_registry:
                    raise HTTPException(status_code=500, detail="Registry not initialized")
                
                result = await self.tool_registry.handle_tool_call(tool_name, parameters)
                return {"success": True, "result": result}
                
            except Exception as e:
                logger.error(f"MCP tool endpoint error for {tool_name}: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Frontend API endpoints
        @app.post("/search")
        async def search_endpoint(request: Dict[str, Any]):
            """Frontend search endpoint for health checks."""
            try:
                query = request.get("query", "")
                limit = request.get("limit", 1)
                
                if not self.tool_registry:
                    return {"success": False, "error": "Registry not initialized"}
                
                # Use jive_search_content tool for search
                result = await self.tool_registry.handle_tool_call("jive_search_content", {
                    "query": query,
                    "limit": limit,
                    "search_type": "keyword",
                    "format": "summary"
                })
                
                return {"success": True, "data": result}
                
            except Exception as e:
                logger.error(f"Search endpoint error: {e}")
                return {"success": False, "error": str(e)}
        
        @app.post("/api/mcp/{tool_name}")
        async def mcp_tool_endpoint(tool_name: str, request: Dict[str, Any]):
            """Frontend MCP tool endpoint."""
            try:
                parameters = request.get("parameters", {})
                
                if not self.tool_registry:
                    raise HTTPException(status_code=500, detail="Registry not initialized")
                
                result = await self.tool_registry.handle_tool_call(tool_name, parameters)
                return {"success": True, "result": result}
                
            except Exception as e:
                logger.error(f"MCP tool endpoint error for {tool_name}: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # MCP protocol endpoint (for compatibility)
        @app.post("/mcp")
        async def mcp_protocol(request: Dict[str, Any]):
            try:
                method = request.get("method")
                params = request.get("params", {})
                
                if method == "tools/list":
                    if self.tool_registry:
                        tools = await self.tool_registry.list_tools()
                        tool_schemas = []
                        for tool_name in tools:
                            tool_instance = self.tool_registry.tools.get(tool_name)
                            if tool_instance and hasattr(tool_instance, 'get_schema'):
                                schema = tool_instance.get_schema()
                                tool_schemas.append(schema)
                        return {"tools": tool_schemas}
                    return {"tools": []}
                
                elif method == "tools/call":
                    tool_name = params.get("name")
                    arguments = params.get("arguments", {})
                    
                    if not self.tool_registry:
                        raise HTTPException(status_code=500, detail="Registry not initialized")
                    
                    result = await self.tool_registry.handle_tool_call(tool_name, arguments)
                    return {"content": [{"type": "text", "text": str(result)}]}
                
                else:
                    raise HTTPException(status_code=400, detail=f"Unknown method: {method}")
                    
            except Exception as e:
                logger.error(f"MCP protocol error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # API endpoints for frontend integration
        @app.post("/api/mcp/jive_search_content")
        async def api_search_content(request: ToolCallRequest):
            try:
                if not self.tool_registry:
                    raise HTTPException(status_code=500, detail="Registry not initialized")
                result = await self.tool_registry.handle_tool_call("jive_search_content", request.parameters)
                return ToolCallResponse(success=True, result=result)
            except Exception as e:
                logger.error(f"Error in jive_search_content: {e}")
                return ToolCallResponse(success=False, error=str(e))
        
        @app.post("/api/mcp/jive_manage_work_item")
        async def api_manage_work_item(request: ToolCallRequest):
            try:
                if not self.tool_registry:
                    raise HTTPException(status_code=500, detail="Registry not initialized")
                result = await self.tool_registry.handle_tool_call("jive_manage_work_item", request.parameters)
                return ToolCallResponse(success=True, result=result)
            except Exception as e:
                logger.error(f"Error in jive_manage_work_item: {e}")
                return ToolCallResponse(success=False, error=str(e))
        
        @app.post("/api/mcp/jive_get_work_item")
        async def api_get_work_item(request: ToolCallRequest):
            try:
                if not self.tool_registry:
                    raise HTTPException(status_code=500, detail="Registry not initialized")
                result = await self.tool_registry.handle_tool_call("jive_get_work_item", request.parameters)
                return ToolCallResponse(success=True, result=result)
            except Exception as e:
                logger.error(f"Error in jive_get_work_item: {e}")
                return ToolCallResponse(success=False, error=str(e))
        
        @app.post("/api/mcp/jive_get_hierarchy")
        async def api_get_hierarchy(request: ToolCallRequest):
            try:
                if not self.tool_registry:
                    raise HTTPException(status_code=500, detail="Registry not initialized")
                result = await self.tool_registry.handle_tool_call("jive_get_hierarchy", request.parameters)
                return ToolCallResponse(success=True, result=result)
            except Exception as e:
                logger.error(f"Error in jive_get_hierarchy: {e}")
                return ToolCallResponse(success=False, error=str(e))
        
        # WebSocket endpoint for frontend
        @app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            try:
                await websocket.accept()
                logger.info(f"WebSocket connection accepted from {websocket.client}")
                
                try:
                    while True:
                        data = await websocket.receive_text()
                        try:
                            message = json.loads(data)
                            logger.debug(f"Received WebSocket message: {message}")
                            
                            # Handle MCP protocol messages
                            if message.get("method") == "tools/list":
                                if self.tool_registry:
                                    tools = await self.tool_registry.list_tools()
                                    tool_schemas = []
                                    for tool in tools:
                                        tool_name = tool.name if hasattr(tool, 'name') else str(tool)
                                        tool_instance = self.tool_registry.tools.get(tool_name)
                                        if tool_instance and hasattr(tool_instance, 'get_schema'):
                                            schema = tool_instance.get_schema()
                                            tool_schemas.append(schema)
                                    
                                    response = {
                                        "jsonrpc": "2.0",
                                        "id": message.get("id"),
                                        "result": {"tools": tool_schemas}
                                    }
                                else:
                                    response = {
                                        "jsonrpc": "2.0",
                                        "id": message.get("id"),
                                        "result": {"tools": []}
                                    }
                                
                                await websocket.send_text(json.dumps(response))
                            
                            elif message.get("method") == "tools/call":
                                tool_name = message.get("params", {}).get("name")
                                arguments = message.get("params", {}).get("arguments", {})
                                
                                if self.tool_registry and tool_name:
                                    try:
                                        result = await self.tool_registry.handle_tool_call(tool_name, arguments)
                                        response = {
                                            "jsonrpc": "2.0",
                                            "id": message.get("id"),
                                            "result": {
                                                "content": [{
                                                    "type": "text",
                                                    "text": json.dumps(result)
                                                }],
                                                "isError": False
                                            }
                                        }
                                    except Exception as e:
                                        response = {
                                            "jsonrpc": "2.0",
                                            "id": message.get("id"),
                                            "error": {
                                                "code": -32603,
                                                "message": f"Tool execution error: {str(e)}"
                                            }
                                        }
                                else:
                                    response = {
                                        "jsonrpc": "2.0",
                                        "id": message.get("id"),
                                        "error": {
                                            "code": -32602,
                                            "message": "Invalid tool name or registry not available"
                                        }
                                    }
                                
                                await websocket.send_text(json.dumps(response))
                            
                        except json.JSONDecodeError:
                            logger.error("Invalid JSON received over WebSocket")
                        except Exception as e:
                            logger.error(f"Error processing WebSocket message: {e}")
                            
                except Exception as e:
                    logger.error(f"WebSocket connection error: {e}")
                finally:
                    logger.info("WebSocket connection closed")
                    
            except Exception as e:
                logger.error(f"WebSocket endpoint error: {e}")
        
        # Configure server settings
        host = self.config.server.host or "localhost"
        port = self.config.server.port or 3454
        
        # Create uvicorn configuration
        config = uvicorn.Config(
            app=app,
            host=host,
            port=port,
            log_level="info",
            access_log=False,  # Disable access logs to prevent stdout output
            loop="asyncio",
            use_colors=False,  # Disable colors to prevent ANSI codes
            log_config=None    # Use our existing logging configuration
        )
        
        server = uvicorn.Server(config)
        await server.serve()
    



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
    
    Provides MCP protocol server with embedded LanceDB database,
    AI model orchestration, and the refined minimal set of 16 essential tools.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize MCP Jive server.
        
        Args:
            config: Server configuration. If None, loads from environment.
        """
        self.config = config or Config()
        self.database: Optional[LanceDBManager] = None
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
        
        # Only configure logging if no handlers exist (avoid overriding main.py setup)
        root_logger = logging.getLogger()
        if not root_logger.handlers:
            # Configure root logger only if not already configured
            logging.basicConfig(
                level=log_level,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.StreamHandler(sys.stderr)
                ]
            )
        else:
            # If handlers exist, just set the level
            root_logger.setLevel(log_level)
        
        # Set specific logger levels
        if self.config.development.enable_debug_logging:
            logging.getLogger('mcp_jive').setLevel(logging.DEBUG)
            logging.getLogger('lancedb').setLevel(logging.DEBUG)
        
        # Configure third-party library loggers to use stderr
        for lib_logger_name in ['uvicorn', 'uvicorn.access', 'uvicorn.error', 'websockets', 'websockets.server']:
            lib_logger = logging.getLogger(lib_logger_name)
            # Remove any existing handlers that might log to stdout
            lib_logger.handlers.clear()
            # Add stderr handler
            stderr_handler = logging.StreamHandler(sys.stderr)
            stderr_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            lib_logger.addHandler(stderr_handler)
            lib_logger.propagate = False  # Prevent propagation to root logger
        
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
            
            # Initialize tool registry
            self.tool_registry = ToolRegistry(
                database=self.database,
                config=self.config,
                lancedb_manager=self.database
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
            
            # AI orchestrator removed
            
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
            tools_health = self.tool_registry.get_health_status() if self.tool_registry else {"status": "not_initialized"}
            
            # Overall health determination
            overall_status = "healthy"
            if not self._running:
                overall_status = "stopped"
            elif database_health.get("status") != "connected":
                overall_status = "degraded"
            
            return {
                "status": overall_status,
                "running": self._running,
                "uptime_seconds": self.stats.uptime_seconds,
                "version": "0.1.0",
                "components": {
                    "database": database_health,
                    "tools": tools_health,
                },
                "stats": self.get_stats(),
                "config": {
                    "host": self.config.server.host,
                    "port": self.config.server.port,
                    "debug": self.config.server.debug,
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
            # AI orchestrator removed
            
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