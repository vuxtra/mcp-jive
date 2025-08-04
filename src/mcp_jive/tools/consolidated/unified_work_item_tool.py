"""Unified Work Item Management Tool - Consolidates CRUD operations.

This tool replaces:
- jive_create_work_item
- jive_update_work_item
- jive_create_task
- jive_update_task
- jive_delete_task
"""

import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
try:
    from mcp.types import Tool
except ImportError:
    # Mock Tool type if MCP not available
    Tool = Dict[str, Any]

from ..base import BaseTool

logger = logging.getLogger(__name__)


class UnifiedWorkItemTool(BaseTool):
    """Unified tool for all work item CRUD operations."""
    
    def __init__(self, storage=None):
        """Initialize the unified work item tool.
        
        Args:
            storage: Work item storage instance (optional)
        """
        super().__init__()
        self.storage = storage
        self.tool_name = "jive_manage_work_item"
        
        # Work item type hierarchy rules
        self.hierarchy_rules = {
            "initiative": ["epic"],
            "epic": ["feature"],
            "feature": ["story"],
            "story": ["task"],
            "task": []  # Tasks cannot have children
        }
    
    @property
    def name(self) -> str:
        """Tool name identifier."""
        return self.tool_name
    
    @property
    def description(self) -> str:
        """Tool description for AI agents."""
        return "Jive: Unified work item management - create, update, or delete work items and tasks"
    
    @property
    def category(self):
        """Tool category."""
        from ..base import ToolCategory
        return ToolCategory.WORK_ITEM_MANAGEMENT
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        """Parameters schema for the tool."""
        return {
            "action": {
                "type": "string",
                "enum": ["create", "update", "delete"],
                "description": "Action to perform on the work item"
            },
            "work_item_id": {
                "type": "string",
                "description": "Work item ID (required for update/delete)"
            },
            "type": {
                "type": "string",
                "enum": ["initiative", "epic", "feature", "story", "task"],
                "description": "Type of work item (required for create)"
            },
            "title": {
                "type": "string",
                "description": "Work item title (required for create)"
            }
        }
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool with given parameters."""
        action = kwargs.get("action")
        
        if action == "create":
            return await self._create_work_item(**kwargs)
        elif action == "update":
            return await self._update_work_item(**kwargs)
        elif action == "delete":
            return await self._delete_work_item(**kwargs)
        else:
            return {
                "success": False,
                "error": f"Invalid action: {action}"
            }
    
    async def get_tools(self) -> List[Tool]:
        """Get the unified work item management tool."""
        return [
            Tool(
                name="jive_manage_work_item",
                description="Jive: Unified work item management - create, update, or delete work items and tasks",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["create", "update", "delete"],
                            "description": "Action to perform on the work item"
                        },
                        "work_item_id": {
                            "type": "string",
                            "description": "Work item identifier - required for update/delete actions. Can be UUID, exact title, or keywords"
                        },
                        "type": {
                            "type": "string",
                            "enum": ["initiative", "epic", "feature", "story", "task"],
                            "description": "Work item type - required for create action"
                        },
                        "title": {
                            "type": "string",
                            "description": "Work item title"
                        },
                        "description": {
                            "type": "string",
                            "description": "Detailed description of the work item"
                        },
                        "status": {
                            "type": "string",
                            "enum": ["not_started", "in_progress", "completed", "blocked", "cancelled"],
                            "default": "not_started",
                            "description": "Current status of the work item"
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["low", "medium", "high", "critical"],
                            "default": "medium",
                            "description": "Priority level of the work item"
                        },
                        "parent_id": {
                            "type": "string",
                            "description": "Parent work item ID for hierarchy (optional)"
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Tags for categorization and filtering"
                        },
                        "acceptance_criteria": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Acceptance criteria for completion validation"
                        },
                        "effort_estimate": {
                            "type": "number",
                            "description": "Effort estimate in hours"
                        },
                        "due_date": {
                            "type": "string",
                            "format": "date-time",
                            "description": "Due date in ISO 8601 format"
                        },
                        "delete_children": {
                            "type": "boolean",
                            "default": False,
                            "description": "Whether to delete child work items (for delete action)"
                        }
                    },
                    "required": ["action"],
                    "allOf": [
                        {
                            "if": {"properties": {"action": {"const": "create"}}},
                            "then": {"required": ["type", "title"]}
                        },
                        {
                            "if": {"properties": {"action": {"enum": ["update", "delete"]}}},
                            "then": {"required": ["work_item_id"]}
                        }
                    ]
                }
            )
        ]
    
    async def handle_tool_call(self, name: str, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle unified work item management calls."""
        if name != "jive_manage_work_item":
            raise ValueError(f"Unknown tool: {name}")
        
        action = arguments.get("action")
        
        try:
            if action == "create":
                result = await self._create_work_item(arguments)
            elif action == "update":
                result = await self._update_work_item(arguments)
            elif action == "delete":
                result = await self._delete_work_item(arguments)
            else:
                raise ValueError(f"Invalid action: {action}")
            
            return [{
                "type": "text",
                "text": result["message"] if "message" in result else str(result)
            }]
            
        except Exception as e:
            logger.error(f"Error in unified work item tool: {e}")
            return [{
                "type": "text",
                "text": f"Error: {str(e)}"
            }]
    
    async def _create_work_item(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new work item."""
        work_item_type = arguments["type"]
        title = arguments["title"]
        description = arguments.get("description", "")
        status = arguments.get("status", "not_started")
        priority = arguments.get("priority", "medium")
        parent_id = arguments.get("parent_id")
        tags = arguments.get("tags", [])
        acceptance_criteria = arguments.get("acceptance_criteria", [])
        effort_estimate = arguments.get("effort_estimate")
        due_date = arguments.get("due_date")
        
        # Generate unique ID
        work_item_id = generate_uuid()
        
        # Validate hierarchy if parent specified
        if parent_id:
            parent = await self._get_work_item_by_id(parent_id)
            if not parent:
                raise ValueError(f"Parent work item not found: {parent_id}")
            
            if not self._validate_hierarchy(parent["type"], work_item_type):
                raise ValueError(
                    f"Invalid hierarchy: {work_item_type} cannot be child of {parent['type']}"
                )
        
        # Create work item object
        work_item = {
            "id": work_item_id,
            "type": work_item_type,
            "title": title,
            "description": description,
            "status": status,
            "priority": priority,
            "parent_id": parent_id,
            "tags": tags,
            "acceptance_criteria": acceptance_criteria,
            "effort_estimate": effort_estimate,
            "due_date": due_date,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Store in database
        await self.storage.create_work_item(work_item)
        
        # Sync to file system
        if self.sync_manager:
            try:
                await self.sync_manager.sync_to_file(work_item)
            except Exception as e:
                logger.warning(f"Failed to sync work item to file: {e}")
        
        logger.info(f"Created {work_item_type} '{title}' with ID: {work_item_id}")
        
        return {
            "success": True,
            "work_item_id": work_item_id,
            "message": f"{work_item_type.title()} '{title}' created successfully",
            "work_item": work_item
        }
    
    async def _update_work_item(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing work item."""
        work_item_id = arguments["work_item_id"]
        
        # Resolve work item ID
        resolved_id = await self.id_resolver.resolve_work_item_id(work_item_id)
        
        # Get existing work item
        existing_item = await self._get_work_item_by_id(resolved_id)
        if not existing_item:
            raise ValueError(f"Work item not found: {work_item_id}")
        
        # Update fields
        updated_item = existing_item.copy()
        
        # Update allowed fields
        updatable_fields = [
            "title", "description", "status", "priority", "tags",
            "acceptance_criteria", "effort_estimate", "due_date"
        ]
        
        for field in updatable_fields:
            if field in arguments:
                updated_item[field] = arguments[field]
        
        # Handle parent_id changes with validation
        if "parent_id" in arguments:
            new_parent_id = arguments["parent_id"]
            if new_parent_id and new_parent_id != existing_item.get("parent_id"):
                parent = await self._get_work_item_by_id(new_parent_id)
                if not parent:
                    raise ValueError(f"Parent work item not found: {new_parent_id}")
                
                if not self._validate_hierarchy(parent["type"], existing_item["type"]):
                    raise ValueError(
                        f"Invalid hierarchy: {existing_item['type']} cannot be child of {parent['type']}"
                    )
            
            updated_item["parent_id"] = new_parent_id
        
        updated_item["updated_at"] = datetime.utcnow().isoformat()
        
        # Update in database
        await self.storage.update_work_item(resolved_id, updated_item)
        
        # Sync to file system
        if self.sync_manager:
            try:
                await self.sync_manager.sync_to_file(updated_item)
            except Exception as e:
                logger.warning(f"Failed to sync updated work item to file: {e}")
        
        logger.info(f"Updated work item '{existing_item['title']}' (ID: {resolved_id})")
        
        return {
            "success": True,
            "work_item_id": resolved_id,
            "message": f"Work item '{updated_item['title']}' updated successfully",
            "work_item": updated_item
        }
    
    async def _delete_work_item(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a work item and optionally its children."""
        work_item_id = arguments["work_item_id"]
        delete_children = arguments.get("delete_children", False)
        
        # Resolve work item ID
        resolved_id = await self.id_resolver.resolve_work_item_id(work_item_id)
        
        # Get existing work item
        existing_item = await self._get_work_item_by_id(resolved_id)
        if not existing_item:
            raise ValueError(f"Work item not found: {work_item_id}")
        
        deleted_items = []
        
        # Handle children if requested
        if delete_children:
            children = await self.storage.get_work_item_children(resolved_id)
            for child in children:
                await self.storage.delete_work_item(child["id"])
                deleted_items.append(child["title"])
                logger.info(f"Deleted child work item: {child['title']} (ID: {child['id']})")
        else:
            # Check for children and warn
            children = await self.storage.get_work_item_children(resolved_id)
            if children:
                logger.warning(
                    f"Work item has {len(children)} children. "
                    f"Use delete_children=true to delete them as well."
                )
        
        # Delete the main work item
        await self.storage.delete_work_item(resolved_id)
        deleted_items.insert(0, existing_item["title"])
        
        # Sync deletion to file system
        if self.sync_manager:
            try:
                await self.sync_manager.remove_from_file(resolved_id)
            except Exception as e:
                logger.warning(f"Failed to sync work item deletion to file: {e}")
        
        logger.info(f"Deleted work item '{existing_item['title']}' (ID: {resolved_id})")
        
        return {
            "success": True,
            "work_item_id": resolved_id,
            "message": f"Deleted {len(deleted_items)} work item(s): {', '.join(deleted_items)}",
            "deleted_count": len(deleted_items)
        }
    
    def _validate_hierarchy(self, parent_type: str, child_type: str) -> bool:
        """Validate work item hierarchy rules."""
        allowed_children = self.hierarchy_rules.get(parent_type, [])
        return child_type in allowed_children
    
    async def _get_work_item_by_id(self, work_item_id: str) -> Optional[Dict[str, Any]]:
        """Get work item by ID with error handling."""
        try:
            return await self.storage.get_work_item(work_item_id)
        except Exception as e:
            logger.error(f"Error getting work item {work_item_id}: {e}")
            return None
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool schema for MCP registration."""
        return {
            "name": "jive_manage_work_item",
            "description": "Jive: Unified work item management - create, update, or delete work items and tasks",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["create", "update", "delete"],
                        "description": "Action to perform on the work item"
                    },
                    "work_item_id": {
                        "type": "string",
                        "description": "Work item identifier - required for update/delete actions. Can be UUID, exact title, or keywords"
                    },
                    "type": {
                        "type": "string",
                        "enum": ["initiative", "epic", "feature", "story", "task"],
                        "description": "Work item type - required for create action"
                    },
                    "title": {
                        "type": "string",
                        "description": "Work item title"
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed description of the work item"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["not_started", "in_progress", "completed", "blocked", "cancelled"],
                        "default": "not_started",
                        "description": "Current status of the work item"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                        "default": "medium",
                        "description": "Priority level of the work item"
                    },
                    "parent_id": {
                        "type": "string",
                        "description": "Parent work item ID for hierarchy (optional)"
                    }
                },
                "required": ["action"]
            }
        }