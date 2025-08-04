"""Unified Execution Tool for MCP Jive.

Consolidates execution and monitoring operations:
- jive_execute_work_item
- jive_execute_workflow
- jive_get_execution_status
- jive_cancel_execution
- jive_validate_workflow
"""

import logging
from typing import Dict, Any, List, Optional, Union
from ..base import BaseTool
from datetime import datetime, timedelta
import asyncio
import uuid
try:
    from mcp.types import Tool
except ImportError:
    # Mock Tool type if MCP not available
    Tool = Dict[str, Any]

logger = logging.getLogger(__name__)


class UnifiedExecutionTool(BaseTool):
    """Unified tool for execution and monitoring operations."""
    
    def __init__(self, storage=None):
        super().__init__()
        self.storage = storage
        self.tool_name = "jive_execute_work_item"
        self.active_executions = {}  # Track active executions
    
    @property
    def name(self) -> str:
        """Tool name identifier."""
        return self.tool_name
    
    @property
    def description(self) -> str:
        """Tool description for AI agents."""
        return "Jive: Unified work item execution and workflow management - execute tasks, manage workflows, and track execution status"
    
    @property
    def category(self):
        """Tool category."""
        from ..base import ToolCategory
        return ToolCategory.EXECUTION_CONTROL
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        """Parameters schema for the tool."""
        return {
            "work_item_id": {
                "type": "string",
                "description": "Work item ID to execute"
            },
            "action": {
                "type": "string",
                "enum": ["execute", "status", "cancel", "validate"],
                "description": "Execution action to perform"
            },
            "execution_mode": {
                "type": "string",
                "enum": ["autonomous", "guided", "validation_only", "dry_run"],
                "description": "Execution mode for the work item"
            }
        }
    
    async def execute(self, params: Dict[str, Any]):
        """Execute the tool with given parameters."""
        from ..base import ToolResult
        try:
            # Handle different execution actions
            action = params.get("action", "execute")
            work_item_id = params.get("work_item_id")
            
            if not work_item_id:
                return ToolResult(
                    success=False,
                    data={},
                    error="work_item_id is required"
                )
            
            if action == "execute":
                return await self._execute_workflow(params)
            elif action == "status":
                return await self._check_status(params)
            elif action == "cancel":
                return await self._cancel_execution(params)
            elif action == "validate":
                return await self._validate_execution(params)
            else:
                return ToolResult(
                    success=False,
                    data={},
                    error=f"Unknown action: {action}"
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                error=f"Execution failed: {str(e)}"
            )
    
    async def get_tools(self) -> List[Tool]:
        """Get the unified execution management tool."""
        return [
            Tool(
                name="jive_execute_work_item",
                description="Jive: Unified work item execution and workflow management - execute tasks, manage workflows, and track execution status",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "work_item_id": {
                            "type": "string",
                            "description": "Work item ID to execute"
                        },
                        "action": {
                            "type": "string",
                            "enum": ["execute", "status", "cancel", "validate"],
                            "description": "Execution action to perform"
                        },
                        "execution_mode": {
                            "type": "string",
                            "enum": ["autonomous", "guided", "validation_only", "dry_run"],
                            "description": "Execution mode for the work item"
                        }
                    },
                    "required": ["work_item_id"]
                }
            )
        ]
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool schema."""
        return {
            "type": "function",
            "function": {
                "name": self.tool_name,
                "description": (
                    "Unified tool for executing work items and workflows. "
                    "Supports autonomous execution, monitoring, validation, and cancellation. "
                    "Can execute single work items or complex workflows with dependencies."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "work_item_id": {
                            "type": "string",
                            "description": "Work item ID (UUID, exact title, or keywords) to execute"
                        },
                        "execution_mode": {
                            "type": "string",
                            "enum": ["autonomous", "guided", "validation_only", "dry_run"],
                            "default": "autonomous",
                            "description": "Execution mode for the work item"
                        },
                        "action": {
                            "type": "string",
                            "enum": ["execute", "status", "cancel", "validate"],
                            "default": "execute",
                            "description": "Action to perform"
                        },
                        "execution_id": {
                            "type": "string",
                            "description": "Execution ID for status/cancel operations"
                        },
                        "workflow_config": {
                            "type": "object",
                            "properties": {
                                "execution_order": {
                                    "type": "string",
                                    "enum": ["sequential", "parallel", "dependency_based"],
                                    "default": "dependency_based",
                                    "description": "Order of execution for workflow tasks"
                                },
                                "auto_start_dependencies": {
                                    "type": "boolean",
                                    "default": True,
                                    "description": "Automatically start dependency execution"
                                },
                                "fail_fast": {
                                    "type": "boolean",
                                    "default": False,
                                    "description": "Stop execution on first failure"
                                },
                                "max_parallel_tasks": {
                                    "type": "integer",
                                    "minimum": 1,
                                    "maximum": 10,
                                    "default": 3,
                                    "description": "Maximum number of parallel tasks"
                                },
                                "timeout_minutes": {
                                    "type": "integer",
                                    "minimum": 1,
                                    "maximum": 1440,
                                    "default": 60,
                                    "description": "Execution timeout in minutes"
                                }
                            },
                            "description": "Configuration for workflow execution"
                        },
                        "execution_context": {
                            "type": "object",
                            "properties": {
                                "environment": {
                                    "type": "string",
                                    "enum": ["development", "staging", "production"],
                                    "default": "development",
                                    "description": "Execution environment"
                                },
                                "priority": {
                                    "type": "string",
                                    "enum": ["low", "medium", "high", "critical"],
                                    "default": "medium",
                                    "description": "Execution priority"
                                },
                                "assigned_agent": {
                                    "type": "string",
                                    "description": "Specific AI agent to assign execution to"
                                },
                                "resource_limits": {
                                    "type": "object",
                                    "properties": {
                                        "max_memory_mb": {"type": "integer"},
                                        "max_cpu_percent": {"type": "integer"},
                                        "max_duration_minutes": {"type": "integer"}
                                    },
                                    "description": "Resource limits for execution"
                                }
                            },
                            "description": "Context and constraints for execution"
                        },
                        "validation_options": {
                            "type": "object",
                            "properties": {
                                "check_dependencies": {
                                    "type": "boolean",
                                    "default": True,
                                    "description": "Validate dependencies before execution"
                                },
                                "check_resources": {
                                    "type": "boolean",
                                    "default": True,
                                    "description": "Validate resource availability"
                                },
                                "check_acceptance_criteria": {
                                    "type": "boolean",
                                    "default": True,
                                    "description": "Validate acceptance criteria are defined"
                                },
                                "dry_run_first": {
                                    "type": "boolean",
                                    "default": False,
                                    "description": "Perform dry run before actual execution"
                                }
                            },
                            "description": "Validation options before execution"
                        },
                        "monitoring_config": {
                            "type": "object",
                            "properties": {
                                "progress_updates": {
                                    "type": "boolean",
                                    "default": True,
                                    "description": "Enable progress updates"
                                },
                                "update_interval_seconds": {
                                    "type": "integer",
                                    "minimum": 5,
                                    "maximum": 300,
                                    "default": 30,
                                    "description": "Progress update interval"
                                },
                                "notify_on_completion": {
                                    "type": "boolean",
                                    "default": True,
                                    "description": "Send notification on completion"
                                },
                                "notify_on_failure": {
                                    "type": "boolean",
                                    "default": True,
                                    "description": "Send notification on failure"
                                }
                            },
                            "description": "Monitoring and notification configuration"
                        },
                        "cancel_options": {
                            "type": "object",
                            "properties": {
                                "reason": {
                                    "type": "string",
                                    "description": "Reason for cancellation"
                                },
                                "force": {
                                    "type": "boolean",
                                    "default": False,
                                    "description": "Force cancellation even if in critical state"
                                },
                                "rollback_changes": {
                                    "type": "boolean",
                                    "default": False,
                                    "description": "Rollback changes made during execution"
                                }
                            },
                            "description": "Options for execution cancellation"
                        }
                    },
                    "required": ["work_item_id"]
                }
            }
        }
    
    async def _execute_workflow(self, params: Dict[str, Any]):
        """Execute a workflow."""
        from ..base import ToolResult
        import uuid
        
        work_item_id = params["work_item_id"]
        execution_mode = params.get("execution_mode", "autonomous")
        execution_id = str(uuid.uuid4())
        
        # Mock execution for now
        self.active_executions[execution_id] = {
            "work_item_id": work_item_id,
            "status": "running",
            "mode": execution_mode,
            "progress": 0
        }
        
        return ToolResult(
            success=True,
            data={
                "execution_id": execution_id,
                "status": "started",
                "work_item_id": work_item_id,
                "mode": execution_mode
            }
        )
    
    async def _check_status(self, params: Dict[str, Any]):
        """Check execution status."""
        from ..base import ToolResult
        
        execution_id = params.get("execution_id")
        if execution_id in self.active_executions:
            execution = self.active_executions[execution_id]
            return ToolResult(
                success=True,
                data={
                    "execution_id": execution_id,
                    "status": execution["status"],
                    "progress": execution["progress"],
                    "work_item_id": execution["work_item_id"]
                }
            )
        else:
            return ToolResult(
                success=False,
                data={},
                error=f"Execution {execution_id} not found"
            )
    
    async def _cancel_execution(self, params: Dict[str, Any]):
        """Cancel an execution."""
        from ..base import ToolResult
        
        execution_id = params.get("execution_id")
        if execution_id in self.active_executions:
            self.active_executions[execution_id]["status"] = "cancelled"
            return ToolResult(
                success=True,
                data={
                    "execution_id": execution_id,
                    "status": "cancelled"
                }
            )
        else:
            return ToolResult(
                success=False,
                data={},
                error=f"Execution {execution_id} not found"
            )
    
    async def _validate_execution(self, params: Dict[str, Any]):
        """Validate execution parameters."""
        from ..base import ToolResult
        
        work_item_id = params["work_item_id"]
        validation_rules = params.get("validation_rules", [])
        
        # Mock validation
        validation_results = {
            "work_item_id": work_item_id,
            "validation_rules": validation_rules,
            "results": {
                "pre_conditions": "passed" if "pre_conditions" in validation_rules else "skipped",
                "post_conditions": "passed" if "post_conditions" in validation_rules else "skipped"
            },
            "overall_status": "valid"
        }
        
        return ToolResult(
            success=True,
            data={"validation_results": validation_results}
        )

    async def handle_tool_call(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle the unified execution tool call."""
        try:
            action = params.get("action", "execute")
            
            if action == "execute":
                return await self._execute_work_item(params)
            elif action == "status":
                return await self._get_execution_status(params)
            elif action == "cancel":
                return await self._cancel_execution(params)
            elif action == "validate":
                return await self._validate_execution(params)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "error_code": "INVALID_ACTION"
                }
        
        except Exception as e:
            logger.error(f"Error in unified execution tool: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "EXECUTION_ERROR"
            }
    
    async def _execute_work_item(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a work item or workflow."""
        work_item_id = params["work_item_id"]
        execution_mode = params.get("execution_mode", "autonomous")
        workflow_config = params.get("workflow_config", {})
        execution_context = params.get("execution_context", {})
        validation_options = params.get("validation_options", {})
        monitoring_config = params.get("monitoring_config", {})
        
        # Resolve work item ID
        resolved_id = await self._resolve_work_item_id(work_item_id)
        if not resolved_id:
            return {
                "success": False,
                "error": f"Work item not found: {work_item_id}",
                "error_code": "WORK_ITEM_NOT_FOUND"
            }
        
        # Get work item
        work_item = await self.storage.get_work_item(resolved_id)
        if not work_item:
            return {
                "success": False,
                "error": f"Work item not found: {resolved_id}",
                "error_code": "WORK_ITEM_NOT_FOUND"
            }
        
        # Validate before execution
        if validation_options.get("check_dependencies", True):
            validation_result = await self._validate_dependencies(resolved_id)
            if not validation_result["success"]:
                return {
                    "success": False,
                    "error": "Dependency validation failed",
                    "validation_errors": validation_result["issues"],
                    "error_code": "VALIDATION_FAILED"
                }
        
        # Create execution record
        execution_id = str(uuid.uuid4())
        execution_record = {
            "execution_id": execution_id,
            "work_item_id": resolved_id,
            "work_item_title": work_item.title,
            "execution_mode": execution_mode,
            "status": "initializing",
            "progress_percentage": 0,
            "started_at": datetime.now().isoformat(),
            "estimated_completion": None,
            "workflow_config": workflow_config,
            "execution_context": execution_context,
            "monitoring_config": monitoring_config,
            "steps": [],
            "logs": [],
            "metrics": {
                "tasks_completed": 0,
                "tasks_failed": 0,
                "total_tasks": 0
            }
        }
        
        self.active_executions[execution_id] = execution_record
        
        # Start execution based on mode
        if execution_mode == "dry_run":
            return await self._perform_dry_run(execution_id, work_item)
        elif execution_mode == "validation_only":
            return await self._perform_validation_only(execution_id, work_item)
        else:
            # Start actual execution
            asyncio.create_task(self._execute_work_item_async(execution_id, work_item))
            
            return {
                "success": True,
                "execution_id": execution_id,
                "status": "started",
                "message": f"Execution started for work item: {work_item.title}",
                "work_item": {
                    "id": work_item.id,
                    "title": work_item.title,
                    "type": work_item.type,
                    "status": work_item.status
                },
                "execution_config": {
                    "mode": execution_mode,
                    "workflow_config": workflow_config,
                    "monitoring_enabled": monitoring_config.get("progress_updates", True)
                }
            }
    
    async def _execute_work_item_async(self, execution_id: str, work_item: Dict[str, Any]):
        """Asynchronously execute a work item."""
        execution = self.active_executions[execution_id]
        
        try:
            # Update status to running
            execution["status"] = "running"
            execution["progress_percentage"] = 10
            
            # Determine execution strategy
            if work_item.get('type') in ["epic", "initiative"]:
                await self._execute_workflow(execution_id, work_item)
            else:
                await self._execute_single_task(execution_id, work_item)
            
            # Mark as completed
            execution["status"] = "completed"
            execution["progress_percentage"] = 100
            execution["completed_at"] = datetime.now().isoformat()
            
            # Update work item status
            if self.storage:
                await self.storage.update_work_item(work_item.get('id'), {
                    "status": "completed",
                    "progress_percentage": 100,
                    "completed_at": datetime.now().isoformat()
                })
            
        except Exception as e:
            logger.error(f"Execution failed for {execution_id}: {str(e)}")
            execution["status"] = "failed"
            execution["error"] = str(e)
            execution["failed_at"] = datetime.now().isoformat()
    
    async def _execute_workflow(self, execution_id: str, work_item: Dict[str, Any]):
        """Execute a workflow (epic/initiative with children)."""
        execution = self.active_executions[execution_id]
        workflow_config = execution["workflow_config"]
        
        # Get child work items
        children = await self._get_child_work_items(work_item.get('id'))
        execution["metrics"]["total_tasks"] = len(children)
        
        if not children:
            execution["logs"].append({
                "timestamp": datetime.now().isoformat(),
                "level": "info",
                "message": "No child tasks found for workflow"
            })
            return
        
        execution_order = workflow_config.get("execution_order", "dependency_based")
        max_parallel = workflow_config.get("max_parallel_tasks", 3)
        fail_fast = workflow_config.get("fail_fast", False)
        
        if execution_order == "sequential":
            await self._execute_sequential(execution_id, children, fail_fast)
        elif execution_order == "parallel":
            await self._execute_parallel(execution_id, children, max_parallel, fail_fast)
        else:  # dependency_based
            await self._execute_dependency_based(execution_id, children, max_parallel, fail_fast)
    
    async def _execute_single_task(self, execution_id: str, work_item: Dict[str, Any]):
        """Execute a single task."""
        execution = self.active_executions[execution_id]
        execution["metrics"]["total_tasks"] = 1
        
        # Simulate task execution steps
        steps = [
            {"name": "analyze_requirements", "progress": 20},
            {"name": "design_solution", "progress": 40},
            {"name": "implement_solution", "progress": 70},
            {"name": "test_solution", "progress": 90},
            {"name": "finalize", "progress": 100}
        ]
        
        for step in steps:
            execution["progress_percentage"] = step["progress"]
            execution["steps"].append({
                "name": step["name"],
                "status": "completed",
                "completed_at": datetime.now().isoformat()
            })
            
            execution["logs"].append({
                "timestamp": datetime.now().isoformat(),
                "level": "info",
                "message": f"Completed step: {step['name']}"
            })
            
            # Simulate work
            await asyncio.sleep(1)
        
        execution["metrics"]["tasks_completed"] = 1
    
    async def _execute_sequential(self, execution_id: str, children: List[Dict[str, Any]], fail_fast: bool):
        """Execute children sequentially."""
        execution = self.active_executions[execution_id]
        
        for i, child in enumerate(children):
            try:
                await self._execute_child_task(execution_id, child)
                execution["metrics"]["tasks_completed"] += 1
                execution["progress_percentage"] = int((i + 1) / len(children) * 90)
            except Exception as e:
                execution["metrics"]["tasks_failed"] += 1
                if fail_fast:
                    raise e
    
    async def _execute_parallel(self, execution_id: str, children: List[Dict[str, Any]], 
                               max_parallel: int, fail_fast: bool):
        """Execute children in parallel batches."""
        execution = self.active_executions[execution_id]
        
        # Process in batches
        for i in range(0, len(children), max_parallel):
            batch = children[i:i + max_parallel]
            tasks = [self._execute_child_task(execution_id, child) for child in batch]
            
            if fail_fast:
                await asyncio.gather(*tasks)
            else:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in results:
                    if isinstance(result, Exception):
                        execution["metrics"]["tasks_failed"] += 1
                    else:
                        execution["metrics"]["tasks_completed"] += 1
            
            execution["progress_percentage"] = int((i + len(batch)) / len(children) * 90)
    
    async def _execute_dependency_based(self, execution_id: str, children: List[Dict[str, Any]],
                                       max_parallel: int, fail_fast: bool):
        """Execute children based on dependency order."""
        execution = self.active_executions[execution_id]
        
        # Build dependency graph
        dependency_graph = await self._build_dependency_graph(children)
        
        # Execute in dependency order
        completed = set()
        running = set()
        
        while len(completed) < len(children):
            # Find ready tasks (dependencies completed)
            ready_tasks = []
            for child in children:
                if (child.get('id') not in completed and 
                    child.get('id') not in running and 
                    len(ready_tasks) < max_parallel):
                    
                    dependencies = dependency_graph.get(child.get('id'), [])
                    if all(dep_id in completed for dep_id in dependencies):
                        ready_tasks.append(child)
            
            if not ready_tasks:
                break  # No more tasks can be started
            
            # Start ready tasks
            tasks = []
            for child in ready_tasks:
                running.add(child.get('id'))
                tasks.append(self._execute_child_task(execution_id, child))
            
            # Wait for completion
            if fail_fast:
                await asyncio.gather(*tasks)
                for child in ready_tasks:
                    completed.add(child.get('id'))
                    running.remove(child.get('id'))
                    execution["metrics"]["tasks_completed"] += 1
            else:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for i, result in enumerate(results):
                    child = ready_tasks[i]
                    completed.add(child.get('id'))
                    running.remove(child.get('id'))
                    
                    if isinstance(result, Exception):
                        execution["metrics"]["tasks_failed"] += 1
                    else:
                        execution["metrics"]["tasks_completed"] += 1
            
            execution["progress_percentage"] = int(len(completed) / len(children) * 90)
    
    async def _execute_child_task(self, execution_id: str, child: Dict[str, Any]):
        """Execute a single child task."""
        execution = self.active_executions[execution_id]
        
        execution["logs"].append({
            "timestamp": datetime.now().isoformat(),
            "level": "info",
            "message": f"Starting execution of: {child.get('title', 'Unknown')}"
        })
        
        # Simulate task execution
        await asyncio.sleep(2)
        
        # Update child status
        if self.storage:
            await self.storage.update_work_item(child.get('id'), {
                "status": "completed",
                "progress_percentage": 100,
                "completed_at": datetime.now().isoformat()
            })
        
        execution["logs"].append({
            "timestamp": datetime.now().isoformat(),
            "level": "info",
            "message": f"Completed execution of: {child.get('title', 'Unknown')}"
        })
    
    async def _get_execution_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get execution status."""
        execution_id = params.get("execution_id")
        
        if not execution_id:
            return {
                "success": False,
                "error": "execution_id is required for status action",
                "error_code": "MISSING_EXECUTION_ID"
            }
        
        if execution_id not in self.active_executions:
            return {
                "success": False,
                "error": f"Execution not found: {execution_id}",
                "error_code": "EXECUTION_NOT_FOUND"
            }
        
        execution = self.active_executions[execution_id]
        
        return {
            "success": True,
            "execution_id": execution_id,
            "status": execution["status"],
            "progress_percentage": execution["progress_percentage"],
            "work_item": {
                "id": execution["work_item_id"],
                "title": execution["work_item_title"]
            },
            "timing": {
                "started_at": execution["started_at"],
                "completed_at": execution.get("completed_at"),
                "failed_at": execution.get("failed_at")
            },
            "metrics": execution["metrics"],
            "steps": execution["steps"],
            "recent_logs": execution["logs"][-10:],  # Last 10 log entries
            "error": execution.get("error")
        }
    
    async def _cancel_execution(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Cancel an active execution."""
        execution_id = params.get("execution_id")
        cancel_options = params.get("cancel_options", {})
        
        if not execution_id:
            return {
                "success": False,
                "error": "execution_id is required for cancel action",
                "error_code": "MISSING_EXECUTION_ID"
            }
        
        if execution_id not in self.active_executions:
            return {
                "success": False,
                "error": f"Execution not found: {execution_id}",
                "error_code": "EXECUTION_NOT_FOUND"
            }
        
        execution = self.active_executions[execution_id]
        
        if execution["status"] in ["completed", "failed", "cancelled"]:
            return {
                "success": False,
                "error": f"Cannot cancel execution in status: {execution['status']}",
                "error_code": "INVALID_STATUS_FOR_CANCEL"
            }
        
        # Cancel execution
        execution["status"] = "cancelled"
        execution["cancelled_at"] = datetime.now().isoformat()
        execution["cancel_reason"] = cancel_options.get("reason", "User requested cancellation")
        
        execution["logs"].append({
            "timestamp": datetime.now().isoformat(),
            "level": "warning",
            "message": f"Execution cancelled: {execution['cancel_reason']}"
        })
        
        return {
            "success": True,
            "execution_id": execution_id,
            "status": "cancelled",
            "message": "Execution cancelled successfully",
            "cancel_reason": execution["cancel_reason"]
        }
    
    async def _validate_execution(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate execution readiness."""
        work_item_id = params["work_item_id"]
        validation_options = params.get("validation_options", {})
        
        # Resolve work item ID
        resolved_id = await self._resolve_work_item_id(work_item_id)
        if not resolved_id:
            return {
                "success": False,
                "error": f"Work item not found: {work_item_id}",
                "error_code": "WORK_ITEM_NOT_FOUND"
            }
        
        validation_results = {
            "success": True,
            "work_item_id": resolved_id,
            "validation_summary": {
                "total_checks": 0,
                "passed_checks": 0,
                "failed_checks": 0
            },
            "checks": []
        }
        
        # Check dependencies
        if validation_options.get("check_dependencies", True):
            dep_result = await self._validate_dependencies(resolved_id)
            validation_results["checks"].append({
                "name": "dependencies",
                "status": "passed" if dep_result["success"] else "failed",
                "details": dep_result
            })
        
        # Check acceptance criteria
        if validation_options.get("check_acceptance_criteria", True):
            ac_result = await self._validate_acceptance_criteria(resolved_id)
            validation_results["checks"].append({
                "name": "acceptance_criteria",
                "status": "passed" if ac_result["success"] else "failed",
                "details": ac_result
            })
        
        # Calculate summary
        validation_results["validation_summary"]["total_checks"] = len(validation_results["checks"])
        validation_results["validation_summary"]["passed_checks"] = sum(
            1 for check in validation_results["checks"] if check["status"] == "passed"
        )
        validation_results["validation_summary"]["failed_checks"] = sum(
            1 for check in validation_results["checks"] if check["status"] == "failed"
        )
        
        validation_results["success"] = validation_results["validation_summary"]["failed_checks"] == 0
        
        return validation_results
    
    async def _perform_dry_run(self, execution_id: str, work_item: Dict[str, Any]) -> Dict[str, Any]:
        """Perform a dry run execution."""
        execution = self.active_executions[execution_id]
        execution["status"] = "dry_run_completed"
        execution["progress_percentage"] = 100
        
        # Simulate what would happen
        dry_run_results = {
            "success": True,
            "execution_id": execution_id,
            "dry_run": True,
            "work_item": {
                "id": work_item.id,
                "title": work_item.title,
                "type": work_item.type
            },
            "simulation_results": {
                "estimated_duration_minutes": 30,
                "estimated_steps": 5,
                "resource_requirements": {
                    "memory_mb": 512,
                    "cpu_percent": 25
                },
                "potential_issues": [],
                "success_probability": 0.95
            }
        }
        
        return dry_run_results
    
    async def _perform_validation_only(self, execution_id: str, work_item: Dict[str, Any]) -> Dict[str, Any]:
        """Perform validation-only execution."""
        execution = self.active_executions[execution_id]
        execution["status"] = "validation_completed"
        execution["progress_percentage"] = 100
        
        # Perform comprehensive validation
        validation_result = await self._validate_execution({
            "work_item_id": work_item.id,
            "validation_options": {
                "check_dependencies": True,
                "check_resources": True,
                "check_acceptance_criteria": True
            }
        })
        
        validation_result["execution_id"] = execution_id
        validation_result["validation_only"] = True
        
        return validation_result
    
    # Helper methods
    async def _resolve_work_item_id(self, work_item_id: str) -> Optional[str]:
        """Resolve work item ID from UUID, title, or keywords."""
        # Try UUID first
        if validate_uuid(work_item_id):
            if await validate_work_item_exists(work_item_id, self.storage):
                return work_item_id
        
        # Try exact title match
        work_items = await self.storage.list_work_items()
        for item in work_items:
            if item.title.lower() == work_item_id.lower():
                return item.id
        
        # Try keyword search
        keywords = work_item_id.lower().split()
        for item in work_items:
            item_text = f"{item.title} {item.description or ''}".lower()
            if all(keyword in item_text for keyword in keywords):
                return item.id
        
        return None
    
    async def _get_child_work_items(self, parent_id: str) -> List[Dict[str, Any]]:
        """Get child work items."""
        all_items = await self.storage.list_work_items()
        return [item for item in all_items if item.parent_id == parent_id]
    
    async def _build_dependency_graph(self, work_items: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Build dependency graph for work items."""
        graph = {}
        for item in work_items:
            dependencies = getattr(item, "dependencies", [])
            graph[item.id] = [dep for dep in dependencies if dep in [wi.id for wi in work_items]]
        return graph
    
    async def _validate_dependencies(self, work_item_id: str) -> Dict[str, Any]:
        """Validate dependencies for a work item."""
        work_item = await self.storage.get_work_item(work_item_id)
        dependencies = getattr(work_item, "dependencies", [])
        
        issues = []
        for dep_id in dependencies:
            dep_item = await self.storage.get_work_item(dep_id)
            if not dep_item:
                issues.append(f"Missing dependency: {dep_id}")
            elif dep_item.status not in ["completed", "in_progress"]:
                issues.append(f"Dependency not ready: {dep_item.title} ({dep_item.status})")
        
        return {
            "success": len(issues) == 0,
            "issues": issues,
            "dependencies_checked": len(dependencies)
        }
    
    async def _validate_acceptance_criteria(self, work_item_id: str) -> Dict[str, Any]:
        """Validate acceptance criteria for a work item."""
        work_item = await self.storage.get_work_item(work_item_id)
        acceptance_criteria = getattr(work_item, "acceptance_criteria", [])
        
        if not acceptance_criteria:
            return {
                "success": False,
                "issues": ["No acceptance criteria defined"],
                "criteria_count": 0
            }
        
        return {
            "success": True,
            "issues": [],
            "criteria_count": len(acceptance_criteria)
        }


# Export the tool
EXECUTION_TOOLS = [UnifiedExecutionTool]