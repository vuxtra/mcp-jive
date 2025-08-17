"""Consolidated Tool Registry for MCP Jive.

Manages the new unified tools and provides backward compatibility
with legacy tool calls during the transition period.
"""

import logging
from typing import Dict, Any, List, Optional, Type
from ..base import BaseTool

# Import unified tools
from .unified_work_item_tool import UnifiedWorkItemTool
from .unified_retrieval_tool import UnifiedRetrievalTool
from .unified_search_tool import UnifiedSearchTool
from .unified_hierarchy_tool import UnifiedHierarchyTool
from .unified_execution_tool import UnifiedExecutionTool
from .unified_progress_tool import UnifiedProgressTool
from .unified_storage_tool import UnifiedStorageTool
from .unified_reorder_tool import UnifiedReorderTool
from .backward_compatibility import BackwardCompatibilityWrapper, MigrationHelper

logger = logging.getLogger(__name__)


class ConsolidatedToolRegistry:
    """Registry for consolidated MCP tools with backward compatibility."""
    
    def __init__(self, storage=None, enable_legacy_support: bool = True):
        self.storage = storage
        self.enable_legacy_support = enable_legacy_support
        self.tools = {}
        self.legacy_tools = {}
        self.compatibility_wrapper = None
        self.migration_helper = None
        
        # Initialize tools
        self._initialize_consolidated_tools()
        
        # Initialize backward compatibility if enabled
        if enable_legacy_support:
            self._initialize_backward_compatibility()
    
    def _initialize_consolidated_tools(self):
        """Initialize the consolidated tools."""
        # Create tool instances with storage
        tool_instances = [
            UnifiedWorkItemTool(storage=self.storage),
            UnifiedRetrievalTool(storage=self.storage),
            UnifiedSearchTool(storage=self.storage),
            UnifiedHierarchyTool(storage=self.storage),
            UnifiedExecutionTool(storage=self.storage),
            UnifiedProgressTool(storage=self.storage),
            UnifiedStorageTool(storage=self.storage),
            UnifiedReorderTool(storage=self.storage)
        ]
        
        # Register tools
        for tool in tool_instances:
            self.tools[tool.tool_name] = tool
            logger.info(f"Registered consolidated tool: {tool.tool_name}")
    
    def _initialize_backward_compatibility(self):
        """Initialize backward compatibility layer."""
        self.compatibility_wrapper = BackwardCompatibilityWrapper(self)
        self.migration_helper = MigrationHelper(self.compatibility_wrapper)
        logger.info("Backward compatibility layer initialized")
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self.tools.get(tool_name)
    
    def list_tools(self) -> List[str]:
        """List all available consolidated tools."""
        return list(self.tools.keys())
    
    def get_tool_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Get schemas for all consolidated tools mapped by tool name."""
        schemas = {}
        for tool in self.tools.values():
            try:
                schema = tool.get_schema()
                schemas[tool.tool_name] = schema
            except Exception as e:
                logger.error(f"Error getting schema for {tool.tool_name}: {str(e)}")
        return schemas
    
    async def handle_tool_call(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a tool call with automatic legacy support."""
        try:
            # Check if it's a consolidated tool
            if tool_name in self.tools:
                tool = self.tools[tool_name]
                return await tool.handle_tool_call(tool_name, params)
            
            # Check if it's a legacy tool and backward compatibility is enabled
            elif self.enable_legacy_support and self.compatibility_wrapper:
                if self.compatibility_wrapper.is_legacy_tool(tool_name):
                    return await self.compatibility_wrapper.handle_legacy_call(tool_name, params)
            
            # Tool not found
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}",
                "error_code": "TOOL_NOT_FOUND",
                "available_tools": self.list_tools(),
                "legacy_support_enabled": self.enable_legacy_support
            }
        
        except Exception as e:
            logger.error(f"Error handling tool call {tool_name}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "TOOL_CALL_ERROR"
            }
    
    def get_migration_info(self, tool_name: str) -> Dict[str, Any]:
        """Get migration information for a tool."""
        if not self.compatibility_wrapper:
            return {"error": "Backward compatibility not enabled"}
        
        return self.compatibility_wrapper.get_migration_info(tool_name)
    
    def list_legacy_tools(self) -> List[Dict[str, str]]:
        """List all legacy tools and their migration paths."""
        if not self.compatibility_wrapper:
            return []
        
        return self.compatibility_wrapper.list_legacy_tools()
    
    def generate_migration_guide(self) -> str:
        """Generate a comprehensive migration guide."""
        if not self.migration_helper:
            return "Migration helper not available (backward compatibility disabled)"
        
        return self.migration_helper.generate_migration_guide()
    
    def validate_migration(self, legacy_calls: List[Dict]) -> Dict[str, Any]:
        """Validate a set of legacy tool calls for migration readiness."""
        if not self.migration_helper:
            return {"error": "Migration helper not available"}
        
        return self.migration_helper.validate_migration(legacy_calls)
    
    def get_tool_statistics(self) -> Dict[str, Any]:
        """Get statistics about tool usage and migration."""
        stats = {
            "consolidated_tools": {
                "total": len(self.tools),
                "tools": list(self.tools.keys())
            },
            "backward_compatibility": {
                "enabled": self.enable_legacy_support,
                "legacy_tools_supported": 0,
                "migration_mappings": 0
            },
            "tool_categories": {
                "Core Entity Management": ["jive_manage_work_item", "jive_get_work_item"],
                "Search & Discovery": ["jive_search_content"],
                "Hierarchy & Dependencies": ["jive_get_hierarchy"],
                "Execution & Monitoring": ["jive_execute_work_item"],
                "Progress & Analytics": ["jive_track_progress"],
                "Storage & Sync": ["jive_sync_data"]
            }
        }
        
        if self.compatibility_wrapper:
            legacy_tools = self.compatibility_wrapper.list_legacy_tools()
            stats["backward_compatibility"]["legacy_tools_supported"] = len(legacy_tools)
            stats["backward_compatibility"]["migration_mappings"] = len(legacy_tools)
        
        return stats
    
    def get_tool_health_status(self) -> Dict[str, Any]:
        """Get health status of all tools."""
        health_status = {
            "overall_status": "healthy",
            "timestamp": "2024-01-15T10:00:00Z",
            "tools": {},
            "issues": []
        }
        
        for tool_name, tool in self.tools.items():
            try:
                # Test tool schema retrieval
                schema = tool.get_schema()
                
                health_status["tools"][tool_name] = {
                    "status": "healthy",
                    "schema_valid": True,
                    "last_checked": "2024-01-15T10:00:00Z"
                }
            except Exception as e:
                health_status["tools"][tool_name] = {
                    "status": "unhealthy",
                    "schema_valid": False,
                    "error": str(e),
                    "last_checked": "2024-01-15T10:00:00Z"
                }
                health_status["issues"].append(f"Tool {tool_name}: {str(e)}")
        
        # Update overall status
        unhealthy_tools = [name for name, status in health_status["tools"].items() 
                          if status["status"] == "unhealthy"]
        
        if unhealthy_tools:
            health_status["overall_status"] = "degraded" if len(unhealthy_tools) < len(self.tools) / 2 else "unhealthy"
        
        return health_status
    
    def disable_legacy_support(self):
        """Disable legacy tool support."""
        self.enable_legacy_support = False
        self.compatibility_wrapper = None
        self.migration_helper = None
        logger.info("Legacy tool support disabled")
    
    def enable_legacy_support(self):
        """Enable legacy tool support."""
        if not self.enable_legacy_support:
            self.enable_legacy_support = True
            self._initialize_backward_compatibility()
            logger.info("Legacy tool support enabled")
    
    def get_tool_documentation(self) -> Dict[str, Any]:
        """Get comprehensive documentation for all tools."""
        documentation = {
            "consolidated_tools": {},
            "migration_guide": "",
            "examples": {},
            "best_practices": []
        }
        
        # Document each consolidated tool
        for tool_name, tool in self.tools.items():
            try:
                schema = tool.get_schema()
                documentation["consolidated_tools"][tool_name] = {
                    "description": schema.get("description", ""),
                    "parameters": schema.get("inputSchema", {}),
                    "category": self._get_tool_category(tool_name),
                    "replaces": self._get_replaced_tools(tool_name)
                }
            except Exception as e:
                logger.error(f"Error documenting tool {tool_name}: {str(e)}")
        
        # Add migration guide
        if self.migration_helper:
            documentation["migration_guide"] = self.migration_helper.generate_migration_guide()
        
        # Add examples
        documentation["examples"] = self._get_tool_examples()
        
        # Add best practices
        documentation["best_practices"] = [
            "Use consolidated tools for new integrations",
            "Migrate legacy tool calls during maintenance windows",
            "Test consolidated tools in development before production use",
            "Monitor deprecation warnings for legacy tools",
            "Use validation_only mode for testing sync operations",
            "Create backups before major sync operations",
            "Use filters to limit scope of operations",
            "Monitor execution status for long-running operations"
        ]
        
        return documentation
    
    def _get_tool_category(self, tool_name: str) -> str:
        """Get the category for a tool."""
        category_map = {
            "jive_manage_work_item": "Core Entity Management",
            "jive_get_work_item": "Core Entity Management",
            "jive_search_content": "Search & Discovery",
            "jive_get_hierarchy": "Hierarchy & Dependencies",
            "jive_execute_work_item": "Execution & Monitoring",
            "jive_track_progress": "Progress & Analytics",
            "jive_sync_data": "Storage & Sync"
        }
        return category_map.get(tool_name, "Unknown")
    
    def _get_replaced_tools(self, tool_name: str) -> List[str]:
        """Get the list of legacy tools replaced by a consolidated tool."""
        if not self.compatibility_wrapper:
            return []
        
        replaced_tools = []
        for legacy_tool, mapping in self.compatibility_wrapper.migration_map.items():
            if mapping["new_tool"] == tool_name:
                replaced_tools.append(legacy_tool)
        
        return replaced_tools
    
    def _get_tool_examples(self) -> Dict[str, List[Dict]]:
        """Get usage examples for each tool."""
        return {
            "jive_manage_work_item": [
                {
                    "description": "Create a new task",
                    "params": {
                        "action": "create",
                        "type": "task",
                        "title": "Implement user authentication",
                        "description": "Add login and registration functionality",
                        "priority": "high"
                    }
                },
                {
                    "description": "Update task status",
                    "params": {
                        "action": "update",
                        "work_item_id": "task-123",
                        "status": "in_progress",
                        "progress_percentage": 50
                    }
                }
            ],
            "jive_get_work_item": [
                {
                    "description": "Get a specific work item",
                    "params": {
                        "work_item_id": "task-123",
                        "include_children": True
                    }
                },
                {
                    "description": "List all high-priority tasks",
                    "params": {
                        "filters": {
                            "priority": ["high"],
                            "type": ["task"]
                        },
                        "limit": 10
                    }
                }
            ],
            "jive_search_content": [
                {
                    "description": "Search for authentication-related work items",
                    "params": {
                        "query": "authentication login",
                        "content_types": ["work_item", "title", "description"],
                        "limit": 5
                    }
                }
            ],
            "jive_get_hierarchy": [
                {
                    "description": "Get all children of an epic",
                    "params": {
                        "work_item_id": "epic-456",
                        "relationship_type": "children",
                        "include_metadata": True
                    }
                }
            ],
            "jive_execute_work_item": [
                {
                    "description": "Execute a task autonomously",
                    "params": {
                        "work_item_id": "task-789",
                        "execution_mode": "mcp_client",
                        "monitoring_config": {
                            "progress_updates": True,
                            "notify_on_completion": True
                        }
                    }
                }
            ],
            "jive_track_progress": [
                {
                    "description": "Update progress for a work item",
                    "params": {
                        "action": "track",
                        "work_item_id": "task-123",
                        "progress_data": {
                            "progress_percentage": 75,
                            "status": "in_progress",
                            "notes": "API integration completed"
                        }
                    }
                }
            ],
            "jive_sync_data": [
                {
                    "description": "Sync work items to JSON file",
                    "params": {
                        "action": "sync",
                        "sync_direction": "db_to_file",
                        "target_file_path": "./exports/work_items.json",
                        "format": "json",
                        "filters": {
                            "status": ["completed"]
                        }
                    }
                }
            ]
        }


# Factory function for creating the registry
def create_consolidated_registry(storage=None, 
                               enable_legacy_support: bool = True) -> ConsolidatedToolRegistry:
    """Create a consolidated tool registry."""
    # Set up dependency injection for ProgressCalculator if storage is available
    if storage and hasattr(storage, 'progress_calculator') and storage.progress_calculator is None:
        from ...services.progress_calculator import ProgressCalculator
        storage.progress_calculator = ProgressCalculator(storage)
    
    return ConsolidatedToolRegistry(storage, enable_legacy_support)


# Export the registry class and factory function
__all__ = ["ConsolidatedToolRegistry", "create_consolidated_registry"]