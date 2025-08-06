"""Backward Compatibility Layer for Consolidated Tools.

This module provides compatibility wrappers for legacy tool calls,
allowing existing integrations to continue working while migrating
to the new consolidated tool architecture.
"""

import logging
from typing import Dict, Any, Callable, List

logger = logging.getLogger(__name__)


class BackwardCompatibilityWrapper:
    """Wrapper to maintain compatibility with old tool calls."""
    
    def __init__(self, new_tool_registry):
        self.new_tools = new_tool_registry
        self.migration_map = self._build_migration_map()
        self.deprecation_warnings = set()  # Track warnings to avoid spam
    
    def _build_migration_map(self) -> Dict[str, Dict]:
        """Map old tool calls to new tool calls with parameter transformations."""
        return {
            # Work Item Management Tools
            "jive_create_work_item": {
                "new_tool": "jive_manage_work_item",
                "parameter_mapping": lambda params: {"action": "create", **params},
                "description": "Use jive_manage_work_item with action='create'"
            },
            "jive_update_work_item": {
                "new_tool": "jive_manage_work_item",
                "parameter_mapping": lambda params: {"action": "update", **params},
                "description": "Use jive_manage_work_item with action='update'"
            },
            "jive_create_task": {
                "new_tool": "jive_manage_work_item",
                "parameter_mapping": lambda params: {
                    "action": "create", 
                    "type": "task", 
                    **{k: v for k, v in params.items() if k != "type"}
                },
                "description": "Use jive_manage_work_item with action='create' and type='task'"
            },
            "jive_update_task": {
                "new_tool": "jive_manage_work_item",
                "parameter_mapping": lambda params: {
                    "action": "update",
                    "work_item_id": params.get("task_id", params.get("work_item_id")),
                    **{k: v for k, v in params.items() if k not in ["task_id"]}
                },
                "description": "Use jive_manage_work_item with action='update'"
            },
            "jive_delete_task": {
                "new_tool": "jive_manage_work_item",
                "parameter_mapping": lambda params: {
                    "action": "delete",
                    "work_item_id": params.get("task_id", params.get("work_item_id")),
                    "delete_children": params.get("delete_subtasks", False)
                },
                "description": "Use jive_manage_work_item with action='delete'"
            },
            
            # Retrieval Tools
            "jive_get_task": {
                "new_tool": "jive_get_work_item",
                "parameter_mapping": lambda params: {
                    "work_item_id": params.get("task_id", params.get("work_item_id")),
                    "include_children": params.get("include_subtasks", False),
                    **{k: v for k, v in params.items() if k not in ["task_id", "include_subtasks"]}
                },
                "description": "Use jive_get_work_item"
            },
            "jive_list_work_items": {
                "new_tool": "jive_get_work_item",
                "parameter_mapping": lambda params: {
                    # Remove work_item_id to trigger list mode
                    **{k: v for k, v in params.items() if k != "work_item_id"}
                },
                "description": "Use jive_get_work_item without work_item_id parameter"
            },
            "jive_list_tasks": {
                "new_tool": "jive_get_work_item",
                "parameter_mapping": lambda params: {
                    "filters": {
                        "type": ["task"],
                        **params.get("filters", {})
                    },
                    **{k: v for k, v in params.items() if k not in ["filters"]}
                },
                "description": "Use jive_get_work_item with filters.type=['task']"
            },
            
            # Search Tools
            "jive_search_work_items": {
                "new_tool": "jive_search_content",
                "parameter_mapping": lambda params: {
                    **params,
                    "content_types": ["work_item", "title", "description"]
                },
                "description": "Use jive_search_content with content_types=['work_item']"
            },
            "jive_search_tasks": {
                "new_tool": "jive_search_content",
                "parameter_mapping": lambda params: {
                    **params,
                    "content_types": ["task", "title", "description"],
                    "filters": {
                        "type": ["task"],
                        **params.get("filters", {})
                    }
                },
                "description": "Use jive_search_content with content_types=['task'] and filters.type=['task']"
            },
            
            # Hierarchy Tools
            "jive_get_work_item_children": {
                "new_tool": "jive_get_hierarchy",
                "parameter_mapping": lambda params: {
                    **params,
                    "relationship_type": "children"
                },
                "description": "Use jive_get_hierarchy with relationship_type='children'"
            },
            "jive_get_work_item_dependencies": {
                "new_tool": "jive_get_hierarchy",
                "parameter_mapping": lambda params: {
                    **params,
                    "relationship_type": "dependencies"
                },
                "description": "Use jive_get_hierarchy with relationship_type='dependencies'"
            },
            "jive_get_task_hierarchy": {
                "new_tool": "jive_get_hierarchy",
                "parameter_mapping": lambda params: {
                    "work_item_id": params.get("root_task_id", params.get("work_item_id")),
                    "relationship_type": "full_hierarchy",
                    **{k: v for k, v in params.items() if k not in ["root_task_id"]}
                },
                "description": "Use jive_get_hierarchy with relationship_type='full_hierarchy'"
            },
            
            # Workflow Execution Tools
            "jive_execute_workflow": {
                "new_tool": "jive_execute_work_item",
                "parameter_mapping": lambda params: {
                    "work_item_id": params.get("workflow_name", "workflow"),
                    "execution_mode": "mcp_client",
                    "workflow_config": {
                        "execution_order": params.get("execution_mode", "dependency_based"),
                        "auto_start_dependencies": params.get("auto_start", True)
                    },
                    **{k: v for k, v in params.items() if k not in ["workflow_name", "execution_mode", "auto_start"]}
                },
                "description": "Use jive_execute_work_item with workflow_config"
            },
            "jive_validate_workflow": {
                "new_tool": "jive_validate_dependencies",
                "parameter_mapping": lambda params: {
                    "work_item_ids": [task.get("id") for task in params.get("tasks", []) if task.get("id")],
                    "check_circular": params.get("check_circular_dependencies", True),
                    "check_missing": params.get("check_missing_dependencies", True),
                    "check_workflow_validity": True
                },
                "description": "Use jive_validate_dependencies with workflow validation"
            },
            "jive_get_workflow_status": {
                "new_tool": "jive_get_execution_status",
                "parameter_mapping": lambda params: {
                    "execution_id": params.get("workflow_id"),
                    "include_task_details": params.get("include_task_details", True),
                    "include_timeline": params.get("include_timeline", True)
                },
                "description": "Use jive_get_execution_status"
            },
            "jive_cancel_workflow": {
                "new_tool": "jive_cancel_execution",
                "parameter_mapping": lambda params: {
                    "execution_id": params.get("workflow_id"),
                    **{k: v for k, v in params.items() if k != "workflow_id"}
                },
                "description": "Use jive_cancel_execution"
            },
            
            # Progress Tracking Tools
            "jive_get_progress_report": {
                "new_tool": "jive_track_progress",
                "parameter_mapping": lambda params: {
                    "action": "get_report",
                    "report_config": params
                },
                "description": "Use jive_track_progress with action='get_report'"
            },
            "jive_get_analytics": {
                "new_tool": "jive_track_progress",
                "parameter_mapping": lambda params: {
                    "action": "get_analytics",
                    "analytics_config": params
                },
                "description": "Use jive_track_progress with action='get_analytics'"
            },
            
            # Storage Sync Tools
            "jive_sync_file_to_database": {
                "new_tool": "jive_sync_data",
                "parameter_mapping": lambda params: {
                    "sync_direction": "file_to_db",
                    **params
                },
                "description": "Use jive_sync_data with sync_direction='file_to_db'"
            },
            "jive_sync_database_to_file": {
                "new_tool": "jive_sync_data",
                "parameter_mapping": lambda params: {
                    "sync_direction": "db_to_file",
                    **params
                },
                "description": "Use jive_sync_data with sync_direction='db_to_file'"
            }
        }
    
    async def handle_legacy_call(self, tool_name: str, params: Dict) -> Dict[str, Any]:
        """Handle calls to legacy tools with automatic migration."""
        if tool_name not in self.migration_map:
            raise ValueError(f"Unknown legacy tool: {tool_name}")
        
        mapping = self.migration_map[tool_name]
        new_tool_name = mapping["new_tool"]
        new_params = mapping["parameter_mapping"](params)
        description = mapping["description"]
        
        # Log deprecation warning (only once per tool)
        if tool_name not in self.deprecation_warnings:
            logger.warning(
                f"DEPRECATED: Tool '{tool_name}' is deprecated. "
                f"{description}. "
                f"See migration guide for details."
            )
            self.deprecation_warnings.add(tool_name)
        
        # Call new tool
        new_tool = self.new_tools.get_tool(new_tool_name)
        if not new_tool:
            raise ValueError(f"New tool '{new_tool_name}' not found in registry")
        
        return await new_tool.handle_tool_call(new_tool_name, new_params)
    
    def get_migration_info(self, tool_name: str) -> Dict[str, str]:
        """Get migration information for a legacy tool."""
        if tool_name not in self.migration_map:
            return {"error": f"Tool '{tool_name}' is not a known legacy tool"}
        
        mapping = self.migration_map[tool_name]
        return {
            "legacy_tool": tool_name,
            "new_tool": mapping["new_tool"],
            "description": mapping["description"],
            "status": "deprecated"
        }
    
    def list_legacy_tools(self) -> List[Dict[str, str]]:
        """List all legacy tools and their migration paths."""
        return [
            {
                "legacy_tool": tool_name,
                "new_tool": mapping["new_tool"],
                "description": mapping["description"]
            }
            for tool_name, mapping in self.migration_map.items()
        ]
    
    def is_legacy_tool(self, tool_name: str) -> bool:
        """Check if a tool name is a legacy tool."""
        return tool_name in self.migration_map
    
    def get_consolidated_tools(self) -> List[str]:
        """Get list of new consolidated tool names."""
        consolidated_tools = set()
        for mapping in self.migration_map.values():
            consolidated_tools.add(mapping["new_tool"])
        return sorted(list(consolidated_tools))


