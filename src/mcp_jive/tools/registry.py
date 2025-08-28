"""Tool Registry for MCP Jive.

Provides base classes and utilities for MCP tool management.
The main tool registry is now MCPConsolidatedToolRegistry.
"""

import logging
from typing import Dict, Any

try:
    from mcp.types import Tool, TextContent
except ImportError:
    # Mock MCP types if not available
    Tool = Dict[str, Any]
    TextContent = Dict[str, Any]

from .base import BaseTool, ToolExecutionContext
from ..config import ServerConfig
from ..lancedb_manager import LanceDBManager

logger = logging.getLogger(__name__)