"""Database manager for MCP Jive server.

This module provides the database manager for the MCP Jive component,
using LanceDB as the embedded vector database.

Features:
- True embedded operation (no external services)
- Built-in vectorization with sentence-transformers
- High-performance vector and keyword search
- Automatic schema management
- Async/await support
- Simplified configuration
"""

# Import LanceDB implementation as the main database manager
from .lancedb_manager import (
    LanceDBManager,
    WeaviateManager,  # Compatibility alias
    DatabaseConfig,
    SearchType,
    WorkItemModel,
    ExecutionLogModel
)

# Re-export for backward compatibility
__all__ = [
    'LanceDBManager',
    'WeaviateManager',  # Compatibility alias for gradual migration
    'DatabaseConfig',
    'SearchType',
    'WorkItemModel',
    'ExecutionLogModel'
]

# For backward compatibility, make WeaviateManager the default export
# This allows existing code to continue working during migration
DatabaseManager = LanceDBManager
WeaviateManager = WeaviateManager  # Explicit compatibility alias