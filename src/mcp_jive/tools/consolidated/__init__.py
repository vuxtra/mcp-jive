"""Consolidated MCP Tools Package.

This package contains the unified tools that consolidate the functionality
of multiple legacy tools into streamlined, AI-optimized interfaces.

Consolidated Tools:
- jive_manage_work_item: Unified CRUD operations for work items
- jive_get_work_item: Unified retrieval and listing
- jive_search_content: Unified search across all content types
- jive_get_hierarchy: Unified hierarchy and dependency navigation
- jive_execute_work_item: Unified execution for work items and workflows
- jive_track_progress: Unified progress tracking and analytics
- jive_sync_data: Unified storage and synchronization

Backward Compatibility:
The package includes a backward compatibility layer that automatically
maps legacy tool calls to the new consolidated tools during the transition period.
"""

from .consolidated_tool_registry import ConsolidatedToolRegistry, create_consolidated_registry
from .unified_work_item_tool import UnifiedWorkItemTool
from .unified_retrieval_tool import UnifiedRetrievalTool
from .unified_search_tool import UnifiedSearchTool
from .unified_hierarchy_tool import UnifiedHierarchyTool
from .unified_execution_tool import UnifiedExecutionTool
from .unified_progress_tool import UnifiedProgressTool
from .unified_storage_tool import UnifiedStorageTool
from .unified_reorder_tool import UnifiedReorderTool
from .backward_compatibility import BackwardCompatibilityWrapper, MigrationHelper

# Version information
__version__ = "1.0.0"
__author__ = "MCP Jive Team"
__description__ = "Consolidated MCP Tools for AI-Optimized Project Management"

# Tool categories for easy reference
TOOL_CATEGORIES = {
    "Core Entity Management": [
        "jive_manage_work_item",
        "jive_get_work_item"
    ],
    "Search & Discovery": [
        "jive_search_content"
    ],
    "Hierarchy & Dependencies": [
        "jive_get_hierarchy",
        "jive_reorder_work_items"
    ],
    "Execution & Monitoring": [
        "jive_execute_work_item"
    ],
    "Progress & Analytics": [
        "jive_track_progress"
    ],
    "Storage & Sync": [
        "jive_sync_data"
    ]
}

# Consolidated tool names
CONSOLIDATED_TOOLS = [
    "jive_manage_work_item",
    "jive_get_work_item", 
    "jive_search_content",
    "jive_get_hierarchy",
    "jive_execute_work_item",
    "jive_track_progress",
    "jive_sync_data",
    "jive_reorder_work_items"
]

# Legacy tools that are replaced by consolidated tools
LEGACY_TOOLS_REPLACED = [
    # Work Item Management
    "jive_create_work_item",
    "jive_update_work_item",
    "jive_create_task",
    "jive_update_task",
    "jive_delete_task",
    
    # Retrieval
    "jive_get_task",
    "jive_list_work_items",
    "jive_list_tasks",
    
    # Search
    "jive_search_work_items",
    "jive_search_tasks",
    
    # Hierarchy
    "jive_get_work_item_children",
    "jive_get_work_item_dependencies",
    "jive_get_task_hierarchy",
    "jive_add_dependency",
    "jive_remove_dependency",
    "jive_validate_dependencies",
    
    # Execution
    "jive_execute_workflow",
    "jive_validate_workflow",
    "jive_get_workflow_status",
    "jive_cancel_workflow",
    
    # Progress
    "jive_get_progress_report",
    "jive_set_milestone",
    "jive_get_analytics",
    
    # Storage
    "jive_sync_file_to_database",
    "jive_sync_database_to_file",
    "jive_get_sync_status"
]

# Migration benefits
CONSOLIDATION_BENEFITS = {
    "for_ai_agents": [
        "Simplified decision-making with fewer tools",
        "Unified parameter patterns across operations",
        "Reduced cognitive load and faster execution",
        "Better error handling and validation",
        "Consistent response formats"
    ],
    "for_developers": [
        "Reduced maintenance overhead",
        "Cleaner API surface",
        "Better documentation and examples",
        "Easier testing and debugging",
        "Improved performance through optimization"
    ],
    "for_users": [
        "More reliable operations",
        "Better progress tracking",
        "Improved error messages",
        "Faster response times",
        "Enhanced functionality through consolidation"
    ]
}

