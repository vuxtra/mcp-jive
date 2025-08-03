"""MCP Client Tools.

Implements comprehensive MCP tools for AI agents to interact with the MCP Jive system.
Provides task management, search and discovery, workflow execution, and progress tracking.

Critical Architectural Constraint: The MCP Client is SOLELY RESPONSIBLE for all local
file access. The MCP Server never directly accesses client code projects or local
file systems. All file operations are performed by the MCP Client and communicated
to the server through the MCP protocol.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import json
from enum import Enum

from mcp.types import Tool, TextContent
from ..error_utils import ErrorHandler, ValidationError, with_error_handling
from pydantic import BaseModel, Field

from ..config import ServerConfig
from mcp_jive.lancedb_manager import LanceDBManager
from ..models.workflow import WorkItem, WorkItemType, WorkItemStatus, Priority
from ..utils.identifier_resolver import IdentifierResolver

logger = logging.getLogger(__name__)


class SearchType(str, Enum):
    """Search type enumeration."""
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"


class ExecutionStatus(str, Enum):
    """Execution status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkItemSearchResult(BaseModel):
    """Work item search result model."""
    work_item: WorkItem
    relevance_score: float = Field(ge=0.0, le=1.0)
    match_highlights: List[str] = Field(default_factory=list)


class ExecutionResult(BaseModel):
    """Execution result model."""
    execution_id: str
    status: ExecutionStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class ProgressReport(BaseModel):
    """Progress report model."""
    work_item_id: str
    completion_percentage: float = Field(ge=0.0, le=100.0)
    completed_children: int = Field(ge=0)
    total_children: int = Field(ge=0)
    estimated_completion: Optional[datetime] = None


class DetailedProgressReport(BaseModel):
    """Detailed progress report model."""
    scope: str
    total_work_items: int
    completed_work_items: int
    in_progress_work_items: int
    blocked_work_items: int
    overall_completion_percentage: float = Field(ge=0.0, le=100.0)
    progress_by_type: Dict[str, ProgressReport]
    metrics: Optional[Dict[str, Any]] = None
    generated_at: datetime = Field(default_factory=datetime.now)


