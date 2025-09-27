"""MCP Jive server implementation.

Main MCP protocol server that handles client connections, tool registration,
and request routing as specified in the MCP Server Core Infrastructure PRD.
"""

import asyncio
import logging
import signal
import sys
import os
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
    
    # Apply comprehensive MCP serialization fixes for tuple bug
    try:
        from .mcp_serialization_fix import apply_comprehensive_fixes
        apply_comprehensive_fixes()
        logging.getLogger(__name__).info("Applied comprehensive MCP serialization fixes for tuple bug")
        # Emit strong proof of which files are loaded
        try:
            import inspect
            fix_file = inspect.getsourcefile(apply_comprehensive_fixes) or "<unknown>"
            logging.getLogger(__name__).warning(
                "PROOF MCP_JIVE_SERVER_LOADED file=%s fix_file=%s", __file__, fix_file
            )
        except Exception as _e:
            # Use parameterized logging to avoid f-string newline issues that caused SyntaxError
            logging.getLogger(__name__).warning(
                "Failed to log server/fix file paths: %s", _e
            )
    except Exception as fix_error:
        logging.getLogger(__name__).warning(f"Failed to apply MCP serialization fixes: {fix_error}")
        
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
        
        # Apply comprehensive MCP serialization fixes for tuple bug
        try:
            from .mcp_serialization_fix import apply_comprehensive_fixes
            apply_comprehensive_fixes()
            logging.getLogger(__name__).info("Applied comprehensive MCP serialization fixes for tuple bug (fallback import)")
        except Exception as fix_error:
            logging.getLogger(__name__).warning(f"Failed to apply comprehensive MCP serialization fixes (fallback): {fix_error}")
            
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

from .health import HealthMonitor
from .tools.consolidated_registry import MCPConsolidatedToolRegistry, create_mcp_consolidated_registry
from .websocket_manager import websocket_manager

logger = logging.getLogger(__name__)


def create_tool_registry(config: ServerConfig, lancedb_manager: LanceDBManager):
    """Create the consolidated tool registry.
    
    Args:
        config: Server configuration
        lancedb_manager: LanceDB manager instance
        
    Returns:
        MCPConsolidatedToolRegistry instance
    """
    logger.info("Using MCPConsolidatedToolRegistry (consolidated tools)")
    return create_mcp_consolidated_registry(
        config=config,
        lancedb_manager=lancedb_manager
    )


