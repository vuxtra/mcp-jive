"""Workflow Engine Data Models.

Defines the data structures for the Agile Workflow Engine as specified in the PRD.
These models handle work item hierarchies (Initiative→Epic→Feature→Story→Task)
and execution tracking for autonomous AI agents.
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


class WorkItemType(str, Enum):
    """Work item types in the agile hierarchy."""
    INITIATIVE = "initiative"
    EPIC = "epic"
    FEATURE = "feature"
    STORY = "story"
    TASK = "task"


class WorkItemStatus(str, Enum):
    """Work item status values."""
    BACKLOG = "backlog"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    REVIEW = "review"
    DONE = "done"
    CANCELLED = "cancelled"


class ExecutionStatus(str, Enum):
    """Execution status for autonomous work items."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ROLLBACK = "rollback"


class Priority(str, Enum):
    """Priority levels for work items."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DependencyType(str, Enum):
    """Types of dependencies between work items."""
    BLOCKS = "blocks"  # This item blocks the dependent item
    DEPENDS_ON = "depends_on"  # This item depends on another item
    RELATES_TO = "relates_to"  # Loose relationship


class WorkItemDependency(BaseModel):
    """Represents a dependency between work items."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    source_id: str = Field(..., description="ID of the source work item")
    target_id: str = Field(..., description="ID of the target work item")
    dependency_type: DependencyType = Field(..., description="Type of dependency")
    description: Optional[str] = Field(None, description="Description of the dependency")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="User or agent that created the dependency")


class ExecutionContext(BaseModel):
    """Context information for autonomous execution."""
    agent_id: str = Field(..., description="ID of the executing agent")
    execution_environment: Dict[str, Any] = Field(default_factory=dict, description="Environment variables and settings")
    resource_limits: Dict[str, Any] = Field(default_factory=dict, description="Resource constraints")
    timeout_seconds: Optional[int] = Field(None, description="Execution timeout")
    retry_count: int = Field(default=0, description="Number of retry attempts")
    max_retries: int = Field(default=3, description="Maximum retry attempts")


class ExecutionResult(BaseModel):
    """Result of work item execution."""
    execution_id: str = Field(..., description="Unique execution identifier")
    work_item_id: str = Field(..., description="ID of the executed work item")
    status: ExecutionStatus = Field(..., description="Execution status")
    started_at: datetime = Field(..., description="Execution start time")
    completed_at: Optional[datetime] = Field(None, description="Execution completion time")
    duration_seconds: Optional[float] = Field(None, description="Execution duration")
    
    # Results and outputs
    success: bool = Field(default=False, description="Whether execution was successful")
    output: Dict[str, Any] = Field(default_factory=dict, description="Execution output data")
    artifacts: List[str] = Field(default_factory=list, description="Generated artifacts (file paths, URLs)")
    
    # Error handling
    error_message: Optional[str] = Field(None, description="Error message if execution failed")
    error_code: Optional[str] = Field(None, description="Error code for categorization")
    stack_trace: Optional[str] = Field(None, description="Stack trace for debugging")
    
    # Progress tracking
    progress_percentage: float = Field(default=0.0, ge=0.0, le=100.0, description="Completion percentage")
    progress_details: Dict[str, Any] = Field(default_factory=dict, description="Detailed progress information")
    
    # Resource usage
    resource_usage: Dict[str, Any] = Field(default_factory=dict, description="Resource consumption metrics")
    
    # Execution context
    context: Optional[ExecutionContext] = Field(None, description="Execution context")


class WorkItem(BaseModel):
    """Core work item model for the agile hierarchy."""
    
    # Core identification
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier")
    title: str = Field(..., min_length=1, max_length=200, description="Work item title")
    description: Optional[str] = Field(None, max_length=5000, description="Detailed description")
    
    # Hierarchy and classification
    type: WorkItemType = Field(..., description="Type of work item")
    parent_id: Optional[str] = Field(None, description="Parent work item ID")
    project_id: str = Field(..., description="Project this work item belongs to")
    
    # Status and priority
    status: WorkItemStatus = Field(default=WorkItemStatus.BACKLOG, description="Current status")
    priority: Priority = Field(default=Priority.MEDIUM, description="Priority level")
    
    # Assignment and ownership
    assignee: Optional[str] = Field(None, description="Assigned user or agent")
    reporter: str = Field(..., description="User who created the work item")
    
    # Timing and estimation
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    due_date: Optional[datetime] = Field(None, description="Due date")
    estimated_hours: Optional[float] = Field(None, ge=0, description="Estimated effort in hours")
    actual_hours: Optional[float] = Field(None, ge=0, description="Actual effort spent")
    
    # Progress tracking
    progress_percentage: float = Field(default=0.0, ge=0.0, le=100.0, description="Completion percentage")
    
    # Autonomous execution
    autonomous_executable: bool = Field(default=False, description="Can be executed autonomously by AI")
    execution_instructions: Optional[str] = Field(None, description="Instructions for autonomous execution")
    execution_context: Optional[ExecutionContext] = Field(None, description="Execution context")
    last_execution: Optional[ExecutionResult] = Field(None, description="Last execution result")
    
    # Metadata and tags
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    labels: Dict[str, str] = Field(default_factory=dict, description="Key-value labels")
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="Custom field values")
    
    # Dependencies (stored as references)
    dependencies: List[str] = Field(default_factory=list, description="List of dependency IDs")
    
    @validator('updated_at', pre=True, always=True)
    def set_updated_at(cls, v):
        """Always update the timestamp when the model is modified."""
        return datetime.utcnow()
    
    @validator('parent_id')
    def validate_parent_hierarchy(cls, v, values):
        """Validate that parent-child relationships follow the hierarchy rules."""
        if v is None:
            return v
        
        work_item_type = values.get('type')
        if work_item_type == WorkItemType.INITIATIVE:
            # Initiatives can't have parents
            raise ValueError("Initiatives cannot have parent work items")
        
        # Note: Full validation requires database lookup, which should be done in the service layer
        return v
    
    @validator('progress_percentage')
    def validate_progress(cls, v, values):
        """Validate progress percentage based on status."""
        status = values.get('status')
        if status == WorkItemStatus.DONE and v != 100.0:
            raise ValueError("Done work items must have 100% progress")
        elif status == WorkItemStatus.BACKLOG and v > 0.0:
            raise ValueError("Backlog work items should have 0% progress")
        return v


