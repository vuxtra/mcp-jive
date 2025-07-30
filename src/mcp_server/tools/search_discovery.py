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
from ..database import WeaviateManager

logger = logging.getLogger(__name__)


class SearchDiscoveryTools:
    """Search and discovery tool implementations."""
    
    def __init__(self, config: ServerConfig, weaviate_manager: WeaviateManager):
        self.config = config
        self.weaviate_manager = weaviate_manager
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
            collection = self.weaviate_manager.get_collection("Task")
            query_builder = collection.query
            
            # Build search query
            filters = []
            
            # Text search
            if "query" in arguments and arguments["query"]:
                # Use hybrid search for better results
                query_builder = query_builder.hybrid(
                    query=arguments["query"],
                    alpha=0.7  # Balance between keyword and vector search
                )
                
            # Status filter
            if "status" in arguments:
                filters.append(
                    collection.query.Filter.by_property("status").equal(arguments["status"])
                )
                
            # Priority filter
            if "priority" in arguments:
                filters.append(
                    collection.query.Filter.by_property("priority").equal(arguments["priority"])
                )
                
            # Tags filter
            if "tags" in arguments and arguments["tags"]:
                tag_filters = []
                for tag in arguments["tags"]:
                    tag_filters.append(
                        collection.query.Filter.by_property("tags").contains_any([tag])
                    )
                if tag_filters:
                    filters.append(collection.query.Filter.any_of(tag_filters))
                    
            # Date filters
            if "created_after" in arguments:
                filters.append(
                    collection.query.Filter.by_property("created_at").greater_than(arguments["created_after"])
                )
                
            if "created_before" in arguments:
                filters.append(
                    collection.query.Filter.by_property("created_at").less_than(arguments["created_before"])
                )
                
            # Apply filters
            if filters:
                if len(filters) == 1:
                    query_builder = query_builder.with_where(filters[0])
                else:
                    query_builder = query_builder.with_where(collection.query.Filter.all_of(filters))
                    
            # Set limit
            limit = arguments.get("limit", 20)
            query_builder = query_builder.limit(limit)
            
            # Execute query
            results = query_builder.objects
            
            # Format results
            tasks = []
            for result in results:
                task_data = result.properties
                task_data["id"] = str(result.uuid)
                if hasattr(result, 'metadata') and result.metadata:
                    task_data["score"] = result.metadata.score
                tasks.append(task_data)
                
            response = {
                "success": True,
                "query": arguments.get("query", ""),
                "filters": {k: v for k, v in arguments.items() if k != "query" and k != "limit"},
                "total_results": len(tasks),
                "limit": limit,
                "tasks": tasks
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
                collection_name = {
                    "task": "Task",
                    "work_item": "WorkItem",
                    "search_index": "SearchIndex"
                }.get(content_type)
                
                if not collection_name:
                    continue
                    
                try:
                    collection = self.weaviate_manager.get_collection(collection_name)
                    
                    # Perform hybrid search
                    results = collection.query.hybrid(
                        query=query,
                        alpha=0.7
                    ).with_limit(50).limit(limit // len(content_types) + 1).objects
                    
                    # Format results
                    for result in results:
                        result_data = {
                            "id": str(result.uuid),
                            "type": content_type,
                            "properties": result.properties
                        }
                        
                        if include_score and hasattr(result, 'metadata') and result.metadata:
                            result_data["score"] = result.metadata.score
                            
                        all_results.append(result_data)
                        
                except Exception as e:
                    logger.warning(f"Error searching in {collection_name}: {e}")
                    continue
                    
            # Sort by score if available
            if include_score:
                all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
                
            # Limit total results
            all_results = all_results[:limit]
            
            response = {
                "success": True,
                "query": query,
                "content_types": content_types,
                "total_results": len(all_results),
                "limit": limit,
                "include_score": include_score,
                "results": all_results
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
            collection = self.weaviate_manager.get_collection("Task")
            query_builder = collection.query
            
            # Build filters
            filters = []
            
            if "status" in arguments:
                filters.append(
                    collection.query.Filter.by_property("status").equal(arguments["status"])
                )
                
            if "priority" in arguments:
                filters.append(
                    collection.query.Filter.by_property("priority").equal(arguments["priority"])
                )
                
            if "parent_id" in arguments:
                if arguments["parent_id"] is None:
                    filters.append(
                        collection.query.Filter.by_property("parent_id").is_null(True)
                    )
                else:
                    filters.append(
                        collection.query.Filter.by_property("parent_id").equal(arguments["parent_id"])
                    )
                    
            # Apply filters
            if filters:
                if len(filters) == 1:
                    query_builder = query_builder.with_where(filters[0])
                else:
                    query_builder = query_builder.with_where(collection.query.Filter.all_of(filters))
                    
            # Apply sorting
            sort_by = arguments.get("sort_by", "created_at")
            sort_order = arguments.get("sort_order", "desc")
            
            if sort_order == "desc":
                query_builder = query_builder.sort(collection.query.Sort.by_property(sort_by, ascending=False))
            else:
                query_builder = query_builder.sort(collection.query.Sort.by_property(sort_by, ascending=True))
                
            # Apply pagination
            limit = arguments.get("limit", 20)
            offset = arguments.get("offset", 0)
            
            query_builder = query_builder.limit(limit).offset(offset)
            
            # Execute query
            results = query_builder.objects
            
            # Format results
            tasks = []
            for result in results:
                task_data = result.properties
                task_data["id"] = str(result.uuid)
                tasks.append(task_data)
                
            response = {
                "success": True,
                "filters": {k: v for k, v in arguments.items() if k not in ["sort_by", "sort_order", "limit", "offset"]},
                "sort_by": sort_by,
                "sort_order": sort_order,
                "limit": limit,
                "offset": offset,
                "total_results": len(tasks),
                "tasks": tasks
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
            
            collection = self.weaviate_manager.get_collection("Task")
            
            async def get_task_children(parent_id: Optional[str], current_depth: int) -> List[Dict[str, Any]]:
                if current_depth >= max_depth:
                    return []
                    
                # Build query for children
                query_builder = collection.query
                
                if parent_id is None:
                    query_builder = query_builder.with_where(
                        collection.query.Filter.by_property("parent_id").is_null(True)
                    )
                else:
                    query_builder = query_builder.with_where(
                        collection.query.Filter.by_property("parent_id").equal(parent_id)
                    )
                    
                # Apply status filters
                status_filters = []
                if not include_completed:
                    status_filters.append(
                        collection.query.Filter.by_property("status").not_equal("completed")
                    )
                if not include_cancelled:
                    status_filters.append(
                        collection.query.Filter.by_property("status").not_equal("cancelled")
                    )
                    
                if status_filters:
                    query_builder = query_builder.with_where(
                        collection.query.Filter.all_of(status_filters)
                    )
                    
                # Execute query
                results = query_builder.objects
                
                # Build hierarchy
                tasks = []
                for result in results:
                    task_data = result.properties
                    task_data["id"] = str(result.uuid)
                    task_data["depth"] = current_depth
                    
                    # Get children recursively
                    children = await get_task_children(str(result.uuid), current_depth + 1)
                    task_data["children"] = children
                    task_data["child_count"] = len(children)
                    
                    tasks.append(task_data)
                    
                return tasks
                
            # Get hierarchy starting from root
            hierarchy = await get_task_children(root_task_id, 0)
            
            # Calculate statistics
            def count_tasks(tasks: List[Dict[str, Any]]) -> Dict[str, int]:
                stats = {"total": 0, "todo": 0, "in_progress": 0, "completed": 0, "cancelled": 0}
                
                for task in tasks:
                    stats["total"] += 1
                    status = task.get("status", "todo")
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