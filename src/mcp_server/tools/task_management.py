"""Task Management Tools.

Implements the 4 task management MCP tools:
- create_task: Create new tasks
- update_task: Update existing tasks
- delete_task: Delete tasks
- get_task: Retrieve task details
"""

import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from mcp.types import Tool, TextContent

from ..config import ServerConfig
from ..database import WeaviateManager

logger = logging.getLogger(__name__)


class TaskManagementTools:
    """Task management tool implementations."""
    
    def __init__(self, config: ServerConfig, weaviate_manager: WeaviateManager):
        self.config = config
        self.weaviate_manager = weaviate_manager
        
    async def initialize(self) -> None:
        """Initialize task management tools."""
        logger.info("Initializing task management tools...")
        
    async def get_tools(self) -> List[Tool]:
        """Get all task management tools."""
        return [
            Tool(
                name="create_task",
                description="Create a new task with title, description, and metadata",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Task title"
                        },
                        "description": {
                            "type": "string",
                            "description": "Task description"
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["low", "medium", "high", "urgent"],
                            "description": "Task priority level",
                            "default": "medium"
                        },
                        "status": {
                            "type": "string",
                            "enum": ["todo", "in_progress", "completed", "cancelled"],
                            "description": "Task status",
                            "default": "todo"
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Task tags for categorization"
                        },
                        "due_date": {
                            "type": "string",
                            "format": "date-time",
                            "description": "Task due date (ISO format)"
                        },
                        "parent_id": {
                            "type": "string",
                            "description": "Parent task ID for hierarchical tasks"
                        }
                    },
                    "required": ["title"]
                }
            ),
            Tool(
                name="update_task",
                description="Update an existing task",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "Task ID to update"
                        },
                        "title": {
                            "type": "string",
                            "description": "Updated task title"
                        },
                        "description": {
                            "type": "string",
                            "description": "Updated task description"
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["low", "medium", "high", "urgent"],
                            "description": "Updated task priority"
                        },
                        "status": {
                            "type": "string",
                            "enum": ["todo", "in_progress", "completed", "cancelled"],
                            "description": "Updated task status"
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Updated task tags"
                        },
                        "due_date": {
                            "type": "string",
                            "format": "date-time",
                            "description": "Updated due date"
                        }
                    },
                    "required": ["task_id"]
                }
            ),
            Tool(
                name="delete_task",
                description="Delete a task and optionally its subtasks",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "Task ID to delete"
                        },
                        "delete_subtasks": {
                            "type": "boolean",
                            "description": "Whether to delete all subtasks",
                            "default": False
                        }
                    },
                    "required": ["task_id"]
                }
            ),
            Tool(
                name="get_task",
                description="Retrieve detailed information about a task",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "Task ID to retrieve"
                        },
                        "include_subtasks": {
                            "type": "boolean",
                            "description": "Whether to include subtask information",
                            "default": False
                        }
                    },
                    "required": ["task_id"]
                }
            )
        ]
        
    async def handle_tool_call(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle tool calls for task management."""
        if name == "create_task":
            return await self._create_task(arguments)
        elif name == "update_task":
            return await self._update_task(arguments)
        elif name == "delete_task":
            return await self._delete_task(arguments)
        elif name == "get_task":
            return await self._get_task(arguments)
        else:
            raise ValueError(f"Unknown task management tool: {name}")
            
    async def _create_task(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Create a new task."""
        try:
            # Generate task ID
            task_id = str(uuid.uuid4())
            
            # Prepare task data
            task_data = {
                "id": task_id,
                "title": arguments["title"],
                "description": arguments.get("description", ""),
                "priority": arguments.get("priority", "medium"),
                "status": arguments.get("status", "todo"),
                "tags": arguments.get("tags", []),
                "due_date": arguments.get("due_date"),
                "parent_id": arguments.get("parent_id"),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "metadata": {
                    "created_by": "mcp_client",
                    "version": 1
                }
            }
            
            # Store in Weaviate
            collection = self.weaviate_manager.get_collection("Task")
            result = collection.data.insert(task_data)
            
            response = {
                "success": True,
                "task_id": task_id,
                "message": f"Task '{arguments['title']}' created successfully",
                "task": task_data
            }
            
            return [TextContent(type="text", text=json.dumps(response, indent=2))]
            
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "message": "Failed to create task"
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
            
    async def _update_task(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Update an existing task."""
        try:
            task_id = arguments["task_id"]
            
            # Get existing task
            collection = self.weaviate_manager.get_collection("Task")
            existing_task = collection.query.fetch_object_by_id(task_id)
            
            if not existing_task:
                error_response = {
                    "success": False,
                    "error": f"Task with ID {task_id} not found",
                    "message": "Task not found"
                }
                return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
                
            # Update task data
            update_data = {"updated_at": datetime.now().isoformat()}
            
            for field in ["title", "description", "priority", "status", "tags", "due_date"]:
                if field in arguments:
                    update_data[field] = arguments[field]
                    
            # Update in Weaviate
            collection.data.update(
                uuid=task_id,
                properties=update_data
            )
            
            # Get updated task
            updated_task = collection.query.fetch_object_by_id(task_id)
            
            response = {
                "success": True,
                "task_id": task_id,
                "message": "Task updated successfully",
                "task": updated_task.properties if updated_task else None
            }
            
            return [TextContent(type="text", text=json.dumps(response, indent=2))]
            
        except Exception as e:
            logger.error(f"Error updating task: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "message": "Failed to update task"
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
            
    async def _delete_task(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Delete a task."""
        try:
            task_id = arguments["task_id"]
            delete_subtasks = arguments.get("delete_subtasks", False)
            
            collection = self.weaviate_manager.get_collection("Task")
            
            # Check if task exists
            existing_task = collection.query.fetch_object_by_id(task_id)
            if not existing_task:
                error_response = {
                    "success": False,
                    "error": f"Task with ID {task_id} not found",
                    "message": "Task not found"
                }
                return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
                
            deleted_count = 1
            
            # Delete subtasks if requested
            if delete_subtasks:
                subtasks = collection.query.where(
                    collection.query.Filter.by_property("parent_id").equal(task_id)
                ).objects
                
                for subtask in subtasks:
                    collection.data.delete_by_id(subtask.uuid)
                    deleted_count += 1
                    
            # Delete main task
            collection.data.delete_by_id(task_id)
            
            response = {
                "success": True,
                "task_id": task_id,
                "deleted_count": deleted_count,
                "message": f"Deleted {deleted_count} task(s) successfully"
            }
            
            return [TextContent(type="text", text=json.dumps(response, indent=2))]
            
        except Exception as e:
            logger.error(f"Error deleting task: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "message": "Failed to delete task"
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
            
    async def _get_task(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get task details."""
        try:
            task_id = arguments["task_id"]
            include_subtasks = arguments.get("include_subtasks", False)
            
            collection = self.weaviate_manager.get_collection("Task")
            
            # Get main task
            task = collection.query.fetch_object_by_id(task_id)
            
            if not task:
                error_response = {
                    "success": False,
                    "error": f"Task with ID {task_id} not found",
                    "message": "Task not found"
                }
                return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
                
            task_data = task.properties
            task_data["id"] = str(task.uuid)
            
            # Get subtasks if requested
            subtasks = []
            if include_subtasks:
                subtask_objects = collection.query.where(
                    collection.query.Filter.by_property("parent_id").equal(task_id)
                ).objects
                
                for subtask in subtask_objects:
                    subtask_data = subtask.properties
                    subtask_data["id"] = str(subtask.uuid)
                    subtasks.append(subtask_data)
                    
            response = {
                "success": True,
                "task": task_data,
                "subtasks": subtasks if include_subtasks else None,
                "subtask_count": len(subtasks) if include_subtasks else None
            }
            
            return [TextContent(type="text", text=json.dumps(response, indent=2))]
            
        except Exception as e:
            logger.error(f"Error getting task: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "message": "Failed to get task"
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
            
    async def cleanup(self) -> None:
        """Cleanup task management tools."""
        logger.info("Cleaning up task management tools...")