class MCPClientTools:
    """MCP Client Tools implementation."""
    
    def __init__(self, config: ServerConfig, lancedb_manager: LanceDBManager):
        self.config = config
        self.lancedb_manager = lancedb_manager
        self.identifier_resolver = IdentifierResolver(lancedb_manager)
        self._execution_cache: Dict[str, ExecutionResult] = {}
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
        """Initialize MCP client tools."""
        logger.info("Initializing MCP client tools...")
        
    async def get_tools(self) -> List[Tool]:
        """Get all MCP client tools."""
        return [
            # Core Work Item Management Tools (5 tools)
            Tool(
                name="jive_create_work_item",
                description="Jive: Create a new agile work item (Initiative/Epic/Feature/Story/Task)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": ["initiative", "epic", "feature", "story", "task"],
                            "description": "Type of work item to create"
                        },
                        "title": {
                            "type": "string",
                            "description": "Work item title"
                        },
                        "description": {
                            "type": "string",
                            "description": "Work item description"
                        },
                        "parent_id": {
                            "type": "string",
                            "description": "Parent work item ID for hierarchy"
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["low", "medium", "high", "critical"],
                            "description": "Work item priority",
                            "default": "medium"
                        },
                        "acceptance_criteria": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Acceptance criteria for the work item"
                        },
                        "effort_estimate": {
                            "type": "number",
                            "description": "Effort estimate in story points or hours"
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Tags for categorization"
                        }
                    },
                    "required": ["type", "title", "description"]
                }
            ),
            Tool(
                name="jive_get_work_item",
                description="Jive: Retrieve work item details by ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "work_item_id": {
                            "type": "string",
                            "description": "Work item identifier - can be exact UUID, exact title, or keywords for search"
                        },
                        "include_children": {
                            "type": "boolean",
                            "description": "Whether to include child work items",
                            "default": False
                        },
                        "include_dependencies": {
                            "type": "boolean",
                            "description": "Whether to include dependencies",
                            "default": False
                        }
                    },
                    "required": ["work_item_id"]
                }
            ),
            Tool(
                name="jive_update_work_item",
                description="Jive: Update work item properties, status, and relationships",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "work_item_id": {
                            "type": "string",
                            "description": "Work item identifier - can be exact UUID, exact title, or keywords for search"
                        },
                        "updates": {
                            "type": "object",
                            "description": "Updates to apply to the work item",
                            "properties": {
                                "title": {"type": "string"},
                                "description": {"type": "string"},
                                "status": {
                                    "type": "string",
                                    "enum": ["not_started", "in_progress", "completed", "blocked", "cancelled"]
                                },
                                "priority": {
                                    "type": "string",
                                    "enum": ["low", "medium", "high", "critical"]
                                },
                                "acceptance_criteria": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "effort_estimate": {"type": "number"},
                                "tags": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                }
                            }
                        }
                    },
                    "required": ["work_item_id", "updates"]
                }
            ),
            Tool(
                name="jive_list_work_items",
                description="Jive: List work items with filtering and pagination",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "filters": {
                            "type": "object",
                            "description": "Filters to apply",
                            "properties": {
                                "type": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "status": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "priority": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "parent_id": {"type": "string"},
                                "tags": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                }
                            }
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of items to return",
                            "default": 50,
                            "minimum": 1,
                            "maximum": 1000
                        },
                        "offset": {
                            "type": "integer",
                            "description": "Number of items to skip",
                            "default": 0,
                            "minimum": 0
                        },
                        "sort_by": {
                            "type": "string",
                            "enum": ["created_at", "updated_at", "priority", "title"],
                            "description": "Field to sort by",
                            "default": "updated_at"
                        },
                        "sort_order": {
                            "type": "string",
                            "enum": ["asc", "desc"],
                            "description": "Sort order",
                            "default": "desc"
                        }
                    }
                }
            ),
            Tool(
                name="jive_search_work_items",
                description="Jive: Semantic and keyword search across work items",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "search_type": {
                            "type": "string",
                            "enum": ["semantic", "keyword", "hybrid"],
                            "description": "Type of search to perform",
                            "default": "semantic"
                        },
                        "filters": {
                            "type": "object",
                            "description": "Additional filters to apply",
                            "properties": {
                                "type": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "status": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "priority": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                }
                            }
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 100
                        }
                    },
                    "required": ["query"]
                }
            )
        ]
        
    async def handle_tool_call(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle tool calls for MCP client tools."""
        if name == "jive_create_work_item":
            return await self._create_work_item(arguments)
        elif name == "jive_get_work_item":
            return await self._get_work_item(arguments)
        elif name == "jive_update_work_item":
            return await self._update_work_item(arguments)
        elif name == "jive_list_work_items":
            return await self._list_work_items(arguments)
        elif name == "jive_search_work_items":
            return await self._search_work_items(arguments)
        else:
            raise ValidationError("Unknown MCP client tool: {name}", "parameter", None)
            
    async def _create_work_item(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Create a new work item."""
        try:
            logger.info(f"Creating work item with arguments: {arguments}")
            # Generate work item ID
            work_item_id = str(uuid.uuid4())
            logger.info(f"Generated work item ID: {work_item_id}")
            
            # Prepare work item data with proper enum conversions
            work_item_data = {
                "id": work_item_id,
                "type": WorkItemType(arguments["type"]),
                "title": arguments["title"],
                "description": arguments["description"],
                "parent_id": arguments.get("parent_id"),
                "project_id": "default_project",  # Required field
                "priority": Priority(arguments.get("priority", "medium")),
                "status": WorkItemStatus.BACKLOG,
                "reporter": "mcp_client",  # Required field
                "acceptance_criteria": arguments.get("acceptance_criteria", []),
                "effort_estimate": arguments.get("effort_estimate"),
                "tags": arguments.get("tags", []),
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "metadata": {
                    "created_by": "mcp_client",
                    "version": 1
                }
            }
            
            # Convert enum values to strings for Weaviate storage
            import copy
            weaviate_data = copy.deepcopy(work_item_data)  # Use deep copy to avoid reference issues
            weaviate_data["type"] = work_item_data["type"].value
            weaviate_data["priority"] = work_item_data["priority"].value
            weaviate_data["status"] = work_item_data["status"].value
            
            # Add item_id field for MCP Jive LanceDB compatibility
            weaviate_data["item_id"] = work_item_id
            weaviate_data["item_type"] = work_item_data["type"].value  # Ensure item_type is set
            
            # Convert datetime objects to RFC3339 strings with timezone
            if "created_at" in weaviate_data:
                weaviate_data["created_at"] = weaviate_data["created_at"].isoformat() + "Z"
            if "updated_at" in weaviate_data:
                weaviate_data["updated_at"] = weaviate_data["updated_at"].isoformat() + "Z"
            
            # Convert metadata dict to JSON string for Weaviate
            import json
            if "metadata" in weaviate_data and isinstance(weaviate_data["metadata"], dict):
                weaviate_data["metadata"] = json.dumps(weaviate_data["metadata"])
                
            # Convert dict fields to JSON strings, but preserve arrays for TEXT_ARRAY fields
            for key, value in weaviate_data.items():
                if isinstance(value, dict) and key != "metadata":
                    weaviate_data[key] = json.dumps(value)
                elif isinstance(value, list) and key not in ["tags", "dependencies", "acceptance_criteria"]:
                    weaviate_data[key] = json.dumps(value)
                # Keep tags, dependencies, and acceptance_criteria as arrays for TEXT_ARRAY fields
                    
            logger.info(f"Converted data for Weaviate: {weaviate_data}")
            
            # Store in Weaviate
            logger.info(f"About to store work item data: {weaviate_data}")
            logger.info(f"Data keys: {list(weaviate_data.keys())}")
            logger.info(f"Has item_id: {'item_id' in weaviate_data}")
            logger.info(f"Has item_type: {'item_type' in weaviate_data}")
            await self.lancedb_manager.store_work_item(weaviate_data)
            logger.info(f"Successfully stored work item in Weaviate")

            # Create WorkItem object for response
            try:
                logger.info(f"Creating WorkItem with data: {work_item_data}")
                work_item = WorkItem(**work_item_data)
                logger.info(f"Successfully created WorkItem: {work_item.id}")
            except Exception as validation_error:
                logger.error(f"WorkItem validation error: {validation_error}")
                logger.error(f"Work item data that failed: {work_item_data}")
                logger.error(f"Error type: {type(validation_error)}")
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
                raise ValueError(f"WorkItem validation failed: {validation_error}")
            
            result = {
                "success": True,
                "work_item": work_item.dict(),
                "message": f"Created {arguments['type']} work item: {arguments['title']}"
            }
            
            logger.info(f"Created work item {work_item_id}: {arguments['title']}")
            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
            
        except Exception as e:
            logger.error(f"Error creating work item: {e}")
            logger.error(f"Error type: {type(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            
            # Check if this is a KeyError for 'id'
            if isinstance(e, KeyError) and str(e) == "'id'":
                logger.error("KeyError for 'id' field detected - this suggests the work_item_data is missing the 'id' key")
                logger.error(f"Current work_item_data keys: {list(work_item_data.keys()) if 'work_item_data' in locals() else 'work_item_data not available'}")
            
            error_response = {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": datetime.now().isoformat()
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
            
    async def _get_work_item(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get work item details by flexible identifier."""
        try:
            identifier = arguments["work_item_id"]
            include_children = arguments.get("include_children", False)
            include_dependencies = arguments.get("include_dependencies", False)
            
            # Resolve flexible identifier to UUID
            work_item_id = await self.identifier_resolver.resolve_work_item_id(identifier)
            
            if not work_item_id:
                # Get resolution info for better error message
                resolution_info = await self.identifier_resolver.get_resolution_info(identifier)
                candidates = resolution_info.get("candidates", [])
                
                error_response = {
                    "success": False,
                    "error": f"Could not resolve work item identifier: '{identifier}'",
                    "identifier_type": "UUID" if resolution_info.get("is_uuid") else "title/keywords",
                    "suggestions": [c.get("title") for c in candidates[:3]] if candidates else [],
                    "timestamp": datetime.now().isoformat()
                }
                return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
            
            # Get work item from Weaviate using resolved UUID
            work_item_data = await self.lancedb_manager.get_work_item(work_item_id)
            
            if not work_item_data:
                error_response = {
                    "success": False,
                    "error": f"Work item {work_item_id} not found in database",
                    "resolved_from": identifier,
                    "timestamp": datetime.now().isoformat()
                }
                return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
            
            result = {
                "success": True,
                "work_item": work_item_data,
                "resolved_from": identifier if identifier != work_item_id else None
            }
            
            # Include children if requested
            if include_children:
                children = await self.lancedb_manager.get_work_item_children(work_item_id)
                result["children"] = children
                result["child_count"] = len(children)
                
            # Include dependencies if requested
            if include_dependencies:
                dependencies = await self.lancedb_manager.get_work_item_dependencies(work_item_id)
                result["dependencies"] = dependencies
                result["dependency_count"] = len(dependencies)
            
            logger.info(f"Retrieved work item {work_item_id} (resolved from '{identifier}')")
            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
            
        except Exception as e:
            logger.error(f"Error retrieving work item: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
            
    async def _update_work_item(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Update work item properties using flexible identifier."""
        try:
            identifier = arguments["work_item_id"]
            updates = arguments["updates"]
            
            # Resolve flexible identifier to UUID
            work_item_id = await self.identifier_resolver.resolve_work_item_id(identifier)
            
            if not work_item_id:
                # Get resolution info for better error message
                resolution_info = await self.identifier_resolver.get_resolution_info(identifier)
                candidates = resolution_info.get("candidates", [])
                
                error_response = {
                    "success": False,
                    "error": f"Could not resolve work item identifier: '{identifier}'",
                    "identifier_type": "UUID" if resolution_info.get("is_uuid") else "title/keywords",
                    "suggestions": [c.get("title") for c in candidates[:3]] if candidates else [],
                    "timestamp": datetime.now().isoformat()
                }
                return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
            
            # Add updated timestamp
            updates["updated_at"] = datetime.now().isoformat()
            
            # Update in Weaviate using resolved UUID
            updated_work_item = await self.lancedb_manager.update_work_item(work_item_id, updates)
            
            if not updated_work_item:
                error_response = {
                    "success": False,
                    "error": f"Work item {work_item_id} not found in database",
                    "resolved_from": identifier,
                    "timestamp": datetime.now().isoformat()
                }
                return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
            
            result = {
                "success": True,
                "work_item": updated_work_item,
                "message": f"Updated work item {work_item_id}",
                "resolved_from": identifier if identifier != work_item_id else None
            }
            
            logger.info(f"Updated work item {work_item_id} (resolved from '{identifier}')")
            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
            
        except Exception as e:
            logger.error(f"Error updating work item: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
            
    async def _list_work_items(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """List work items with filtering and pagination."""
        try:
            filters = arguments.get("filters", {})
            limit = arguments.get("limit", 50)
            offset = arguments.get("offset", 0)
            sort_by = arguments.get("sort_by", "updated_at")
            sort_order = arguments.get("sort_order", "desc")
            
            # Query Weaviate
            work_items = await self.lancedb_manager.list_work_items(
                filters=filters,
                limit=limit,
                offset=offset,
                sort_by=sort_by,
                sort_order=sort_order
            )
            
            result = {
                "success": True,
                "work_items": work_items,
                "count": len(work_items),
                "filters": filters,
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "sort_by": sort_by,
                    "sort_order": sort_order
                }
            }
            
            logger.info(f"Listed {len(work_items)} work items")
            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
            
        except Exception as e:
            logger.error(f"Error listing work items: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
            
    async def _search_work_items(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Search work items using semantic or keyword search."""
        try:
            query = arguments["query"]
            search_type = arguments.get("search_type", "semantic")
            filters = arguments.get("filters", {})
            limit = arguments.get("limit", 10)
            
            # Perform search in Weaviate
            search_results = await self.lancedb_manager.search_work_items(
                query=query,
                search_type=search_type,
                filters=filters,
                limit=limit
            )
            
            result = {
                "success": True,
                "query": query,
                "search_type": search_type,
                "results": search_results,
                "count": len(search_results),
                "filters": filters
            }
            
            logger.info(f"Search '{query}' returned {len(search_results)} results")
            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
            
        except Exception as e:
            logger.error(f"Error searching work items: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
            
    async def cleanup(self) -> None:
        """Cleanup MCP client tools."""
        logger.info("Cleaning up MCP client tools...")
        self._execution_cache.clear()