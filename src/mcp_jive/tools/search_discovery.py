"""Search and Discovery Tools.

Implements the 4 search and discovery MCP tools:
- search_tasks: Search tasks by various criteria
- search_content: Search content across all data
- list_tasks: List tasks with filtering options
- get_task_hierarchy: Get hierarchical task structure
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from mcp.types import Tool, TextContent

from ..config import ServerConfig
from ..lancedb_manager import LanceDBManager

logger = logging.getLogger(__name__)


class SearchDiscoveryTools:
    """Search and discovery tool implementations."""
    
    def __init__(self, config: ServerConfig, lancedb_manager: LanceDBManager):
        self.config = config
        self.lancedb_manager = lancedb_manager
    async def _safe_database_operation(self, operation):
        """Safely execute a database operation with error handling."""
        try:
            return await operation()
        except Exception as e:
            error_msg = str(e).lower()
            if any(keyword in error_msg for keyword in [
                'connection refused', 'unavailable', 'grpc', 'timeout'
            ]):
                logger.error(f"Database connection error: {e}")
                return self._format_error_response("database_connection", "Database temporarily unavailable")
            else:
                logger.error(f"Database operation error: {e}", exc_info=True)
                return self._format_error_response("database_operation", str(e))
                
    def _format_error_response(self, error_type: str, error_message: str):
        """Format a standardized error response."""
        from mcp.types import TextContent
        return [TextContent(
            type="text",
            text=f"Error ({error_type}): {error_message}"
        )]

        
    async def initialize(self) -> None:
        """Initialize search and discovery tools."""
        logger.info("Initializing search and discovery tools...")
        
    async def get_tools(self) -> List[Tool]:
        """Get all search and discovery tools."""
        return [
            Tool(
                name="jive_search_tasks",
                description="Jive: Search task (development task or work item)s by title, description, tags, or other criteria",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query text"
                        },
                        "status": {
                            "type": "string",
                            "enum": ["todo", "in_progress", "completed", "cancelled"],
                            "description": "Filter by task status"
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["low", "medium", "high", "urgent"],
                            "description": "Filter by task priority"
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter by tags (any of these tags)"
                        },
                        "created_after": {
                            "type": "string",
                            "format": "date-time",
                            "description": "Filter tasks created after this date"
                        },
                        "created_before": {
                            "type": "string",
                            "format": "date-time",
                            "description": "Filter tasks created before this date"
                        },
                        "limit": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 100,
                            "default": 20,
                            "description": "Maximum number of results to return"
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="jive_search_content",
                description="Jive: Search across all content types (task (development task or work item)s, work items, etc.)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query text"
                        },
                        "content_types": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["task", "work_item", "search_index"]
                            },
                            "description": "Types of content to search",
                            "default": ["task", "work_item"]
                        },
                        "limit": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 100,
                            "default": 20,
                            "description": "Maximum number of results to return"
                        },
                        "include_score": {
                            "type": "boolean",
                            "default": False,
                            "description": "Include relevance scores in results"
                        }
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="jive_list_tasks",
                description="Jive: List task (development task or work item)s with optional filtering and sorting",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "enum": ["todo", "in_progress", "completed", "cancelled"],
                            "description": "Filter by task status"
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["low", "medium", "high", "urgent"],
                            "description": "Filter by task priority"
                        },
                        "parent_id": {
                            "type": "string",
                            "description": "Filter by parent task ID (null for top-level tasks)"
                        },
                        "sort_by": {
                            "type": "string",
                            "enum": ["created_at", "updated_at", "title", "priority", "due_date"],
                            "default": "created_at",
                            "description": "Field to sort by"
                        },
                        "sort_order": {
                            "type": "string",
                            "enum": ["asc", "desc"],
                            "default": "desc",
                            "description": "Sort order"
                        },
                        "limit": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 100,
                            "default": 20,
                            "description": "Maximum number of results to return"
                        },
                        "offset": {
                            "type": "integer",
                            "minimum": 0,
                            "default": 0,
                            "description": "Number of results to skip"
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="jive_get_task_hierarchy",
                description="Jive: Get hierarchical structure of task (development task or work item)s starting from a root task (development task or work item)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "root_task_id": {
                            "type": "string",
                            "description": "Root task ID (null for all top-level tasks)"
                        },
                        "max_depth": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 10,
                            "default": 5,
                            "description": "Maximum depth of hierarchy to retrieve"
                        },
                        "include_completed": {
                            "type": "boolean",
                            "default": True,
                            "description": "Whether to include completed tasks"
                        },
                        "include_cancelled": {
                            "type": "boolean",
                            "default": False,
                            "description": "Whether to include cancelled tasks"
                        }
                    },
                    "required": []
                }
            )
        ]
        
    async def handle_tool_call(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle tool calls for search and discovery."""
        if name == "jive_search_tasks":
            return await self._search_tasks(arguments)
        elif name == "jive_search_content":
            return await self._search_content(arguments)
        elif name == "jive_list_tasks":
            return await self._list_tasks(arguments)
        elif name == "jive_get_task_hierarchy":
            return await self._get_task_hierarchy(arguments)
        else:
            raise ValueError(f"Unknown search and discovery tool: {name}")
            
    async def _search_tasks(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Search tasks by various criteria."""
        try:
            query = arguments.get("query", "")
            limit = arguments.get("limit", 20)
            
            # Use LanceDB manager's search_tasks method
            if query:
                # Use vector search for text queries
                from mcp_jive.lancedb_manager import SearchType
                tasks = await self.lancedb_manager.search_tasks(
                    query=query,
                    search_type=SearchType.VECTOR,
                    limit=limit
                )
            else:
                # Use list_work_items for filtering without search query
                # Build filters for LanceDB
                filters = {}
                if "status" in arguments:
                    filters["status"] = arguments["status"]
                if "priority" in arguments:
                    filters["priority"] = arguments["priority"]
                
                # Note: LanceDB manager doesn't have list_tasks, using search with empty query
                tasks = await self.lancedb_manager.search_tasks(
                    query="",
                    search_type=SearchType.VECTOR,
                    limit=limit
                )
                
                # Apply filters manually since LanceDB search doesn't support complex filtering yet
                if filters:
                    filtered_tasks = []
                    for task in tasks:
                        match = True
                        for key, value in filters.items():
                            if task.get(key) != value:
                                match = False
                                break
                        if match:
                            filtered_tasks.append(task)
                    tasks = filtered_tasks[:limit]
            
            # Fix datetime and numpy array serialization
            import numpy as np
            serialized_tasks = []
            for task in tasks:
                serialized_task = {}
                for key, value in task.items():
                    if isinstance(value, datetime):
                        serialized_task[key] = value.isoformat()
                    elif isinstance(value, np.ndarray):
                        # Skip vector fields in response to avoid serialization issues
                        continue
                    elif hasattr(value, 'tolist') and hasattr(value, 'dtype'):
                        # Handle other numpy types
                        continue
                    else:
                        serialized_task[key] = value
                serialized_tasks.append(serialized_task)
            
            response = {
                "success": True,
                "query": query,
                "filters": {k: v for k, v in arguments.items() if k not in ["query", "limit"]},
                "total_results": len(serialized_tasks),
                "limit": limit,
                "tasks": serialized_tasks
            }
            
            return [TextContent(type="text", text=json.dumps(response, indent=2))]
            
        except Exception as e:
            logger.error(f"Error searching tasks: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "message": "Failed to search tasks"
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
            
    async def _search_content(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Search across all content types."""
        try:
            query = arguments["query"]
            content_types = arguments.get("content_types", ["task", "work_item"])
            limit = arguments.get("limit", 20)
            include_score = arguments.get("include_score", False)
            
            all_results = []
            
            # Search in each content type
            for content_type in content_types:
                try:
                    search_limit = limit // len(content_types) + 1
                    
                    if content_type == "task":
                        # Use the existing search_tasks method from LanceDBManager
                        from ..lancedb_manager import SearchType
                        task_results = await self.lancedb_manager.search_tasks(
                            query=query,
                            search_type=SearchType.VECTOR,
                            limit=search_limit
                        )
                        
                        # Format task results
                        for task in task_results:
                            result_data = {
                                "id": task.get("id"),
                                "type": "task",
                                "title": task.get("title"),
                                "description": task.get("description"),
                                "status": task.get("status"),
                                "priority": task.get("priority"),
                                "created_at": task.get("created_at"),
                                "updated_at": task.get("updated_at")
                            }
                            
                            if include_score and "_distance" in task:
                                result_data["score"] = 1.0 - task["_distance"]  # Convert distance to score
                                
                            all_results.append(result_data)
                            
                    elif content_type == "work_item":
                        # Use the existing search_work_items method from LanceDBManager
                        from mcp_jive.lancedb_manager import SearchType
                        work_item_results = await self.lancedb_manager.search_work_items(
                            query=query,
                            search_type=SearchType.VECTOR,
                            limit=search_limit
                        )
                        
                        # Format work item results
                        for item in work_item_results:
                            result_data = {
                                "id": item.get("id"),
                                "type": "work_item",
                                "title": item.get("title"),
                                "description": item.get("description"),
                                "item_type": item.get("item_type"),
                                "status": item.get("status"),
                                "priority": item.get("priority"),
                                "created_at": item.get("created_at"),
                                "updated_at": item.get("updated_at")
                            }
                            
                            if include_score and "_distance" in item:
                                result_data["score"] = 1.0 - item["_distance"]  # Convert distance to score
                                
                            all_results.append(result_data)
                            
                    elif content_type == "search_index":
                        # Use the existing search_content method from LanceDBManager
                        search_results = await self.lancedb_manager.search_content(
                            query=query,
                            limit=search_limit
                        )
                        
                        # Format search index results
                        for result in search_results:
                            result_data = {
                                "id": result.get("id"),
                                "type": "search_index",
                                "title": result.get("title"),
                                "content": result.get("content"),
                                "source_type": result.get("source_type"),
                                "source_id": result.get("source_id"),
                                "created_at": result.get("created_at")
                            }
                            
                            if include_score and "_distance" in result:
                                result_data["score"] = 1.0 - result["_distance"]  # Convert distance to score
                                
                            all_results.append(result_data)
                        
                except Exception as e:
                    logger.warning(f"Error searching in {content_type}: {e}")
                    continue
                    
            # Sort by score if available
            if include_score:
                all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
                
            # Limit total results
            all_results = all_results[:limit]
            
            # Apply datetime serialization fix
            serialized_results = []
            for result in all_results:
                serialized_result = {}
                for key, value in result.items():
                    if isinstance(value, datetime):
                        serialized_result[key] = value.isoformat()
                    elif hasattr(value, 'dtype') and 'numpy' in str(type(value)):
                        # Skip numpy arrays and other numpy types
                        continue
                    else:
                        serialized_result[key] = value
                serialized_results.append(serialized_result)
            
            response = {
                "success": True,
                "query": query,
                "content_types": content_types,
                "total_results": len(serialized_results),
                "limit": limit,
                "include_score": include_score,
                "results": serialized_results
            }
            
            return [TextContent(type="text", text=json.dumps(response, indent=2))]
            
        except Exception as e:
            logger.error(f"Error searching content: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "message": "Failed to search content"
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
            
    async def _list_tasks(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """List tasks with filtering and sorting."""
        try:
            # Build filters for LanceDB
            filters = {}
            if "status" in arguments:
                filters["status"] = arguments["status"]
            if "priority" in arguments:
                filters["priority"] = arguments["priority"]
            if "parent_id" in arguments:
                filters["parent_id"] = arguments["parent_id"]
                
            # Get pagination and sorting parameters
            limit = arguments.get("limit", 20)
            offset = arguments.get("offset", 0)
            sort_by = arguments.get("sort_by", "created_at")
            sort_order = arguments.get("sort_order", "desc")
            
            # Use LanceDB manager's list_work_items method
            # Note: We're using list_work_items since there's no list_tasks method
            # and tasks are stored as work items in the current implementation
            tasks = await self.lancedb_manager.list_work_items(
                filters=filters,
                limit=limit,
                offset=offset,
                sort_by=sort_by,
                sort_order=sort_order
            )
            
            # Fix datetime and numpy array serialization
            import numpy as np
            serialized_tasks = []
            for task in tasks:
                serialized_task = {}
                for key, value in task.items():
                    if isinstance(value, datetime):
                        serialized_task[key] = value.isoformat()
                    elif isinstance(value, np.ndarray):
                        # Skip vector fields in response to avoid serialization issues
                        continue
                    elif hasattr(value, 'tolist') and hasattr(value, 'dtype'):
                        # Handle other numpy types
                        continue
                    else:
                        serialized_task[key] = value
                serialized_tasks.append(serialized_task)
                
            response = {
                "success": True,
                "filters": {k: v for k, v in arguments.items() if k not in ["sort_by", "sort_order", "limit", "offset"]},
                "sort_by": sort_by,
                "sort_order": sort_order,
                "limit": limit,
                "offset": offset,
                "total_results": len(serialized_tasks),
                "tasks": serialized_tasks
            }
            
            return [TextContent(type="text", text=json.dumps(response, indent=2))]
            
        except Exception as e:
            logger.error(f"Error listing tasks: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "message": "Failed to list tasks"
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
            
    async def _get_task_hierarchy(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get hierarchical task structure."""
        try:
            root_task_id = arguments.get("root_task_id")
            max_depth = arguments.get("max_depth", 5)
            include_completed = arguments.get("include_completed", True)
            include_cancelled = arguments.get("include_cancelled", False)
            
            # Get all work items (tasks are stored as work items)
            all_items = await self.lancedb_manager.list_work_items(
                filters={},
                limit=1000,  # Get all items for hierarchy building
                offset=0,
                sort_by="created_at",
                sort_order="asc"
            )
            
            # Filter by status if needed
            filtered_items = []
            for item in all_items:
                status = item.get("status", "backlog")
                if not include_completed and status == "completed":
                    continue
                if not include_cancelled and status == "cancelled":
                    continue
                filtered_items.append(item)
            
            # Build hierarchy recursively
            def get_task_children(parent_id: Optional[str], current_depth: int) -> List[Dict[str, Any]]:
                if current_depth >= max_depth:
                    return []
                
                children = []
                for item in filtered_items:
                    item_parent_id = item.get("parent_id")
                    
                    # Check if this item is a child of the current parent
                    if (parent_id is None and item_parent_id is None) or (item_parent_id == parent_id):
                        # Create task data with hierarchy info
                        task_data = {}
                        for key, value in item.items():
                            if isinstance(value, datetime):
                                task_data[key] = value.isoformat()
                            elif hasattr(value, 'dtype') and 'numpy' in str(type(value)):
                                # Skip numpy arrays
                                continue
                            else:
                                task_data[key] = value
                        
                        task_data["depth"] = current_depth
                        
                        # Get children recursively
                        children_list = get_task_children(item.get("id"), current_depth + 1)
                        task_data["children"] = children_list
                        task_data["child_count"] = len(children_list)
                        
                        children.append(task_data)
                
                return children
            
            # Get hierarchy starting from root
            hierarchy = get_task_children(root_task_id, 0)
            
            # Calculate statistics
            def count_tasks(tasks: List[Dict[str, Any]]) -> Dict[str, int]:
                stats = {"total": 0, "backlog": 0, "todo": 0, "in_progress": 0, "completed": 0, "cancelled": 0}
                
                for task in tasks:
                    stats["total"] += 1
                    status = task.get("status", "backlog")
                    if status in stats:
                        stats[status] += 1
                        
                    # Count children
                    child_stats = count_tasks(task.get("children", []))
                    for key in stats:
                        stats[key] += child_stats[key]
                        
                return stats
                
            statistics = count_tasks(hierarchy)
            
            response = {
                "success": True,
                "root_task_id": root_task_id,
                "max_depth": max_depth,
                "include_completed": include_completed,
                "include_cancelled": include_cancelled,
                "statistics": statistics,
                "hierarchy": hierarchy
            }
            
            return [TextContent(type="text", text=json.dumps(response, indent=2))]
            
        except Exception as e:
            logger.error(f"Error getting task hierarchy: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "message": "Failed to get task hierarchy"
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
            
    async def cleanup(self) -> None:
        """Cleanup search and discovery tools."""
        logger.info("Cleaning up search and discovery tools...")