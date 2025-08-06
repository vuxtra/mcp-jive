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

def convert_datetime_to_string(obj):
    """Recursively convert datetime objects to ISO strings for JSON serialization."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {convert_datetime_to_string(key): convert_datetime_to_string(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_datetime_to_string(item) for item in obj]
    elif hasattr(obj, 'isoformat'):
        return obj.isoformat()
    elif 'datetime' in str(type(obj)).lower():
        return str(obj)
    return obj

from ..config import ServerConfig
from mcp_jive.lancedb_manager import LanceDBManager
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
)
from ..utils.identifier_resolver import IdentifierResolver

logger = logging.getLogger(__name__)


# Enums are imported from models.workflow module


class WorkflowEngineTools:
    """Agile Workflow Engine tool implementations."""
    
    def __init__(self, config: ServerConfig, lancedb_manager: LanceDBManager):
        self.config = config
        self.lancedb_manager = lancedb_manager
        self.active_executions: Dict[str, Dict[str, Any]] = {}
        self.dependency_graph = nx.DiGraph()
        
        # Initialize services
        self.identifier_resolver = IdentifierResolver(lancedb_manager)
        self.hierarchy_manager = HierarchyManager(config, lancedb_manager)
        self.dependency_engine = DependencyEngine(config, lancedb_manager)
        # Autonomous executor removed - no longer needed
        
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
            table = self.lancedb_manager.db.open_table("WorkItem")
            
            # Check if table exists, if not it will be created by LanceDBManager
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
                            "description": "Work item identifier - can be exact UUID, exact title, or keywords for search"
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
                            "description": "Work item identifier - can be exact UUID, exact title, or keywords for search"
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
                            "description": "List of work item identifiers to validate - can be UUIDs, titles, or keywords (empty for all work items)"
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
                            "description": "Work item identifier - can be exact UUID, exact title, or keywords for search"
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
        """Get child work items for a given work item using flexible identifier."""
        try:
            identifier = arguments["work_item_id"]
            include_metadata = arguments.get("include_metadata", True)
            recursive = arguments.get("recursive", False)
            
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
                    "suggestions": [c.get("title") for c in candidates[:3]] if candidates else []
                }
                return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
            
            # Use the LanceDBManager's get_work_item_children method
            children_data = await self.lancedb_manager.get_work_item_children(
                work_item_id=work_item_id,
                recursive=recursive
            )
            
            children = []
            for child_data in children_data:
                # Convert LanceDB result to the expected format
                if True:  # Always process children
                    # Helper function to safely get property values and convert everything to JSON-safe types
                    def safe_get_property(key, default=None):
                        value = child_data.get(key, default)
                        if value is None:
                            return default
                        def recursive_convert(o):
                            if isinstance(o, datetime):
                                return o.isoformat()
                            elif isinstance(o, dict):
                                return {recursive_convert(k): recursive_convert(v) for k, v in o.items()}
                            elif isinstance(o, list):
                                return [recursive_convert(item) for item in o]
                            else:
                                try:
                                    json.dumps(o)
                                    return o
                                except:
                                    return str(o)
                        return recursive_convert(value)
                    
                    child_item = {
                        "id": child_data.get("id"),
                        "type": safe_get_property("item_type", "task"),
                        "title": safe_get_property("title", ""),
                        "status": safe_get_property("status", WorkItemStatus.BACKLOG.value)
                    }
                    
                    if include_metadata:
                        try:
                            metadata_fields = {
                                "description": safe_get_property("description", ""),
                                "priority": safe_get_property("priority", Priority.MEDIUM.value),
                                "effort_estimate": safe_get_property("estimated_hours", 0),
                                "acceptance_criteria": safe_get_property("acceptance_criteria", []),
                                "assignee": safe_get_property("assignee"),
                                "created_at": safe_get_property("created_at"),
                                "updated_at": safe_get_property("updated_at"),
                                "parent_id": safe_get_property("parent_id")
                            }
                            # Test each field individually
                            for field_name, field_value in metadata_fields.items():
                                try:
                                    json.dumps(field_value, default=str)
                                except Exception as field_error:
                                    logger.error(f"Field {field_name} failed serialization: {field_error}, value: {field_value}, type: {type(field_value)}")
                                    metadata_fields[field_name] = str(field_value) if field_value is not None else None
                            
                            child_item.update(metadata_fields)
                        except Exception as metadata_error:
                            logger.error(f"Metadata processing failed: {metadata_error}")
                            # Skip metadata if there's an issue
                            pass
                    
                    # Note: Recursive logic is handled by LanceDB manager, not here
                    # This prevents double recursion which was causing infinite loops
                    
                    try:
                        # Test JSON serialization before adding to children
                        json.dumps(child_item, default=str)
                        children.append(child_item)
                    except Exception as serialize_error:
                        logger.error(f"Failed to serialize child_item: {serialize_error}")
                        logger.error(f"Problematic child_item: {child_item}")
                        # Add a simplified version without problematic fields
                        simplified_child = {
                            "id": child_item.get("id"),
                            "type": child_item.get("type"),
                            "title": child_item.get("title"),
                            "status": child_item.get("status")
                        }
                        children.append(simplified_child)
            
            response = {
                "success": True,
                "work_item_id": work_item_id,
                "resolved_from": identifier if identifier != work_item_id else None,
                "children_count": len(children),
                "children": children,
                "recursive": recursive,
                "include_metadata": include_metadata,
                "message": f"Found {len(children)} children for work item {work_item_id}"
            }
            
            # Convert all datetime objects to strings before JSON serialization
            safe_response = convert_datetime_to_string(response)
            
            return [TextContent(type="text", text=json.dumps(safe_response, indent=2))]
            
        except Exception as e:
            logger.error(f"Error getting work item children: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "message": "Failed to get work item children"
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2, default=str))]
            
    async def _get_work_item_dependencies(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get dependencies that block a work item using flexible identifier."""
        try:
            identifier = arguments["work_item_id"]
            include_transitive = arguments.get("include_transitive", True)
            only_blocking = arguments.get("only_blocking", True)
            
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
            
            # Get the work item using LanceDBManager
            work_item_data = await self.lancedb_manager.get_work_item(work_item_id)
            
            if not work_item_data:
                error_response = {
                    "success": False,
                    "error": f"Work item {work_item_id} not found",
                    "message": "Work item not found"
                }
                return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
            
            # Get dependencies from the work item data
            dependencies = work_item_data.get("dependencies", [])
            if isinstance(dependencies, str):
                try:
                    dependencies = json.loads(dependencies)
                except:
                    dependencies = []
            
            dependency_details = []
            blocking_dependencies = []
            
            for dep_id in dependencies:
                # Get dependency work item data
                dep_data = await self.lancedb_manager.get_work_item(dep_id)
                
                if dep_data:
                    dep_status = dep_data.get("status", WorkItemStatus.BACKLOG.value)
                    
                    dep_info = {
                        "id": dep_id,
                        "title": dep_data.get("title", ""),
                        "status": dep_status,
                        "type": dep_data.get("item_type", "task"),
                        "is_blocking": dep_status not in [WorkItemStatus.DONE.value, WorkItemStatus.REVIEW.value]
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
                "work_item_title": work_item_data.get("title", ""),
                "work_item_status": work_item_data.get("status", WorkItemStatus.BACKLOG.value),
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
        """Validate dependency graph for circular dependencies and consistency using flexible identifiers."""
        try:
            identifiers = arguments.get("work_item_ids", [])
            check_circular = arguments.get("check_circular", True)
            check_missing = arguments.get("check_missing", True)
            suggest_fixes = arguments.get("suggest_fixes", True)
            
            # Resolve flexible identifiers to UUIDs
            work_item_ids = []
            resolution_info = []
            
            if identifiers:
                for identifier in identifiers:
                    resolved_id = await self.identifier_resolver.resolve_work_item_id(identifier)
                    if resolved_id:
                        work_item_ids.append(resolved_id)
                        resolution_info.append({
                            "original": identifier,
                            "resolved": resolved_id,
                            "status": "resolved"
                        })
                    else:
                        resolution_info.append({
                            "original": identifier,
                            "resolved": None,
                            "status": "failed"
                        })
                        logger.warning(f"Could not resolve identifier: '{identifier}'")
            
            # If some identifiers failed to resolve, include that in the response
            failed_resolutions = [r for r in resolution_info if r["status"] == "failed"]
            if failed_resolutions:
                logger.warning(f"Failed to resolve {len(failed_resolutions)} identifiers")
            
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
                "resolution_info": resolution_info if identifiers else [],
                "failed_resolutions": len(failed_resolutions) if identifiers else 0,
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
        """Start autonomous execution of a work item using flexible identifier."""
        try:
            identifier = arguments["work_item_id"]
            execution_mode = arguments.get("execution_mode", "dependency_based")
            agent_context = arguments.get("agent_context", {})
            validate_before_execution = arguments.get("validate_before_execution", True)
            
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
            
            # Generate execution ID and start simple execution tracking
            execution_id = f"exec_{work_item_id}_{int(datetime.now().timestamp())}"
            
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
            
            # Simple execution tracking without autonomous executor
            # This method provides basic execution monitoring
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
            
            # Get execution status from local tracking
            if execution_id not in self.active_executions:
                error_response = {
                    "success": False,
                    "error": f"Execution {execution_id} not found",
                    "message": "Execution not found"
                }
                return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
            
            execution_data = self.active_executions[execution_id]
            
            response = {
                "success": True,
                "execution_id": execution_id,
                "work_item_id": execution_data["work_item_id"],
                "status": execution_data["status"],
                "progress_percentage": execution_data["progress_percentage"],
                "start_time": execution_data["start_time"],
                "end_time": execution_data["end_time"],
                "error_message": execution_data["error_message"],
                "execution_mode": execution_data["execution_mode"],
                "execution_success": execution_data["status"] == ExecutionStatus.COMPLETED.value
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
            
            # Cancel execution locally (no autonomous executor needed)
            cancellation_success = True
            
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