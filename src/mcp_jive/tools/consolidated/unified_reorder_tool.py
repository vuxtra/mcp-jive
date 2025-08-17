"""Unified Work Item Reordering Tool for MCP Jive.

This tool provides comprehensive work item reordering functionality including:
- Drag-and-drop reordering within the same parent
- Moving work items between different parents
- Automatic sequence number recalculation
- Batch order index updates
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

from ..base import BaseTool, ToolCategory, ToolSchema, ToolResult
from ...storage.work_item_storage import WorkItemStorage
from ...uuid_utils import validate_uuid

logger = logging.getLogger(__name__)

class UnifiedReorderTool(BaseTool):
    """Unified tool for work item reordering operations."""
    
    def __init__(self, storage: Optional[WorkItemStorage] = None):
        """Initialize the unified reorder tool.
        
        Args:
            storage: Work item storage instance (optional)
        """
        super().__init__()
        self.storage = storage
        self.tool_name = "jive_reorder_work_items"
    
    @property
    def name(self) -> str:
        """Tool name identifier."""
        return "jive_reorder_work_items"
    
    @property
    def description(self) -> str:
        """Tool description for AI agents."""
        return "Jive: Unified work item reordering - reorder work items within the same parent, move between parents, and recalculate sequence numbers"
    
    @property
    def category(self) -> ToolCategory:
        """Tool category."""
        return ToolCategory.HIERARCHY_MANAGEMENT
    
    @property
    def parameters_schema(self) -> Dict[str, ToolSchema]:
        """Parameters schema for the tool."""
        return {
            "action": ToolSchema(
                name="action",
                type="string",
                description="Action to perform on work items",
                required=True,
                default="reorder",
                enum=["reorder", "move", "swap", "recalculate"]
            ),
            "work_item_ids": ToolSchema(
                name="work_item_ids",
                type="array",
                description="Array of work item IDs in the desired order (required for reorder action)",
                required=False
            ),
            "parent_id": ToolSchema(
                name="parent_id",
                type="string",
                description="Parent work item ID for reordering within a specific parent (optional)",
                required=False
            ),
            "work_item_id": ToolSchema(
                name="work_item_id",
                type="string",
                description="Work item ID for move, swap, or recalculate actions",
                required=False
            ),
            "new_parent_id": ToolSchema(
                name="new_parent_id",
                type="string",
                description="New parent ID for move action",
                required=False
            ),
            "position": ToolSchema(
                name="position",
                type="integer",
                description="Position within the new parent for move action (optional)",
                required=False
            ),
            "work_item_id_1": ToolSchema(
                name="work_item_id_1",
                type="string",
                description="First work item ID for swap action",
                required=False
            ),
            "work_item_id_2": ToolSchema(
                name="work_item_id_2",
                type="string",
                description="Second work item ID for swap action",
                required=False
            )
        }
        
    async def execute(self, **kwargs) -> ToolResult:
        """Execute reordering operations.
        
        Args:
            **kwargs: Tool parameters
            
        Returns:
            Tool execution result
        """
        try:
            if not self.storage:
                raise RuntimeError("Work item storage not available")
                
            action = kwargs.get("action", "reorder")
            
            if action == "reorder":
                result = await self._reorder_work_items(kwargs)
            elif action == "move":
                result = await self._move_work_item(kwargs)
            elif action == "swap":
                result = await self._swap_work_items(kwargs)
            elif action == "recalculate":
                result = await self._recalculate_sequences(kwargs)
            else:
                raise ValueError(f"Unknown action: {action}")
            
            return ToolResult.success_result(data=result, message=f"Successfully executed {action} operation")
                
        except Exception as e:
            logger.error(f"Error in reorder tool execution: {e}")
            return ToolResult.error_result(error=str(e), data={"error_code": "REORDER_EXECUTION_ERROR"})
    
    async def _reorder_work_items(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Reorder work items within the same parent.
        
        Args:
            arguments: Contains work_item_ids in new order and optional parent_id
            
        Returns:
            Reordering result
        """
        work_item_ids = arguments.get("work_item_ids", [])
        parent_id = arguments.get("parent_id")
        
        if not work_item_ids:
            raise ValueError("work_item_ids is required for reordering")
            
        # Validate all work items exist and have the same parent
        work_items = []
        for work_item_id in work_item_ids:
            item = await self.storage.get_work_item(work_item_id)
            if not item:
                raise ValueError(f"Work item not found: {work_item_id}")
            work_items.append(item)
            
        # Verify all items have the same parent
        expected_parent = parent_id if parent_id else work_items[0].get('parent_id')
        for item in work_items:
            if item.get('parent_id') != expected_parent:
                raise ValueError(f"All work items must have the same parent for reordering")
        
        # Calculate new sequence numbers and order indices
        updates = []
        for i, work_item_id in enumerate(work_item_ids):
            item = work_items[i]
            
            # Generate new sequence number based on position
            if expected_parent:
                parent_item = await self.storage.get_work_item(expected_parent)
                if not parent_item:
                    raise ValueError(f"Parent work item not found: {expected_parent}")
                parent_sequence = parent_item.get('sequence_number', '0')
                new_sequence = f"{parent_sequence}.{i + 1}"
                
                # Calculate order index based on parent's order
                parent_order = parent_item.get('order_index', 0)
                new_order_index = parent_order * 1000 + (i + 1)
            else:
                # Top-level item
                new_sequence = str(i + 1)
                new_order_index = i + 1
            
            updates.append({
                "id": work_item_id,
                "sequence_number": new_sequence,
                "order_index": new_order_index
            })
        
        # Perform batch update
        result = await self.storage.batch_update_order_indices(updates)
        
        if result["success"]:
            logger.info(f"Successfully reordered {len(work_item_ids)} work items")
            return {
                "success": True,
                "message": f"Successfully reordered {result['updated_count']} work items",
                "updated_count": result["updated_count"],
                "reordered_items": updates
            }
        else:
            return {
                "success": False,
                "error": "Failed to reorder some work items",
                "failed_updates": result["failed_updates"],
                "errors": result["errors"]
            }
    
    async def _move_work_item(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Move a work item to a different parent.
        
        Args:
            arguments: Contains work_item_id, new_parent_id, and optional position
            
        Returns:
            Move result
        """
        work_item_id = arguments.get("work_item_id")
        new_parent_id = arguments.get("new_parent_id")
        position = arguments.get("position", -1)  # -1 means append to end
        
        if not work_item_id:
            raise ValueError("work_item_id is required for moving")
            
        # Get the work item to move
        work_item = await self.storage.get_work_item(work_item_id)
        if not work_item:
            raise ValueError(f"Work item not found: {work_item_id}")
            
        # Validate new parent if provided
        if new_parent_id:
            parent_item = await self.storage.get_work_item(new_parent_id)
            if not parent_item:
                raise ValueError(f"Parent work item not found: {new_parent_id}")
                
            # Validate hierarchy rules
            if not self._validate_hierarchy(parent_item.get('item_type'), work_item.get('item_type')):
                raise ValueError(
                    f"Invalid hierarchy: {work_item.get('item_type')} cannot be child of {parent_item.get('item_type')}"
                )
        
        # Get siblings in the new parent
        siblings = []
        if new_parent_id:
            all_items = await self.storage.list_work_items()
            siblings = [item for item in all_items if item.get('parent_id') == new_parent_id and item.get('id') != work_item_id]
        else:
            # Moving to top level
            all_items = await self.storage.list_work_items()
            siblings = [item for item in all_items if not item.get('parent_id') and item.get('id') != work_item_id]
            
        # Sort siblings by order_index
        siblings.sort(key=lambda x: x.get('order_index', 0))
        
        # Insert at specified position
        if position == -1 or position >= len(siblings):
            # Append to end
            siblings.append(work_item)
        else:
            # Insert at position
            siblings.insert(position, work_item)
        
        # Update parent_id for the moved item
        await self.storage.update_work_item(work_item_id, {"parent_id": new_parent_id})
        
        # Recalculate sequence numbers for all siblings
        updates = []
        for i, sibling in enumerate(siblings):
            if new_parent_id:
                parent_item = await self.storage.get_work_item(new_parent_id)
                parent_sequence = parent_item.get('sequence_number', '0')
                new_sequence = f"{parent_sequence}.{i + 1}"
                parent_order = parent_item.get('order_index', 0)
                new_order_index = parent_order * 1000 + (i + 1)
            else:
                new_sequence = str(i + 1)
                new_order_index = i + 1
                
            updates.append({
                "id": sibling.get('id'),
                "sequence_number": new_sequence,
                "order_index": new_order_index
            })
        
        # Perform batch update
        result = await self.storage.batch_update_order_indices(updates)
        
        if result["success"]:
            logger.info(f"Successfully moved work item {work_item_id} to new parent {new_parent_id}")
            return {
                "success": True,
                "message": f"Successfully moved work item to new parent",
                "moved_item_id": work_item_id,
                "new_parent_id": new_parent_id,
                "updated_siblings": result["updated_count"]
            }
        else:
            return {
                "success": False,
                "error": "Failed to update sequence numbers after move",
                "failed_updates": result["failed_updates"],
                "errors": result["errors"]
            }
    
    async def _swap_work_items(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Swap positions of two work items.
        
        Args:
            arguments: Contains work_item_id_1 and work_item_id_2
            
        Returns:
            Swap result
        """
        work_item_id_1 = arguments.get("work_item_id_1")
        work_item_id_2 = arguments.get("work_item_id_2")
        
        if not work_item_id_1 or not work_item_id_2:
            raise ValueError("Both work_item_id_1 and work_item_id_2 are required for swapping")
            
        # Get both work items
        item_1 = await self.storage.get_work_item(work_item_id_1)
        item_2 = await self.storage.get_work_item(work_item_id_2)
        
        if not item_1:
            raise ValueError(f"Work item not found: {work_item_id_1}")
        if not item_2:
            raise ValueError(f"Work item not found: {work_item_id_2}")
            
        # Verify they have the same parent
        if item_1.get('parent_id') != item_2.get('parent_id'):
            raise ValueError("Work items must have the same parent to swap positions")
        
        # Swap their order indices and sequence numbers
        updates = [
            {
                "id": work_item_id_1,
                "sequence_number": item_2.get('sequence_number'),
                "order_index": item_2.get('order_index', 0)
            },
            {
                "id": work_item_id_2,
                "sequence_number": item_1.get('sequence_number'),
                "order_index": item_1.get('order_index', 0)
            }
        ]
        
        # Perform batch update
        result = await self.storage.batch_update_order_indices(updates)
        
        if result["success"]:
            logger.info(f"Successfully swapped positions of {work_item_id_1} and {work_item_id_2}")
            return {
                "success": True,
                "message": "Successfully swapped work item positions",
                "swapped_items": [work_item_id_1, work_item_id_2]
            }
        else:
            return {
                "success": False,
                "error": "Failed to swap work item positions",
                "failed_updates": result["failed_updates"],
                "errors": result["errors"]
            }
    
    async def _recalculate_sequences(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Recalculate sequence numbers for all work items or a specific parent.
        
        Args:
            arguments: Optional parent_id to recalculate only children of that parent
            
        Returns:
            Recalculation result
        """
        parent_id = arguments.get("parent_id")
        
        # Get all work items
        all_items = await self.storage.list_work_items()
        
        if parent_id:
            # Recalculate only children of specified parent
            children = [item for item in all_items if item.get('parent_id') == parent_id]
            children.sort(key=lambda x: x.get('order_index', 0))
            
            parent_item = await self.storage.get_work_item(parent_id)
            if not parent_item:
                raise ValueError(f"Parent work item not found: {parent_id}")
                
            parent_sequence = parent_item.get('sequence_number', '0')
            parent_order = parent_item.get('order_index', 0)
            
            updates = []
            for i, child in enumerate(children):
                new_sequence = f"{parent_sequence}.{i + 1}"
                new_order_index = parent_order * 1000 + (i + 1)
                
                updates.append({
                    "id": child.get('id'),
                    "sequence_number": new_sequence,
                    "order_index": new_order_index
                })
        else:
            # Recalculate all sequence numbers
            updates = []
            
            # First, handle top-level items
            top_level = [item for item in all_items if not item.get('parent_id')]
            top_level.sort(key=lambda x: x.get('order_index', 0))
            
            for i, item in enumerate(top_level):
                new_sequence = str(i + 1)
                new_order_index = i + 1
                
                updates.append({
                    "id": item.get('id'),
                    "sequence_number": new_sequence,
                    "order_index": new_order_index
                })
                
                # Recursively handle children
                await self._recalculate_children_sequences(item.get('id'), new_sequence, new_order_index, all_items, updates)
        
        # Perform batch update
        result = await self.storage.batch_update_order_indices(updates)
        
        if result["success"]:
            scope = f"children of {parent_id}" if parent_id else "all work items"
            logger.info(f"Successfully recalculated sequence numbers for {scope}")
            return {
                "success": True,
                "message": f"Successfully recalculated sequence numbers for {scope}",
                "updated_count": result["updated_count"]
            }
        else:
            return {
                "success": False,
                "error": "Failed to recalculate sequence numbers",
                "failed_updates": result["failed_updates"],
                "errors": result["errors"]
            }
    
    async def _recalculate_children_sequences(self, parent_id: str, parent_sequence: str, parent_order: int, all_items: List[Dict], updates: List[Dict]) -> None:
        """Recursively recalculate sequence numbers for children."""
        children = [item for item in all_items if item.get('parent_id') == parent_id]
        children.sort(key=lambda x: x.get('order_index', 0))
        
        for i, child in enumerate(children):
            new_sequence = f"{parent_sequence}.{i + 1}"
            new_order_index = parent_order * 1000 + (i + 1)
            
            updates.append({
                "id": child.get('id'),
                "sequence_number": new_sequence,
                "order_index": new_order_index
            })
            
            # Recursively handle grandchildren
            await self._recalculate_children_sequences(child.get('id'), new_sequence, new_order_index, all_items, updates)
    
    def _validate_hierarchy(self, parent_type: str, child_type: str) -> bool:
        """Validate if a child type can be under a parent type."""
        hierarchy_rules = {
            "initiative": ["epic"],
            "epic": ["feature"],
            "feature": ["story"],
            "story": ["task"],
            "task": []  # Tasks cannot have children
        }
        
        allowed_children = hierarchy_rules.get(parent_type, [])
        return child_type in allowed_children
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool schema for MCP registration."""
        return {
            "name": "jive_reorder_work_items",
            "description": "Jive: Unified work item reordering - reorder work items within the same parent, move between parents, and recalculate sequence numbers",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["reorder", "move", "swap", "recalculate"],
                        "default": "reorder",
                        "description": "Action to perform on work items"
                    },
                    "work_item_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Array of work item IDs in the desired order (required for reorder action)"
                    },
                    "parent_id": {
                        "type": "string",
                        "description": "Parent work item ID for reordering within a specific parent (optional)"
                    },
                    "work_item_id": {
                        "type": "string",
                        "description": "Work item ID for move, swap, or recalculate actions"
                    },
                    "new_parent_id": {
                        "type": "string",
                        "description": "New parent ID for move action"
                    },
                    "position": {
                        "type": "integer",
                        "description": "Position within the new parent for move action (optional)"
                    },
                    "work_item_id_1": {
                        "type": "string",
                        "description": "First work item ID for swap action"
                    },
                    "work_item_id_2": {
                        "type": "string",
                        "description": "Second work item ID for swap action"
                    }
                },
                "required": ["action"]
            }
        }