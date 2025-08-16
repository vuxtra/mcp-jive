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
from ..base import BaseTool, ToolResult
from datetime import datetime
import uuid
from collections import defaultdict
from ...uuid_utils import validate_uuid, validate_work_item_exists
try:
    from mcp.types import Tool
except ImportError:
    # Mock Tool type if MCP not available
    Tool = Dict[str, Any]

logger = logging.getLogger(__name__)


class HierarchyValidator:
    """Comprehensive hierarchy validation and orphan detection."""
    
    def __init__(self, storage):
        self.storage = storage
        self.logger = logging.getLogger(__name__)
    
    async def validate_hierarchy(self, root_id: str = None) -> Dict[str, Any]:
        """Perform comprehensive hierarchy validation."""
        validation_results = {
            'is_valid': True,
            'orphaned_items': [],
            'circular_references': [],
            'invalid_references': [],
            'depth_violations': [],
            'summary': {}
        }
        
        # Get all work items
        all_items = await self.storage.list_work_items()
        
        # Check for orphaned items
        orphaned = await self._find_orphaned_items(all_items, root_id)
        validation_results['orphaned_items'] = orphaned
        
        # Check for circular references
        circular = await self._find_circular_references(all_items)
        validation_results['circular_references'] = circular
        
        # Check for invalid parent references
        invalid_refs = await self._find_invalid_references(all_items)
        validation_results['invalid_references'] = invalid_refs
        
        # Check depth violations
        depth_violations = await self._find_depth_violations(all_items)
        validation_results['depth_violations'] = depth_violations
        
        # Determine overall validity
        validation_results['is_valid'] = (
            len(orphaned) == 0 and 
            len(circular) == 0 and 
            len(invalid_refs) == 0 and
            len(depth_violations) == 0
        )
        
        # Generate summary
        validation_results['summary'] = self._generate_validation_summary(
            validation_results
        )
        
        return validation_results
    
    async def _find_orphaned_items(self, all_items: List[Dict[str, Any]], 
                                   root_id: str = None) -> List[Dict[str, Any]]:
        """Find items that have no valid parent or root connection."""
        orphaned_items = []
        
        # Build parent-child mapping
        parent_map = {}
        child_map = defaultdict(list)
        
        for item in all_items:
            if not item:  # Skip None items
                continue
                
            item_id = item.get('id')
            parent_id = item.get('parent_id')
            
            if parent_id:
                parent_map[item_id] = parent_id
                child_map[parent_id].append(item_id)
        
        # Find items with no path to root
        for item in all_items:
            if not item:  # Skip None items
                continue
                
            item_id = item.get('id')
            
            # Skip if this is a root item
            if not item.get('parent_id'):
                continue
            
            # Check if there's a valid path to root
            if not await self._has_path_to_root(item_id, parent_map, root_id):
                orphaned_items.append({
                    'id': item_id,
                    'title': item.get('title', ''),
                    'parent_id': item.get('parent_id'),
                    'reason': 'No valid path to root'
                })
        
        return orphaned_items
    
    async def _has_path_to_root(self, item_id: str, parent_map: Dict[str, str], 
                                root_id: str = None) -> bool:
        """Check if an item has a valid path to root."""
        visited = set()
        current_id = item_id
        
        while current_id and current_id not in visited:
            visited.add(current_id)
            
            # If we reach the specified root, path is valid
            if root_id and current_id == root_id:
                return True
            
            # If no parent, check if this is a valid root
            parent_id = parent_map.get(current_id)
            if not parent_id:
                # If no specific root specified, any parentless item is valid
                return root_id is None
            
            # Check if parent exists
            parent_item = await self.storage.get_work_item(parent_id)
            if not parent_item:
                return False
            
            current_id = parent_id
        
        # If we hit a cycle or couldn't reach root
        return False
    
    async def _find_circular_references(self, all_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find circular references in the hierarchy."""
        circular_refs = []
        visited_global = set()
        
        for item in all_items:
            if not item:  # Skip None items
                continue
                
            item_id = item.get('id')
            if item_id in visited_global:
                continue
            
            # Detect cycles starting from this item
            cycle = await self._detect_cycle_from_item(item_id, all_items)
            if cycle:
                circular_refs.append({
                    'cycle': cycle,
                    'severity': 'error',
                    'message': f'Circular reference detected: {"->".join(cycle)}'
                })
                # Mark all items in cycle as visited
                visited_global.update(cycle)
        
        return circular_refs
    
    async def _detect_cycle_from_item(self, start_id: str, all_items: List[Dict[str, Any]]) -> Optional[List[str]]:
        """Detect cycle starting from a specific item."""
        visited = set()
        path = []
        
        async def dfs(current_id: str) -> Optional[List[str]]:
            if current_id in path:
                # Found cycle - return the cycle portion
                cycle_start = path.index(current_id)
                return path[cycle_start:] + [current_id]
            
            if current_id in visited:
                return None
            
            visited.add(current_id)
            path.append(current_id)
            
            # Get current item
            current_item = await self.storage.get_work_item(current_id)
            if not current_item:
                path.pop()
                return None
            
            # Check parent relationship
            parent_id = current_item.get('parent_id')
            if parent_id:
                cycle = await dfs(parent_id)
                if cycle:
                    path.pop()
                    return cycle
            
            # Check dependencies
            dependencies = current_item.get('dependencies', [])
            if dependencies:
                for dep_id in dependencies:
                    cycle = await dfs(dep_id)
                    if cycle:
                        path.pop()
                        return cycle
            
            path.pop()
            return None
        
        return await dfs(start_id)
    
    async def _find_invalid_references(self, all_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find invalid parent or dependency references."""
        invalid_refs = []
        valid_ids = {item.get('id') for item in all_items if item and item.get('id')}
        
        for item in all_items:
            if not item:  # Skip None items
                continue
                
            item_id = item.get('id')
            item_title = item.get('title', '')
            
            # Check parent reference
            parent_id = item.get('parent_id')
            if parent_id and parent_id not in valid_ids:
                invalid_refs.append({
                    'type': 'invalid_parent',
                    'item_id': item_id,
                    'item_title': item_title,
                    'invalid_reference': parent_id,
                    'severity': 'error',
                    'message': f'Item {item_id} references non-existent parent {parent_id}'
                })
            
            # Check dependency references
            dependencies = item.get('dependencies', [])
            if dependencies:
                for dep_id in dependencies:
                    if dep_id not in valid_ids:
                        invalid_refs.append({
                            'type': 'invalid_dependency',
                            'item_id': item_id,
                            'item_title': item_title,
                            'invalid_reference': dep_id,
                            'severity': 'error',
                            'message': f'Item {item_id} references non-existent dependency {dep_id}'
                        })
        
        return invalid_refs
    
    async def _find_depth_violations(self, all_items: List[Dict[str, Any]], 
                                     max_depth: int = 10) -> List[Dict[str, Any]]:
        """Find items that exceed maximum hierarchy depth."""
        depth_violations = []
        
        for item in all_items:
            if not item:  # Skip None items
                continue
                
            item_id = item.get('id')
            depth = await self._calculate_item_depth(item_id)
            
            if depth > max_depth:
                depth_violations.append({
                    'item_id': item_id,
                    'item_title': item.get('title', ''),
                    'depth': depth,
                    'max_allowed': max_depth,
                    'severity': 'warning',
                    'message': f'Item {item_id} exceeds maximum depth ({depth} > {max_depth})'
                })
        
        return depth_violations
    
    async def _calculate_item_depth(self, item_id: str) -> int:
        """Calculate the depth of an item in the hierarchy."""
        depth = 0
        current_id = item_id
        visited = set()
        
        while current_id and current_id not in visited:
            visited.add(current_id)
            current_item = await self.storage.get_work_item(current_id)
            
            if not current_item:
                break
            
            parent_id = current_item.get('parent_id')
            if not parent_id:
                break
            
            depth += 1
            current_id = parent_id
        
        return depth
    
    def _generate_validation_summary(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of validation results."""
        return {
            'total_orphaned_items': len(validation_results['orphaned_items']),
            'total_circular_references': len(validation_results['circular_references']),
            'total_invalid_references': len(validation_results['invalid_references']),
            'total_depth_violations': len(validation_results['depth_violations']),
            'overall_health': 'healthy' if validation_results['is_valid'] else 'issues_found',
            'validation_timestamp': datetime.now().isoformat()
        }
    
    async def cleanup_orphaned_items(self, orphaned_items: List[Dict[str, Any]], 
                                     action: str = 'move_to_root') -> Dict[str, Any]:
        """Clean up orphaned items based on specified action."""
        cleanup_results = {
            'success': True,
            'processed_items': [],
            'errors': []
        }
        
        for orphan in orphaned_items:
            try:
                if action == 'move_to_root':
                    # Move orphan to root level
                    await self.storage.update_work_item(orphan['id'], {
                        'parent_id': None,
                        'cleanup_reason': 'Moved from orphaned state',
                        'cleanup_timestamp': datetime.now().isoformat()
                    })
                
                elif action == 'delete':
                    # Delete orphaned item
                    await self.storage.delete_work_item(orphan['id'])
                
                elif action == 'assign_parent':
                    # Assign to a default parent (requires parent_id in action_params)
                    default_parent = orphan.get('suggested_parent_id')
                    if default_parent:
                        await self.storage.update_work_item(orphan['id'], {
                            'parent_id': default_parent,
                            'cleanup_reason': 'Assigned to suggested parent',
                            'cleanup_timestamp': datetime.now().isoformat()
                        })
                
                cleanup_results['processed_items'].append(orphan['id'])
                
            except Exception as e:
                cleanup_results['errors'].append({
                    'item_id': orphan['id'],
                    'error': str(e)
                })
                cleanup_results['success'] = False
        
        return cleanup_results


class UnifiedHierarchyTool(BaseTool):
    """Unified tool for hierarchy and dependency operations."""
    
    def __init__(self, storage=None):
        super().__init__()
        self.storage = storage
        self.tool_name = "jive_get_hierarchy"
        self.hierarchy_validator = HierarchyValidator(storage) if storage else None
    
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
                "enum": ["get", "add_dependency", "remove_dependency", "validate", "validate_comprehensive", "cleanup_orphans", "get_children", "create_relationship", "get_dependencies"],
                "description": "Action to perform"
            },
            "cleanup_action": {
                "type": "string",
                "enum": ["move_to_root", "delete", "assign_parent"],
                "description": "Action to take when cleaning up orphaned items",
                "default": "move_to_root"
            },
            "root_id": {
                "type": "string",
                "description": "Root item ID for comprehensive validation"
            }
        }
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters."""
        try:
            action = kwargs.get("action", "get")
            work_item_id = kwargs.get("work_item_id")
            relationship_type = kwargs.get("relationship_type")
            
            if action == "get":
                result = await self._get_relationships(work_item_id, relationship_type, kwargs)
                return ToolResult(
                    success=result.get("success", False),
                    data=result.get("data"),
                    message=result.get("message"),
                    error=result.get("error"),
                    metadata=result.get("metadata")
                )
            elif action == "add_dependency":
                result = await self._add_dependency(work_item_id, kwargs)
                return ToolResult(
                    success=result.get("success", False),
                    data=result.get("data"),
                    message=result.get("message"),
                    error=result.get("error"),
                    metadata=result.get("metadata")
                )
            elif action == "remove_dependency":
                result = await self._remove_dependency(work_item_id, kwargs)
                return ToolResult(
                    success=result.get("success", False),
                    data=result.get("data"),
                    message=result.get("message"),
                    error=result.get("error"),
                    metadata=result.get("metadata")
                )
            elif action == "validate":
                result = await self._validate_dependencies(work_item_id, kwargs)
                return ToolResult(
                    success=result.get("success", False),
                    data=result.get("data"),
                    message=result.get("message"),
                    error=result.get("error"),
                    metadata=result.get("metadata")
                )
            elif action == "validate_comprehensive":
                result = await self._validate_comprehensive(work_item_id, kwargs)
                return ToolResult(
                    success=result.get("success", False),
                    data=result.get("data"),
                    message=result.get("message"),
                    error=result.get("error"),
                    metadata=result.get("metadata")
                )
            elif action == "cleanup_orphans":
                result = await self._cleanup_orphans(kwargs)
                return ToolResult(
                    success=result.get("success", False),
                    data=result.get("data"),
                    message=result.get("message"),
                    error=result.get("error"),
                    metadata=result.get("metadata")
                )
            elif action == "get_children":
                # Legacy support: get_children maps to get with relationship_type="children"
                kwargs["relationship_type"] = "children"
                result = await self._get_relationships(work_item_id, "children", kwargs)
                return ToolResult(
                    success=result.get("success", False),
                    data=result.get("data"),
                    message=result.get("message"),
                    error=result.get("error"),
                    metadata=result.get("metadata")
                )
            elif action == "get_dependencies":
                # Legacy support: get_dependencies maps to get with relationship_type="dependencies"
                kwargs["relationship_type"] = "dependencies"
                result = await self._get_relationships(work_item_id, "dependencies", kwargs)
                return ToolResult(
                    success=result.get("success", False),
                    data=result.get("data"),
                    message=result.get("message"),
                    error=result.get("error"),
                    metadata=result.get("metadata")
                )
            elif action == "create_relationship":
                # Legacy support: create_relationship maps to add_dependency
                # Handle legacy parameter names
                legacy_params = kwargs.copy()
                if "parent_id" in kwargs and "child_id" in kwargs:
                    # For parent-child relationships, parent is the work_item_id and child is target
                    legacy_params["target_work_item_id"] = kwargs["child_id"]
                    parent_id = kwargs["parent_id"]
                elif "child_id" in kwargs:
                    legacy_params["target_work_item_id"] = kwargs["child_id"]
                    parent_id = work_item_id
                else:
                    parent_id = work_item_id
                
                result = await self._add_dependency(parent_id, legacy_params)
                return ToolResult(
                    success=result.get("success", False),
                    data=result.get("data"),
                    message=result.get("message"),
                    error=result.get("error"),
                    metadata=result.get("metadata")
                )
            else:
                return ToolResult(
                    success=False,
                    error=f"Invalid action: {action}"
                )
        except Exception as e:
            logger.error(f"Error in unified hierarchy tool execute: {str(e)}")
            return ToolResult(
                success=False,
                error=str(e)
            )
    
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
                            "enum": ["get", "add_dependency", "remove_dependency", "validate", "validate_comprehensive", "cleanup_orphans"],
                            "description": "Action to perform"
                        },
                        "cleanup_action": {
                            "type": "string",
                            "enum": ["move_to_root", "delete", "assign_parent"],
                            "description": "Action to take when cleaning up orphaned items",
                            "default": "move_to_root"
                        },
                        "root_id": {
                            "type": "string",
                            "description": "Root item ID for comprehensive validation"
                        }
                    },
                    "required": ["work_item_id"]
                }
            )
        ]
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool schema for MCP registration."""
        return {
            "name": "jive_get_hierarchy",
            "description": "Jive: Unified hierarchy and dependency operations - retrieve relationships, manage dependencies, and validate hierarchy structures",
            "inputSchema": {
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
            item_title = item.get("title", "")
            if item_title.lower() == work_item_id.lower():
                return item.get("id")
        
        # Try keyword search
        keywords = work_item_id.lower().split()
        for item in work_items:
            item_title = item.get("title", "")
            item_description = item.get("description", "")
            item_text = f"{item_title} {item_description or ''}".lower()
            if all(keyword in item_text for keyword in keywords):
                return item.get("id")
        
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
            # Handle both dict and object formats
            parent_id = item.get('parent_id')
            status = item.get('status', 'not_started')
            
            if parent_id == work_item_id:
                if not include_completed and status == "completed":
                    continue
                if not include_cancelled and status == "cancelled":
                    continue
                
                item_id = item.get('id')
                title = item.get('title')
                item_type = item.get('item_type')
                priority = item.get('priority', 'medium')
                
                child_data = {
                    "id": item_id,
                    "title": title,
                    "type": item_type,
                    "status": status,
                    "priority": priority
                }
                
                if include_metadata:
                    description = item.get('description', '')
                    tags = item.get('tags', [])
                    created_at = item.get('created_at')
                    updated_at = item.get('updated_at')
                    effort_estimate = item.get('effort_estimate')
                    progress_percentage = item.get('progress', 0)
                    
                    child_data.update({
                        "description": description,
                        "tags": tags,
                        "created_at": created_at.isoformat() if hasattr(created_at, 'isoformat') else created_at,
                        "updated_at": updated_at.isoformat() if hasattr(updated_at, 'isoformat') else updated_at,
                        "effort_estimate": effort_estimate,
                        "progress_percentage": progress_percentage
                    })
                
                children.append(child_data)
        
        return children
    
    async def _get_parents(self, work_item_id: str, include_completed: bool,
                          include_cancelled: bool, include_metadata: bool) -> List[Dict]:
        """Get parent chain of a work item."""
        work_item = await self.storage.get_work_item(work_item_id)
        parents = []
        
        current_item = work_item
        while current_item:
            # Handle both dict and object formats
            parent_id = current_item.get('parent_id')
            if not parent_id:
                break
                
            parent = await self.storage.get_work_item(parent_id)
            if not parent:
                break
            
            # Handle parent status check
            parent_status = parent.get('status', 'not_started')
            if not include_completed and parent_status == "completed":
                break
            if not include_cancelled and parent_status == "cancelled":
                break
            
            # Extract parent data
            parent_id_val = parent.get('id')
            parent_title = parent.get('title')
            parent_type = parent.get('item_type')
            parent_priority = parent.get('priority', 'medium')
            
            parent_data = {
                "id": parent_id_val,
                "title": parent_title,
                "type": parent_type,
                "status": parent_status,
                "priority": parent_priority,
                "level": len(parents) + 1
            }
            
            if include_metadata:
                description = parent.get('description', '')
                tags = parent.get('tags', [])
                created_at = parent.get('created_at')
                updated_at = parent.get('updated_at')
                
                parent_data.update({
                    "description": description,
                    "tags": tags,
                    "created_at": created_at.isoformat() if hasattr(created_at, 'isoformat') else created_at,
                    "updated_at": updated_at.isoformat() if hasattr(updated_at, 'isoformat') else updated_at
                })
            
            parents.append(parent_data)
            current_item = parent
        
        return parents
    
    async def _get_dependencies(self, work_item_id: str, include_completed: bool,
                               include_cancelled: bool, include_metadata: bool) -> List[Dict]:
        """Get dependencies of a work item."""
        work_item = await self.storage.get_work_item(work_item_id)
        dependencies = []
        
        # Handle both dict and object formats for work_item
        work_item_deps = None
        if isinstance(work_item, dict):
            work_item_deps = work_item.get("dependencies")
        else:
            work_item_deps = work_item.get("dependencies")
            
        if work_item_deps:
            for dep_id in work_item_deps:
                dep_item = await self.storage.get_work_item(dep_id)
                if not dep_item:
                    continue
                
                # Handle dependency item status check
                dep_status = dep_item.get('status', 'not_started')
                if not include_completed and dep_status == "completed":
                    continue
                if not include_cancelled and dep_status == "cancelled":
                    continue
                
                # Extract dependency data
                dep_id_val = dep_item.get('id')
                dep_title = dep_item.get('title')
                dep_type = dep_item.get('item_type')
                dep_priority = dep_item.get('priority', 'medium')
                
                dep_data = {
                    "id": dep_id_val,
                    "title": dep_title,
                    "type": dep_type,
                    "status": dep_status,
                    "priority": dep_priority,
                    "dependency_type": "blocks"
                }
                
                if include_metadata:
                    description = dep_item.get('description', '')
                    tags = dep_item.get('tags', [])
                    progress_percentage = dep_item.get('progress', 0)
                    
                    dep_data.update({
                        "description": description,
                        "tags": tags,
                        "progress_percentage": progress_percentage
                    })
                
                dependencies.append(dep_data)
        
        return dependencies
    
    async def _get_dependents(self, work_item_id: str, include_completed: bool,
                             include_cancelled: bool, include_metadata: bool) -> List[Dict]:
        """Get work items that depend on this work item."""
        all_items = await self.storage.list_work_items()
        dependents = []
        
        for item in all_items:
            # Handle both dict and object formats for item
            item_deps = None
            if isinstance(item, dict):
                item_deps = item.get("dependencies")
            else:
                item_deps = item.get("dependencies")
                
            if item_deps and work_item_id in item_deps:
                # Handle item status check
                item_status = item.get('status', 'not_started')
                if not include_completed and item_status == "completed":
                    continue
                if not include_cancelled and item_status == "cancelled":
                    continue
                
                # Extract item data
                item_id = item.get('id')
                item_title = item.get('title')
                item_type = item.get('item_type')
                item_priority = item.get('priority', 'medium')
                
                dep_data = {
                    "id": item_id,
                    "title": item_title,
                    "type": item_type,
                    "status": item_status,
                    "priority": item_priority,
                    "dependency_type": "blocked_by"
                }
                
                if include_metadata:
                    description = item.get('description', '')
                    tags = item.get('tags', [])
                    progress_percentage = item.get('progress', 0)
                    
                    dep_data.update({
                        "description": description,
                        "tags": tags,
                        "progress_percentage": progress_percentage
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
            
            item_status = item.get("status", "not_started")
            if not include_completed and item_status == "completed":
                return
            if not include_cancelled and item_status == "cancelled":
                return
            
            item_data = {
                "id": item.get("id"),
                "title": item.get("title", ""),
                "type": item.get("type", ""),
                "status": item_status,
                "priority": item.get("priority", "medium"),
                "depth": current_depth,
                "path": parent_path + [item_id],
                "children": []
            }
            
            if include_metadata:
                item_data.update({
                    "description": item.get("description", ""),
                    "tags": item.get("tags", []),
                    "progress_percentage": item.get("progress", 0)
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
        if not work_item:
            return {
                "success": False,
                "error": f"Source work item not found: {work_item_id}",
                "error_code": "SOURCE_NOT_FOUND"
            }
        
        # Handle both dict and object formats for work_item
        if isinstance(work_item, dict):
            dependencies = work_item.get("dependencies", [])
            # Ensure dependencies is a Python list, not numpy array
            if hasattr(dependencies, 'tolist'):
                dependencies = dependencies.tolist()
            elif not isinstance(dependencies, list):
                try:
                    dependencies = list(dependencies) if dependencies is not None else []
                except Exception:
                    dependencies = []
            
            if resolved_target_id not in dependencies:
                dependencies.append(resolved_target_id)
                work_item["dependencies"] = dependencies
                await self.storage.update_work_item(work_item_id, {"dependencies": dependencies})
        else:
            dependencies = work_item.get("dependencies", [])
            # Ensure dependencies is a Python list, not numpy array
            if hasattr(dependencies, 'tolist'):
                dependencies = dependencies.tolist()
            elif not isinstance(dependencies, list):
                try:
                    dependencies = list(dependencies) if dependencies is not None else []
                except Exception:
                    dependencies = []
            
            if resolved_target_id not in dependencies:
                dependencies.append(resolved_target_id)
                work_item["dependencies"] = dependencies
                await self.storage.update_work_item(work_item_id, {"dependencies": dependencies})
        
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
        # Handle both dict and object formats for work_item
        if isinstance(work_item, dict):
            dependencies = work_item.get("dependencies", [])
            # Ensure dependencies is a Python list, not numpy array
            if hasattr(dependencies, 'tolist'):
                dependencies = dependencies.tolist()
            elif not isinstance(dependencies, list):
                dependencies = list(dependencies) if dependencies else []
            
            if resolved_target_id in dependencies:
                dependencies.remove(resolved_target_id)
                work_item["dependencies"] = dependencies
                await self.storage.update_work_item(work_item_id, {"dependencies": dependencies})
                
                return {
                    "success": True,
                    "message": f"Dependency removed: {work_item_id} no longer depends on {resolved_target_id}"
                }
        else:
            dependencies = work_item.get("dependencies", [])
            # Ensure dependencies is a Python list, not numpy array
            if hasattr(dependencies, 'tolist'):
                dependencies = dependencies.tolist()
            elif not isinstance(dependencies, list):
                dependencies = list(dependencies) if dependencies else []
            
            if resolved_target_id in dependencies:
                dependencies.remove(resolved_target_id)
                work_item["dependencies"] = dependencies
                await self.storage.update_work_item(work_item_id, {"dependencies": dependencies})
                
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
            
            # Handle both dict and object formats for current_item
            if isinstance(current_item, dict):
                dependencies = current_item.get("dependencies", [])
            else:
                dependencies = current_item.get("dependencies", [])
            
            if dependencies is not None and len(dependencies) > 0:
                for dep_id in dependencies:
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
            # Handle both dict and object formats for current_item
            if isinstance(current_item, dict):
                dependencies = current_item.get("dependencies", [])
            else:
                dependencies = current_item.get("dependencies", [])
            
            if dependencies is not None and len(dependencies) > 0:
                for dep_id in dependencies:
                    await detect_cycle(dep_id)
            
            path.pop()
        
        await detect_cycle(work_item_id)
        return issues
    
    async def _check_missing_dependencies(self, work_item_id: str) -> List[Dict]:
        """Check for missing dependencies."""
        issues = []
        work_item = await self.storage.get_work_item(work_item_id)
        
        # Handle both dict and object formats for work_item
        if isinstance(work_item, dict):
            dependencies = work_item.get("dependencies", [])
        else:
            dependencies = work_item.get("dependencies", [])
        
        if dependencies is not None and len(dependencies) > 0:
            for dep_id in dependencies:
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
            if not item:  # Skip None items
                continue
                
            parent_id = item.get("parent_id")
            has_parent = bool(parent_id)
            
            # Handle both dict and object formats for item
            if isinstance(item, dict):
                dependencies = item.get("dependencies", [])
            else:
                dependencies = item.get("dependencies", [])
            
            # Ensure dependencies is a list and not empty
            has_dependencies = bool(dependencies is not None and len(dependencies) > 0)
            is_referenced = False
            
            # Check if this item is referenced by others
            item_id = item.get("id")
            item_title = item.get("title", "")
            
            for other_item in all_items:
                other_item_id = other_item.get("id")
                other_item_parent_id = other_item.get("parent_id")
                
                if other_item_id != item_id:
                    # Handle both dict and object formats for other_item
                    if isinstance(other_item, dict):
                        other_dependencies = other_item.get("dependencies", [])
                    else:
                        other_dependencies = other_item.get("dependencies", [])
                    
                    if (other_item_parent_id == item_id or 
                        (other_dependencies and item_id in other_dependencies)):
                        is_referenced = True
                        break
            
            if not has_parent and not has_dependencies and not is_referenced:
                issues.append({
                    "type": "orphaned_item",
                    "severity": "warning",
                    "message": f"Orphaned work item: {item_id} ({item_title})",
                    "item_id": item_id,
                    "item_title": item_title
                })
        
        return issues
    
    async def _validate_comprehensive(self, work_item_id: str, params: Dict) -> Dict[str, Any]:
        """Perform comprehensive hierarchy validation using HierarchyValidator."""
        if not self.hierarchy_validator:
            return {
                "success": False,
                "error": "Hierarchy validator not initialized",
                "error_code": "VALIDATOR_NOT_AVAILABLE"
            }
        
        try:
            root_id = params.get("root_id")
            validation_results = await self.hierarchy_validator.validate_hierarchy(root_id)
            
            return {
                "success": validation_results['is_valid'],
                "data": validation_results,
                "message": f"Comprehensive validation completed. Found {validation_results['summary']['total_orphaned_items']} orphaned items, {validation_results['summary']['total_circular_references']} circular references, {validation_results['summary']['total_invalid_references']} invalid references, and {validation_results['summary']['total_depth_violations']} depth violations.",
                "metadata": {
                    "validation_type": "comprehensive",
                    "root_id": root_id,
                    "timestamp": validation_results['summary']['validation_timestamp']
                }
            }
        except Exception as e:
            logger.error(f"Error in comprehensive validation: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "COMPREHENSIVE_VALIDATION_ERROR"
            }
    
    async def _cleanup_orphans(self, params: Dict) -> Dict[str, Any]:
        """Clean up orphaned items using HierarchyValidator."""
        if not self.hierarchy_validator:
            return {
                "success": False,
                "error": "Hierarchy validator not initialized",
                "error_code": "VALIDATOR_NOT_AVAILABLE"
            }
        
        try:
            # First, find orphaned items
            root_id = params.get("root_id")
            validation_results = await self.hierarchy_validator.validate_hierarchy(root_id)
            orphaned_items = validation_results['orphaned_items']
            
            if not orphaned_items:
                return {
                    "success": True,
                    "data": {
                        "processed_items": [],
                        "errors": []
                    },
                    "message": "No orphaned items found to clean up",
                    "metadata": {
                        "cleanup_action": params.get("cleanup_action", "move_to_root"),
                        "total_orphaned_found": 0
                    }
                }
            
            # Clean up orphaned items
            cleanup_action = params.get("cleanup_action", "move_to_root")
            cleanup_results = await self.hierarchy_validator.cleanup_orphaned_items(
                orphaned_items, cleanup_action
            )
            
            return {
                "success": cleanup_results['success'],
                "data": cleanup_results,
                "message": f"Cleanup completed. Processed {len(cleanup_results['processed_items'])} items with {len(cleanup_results['errors'])} errors.",
                "metadata": {
                    "cleanup_action": cleanup_action,
                    "total_orphaned_found": len(orphaned_items),
                    "total_processed": len(cleanup_results['processed_items']),
                    "total_errors": len(cleanup_results['errors'])
                }
            }
        except Exception as e:
            logger.error(f"Error in orphan cleanup: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "ORPHAN_CLEANUP_ERROR"
            }


# Export the tool
HIERARCHY_TOOLS = [UnifiedHierarchyTool]