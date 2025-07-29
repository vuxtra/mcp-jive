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
from pydantic import BaseModel, Field

from ..config import ServerConfig
from ..database import WeaviateManager
from ..models.workflow import WorkItem, WorkItemType, WorkItemStatus, Priority

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
    
    def __init__(self, config: ServerConfig, weaviate_manager: WeaviateManager):
        self.config = config
        self.weaviate_manager = weaviate_manager
        self._execution_cache: Dict[str, ExecutionResult] = {}
        
    async def initialize(self) -> None:
        """Initialize MCP client tools."""
        logger.info("Initializing MCP client tools...")
        
    async def get_tools(self) -> List[Tool]:
        """Get all MCP client tools."""
        return [
            # Core Work Item Management Tools (5 tools)
            Tool(
                name="create_work_item",
                description="Create a new agile work item (Initiative/Epic/Feature/Story/Task)",
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
                name="get_work_item",
                description="Retrieve work item details by ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "work_item_id": {
                            "type": "string",
                            "description": "Work item ID to retrieve"
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
                name="update_work_item",
                description="Update work item properties, status, and relationships",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "work_item_id": {
                            "type": "string",
                            "description": "Work item ID to update"
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
                name="list_work_items",
                description="List work items with filtering and pagination",
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
                name="search_work_items",
                description="Semantic and keyword search across work items",
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
        if name == "create_work_item":
            return await self._create_work_item(arguments)
        elif name == "get_work_item":
            return await self._get_work_item(arguments)
        elif name == "update_work_item":
            return await self._update_work_item(arguments)
        elif name == "list_work_items":
            return await self._list_work_items(arguments)
        elif name == "search_work_items":
            return await self._search_work_items(arguments)
        else:
            raise ValueError(f"Unknown MCP client tool: {name}")
            
    async def _create_work_item(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Create a new work item."""
        try:
            # Generate work item ID
            work_item_id = str(uuid.uuid4())
            
            # Prepare work item data
            work_item_data = {
                "id": work_item_id,
                "type": arguments["type"],
                "title": arguments["title"],
                "description": arguments["description"],
                "parent_id": arguments.get("parent_id"),
                "priority": arguments.get("priority", "medium"),
                "status": "not_started",
                "acceptance_criteria": arguments.get("acceptance_criteria", []),
                "effort_estimate": arguments.get("effort_estimate"),
                "tags": arguments.get("tags", []),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "metadata": {
                    "created_by": "mcp_client",
                    "version": 1
                }
            }
            
            # Store in Weaviate
            await self.weaviate_manager.store_work_item(work_item_data)
            
            # Create WorkItem object for response
            work_item = WorkItem(**work_item_data)
            
            result = {
                "success": True,
                "work_item": work_item.dict(),
                "message": f"Created {arguments['type']} work item: {arguments['title']}"
            }
            
            logger.info(f"Created work item {work_item_id}: {arguments['title']}")
            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
            
        except Exception as e:
            logger.error(f"Error creating work item: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
            
    async def _get_work_item(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Retrieve a work item by ID."""
        try:
            work_item_id = arguments["work_item_id"]
            include_children = arguments.get("include_children", False)
            include_dependencies = arguments.get("include_dependencies", False)
            
            # Retrieve from Weaviate
            work_item_data = await self.weaviate_manager.get_work_item(work_item_id)
            
            if not work_item_data:
                error_response = {
                    "success": False,
                    "error": f"Work item not found: {work_item_id}",
                    "timestamp": datetime.now().isoformat()
                }
                return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
            
            result = {
                "success": True,
                "work_item": work_item_data
            }
            
            # Include children if requested
            if include_children:
                children = await self.weaviate_manager.get_work_item_children(work_item_id)
                result["children"] = children
                
            # Include dependencies if requested
            if include_dependencies:
                dependencies = await self.weaviate_manager.get_work_item_dependencies(work_item_id)
                result["dependencies"] = dependencies
            
            logger.info(f"Retrieved work item {work_item_id}")
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
        """Update a work item."""
        try:
            work_item_id = arguments["work_item_id"]
            updates = arguments["updates"]
            
            # Add updated timestamp
            updates["updated_at"] = datetime.now().isoformat()
            
            # Update in Weaviate
            updated_work_item = await self.weaviate_manager.update_work_item(work_item_id, updates)
            
            if not updated_work_item:
                error_response = {
                    "success": False,
                    "error": f"Work item not found: {work_item_id}",
                    "timestamp": datetime.now().isoformat()
                }
                return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
            
            result = {
                "success": True,
                "work_item": updated_work_item,
                "message": f"Updated work item {work_item_id}"
            }
            
            logger.info(f"Updated work item {work_item_id}")
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
            work_items = await self.weaviate_manager.list_work_items(
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
            search_results = await self.weaviate_manager.search_work_items(
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