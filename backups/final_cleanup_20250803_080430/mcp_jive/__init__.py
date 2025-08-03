"""MCP Jive - Autonomous AI Code Builder.

A Python-based MCP server that enables AI agents to autonomously manage
and execute agile workflows through a refined minimal set of 16 essential tools.
"""

__version__ = "0.1.0"
__author__ = "MCP Jive Development Team"
__description__ = "Autonomous AI Code Builder with MCP Protocol Support"

# Core components
from .server import MCPJiveServer
from .config import Config
from .lancedb_manager import LanceDBManager, DatabaseConfig

__all__ = [
    "MCPJiveServer",
    "Config",
    "LanceDBManager",
    "DatabaseConfig",
    "__version__",
]