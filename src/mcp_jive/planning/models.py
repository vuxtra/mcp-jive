"""Data models for execution planning and AI guidance.

This module defines the core data structures used by the planning engine
to represent execution plans, steps, analysis results, and guidance.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from enum import Enum


class PlanningScope(str, Enum):
    """Scope of planning analysis."""
    SINGLE_ITEM = "single_item"
    HIERARCHY = "hierarchy"
    DEPENDENCIES = "dependencies"
    FULL_PROJECT = "full_project"


class GuidanceType(str, Enum):
    """Type of AI guidance to generate."""
    STRATEGIC = "strategic"
    TACTICAL = "tactical"
    OPERATIONAL = "operational"
    TECHNICAL = "technical"


class InstructionDetail(str, Enum):
    """Level of instruction detail."""
    HIGH_LEVEL = "high_level"
    DETAILED = "detailed"
    STEP_BY_STEP = "step_by_step"
    COMPREHENSIVE = "comprehensive"


class ExecutionPriority(str, Enum):
    """Execution priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskLevel(str, Enum):
    """Risk assessment levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PlanningContext(BaseModel):
    """Context information for execution planning."""
    target_agent: Optional[str] = Field(None, description="Target AI agent for execution")
    execution_environment: str = Field("development", description="Execution environment")
    available_tools: List[str] = Field(default_factory=list, description="Available tools for execution")
    constraints: List[str] = Field(default_factory=list, description="Execution constraints")
    resource_limits: Dict[str, Any] = Field(default_factory=dict, description="Resource limitations")
    timeout_minutes: int = Field(60, description="Maximum execution timeout")
    priority: ExecutionPriority = Field(ExecutionPriority.MEDIUM, description="Execution priority")


class AIGuidance(BaseModel):
    """AI guidance for execution steps."""
    approach: str = Field(..., description="High-level approach description")
    key_considerations: List[str] = Field(default_factory=list, description="Important considerations")
    success_criteria: List[str] = Field(default_factory=list, description="Success validation criteria")
    best_practices: List[str] = Field(default_factory=list, description="Recommended best practices")
    common_pitfalls: List[str] = Field(default_factory=list, description="Common mistakes to avoid")
    tools_needed: List[str] = Field(default_factory=list, description="Required tools for execution")
    estimated_complexity: str = Field("medium", description="Estimated complexity level")
    context_adaptations: Dict[str, Any] = Field(default_factory=dict, description="Context-specific adaptations")


class ExecutionStep(BaseModel):
    """Individual step in an execution plan."""
    step_id: str = Field(..., description="Unique step identifier")
    work_item_id: str = Field(..., description="Associated work item ID")
    title: str = Field(..., description="Step title")
    description: str = Field("", description="Detailed step description")
    priority: ExecutionPriority = Field(ExecutionPriority.MEDIUM, description="Step priority")
    estimated_duration: Optional[timedelta] = Field(None, description="Estimated duration")
    dependencies: List[str] = Field(default_factory=list, description="Dependent step IDs")
    prerequisites: List[str] = Field(default_factory=list, description="Required prerequisites")
    ai_guidance: Optional[AIGuidance] = Field(None, description="AI guidance for this step")
    validation_criteria: List[str] = Field(default_factory=list, description="Step validation criteria")
    rollback_instructions: Optional[str] = Field(None, description="Rollback instructions if step fails")
    parallel_eligible: bool = Field(False, description="Can be executed in parallel")
    critical_path: bool = Field(False, description="Part of critical path")
    resource_requirements: Dict[str, Any] = Field(default_factory=dict, description="Resource requirements")


class CriticalPath(BaseModel):
    """Critical path analysis results."""
    path_steps: List[str] = Field(..., description="Step IDs in critical path order")
    total_duration: timedelta = Field(..., description="Total critical path duration")
    bottlenecks: List[str] = Field(default_factory=list, description="Identified bottleneck steps")
    optimization_opportunities: List[str] = Field(default_factory=list, description="Potential optimizations")
    parallel_opportunities: List[List[str]] = Field(default_factory=list, description="Steps that can run in parallel")


class RiskFactor(BaseModel):
    """Individual risk factor."""
    risk_id: str = Field(..., description="Unique risk identifier")
    description: str = Field(..., description="Risk description")
    probability: float = Field(..., ge=0.0, le=1.0, description="Risk probability (0-1)")
    impact: RiskLevel = Field(..., description="Risk impact level")
    affected_steps: List[str] = Field(default_factory=list, description="Affected step IDs")
    mitigation_strategies: List[str] = Field(default_factory=list, description="Mitigation approaches")
    contingency_plans: List[str] = Field(default_factory=list, description="Contingency plans")


class RiskAssessment(BaseModel):
    """Comprehensive risk assessment."""
    overall_risk_level: RiskLevel = Field(..., description="Overall project risk level")
    risk_factors: List[RiskFactor] = Field(default_factory=list, description="Identified risk factors")
    high_risk_steps: List[str] = Field(default_factory=list, description="High-risk step IDs")
    recommended_mitigations: List[str] = Field(default_factory=list, description="Recommended mitigations")
    monitoring_points: List[str] = Field(default_factory=list, description="Key monitoring checkpoints")


class HierarchyNode(BaseModel):
    """Node in work item hierarchy."""
    work_item_id: str = Field(..., description="Work item ID")
    title: str = Field(..., description="Work item title")
    item_type: str = Field(..., description="Work item type")
    status: str = Field(..., description="Current status")
    priority: str = Field(..., description="Priority level")
    complexity: Optional[str] = Field(None, description="Complexity level")
    context_tags: List[str] = Field(default_factory=list, description="Context tags")
    children: List['HierarchyNode'] = Field(default_factory=list, description="Child nodes")
    dependencies: List[str] = Field(default_factory=list, description="Dependency work item IDs")
    depth: int = Field(0, description="Depth in hierarchy")
    estimated_effort: Optional[float] = Field(None, description="Estimated effort")


class HierarchyAnalysis(BaseModel):
    """Analysis of work item hierarchy."""
    root_work_item_id: str = Field(..., description="Root work item ID")
    hierarchy_tree: HierarchyNode = Field(..., description="Complete hierarchy tree")
    total_items: int = Field(..., description="Total number of work items")
    max_depth: int = Field(..., description="Maximum hierarchy depth")
    dependency_count: int = Field(..., description="Total number of dependencies")
    complexity_distribution: Dict[str, int] = Field(default_factory=dict, description="Complexity distribution")
    type_distribution: Dict[str, int] = Field(default_factory=dict, description="Type distribution")
    status_distribution: Dict[str, int] = Field(default_factory=dict, description="Status distribution")
    circular_dependencies: List[List[str]] = Field(default_factory=list, description="Circular dependency chains")
    orphaned_items: List[str] = Field(default_factory=list, description="Items without dependencies")
    leaf_items: List[str] = Field(default_factory=list, description="Leaf node work items")


class ResourceAllocation(BaseModel):
    """Resource allocation for execution."""
    agent_assignments: Dict[str, List[str]] = Field(default_factory=dict, description="Agent to step assignments")
    parallel_capacity: int = Field(3, description="Maximum parallel execution capacity")
    resource_constraints: Dict[str, Any] = Field(default_factory=dict, description="Resource constraints")
    load_balancing: Dict[str, float] = Field(default_factory=dict, description="Load distribution")
    optimization_score: float = Field(0.0, description="Resource optimization score")


class ExecutionPlan(BaseModel):
    """Comprehensive execution plan."""
    plan_id: str = Field(..., description="Unique plan identifier")
    work_item_id: str = Field(..., description="Root work item ID")
    planning_scope: PlanningScope = Field(..., description="Scope of planning")
    created_at: datetime = Field(default_factory=datetime.now, description="Plan creation timestamp")
    
    # Core planning components
    execution_sequence: List[ExecutionStep] = Field(default_factory=list, description="Ordered execution steps")
    hierarchy_analysis: Optional[HierarchyAnalysis] = Field(None, description="Hierarchy analysis results")
    critical_path: Optional[CriticalPath] = Field(None, description="Critical path analysis")
    risk_assessment: Optional[RiskAssessment] = Field(None, description="Risk assessment")
    resource_allocation: Optional[ResourceAllocation] = Field(None, description="Resource allocation plan")
    
    # Execution metadata
    estimated_total_duration: Optional[timedelta] = Field(None, description="Total estimated duration")
    estimated_effort: Optional[float] = Field(None, description="Total estimated effort")
    confidence_score: float = Field(0.0, ge=0.0, le=1.0, description="Plan confidence score")
    
    # Context and constraints
    planning_context: Optional[PlanningContext] = Field(None, description="Planning context")
    execution_constraints: List[str] = Field(default_factory=list, description="Execution constraints")
    success_metrics: List[str] = Field(default_factory=list, description="Success measurement criteria")
    
    # Optimization and alternatives
    optimization_opportunities: List[str] = Field(default_factory=list, description="Identified optimizations")
    alternative_approaches: List[str] = Field(default_factory=list, description="Alternative execution approaches")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            timedelta: lambda v: v.total_seconds()
        }


# Update forward references
HierarchyNode.model_rebuild()