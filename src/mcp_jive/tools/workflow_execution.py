"""Workflow Execution Tools.

Implements the 4 workflow execution MCP tools:
- execute_workflow: Execute a workflow with tasks
- validate_workflow: Validate workflow structure and dependencies
- get_workflow_status: Get current workflow execution status
- cancel_workflow: Cancel a running workflow
"""

import logging
import uuid
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from enum import Enum

from mcp.types import Tool, TextContent
from ..error_utils import ErrorHandler, ValidationError, with_error_handling
from ..uuid_utils import validate_uuid, is_valid_uuid, generate_uuid, UUIDValidator

from ..config import ServerConfig
from mcp_jive.lancedb_manager import LanceDBManager

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class WorkflowExecutionTools:
    """Workflow execution tool implementations."""
    
    def __init__(self, config: ServerConfig, lancedb_manager: LanceDBManager):
        self.config = config
        self.lancedb_manager = lancedb_manager
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        
    async def initialize(self) -> None:
        """Initialize workflow execution tools."""
        logger.info("Initializing workflow execution tools...")
        
    async def get_tools(self) -> List[Tool]:
        """Get all workflow execution tools."""
        return [
            Tool(
                name="jive_execute_workflow",
                description="Jive: Execute a workflow with a set of task (development task or work item)s and dependencies",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "workflow_name": {
                            "type": "string",
                            "description": "Name of the workflow"
                        },
                        "description": {
                            "type": "string",
                            "description": "Workflow description"
                        },
                        "tasks": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string", "description": "Task ID"},
                                    "title": {"type": "string", "description": "Task title"},
                                    "description": {"type": "string", "description": "Task description"},
                                    "dependencies": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "List of task IDs this task depends on"
                                    },
                                    "estimated_duration": {
                                        "type": "integer",
                                        "description": "Estimated duration in minutes"
                                    },
                                    "priority": {
                                        "type": "string",
                                        "enum": ["low", "medium", "high", "urgent"],
                                        "default": "medium"
                                    }
                                },
                                "required": ["id", "title"]
                            },
                            "description": "List of tasks in the workflow"
                        },
                        "execution_mode": {
                            "type": "string",
                            "enum": ["sequential", "parallel", "dependency_based"],
                            "default": "dependency_based",
                            "description": "How to execute the workflow"
                        },
                        "auto_start": {
                            "type": "boolean",
                            "default": True,
                            "description": "Whether to start execution immediately"
                        }
                    },
                    "required": ["workflow_name", "tasks"]
                }
            ),
            Tool(
                name="jive_validate_workflow",
                description="Jive: Validate workflow structure, dependencies, and feasibility",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "tasks": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string", "description": "Task ID"},
                                    "title": {"type": "string"},
                                    "dependencies": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    }
                                },
                                "required": ["id", "title"]
                            },
                            "description": "List of tasks to validate"
                        },
                        "check_circular_dependencies": {
                            "type": "boolean",
                            "default": True,
                            "description": "Check for circular dependencies"
                        },
                        "check_missing_dependencies": {
                            "type": "boolean",
                            "default": True,
                            "description": "Check for missing dependency references"
                        }
                    },
                    "required": ["tasks"]
                }
            ),
            Tool(
                name="jive_get_workflow_status",
                description="Jive: Get current status and progress of a workflow",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "description": "Workflow ID to check status"
                        },
                        "include_task_details": {
                            "type": "boolean",
                            "default": True,
                            "description": "Include detailed task status information"
                        },
                        "include_timeline": {
                            "type": "boolean",
                            "default": False,
                            "description": "Include execution timeline"
                        }
                    },
                    "required": ["workflow_id"]
                }
            ),
            Tool(
                name="jive_cancel_workflow",
                description="Jive: Cancel a running workflow",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "description": "Workflow ID to cancel"
                        },
                        "reason": {
                            "type": "string",
                            "description": "Reason for cancellation"
                        },
                        "force": {
                            "type": "boolean",
                            "default": False,
                            "description": "Force cancellation even if tasks are running"
                        }
                    },
                    "required": ["workflow_id"]
                }
            )
        ]
        
    async def handle_tool_call(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle tool calls for workflow execution."""
        if name == "jive_execute_workflow":
            return await self._execute_workflow(arguments)
        elif name == "jive_validate_workflow":
            return await self._validate_workflow(arguments)
        elif name == "jive_get_workflow_status":
            return await self._get_workflow_status(arguments)
        elif name == "jive_cancel_workflow":
            return await self._cancel_workflow(arguments)
        else:
            raise ValidationError("Unknown workflow execution tool: {name}", "parameter", None)
            
    async def _execute_workflow(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute a workflow."""
        try:
            workflow_id = str(uuid.uuid4())
            workflow_name = arguments["workflow_name"]
            description = arguments.get("description", "")
            tasks = arguments["tasks"]
            execution_mode = arguments.get("execution_mode", "dependency_based")
            auto_start = arguments.get("auto_start", True)
            
            # Validate workflow first
            validation_result = await self._validate_workflow_internal(tasks)
            if not validation_result["valid"]:
                error_response = {
                    "success": False,
                    "error": "Workflow validation failed",
                    "validation_errors": validation_result["errors"],
                    "message": "Cannot execute invalid workflow"
                }
                return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
                
            # Create workflow data
            workflow_data = {
                "name": workflow_name,
                "description": description,
                "status": WorkflowStatus.PENDING.value,
                "execution_mode": execution_mode,
                "tasks": tasks,
                "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                "started_at": None,
                "completed_at": None,
                "progress": {
                    "total_tasks": len(tasks),
                    "completed_tasks": 0,
                    "failed_tasks": 0,
                    "percentage": 0.0
                },
                "execution_order": self._calculate_execution_order(tasks),
                "timeline": []
            }
            
            # Store workflow
            self.active_workflows[workflow_id] = workflow_data
            
            # Store in LanceDB using the proper method
            try:
                workflow_record = {
                    "id": workflow_id,
                    "item_id": workflow_id,
                    "item_type": "workflow",
                    "title": workflow_name,
                    "description": json.dumps(workflow_data),
                    "status": WorkflowStatus.PENDING.value,
                    "priority": "medium",
                    "assignee": None,
                    "tags": [],
                    "estimated_hours": None,
                    "actual_hours": None,
                    "progress": 0.0,
                    "parent_id": None,
                    "dependencies": [],
                    "acceptance_criteria": None,
                    "metadata": json.dumps({
                        "workflow_id": workflow_id,
                        "task_count": len(tasks),
                        "execution_mode": execution_mode
                    })
                }
                await self.lancedb_manager.create_work_item(workflow_record)
            except Exception as e:
                logger.warning(f"Failed to store workflow in database: {e}")
                # Continue execution even if storage fails
            
            # Start execution if auto_start is True
            if auto_start:
                await self._start_workflow_execution(workflow_id)
                
            response = {
                "success": True,
                "execution_id": workflow_id,
                "workflow_id": workflow_id,
                "workflow_name": workflow_name,
                "status": workflow_data["status"],
                "total_tasks": len(tasks),
                "execution_mode": execution_mode,
                "auto_started": auto_start,
                "message": f"Workflow '{workflow_name}' created successfully"
            }
            
            return [TextContent(type="text", text=json.dumps(response, indent=2))]
            
        except Exception as e:
            logger.error(f"Error executing workflow: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "message": "Failed to execute workflow"
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
            
    async def _validate_workflow(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Validate workflow structure."""
        try:
            tasks = arguments["tasks"]
            check_circular = arguments.get("check_circular_dependencies", True)
            check_missing = arguments.get("check_missing_dependencies", True)
            
            validation_result = await self._validate_workflow_internal(
                tasks, check_circular, check_missing
            )
            
            response = {
                "success": True,
                "valid": validation_result["valid"],
                "errors": validation_result["errors"],
                "warnings": validation_result["warnings"],
                "task_count": len(tasks),
                "dependency_count": sum(len(task.get("dependencies", [])) for task in tasks),
                "execution_order": validation_result.get("execution_order", []),
                "message": "Workflow validation completed"
            }
            
            return [TextContent(type="text", text=json.dumps(response, indent=2))]
            
        except Exception as e:
            logger.error(f"Error validating workflow: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "message": "Failed to validate workflow"
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
            
    async def _get_workflow_status(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get workflow status."""
        try:
            workflow_id = arguments["workflow_id"]
            include_task_details = arguments.get("include_task_details", True)
            include_timeline = arguments.get("include_timeline", False)
            
            if workflow_id not in self.active_workflows:
                error_response = {
                    "success": False,
                    "error": f"Workflow with ID {workflow_id} not found",
                    "message": "Workflow not found"
                }
                return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
                
            workflow_data = self.active_workflows[workflow_id]
            
            # Calculate current progress
            progress = await self._calculate_workflow_progress(workflow_id)
            workflow_data["progress"] = progress
            
            response = {
                "success": True,
                "workflow_id": workflow_id,
                "name": workflow_data["name"],
                "status": workflow_data["status"],
                "progress": progress,
                "created_at": workflow_data["created_at"],
                "started_at": workflow_data.get("started_at"),
                "completed_at": workflow_data.get("completed_at"),
                "execution_mode": workflow_data["execution_mode"]
            }
            
            if include_task_details:
                response["tasks"] = workflow_data["tasks"]
                response["execution_order"] = workflow_data.get("execution_order", [])
                
            if include_timeline:
                response["timeline"] = workflow_data.get("timeline", [])
                
            return [TextContent(type="text", text=json.dumps(response, indent=2))]
            
        except Exception as e:
            logger.error(f"Error getting workflow status: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "message": "Failed to get workflow status"
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
            
    async def _cancel_workflow(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Cancel a workflow."""
        try:
            workflow_id = arguments["workflow_id"]
            reason = arguments.get("reason", "User requested cancellation")
            force = arguments.get("force", False)
            
            if workflow_id not in self.active_workflows:
                error_response = {
                    "success": False,
                    "error": f"Workflow with ID {workflow_id} not found",
                    "message": "Workflow not found"
                }
                return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
                
            workflow_data = self.active_workflows[workflow_id]
            current_status = workflow_data["status"]
            
            # Check if workflow can be cancelled
            if current_status in [WorkflowStatus.COMPLETED.value, WorkflowStatus.CANCELLED.value]:
                error_response = {
                    "success": False,
                    "error": f"Cannot cancel workflow in {current_status} status",
                    "message": "Workflow cannot be cancelled"
                }
                return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
                
            if current_status == WorkflowStatus.RUNNING.value and not force:
                error_response = {
                    "success": False,
                    "error": "Workflow is currently running. Use force=true to cancel",
                    "message": "Cannot cancel running workflow without force flag"
                }
                return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
                
            # Cancel the workflow
            workflow_data["status"] = WorkflowStatus.CANCELLED.value
            workflow_data["cancelled_at"] = datetime.now().isoformat() + "Z"
            workflow_data["cancellation_reason"] = reason
            
            # Add to timeline
            workflow_data["timeline"].append({
                "timestamp": datetime.now().isoformat() + "Z",
                "event": "workflow_cancelled",
                "reason": reason,
                "forced": force
            })
            
            response = {
                "success": True,
                "workflow_id": workflow_id,
                "previous_status": current_status,
                "new_status": WorkflowStatus.CANCELLED.value,
                "reason": reason,
                "forced": force,
                "cancelled_at": workflow_data["cancelled_at"],
                "message": f"Workflow '{workflow_data['name']}' cancelled successfully"
            }
            
            return [TextContent(type="text", text=json.dumps(response, indent=2))]
            
        except Exception as e:
            logger.error(f"Error cancelling workflow: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "message": "Failed to cancel workflow"
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
            
    async def _validate_workflow_internal(self, tasks: List[Dict[str, Any]], 
                                        check_circular: bool = True, 
                                        check_missing: bool = True) -> Dict[str, Any]:
        """Internal workflow validation."""
        errors = []
        warnings = []
        
        # Get task IDs
        task_ids = {task["id"] for task in tasks}
        
        # Check for duplicate task IDs
        seen_ids = set()
        for task in tasks:
            task_id = task["id"]
            if task_id in seen_ids:
                errors.append(f"Duplicate task ID: {task_id}")
            seen_ids.add(task_id)
            
        # Check missing dependencies
        if check_missing:
            for task in tasks:
                dependencies = task.get("dependencies", [])
                for dep_id in dependencies:
                    if dep_id not in task_ids:
                        errors.append(f"Task '{task['id']}' depends on non-existent task '{dep_id}'")
                        
        # Check circular dependencies
        if check_circular:
            circular_deps = self._find_circular_dependencies(tasks)
            if circular_deps:
                errors.extend([f"Circular dependency detected: {' -> '.join(cycle)}" for cycle in circular_deps])
                
        # Calculate execution order
        execution_order = []
        if not errors:
            try:
                execution_order = self._calculate_execution_order(tasks)
            except Exception as e:
                errors.append(f"Failed to calculate execution order: {str(e)}")
                
        # Check for orphaned tasks (no dependencies and no dependents)
        if not errors:
            all_dependencies = set()
            for task in tasks:
                all_dependencies.update(task.get("dependencies", []))
                
            for task in tasks:
                task_id = task["id"]
                has_dependencies = bool(task.get("dependencies"))
                has_dependents = task_id in all_dependencies
                
                if not has_dependencies and not has_dependents and len(tasks) > 1:
                    warnings.append(f"Task '{task_id}' appears to be orphaned (no dependencies or dependents)")
                    
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "execution_order": execution_order
        }
        
    def _find_circular_dependencies(self, tasks: List[Dict[str, Any]]) -> List[List[str]]:
        """Find circular dependencies using DFS."""
        # Build dependency graph
        graph = {}
        for task in tasks:
            task_id = task["id"]
            dependencies = task.get("dependencies", [])
            graph[task_id] = dependencies
            
        # DFS to find cycles
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node: str, path: List[str]) -> None:
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:] + [node])
                return
                
            if node in visited:
                return
                
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                dfs(neighbor, path + [node])
                
            rec_stack.remove(node)
            
        for task_id in graph:
            if task_id not in visited:
                dfs(task_id, [])
                
        return cycles
        
    def _calculate_execution_order(self, tasks: List[Dict[str, Any]]) -> List[str]:
        """Calculate topological execution order."""
        # Build dependency graph
        graph = {}
        in_degree = {}
        
        for task in tasks:
            task_id = task["id"]
            dependencies = task.get("dependencies", [])
            graph[task_id] = dependencies
            in_degree[task_id] = len(dependencies)
            
        # Topological sort using Kahn's algorithm
        queue = [task_id for task_id, degree in in_degree.items() if degree == 0]
        execution_order = []
        
        while queue:
            current = queue.pop(0)
            execution_order.append(current)
            
            # Update in-degrees of dependent tasks
            for task_id, dependencies in graph.items():
                if current in dependencies:
                    in_degree[task_id] -= 1
                    if in_degree[task_id] == 0:
                        queue.append(task_id)
                        
        return execution_order
        
    async def _start_workflow_execution(self, workflow_id: str) -> None:
        """Start workflow execution (simulated)."""
        # Validate UUID format
        workflow_id = validate_uuid(workflow_id, "workflow_id")

        if workflow_id not in self.active_workflows:
            return
            
        workflow_data = self.active_workflows[workflow_id]
        workflow_data["status"] = WorkflowStatus.RUNNING.value
        workflow_data["started_at"] = datetime.now().isoformat() + "Z"
        
        # Add to timeline
        workflow_data["timeline"].append({
            "timestamp": datetime.now().isoformat() + "Z",
            "event": "workflow_started",
            "message": "Workflow execution started"
        })
        
        # Simulate task execution (in a real implementation, this would trigger actual task execution)
        asyncio.create_task(self._simulate_workflow_execution(workflow_id))
        
    async def _simulate_workflow_execution(self, workflow_id: str) -> None:
        """Simulate workflow execution for demonstration."""
        # Validate UUID format
        workflow_id = validate_uuid(workflow_id, "workflow_id")

        try:
            workflow_data = self.active_workflows[workflow_id]
            tasks = workflow_data["tasks"]
            execution_order = workflow_data["execution_order"]
            
            for task_id in execution_order:
                if workflow_data["status"] == WorkflowStatus.CANCELLED.value:
                    break
                    
                # Simulate task execution
                await asyncio.sleep(1)  # Simulate work
                
                # Update progress
                workflow_data["timeline"].append({
                    "timestamp": datetime.now().isoformat() + "Z",
                    "event": "task_completed",
                    "task_id": task_id,
                    "message": f"Task {task_id} completed"
                })
                
            # Mark workflow as completed
            if workflow_data["status"] != WorkflowStatus.CANCELLED.value:
                workflow_data["status"] = WorkflowStatus.COMPLETED.value
                workflow_data["completed_at"] = datetime.now().isoformat() + "Z"
                
                workflow_data["timeline"].append({
                    "timestamp": datetime.now().isoformat() + "Z",
                    "event": "workflow_completed",
                    "message": "Workflow execution completed successfully"
                })
                
        except Exception as e:
            logger.error(f"Error in workflow execution simulation: {e}")
            workflow_data["status"] = WorkflowStatus.FAILED.value
            workflow_data["error"] = str(e)
            
    async def _calculate_workflow_progress(self, workflow_id: str) -> Dict[str, Any]:
        """Calculate workflow progress."""
        # Validate UUID format
        workflow_id = validate_uuid(workflow_id, "workflow_id")

        workflow_data = self.active_workflows[workflow_id]
        tasks = workflow_data["tasks"]
        timeline = workflow_data.get("timeline", [])
        
        # Count completed tasks from timeline
        completed_tasks = len([event for event in timeline if event.get("event") == "task_completed"])
        total_tasks = len(tasks)
        
        percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": 0,  # Simplified for demo
            "percentage": round(percentage, 2)
        }
        
    async def cleanup(self) -> None:
        """Cleanup workflow execution tools."""
        logger.info("Cleaning up workflow execution tools...")
        
        # Cancel all active workflows
        for workflow_id in list(self.active_workflows.keys()):
            workflow_data = self.active_workflows[workflow_id]
            if workflow_data["status"] in [WorkflowStatus.RUNNING.value, WorkflowStatus.PENDING.value]:
                workflow_data["status"] = WorkflowStatus.CANCELLED.value
                workflow_data["cancelled_at"] = datetime.now().isoformat() + "Z"
                workflow_data["cancellation_reason"] = "Server shutdown"
                
        self.active_workflows.clear()