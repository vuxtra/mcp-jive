"""Unified Work Item Retrieval Tool - Consolidates retrieval and listing operations.

This tool replaces:
- jive_get_work_item
- jive_get_task
- jive_list_work_items
- jive_list_tasks
"""

import json
import logging
from typing import Dict, Any, Optional, List, Union, Tuple
try:
    from mcp.types import Tool
except ImportError:
    # Mock Tool type if MCP not available
    Tool = Dict[str, Any]
from datetime import datetime
import uuid

from ..base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class UnifiedRetrievalTool(BaseTool):
    """Unified tool for work item retrieval and listing."""
    
    def __init__(self, storage=None):
        """Initialize the unified retrieval tool.
        
        Args:
            storage: Work item storage instance (optional)
        """
        super().__init__()
        self.storage = storage
        self.tool_name = "jive_get_work_item"
    
    @property
    def name(self) -> str:
        """Tool name identifier."""
        return self.tool_name
    
    @property
    def description(self) -> str:
        """Tool description for AI agents."""
        return "Jive: Unified work item retrieval and listing with flexible filtering and pagination"
    
    @property
    def category(self):
        """Tool category."""
        from ..base import ToolCategory
        return ToolCategory.WORK_ITEM_MANAGEMENT
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        """Parameters schema for the tool."""
        return {
            "work_item_id": {
                "type": "string",
                "description": "Work item ID for single retrieval (optional)"
            },
            "filters": {
                "type": "object",
                "description": "Filters for listing work items"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of items to return"
            }
        }

    async def _resolve_work_item_id(self, work_item_id: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """Resolve work item ID from UUID, title, or keywords. Returns (resolved_id, work_item_data)."""
        from ...uuid_utils import is_valid_uuid
        
        logger.info(f"🔍 Resolving work item ID: '{work_item_id}'")
        
        # Handle empty or whitespace-only identifiers
        if not work_item_id or not work_item_id.strip():
            logger.info(f"   ❌ Empty or whitespace-only identifier provided")
            return None, None
        
        # Check if it's already a valid UUID
        if is_valid_uuid(work_item_id):
            logger.info(f"   📋 Trying UUID lookup for: {work_item_id}")
            # Verify the work item exists
            work_item = await self.storage.get_work_item(work_item_id)
            if work_item:
                logger.info(f"   ✅ Found by UUID: {work_item.get('title')}")
                return work_item_id, work_item
            else:
                logger.info(f"   ❌ UUID not found in storage")
        
        # Try direct ID lookup first (for non-UUID IDs like "test-123")
        try:
            logger.info(f"   📋 Trying direct ID lookup for: {work_item_id}")
            work_item = await self.storage.get_work_item(work_item_id)
            if work_item:
                logger.info(f"   ✅ Found by direct ID: {work_item.get('title')}")
                return work_item_id, work_item
        except Exception as e:
            logger.info(f"   ❌ Direct ID lookup failed: {e}")
            pass  # Continue with other resolution methods
         
        # Try exact title match
        logger.info(f"   📋 Listing all work items for title/keyword search")
        work_items_result = await self.storage.list_work_items()
        # Handle both list and dict responses
        if isinstance(work_items_result, dict) and "items" in work_items_result:
            work_items = work_items_result["items"]
        else:
            work_items = work_items_result
            
        logger.info(f"   📊 Found {len(work_items)} work items to search through")
        for i, item in enumerate(work_items):
            logger.info(f"     {i+1}. {item.get('title', 'No title')} (ID: {item.get('id', 'No ID')})")
            
        for item in work_items:
            if item.get("title", "").lower() == work_item_id.lower():
                logger.info(f"   ✅ Found by exact title match: {item.get('title')}")
                # Get the full work item data
                work_item = await self.storage.get_work_item(item.get("id"))
                return item.get("id"), work_item
        
        # Try keyword search
        keywords = work_item_id.lower().split()
        logger.info(f"   📋 Trying keyword search with: {keywords}")
        for item in work_items:
            item_text = f"{item.get('title', '')} {item.get('description', '')}".lower()
            if all(keyword in item_text for keyword in keywords):
                logger.info(f"   ✅ Found by keyword search: {item.get('title')}")
                # Get the full work item data
                work_item = await self.storage.get_work_item(item.get("id"))
                return item.get("id"), work_item
        
        logger.info(f"   ❌ No match found for: '{work_item_id}'")
        return None, None
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters."""
        try:
            work_item_id = kwargs.get("work_item_id")
            
            if work_item_id:
                result = await self._get_single_work_item(work_item_id, kwargs)
                return ToolResult(
                    success=result.get("success", False),
                    data=result.get("work_item"),  # Map work_item to data
                    message=result.get("message"),
                    error=result.get("error"),
                    metadata=result.get("metadata")
                )
            else:
                result = await self._list_work_items(kwargs)
                return ToolResult(
                    success=result.get("success", False),
                    data=result.get("work_items"),  # Map work_items to data
                    message=result.get("message"),
                    error=result.get("error"),
                    metadata=result.get("pagination")  # Include pagination as metadata
                )
        except Exception as e:
            logger.error(f"Error in unified retrieval tool execute: {str(e)}")
            return ToolResult(
                success=False,
                error=str(e)
            )
    
    async def get_tools(self) -> List[Tool]:
        """Get the unified work item retrieval tool."""
        return [
            Tool(
                name="jive_get_work_item",
                description="Jive: Get single work item details or list work items with filtering and pagination",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "work_item_id": {
                            "type": "string",
                            "description": "Work item identifier for single item retrieval. Can be UUID, exact title, or keywords. If not provided, returns a list of work items."
                        },
                        "filters": {
                            "type": "object",
                            "properties": {
                                "type": {
                                    "type": "array",
                                    "items": {
                                        "type": "string",
                                        "enum": ["initiative", "epic", "feature", "story", "task"]
                                    },
                                    "description": "Filter by work item types"
                                },
                                "status": {
                                    "type": "array",
                                    "items": {
                                        "type": "string",
                                        "enum": ["not_started", "in_progress", "completed", "blocked", "cancelled"]
                                    },
                                    "description": "Filter by status values"
                                },
                                "priority": {
                                    "type": "array",
                                    "items": {
                                        "type": "string",
                                        "enum": ["low", "medium", "high", "critical"]
                                    },
                                    "description": "Filter by priority levels"
                                },
                                "assignee_id": {
                                    "type": "string",
                                    "description": "Filter by assignee identifier"
                                },
                                "parent_id": {
                                    "type": "string",
                                    "description": "Filter by parent work item ID"
                                },
                                "tags": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Filter by tags (work items must have all specified tags)"
                                },
                                "created_after": {
                                    "type": "string",
                                    "format": "date-time",
                                    "description": "Filter work items created after this date"
                                },
                                "created_before": {
                                    "type": "string",
                                    "format": "date-time",
                                    "description": "Filter work items created before this date"
                                },
                                "updated_after": {
                                    "type": "string",
                                    "format": "date-time",
                                    "description": "Filter work items updated after this date"
                                }
                            },
                            "description": "Filters for listing work items (ignored when work_item_id is provided)"
                        },
                        "include_children": {
                            "type": "boolean",
                            "default": False,
                            "description": "Include child work items in the response"
                        },
                        "include_metadata": {
                            "type": "boolean",
                            "default": True,
                            "description": "Include metadata like effort estimates and acceptance criteria"
                        },
                        "sort_by": {
                            "type": "string",
                            "enum": ["order_index", "created_date", "updated_date", "priority", "status", "title", "due_date"],
                            "default": "order_index",
                            "description": "Field to sort by (for listing)"
                        },
                        "sort_order": {
                            "type": "string",
                            "enum": ["asc", "desc"],
                            "default": "asc",
                            "description": "Sort order (for listing)"
                        },
                        "limit": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 100,
                            "default": 50,
                            "description": "Maximum number of items to return (for listing)"
                        },
                        "offset": {
                            "type": "integer",
                            "minimum": 0,
                            "default": 0,
                            "description": "Number of items to skip (for listing pagination)"
                        }
                    },
                    "required": []
                }
            )
        ]
    
    async def handle_tool_call(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle unified work item retrieval calls."""
        if name != "jive_get_work_item":
            raise ValueError(f"Unknown tool: {name}")
        
        work_item_id = arguments.get("work_item_id")
        
        try:
            if work_item_id is not None:
                result = await self._get_single_work_item(work_item_id, arguments)
                # Return the full result structure for single item retrieval
                return result
            else:
                result = await self._list_work_items(arguments)
                # Return the list result for multiple items
                return result
            
        except Exception as e:
            logger.error(f"Error in unified retrieval tool: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "RETRIEVAL_ERROR"
            }
    
    async def _get_single_work_item(self, work_item_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get single work item with optional related data."""
        include_children = arguments.get("include_children", False)
        include_metadata = arguments.get("include_metadata", True)
        
        # Resolve work item ID (supports UUID, exact title, or keywords)
        resolved_id, work_item = await self._resolve_work_item_id(work_item_id)
        if not resolved_id:
            raise ValueError(f"Work item not found: {work_item_id}")
        
        if not work_item:
            raise ValueError(f"Work item not found: {work_item_id}")
        
        # Include children if requested
        if include_children:
            try:
                children = await self.storage.get_work_item_children(resolved_id)
                work_item["children"] = children
                work_item["children_count"] = len(children)
            except Exception as e:
                logger.warning(f"Failed to get children for {resolved_id}: {e}")
                work_item["children"] = []
                work_item["children_count"] = 0
        
        # Include metadata if requested
        if include_metadata:
            try:
                metadata = await self._get_work_item_metadata(resolved_id)
                work_item["metadata"] = metadata
            except Exception as e:
                logger.warning(f"Failed to get metadata for {resolved_id}: {e}")
                work_item["metadata"] = {}
        
        logger.info(f"Retrieved work item: {work_item['title']} (ID: {resolved_id})")
        
        return {
            "success": True,
            "work_item": work_item,
            "message": f"Retrieved work item: {work_item['title']}"
        }
    
    async def _list_work_items(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """List work items with filtering and pagination."""
        filters = arguments.get("filters", {})
        limit = arguments.get("limit", 50)
        offset = arguments.get("offset", 0)
        include_metadata = arguments.get("include_metadata", True)
        
        # Get sort parameters with order_index as default
        sort_by = arguments.get("sort_by", "order_index")
        sort_order = arguments.get("sort_order", "asc")
        
        # Execute query with pagination and sorting
        result = await self.storage.list_work_items(
            filters=filters,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Extract work items from result
        if isinstance(result, dict) and "items" in result:
            work_items = result["items"]
            total_count = result.get("total", len(work_items))
        else:
            work_items = result
            total_count = len(work_items)
        
        # Add metadata if requested
        if include_metadata:
            for item in work_items:
                try:
                    item["metadata"] = await self._get_work_item_metadata(item["id"])
                except Exception as e:
                    logger.warning(f"Failed to get metadata for {item['id']}: {e}")
                    item["metadata"] = {}
        
        # Calculate pagination info
        has_more = offset + len(work_items) < total_count
        
        logger.info(
            f"Listed {len(work_items)} work items "
            f"(offset: {offset}, total: {total_count})"
        )
        
        return {
            "success": True,
            "work_items": work_items,
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": has_more,
                "current_page": (offset // limit) + 1,
                "total_pages": (total_count + limit - 1) // limit
            },
            "filters_applied": filters,
            "message": f"Found {total_count} work items, showing {len(work_items)} items"
        }
    

    
    async def _get_work_item_metadata(self, work_item_id: str) -> Dict[str, Any]:
        """Get additional metadata for a work item."""
        metadata = {}
        
        try:
            # Get children count
            children = await self.storage.get_work_item_children(work_item_id)
            metadata["children_count"] = len(children)
            
            # Get dependencies count
            dependencies = await self.storage.get_work_item_dependencies(work_item_id)
            metadata["dependencies_count"] = len(dependencies)
            metadata["blocking_dependencies"] = len([
                dep for dep in dependencies 
                if dep.get("is_blocking", False) and dep.get("status") != "completed"
            ])
            
            # Calculate progress if it has children
            if metadata["children_count"] > 0:
                completed_children = len([
                    child for child in children 
                    if child.get("status") == "completed"
                ])
                metadata["progress_percentage"] = (
                    completed_children / metadata["children_count"] * 100
                )
            
        except Exception as e:
            logger.warning(f"Error calculating metadata for {work_item_id}: {e}")
        
        return metadata
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool schema for MCP registration."""
        return {
            "name": "jive_get_work_item",
            "description": "Jive: Unified work item retrieval - get work items by ID, title, or search criteria",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "work_item_id": {
                        "type": "string",
                        "description": "Work item identifier - can be UUID, exact title, or keywords for search"
                    },
                    "include_children": {
                        "type": "boolean",
                        "default": False,
                        "description": "Include child work items in the response"
                    },
                    "include_metadata": {
                        "type": "boolean",
                        "default": True,
                        "description": "Include additional metadata like progress and relationships"
                    },
                    "format": {
                        "type": "string",
                        "enum": ["detailed", "summary", "minimal"],
                        "default": "detailed",
                        "description": "Response format level"
                    }
                },
                "required": ["work_item_id"]
            }
        }