class MigrationHelper:
    """Helper class for migration guidance and validation."""
    
    def __init__(self, compatibility_wrapper: BackwardCompatibilityWrapper):
        self.wrapper = compatibility_wrapper
    
    def generate_migration_guide(self) -> str:
        """Generate a comprehensive migration guide."""
        guide = "# MCP Tool Migration Guide\n\n"
        guide += "This guide helps you migrate from legacy tools to consolidated tools.\n\n"
        
        # Group by new tool
        tool_groups = {}
        for legacy_tool, mapping in self.wrapper.migration_map.items():
            new_tool = mapping["new_tool"]
            if new_tool not in tool_groups:
                tool_groups[new_tool] = []
            tool_groups[new_tool].append((legacy_tool, mapping["description"]))
        
        for new_tool, legacy_tools in tool_groups.items():
            guide += f"## {new_tool}\n\n"
            guide += f"Replaces {len(legacy_tools)} legacy tools:\n\n"
            
            for legacy_tool, description in legacy_tools:
                guide += f"- **{legacy_tool}**: {description}\n"
            
            guide += "\n"
        
        guide += "## Migration Steps\n\n"
        guide += "1. Update tool calls to use new consolidated tools\n"
        guide += "2. Update parameter names and structures as needed\n"
        guide += "3. Test functionality with new tools\n"
        guide += "4. Remove references to legacy tools\n\n"
        
        guide += "## Backward Compatibility\n\n"
        guide += "Legacy tools will continue to work during the transition period "
        guide += "but will show deprecation warnings. Plan to migrate within 2 releases.\n"
        
        return guide
    
    def validate_migration(self, legacy_calls: List[Dict]) -> Dict[str, Any]:
        """Validate a set of legacy tool calls for migration readiness."""
        results = {
            "total_calls": len(legacy_calls),
            "migrable_calls": 0,
            "unknown_calls": 0,
            "migration_plan": [],
            "warnings": []
        }
        
        for call in legacy_calls:
            tool_name = call.get("tool_name")
            if not tool_name:
                results["warnings"].append("Call missing tool_name")
                continue
            
            if self.wrapper.is_legacy_tool(tool_name):
                results["migrable_calls"] += 1
                migration_info = self.wrapper.get_migration_info(tool_name)
                results["migration_plan"].append(migration_info)
            else:
                results["unknown_calls"] += 1
                results["warnings"].append(f"Unknown tool: {tool_name}")
        
        return results