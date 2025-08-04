"""Unified Hierarchy Tool for MCP Jive.

Consolidates hierarchy and dependency management operations:
- jive_get_work_item_children
- jive_get_work_item_dependencies
- jive_get_task_hierarchy
- jive_add_dependency
- jive_remove_dependency
- jive_validate_dependencies
"""

import logging
from typing import Dict, Any, List, Optional, Union
from ..base import BaseTool
from datetime import datetime
import uuid
try:
    from mcp.types import Tool
except ImportError:
    # Mock Tool type if MCP not available
    Tool = Dict[str, Any]

logger = logging.getLogger(__name__)


class UnifiedHierarchyTool(BaseTool):
    """Unified tool for hierarchy and dependency operations."""
    
    def __init__(self, storage=None):
        super().__init__()
        self.storage = storage
        self.tool_name = "jive_get_hierarchy"
    
    @property
    def name(self) -> str:
        """Tool name identifier."""
        return self.tool_name
    
    @property
    def description(self) -> str:
        """Tool description for AI agents."""
        return "Unified tool for hierarchy and dependency operations. Retrieves parent-child relationships, dependencies, and full hierarchies."
    
    @property
    def category(self):
        """Tool category."""
        from ..base import ToolCategory
        return ToolCategory.HIERARCHY_MANAGEMENT
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        """Parameters schema for the tool."""
        return {
            "work_item_id": {
                "type": "string",
                "description": "Work item ID (UUID, exact title, or keywords)"
            },
            "relationship_type": {
                "type": "string",
                "enum": ["children", "parents", "dependencies", "dependents", "full_hierarchy"],
                "description": "Type of relationship to retrieve"
            },
            "action": {
                "type": "string",
                "enum": ["get", "add_dependency", "remove_dependency", "validate"],
                "description": "Action to perform"
            }
        }
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool with given parameters."""
        action = kwargs.get("action", "get")
        work_item_id = kwargs.get("work_item_id")
        relationship_type = kwargs.get("relationship_type")
        
        if action == "get":
            return await self._get_relationships(work_item_id, relationship_type, **kwargs)
        elif action == "add_dependency":
            return await self._add_dependency(**kwargs)
        elif action == "remove_dependency":
            return await self._remove_dependency(**kwargs)
        elif action == "validate":
            return await self._validate_dependencies(**kwargs)
        else:
            return {
                "success": False,
                "error": f"Invalid action: {action}"
            }
    
    async def get_tools(self) -> List[Tool]:
        """Get the unified hierarchy management tool."""
        return [
            Tool(
                name="jive_get_hierarchy",
                description="Unified tool for hierarchy and dependency operations. Retrieves parent-child relationships, dependencies, and full hierarchies.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "work_item_id": {
                            "type": "string",
                            "description": "Work item ID (UUID, exact title, or keywords)"
                        },
                        "relationship_type": {
                            "type": "string",
                            "enum": ["children", "parents", "dependencies", "dependents", "full_hierarchy"],
                            "description": "Type of relationship to retrieve"
                        },
                        "action": {
                            "type": "string",
                            "enum": ["get", "add_dependency", "remove_dependency", "validate"],
                            "description": "Action to perform"
                        }
                    },
                    "required": ["work_item_id"]
                }
            )
        ]
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool schema."""
        return {
            "type": "function",
            "function": {
                "name": self.tool_name,
                "description": (
                    "Unified tool for hierarchy and dependency operations. "
                    "Retrieves parent-child relationships, dependencies, and full hierarchies. "
                    "Can also manage dependencies and validate hierarchy structures."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "work_item_id": {
                            "type": "string",
                            "description": "Work item ID (UUID, exact title, or keywords)"
                        },
                        "relationship_type": {
                            "type": "string",
                            "enum": [
                                "children", "parents", "dependencies", "dependents",
                                "full_hierarchy", "ancestors", "descendants"
                            ],
                            "description": "Type of relationship to retrieve"
                        },
                        "action": {
                            "type": "string",
                            "enum": ["get", "add_dependency", "remove_dependency", "validate"],
                            "default": "get",
                            "description": "Action to perform (get relationships or manage dependencies)"
                        },
                        "target_work_item_id": {
                            "type": "string",
                            "description": "Target work item ID for dependency operations"
                        },
                        "dependency_type": {
                            "type": "string",
                            "enum": ["blocks", "blocked_by", "related", "subtask_of"],
                            "default": "blocks",
                            "description": "Type of dependency relationship"
                        },
                        "max_depth": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 10,
                            "default": 5,
                            "description": "Maximum depth for hierarchy traversal"
                        },
                        "include_completed": {
                            "type": "boolean",
                            "default": True,
                            "description": "Include completed work items in results"
                        },
                        "include_cancelled": {
                            "type": "boolean",
                            "default": False,
                            "description": "Include cancelled work items in results"
                        },
                        "include_metadata": {
                            "type": "boolean",
                            "default": True,
                            "description": "Include metadata like progress, effort estimates"
                        },
                        "validation_options": {
                            "type": "object",
                            "properties": {
                                "check_circular": {
                                    "type": "boolean",
                                    "default": True,
                                    "description": "Check for circular dependencies"
                                },
                                "check_missing": {
                                    "type": "boolean",
                                    "default": True,
                                    "description": "Check for missing dependencies"
                                },
                                "check_orphans": {
                                    "type": "boolean",
                                    "default": False,
                                    "description": "Check for orphaned work items"
                                }
                            },
                            "description": "Options for dependency validation"
                        }
                    },
                    "required": ["work_item_id", "relationship_type"]
                }
            }
        }
    
    async def handle_tool_call(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle the unified hierarchy tool call."""
        try:
            work_item_id = params["work_item_id"]
            relationship_type = params["relationship_type"]
            action = params.get("action", "get")
            
            # Resolve work item ID
            resolved_id = await self._resolve_work_item_id(work_item_id)
            if not resolved_id:
                return {
                    "success": False,
                    "error": f"Work item not found: {work_item_id}",
                    "error_code": "WORK_ITEM_NOT_FOUND"
                }
            
            if action == "get":
                return await self._get_relationships(resolved_id, relationship_type, params)
            elif action == "add_dependency":
                return await self._add_dependency(resolved_id, params)
            elif action == "remove_dependency":
                return await self._remove_dependency(resolved_id, params)
            elif action == "validate":
                return await self._validate_dependencies(resolved_id, params)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "error_code": "INVALID_ACTION"
                }
        
        except Exception as e:
            logger.error(f"Error in unified hierarchy tool: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "HIERARCHY_ERROR"
            }
    
    async def _resolve_work_item_id(self, work_item_id: str) -> Optional[str]:
        """Resolve work item ID from UUID, title, or keywords."""
        # Try UUID first
        if validate_uuid(work_item_id):
            if await validate_work_item_exists(work_item_id, self.storage):
                return work_item_id
        
        # Try exact title match
        work_items = await self.storage.list_work_items()
        for item in work_items:
            if item.title.lower() == work_item_id.lower():
                return item.id
        
        # Try keyword search
        keywords = work_item_id.lower().split()
        for item in work_items:
            item_text = f"{item.title} {item.description or ''}".lower()
            if all(keyword in item_text for keyword in keywords):
                return item.id
        
        return None
    
    async def _get_relationships(self, work_item_id: str, relationship_type: str, params: Dict) -> Dict[str, Any]:
        """Get relationships for a work item."""
        max_depth = params.get("max_depth", 5)
        include_completed = params.get("include_completed", True)
        include_cancelled = params.get("include_cancelled", False)
        include_metadata = params.get("include_metadata", True)
        
        work_item = await self.storage.get_work_item(work_item_id)
        if not work_item:
            return {
                "success": False,
                "error": f"Work item not found: {work_item_id}",
                "error_code": "WORK_ITEM_NOT_FOUND"
            }
        
        result = {
            "success": True,
            "work_item_id": work_item_id,
            "relationship_type": relationship_type,
            "relationships": [],
            "metadata": {
                "total_count": 0,
                "max_depth_reached": False,
                "traversal_stats": {}
            }
        }
        
        if relationship_type == "children":
            result["relationships"] = await self._get_children(
                work_item_id, include_completed, include_cancelled, include_metadata
            )
        elif relationship_type == "parents":
            result["relationships"] = await self._get_parents(
                work_item_id, include_completed, include_cancelled, include_metadata
            )
        elif relationship_type == "dependencies":
            result["relationships"] = await self._get_dependencies(
                work_item_id, include_completed, include_cancelled, include_metadata
            )
        elif relationship_type == "dependents":
            result["relationships"] = await self._get_dependents(
                work_item_id, include_completed, include_cancelled, include_metadata
            )
        elif relationship_type == "full_hierarchy":
            result["relationships"] = await self._get_full_hierarchy(
                work_item_id, max_depth, include_completed, include_cancelled, include_metadata
            )
        elif relationship_type == "ancestors":
            result["relationships"] = await self._get_ancestors(
                work_item_id, max_depth, include_completed, include_cancelled, include_metadata
            )
        elif relationship_type == "descendants":
            result["relationships"] = await self._get_descendants(
                work_item_id, max_depth, include_completed, include_cancelled, include_metadata
            )
        
        result["metadata"]["total_count"] = len(result["relationships"])
        return result
    
    async def _get_children(self, work_item_id: str, include_completed: bool, 
                           include_cancelled: bool, include_metadata: bool) -> List[Dict]:
        """Get direct children of a work item."""
        all_items = await self.storage.list_work_items()
        children = []
        
        for item in all_items:
            if item.parent_id == work_item_id:
                if not include_completed and item.status == "completed":
                    continue
                if not include_cancelled and item.status == "cancelled":
                    continue
                
                child_data = {
                    "id": item.id,
                    "title": item.title,
                    "type": item.type,
                    "status": item.status,
                    "priority": item.priority
                }
                
                if include_metadata:
                    child_data.update({
                        "description": item.description,
                        "tags": item.tags,
                        "created_at": item.created_at.isoformat() if item.created_at else None,
                        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
                        "effort_estimate": getattr(item, "effort_estimate", None),
                        "progress_percentage": getattr(item, "progress_percentage", 0)
                    })
                
                children.append(child_data)
        
        return children
    
    async def _get_parents(self, work_item_id: str, include_completed: bool,
                          include_cancelled: bool, include_metadata: bool) -> List[Dict]:
        """Get parent chain of a work item."""
        work_item = await self.storage.get_work_item(work_item_id)
        parents = []
        
        current_item = work_item
        while current_item and current_item.parent_id:
            parent = await self.storage.get_work_item(current_item.parent_id)
            if not parent:
                break
            
            if not include_completed and parent.status == "completed":
                break
            if not include_cancelled and parent.status == "cancelled":
                break
            
            parent_data = {
                "id": parent.id,
                "title": parent.title,
                "type": parent.type,
                "status": parent.status,
                "priority": parent.priority,
                "level": len(parents) + 1
            }
            
            if include_metadata:
                parent_data.update({
                    "description": parent.description,
                    "tags": parent.tags,
                    "created_at": parent.created_at.isoformat() if parent.created_at else None,
                    "updated_at": parent.updated_at.isoformat() if parent.updated_at else None
                })
            
            parents.append(parent_data)
            current_item = parent
        
        return parents
    
    async def _get_dependencies(self, work_item_id: str, include_completed: bool,
                               include_cancelled: bool, include_metadata: bool) -> List[Dict]:
        """Get dependencies of a work item."""
        work_item = await self.storage.get_work_item(work_item_id)
        dependencies = []
        
        if hasattr(work_item, "dependencies") and work_item.dependencies:
            for dep_id in work_item.dependencies:
                dep_item = await self.storage.get_work_item(dep_id)
                if not dep_item:
                    continue
                
                if not include_completed and dep_item.status == "completed":
                    continue
                if not include_cancelled and dep_item.status == "cancelled":
                    continue
                
                dep_data = {
                    "id": dep_item.id,
                    "title": dep_item.title,
                    "type": dep_item.type,
                    "status": dep_item.status,
                    "priority": dep_item.priority,
                    "dependency_type": "blocks"
                }
                
                if include_metadata:
                    dep_data.update({
                        "description": dep_item.description,
                        "tags": dep_item.tags,
                        "progress_percentage": getattr(dep_item, "progress_percentage", 0)
                    })
                
                dependencies.append(dep_data)
        
        return dependencies
    
    async def _get_dependents(self, work_item_id: str, include_completed: bool,
                             include_cancelled: bool, include_metadata: bool) -> List[Dict]:
        """Get work items that depend on this work item."""
        all_items = await self.storage.list_work_items()
        dependents = []
        
        for item in all_items:
            if hasattr(item, "dependencies") and item.dependencies:
                if work_item_id in item.dependencies:
                    if not include_completed and item.status == "completed":
                        continue
                    if not include_cancelled and item.status == "cancelled":
                        continue
                    
                    dep_data = {
                        "id": item.id,
                        "title": item.title,
                        "type": item.type,
                        "status": item.status,
                        "priority": item.priority,
                        "dependency_type": "blocked_by"
                    }
                    
                    if include_metadata:
                        dep_data.update({
                            "description": item.description,
                            "tags": item.tags,
                            "progress_percentage": getattr(item, "progress_percentage", 0)
                        })
                    
                    dependents.append(dep_data)
        
        return dependents
    
    async def _get_full_hierarchy(self, work_item_id: str, max_depth: int,
                                 include_completed: bool, include_cancelled: bool,
                                 include_metadata: bool) -> List[Dict]:
        """Get full hierarchy tree starting from work item."""
        hierarchy = []
        visited = set()
        
        async def traverse_hierarchy(item_id: str, current_depth: int, parent_path: List[str]):
            if current_depth > max_depth or item_id in visited:
                return
            
            visited.add(item_id)
            item = await self.storage.get_work_item(item_id)
            if not item:
                return
            
            if not include_completed and item.status == "completed":
                return
            if not include_cancelled and item.status == "cancelled":
                return
            
            item_data = {
                "id": item.id,
                "title": item.title,
                "type": item.type,
                "status": item.status,
                "priority": item.priority,
                "depth": current_depth,
                "path": parent_path + [item_id],
                "children": []
            }
            
            if include_metadata:
                item_data.update({
                    "description": item.description,
                    "tags": item.tags,
                    "progress_percentage": getattr(item, "progress_percentage", 0)
                })
            
            # Get children
            children = await self._get_children(item_id, include_completed, include_cancelled, False)
            for child in children:
                child_hierarchy = await traverse_hierarchy(
                    child["id"], current_depth + 1, parent_path + [item_id]
                )
                if child_hierarchy:
                    item_data["children"].append(child_hierarchy)
            
            return item_data
        
        root_hierarchy = await traverse_hierarchy(work_item_id, 0, [])
        if root_hierarchy:
            hierarchy.append(root_hierarchy)
        
        return hierarchy
    
    async def _get_ancestors(self, work_item_id: str, max_depth: int,
                            include_completed: bool, include_cancelled: bool,
                            include_metadata: bool) -> List[Dict]:
        """Get all ancestors up to max_depth."""
        return await self._get_parents(work_item_id, include_completed, include_cancelled, include_metadata)
    
    async def _get_descendants(self, work_item_id: str, max_depth: int,
                              include_completed: bool, include_cancelled: bool,
                              include_metadata: bool) -> List[Dict]:
        """Get all descendants up to max_depth."""
        descendants = []
        visited = set()
        
        async def traverse_descendants(item_id: str, current_depth: int):
            if current_depth >= max_depth or item_id in visited:
                return
            
            visited.add(item_id)
            children = await self._get_children(item_id, include_completed, include_cancelled, include_metadata)
            
            for child in children:
                child["depth"] = current_depth + 1
                descendants.append(child)
                await traverse_descendants(child["id"], current_depth + 1)
        
        await traverse_descendants(work_item_id, 0)
        return descendants
    
    async def _add_dependency(self, work_item_id: str, params: Dict) -> Dict[str, Any]:
        """Add a dependency relationship."""
        target_id = params.get("target_work_item_id")
        dependency_type = params.get("dependency_type", "blocks")
        
        if not target_id:
            return {
                "success": False,
                "error": "target_work_item_id is required for add_dependency action",
                "error_code": "MISSING_TARGET"
            }
        
        # Resolve target ID
        resolved_target_id = await self._resolve_work_item_id(target_id)
        if not resolved_target_id:
            return {
                "success": False,
                "error": f"Target work item not found: {target_id}",
                "error_code": "TARGET_NOT_FOUND"
            }
        
        # Check for circular dependency
        if await self._would_create_circular_dependency(work_item_id, resolved_target_id):
            return {
                "success": False,
                "error": "Adding this dependency would create a circular dependency",
                "error_code": "CIRCULAR_DEPENDENCY"
            }
        
        # Add dependency
        work_item = await self.storage.get_work_item(work_item_id)
        if not hasattr(work_item, "dependencies"):
            work_item.dependencies = []
        
        if resolved_target_id not in work_item.dependencies:
            work_item.dependencies.append(resolved_target_id)
            await self.storage.update_work_item(work_item_id, {"dependencies": work_item.dependencies})
        
        return {
            "success": True,
            "message": f"Dependency added: {work_item_id} depends on {resolved_target_id}",
            "dependency": {
                "source_id": work_item_id,
                "target_id": resolved_target_id,
                "type": dependency_type
            }
        }
    
    async def _remove_dependency(self, work_item_id: str, params: Dict) -> Dict[str, Any]:
        """Remove a dependency relationship."""
        target_id = params.get("target_work_item_id")
        
        if not target_id:
            return {
                "success": False,
                "error": "target_work_item_id is required for remove_dependency action",
                "error_code": "MISSING_TARGET"
            }
        
        # Resolve target ID
        resolved_target_id = await self._resolve_work_item_id(target_id)
        if not resolved_target_id:
            return {
                "success": False,
                "error": f"Target work item not found: {target_id}",
                "error_code": "TARGET_NOT_FOUND"
            }
        
        # Remove dependency
        work_item = await self.storage.get_work_item(work_item_id)
        if hasattr(work_item, "dependencies") and work_item.dependencies:
            if resolved_target_id in work_item.dependencies:
                work_item.dependencies.remove(resolved_target_id)
                await self.storage.update_work_item(work_item_id, {"dependencies": work_item.dependencies})
                
                return {
                    "success": True,
                    "message": f"Dependency removed: {work_item_id} no longer depends on {resolved_target_id}"
                }
        
        return {
            "success": False,
            "error": f"Dependency not found: {work_item_id} -> {resolved_target_id}",
            "error_code": "DEPENDENCY_NOT_FOUND"
        }
    
    async def _validate_dependencies(self, work_item_id: str, params: Dict) -> Dict[str, Any]:
        """Validate dependency structure."""
        validation_options = params.get("validation_options", {})
        check_circular = validation_options.get("check_circular", True)
        check_missing = validation_options.get("check_missing", True)
        check_orphans = validation_options.get("check_orphans", False)
        
        validation_results = {
            "success": True,
            "work_item_id": work_item_id,
            "validation_summary": {
                "total_issues": 0,
                "circular_dependencies": 0,
                "missing_dependencies": 0,
                "orphaned_items": 0
            },
            "issues": []
        }
        
        if check_circular:
            circular_issues = await self._check_circular_dependencies(work_item_id)
            validation_results["issues"].extend(circular_issues)
            validation_results["validation_summary"]["circular_dependencies"] = len(circular_issues)
        
        if check_missing:
            missing_issues = await self._check_missing_dependencies(work_item_id)
            validation_results["issues"].extend(missing_issues)
            validation_results["validation_summary"]["missing_dependencies"] = len(missing_issues)
        
        if check_orphans:
            orphan_issues = await self._check_orphaned_items()
            validation_results["issues"].extend(orphan_issues)
            validation_results["validation_summary"]["orphaned_items"] = len(orphan_issues)
        
        validation_results["validation_summary"]["total_issues"] = len(validation_results["issues"])
        validation_results["success"] = validation_results["validation_summary"]["total_issues"] == 0
        
        return validation_results
    
    async def _would_create_circular_dependency(self, source_id: str, target_id: str) -> bool:
        """Check if adding a dependency would create a circular dependency."""
        visited = set()
        
        async def has_path_to_source(current_id: str) -> bool:
            if current_id == source_id:
                return True
            if current_id in visited:
                return False
            
            visited.add(current_id)
            current_item = await self.storage.get_work_item(current_id)
            
            if hasattr(current_item, "dependencies") and current_item.dependencies:
                for dep_id in current_item.dependencies:
                    if await has_path_to_source(dep_id):
                        return True
            
            return False
        
        return await has_path_to_source(target_id)
    
    async def _check_circular_dependencies(self, work_item_id: str) -> List[Dict]:
        """Check for circular dependencies."""
        issues = []
        visited = set()
        path = []
        
        async def detect_cycle(current_id: str):
            if current_id in path:
                cycle_start = path.index(current_id)
                cycle = path[cycle_start:] + [current_id]
                issues.append({
                    "type": "circular_dependency",
                    "severity": "error",
                    "message": f"Circular dependency detected: {' -> '.join(cycle)}",
                    "cycle": cycle
                })
                return
            
            if current_id in visited:
                return
            
            visited.add(current_id)
            path.append(current_id)
            
            current_item = await self.storage.get_work_item(current_id)
            if hasattr(current_item, "dependencies") and current_item.dependencies:
                for dep_id in current_item.dependencies:
                    await detect_cycle(dep_id)
            
            path.pop()
        
        await detect_cycle(work_item_id)
        return issues
    
    async def _check_missing_dependencies(self, work_item_id: str) -> List[Dict]:
        """Check for missing dependencies."""
        issues = []
        work_item = await self.storage.get_work_item(work_item_id)
        
        if hasattr(work_item, "dependencies") and work_item.dependencies:
            for dep_id in work_item.dependencies:
                dep_item = await self.storage.get_work_item(dep_id)
                if not dep_item:
                    issues.append({
                        "type": "missing_dependency",
                        "severity": "error",
                        "message": f"Missing dependency: {dep_id} referenced by {work_item_id}",
                        "missing_id": dep_id,
                        "referencing_id": work_item_id
                    })
        
        return issues
    
    async def _check_orphaned_items(self) -> List[Dict]:
        """Check for orphaned work items."""
        issues = []
        all_items = await self.storage.list_work_items()
        
        # Find items without parents or dependencies
        for item in all_items:
            has_parent = bool(item.parent_id)
            has_dependencies = bool(getattr(item, "dependencies", []))
            is_referenced = False
            
            # Check if this item is referenced by others
            for other_item in all_items:
                if other_item.id != item.id:
                    if (other_item.parent_id == item.id or 
                        (hasattr(other_item, "dependencies") and 
                         other_item.dependencies and 
                         item.id in other_item.dependencies)):
                        is_referenced = True
                        break
            
            if not has_parent and not has_dependencies and not is_referenced:
                issues.append({
                    "type": "orphaned_item",
                    "severity": "warning",
                    "message": f"Orphaned work item: {item.id} ({item.title})",
                    "item_id": item.id,
                    "item_title": item.title
                })
        
        return issues


# Export the tool
HIERARCHY_TOOLS = [UnifiedHierarchyTool]