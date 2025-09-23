"""Namespace management for MCP-Jive server.

This module provides namespace isolation capabilities, allowing multiple
projects to use the same MCP server instance with complete data separation.
"""

from .namespace_manager import NamespaceManager

__all__ = ["NamespaceManager"]