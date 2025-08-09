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
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from ...uuid_utils import validate_uuid, is_valid_uuid
try:
    from mcp.types import Tool
except ImportError:
    # Mock Tool type if MCP not available
    Tool = Dict[str, Any]

from ..base import BaseTool, ToolResult
from ...uuid_utils import generate_uuid, validate_uuid

logger = logging.getLogger(__name__)


class UnifiedWorkItemTool(BaseTool):
    """Unified tool for all work item CRUD operations."""
    
    def __init__(self, storage=None, sync_manager=None):
        """Initialize the unified work item tool.
        
        Args:
            storage: Work item storage instance (optional)
            sync_manager: Sync manager instance (optional)
        """
        super().__init__()
        self.storage = storage
        self.sync_manager = sync_manager
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
            },
            "description": {
                "type": "string",
                "description": "Detailed description of the work item"
            },
            "context_tags": {
                "type": "array",
                "items": {"type": "string"},
                "maxItems": 3,
                "description": "Technical context tags for AI categorization"
            },
            "complexity": {
                "type": "string",
                "enum": ["simple", "moderate", "complex"],
                "description": "Implementation complexity to guide AI agent approach"
            },
            "acceptance_criteria": {
                "type": "array",
                "items": {"type": "string"},
                "maxItems": 5,
                "description": "Clear, testable criteria for AI agents to validate completion"
            },
            "notes": {
                "type": "string",
                "maxLength": 500,
                "description": "Implementation notes, constraints, or context for AI agent"
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
        }
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters."""
        try:
            action = kwargs.get("action")
            
            if action == "create":
                result = await self._create_work_item(kwargs)
            elif action == "update":
                result = await self._update_work_item(kwargs)
            elif action == "delete":
                result = await self._delete_work_item(kwargs)
            else:
                return ToolResult(
                    success=False,
                    error=f"Invalid action: {action}"
                )
            
            # Convert dictionary result to ToolResult
            return ToolResult(
                success=result.get("success", False),
                data=result.get("data"),
                message=result.get("message"),
                error=result.get("error"),
                metadata=result.get("metadata")
            )
        except Exception as e:
            logger.error(f"Error in unified work item tool execution: {str(e)}")
            return ToolResult(
                success=False,
                error=f"Tool execution failed: {str(e)}"
            )
    
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
                        "parent_id": {
                            "type": "string",
                            "description": "Parent work item ID for hierarchy (optional)"
                        },
                        "context_tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "maxItems": 3,
                            "description": "Technical context tags for AI categorization: 'frontend', 'backend', 'database', 'api', 'testing', 'documentation'"
                        },
                        "complexity": {
                            "type": "string",
                            "enum": ["simple", "moderate", "complex"],
                            "description": "Implementation complexity to guide AI agent approach and resource allocation"
                        },
                        "acceptance_criteria": {
                            "type": "array",
                            "items": {"type": "string"},
                            "maxItems": 5,
                            "description": "Clear, testable criteria for AI agents to validate completion"
                        },
                        "notes": {
                            "type": "string",
                            "maxLength": 500,
                            "description": "Implementation notes, constraints, or context for AI agent"
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["low", "medium", "high", "critical"],
                            "default": "medium",
                            "description": "Priority level of the work item"
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
    
    async def handle_tool_call(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle unified work item management calls."""
        if name != "jive_manage_work_item":
            raise ValueError(f"Unknown tool: {name}")
        
        action = arguments["action"]
        
        try:
            if action == "create":
                result = await self._create_work_item(arguments)
            elif action == "update":
                result = await self._update_work_item(arguments)
            elif action == "delete":
                result = await self._delete_work_item(arguments)
            else:
                raise ValueError(f"Invalid action: {action}")
            
            return {
                "success": True,
                "data": {
                    "id": result.get("metadata", {}).get("work_item_id"),
                    "message": result.get("message"),
                    "work_item": result.get("data")
                }
            }
            
        except Exception as e:
            logger.error(f"Error in unified work item tool: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "WORK_ITEM_ERROR"
            }
    
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
        
        # AI optimization parameters
        context_tags = arguments.get("context_tags", [])
        complexity = arguments.get("complexity", "medium")
        notes = arguments.get("notes", "")
        
        # Generate unique ID
        work_item_id = generate_uuid()
        
        # Validate hierarchy if parent specified
        if parent_id:
            parent = await self._get_work_item_by_id(parent_id)
            if not parent:
                raise ValueError(f"Parent work item not found: {parent_id}")
            
            if not self._validate_hierarchy(parent["item_type"], work_item_type):
                raise ValueError(
                    f"Invalid hierarchy: {work_item_type} cannot be child of {parent['item_type']}"
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
            "context_tags": context_tags,
            "complexity": complexity,
            "notes": notes,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
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
            "data": work_item,
            "message": f"{work_item_type.title()} '{title}' created successfully",
            "metadata": {
                "work_item_id": work_item_id,
                "type": work_item_type
            }
        }
    
    async def _update_work_item(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing work item."""
        work_item_id = arguments["work_item_id"]
        
        # Resolve work item ID
        resolved_id = await self._resolve_work_item_id(work_item_id)
        
        # Get existing work item
        existing_item = await self._get_work_item_by_id(resolved_id)
        if not existing_item:
            raise ValueError(f"Work item not found: {work_item_id}")
        
        # Update fields
        updated_item = existing_item.copy()
        
        # Update allowed fields
        updatable_fields = [
            "title", "description", "status", "priority", "tags",
            "acceptance_criteria", "effort_estimate", "due_date",
            "context_tags", "complexity", "notes", "assignee"
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
                
                if not self._validate_hierarchy(parent["item_type"], existing_item["type"]):
                    raise ValueError(
                        f"Invalid hierarchy: {existing_item['type']} cannot be child of {parent['item_type']}"
                    )
            
            updated_item["parent_id"] = new_parent_id
        
        updated_item["updated_at"] = datetime.now(timezone.utc).isoformat()
        
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
            "data": updated_item,
            "message": f"Work item '{updated_item['title']}' updated successfully",
            "metadata": {
                "work_item_id": resolved_id,
                "type": updated_item.get('type')
            }
        }
    
    async def _delete_work_item(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a work item and optionally its children."""
        work_item_id = arguments["work_item_id"]
        delete_children = arguments.get("delete_children", False)
        
        # Resolve work item ID
        resolved_id = await self._resolve_work_item_id(work_item_id)
        
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
            if children is not None and len(children) > 0:
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
            "data": {
                "deleted_items": deleted_items,
                "deleted_count": len(deleted_items)
            },
            "message": f"Deleted {len(deleted_items)} work item(s): {', '.join(deleted_items)}",
            "metadata": {
                "work_item_id": resolved_id,
                "type": existing_item.get('type')
            }
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
                    },
                    "context_tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "maxItems": 3,
                        "description": "Technical context tags for AI categorization"
                    },
                    "complexity": {
                        "type": "string",
                        "enum": ["simple", "moderate", "complex"],
                        "description": "Implementation complexity to guide AI agent approach"
                    },
                    "notes": {
                        "type": "string",
                        "maxLength": 500,
                        "description": "Implementation notes, constraints, or context for AI agent"
                    },
                    "acceptance_criteria": {
                        "type": "array",
                        "items": {"type": "string"},
                        "maxItems": 5,
                        "description": "Clear, testable criteria for AI agents to validate completion"
                    }
                },
                "required": ["action"]
            }
        }
    
    async def _resolve_work_item_id(self, work_item_id: str) -> Optional[str]:
        """Resolve work item ID from UUID, title, or keywords."""
        # Try UUID first
        if is_valid_uuid(work_item_id):
            # Check if work item exists in storage
            try:
                existing_item = await self._get_work_item_by_id(work_item_id)
                if existing_item:
                    return work_item_id
            except Exception:
                pass
        
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