class MCPServer:
    """Main MCP Jive Server implementation."""
    
    def __init__(self, 
                 config: Optional[Config] = None, 
                 lancedb_manager: Optional[LanceDBManager] = None):
        # Accept full Config object or create default
        if isinstance(config, Config):
            self.config = config
        elif isinstance(config, ServerConfig):
            # Create full Config with provided ServerConfig
            full_config = Config()
            full_config.server = config
            self.config = full_config
        else:
            self.config = config or Config()
        
        # Check if MCP is available
        if not MCP_AVAILABLE:
            raise ImportError("MCP library is not available. Please install it with: pip install mcp")
            
        self.server = Server("mcp-jive-server")
        self.lancedb_manager = lancedb_manager
        self.health_monitor: Optional[HealthMonitor] = None
        
        # Tool registry
        self.tool_registry: Optional[MCPConsolidatedToolRegistry] = None
        
        # Initialize namespace manager
        from .namespace.namespace_manager import NamespaceManager, NamespaceConfig
        namespace_config = NamespaceConfig(auto_create_namespaces=True)
        self.namespace_manager = NamespaceManager(namespace_config)
        
        self.is_running = False
        self.start_time: Optional[datetime] = None
        
        # Initialize shutdown event
        self._shutdown_event = asyncio.Event()
        
        # Setup signal handlers
        self._setup_signal_handlers()
        
        # MCP handlers will be registered during MCP server initialization
        # See _register_tool_handlers() method called from initialize_mcp_server()
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive server health status."""
        try:
            # Get component health
            database_health = self.lancedb_manager.get_health_status() if self.lancedb_manager else {"status": "not_initialized"}
            tools_health = self.tool_registry.get_health_status() if self.tool_registry else {"status": "not_initialized"}
            
            # Overall health determination
            overall_status = "healthy"
            if not self.is_running:
                overall_status = "stopped"
            elif database_health.get("status") != "connected":
                overall_status = "degraded"
            
            uptime_seconds = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
            
            return {
                "status": overall_status,
                "running": self.is_running,
                "uptime_seconds": uptime_seconds,
                "version": "0.1.0",
                "components": {
                    "database": database_health,
                    "tools": tools_health,
                },
                "config": {
                    "host": self.config.server.host,
                    "port": self.config.server.port,
                    "debug": self.config.server.debug,
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "running": self.is_running,
                "error": str(e)
            }
        
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
        
    # Old _register_handlers method removed - replaced by _register_tool_handlers
    # which properly returns ListToolsResult instead of List[Tool]
            
    async def start(self) -> None:
        """Start the MCP server and all components."""
        logger.info("Starting MCP Jive Server...")
        self.start_time = datetime.now()
        
        try:
            # Initialize LanceDB if not provided
            if not self.lancedb_manager:
                from .lancedb_manager import DatabaseConfig as LanceDBConfig
                db_config = LanceDBConfig(
                    data_path=getattr(self.config.database, 'lancedb_data_path', './data/lancedb_jive'),
                    namespace=getattr(self.config.database, 'lancedb_namespace', None),
                    embedding_model=getattr(self.config.database, 'lancedb_embedding_model', 'all-MiniLM-L6-v2'),
                    device=getattr(self.config.database, 'lancedb_device', 'cpu')
                )
                self.lancedb_manager = LanceDBManager(db_config)
                await self.lancedb_manager.initialize()
            
            # Initialize health monitor
            self.health_monitor = HealthMonitor(self.config, self.lancedb_manager)
            
            # Initialize consolidated tool registry
            logger.info("Initializing tool registry")
            self.tool_registry = create_tool_registry(
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

    async def _register_tool_handlers_for_server(self, server: Server) -> None:
        """Register MCP tool handlers for a specific server instance."""
        if not server or not self.tool_registry:
            return

        # List tools handler
        @server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available tools."""
            try:
                # Get tool schemas from the registry
                tool_schemas = {}
                if hasattr(self.tool_registry, 'get_tool_schemas'):
                    tool_schemas = self.tool_registry.get_tool_schemas()
                else:
                    # Fallback for legacy registry
                    tool_names = await self.tool_registry.list_tools()
                    tool_schemas = {name: {} for name in tool_names}
                
                # Convert internal schemas to MCP Tool objects
                mcp_tools = []
                for tool_name, schema in tool_schemas.items():
                    try:
                        # Ensure we have proper schema structure
                        tool_schema = {
                            "name": schema.get("name", tool_name),
                            "description": schema.get("description", f"Tool: {tool_name}"),
                            "inputSchema": schema.get("inputSchema", {"type": "object", "properties": {}})
                        }
                        
                        # Create MCP Tool object
                        mcp_tool = Tool(
                            name=tool_schema["name"],
                            description=tool_schema["description"],
                            inputSchema=tool_schema["inputSchema"]
                        )
                        mcp_tools.append(mcp_tool)
                        
                    except Exception as e:
                        logger.error(f"Error creating MCP tool for {tool_name}: {e}")
                        # Create minimal tool as fallback
                        mcp_tool = Tool(
                            name=tool_name,
                            description=f"Tool: {tool_name}",
                            inputSchema={"type": "object", "properties": {}}
                        )
                        mcp_tools.append(mcp_tool)
                
                # Debug logging
                logger.debug(f"Converted {len(mcp_tools)} tools to MCP format")
                for i, tool in enumerate(mcp_tools):
                    logger.debug(f"MCP Tool {i}: name={tool.name}, type={type(tool)}")
                
                # Return list of tools (MCP library will wrap in ListToolsResult)
                return mcp_tools
                
            except Exception as e:
                logger.error(f"Error listing tools: {e}")
                # Return empty tools list on error
                return []
        
        # Call tool handler
        @server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Handle tool execution requests."""
            try:
                logger.debug(f"Calling tool '{name}' with arguments: {arguments}")
                
                # Use call_tool method which returns List[TextContent]
                content = await self.tool_registry.call_tool(name, arguments)
                
                return CallToolResult(content=content)
                
            except Exception as e:
                logger.error(f"Error calling tool '{name}': {e}")
                
                # Return error as content
                error_content = [TextContent(
                    type="text",
                    text=f"Error executing tool '{name}': {str(e)}"
                )]
                return CallToolResult(content=error_content, isError=True)

    async def call_tool_with_namespace(self, name: str, arguments: Dict[str, Any], namespace: Optional[str] = None) -> Any:
        """Call a tool with namespace context.
        
        Args:
            name: Tool name to execute
            arguments: Tool arguments
            namespace: Optional namespace for tool execution
            
        Returns:
            Tool execution result
        """
        try:
            logger.debug(f"Calling tool '{name}' with namespace '{namespace}' and arguments: {arguments}")
            
            # If namespace is provided, resolve it and ensure it exists
            if namespace:
                resolved_namespace = self.namespace_manager.resolve_namespace(namespace)
                # Ensure namespace exists (auto-create if enabled)
                if not self.namespace_manager.ensure_namespace_exists(resolved_namespace):
                    raise ValueError(f"Namespace '{resolved_namespace}' does not exist and auto-creation is disabled")
                
                # Update the tool registry context
                if hasattr(self.tool_registry, 'set_namespace_context'):
                    await self.tool_registry.set_namespace_context(resolved_namespace)
            
            # Call the tool
            result = await self.tool_registry.call_tool(name, arguments)
            
            # Reset namespace context if it was set
            if namespace and hasattr(self.tool_registry, 'clear_namespace_context'):
                await self.tool_registry.clear_namespace_context()
                
            return result
            
        except Exception as e:
            logger.error(f"Error calling tool '{name}' with namespace '{namespace}': {e}")
            # Reset namespace context on error
            if namespace and hasattr(self.tool_registry, 'clear_namespace_context'):
                try:
                    await self.tool_registry.clear_namespace_context()
                except:
                    pass
            raise

    async def _register_prompt_handlers_for_server(self, server: Server) -> None:
        """Register MCP prompt handlers for a specific server instance."""
        if not server:
            return
        
        # List prompts handler
        @server.list_prompts()
        async def list_prompts() -> ListPromptsResult:
            """List available prompts."""
            # For now, return empty list - prompts can be added later
            return ListPromptsResult(prompts=[])
            
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
            
            # Register MCP tool handlers for stdio mode
            await self._register_tool_handlers_for_server(self.server)
            await self._register_prompt_handlers_for_server(self.server)
            
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
                        # Create a task for the server run with timeout to prevent hanging
                        server_task = asyncio.create_task(
                            asyncio.wait_for(
                                self.server.run(
                                    read_stream,
                                    write_stream,
                                    self.server.create_initialization_options()
                                ),
                                timeout=30.0  # 30 second timeout for stdio handshake
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
                                # MCP handshake completed successfully, pre-warm embedding model
                                logger.info("MCP handshake completed, pre-warming embedding model...")
                                if hasattr(self, 'lancedb_manager') and self.lancedb_manager:
                                    asyncio.create_task(self.lancedb_manager.warm_up_embedding_model())
                            except asyncio.TimeoutError:
                                logger.warning("MCP stdio handshake timed out after 30 seconds, but server components are ready")
                                logger.info("Server will continue running without stdio transport completion")
                                # Pre-warm embedding model even after timeout
                                if hasattr(self, 'lancedb_manager') and self.lancedb_manager:
                                    asyncio.create_task(self.lancedb_manager.warm_up_embedding_model())
                                # Don't raise the timeout error, just log it and continue
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
                from fastapi import FastAPI, HTTPException, WebSocket, Request
                from fastapi.responses import JSONResponse
                import uvicorn
                from pydantic import BaseModel
                from typing import Dict, Any, Optional
                import json
                from datetime import datetime
                import uuid
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
                return self.get_health_status()
            
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
            
            # Namespace management endpoints
            @app.get("/namespaces")
            async def list_namespaces():
                """List all available namespaces."""
                try:
                    namespaces = self.namespace_manager.list_namespaces()
                    return {"namespaces": namespaces}
                except Exception as e:
                    logger.error(f"Error listing namespaces: {e}")
                    raise HTTPException(status_code=500, detail=str(e))
            
            @app.post("/namespaces")
            async def create_namespace(request: Dict[str, Any]):
                """Create a new namespace."""
                try:
                    namespace_name = request.get("name")
                    if not namespace_name:
                        raise HTTPException(status_code=400, detail="Namespace name is required")
                    
                    success = self.namespace_manager.create_namespace(namespace_name)
                    if success:
                        return {"success": True, "namespace": namespace_name}
                    else:
                        raise HTTPException(status_code=400, detail="Failed to create namespace")
                except HTTPException:
                    raise
                except Exception as e:
                    logger.error(f"Error creating namespace {namespace_name}: {e}")
                    raise HTTPException(status_code=500, detail=str(e))
            
            @app.delete("/namespaces/{namespace_name}")
            async def delete_namespace(namespace_name: str):
                """Delete a namespace."""
                try:
                    # Check if namespace exists
                    if not self.namespace_manager.namespace_exists(namespace_name):
                        raise HTTPException(status_code=404, detail="Namespace not found")
                    
                    # Prevent deletion of default namespace
                    if namespace_name == self.namespace_manager.config.default_namespace:
                        raise HTTPException(status_code=400, detail="Cannot delete default namespace")
                    
                    success = self.namespace_manager.delete_namespace(namespace_name)
                    if success:
                        return {"success": True, "message": f"Namespace '{namespace_name}' deleted"}
                    else:
                        raise HTTPException(status_code=400, detail="Failed to delete namespace")
                except HTTPException:
                    raise
                except Exception as e:
                    logger.error(f"Error deleting namespace {namespace_name}: {e}")
                    raise HTTPException(status_code=500, detail=str(e))
            
            # Execute tool endpoint
            @app.post("/tools/execute", response_model=ToolCallResponse)
            async def execute_tool(request: ToolCallRequest, http_request: Request):
                try:
                    if not self.tool_registry:
                        raise HTTPException(status_code=500, detail="Registry not initialized")
                    
                    # Extract namespace from X-Namespace header
                    namespace = http_request.headers.get("X-Namespace")
                    
                    # Call the tool with namespace support
                    if namespace:
                        result = await self.call_tool_with_namespace(request.tool_name, request.parameters, namespace)
                    else:
                        # Fallback to default behavior for backward compatibility
                        result = await self.tool_registry.handle_tool_call(
                            request.tool_name, 
                            request.parameters
                        )
                    
                    # Ensure result is in the correct format for ToolCallResponse
                    if isinstance(result, list) and len(result) > 0:
                        # Check if it's a TextContent object
                        first_item = result[0]
                        if hasattr(first_item, 'text'):
                            # Handle TextContent list from MCP tools - extract the JSON from text
                            try:
                                import json
                                text_content = first_item.text
                                parsed_result = json.loads(text_content)
                                formatted_result = parsed_result
                                logger.info(f"Successfully parsed TextContent JSON: {type(parsed_result)}")
                            except (json.JSONDecodeError, AttributeError, IndexError) as e:
                                logger.error(f"Failed to parse TextContent JSON: {e}")
                                # Fallback to original result if parsing fails
                                formatted_result = result
                        else:
                            # Regular list, use as-is
                            formatted_result = result
                    elif isinstance(result, dict):
                        formatted_result = result
                    else:
                        # For other types, convert to string and try to parse as JSON
                        try:
                            import json
                            if isinstance(result, str):
                                formatted_result = json.loads(result)
                            else:
                                formatted_result = result
                        except json.JSONDecodeError:
                            formatted_result = result
                    
                    return ToolCallResponse(success=True, result=formatted_result)
                    
                except Exception as e:
                    logger.error(f"Error executing tool {request.tool_name}: {e}")
                    return ToolCallResponse(success=False, error=str(e))
            
            # WebSocket endpoint for real-time communication
            @app.websocket("/ws")
            async def websocket_endpoint(websocket: WebSocket):
                """WebSocket endpoint for real-time communication with frontend."""
                try:
                    await websocket.accept()
                    await websocket_manager.connect(websocket, {
                        "connected_at": datetime.now().isoformat(),
                        "user_agent": websocket.headers.get("user-agent", "unknown")
                    })
                    
                    # Keep connection alive and handle incoming messages
                    while True:
                        try:
                            # Wait for messages from client
                            data = await websocket.receive_text()
                            logger.debug(f"Received WebSocket message: {data}")
                            
                            # Echo back or handle specific message types if needed
                            # For now, just acknowledge receipt
                            await websocket.send_text(json.dumps({
                                "type": "ack",
                                "message": "Message received",
                                "timestamp": datetime.now().isoformat()
                            }))
                            
                        except Exception as e:
                            logger.debug(f"WebSocket message handling error: {e}")
                            break
                            
                except Exception as e:
                    logger.error(f"WebSocket connection error: {e}")
                finally:
                    await websocket_manager.disconnect(websocket)
            
            # MCP WebSocket endpoint for JSON-RPC 2.0 protocol
            @app.websocket("/mcp")
            async def mcp_websocket_endpoint(websocket: WebSocket):
                """WebSocket endpoint for MCP protocol communication."""
                session_id = None
                try:
                    await websocket.accept()
                    logger.info("MCP WebSocket client connected")
                    
                    # Keep connection alive and handle MCP JSON-RPC messages
                    while True:
                        try:
                            # Wait for JSON-RPC messages from client
                            data = await websocket.receive_text()
                            logger.debug(f"Received MCP WebSocket message: {data}")
                            
                            # Parse JSON-RPC request
                            try:
                                request = json.loads(data)
                                method = request.get("method")
                                params = request.get("params", {})
                                request_id = request.get("id")
                                
                                if method == "initialize":
                                    # Handle MCP initialization
                                    protocol_version = params.get("protocolVersion", "2024-11-05")
                                    client_capabilities = params.get("capabilities", {})
                                    client_info = params.get("clientInfo", {})
                                    
                                    logger.info(f"MCP WebSocket client initializing: {client_info.get('name', 'unknown')} v{client_info.get('version', 'unknown')}")
                                    
                                    # Extract bound_namespace from client registration
                                    bound_namespace = None
                                    
                                    # Check for bound_namespace in various locations
                                    if "bound_namespace" in client_info:
                                        bound_namespace = client_info["bound_namespace"]
                                    elif "bound_namespace" in client_capabilities:
                                        bound_namespace = client_capabilities["bound_namespace"]
                                    elif "_meta" in params and "bound_namespace" in params["_meta"]:
                                        bound_namespace = params["_meta"]["bound_namespace"]
                                    
                                    if bound_namespace:
                                        logger.info(f"MCP WebSocket client bound to namespace: {bound_namespace}")
                                    else:
                                        logger.info("MCP WebSocket client has flexible namespace access")
                                    
                                    # Generate session ID
                                    import uuid
                                    session_id = str(uuid.uuid4())
                                    
                                    # Store session with namespace binding
                                    mcp_sessions[session_id] = {
                                        "client_info": client_info,
                                        "capabilities": client_capabilities,
                                        "protocol_version": protocol_version,
                                        "created_at": datetime.now().isoformat(),
                                        "transport": "websocket",
                                        "bound_namespace": bound_namespace
                                    }
                                    
                                    # Send initialization response
                                    response = {
                                        "jsonrpc": "2.0",
                                        "id": request_id,
                                        "result": {
                                            "protocolVersion": "2024-11-05",
                                            "capabilities": {
                                                "tools": {},
                                                "resources": {},
                                                "prompts": {},
                                                "logging": {}
                                            },
                                            "serverInfo": {
                                                "name": "mcp-jive",
                                                "version": "1.0.0"
                                            },
                                            "sessionId": session_id
                                        }
                                    }
                                    await websocket.send_text(json.dumps(response))
                                    
                                elif method == "tools/list":
                                    # Validate session
                                    if not session_id or session_id not in mcp_sessions:
                                        error_response = {
                                            "jsonrpc": "2.0",
                                            "id": request_id,
                                            "error": {
                                                "code": -32002,
                                                "message": "Invalid session"
                                            }
                                        }
                                        await websocket.send_text(json.dumps(error_response))
                                        continue
                                    
                                    # Get available tools
                                    tools_list = await self.list_tools()
                                    response = {
                                        "jsonrpc": "2.0",
                                        "id": request_id,
                                        "result": {
                                            "tools": tools_list
                                        }
                                    }
                                    await websocket.send_text(json.dumps(response))
                                    
                                elif method == "tools/call":
                                    # Validate session
                                    if not session_id or session_id not in mcp_sessions:
                                        error_response = {
                                            "jsonrpc": "2.0",
                                            "id": request_id,
                                            "error": {
                                                "code": -32002,
                                                "message": "Invalid session"
                                            }
                                        }
                                        await websocket.send_text(json.dumps(error_response))
                                        continue
                                    
                                    # Execute tool
                                    tool_name = params.get("name")
                                    tool_arguments = params.get("arguments", {})
                                    
                                    if not tool_name:
                                        error_response = {
                                            "jsonrpc": "2.0",
                                            "id": request_id,
                                            "error": {
                                                "code": -32602,
                                                "message": "Missing tool name"
                                            }
                                        }
                                        await websocket.send_text(json.dumps(error_response))
                                        continue
                                    
                                    # Extract namespace from request metadata or arguments
                                    request_namespace = None
                                    if "_meta" in params:
                                        request_namespace = params["_meta"].get("namespace")
                                    elif "namespace" in tool_arguments:
                                        request_namespace = tool_arguments.get("namespace")
                                    
                                    # Enforce namespace binding for session-based clients
                                    final_namespace = request_namespace
                                    if session_id in mcp_sessions:
                                        session_data = mcp_sessions[session_id]
                                        bound_namespace = session_data.get("bound_namespace")
                                        
                                        if bound_namespace:
                                            # Client is bound to a specific namespace
                                            if request_namespace and request_namespace != bound_namespace:
                                                # Client tried to use a different namespace than bound
                                                error_response = {
                                                    "jsonrpc": "2.0",
                                                    "id": request_id,
                                                    "error": {
                                                        "code": -32602,
                                                        "message": f"Namespace access denied. Client is bound to namespace '{bound_namespace}' but requested '{request_namespace}'"
                                                    }
                                                }
                                                await websocket.send_text(json.dumps(error_response))
                                                continue
                                            
                                            # Use the bound namespace
                                            final_namespace = bound_namespace
                                            logger.debug(f"Using bound namespace '{bound_namespace}' for WebSocket client {session_id}")
                                        else:
                                            # Client is flexible, can use any namespace
                                            logger.debug(f"Using requested namespace '{request_namespace}' for flexible WebSocket client {session_id}")
                                    
                                    # Call the tool with namespace context
                                    result = await self.call_tool_with_namespace(tool_name, tool_arguments, final_namespace)
                                    response = {
                                        "jsonrpc": "2.0",
                                        "id": request_id,
                                        "result": {
                                            "content": [{"type": "text", "text": str(result)}]
                                        }
                                    }
                                    await websocket.send_text(json.dumps(response))
                                    
                                else:
                                    # Unknown method
                                    error_response = {
                                        "jsonrpc": "2.0",
                                        "id": request_id,
                                        "error": {
                                            "code": -32601,
                                            "message": f"Method not found: {method}"
                                        }
                                    }
                                    await websocket.send_text(json.dumps(error_response))
                                    
                            except json.JSONDecodeError as e:
                                logger.error(f"Invalid JSON in MCP WebSocket message: {e}")
                                error_response = {
                                    "jsonrpc": "2.0",
                                    "id": None,
                                    "error": {
                                        "code": -32700,
                                        "message": "Parse error"
                                    }
                                }
                                await websocket.send_text(json.dumps(error_response))
                                
                        except Exception as e:
                            logger.debug(f"MCP WebSocket message handling error: {e}")
                            break
                            
                except Exception as e:
                    logger.error(f"MCP WebSocket connection error: {e}")
                finally:
                    if session_id and session_id in mcp_sessions:
                        del mcp_sessions[session_id]
                    logger.info("MCP WebSocket client disconnected")
            

            
            # Use global session storage for MCP clients
            global mcp_sessions
            
            # MCP protocol endpoint (streamable HTTP transport)
            # Support both /mcp/{namespace} and /mcp (backward compatibility)
            @app.post("/mcp/{namespace}")
            @app.post("/mcp")
            async def mcp_protocol(request: Request, namespace: str = "default"):
                try:
                    # Parse JSON body
                    body = await request.json()
                    method = body.get("method")
                    params = body.get("params", {})
                    request_id = body.get("id")
                    
                    # Get session ID from header
                    session_id = request.headers.get("Mcp-Session-Id")
                    
                    if method == "initialize":
                        # Handle MCP initialization handshake
                        protocol_version = params.get("protocolVersion", "2024-11-05")
                        client_capabilities = params.get("capabilities", {})
                        client_info = params.get("clientInfo", {})
                        
                        # Use URL namespace parameter as primary source, with fallback to clientInfo
                        bound_namespace = namespace if namespace != "default" else None
                        
                        # Fallback: Extract namespace binding from client info or capabilities (for backward compatibility)
                        if not bound_namespace:
                            if "bound_namespace" in client_info:
                                bound_namespace = client_info.get("bound_namespace")
                            elif "namespace" in client_info:
                                bound_namespace = client_info.get("namespace")
                            elif "bound_namespace" in client_capabilities:
                                bound_namespace = client_capabilities.get("bound_namespace")
                            elif "namespace" in client_capabilities:
                                bound_namespace = client_capabilities.get("namespace")
                            elif "_meta" in params and "namespace" in params["_meta"]:
                                bound_namespace = params["_meta"].get("namespace")
                        
                        logger.info(f"MCP client initializing: {client_info.get('name', 'unknown')} v{client_info.get('version', 'unknown')}")
                        logger.info(f"URL namespace: {namespace}")
                        if bound_namespace:
                            logger.info(f"Client bound to namespace: {bound_namespace}")
                        else:
                            logger.info("Client not bound to specific namespace (flexible mode)")
                        
                        # Generate new session ID
                        import uuid
                        new_session_id = str(uuid.uuid4())
                        
                        # Store session with namespace binding
                        mcp_sessions[new_session_id] = {
                            "client_info": client_info,
                            "capabilities": client_capabilities,
                            "protocol_version": protocol_version,
                            "bound_namespace": bound_namespace,  # Store namespace binding
                            "created_at": datetime.now().isoformat()
                        }
                        
                        # Return proper JSON-RPC 2.0 response with session header
                        response_data = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {
                                "protocolVersion": "2024-11-05",
                                "capabilities": {
                                    "tools": {},
                                    "prompts": {},
                                    "resources": {},
                                    "logging": {}
                                },
                                "serverInfo": {
                                    "name": "mcp-jive",
                                    "version": "0.1.0"
                                }
                            }
                        }
                        
                        # Create response with session header
                        response = JSONResponse(content=response_data)
                        response.headers["Mcp-Session-Id"] = new_session_id
                        return response
                    
                    # For all other methods, validate session OR allow sessionless mode
                    # Support sessionless mode for compatibility with simplified MCP clients (like Context7)
                    sessionless_mode = not session_id
                    if session_id and session_id not in mcp_sessions:
                        return JSONResponse(
                            content={
                                "jsonrpc": "2.0",
                                "id": request_id,
                                "error": {
                                    "code": -32002,
                                    "message": "Invalid session",
                                    "data": "Session not found or expired"
                                }
                            },
                            status_code=400
                        )
                    
                    # Log sessionless access for debugging
                    if sessionless_mode:
                        logger.info(f"Sessionless MCP request: {method}")
                    
                    # Initialize response_data to track if it gets set
                    response_data = None
                    logger.info(f"Processing method: {method} with params: {params}")
                    
                    if method == "tools/list":
                        logger.info(f"Processing tools/list request (sessionless: {sessionless_mode})")
                        if self.tool_registry:
                            tools = await self.tool_registry.list_tools()
                            logger.info(f"Found {len(tools)} tools from registry")
                            # tools is already a list of Tool objects, convert them to schemas
                            tool_schemas = []
                            for tool in tools:
                                if hasattr(tool, 'model_dump'):
                                    # Tool is a Pydantic model, serialize it
                                    schema = tool.model_dump(by_alias=True, mode="json", exclude_none=True)
                                    tool_schemas.append(schema)
                                elif isinstance(tool, dict):
                                    # Tool is already a dict
                                    tool_schemas.append(tool)
                                else:
                                    # Fallback: convert to dict manually
                                    schema = {
                                        "name": getattr(tool, 'name', 'unknown'),
                                        "description": getattr(tool, 'description', ''),
                                        "inputSchema": getattr(tool, 'inputSchema', {})
                                    }
                                    tool_schemas.append(schema)
                            response_data = {
                                "jsonrpc": "2.0",
                                "id": request_id,
                                "result": {"tools": tool_schemas}
                            }
                            logger.info(f"Created response with {len(tool_schemas)} tool schemas")
                        else:
                            logger.warning("Tool registry not available")
                            response_data = {
                                "jsonrpc": "2.0",
                                "id": request_id,
                                "result": {"tools": []}
                            }
                        
                        logger.info(f"Returning response: {response_data}")
                        # Return response with session header (only if not sessionless)
                        response = JSONResponse(content=response_data)
                        if not sessionless_mode:
                            response.headers["Mcp-Session-Id"] = session_id
                        return response
                    
                    elif method == "tools/call":
                        tool_name = params.get("name")
                        tool_arguments = params.get("arguments", {})
                        
                        if not self.tool_registry:
                            response_data = {
                                "jsonrpc": "2.0",
                                "id": request_id,
                                "error": {
                                    "code": -32603,
                                    "message": "Registry not initialized"
                                }
                            }
                            response = JSONResponse(content=response_data, status_code=500)
                            if not sessionless_mode:
                                response.headers["Mcp-Session-Id"] = session_id
                            return response
                        
                        # Extract namespace from URL parameter (primary), then request metadata or arguments
                        request_namespace = namespace if namespace != "default" else None
                        
                        # Fallback: Extract from request metadata or arguments (for backward compatibility)
                        if not request_namespace:
                            if "_meta" in params:
                                request_namespace = params["_meta"].get("namespace")
                            elif "namespace" in tool_arguments:
                                request_namespace = tool_arguments.get("namespace")
                        
                        # Enforce namespace binding for session-based clients
                        final_namespace = request_namespace
                        if not sessionless_mode and session_id in mcp_sessions:
                            session_data = mcp_sessions[session_id]
                            bound_namespace = session_data.get("bound_namespace")
                            
                            if bound_namespace:
                                # Client is bound to a specific namespace
                                if request_namespace and request_namespace != bound_namespace:
                                    # Client tried to use a different namespace than bound
                                    response_data = {
                                        "jsonrpc": "2.0",
                                        "id": request_id,
                                        "error": {
                                            "code": -32602,
                                            "message": f"Namespace access denied. Client is bound to namespace '{bound_namespace}' but requested '{request_namespace}'"
                                        }
                                    }
                                    response = JSONResponse(content=response_data, status_code=403)
                                    response.headers["Mcp-Session-Id"] = session_id
                                    return response
                                
                                # Use the bound namespace
                                final_namespace = bound_namespace
                                logger.debug(f"Using bound namespace '{bound_namespace}' for client {session_id}")
                            else:
                                # Client is flexible, can use any namespace
                                logger.debug(f"Using requested namespace '{request_namespace}' for flexible client {session_id}")
                        
                        # Call the tool with namespace context
                        result = await self.call_tool_with_namespace(tool_name, tool_arguments, final_namespace)
                        
                        # Handle TextContent result properly
                        if isinstance(result, list) and len(result) > 0 and hasattr(result[0], 'text'):
                            # Result is already a list of TextContent objects
                            content = [{"type": "text", "text": item.text} for item in result]
                        else:
                            # Fallback: convert to string
                            content = [{"type": "text", "text": str(result)}]
                        
                        response_data = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {"content": content}
                        }
                        response = JSONResponse(content=response_data)
                        if not sessionless_mode:
                            response.headers["Mcp-Session-Id"] = session_id
                        return response
                    
                    elif method == "notifications/initialized":
                        # Handle MCP initialized notification (no response required for notifications)
                        logger.info(f"MCP client initialized notification received (sessionless: {sessionless_mode})")
                        # Notifications don't require a response, return 204 No Content
                        from fastapi import Response
                        return Response(status_code=204)
                    
                    else:
                        # Return JSON-RPC error for unknown methods
                        response_data = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {
                                "code": -32601,
                                "message": f"Method not found: {method}"
                            }
                        }
                        response = JSONResponse(content=response_data, status_code=400)
                        if not sessionless_mode:
                            response.headers["Mcp-Session-Id"] = session_id
                        return response
                        
                except Exception as e:
                    logger.error(f"MCP protocol error: {e}")
                    # Return JSON-RPC error response
                    response_data = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32603,
                            "message": "Internal error",
                            "data": str(e)
                        }
                    }
                    response = JSONResponse(content=response_data, status_code=500)
                    return response
            
            # SSE endpoint for MCP streaming transport
            @app.get("/mcp")
            async def mcp_sse_endpoint():
                """SSE endpoint for MCP streaming transport."""
                try:
                    from fastapi.responses import StreamingResponse
                    import asyncio
                    
                    async def event_stream():
                        """Generate SSE events for MCP communication."""
                        try:
                            # Send initial connection notification (JSON-RPC 2.0)
                            connection_notification = {
                                "jsonrpc": "2.0",
                                "method": "notifications/initialized",
                                "params": {
                                    "protocolVersion": "2024-11-05",
                                    "capabilities": {},
                                    "serverInfo": {
                                        "name": "mcp-jive",
                                        "version": "1.0.0"
                                    }
                                }
                            }
                            yield f"data: {json.dumps(connection_notification)}\n\n"
                            
                            # Keep connection alive with periodic heartbeat (JSON-RPC 2.0)
                            while True:
                                await asyncio.sleep(30)  # Send heartbeat every 30 seconds
                                heartbeat_notification = {
                                    "jsonrpc": "2.0",
                                    "method": "notifications/heartbeat",
                                    "params": {
                                        "timestamp": datetime.now().isoformat()
                                    }
                                }
                                yield f"data: {json.dumps(heartbeat_notification)}\n\n"
                        except Exception as e:
                            logger.error(f"SSE stream error: {e}")
                            error_notification = {
                                "jsonrpc": "2.0",
                                "method": "notifications/error",
                                "params": {
                                    "code": -32603,
                                    "message": "Internal error",
                                    "data": str(e)
                                }
                            }
                            yield f"data: {json.dumps(error_notification)}\n\n"
                    
                    return StreamingResponse(
                        event_stream(),
                        media_type="text/event-stream",
                        headers={
                            "Cache-Control": "no-cache",
                            "Connection": "keep-alive",
                            "Access-Control-Allow-Origin": "*",
                            "Access-Control-Allow-Headers": "Cache-Control"
                        }
                    )
                except Exception as e:
                    logger.error(f"SSE endpoint error: {e}")
                    raise HTTPException(status_code=500, detail=str(e))
            
            # Configure server settings
            host = self.config.server.host or "127.0.0.1"
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
    
    # Removed duplicate run_combined method - using the newer implementation below
    
    async def _verify_port_release(self, host: str, port: int, timeout: float = 10.0) -> None:
        """Verify that the port is fully released after shutdown."""
        import socket
        import time
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    sock.bind((host, port))
                logger.info(f"Port {port} successfully released")
                return
            except OSError as e:
                if e.errno == 48:  # Address already in use
                    await asyncio.sleep(0.5)
                    continue
                else:
                    # Other socket errors, consider port released
                    logger.warning(f"Socket error during port verification: {e}")
                    return
        
        logger.warning(f"Port {port} may still be in use after {timeout}s timeout")
    
    async def _ensure_port_available(self, host: str, port: int, max_retries: int = 5, retry_delay: float = 2.0) -> None:
        """Ensure port is available with enhanced retry mechanism."""
        import socket
        
        for attempt in range(max_retries):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    sock.bind((host, port))
                logger.info(f"Port {port} is available")
                return
            except OSError as e:
                if e.errno == 48:  # Address already in use
                    if attempt < max_retries - 1:
                        logger.warning(f"Port {port} is in use, waiting {retry_delay}s before retry... (attempt {attempt + 1}/{max_retries})")
                        await asyncio.sleep(retry_delay)
                        # Exponential backoff for subsequent retries
                        retry_delay = min(retry_delay * 1.5, 10.0)
                        continue
                    else:
                        logger.error(f"Port {port} is still in use after {max_retries} attempts.")
                        logger.error(f"Please stop any existing server instances or use a different port.")
                        logger.error(f"You can check what's using the port with: lsof -i :{port}")
                        raise RuntimeError(f"Port {port} already in use after {max_retries} attempts") from e
                else:
                    logger.error(f"Unexpected socket error: {e}")
                    raise
    
    async def _run_stdio_server(self) -> None:
        """Internal method to run stdio server for combined mode."""
        try:
            if stdio_server:
                # Create a separate MCP server instance for stdio transport
                stdio_mcp_server = Server("mcp-jive-stdio")
                
                # Register the same handlers for stdio server
                await self._register_tool_handlers_for_server(stdio_mcp_server)
                await self._register_prompt_handlers_for_server(stdio_mcp_server)
                
                async with stdio_server() as (read_stream, write_stream):
                    try:
                        # Add timeout handling like in standalone stdio mode
                        await asyncio.wait_for(
                            stdio_mcp_server.run(
                                read_stream,
                                write_stream,
                                stdio_mcp_server.create_initialization_options()
                            ),
                            timeout=30.0  # 30 second timeout for stdio handshake
                        )
                        
                        # MCP handshake completed successfully, pre-warm embedding model
                        logger.info("MCP handshake completed in combined mode, pre-warming embedding model...")
                        if hasattr(self, 'database') and self.database:
                            asyncio.create_task(self.database.warm_up_embedding_model())
                    except asyncio.TimeoutError:
                        logger.warning("MCP stdio handshake timed out after 30 seconds in combined mode, but server components are ready")
                        logger.info("Server will continue running without stdio transport completion")
                        # Pre-warm embedding model even after timeout
                        if hasattr(self, 'database') and self.database:
                            asyncio.create_task(self.database.warm_up_embedding_model())
                        # Don't raise the timeout error, just log it and continue
                    except Exception as e:
                        logger.error(f"stdio server task error in combined mode: {e}")
                        raise
            else:
                logger.error("stdio_server not available")
                raise RuntimeError("MCP stdio server not available")
        except Exception as e:
            logger.error(f"stdio server error in combined mode: {e}")
    
    async def _register_tool_handlers_for_server(self, server: Server) -> None:
        """Register tool handlers for a specific MCP server instance."""
        if not self.tool_registry:
            logger.warning("Tool registry not initialized, skipping tool handler registration")
            return
        
        @server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """Handle list tools request."""
            try:
                tools = await self.tool_registry.list_tools()
                return tools
            except Exception as e:
                logger.error(f"Error listing tools: {e}")
                return []
        
        @server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
            """Handle call tool request."""
            try:
                result = await self.tool_registry.call_tool(name, arguments)
                
                # Convert result to TextContent
                if isinstance(result, str):
                    return [TextContent(type="text", text=result)]
                elif isinstance(result, dict):
                    import json
                    return [TextContent(type="text", text=json.dumps(result, indent=2))]
                elif isinstance(result, list) and all(isinstance(item, TextContent) for item in result):
                    return result
                else:
                    import json
                    return [TextContent(type="text", text=json.dumps(result, indent=2))]
                    
            except Exception as e:
                logger.error(f"Error calling tool {name}: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    async def _register_prompt_handlers_for_server(self, server: Server) -> None:
        """Register prompt handlers for a specific MCP server instance."""
        @server.list_prompts()
        async def handle_list_prompts() -> ListPromptsResult:
            """Handle list prompts request."""
            return ListPromptsResult(prompts=[])
    
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


# Global server instance will be defined after MCPJiveServer class

# Convenience function for running the server
async def run_server(config: Optional[Config] = None) -> None:
    """Run the MCP Jive server.
    
    Args:
        config: Server configuration. If None, loads from environment.
    """
    server = MCPJiveServer(config)
    set_server_instance(server)  # Set as global instance
    
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
        self.tool_registry = None
        self.mcp_server = None
        self.stats = ServerStats(start_time=datetime.now())
        self._shutdown_event = asyncio.Event()
        self._running = False
        
        # Initialize namespace manager
        from .namespace.namespace_manager import NamespaceManager, NamespaceConfig
        namespace_config = NamespaceConfig(auto_create_namespaces=True)
        self.namespace_manager = NamespaceManager(namespace_config)
        
        # Setup logging
        self._setup_logging()
    
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
            from .lancedb_manager import DatabaseConfig as LanceDBConfig
            db_config = LanceDBConfig(
                data_path=getattr(self.config.database, 'lancedb_data_path', './data/lancedb_jive'),
                namespace=getattr(self.config.database, 'lancedb_namespace', None),
                embedding_model=getattr(self.config.database, 'lancedb_embedding_model', 'all-MiniLM-L6-v2'),
                device=getattr(self.config.database, 'lancedb_device', 'cpu')
            )
            
            self.database = LanceDBManager(db_config)
            await self.database.initialize()
            
            # Initialize tool registry
            self.tool_registry = create_tool_registry(
                config=self.config,
                lancedb_manager=self.database
            )
            await self.tool_registry.initialize()
            
            logger.info("MCP Jive server initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize server: {e}")
            await self.shutdown()
            raise
    
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating shutdown...")
            if hasattr(self, '_shutdown_event'):
                try:
                    loop = asyncio.get_running_loop()
                    loop.call_soon_threadsafe(self._shutdown_event.set)
                except RuntimeError:
                    self._shutdown_event.set()
        
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
    
    async def broadcast_event(self, event_type: str, data: Dict[str, Any]) -> int:
        """Broadcast an event to all connected WebSocket clients.
        
        Args:
            event_type: Type of event (e.g., 'work_item_update', 'progress_update')
            data: Event data to broadcast
            
        Returns:
            Number of clients that received the event
        """
        try:
            return await websocket_manager.broadcast_event(event_type, data)
        except Exception as e:
            logger.error(f"Failed to broadcast {event_type} event: {e}")
            return 0
    
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
    
    async def run_combined(self) -> None:
        """Run the MCP server using combined transport (stdio + http with embedded websocket)."""
        logger.info("Starting MCP Jive server with combined transport...")
        
        try:
            # Initialize the server (but don't start stdio transport yet)
            await self.initialize()
            self._running = True
            
            # Setup signal handlers for graceful shutdown
            self._setup_signal_handlers()
            
            # Use the MCPServer's run_http method for HTTP transport
            mcp_server = MCPServer(
                config=self.config,
                lancedb_manager=self.database
            )
            
            # Set the tool registry on the MCP server
            mcp_server.tool_registry = self.tool_registry
            
            # Run the HTTP server
            await mcp_server.run_http()
            
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Error running combined server: {e}")
            raise
        finally:
            logger.info("Shutting down combined server...")
            await self.shutdown()
            logger.info("Combined server shutdown complete")


# Global server instance for broadcasting events from MCP tools
_global_server_instance: Optional[MCPJiveServer] = None

# Global session storage for MCP clients (moved from local scope to fix session persistence)
mcp_sessions: Dict[str, Dict[str, Any]] = {}

def get_server_instance() -> Optional[MCPJiveServer]:
    """Get the global server instance for broadcasting events.
    
    Returns:
        The global server instance or None if not initialized
    """
    return _global_server_instance

def set_server_instance(server: MCPJiveServer) -> None:
    """Set the global server instance.
    
    Args:
        server: The server instance to set as global
    """
    global _global_server_instance
    _global_server_instance = server


if __name__ == "__main__":
    # Allow running the server directly
    asyncio.run(run_server())