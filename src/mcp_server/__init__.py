"""MCP Jive Server - Core Infrastructure Package.

This package provides the foundational MCP server infrastructure including:
- Python MCP Server implementation
- Embedded Weaviate database integration
- Configuration management
- Connection management
- AI model orchestration
- Health monitoring

The server implements the 16 essential MCP tools and maintains strict
architectural boundaries - it never directly accesses client files.
"""

__version__ = "0.1.0"
__author__ = "MCP Jive Team"
__email__ = "team@mcpjive.com"

from .server import MCPServer
from .config import ServerConfig
from mcp_jive.lancedb_manager import LanceDBManager, DatabaseConfig
from .health import HealthMonitor

__all__ = [
    "MCPServer",
    "ServerConfig", 
    "LanceDBManager",
    "DatabaseConfig",
    "HealthMonitor",
]