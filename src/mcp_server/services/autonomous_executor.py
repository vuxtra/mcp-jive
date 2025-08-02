"""Autonomous Executor Service.

Handles autonomous execution of work items by AI agents.
Manages execution context, monitoring, and result tracking.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import uuid4

from ..models.workflow import (
    WorkItem,
    ExecutionStatus,
    ExecutionResult,
    ExecutionContext,
    WorkItemStatus,
)
from ..lancedb_manager import LanceDBManager
from ..config import ServerConfig

logger = logging.getLogger(__name__)


class AutonomousExecutor:
    """Manages autonomous execution of work items by AI agents."""
    
    def __init__(self, config: ServerConfig, lancedb_manager: LanceDBManager):
        self.config = config
        self.lancedb_manager = lancedb_manager
        self.logger = logging.getLogger(__name__)
        self.execution_collection = "ExecutionResult"
        self.active_executions: Dict[str, asyncio.Task] = {}
        self.execution_results: Dict[str, ExecutionResult] = {}
        
    async def initialize(self) -> None:
        """Initialize the autonomous executor."""
        try:
            # Ensure the execution results collection exists
            await self._ensure_execution_collection_exists()
            self.logger.info("Autonomous executor initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize autonomous executor: {e}")
            raise
    
    async def _ensure_execution_collection_exists(self) -> None:
        """Ensure the ExecutionResult table exists in LanceDB."""
        try:
            # LanceDB tables are created automatically when first accessed
            # Just ensure the database connection is working
            await self.lancedb_manager.ensure_tables_exist()
            self.logger.info(f"✅ LanceDB table '{self.execution_collection}' ready")
        except Exception as e:
            self.logger.error(f"Failed to ensure execution table exists: {e}")
            raise

    async def execute_work_item(
        self, 
        work_item: WorkItem, 
        context: ExecutionContext
    ) -> str:
        """Start autonomous execution of a work item.
        
        Args:
            work_item: Work item to execute
            context: Execution context with agent and environment info
            
        Returns:
            Execution ID for tracking
        """
        try:
            # Validate that the work item can be executed autonomously
            if not work_item.autonomous_executable:
                raise ValueError(f"Work item {work_item.id} is not marked for autonomous execution")
            
            if not work_item.execution_instructions:
                raise ValueError(f"Work item {work_item.id} has no execution instructions")
            
            # Create execution ID
            execution_id = str(uuid4())
            
            # Create initial execution result
            execution_result = ExecutionResult(
                execution_id=execution_id,
                work_item_id=work_item.id,
                status=ExecutionStatus.PENDING,
                started_at=datetime.utcnow(),
                context=context
            )
            
            # Store in memory and Weaviate
            self.execution_results[execution_id] = execution_result
            await self._store_execution_result(execution_result)
            
            # Start execution task
            task = asyncio.create_task(
                self._execute_work_item_async(work_item, execution_result)
            )
            self.active_executions[execution_id] = task
            
            self.logger.info(f"Started execution {execution_id} for work item {work_item.id}")
            return execution_id
            
        except Exception as e:
            self.logger.error(f"Failed to start execution for work item {work_item.id}: {e}")
            raise
    
    async def _execute_work_item_async(
        self, 
        work_item: WorkItem, 
        execution_result: ExecutionResult
    ) -> None:
        """Asynchronously execute a work item."""
        try:
            # Update status to running
            execution_result.status = ExecutionStatus.RUNNING
            execution_result.progress_percentage = 0.0
            await self._update_execution_result(execution_result)
            
            # Simulate execution based on work item type and instructions
            # In a real implementation, this would interface with actual AI agents
            await self._simulate_execution(work_item, execution_result)
            
            # Mark as completed
            execution_result.status = ExecutionStatus.COMPLETED
            execution_result.completed_at = datetime.utcnow()
            execution_result.duration_seconds = (
                execution_result.completed_at - execution_result.started_at
            ).total_seconds()
            execution_result.success = True
            execution_result.progress_percentage = 100.0
            
            await self._update_execution_result(execution_result)
            
            # Update work item status
            await self._update_work_item_status(work_item.id, WorkItemStatus.DONE)
            
            self.logger.info(f"Completed execution {execution_result.execution_id}")
            
        except asyncio.CancelledError:
            # Execution was cancelled
            execution_result.status = ExecutionStatus.CANCELLED
            execution_result.completed_at = datetime.utcnow()
            execution_result.duration_seconds = (
                execution_result.completed_at - execution_result.started_at
            ).total_seconds()
            execution_result.error_message = "Execution was cancelled"
            
            await self._update_execution_result(execution_result)
            await self._update_work_item_status(work_item.id, WorkItemStatus.BLOCKED)
            
            self.logger.info(f"Cancelled execution {execution_result.execution_id}")
            
        except Exception as e:
            # Execution failed
            execution_result.status = ExecutionStatus.FAILED
            execution_result.completed_at = datetime.utcnow()
            execution_result.duration_seconds = (
                execution_result.completed_at - execution_result.started_at
            ).total_seconds()
            execution_result.success = False
            execution_result.error_message = str(e)
            execution_result.error_code = type(e).__name__
            
            await self._update_execution_result(execution_result)
            await self._update_work_item_status(work_item.id, WorkItemStatus.BLOCKED)
            
            self.logger.error(f"Failed execution {execution_result.execution_id}: {e}")
            
        finally:
            # Clean up active execution
            if execution_result.execution_id in self.active_executions:
                del self.active_executions[execution_result.execution_id]
    
    async def _simulate_execution(
        self, 
        work_item: WorkItem, 
        execution_result: ExecutionResult
    ) -> None:
        """Simulate work item execution.
        
        In a real implementation, this would:
        1. Parse execution instructions
        2. Interface with appropriate AI agents
        3. Execute the actual work
        4. Monitor progress
        5. Handle errors and retries
        """
        # Simulate different execution times based on work item type
        execution_time_map = {
            "task": 5,      # 5 seconds
            "story": 15,    # 15 seconds
            "feature": 30,  # 30 seconds
            "epic": 60,     # 60 seconds
            "initiative": 120,  # 2 minutes
        }
        
        total_time = execution_time_map.get(work_item.type.value, 10)
        progress_steps = 10
        step_time = total_time / progress_steps
        
        for step in range(progress_steps):
            # Check if execution was cancelled
            if execution_result.status == ExecutionStatus.CANCELLED:
                break
            
            # Update progress
            progress = (step + 1) * (100.0 / progress_steps)
            execution_result.progress_percentage = progress
            execution_result.progress_details = {
                "step": step + 1,
                "total_steps": progress_steps,
                "current_task": f"Executing step {step + 1} of {progress_steps}",
                "estimated_remaining_seconds": (progress_steps - step - 1) * step_time
            }
            
            await self._update_execution_result(execution_result)
            
            # Simulate work
            await asyncio.sleep(step_time)
        
        # Set final output
        execution_result.output = {
            "result": "Work item executed successfully",
            "work_item_type": work_item.type.value,
            "execution_method": "simulated",
            "instructions_processed": work_item.execution_instructions[:100] + "..." if work_item.execution_instructions else None
        }
        
        execution_result.artifacts = [
            f"artifact_{work_item.id}_output.json",
            f"artifact_{work_item.id}_log.txt"
        ]
        
        execution_result.resource_usage = {
            "cpu_seconds": total_time * 0.1,
            "memory_mb": 50,
            "network_requests": 5
        }
    
    async def get_execution_status(self, execution_id: str) -> Optional[ExecutionResult]:
        """Get the current status of an execution.
        
        Args:
            execution_id: ID of the execution
            
        Returns:
            ExecutionResult or None if not found
        """
        try:
            # Check in-memory cache first
            if execution_id in self.execution_results:
                return self.execution_results[execution_id]
            
            # Query from Weaviate            table = await self.lancedb_manager.get_table("WorkItem")
            
            # Fetch all execution results and find the matching one
            response = await self.lancedb_manager.search_work_items("", {}, limit=100)
            
            for obj in response.objects:
                # Check if this is the execution result we're looking for
                if obj.properties.get("execution_id") == execution_id:
                    execution_result = self._weaviate_to_execution_result(obj)
                    self.execution_results[execution_id] = execution_result
                    return execution_result
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get execution status for {execution_id}: {e}")
            return None
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running execution.
        
        Args:
            execution_id: ID of the execution to cancel
            
        Returns:
            True if cancelled successfully
        """
        try:
            # Check if execution is active
            if execution_id in self.active_executions:
                task = self.active_executions[execution_id]
                task.cancel()
                
                # Wait for cancellation to complete
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                
                self.logger.info(f"Cancelled execution {execution_id}")
                return True
            else:
                # Execution might be completed or not found
                execution_result = await self.get_execution_status(execution_id)
                if execution_result and execution_result.status == ExecutionStatus.RUNNING:
                    # Update status to cancelled
                    execution_result.status = ExecutionStatus.CANCELLED
                    execution_result.completed_at = datetime.utcnow()
                    execution_result.error_message = "Execution cancelled by user"
                    await self._update_execution_result(execution_result)
                    return True
                
                return False
            
        except Exception as e:
            self.logger.error(f"Failed to cancel execution {execution_id}: {e}")
            return False
    
    async def _store_execution_result(self, execution_result: ExecutionResult) -> None:
        """Store execution result in Weaviate."""
        try:
            table = await self.lancedb_manager.get_table("WorkItem")
            
            properties = {
                "execution_id": execution_result.execution_id,
                "work_item_id": execution_result.work_item_id,
                "status": execution_result.status.value,
                "started_at": execution_result.started_at.isoformat(),
                "success": execution_result.success,
                "output": execution_result.output,
                "artifacts": execution_result.artifacts,
                "progress_percentage": execution_result.progress_percentage,
                "progress_details": execution_result.progress_details,
                "resource_usage": execution_result.resource_usage,
            }
            
            if execution_result.completed_at:
                properties["completed_at"] = execution_result.completed_at.isoformat()
            if execution_result.duration_seconds:
                properties["duration_seconds"] = execution_result.duration_seconds
            if execution_result.error_message:
                properties["error_message"] = execution_result.error_message
            if execution_result.error_code:
                properties["error_code"] = execution_result.error_code
            if execution_result.stack_trace:
                properties["stack_trace"] = execution_result.stack_trace
            if execution_result.context:
                properties["agent_id"] = execution_result.context.agent_id
                properties["execution_environment"] = execution_result.context.execution_environment
            
            await self.lancedb_manager.create_work_item(work_item_data)
            
        except Exception as e:
            self.logger.error(f"Failed to store execution result: {e}")
            raise
    
    async def _update_execution_result(self, execution_result: ExecutionResult) -> None:
        """Update execution result in Weaviate."""
        try:
            # For simplicity, we'll delete and re-insert
            # In production, you'd want to use proper update operations
            await self._store_execution_result(execution_result)
            
        except Exception as e:
            self.logger.error(f"Failed to update execution result: {e}")
    
    async def _update_work_item_status(self, work_item_id: str, status: WorkItemStatus) -> None:
        """Update work item status.
        
        This would typically interface with the hierarchy manager.
        """
        try:
            # In a real implementation, this would update the work item in Weaviate
            self.logger.info(f"Updated work item {work_item_id} status to {status.value}")
            
        except Exception as e:
            self.logger.error(f"Failed to update work item status: {e}")
    
    def _weaviate_to_execution_result(self, weaviate_obj) -> ExecutionResult:
        """Convert Weaviate object to ExecutionResult model."""
        properties = weaviate_obj.properties
        
        started_at = properties.get('started_at')
        if isinstance(started_at, str):
            started_at = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
        
        completed_at = properties.get('completed_at')
        if isinstance(completed_at, str):
            completed_at = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
        
        context = None
        if properties.get('agent_id'):
            context = ExecutionContext(
                agent_id=properties.get('agent_id', ''),
                execution_environment=properties.get('execution_environment', {})
            )
        
        return ExecutionResult(
            execution_id=properties.get('execution_id', ''),
            work_item_id=properties.get('work_item_id', ''),
            status=ExecutionStatus(properties.get('status', 'pending')),
            started_at=started_at or datetime.utcnow(),
            completed_at=completed_at,
            duration_seconds=properties.get('duration_seconds'),
            success=properties.get('success', False),
            output=properties.get('output', {}),
            artifacts=properties.get('artifacts', []),
            error_message=properties.get('error_message'),
            error_code=properties.get('error_code'),
            stack_trace=properties.get('stack_trace'),
            progress_percentage=properties.get('progress_percentage', 0.0),
            progress_details=properties.get('progress_details', {}),
            resource_usage=properties.get('resource_usage', {}),
            context=context
        )
    
    async def cleanup(self) -> None:
        """Cleanup resources and cancel active executions."""
        try:
            # Cancel all active executions
            for execution_id, task in self.active_executions.items():
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            self.active_executions.clear()
            self.execution_results.clear()
            
            self.logger.info("Autonomous executor cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during autonomous executor cleanup: {e}")