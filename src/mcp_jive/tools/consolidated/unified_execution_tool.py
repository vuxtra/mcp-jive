"""Unified Execution Tool for MCP Jive.

Consolidates execution and monitoring operations:
- jive_execute_work_item
- jive_execute_workflow
- jive_get_execution_status
- jive_cancel_execution
- jive_validate_workflow
- AI guidance and planning capabilities
"""

import logging
from typing import Dict, Any, List, Optional, Union
from ..base import BaseTool, ToolResult
from datetime import datetime, timedelta
import asyncio
import uuid
try:
    import numpy as np
except ImportError:
    np = None
from ...uuid_utils import validate_uuid, validate_work_item_exists
from ...planning.execution_planner import ExecutionPlanner
from ...planning.ai_guidance_generator import AIGuidanceGenerator
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
        self.execution_planner = ExecutionPlanner(storage)
        self.ai_guidance_generator = AIGuidanceGenerator()
    
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
                "enum": ["execute", "status", "cancel", "validate", "plan", "guide", "instruct", "prompt"],
                "description": "Execution action to perform"
            },
            "execution_mode": {
                "type": "string",
                "enum": ["autonomous", "guided", "validation_only", "dry_run"],
                "description": "Execution mode for the work item"
            }
        }
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters."""
        try:
            # Handle different execution actions
            action = kwargs.get("action", "execute")
            work_item_id = kwargs.get("work_item_id")
            
            if not work_item_id:
                return ToolResult(
                    success=False,
                    error="work_item_id is required"
                )
            
            if action == "execute":
                result = await self._execute_work_item(kwargs)
                return ToolResult(
                    success=result.get("success", False),
                    data=result,
                    message=result.get("message"),
                    error=result.get("error"),
                    metadata=result.get("metadata")
                )
            elif action == "status":
                result = await self._check_status(kwargs)
                return ToolResult(
                    success=result.get("success", False),
                    data=result.get("data"),
                    message=result.get("message"),
                    error=result.get("error"),
                    metadata=result.get("metadata")
                )
            elif action == "cancel":
                result = await self._cancel_execution(kwargs)
                return ToolResult(
                    success=result.get("success", False),
                    data=result.get("data"),
                    message=result.get("message"),
                    error=result.get("error"),
                    metadata=result.get("metadata")
                )
            elif action == "validate":
                result = await self._validate_execution(kwargs)
                return ToolResult(
                    success=result.get("success", False),
                    data=result.get("data"),
                    message=result.get("message"),
                    error=result.get("error"),
                    metadata=result.get("metadata")
                )
            elif action == "plan":
                result = await self._generate_execution_plan(kwargs)
                return ToolResult(
                    success=result.get("success", False),
                    data=result.get("data"),
                    message=result.get("message"),
                    error=result.get("error"),
                    metadata=result.get("metadata")
                )
            elif action == "guide":
                result = await self._generate_ai_guidance(kwargs)
                return ToolResult(
                    success=result.get("success", False),
                    data=result.get("data"),
                    message=result.get("message"),
                    error=result.get("error"),
                    metadata=result.get("metadata")
                )
            elif action == "instruct":
                result = await self._generate_instructions(kwargs)
                return ToolResult(
                    success=result.get("success", False),
                    data=result.get("data"),
                    message=result.get("message"),
                    error=result.get("error"),
                    metadata=result.get("metadata")
                )
            elif action == "prompt":
                result = await self._generate_prompt_template(kwargs)
                return ToolResult(
                    success=result.get("success", False),
                    data=result.get("data"),
                    message=result.get("message"),
                    error=result.get("error"),
                    metadata=result.get("metadata")
                )
            else:
                return ToolResult(
                    success=False,
                    error=f"Unknown action: {action}"
                )
                
        except Exception as e:
            logger.error(f"Error in unified execution tool execute: {str(e)}")
            return ToolResult(
                success=False,
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
                            "enum": ["execute", "status", "cancel", "validate", "plan", "guide", "instruct", "prompt"],
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
            "name": self.tool_name,
            "description": (
                "Unified tool for executing work items and workflows. "
                "Supports execution, monitoring, validation, and cancellation. "
                "Can execute single work items or complex workflows with dependencies."
            ),
            "inputSchema": {
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
                        "enum": ["execute", "status", "cancel", "validate", "plan", "guide", "instruct", "prompt"],
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
                    },
                    "guidance_type": {
                        "type": "string",
                        "enum": ["comprehensive", "execution", "validation", "troubleshooting"],
                        "default": "comprehensive",
                        "description": "Type of AI guidance to generate"
                    },
                    "planning_scope": {
                        "type": "string",
                        "enum": ["single_item", "hierarchy", "dependencies", "full_project"],
                        "default": "single_item",
                        "description": "Scope of planning analysis"
                    },
                    "instruction_detail": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                        "default": "medium",
                        "description": "Level of detail for generated instructions"
                    },
                    "prompt_template_type": {
                        "type": "string",
                        "enum": ["execution", "validation", "planning", "instruction"],
                        "default": "execution",
                        "description": "Type of prompt template to generate"
                    },
                    "include_context": {
                        "type": "boolean",
                        "default": True,
                        "description": "Include work item context in guidance"
                    },
                    "include_dependencies": {
                        "type": "boolean",
                        "default": True,
                        "description": "Include dependency analysis in planning"
                    }
                },
                "required": ["work_item_id"]
            }
        }
    
    async def _execute_workflow(self, kwargs: Dict[str, Any]):
        """Execute a workflow."""
        import uuid
        
        work_item_id = kwargs["work_item_id"]
        execution_mode = kwargs.get("execution_mode", "mcp_client")
        execution_id = str(uuid.uuid4())
        
        # Mock execution for now
        self.active_executions[execution_id] = {
            "work_item_id": work_item_id,
            "status": "running",
            "mode": execution_mode,
            "progress": 0
        }
        
        return {
            "success": True,
            "data": {
                "execution_id": execution_id,
                "status": "started",
                "work_item_id": work_item_id,
                "mode": execution_mode
            }
        }
    
    async def _check_status(self, kwargs: Dict[str, Any]):
        """Check execution status."""
        
        execution_id = kwargs.get("execution_id")
        if execution_id in self.active_executions:
            execution = self.active_executions[execution_id]
            return {
                "success": True,
                "data": {
                    "execution_id": execution_id,
                    "status": execution["status"],
                    "progress": execution["progress"],
                    "work_item_id": execution["work_item_id"]
                }
            }
        else:
            return {
                "success": False,
                "data": {},
                "error": f"Execution {execution_id} not found"
            }
    
    async def _cancel_execution(self, kwargs: Dict[str, Any]):
        """Cancel an execution."""
        
        execution_id = kwargs.get("execution_id")
        if execution_id in self.active_executions:
            self.active_executions[execution_id]["status"] = "cancelled"
            return {
                "success": True,
                "data": {
                    "execution_id": execution_id,
                    "status": "cancelled"
                }
            }
        else:
            return {
                "success": False,
                "data": {},
                "error": f"Execution {execution_id} not found"
            }
    
    async def _validate_execution(self, kwargs: Dict[str, Any]):
        """Validate execution parameters."""
        
        work_item_id = kwargs["work_item_id"]
        validation_rules = kwargs.get("validation_rules", [])
        
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
        
        return {
            "success": True,
            "data": {"validation_results": validation_results}
        }

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
            elif action == "plan":
                return await self._generate_execution_plan(params)
            elif action == "guide":
                return await self._generate_ai_guidance(params)
            elif action == "instruct":
                return await self._generate_instructions(params)
            elif action == "prompt":
                return await self._generate_prompt_template(params)
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
        """Provide AI guidance and task orchestration for work item execution."""
        work_item_id = params["work_item_id"]
        execution_mode = params.get("execution_mode", "guided")
        priority_setting = params.get("priority_setting", "dependency_order")
        include_context = params.get("include_context", True)
        
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
        
        # Generate hierarchical execution plan
        execution_summary = await self._generate_execution_summary(resolved_id, priority_setting)
        
        # Get next actionable task with detailed instructions
        next_task_guidance = await self._get_next_task_guidance(execution_summary, include_context)
        
        # Create execution session for progress tracking
        execution_id = str(uuid.uuid4())
        execution_session = {
            "execution_id": execution_id,
            "root_work_item_id": resolved_id,
            "execution_summary": execution_summary,
            "current_task_index": 0,
            "status": "ready",
            "started_at": datetime.now().isoformat(),
            "progress_updates": [],
            "logs": []
        }
        
        self.active_executions[execution_id] = execution_session
        
        return {
            "success": True,
            "execution_id": execution_id,
            "execution_summary": execution_summary,
            "next_task": next_task_guidance,
            "message": "Here is the execution plan and your first task. Please keep me updated on progress as you work.",
            "instructions": {
                "progress_reporting": "Please report progress back to this tool using the 'status' action with your execution_id",
                "task_completion": "When you complete the current task, call this tool again to get the next task",
                "issue_reporting": "If you encounter blockers, report them immediately for guidance"
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
                await self._execute_workflow_internal(execution_id, work_item)
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
            
            # Update work item status to reflect failure
            if self.storage:
                try:
                    await self.storage.update_work_item(work_item.get('id'), {
                        "status": "blocked",
                        "notes": f"Execution failed: {str(e)}"
                    })
                except Exception as update_error:
                    logger.error(f"Failed to update work item status: {str(update_error)}")
    
    async def _execute_workflow_internal(self, execution_id: str, work_item: Dict[str, Any]):
        """Execute a workflow (epic/initiative with children)."""
        execution = self.active_executions[execution_id]
        workflow_config = execution["workflow_config"]
        
        # Get child work items
        children = await self._get_child_work_items(work_item.get('id'))
        execution["metrics"]["total_tasks"] = len(children)
        
        # Safe handling of children to avoid numpy array ambiguity
        try:
            if children is None:
                children_empty = True
            elif hasattr(children, 'tolist'):
                children = children.tolist()
                children_empty = len(children) == 0
            elif isinstance(children, (list, tuple)):
                children_empty = len(children) == 0
            else:
                try:
                    children_empty = len(list(children)) == 0
                except Exception:
                    children_empty = True
        except Exception:
            children_empty = True
        
        if children_empty:
            self._safe_log_append(execution, {
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
            
            self._safe_log_append(execution, {
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
                child_id = str(child.get('id'))  # Convert to string to avoid numpy issues
                if (child_id not in completed and 
                    child_id not in running and 
                    len(ready_tasks) < max_parallel):
                    
                    dependencies = dependency_graph.get(child_id, [])
                    # Ensure dependencies is a Python list to avoid numpy array issues
                    if hasattr(dependencies, 'tolist'):
                        dependencies = dependencies.tolist()
                    # Convert dependency IDs to strings to avoid numpy comparison issues
                    dependencies = [str(dep_id) for dep_id in dependencies]
                    if all(dep_id in completed for dep_id in dependencies):
                        ready_tasks.append(child)
            
            if len(ready_tasks) == 0:
                break  # No more tasks can be started
            
            # Start ready tasks
            tasks = []
            for child in ready_tasks:
                running.add(str(child.get('id')))  # Convert to string to avoid numpy issues
                tasks.append(self._execute_child_task(execution_id, child))
            
            # Wait for completion
            if fail_fast:
                await asyncio.gather(*tasks)
                for child in ready_tasks:
                    child_id = str(child.get('id'))  # Convert to string to avoid numpy issues
                    completed.add(child_id)
                    running.remove(child_id)
                    execution["metrics"]["tasks_completed"] += 1
            else:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for i, result in enumerate(results):
                    child = ready_tasks[i]
                    child_id = str(child.get('id'))  # Convert to string to avoid numpy issues
                    completed.add(child_id)
                    running.remove(child_id)
                    
                    if isinstance(result, Exception):
                        execution["metrics"]["tasks_failed"] += 1
                    else:
                        execution["metrics"]["tasks_completed"] += 1
            
            execution["progress_percentage"] = int(len(completed) / len(children) * 90)
    
    async def _execute_child_task(self, execution_id: str, child: Dict[str, Any]):
        """Execute a single child task."""
        execution = self.active_executions[execution_id]
        
        self._safe_log_append(execution, {
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
        
        self._safe_log_append(execution, {
            "timestamp": datetime.now().isoformat(),
            "level": "info",
            "message": f"Completed execution of: {child.get('title', 'Unknown')}"
        })
    
    async def _get_execution_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get execution status and handle progress updates."""
        execution_id = params.get("execution_id")
        progress_update = params.get("progress_update")
        
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
        
        # Handle progress update if provided
        if progress_update:
            await self._update_execution_progress(execution_id, progress_update)
        
        # Check if current task is completed and get next task
        next_task_guidance = None
        if progress_update and progress_update.get("task_completed"):
            next_task_guidance = await self._advance_to_next_task(execution_id)
        
        response = {
            "success": True,
            "execution_id": execution_id,
            "status": execution["status"],
            "current_task_index": execution.get("current_task_index", 0),
            "total_tasks": execution["execution_summary"]["total_tasks"],
            "progress_percentage": self._calculate_progress_percentage(execution),
            "root_work_item": execution["execution_summary"]["root_work_item"],
            "timing": {
                "started_at": execution["started_at"]
            },
            "recent_updates": self._safe_get_recent_updates(execution.get("progress_updates"))
        }
        
        # Add next task guidance if available
        if next_task_guidance:
            response["next_task"] = next_task_guidance
            response["message"] = "Task completed! Here is your next task."
        elif execution["status"] == "completed":
            response["message"] = "All tasks completed successfully!"
        else:
            response["message"] = "Execution in progress. Continue with current task."
        
        return response
    
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
        
        # Safely handle logs - ensure it's a list
        if "logs" not in execution:
            execution["logs"] = []
        elif hasattr(execution["logs"], 'tolist'):
            execution["logs"] = execution["logs"].tolist()
        elif not isinstance(execution["logs"], list):
            execution["logs"] = list(execution["logs"]) if execution["logs"] else []
        
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
                "id": work_item.get("id"),
                "title": work_item.get("title", "Unknown"),
                "type": work_item.get("type")
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
            "work_item_id": work_item.get("id"),
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
    def _safe_log_append(self, execution: Dict[str, Any], log_entry: Dict[str, Any]) -> None:
        """Safely append to execution logs, handling numpy arrays."""
        if "logs" not in execution:
            execution["logs"] = []
        elif hasattr(execution["logs"], 'tolist'):
            execution["logs"] = execution["logs"].tolist()
        elif not isinstance(execution["logs"], list):
            execution["logs"] = list(execution["logs"]) if execution["logs"] else []
        
        execution["logs"].append(log_entry)
    
    async def _resolve_work_item_id(self, work_item_id: str) -> Optional[str]:
        """Resolve work item ID from UUID, title, or keywords."""
        # Try UUID first
        if validate_uuid(work_item_id):
            if await validate_work_item_exists(work_item_id, self.storage):
                return work_item_id
        
        # Try exact title match
        work_items = await self.storage.list_work_items()
        for item in work_items:
            item_title = item.get("title", "")
            if item_title.lower() == work_item_id.lower():
                return item.get("id")
        
        # Try keyword search
        keywords = work_item_id.lower().split()
        for item in work_items:
            item_title = item.get("title", "")
            item_description = item.get("description", "")
            item_text = f"{item_title} {item_description or ''}".lower()
            if all(keyword in item_text for keyword in keywords):
                return item.get("id")
        
        return None
    
    async def _get_child_work_items(self, parent_id: str) -> List[Dict[str, Any]]:
        """Get child work items."""
        all_items = await self.storage.list_work_items()
        return [item for item in all_items if item.get('parent_id') == parent_id]
    
    async def _build_dependency_graph(self, work_items: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Build dependency graph for work items."""
        graph = {}
        
        # Build list of work item IDs safely first
        work_item_ids = []
        for wi in work_items:
            wi_id = wi.get("id")
            if wi_id is not None:
                work_item_ids.append(wi_id)
        
        # Convert to set for faster lookup and avoid array ambiguity issues
        work_item_ids_set = set(work_item_ids)
        
        for item in work_items:
            # Handle both dict and object formats for item
            if isinstance(item, dict):
                dependencies = item.get("dependencies", [])
                item_id = item.get("id")
            else:
                dependencies = item.get("dependencies", [])
                item_id = item.get("id")
            
            # Handle numpy arrays safely
            if hasattr(dependencies, 'tolist'):
                dependencies = dependencies.tolist()
            elif dependencies is None:
                dependencies = []
            
            # Ensure dependencies is a list
            if not isinstance(dependencies, list):
                dependencies = list(dependencies) if dependencies else []
            
            # Filter dependencies to only include valid work item IDs
            # Using set membership avoids array ambiguity issues
            valid_dependencies = []
            for dep in dependencies:
                if dep in work_item_ids_set:
                    valid_dependencies.append(dep)
            
            graph[item_id] = valid_dependencies
        
        return graph
    
    async def _validate_dependencies(self, work_item_id: str) -> Dict[str, Any]:
        """Validate dependencies for a work item."""
        work_item = await self.storage.get_work_item(work_item_id)
        # Handle both dict and object formats for work_item
        dependencies = work_item.get("dependencies", [])
        
        # Handle numpy arrays safely
        if hasattr(dependencies, 'tolist'):
            dependencies = dependencies.tolist()
        elif not isinstance(dependencies, list):
            dependencies = []
        
        issues = []
        for dep_id in dependencies:
            dep_item = await self.storage.get_work_item(dep_id)
            if not dep_item:
                issues.append(f"Missing dependency: {dep_id}")
            else:
                dep_status = dep_item.get("status", "not_started")
                if dep_status not in ["completed"]:
                    dep_title = dep_item.get("title", "Unknown")
                    issues.append(f"Dependency not ready: {dep_title} ({dep_status})")
        
        return {
            "success": len(issues) == 0,
            "issues": issues,
            "dependencies_checked": len(dependencies)
        }
    
    async def _validate_acceptance_criteria(self, work_item_id: str) -> Dict[str, Any]:
        """Validate acceptance criteria for a work item."""
        work_item = await self.storage.get_work_item(work_item_id)
        acceptance_criteria = work_item.get("acceptance_criteria", [])
        
        # Safe handling of acceptance_criteria to avoid numpy array ambiguity
        try:
            if acceptance_criteria is None:
                criteria_empty = True
            elif hasattr(acceptance_criteria, 'tolist'):
                acceptance_criteria = acceptance_criteria.tolist()
                criteria_empty = len(acceptance_criteria) == 0
            elif isinstance(acceptance_criteria, (list, tuple)):
                criteria_empty = len(acceptance_criteria) == 0
            else:
                try:
                    criteria_empty = len(list(acceptance_criteria)) == 0
                except Exception:
                    criteria_empty = True
        except Exception:
            criteria_empty = True
        
        if criteria_empty:
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
    
    async def _generate_execution_plan(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an execution plan for a work item."""
        try:
            work_item_id = kwargs["work_item_id"]
            planning_scope = kwargs.get("planning_scope", "single_item")
            include_dependencies = kwargs.get("include_dependencies", True)
            
            # Resolve work item ID
            resolved_id = await self._resolve_work_item_id(work_item_id)
            if not resolved_id:
                return {
                    "success": False,
                    "error": f"Work item not found: {work_item_id}"
                }
            
            # Generate execution plan using the planner
            execution_plan = await self.execution_planner.generate_execution_plan(
                resolved_id, 
                planning_scope,
                include_dependencies
            )
            
            return {
                "success": True,
                "data": {
                    "work_item_id": resolved_id,
                    "planning_scope": planning_scope,
                    "execution_plan": execution_plan
                },
                "message": "Execution plan generated successfully",
                "metadata": {
                    "plan_type": "execution",
                    "scope": planning_scope,
                    "generated_at": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating execution plan: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to generate execution plan: {str(e)}"
            }
    
    async def _generate_ai_guidance(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI guidance for a work item."""
        try:
            work_item_id = kwargs["work_item_id"]
            guidance_type = kwargs.get("guidance_type", "comprehensive")
            include_context = kwargs.get("include_context", True)
            
            # Resolve work item ID
            resolved_id = await self._resolve_work_item_id(work_item_id)
            if not resolved_id:
                return {
                    "success": False,
                    "error": f"Work item not found: {work_item_id}"
                }
            
            # Get work item details
            work_item = await self.storage.get_work_item(resolved_id)
            
            # Generate AI guidance using available method
            from ...planning.models import PlanningContext, GuidanceType, InstructionDetail
            
            # Create planning context
            context = PlanningContext(
                work_item_id=resolved_id,
                execution_mode="autonomous",
                available_tools=[],
                resource_constraints={},
                environment="development"
            )
            
            # Map guidance_type string to enum
            guidance_type_enum = GuidanceType.STRATEGIC if guidance_type == "comprehensive" else GuidanceType.TACTICAL
            
            guidance = await self.ai_guidance_generator.generate_execution_guidance(
                work_item,
                context,
                guidance_type_enum,
                InstructionDetail.DETAILED
            )
            
            return {
                "success": True,
                "data": {
                    "work_item_id": resolved_id,
                    "guidance_type": guidance_type,
                    "ai_guidance": guidance
                },
                "message": "AI guidance generated successfully",
                "metadata": {
                    "guidance_type": guidance_type,
                    "include_context": include_context,
                    "generated_at": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating AI guidance: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to generate AI guidance: {str(e)}"
            }
    
    async def _generate_instructions(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate step-by-step instructions for a work item."""
        try:
            work_item_id = kwargs["work_item_id"]
            instruction_detail = kwargs.get("instruction_detail", "medium")
            include_context = kwargs.get("include_context", True)
            
            # Resolve work item ID
            resolved_id = await self._resolve_work_item_id(work_item_id)
            if not resolved_id:
                return {
                    "success": False,
                    "error": f"Work item not found: {work_item_id}"
                }
            
            # Get work item details
            work_item = await self.storage.get_work_item(resolved_id)
            
            # Generate instructions
            instructions = await self.ai_guidance_generator.generate_step_by_step_instructions(
                work_item,
                instruction_detail,
                include_context
            )
            
            return {
                "success": True,
                "data": {
                    "work_item_id": resolved_id,
                    "instruction_detail": instruction_detail,
                    "instructions": instructions
                },
                "message": "Step-by-step instructions generated successfully",
                "metadata": {
                    "detail_level": instruction_detail,
                    "include_context": include_context,
                    "generated_at": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating instructions: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to generate instructions: {str(e)}"
            }
    
    async def _generate_prompt_template(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a prompt template for a work item."""
        try:
            work_item_id = kwargs["work_item_id"]
            prompt_template_type = kwargs.get("prompt_template_type", "execution")
            include_context = kwargs.get("include_context", True)
            
            # Resolve work item ID
            resolved_id = await self._resolve_work_item_id(work_item_id)
            if not resolved_id:
                return {
                    "success": False,
                    "error": f"Work item not found: {work_item_id}"
                }
            
            # Get work item details
            work_item = await self.storage.get_work_item(resolved_id)
            
            # Generate prompt template
            prompt_template = await self.ai_guidance_generator.generate_prompt_template(
                work_item,
                prompt_template_type,
                include_context
            )
            
            return {
                "success": True,
                "data": {
                    "work_item_id": resolved_id,
                    "template_type": prompt_template_type,
                    "prompt_template": prompt_template
                },
                "message": "Prompt template generated successfully",
                "metadata": {
                    "template_type": prompt_template_type,
                    "include_context": include_context,
                    "generated_at": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating prompt template: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to generate prompt template: {str(e)}"
            }
    
    async def _generate_execution_summary(self, work_item_id: str, priority_setting: str) -> Dict[str, Any]:
        """Generate a hierarchical execution summary with ordered tasks."""
        # Get the root work item and its full hierarchy
        work_item = await self.storage.get_work_item(work_item_id)
        children = await self._get_child_work_items(work_item_id)
        
        # Build complete task list including root and all children
        all_tasks = [work_item]
        # Handle numpy arrays safely - check length instead of truthiness
        if children is not None and len(children) > 0:
            all_tasks.extend(children)
        
        # Sort tasks based on priority setting
        ordered_tasks = await self._sort_tasks_by_priority(all_tasks, priority_setting)
        
        # Generate execution summary
        summary = {
            "root_work_item": {
                "id": work_item.get("id"),
                "title": work_item.get("title"),
                "type": work_item.get("type"),
                "description": work_item.get("description", "")
            },
            "total_tasks": len(ordered_tasks),
            "execution_order": [],
            "priority_setting": priority_setting,
            "estimated_duration": "TBD",
            "dependencies_resolved": True
        }
        
        # Build execution order with task details
        for i, task in enumerate(ordered_tasks):
            task_info = {
                "order": i + 1,
                "id": task.get("id"),
                "title": task.get("title"),
                "type": task.get("type"),
                "status": task.get("status", "not_started"),
                "priority": task.get("priority", "medium"),
                "complexity": task.get("complexity", "moderate"),
                "description": task.get("description", "")[:200] + "..." if len(task.get("description", "")) > 200 else task.get("description", "")
            }
            summary["execution_order"].append(task_info)
        
        return summary
    
    async def _get_next_task_guidance(self, execution_summary: Dict[str, Any], include_context: bool) -> Dict[str, Any]:
        """Get detailed guidance for the next task to be executed."""
        # Safe handling of execution_order to avoid numpy array ambiguity
        execution_order = execution_summary.get("execution_order")
        try:
            if execution_order is None:
                order_empty = True
            elif hasattr(execution_order, 'tolist'):
                execution_order = execution_order.tolist()
                order_empty = len(execution_order) == 0
            elif isinstance(execution_order, (list, tuple)):
                order_empty = len(execution_order) == 0
            else:
                try:
                    order_empty = len(list(execution_order)) == 0
                except Exception:
                    order_empty = True
        except Exception:
            order_empty = True
        
        if order_empty:
            return {
                "error": "No tasks available for execution",
                "has_next_task": False
            }
        
        # Get the first task (next to be executed)
        next_task = execution_summary["execution_order"][0]
        task_id = next_task["id"]
        
        # Get full task details
        task_details = await self.storage.get_work_item(task_id)
        
        # Generate comprehensive guidance using AI guidance generator
        from ...planning.models import PlanningContext, GuidanceType, InstructionDetail
        
        context = PlanningContext(
            execution_environment="development",
            available_tools=["unified_work_item_tool", "unified_storage_tool"],
            priority="medium"
        )
        
        guidance = await self.ai_guidance_generator.generate_execution_guidance(
            work_item=task_details,
            context=context,
            guidance_type=GuidanceType.TACTICAL,
            instruction_detail=InstructionDetail.DETAILED
        )
        
        # Load execution prompt template
        execution_prompt = await self._load_prompt_template("execution")
        
        # Combine task details with guidance and prompt instructions
        task_guidance = {
            "task_details": {
                "id": task_details.get("id"),
                "title": task_details.get("title"),
                "type": task_details.get("type"),
                "description": task_details.get("description", ""),
                "acceptance_criteria": task_details.get("acceptance_criteria", []),
                "notes": task_details.get("notes", ""),
                "complexity": task_details.get("complexity", "moderate"),
                "priority": task_details.get("priority", "medium")
            },
            "ai_guidance": guidance,
            "execution_instructions": execution_prompt,
            "progress_tracking": {
                "report_frequency": "After each major milestone",
                "required_updates": [
                    "Task started",
                    "Major progress milestones",
                    "Blockers encountered",
                    "Task completed"
                ]
            },
            "has_next_task": True,
            "task_position": f"1 of {execution_summary['total_tasks']}"
        }
        
        return task_guidance
    
    async def _sort_tasks_by_priority(self, tasks: List[Dict[str, Any]], priority_setting: str) -> List[Dict[str, Any]]:
        """Sort tasks based on the specified priority setting."""
        if priority_setting == "dependency_order":
            # Sort by dependencies first, then by priority
            return await self._sort_by_dependencies(tasks)
        elif priority_setting == "priority_high_first":
            # Sort by priority level (critical > high > medium > low)
            priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            return sorted(tasks, key=lambda x: priority_order.get(x.get("priority", "medium"), 2))
        elif priority_setting == "complexity_simple_first":
            # Sort by complexity (simple > moderate > complex)
            complexity_order = {"simple": 0, "moderate": 1, "complex": 2}
            return sorted(tasks, key=lambda x: complexity_order.get(x.get("complexity", "moderate"), 1))
        else:
            # Default: maintain original order
            return tasks
    
    async def _sort_by_dependencies(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort tasks by dependency order using topological sort."""
        # For now, implement a simple dependency-aware sort
        # This can be enhanced with proper topological sorting later
        
        # Separate tasks by type (higher level types first)
        type_order = {"initiative": 0, "epic": 1, "feature": 2, "story": 3, "task": 4}
        
        # Sort by type first, then by priority within type
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        
        return sorted(tasks, key=lambda x: (
            type_order.get(x.get("type", "task"), 4),
            priority_order.get(x.get("priority", "medium"), 2)
        ))
    
    async def _load_prompt_template(self, template_type: str) -> str:
        """Load prompt template from the prompts directory."""
        try:
            template_path = Path(__file__).parent.parent / "planning" / "prompts" / f"{template_type}.md"
            if template_path.exists():
                return template_path.read_text()
            else:
                return f"Execute the {template_type} task according to the requirements and acceptance criteria. Report progress regularly."
        except Exception:
            return f"Execute the {template_type} task according to the requirements and acceptance criteria. Report progress regularly."
    
    async def _update_execution_progress(self, execution_id: str, progress_update: Dict[str, Any]) -> None:
        """Update execution progress with AI agent feedback."""
        execution = self.active_executions[execution_id]
        
        # Create progress update record
        update_record = {
            "timestamp": datetime.now().isoformat(),
            "update_type": progress_update.get("type", "progress"),
            "message": progress_update.get("message", ""),
            "task_index": execution.get("current_task_index", 0),
            "details": progress_update.get("details", {})
        }
        
        # Add to progress updates
        execution["progress_updates"].append(update_record)
        
        # Update status if provided
        if "status" in progress_update:
            execution["status"] = progress_update["status"]
        
        # Handle blockers
        if progress_update.get("type") == "blocker":
            execution["status"] = "blocked"
            update_record["blocker_details"] = progress_update.get("blocker_details", {})
    
    async def _advance_to_next_task(self, execution_id: str) -> Dict[str, Any]:
        """Advance to the next task in the execution sequence."""
        execution = self.active_executions[execution_id]
        current_index = execution.get("current_task_index", 0)
        total_tasks = execution["execution_summary"]["total_tasks"]
        
        # Move to next task
        next_index = current_index + 1
        
        if next_index >= total_tasks:
            # All tasks completed
            execution["status"] = "completed"
            execution["current_task_index"] = total_tasks
            return {
                "has_next_task": False,
                "message": "All tasks completed successfully!",
                "completion_summary": {
                    "total_tasks": total_tasks,
                    "completed_tasks": total_tasks,
                    "execution_time": self._calculate_execution_time(execution)
                }
            }
        
        # Update current task index
        execution["current_task_index"] = next_index
        
        # Get next task details
        next_task_info = execution["execution_summary"]["execution_order"][next_index]
        task_id = next_task_info["id"]
        
        # Get full task details and generate guidance
        task_details = await self.storage.get_work_item(task_id)
        
        from ...planning.models import PlanningContext, GuidanceType, InstructionDetail
        
        context = PlanningContext(
            execution_environment="development",
            available_tools=["unified_work_item_tool", "unified_storage_tool"],
            priority="medium"
        )
        
        guidance = await self.ai_guidance_generator.generate_execution_guidance(
            work_item=task_details,
            context=context,
            guidance_type=GuidanceType.TACTICAL,
            instruction_detail=InstructionDetail.DETAILED
        )
        
        # Load execution prompt template
        execution_prompt = await self._load_prompt_template("execution")
        
        return {
            "has_next_task": True,
            "task_details": {
                "id": task_details.get("id"),
                "title": task_details.get("title"),
                "type": task_details.get("type"),
                "description": task_details.get("description", ""),
                "acceptance_criteria": task_details.get("acceptance_criteria", []),
                "notes": task_details.get("notes", ""),
                "complexity": task_details.get("complexity", "moderate"),
                "priority": task_details.get("priority", "medium")
            },
            "ai_guidance": guidance,
            "execution_instructions": execution_prompt,
            "task_position": f"{next_index + 1} of {total_tasks}",
            "progress_tracking": {
                "report_frequency": "After each major milestone",
                "required_updates": [
                    "Task started",
                    "Major progress milestones",
                    "Blockers encountered",
                    "Task completed"
                ]
            }
        }
    
    def _calculate_progress_percentage(self, execution: Dict[str, Any]) -> float:
        """Calculate overall progress percentage."""
        current_index = execution.get("current_task_index", 0)
        total_tasks = execution["execution_summary"]["total_tasks"]
        
        if total_tasks == 0:
            return 0.0
        
        return round((current_index / total_tasks) * 100, 1)
    
    def _safe_get_recent_updates(self, progress_updates: Any) -> List[Any]:
        """Safely extract recent updates from progress_updates, handling numpy arrays."""
        try:
            if progress_updates is None:
                return []
            
            # Handle numpy arrays
            if hasattr(progress_updates, 'tolist'):
                progress_updates = progress_updates.tolist()
            
            # Ensure it's a list
            if not isinstance(progress_updates, list):
                progress_updates = list(progress_updates) if progress_updates else []
            
            # Return last 5 items
            return progress_updates[-5:] if progress_updates else []
        except Exception:
            return []
    
    def _calculate_execution_time(self, execution: Dict[str, Any]) -> str:
        """Calculate total execution time."""
        try:
            start_time = datetime.fromisoformat(execution["started_at"])
            end_time = datetime.now()
            duration = end_time - start_time
            
            hours = duration.seconds // 3600
            minutes = (duration.seconds % 3600) // 60
            
            if hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
        except Exception:
            return "Unknown"


# Export the tool
EXECUTION_TOOLS = [UnifiedExecutionTool]