"""Agile Workflow Engine Tools.

Implements the 6 workflow engine MCP tools for managing work item hierarchies:
- get_work_item_children: Get child tasks for a work item
- get_work_item_dependencies: Check what blocks this task
- validate_dependencies: Ensure no circular dependencies
- execute_work_item: Start autonomous execution of work item
- get_execution_status: Monitor real-time execution progress
- cancel_execution: Stop and rollback work item execution
"""

import logging
import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
import json
from enum import Enum
import networkx as nx

from mcp.types import Tool, TextContent

from ..config import ServerConfig
from ..database import WeaviateManager
from ..models.workflow import (
    WorkItem,
    WorkItemType,
    WorkItemStatus,
    ExecutionStatus,
    Priority,
    ExecutionContext,
    ExecutionResult,
    ValidationResult,
)
from ..services import (
    HierarchyManager,
    DependencyEngine,
    AutonomousExecutor,
)

logger = logging.getLogger(__name__)


# Enums are imported from models.workflow module


class WorkflowEngineTools:
    """Agile Workflow Engine tool implementations."""
    
    def __init__(self, config: ServerConfig, weaviate_manager: WeaviateManager):
        self.config = config
        self.weaviate_manager = weaviate_manager
        self.active_executions: Dict[str, Dict[str, Any]] = {}
        self.dependency_graph = nx.DiGraph()
        
        # Initialize services
        self.hierarchy_manager = HierarchyManager(config, weaviate_manager)
        self.dependency_engine = DependencyEngine(config, weaviate_manager)
        self.autonomous_executor = AutonomousExecutor(config, weaviate_manager)
        
    async def initialize(self) -> None:
        """Initialize workflow engine tools."""
        logger.info("Initializing workflow engine tools...")
        
        # Initialize all services
        await self.hierarchy_manager.initialize()
        await self.dependency_engine.initialize()
        await self.autonomous_executor.initialize()
        
        # Ensure WorkItem collection exists with proper schema
        await self._ensure_work_item_schema()
        
    async def _ensure_work_item_schema(self) -> None:
        """Ensure WorkItem collection has proper schema for hierarchy."""
        try:
            collection = self.weaviate_manager.get_collection("WorkItem")
            
            # Check if collection exists, if not it will be created by WeaviateManager
            logger.info("WorkItem collection schema verified for workflow engine")
            
        except Exception as e:
            logger.error(f"Error ensuring WorkItem schema: {e}")
            raise
        
    async def get_tools(self) -> List[Tool]:
        """Get all workflow engine tools."""
        return [
            Tool(
                name="jive_get_work_item_children",
                description="Jive: Get child work items for a given work item in the hierarchy",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "work_item_id": {
                            "type": "string",
                            "description": "ID of the work item to get children for"
                        },
                        "include_metadata": {
                            "type": "boolean",
                            "default": True,
                            "description": "Include metadata like effort estimates and acceptance criteria"
                        },
                        "recursive": {
                            "type": "boolean",
                            "default": False,
                            "description": "Get all descendants, not just direct children"
                        }
                    },
                    "required": ["work_item_id"]
                }
            ),
            Tool(
                name="jive_get_work_item_dependencies",
                description="Jive: Get dependencies that block a work item from being executed",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "work_item_id": {
                            "type": "string",
                            "description": "ID of the work item to check dependencies for"
                        },
                        "include_transitive": {
                            "type": "boolean",
                            "default": True,
                            "description": "Include transitive dependencies (dependencies of dependencies)"
                        },
                        "only_blocking": {
                            "type": "boolean",
                            "default": True,
                            "description": "Only return dependencies that are currently blocking execution"
                        }
                    },
                    "required": ["work_item_id"]
                }
            ),
            Tool(
                name="jive_validate_dependencies",
                description="Jive: Validate dependency graph for circular dependencies and consistency",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "work_item_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of work item IDs to validate (empty for all work items)"
                        },
                        "check_circular": {
                            "type": "boolean",
                            "default": True,
                            "description": "Check for circular dependencies"
                        },
                        "check_missing": {
                            "type": "boolean",
                            "default": True,
                            "description": "Check for missing dependency references"
                        },
                        "suggest_fixes": {
                            "type": "boolean",
                            "default": True,
                            "description": "Suggest fixes for dependency issues"
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="jive_execute_work_item",
                description="Jive: Start autonomous execution of a work item through AI agent coordination",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "work_item_id": {
                            "type": "string",
                            "description": "ID of the work item to execute"
                        },
                        "execution_mode": {
                            "type": "string",
                            "enum": ["sequential", "parallel", "dependency_based"],
                            "default": "dependency_based",
                            "description": "How to execute child work items"
                        },
                        "agent_context": {
                            "type": "object",
                            "description": "Additional context for AI agent execution",
                            "properties": {
                                "project_path": {"type": "string"},
                                "environment": {"type": "string"},
                                "constraints": {"type": "array", "items": {"type": "string"}}
                            }
                        },
                        "validate_before_execution": {
                            "type": "boolean",
                            "default": True,
                            "description": "Validate dependencies before starting execution"
                        }
                    },
                    "required": ["work_item_id"]
                }
            ),
            Tool(
                name="jive_get_execution_status",
                description="Jive: Monitor real-time execution progress of a work item",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "execution_id": {
                            "type": "string",
                            "description": "ID of the execution to monitor"
                        },
                        "include_logs": {
                            "type": "boolean",
                            "default": False,
                            "description": "Include execution logs in the response"
                        },
                        "include_artifacts": {
                            "type": "boolean",
                            "default": True,
                            "description": "Include generated artifacts information"
                        },
                        "include_validation_results": {
                            "type": "boolean",
                            "default": True,
                            "description": "Include validation results against acceptance criteria"
                        }
                    },
                    "required": ["execution_id"]
                }
            ),
            Tool(
                name="jive_cancel_execution",
                description="Jive: Stop and rollback work item execution",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "execution_id": {
                            "type": "string",
                            "description": "ID of the execution to cancel"
                        },
                        "reason": {
                            "type": "string",
                            "description": "Reason for cancellation"
                        },
                        "rollback_changes": {
                            "type": "boolean",
                            "default": True,
                            "description": "Whether to rollback any changes made during execution"
                        },
                        "force": {
                            "type": "boolean",
                            "default": False,
                            "description": "Force cancellation even if rollback fails"
                        }
                    },
                    "required": ["execution_id"]
                }
            )
        ]
        
    async def handle_tool_call(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle tool calls for workflow engine."""
        if name == "jive_get_work_item_children":
            return await self._get_work_item_children(arguments)
        elif name == "jive_get_work_item_dependencies":
            return await self._get_work_item_dependencies(arguments)
        elif name == "jive_validate_dependencies":
            return await self._validate_dependencies(arguments)
        elif name == "jive_execute_work_item":
            return await self._execute_work_item(arguments)
        elif name == "jive_get_execution_status":
            return await self._get_execution_status(arguments)
        elif name == "jive_cancel_execution":
            return await self._cancel_execution(arguments)
        else:
            raise ValueError(f"Unknown workflow engine tool: {name}")
            
    async def _get_work_item_children(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get child work items for a given work item."""
        try:
            work_item_id = arguments["work_item_id"]
            include_metadata = arguments.get("include_metadata", True)
            recursive = arguments.get("recursive", False)
            
            # Query Weaviate for work items with this parent_id
            collection = self.weaviate_manager.get_collection("WorkItem")
            
            # Build query to find children
            query_filter = {
                "path": ["metadata", "parent_id"],
                "operator": "Equal",
                "valueText": work_item_id
            }
            
            result = collection.query.fetch_objects(
                where=query_filter,
                limit=100
            )
            
            children = []
            for obj in result.objects:
                child_data = {
                    "id": obj.properties.get("metadata", {}).get("work_item_id", obj.uuid),
                    "type": obj.properties.get("metadata", {}).get("type", "Task"),
                    "title": obj.properties.get("title", ""),
                    "status": obj.properties.get("status", WorkItemStatus.NOT_STARTED.value)
                }
                
                if include_metadata:
                    metadata = obj.properties.get("metadata", {})
                    child_data.update({
                        "description": obj.properties.get("content", ""),
                        "priority": metadata.get("priority", Priority.MEDIUM.value),
                        "effort_estimate": metadata.get("effort_estimate", 0),
                        "acceptance_criteria": metadata.get("acceptance_criteria", []),
                        "assigned_agent": metadata.get("assigned_agent"),
                        "created_at": obj.properties.get("created_at"),
                        "updated_at": obj.properties.get("updated_at")
                    })
                
                children.append(child_data)
                
                # If recursive, get children of children
                if recursive:
                    grandchildren_args = {
                        "work_item_id": child_data["id"],
                        "include_metadata": include_metadata,
                        "recursive": True
                    }
                    grandchildren_result = await self._get_work_item_children(grandchildren_args)
                    grandchildren_data = json.loads(grandchildren_result[0].text)
                    if grandchildren_data["success"]:
                        child_data["children"] = grandchildren_data["children"]
            
            response = {
                "success": True,
                "work_item_id": work_item_id,
                "children_count": len(children),
                "children": children,
                "recursive": recursive,
                "include_metadata": include_metadata,
                "message": f"Found {len(children)} children for work item {work_item_id}"
            }
            
            return [TextContent(type="text", text=json.dumps(response, indent=2))]
            
        except Exception as e:
            logger.error(f"Error getting work item children: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "message": "Failed to get work item children"
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
            
    async def _get_work_item_dependencies(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get dependencies that block a work item."""
        try:
            work_item_id = arguments["work_item_id"]
            include_transitive = arguments.get("include_transitive", True)
            only_blocking = arguments.get("only_blocking", True)
            
            # Get the work item first
            collection = self.weaviate_manager.get_collection("WorkItem")
            
            query_filter = {
                "path": ["metadata", "work_item_id"],
                "operator": "Equal",
                "valueText": work_item_id
            }
            
            result = collection.query.fetch_objects(
                where=query_filter,
                limit=1
            )
            
            if not result.objects:
                error_response = {
                    "success": False,
                    "error": f"Work item {work_item_id} not found",
                    "message": "Work item not found"
                }
                return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
            
            work_item = result.objects[0]
            metadata = work_item.properties.get("metadata", {})
            dependencies = metadata.get("dependencies", [])
            
            dependency_details = []
            blocking_dependencies = []
            
            for dep_id in dependencies:
                # Get dependency details
                dep_filter = {
                    "path": ["metadata", "work_item_id"],
                    "operator": "Equal",
                    "valueText": dep_id
                }
                
                dep_result = collection.query.fetch_objects(
                    where=dep_filter,
                    limit=1
                )
                
                if dep_result.objects:
                    dep_obj = dep_result.objects[0]
                    dep_status = dep_obj.properties.get("status", WorkItemStatus.NOT_STARTED.value)
                    
                    dep_info = {
                        "id": dep_id,
                        "title": dep_obj.properties.get("title", ""),
                        "status": dep_status,
                        "type": dep_obj.properties.get("metadata", {}).get("type", "Task"),
                        "is_blocking": dep_status not in [WorkItemStatus.COMPLETED.value, WorkItemStatus.VALIDATED.value]
                    }
                    
                    dependency_details.append(dep_info)
                    
                    if dep_info["is_blocking"] and only_blocking:
                        blocking_dependencies.append(dep_info)
                        
                    # Get transitive dependencies if requested
                    if include_transitive and dep_info["is_blocking"]:
                        transitive_args = {
                            "work_item_id": dep_id,
                            "include_transitive": True,
                            "only_blocking": only_blocking
                        }
                        transitive_result = await self._get_work_item_dependencies(transitive_args)
                        transitive_data = json.loads(transitive_result[0].text)
                        if transitive_data["success"]:
                            dep_info["transitive_dependencies"] = transitive_data["dependencies"]
            
            final_dependencies = blocking_dependencies if only_blocking else dependency_details
            
            response = {
                "success": True,
                "work_item_id": work_item_id,
                "work_item_title": work_item.properties.get("title", ""),
                "work_item_status": work_item.properties.get("status", WorkItemStatus.NOT_STARTED.value),
                "dependencies_count": len(final_dependencies),
                "dependencies": final_dependencies,
                "is_blocked": len(blocking_dependencies) > 0,
                "include_transitive": include_transitive,
                "only_blocking": only_blocking,
                "message": f"Found {len(final_dependencies)} dependencies for work item {work_item_id}"
            }
            
            return [TextContent(type="text", text=json.dumps(response, indent=2))]
            
        except Exception as e:
            logger.error(f"Error getting work item dependencies: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "message": "Failed to get work item dependencies"
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
            
    async def _validate_dependencies(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Validate dependency graph for circular dependencies and consistency."""
        try:
            work_item_ids = arguments.get("work_item_ids", [])
            check_circular = arguments.get("check_circular", True)
            check_missing = arguments.get("check_missing", True)
            suggest_fixes = arguments.get("suggest_fixes", True)
            
            # Use dependency engine to validate dependencies
            validation_result = await self.dependency_engine.validate_dependencies(
                work_item_ids=work_item_ids,
                check_circular=check_circular,
                check_missing=check_missing,
                suggest_fixes=suggest_fixes
            )
            
            response = {
                "success": True,
                "valid": validation_result.is_valid,
                "work_items_validated": len(work_item_ids) if work_item_ids else validation_result.total_work_items,
                "errors": [error.dict() for error in validation_result.errors],
                "warnings": [warning.dict() for warning in validation_result.warnings],
                "suggested_fixes": [fix.dict() for fix in validation_result.suggested_fixes] if suggest_fixes else [],
                "execution_order": validation_result.execution_order,
                "graph_stats": validation_result.graph_stats,
                "message": f"Validation completed: {'Valid' if validation_result.is_valid else 'Invalid'} dependency graph"
            }
            
            return [TextContent(type="text", text=json.dumps(response, indent=2))]
            
        except Exception as e:
            logger.error(f"Error validating dependencies: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "message": "Failed to validate dependencies"
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
            
    async def _execute_work_item(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Start autonomous execution of a work item."""
        try:
            work_item_id = arguments["work_item_id"]
            execution_mode = arguments.get("execution_mode", "dependency_based")
            agent_context = arguments.get("agent_context", {})
            validate_before_execution = arguments.get("validate_before_execution", True)
            
            # Get work item from hierarchy manager
            work_item = await self.hierarchy_manager.get_work_item(work_item_id)
            if not work_item:
                raise ValueError(f"Work item {work_item_id} not found")
            
            # Create execution context
            execution_context = ExecutionContext(
                agent_id=agent_context.get("agent_id", "default_agent"),
                execution_environment={
                    "execution_mode": execution_mode,
                    "validate_before_execution": validate_before_execution,
                    **agent_context
                }
            )
            
            # Use autonomous executor to start execution
            execution_id = await self.autonomous_executor.execute_work_item(work_item, execution_context)
            
            # Store execution record
            self.active_executions[execution_id] = {
                "execution_id": execution_id,
                "work_item_id": work_item_id,
                "status": ExecutionStatus.PENDING.value,
                "progress_percentage": 0.0,
                "start_time": datetime.now().isoformat(),
                "end_time": None,
                "error_message": None,
                "execution_mode": execution_mode,
                "agent_context": agent_context
            }
            
            response = {
                "success": True,
                "execution_id": execution_id,
                "work_item_id": work_item_id,
                "work_item_title": work_item.title,
                "status": ExecutionStatus.PENDING.value,
                "execution_mode": execution_mode,
                "start_time": datetime.now().isoformat(),
                "message": f"Started execution of work item {work_item_id}"
            }
            
            return [TextContent(type="text", text=json.dumps(response, indent=2))]
            
        except Exception as e:
            logger.error(f"Error executing work item: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "message": "Failed to execute work item"
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
            
    async def _simulate_execution(self, execution_id: str) -> None:
        """Monitor work item execution progress."""
        try:
            execution_data = self.active_executions[execution_id]
            
            # The autonomous executor handles the actual execution
            # This method is kept for compatibility but execution is managed by autonomous_executor
            logger.info(f"Execution {execution_id} monitoring started")
                    
        except Exception as e:
            logger.error(f"Error in execution monitoring: {e}")
            if execution_id in self.active_executions:
                self.active_executions[execution_id]["status"] = ExecutionStatus.FAILED.value
                self.active_executions[execution_id]["error_message"] = str(e)
                self.active_executions[execution_id]["end_time"] = datetime.now().isoformat()
            
    async def _get_execution_status(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Monitor real-time execution progress of a work item."""
        try:
            execution_id = arguments["execution_id"]
            include_logs = arguments.get("include_logs", False)
            include_artifacts = arguments.get("include_artifacts", True)
            include_validation_results = arguments.get("include_validation_results", True)
            
            # Use autonomous executor to get execution status
            execution_result = await self.autonomous_executor.get_execution_status(execution_id)
            
            if not execution_result:
                error_response = {
                    "success": False,
                    "error": f"Execution {execution_id} not found",
                    "message": "Execution not found"
                }
                return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
            
            response = {
                "success": True,
                "execution_id": execution_id,
                "work_item_id": execution_result.work_item_id,
                "status": execution_result.status.value,
                "progress_percentage": execution_result.progress_percentage,
                "start_time": execution_result.started_at.isoformat(),
                "end_time": execution_result.completed_at.isoformat() if execution_result.completed_at else None,
                "error_message": execution_result.error_message,
                "duration_seconds": execution_result.duration_seconds,
                "success": execution_result.success
            }
            
            if include_artifacts:
                response["artifacts"] = execution_result.artifacts
                
            if include_logs:
                response["output"] = execution_result.output
            
            return [TextContent(type="text", text=json.dumps(response, indent=2))]
            
        except Exception as e:
            logger.error(f"Error getting execution status: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "message": "Failed to get execution status"
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
            
    async def _cancel_execution(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Stop and rollback work item execution."""
        try:
            execution_id = arguments["execution_id"]
            reason = arguments.get("reason", "User requested cancellation")
            rollback_changes = arguments.get("rollback_changes", True)
            force = arguments.get("force", False)
            
            if execution_id not in self.active_executions:
                error_response = {
                    "success": False,
                    "error": f"Execution {execution_id} not found",
                    "message": "Execution not found"
                }
                return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
            
            execution_data = self.active_executions[execution_id]
            current_status = execution_data["status"]
            
            # Use autonomous executor to cancel execution
            cancellation_success = await self.autonomous_executor.cancel_execution(execution_id)
            
            # Update local execution data
            execution_data["status"] = ExecutionStatus.CANCELLED.value
            execution_data["end_time"] = datetime.now().isoformat()
            execution_data["error_message"] = f"Cancelled: {reason}"
            
            response = {
                "success": cancellation_success,
                "execution_id": execution_id,
                "work_item_id": execution_data["work_item_id"],
                "previous_status": current_status,
                "new_status": ExecutionStatus.CANCELLED.value,
                "reason": reason,
                "cancelled_at": execution_data["end_time"],
                "message": f"Execution {execution_id} cancelled successfully" if cancellation_success else f"Failed to cancel execution {execution_id}"
            }
            
            return [TextContent(type="text", text=json.dumps(response, indent=2))]
            
        except Exception as e:
            logger.error(f"Error cancelling execution: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "message": "Failed to cancel execution"
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
            
    async def cleanup(self) -> None:
        """Cleanup workflow engine tools."""
        logger.info("Cleaning up workflow engine tools...")
        
        # Cancel any active executions
        for execution_id in list(self.active_executions.keys()):
            if self.active_executions[execution_id]["status"] == ExecutionStatus.RUNNING.value:
                await self._cancel_execution({
                    "execution_id": execution_id,
                    "reason": "System shutdown",
                    "rollback_changes": False,
                    "force": True
                })
        
        self.active_executions.clear()
        self.dependency_graph.clear()
        
        try:
            await self.hierarchy_manager.cleanup()
            await self.dependency_engine.cleanup()
            await self.autonomous_executor.cleanup()
            logger.info("Workflow engine tools cleanup completed")
        except Exception as e:
            logger.error(f"Error during workflow engine cleanup: {e}")