# Quick start guide
QUICK_START_GUIDE = """
# Quick Start Guide for Consolidated MCP Tools

## 1. Create the Registry
```python
from mcp_jive.tools.consolidated import create_consolidated_registry
# from mcp_jive.storage.work_item_storage import WorkItemStorage  # Module not available

# For now, use None as storage - this will be replaced with actual storage implementation
storage = None
registry = create_consolidated_registry(storage, enable_legacy_support=True)
```

## 2. Use Consolidated Tools
```python
# Create a work item
result = await registry.handle_tool_call("jive_manage_work_item", {
    "action": "create",
    "type": "task",
    "title": "Implement feature X",
    "priority": "high"
})

# Search for work items
result = await registry.handle_tool_call("jive_search_content", {
    "query": "authentication",
    "content_types": ["work_item", "title"],
    "limit": 5
})

# Execute a work item
result = await registry.handle_tool_call("jive_execute_work_item", {
    "work_item_id": "task-123",
    "execution_mode": "mcp_client"
})
```

## 3. Migration from Legacy Tools
```python
# Legacy tool calls are automatically mapped
result = await registry.handle_tool_call("jive_create_work_item", {
    "title": "Old style call",
    "type": "task"
})
# This automatically maps to jive_manage_work_item with action="create"

# Get migration information
migration_info = registry.get_migration_info("jive_create_work_item")
print(migration_info["description"])  # Shows how to migrate
```

## 4. Disable Legacy Support (Production)
```python
# After migration is complete
registry.disable_legacy_support()
```
"""

# Export all public components
__all__ = [
    # Main registry
    "ConsolidatedToolRegistry",
    "create_consolidated_registry",
    
    # Individual tools
    "UnifiedWorkItemTool",
    "UnifiedRetrievalTool", 
    "UnifiedSearchTool",
    "UnifiedHierarchyTool",
    "UnifiedExecutionTool",
    "UnifiedProgressTool",
    "UnifiedStorageTool",
    
    # Compatibility layer
    "BackwardCompatibilityWrapper",
    "MigrationHelper",
    
    # Constants and metadata
    "TOOL_CATEGORIES",
    "CONSOLIDATED_TOOLS",
    "LEGACY_TOOLS_REPLACED",
    "CONSOLIDATION_BENEFITS",
    "QUICK_START_GUIDE",
    
    # Version info
    "__version__",
    "__author__",
    "__description__"
]


def get_consolidation_summary() -> dict:
    """Get a summary of the consolidation effort."""
    return {
        "version": __version__,
        "consolidated_tools": len(CONSOLIDATED_TOOLS),
        "legacy_tools_replaced": len(LEGACY_TOOLS_REPLACED),
        "reduction_percentage": round((len(LEGACY_TOOLS_REPLACED) - len(CONSOLIDATED_TOOLS)) / len(LEGACY_TOOLS_REPLACED) * 100, 1),
        "categories": len(TOOL_CATEGORIES),
        "benefits": CONSOLIDATION_BENEFITS,
        "migration_support": "Full backward compatibility with automatic mapping"
    }


def print_consolidation_info():
    """Print information about the consolidation."""
    summary = get_consolidation_summary()
    
    print(f"\n🚀 MCP Jive Consolidated Tools v{summary['version']}")
    print("=" * 50)
    print(f"📊 Consolidation Summary:")
    print(f"   • {summary['consolidated_tools']} consolidated tools")
    print(f"   • {summary['legacy_tools_replaced']} legacy tools replaced")
    print(f"   • {summary['reduction_percentage']}% reduction in tool count")
    print(f"   • {summary['categories']} functional categories")
    print(f"\n🔄 Migration Support: {summary['migration_support']}")
    print(f"\n📚 Quick Start:")
    print("   from mcp_jive.tools.consolidated import create_consolidated_registry")
    print("   registry = create_consolidated_registry(storage)")
    print("\n✨ Ready for AI-optimized project management!\n")


# Print info when module is imported (optional, can be removed for production)
if __name__ != "__main__":
    import os
    if os.getenv("MCP_JIVE_SHOW_CONSOLIDATION_INFO", "false").lower() == "true":
        print_consolidation_info()