class WorkItemHierarchy(BaseModel):
    """Represents a work item with its hierarchical context."""
    work_item: WorkItem = Field(..., description="The work item")
    children: List['WorkItemHierarchy'] = Field(default_factory=list, description="Child work items")
    depth: int = Field(default=0, description="Depth in the hierarchy")
    path: List[str] = Field(default_factory=list, description="Path from root to this item")
    
    class Config:
        # Enable forward references for recursive model
        arbitrary_types_allowed = True


class DependencyGraph(BaseModel):
    """Represents the dependency graph for validation and analysis."""
    work_items: Dict[str, WorkItem] = Field(..., description="Work items in the graph")
    dependencies: List[WorkItemDependency] = Field(..., description="Dependencies between work items")
    
    def get_dependencies_for_item(self, work_item_id: str) -> List[WorkItemDependency]:
        """Get all dependencies for a specific work item."""
        return [
            dep for dep in self.dependencies 
            if dep.source_id == work_item_id or dep.target_id == work_item_id
        ]
    
    def get_blocking_dependencies(self, work_item_id: str) -> List[WorkItemDependency]:
        """Get dependencies that block this work item."""
        return [
            dep for dep in self.dependencies 
            if dep.target_id == work_item_id and dep.dependency_type == DependencyType.BLOCKS
        ]
    
    def get_dependent_items(self, work_item_id: str) -> List[WorkItemDependency]:
        """Get items that depend on this work item."""
        return [
            dep for dep in self.dependencies 
            if dep.source_id == work_item_id and dep.dependency_type == DependencyType.BLOCKS
        ]


class ValidationError(BaseModel):
    """Validation error details."""
    type: str = Field(..., description="Error type")
    description: str = Field(..., description="Error description")
    work_items: List[str] = Field(default_factory=list, description="Affected work items")
    
    def dict(self, **kwargs):
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.type,
            "description": self.description,
            "work_items": self.work_items
        }


class ValidationWarning(BaseModel):
    """Validation warning details."""
    type: str = Field(..., description="Warning type")
    description: str = Field(..., description="Warning description")
    work_item_id: Optional[str] = Field(None, description="Affected work item")
    
    def dict(self, **kwargs):
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.type,
            "description": self.description,
            "work_item_id": self.work_item_id
        }


class SuggestedFix(BaseModel):
    """Suggested fix for validation issues."""
    type: str = Field(..., description="Fix type")
    description: str = Field(..., description="Fix description")
    action: str = Field(..., description="Action to take")
    from_work_item: Optional[str] = Field(None, description="Source work item")
    to_work_item: Optional[str] = Field(None, description="Target work item")
    
    def dict(self, **kwargs):
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.type,
            "description": self.description,
            "action": self.action,
            "from_work_item": self.from_work_item,
            "to_work_item": self.to_work_item
        }


class ValidationResult(BaseModel):
    """Result of dependency validation."""
    is_valid: bool = Field(..., description="Whether the dependencies are valid")
    total_work_items: int = Field(default=0, description="Total number of work items validated")
    errors: List[ValidationError] = Field(default_factory=list, description="Validation errors")
    warnings: List[ValidationWarning] = Field(default_factory=list, description="Validation warnings")
    suggested_fixes: List[SuggestedFix] = Field(default_factory=list, description="Suggested fixes")
    execution_order: List[str] = Field(default_factory=list, description="Recommended execution order")
    graph_stats: Dict[str, Any] = Field(default_factory=dict, description="Graph statistics")
    circular_dependencies: List[List[str]] = Field(default_factory=list, description="Detected circular dependency chains")
    orphaned_items: List[str] = Field(default_factory=list, description="Work items without valid parents")
    

class ProgressCalculation(BaseModel):
    """Progress calculation for hierarchical work items."""
    work_item_id: str = Field(..., description="Work item ID")
    direct_progress: float = Field(..., ge=0.0, le=100.0, description="Direct progress of the item")
    calculated_progress: float = Field(..., ge=0.0, le=100.0, description="Calculated progress including children")
    child_count: int = Field(default=0, description="Number of child items")
    completed_children: int = Field(default=0, description="Number of completed children")
    calculation_method: str = Field(..., description="Method used for calculation")
    last_updated: datetime = Field(default_factory=datetime.utcnow)


# Update forward references
WorkItemHierarchy.model_rebuild()