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
from datetime import datetime, timezone
import json
import pandas as pd

from ..error_utils import ErrorHandler, ValidationError, with_error_handling

from mcp.types import Tool, TextContent

from ..config import ServerConfig
from mcp_jive.lancedb_manager import LanceDBManager

logger = logging.getLogger(__name__)


class TaskManagementTools:
    """Task management tool implementations."""
    
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
        """Initialize task management tools."""
        logger.info("Initializing task management tools...")
        
    async def get_tools(self) -> List[Tool]:
        """Get all task management tools."""
        return [
            Tool(
                name="jive_create_task",
                description="Jive: Create a new task (development task or work item) with title, description, and metadata",
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
                name="jive_update_task",
                description="Jive: Update an existing task (development task or work item)",
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
                name="jive_delete_task",
                description="Jive: Delete a task (development task or work item) and optionally its subtask (development task or work item)s",
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
                name="jive_get_task",
                description="Jive: Retrieve detailed information about a task (development task or work item)",
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
        if name == "jive_create_task":
            return await self._create_task(arguments)
        elif name == "jive_update_task":
            return await self._update_task(arguments)
        elif name == "jive_delete_task":
            return await self._delete_task(arguments)
        elif name == "jive_get_task":
            return await self._get_task(arguments)
        else:
            raise ValidationError("Unknown task management tool: {name}", "parameter", None)
            
    async def _create_task(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Create a new task."""
        try:
            # Generate task ID
            task_id = str(uuid.uuid4())
            
            # Prepare task data
            # Safely extract arguments to avoid NumPy boolean evaluation errors
            import numpy as np
            
            # Process tags safely to avoid NumPy array boolean evaluation
            if "tags" in arguments:
                tags_value = arguments["tags"]
                if isinstance(tags_value, np.ndarray):
                    tags_value = tags_value.tolist()
                elif hasattr(tags_value, 'tolist') and not isinstance(tags_value, (str, list)):
                    tags_value = tags_value.tolist()
                else:
                    # Handle all other cases (including non-list types)
                    # Avoid boolean evaluation of numpy arrays
                    try:
                        if tags_value is None:
                            tags_value = []
                        elif isinstance(tags_value, list):
                            # Already a list, keep as is
                            pass
                        else:
                            tags_value = list(tags_value)
                    except (TypeError, ValueError):
                        tags_value = []
            else:
                tags_value = []
            
            # Safe extraction to avoid NumPy boolean evaluation
            description_value = ""
            if "description" in arguments:
                description_value = arguments["description"]
            
            priority_value = "medium"
            if "priority" in arguments:
                priority_value = arguments["priority"]
            
            status_value = "todo"
            if "status" in arguments:
                status_value = arguments["status"]
            
            due_date_value = None
            if "due_date" in arguments:
                due_date_value = arguments["due_date"]
            
            parent_id_value = None
            if "parent_id" in arguments:
                parent_id_value = arguments["parent_id"]
            
            task_data = {
                "id": task_id,
                "item_id": task_id,
                "title": arguments["title"],
                "description": description_value,
                "item_type": "task",
                "priority": priority_value,
                "status": status_value,
                "tags": tags_value,
                "parent_id": parent_id_value,
                "metadata": json.dumps({
                    "created_by": "mcp_client",
                    "version": 1,
                    "due_date": due_date_value
                })
            }
            
            # Store in LanceDB using the manager (tasks are stored as work items)
            created_task_id = await self.lancedb_manager.create_work_item(task_data)
            
            response = {
                "success": True,
                "task_id": created_task_id,
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
            
            # Get existing task using LanceDB (tasks are stored as work items)
            table = self.lancedb_manager.get_table("WorkItem")
            result = table.search().where(f"id = '{task_id}' AND item_type = 'task'").limit(1).to_pandas()
            
            if len(result) == 0:
                error_response = {
                    "success": False,
                    "error": f"Task with ID {task_id} not found",
                    "message": "Task not found"
                }
                return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
                
            # Get existing task data and handle numpy/pandas types
            import numpy as np
            existing_task_raw = result.iloc[0].to_dict()
            existing_task = {}
            
            logger.info(f"Processing existing task data for task_id: {task_id}")
            
            for k, v in existing_task_raw.items():
                try:
                    logger.info(f"Processing field {k}: type={type(v)}, value={repr(v)}")
                    
                    if k == "vector":
                        continue  # Skip vector field entirely
                    elif isinstance(v, np.ndarray):
                        # Handle numpy arrays - this must come FIRST
                        logger.info(f"Converting numpy array {k} with shape {v.shape}")
                        existing_task[k] = v.tolist()
                    elif isinstance(v, (np.integer, np.floating, np.bool_)):
                        # Handle numpy scalars
                        logger.info(f"Converting numpy scalar {k}")
                        existing_task[k] = v.item()
                    elif k in ['created_at', 'updated_at'] and hasattr(v, 'to_pydatetime'):
                        # Keep datetime objects as datetime for TaskModel
                        existing_task[k] = v.to_pydatetime()
                    elif hasattr(v, 'isoformat'):  # other datetime objects
                        existing_task[k] = v.isoformat()
                    elif hasattr(v, 'tolist') and not isinstance(v, (str, list)):
                        # Other array-like objects
                        existing_task[k] = v.tolist()
                    elif hasattr(pd, 'isna') and pd.isna(v):  # pandas NaN
                        existing_task[k] = None
                    else:
                        existing_task[k] = v
                        
                    logger.info(f"Field {k} converted to: type={type(existing_task[k])}, value={repr(existing_task[k])}")
                    
                except Exception as field_error:
                    logger.error(f"Error processing field {k}: {field_error}")
                    logger.error(f"Field type: {type(v)}, value: {repr(v)}")
                    # Set a safe default value
                    if k == 'tags':
                        existing_task[k] = []
                    elif k in ['created_at', 'updated_at']:
                        existing_task[k] = None
                    else:
                        existing_task[k] = None
            
            # Prepare update data (exclude created_at and updated_at as they're auto-generated by TaskModel)
            # Ensure tags is a proper list of strings
            existing_tags = existing_task.get("tags", [])
            if hasattr(existing_tags, 'tolist'):
                existing_tags = existing_tags.tolist()
            else:
                # Handle all other cases (including non-list types)
                # Avoid boolean evaluation of numpy arrays
                try:
                    if existing_tags is None:
                        existing_tags = []
                    elif isinstance(existing_tags, list):
                        # Already a list, keep as is
                        pass
                    else:
                        existing_tags = list(existing_tags)
                except (TypeError, ValueError):
                    existing_tags = []
            
            # Ensure tags are properly converted to Python list of strings
            if isinstance(existing_tags, list):
                existing_tags = [str(tag) for tag in existing_tags]
            else:
                existing_tags = []
            
            # Process arguments tags to ensure they're also converted from numpy arrays
            # Use explicit check to avoid boolean evaluation of numpy arrays in .get() default
            if "tags" in arguments:
                args_tags = arguments["tags"]
            else:
                args_tags = existing_tags
            if hasattr(args_tags, 'tolist'):
                args_tags = args_tags.tolist()
            else:
                # Handle all other cases (including non-list types)
                # Avoid boolean evaluation of numpy arrays
                try:
                    if args_tags is None:
                        args_tags = []
                    elif isinstance(args_tags, list):
                        # Already a list, keep as is
                        pass
                    else:
                        args_tags = list(args_tags)
                except (TypeError, ValueError):
                    args_tags = []
            
            # Ensure all tags are strings
            if isinstance(args_tags, list):
                args_tags = [str(tag) for tag in args_tags]
            else:
                args_tags = []
            
            # Create update_data with explicit checks to avoid boolean evaluation
            # CRITICAL: Never use conditional expressions with NumPy arrays
            # as this triggers "The truth value of an array with more than one element is ambiguous"
            
            # Safe extraction for update fields
            title_value = existing_task.get("title")
            if "title" in arguments:
                title_value = arguments["title"]
            
            description_value = existing_task.get("description")
            if "description" in arguments:
                description_value = arguments["description"]
            
            priority_value = existing_task.get("priority")
            if "priority" in arguments:
                priority_value = arguments["priority"]
            
            status_value = existing_task.get("status")
            if "status" in arguments:
                status_value = arguments["status"]
            
            update_data = {
                "id": task_id,
                "item_id": task_id,
                "item_type": "task",
                "title": title_value,
                "description": description_value,
                "priority": priority_value,
                "status": status_value,
                "tags": args_tags,
                "parent_id": existing_task.get("parent_id")
            }
            
            # Final safety check: convert any remaining numpy arrays in update_data
            for key, value in update_data.items():
                if hasattr(value, 'tolist'):  # numpy array
                    update_data[key] = value.tolist()
                elif hasattr(value, 'item'):  # numpy scalar
                    update_data[key] = value.item()
            
            # Handle metadata updates
            try:
                metadata = json.loads(existing_task.get("metadata", "{}"))
                if "due_date" in arguments:
                    metadata["due_date"] = arguments["due_date"]
                update_data["metadata"] = json.dumps(metadata)
            except (json.JSONDecodeError, TypeError):
                # Safe metadata creation to avoid NumPy boolean evaluation
                metadata = {}
                if "due_date" in arguments:
                    metadata["due_date"] = arguments["due_date"]
                update_data["metadata"] = json.dumps(metadata)
            
            # Delete old record
            table.delete(f"id = '{task_id}'")
            
            # All numpy arrays should be converted to Python types by now
            
            # Create new task with updated data using the manager's create_work_item method
            await self.lancedb_manager.create_work_item(update_data)
            
            # Prepare response data (exclude vector and handle serialization)
            response_task = {}
            for k, v in update_data.items():
                if k == "vector":
                    continue  # Skip vector field
                elif hasattr(v, 'item') and not hasattr(v, '__len__'):  # numpy scalar only
                    response_task[k] = v.item()
                elif hasattr(v, 'item') and hasattr(v, '__len__') and hasattr(v, 'size') and v.size == 1:
                    # Single-element numpy array
                    response_task[k] = v.item()
                elif hasattr(v, 'isoformat'):  # datetime object
                    response_task[k] = v.isoformat()
                elif hasattr(v, 'tolist'):  # numpy array
                    response_task[k] = v.tolist()
                elif hasattr(pd, 'isna'):
                    # Safe pandas NaN check to avoid NumPy boolean evaluation
                    try:
                        if pd.isna(v) and not hasattr(v, '__len__'):
                            response_task[k] = None
                        else:
                            response_task[k] = v
                    except (ValueError, TypeError):
                        response_task[k] = v
                else:
                    response_task[k] = v
            
            response = {
                "success": True,
                "task_id": task_id,
                "message": "Task updated successfully",
                "task": response_task
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
            
            table = self.lancedb_manager.get_table("WorkItem")
            
            # Check if task exists (tasks are stored as work items)
            result = table.search().where(f"id = '{task_id}' AND item_type = 'task'").limit(1).to_pandas()
            if len(result) == 0:
                error_response = {
                    "success": False,
                    "error": f"Task with ID {task_id} not found",
                    "message": "Task not found"
                }
                return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
                
            deleted_count = 1
            
            # Delete subtasks if requested
            if delete_subtasks:
                # Find subtasks by checking parent_id and ensuring they are tasks
                subtasks_result = table.search().where(
                    f"parent_id = '{task_id}' AND item_type = 'task'"
                ).to_pandas()
                
                for _, subtask in subtasks_result.iterrows():
                    table.delete(f"id = '{subtask['id']}'")
                    deleted_count += 1
                    
            # Delete main task
            table.delete(f"id = '{task_id}'")
            
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
            
            table = self.lancedb_manager.get_table("WorkItem")
            
            # Get main task (tasks are stored as work items)
            result = table.search().where(f"id = '{task_id}' AND item_type = 'task'").limit(1).to_pandas()
            
            if len(result) == 0:
                error_response = {
                    "success": False,
                    "error": f"Task with ID {task_id} not found",
                    "message": "Task not found"
                }
                return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
                
            task_data_raw = result.iloc[0].to_dict()
            
            # Prepare task data with proper JSON serialization
            task_data = {}
            for k, v in task_data_raw.items():
                if k == "vector":
                    continue  # Skip vector field
                elif hasattr(v, 'item') and not hasattr(v, '__len__'):  # numpy scalar only
                    task_data[k] = v.item()
                elif hasattr(v, 'item') and hasattr(v, '__len__') and hasattr(v, 'size') and v.size == 1:
                    # Single-element numpy array
                    task_data[k] = v.item()
                elif hasattr(v, 'isoformat'):  # datetime object
                    task_data[k] = v.isoformat()
                elif hasattr(v, 'tolist'):  # numpy array
                    task_data[k] = v.tolist()
                elif hasattr(pd, 'isna'):
                    # Safe pandas NaN check to avoid NumPy boolean evaluation
                    try:
                        if pd.isna(v) and not hasattr(v, '__len__'):
                            task_data[k] = None
                        else:
                            task_data[k] = v
                    except (ValueError, TypeError):
                        task_data[k] = v
                else:
                    task_data[k] = v
            
            # Get subtasks if requested
            subtasks = []
            if include_subtasks:
                # Find subtasks by checking parent_id and ensuring they are tasks
                subtasks_result = table.search().where(
                    f"parent_id = '{task_id}' AND item_type = 'task'"
                ).to_pandas()
                
                for _, subtask in subtasks_result.iterrows():
                    subtask_data_raw = subtask.to_dict()
                    # Prepare subtask data with proper JSON serialization
                    subtask_data = {}
                    for k, v in subtask_data_raw.items():
                        if k == "vector":
                            continue  # Skip vector field
                        elif hasattr(v, 'item') and not hasattr(v, '__len__'):  # numpy scalar only
                            subtask_data[k] = v.item()
                        elif hasattr(v, 'item') and hasattr(v, '__len__') and hasattr(v, 'size') and v.size == 1:
                            # Single-element numpy array
                            subtask_data[k] = v.item()
                        elif hasattr(v, 'isoformat'):  # datetime object
                            subtask_data[k] = v.isoformat()
                        elif hasattr(v, 'tolist'):  # numpy array
                            subtask_data[k] = v.tolist()
                        elif hasattr(pd, 'isna'):
                            # Safe pandas NaN check to avoid NumPy boolean evaluation
                            try:
                                if pd.isna(v) and not hasattr(v, '__len__'):
                                    subtask_data[k] = None
                                else:
                                    subtask_data[k] = v
                            except (ValueError, TypeError):
                                subtask_data[k] = v
                        else:
                            subtask_data[k] = v
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