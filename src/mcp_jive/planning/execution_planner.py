"""Execution Planner for AI guidance and planning engine.

This module provides comprehensive execution planning capabilities including
hierarchy analysis, dependency resolution, critical path identification,
and AI guidance generation for work item execution.
"""

import logging
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timedelta
import asyncio
from collections import defaultdict, deque

from .models import (
    ExecutionPlan,
    ExecutionStep,
    HierarchyAnalysis,
    HierarchyNode,
    CriticalPath,
    RiskAssessment,
    RiskFactor,
    PlanningContext,
    AIGuidance,
    ResourceAllocation,
    PlanningScope,
    ExecutionPriority,
    RiskLevel
)
from ..uuid_utils import generate_uuid

logger = logging.getLogger(__name__)


class ExecutionPlanner:
    """Core execution planning engine.
    
    Provides comprehensive planning capabilities for work item execution,
    including hierarchy analysis, dependency resolution, critical path
    identification, and AI guidance generation.
    """
    
    def __init__(self, storage=None):
        """Initialize the execution planner.
        
        Args:
            storage: Storage backend for work item data
        """
        self.storage = storage
        self.logger = logging.getLogger(__name__)
    
    async def analyze_work_item_hierarchy(self, work_item_id: str) -> HierarchyAnalysis:
        """Analyze work item hierarchy structure.
        
        Args:
            work_item_id: Root work item ID to analyze
            
        Returns:
            HierarchyAnalysis: Comprehensive hierarchy analysis
        """
        try:
            # Get root work item
            root_item = await self._get_work_item(work_item_id)
            if not root_item:
                raise ValueError(f"Work item {work_item_id} not found")
            
            # Build hierarchy tree
            hierarchy_tree = await self._build_hierarchy_tree(work_item_id)
            
            # Analyze hierarchy structure
            analysis = await self._analyze_hierarchy_structure(hierarchy_tree)
            
            return HierarchyAnalysis(
                root_work_item_id=work_item_id,
                hierarchy_tree=hierarchy_tree,
                **analysis
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing hierarchy for {work_item_id}: {str(e)}")
            raise
    
    async def generate_execution_plan(
        self, 
        work_item_id: str, 
        context: Optional[PlanningContext] = None,
        scope: PlanningScope = PlanningScope.HIERARCHY
    ) -> ExecutionPlan:
        """Generate comprehensive execution plan.
        
        Args:
            work_item_id: Root work item ID
            context: Planning context and constraints
            scope: Scope of planning analysis
            
        Returns:
            ExecutionPlan: Complete execution plan with steps and analysis
        """
        try:
            plan_id = generate_uuid()
            
            # Set default context if not provided
            if context is None:
                context = PlanningContext()
            
            # Analyze hierarchy if scope requires it
            hierarchy_analysis = None
            if scope in [PlanningScope.HIERARCHY, PlanningScope.FULL_PROJECT]:
                hierarchy_analysis = await self.analyze_work_item_hierarchy(work_item_id)
            
            # Generate execution sequence
            execution_sequence = await self._generate_execution_sequence(
                work_item_id, context, scope, hierarchy_analysis
            )
            
            # Perform critical path analysis
            critical_path = await self._analyze_critical_path(execution_sequence)
            
            # Assess risks
            risk_assessment = await self._assess_execution_risks(
                execution_sequence, hierarchy_analysis
            )
            
            # Optimize resource allocation
            resource_allocation = await self._optimize_resource_allocation(
                execution_sequence, context
            )
            
            # Calculate estimates
            total_duration, total_effort = await self._calculate_estimates(execution_sequence)
            
            # Generate optimization opportunities
            optimization_opportunities = await self._identify_optimizations(
                execution_sequence, critical_path
            )
            
            return ExecutionPlan(
                plan_id=plan_id,
                work_item_id=work_item_id,
                planning_scope=scope,
                execution_sequence=execution_sequence,
                hierarchy_analysis=hierarchy_analysis,
                critical_path=critical_path,
                risk_assessment=risk_assessment,
                resource_allocation=resource_allocation,
                estimated_total_duration=total_duration,
                estimated_effort=total_effort,
                planning_context=context,
                optimization_opportunities=optimization_opportunities,
                confidence_score=await self._calculate_confidence_score(
                    execution_sequence, risk_assessment
                )
            )
            
        except Exception as e:
            self.logger.error(f"Error generating execution plan for {work_item_id}: {str(e)}")
            raise
    
    async def optimize_execution_sequence(
        self, 
        plan: ExecutionPlan
    ) -> ExecutionPlan:
        """Optimize execution sequence for better performance.
        
        Args:
            plan: Original execution plan
            
        Returns:
            ExecutionPlan: Optimized execution plan
        """
        try:
            # Identify parallel execution opportunities
            optimized_sequence = await self._optimize_for_parallelism(
                plan.execution_sequence
            )
            
            # Rebalance resource allocation
            optimized_resources = await self._optimize_resource_allocation(
                optimized_sequence, plan.planning_context
            )
            
            # Recalculate critical path
            optimized_critical_path = await self._analyze_critical_path(
                optimized_sequence
            )
            
            # Update plan with optimizations
            plan.execution_sequence = optimized_sequence
            plan.resource_allocation = optimized_resources
            plan.critical_path = optimized_critical_path
            
            # Recalculate estimates
            plan.estimated_total_duration, plan.estimated_effort = \
                await self._calculate_estimates(optimized_sequence)
            
            return plan
            
        except Exception as e:
            self.logger.error(f"Error optimizing execution plan: {str(e)}")
            raise
    
    async def identify_critical_path(self, plan: ExecutionPlan) -> CriticalPath:
        """Identify critical path in execution plan.
        
        Args:
            plan: Execution plan to analyze
            
        Returns:
            CriticalPath: Critical path analysis results
        """
        return await self._analyze_critical_path(plan.execution_sequence)
    
    async def assess_execution_risks(
        self, 
        plan: ExecutionPlan
    ) -> RiskAssessment:
        """Assess execution risks for the plan.
        
        Args:
            plan: Execution plan to assess
            
        Returns:
            RiskAssessment: Comprehensive risk assessment
        """
        return await self._assess_execution_risks(
            plan.execution_sequence, plan.hierarchy_analysis
        )
    
    # Private helper methods
    
    async def _get_work_item(self, work_item_id: str) -> Optional[Dict[str, Any]]:
        """Get work item from storage."""
        if not self.storage:
            # Mock work item for testing
            return {
                "work_item_id": work_item_id,
                "title": f"Work Item {work_item_id}",
                "item_type": "task",
                "status": "not_started",
                "priority": "medium",
                "complexity": "moderate",
                "context_tags": [],
                "acceptance_criteria": [],
                "notes": ""
            }
        
        try:
            return await self.storage.get_work_item(work_item_id)
        except Exception as e:
            self.logger.error(f"Error getting work item {work_item_id}: {str(e)}")
            return None
    
    async def _build_hierarchy_tree(self, work_item_id: str, depth: int = 0) -> HierarchyNode:
        """Build hierarchy tree recursively."""
        work_item = await self._get_work_item(work_item_id)
        if not work_item:
            raise ValueError(f"Work item {work_item_id} not found")
        
        # Create hierarchy node
        node = HierarchyNode(
            work_item_id=work_item_id,
            title=work_item.get("title", ""),
            item_type=work_item.get("item_type", "task"),
            status=work_item.get("status", "not_started"),
            priority=work_item.get("priority", "medium"),
            complexity=work_item.get("complexity"),
            context_tags=work_item.get("context_tags", []),
            depth=depth,
            estimated_effort=work_item.get("effort_estimate")
        )
        
        # Get children (mock implementation)
        children = await self._get_work_item_children(work_item_id)
        for child_id in children:
            child_node = await self._build_hierarchy_tree(child_id, depth + 1)
            node.children.append(child_node)
        
        # Get dependencies (mock implementation)
        dependencies = await self._get_work_item_dependencies(work_item_id)
        node.dependencies = dependencies
        
        return node
    
    async def _get_work_item_children(self, work_item_id: str) -> List[str]:
        """Get child work item IDs."""
        # Mock implementation - return empty list for now
        return []
    
    async def _get_work_item_dependencies(self, work_item_id: str) -> List[str]:
        """Get dependency work item IDs."""
        # Mock implementation - return empty list for now
        return []
    
    async def _analyze_hierarchy_structure(self, tree: HierarchyNode) -> Dict[str, Any]:
        """Analyze hierarchy structure and return metrics."""
        total_items = 0
        max_depth = 0
        dependency_count = 0
        complexity_dist = defaultdict(int)
        type_dist = defaultdict(int)
        status_dist = defaultdict(int)
        leaf_items = []
        
        def traverse(node: HierarchyNode, depth: int):
            nonlocal total_items, max_depth, dependency_count
            
            total_items += 1
            max_depth = max(max_depth, depth)
            dependency_count += len(node.dependencies)
            
            if node.complexity:
                complexity_dist[node.complexity] += 1
            type_dist[node.item_type] += 1
            status_dist[node.status] += 1
            
            if not node.children:
                leaf_items.append(node.work_item_id)
            
            for child in node.children:
                traverse(child, depth + 1)
        
        traverse(tree, 0)
        
        return {
            "total_items": total_items,
            "max_depth": max_depth,
            "dependency_count": dependency_count,
            "complexity_distribution": dict(complexity_dist),
            "type_distribution": dict(type_dist),
            "status_distribution": dict(status_dist),
            "circular_dependencies": [],  # TODO: Implement circular dependency detection
            "orphaned_items": [],  # TODO: Implement orphan detection
            "leaf_items": leaf_items
        }
    
    async def _generate_execution_sequence(
        self,
        work_item_id: str,
        context: PlanningContext,
        scope: PlanningScope,
        hierarchy_analysis: Optional[HierarchyAnalysis]
    ) -> List[ExecutionStep]:
        """Generate ordered execution sequence."""
        steps = []
        
        if scope == PlanningScope.SINGLE_ITEM:
            # Single item execution
            step = await self._create_execution_step(work_item_id, context)
            steps.append(step)
        else:
            # Multi-item execution based on hierarchy
            # Safe handling of hierarchy_analysis to avoid numpy array ambiguity
            hierarchy_available = False
            if hierarchy_analysis is not None:
                if hasattr(hierarchy_analysis, 'tolist'):
                    # Convert numpy array to list if needed
                    hierarchy_analysis = hierarchy_analysis.tolist()
                    hierarchy_available = len(hierarchy_analysis) > 0 if isinstance(hierarchy_analysis, list) else bool(hierarchy_analysis)
                else:
                    hierarchy_available = bool(hierarchy_analysis)
            
            if hierarchy_available:
                steps = await self._create_steps_from_hierarchy(
                    hierarchy_analysis.hierarchy_tree, context
                )
            else:
                # Fallback to single item
                step = await self._create_execution_step(work_item_id, context)
                steps.append(step)
        
        # Sort steps by dependencies and priority
        sorted_steps = await self._sort_steps_by_dependencies(steps)
        
        return sorted_steps
    
    async def _create_execution_step(
        self, 
        work_item_id: str, 
        context: PlanningContext
    ) -> ExecutionStep:
        """Create execution step for work item."""
        work_item = await self._get_work_item(work_item_id)
        if not work_item:
            raise ValueError(f"Work item {work_item_id} not found")
        
        # Generate AI guidance
        ai_guidance = await self._generate_ai_guidance(work_item, context)
        
        # Estimate duration based on complexity
        duration = await self._estimate_step_duration(work_item)
        
        return ExecutionStep(
            step_id=generate_uuid(),
            work_item_id=work_item_id,
            title=work_item.get("title", ""),
            description=work_item.get("description", ""),
            priority=ExecutionPriority(work_item.get("priority", "medium")),
            estimated_duration=duration,
            dependencies=work_item.get("dependencies", []),
            ai_guidance=ai_guidance,
            validation_criteria=work_item.get("acceptance_criteria", [])
        )
    
    async def _generate_ai_guidance(
        self, 
        work_item: Dict[str, Any], 
        context: PlanningContext
    ) -> AIGuidance:
        """Generate AI guidance for work item execution."""
        complexity = work_item.get("complexity", "moderate")
        context_tags = work_item.get("context_tags", [])
        item_type = work_item.get("item_type", "task")
        
        # Generate approach based on complexity and type
        approach = await self._generate_approach(item_type, complexity, context_tags)
        
        # Generate considerations based on context
        considerations = await self._generate_considerations(work_item, context)
        
        # Generate success criteria
        success_criteria = work_item.get("acceptance_criteria", [])
        if not success_criteria:
            success_criteria = await self._generate_default_success_criteria(work_item)
        
        return AIGuidance(
            approach=approach,
            key_considerations=considerations,
            success_criteria=success_criteria,
            best_practices=await self._generate_best_practices(context_tags),
            common_pitfalls=await self._generate_common_pitfalls(complexity),
            tools_needed=context.available_tools,
            estimated_complexity=complexity
        )
    
    async def _generate_approach(
        self, 
        item_type: str, 
        complexity: str, 
        context_tags: List[str]
    ) -> str:
        """Generate execution approach based on work item characteristics."""
        approaches = {
            "task": {
                "simple": "Direct implementation with minimal planning",
                "moderate": "Systematic implementation with validation checkpoints",
                "complex": "Phased implementation with comprehensive testing"
            },
            "epic": {
                "simple": "Sequential execution of child features",
                "moderate": "Parallel execution with dependency management",
                "complex": "Strategic phased rollout with risk mitigation"
            },
            "initiative": {
                "simple": "Coordinated execution across teams",
                "moderate": "Strategic execution with milestone tracking",
                "complex": "Enterprise-wide transformation with change management"
            }
        }
        
        base_approach = approaches.get(item_type, approaches["task"]).get(
            complexity, approaches["task"]["moderate"]
        )
        
        # Enhance approach based on context tags
        if self._safe_tag_check("frontend", context_tags):
            base_approach += ". Focus on user experience and responsive design."
        elif self._safe_tag_check("backend", context_tags):
            base_approach += ". Emphasize scalability and performance optimization."
        elif self._safe_tag_check("database", context_tags):
            base_approach += ". Prioritize data integrity and query optimization."
        
        return base_approach
    
    async def _generate_considerations(
        self, 
        work_item: Dict[str, Any], 
        context: PlanningContext
    ) -> List[str]:
        """Generate key considerations for execution."""
        considerations = []
        
        # Environment-specific considerations
        if context.execution_environment == "production":
            considerations.append("Ensure zero-downtime deployment")
            considerations.append("Implement comprehensive monitoring")
        elif context.execution_environment == "staging":
            considerations.append("Validate against production-like data")
        
        # Complexity-based considerations
        complexity = work_item.get("complexity", "moderate")
        if complexity == "complex":
            considerations.extend([
                "Break down into smaller, manageable tasks",
                "Implement comprehensive error handling",
                "Plan for rollback scenarios"
            ])
        
        # Context tag considerations
        context_tags = work_item.get("context_tags", [])
        if self._safe_tag_check("security", context_tags):
            considerations.append("Implement security best practices")
        if self._safe_tag_check("performance", context_tags):
            considerations.append("Optimize for performance and scalability")
        
        return considerations
    
    async def _generate_default_success_criteria(
        self, 
        work_item: Dict[str, Any]
    ) -> List[str]:
        """Generate default success criteria if none provided."""
        item_type = work_item.get("item_type", "task")
        
        criteria_templates = {
            "task": [
                "Implementation meets functional requirements",
                "Code passes all tests",
                "Documentation is updated"
            ],
            "epic": [
                "All child features are completed",
                "Integration testing passes",
                "User acceptance criteria met"
            ],
            "initiative": [
                "All strategic objectives achieved",
                "Stakeholder approval obtained",
                "Success metrics validated"
            ]
        }
        
        return criteria_templates.get(item_type, criteria_templates["task"])
    
    async def _generate_best_practices(self, context_tags: List[str]) -> List[str]:
        """Generate best practices based on context tags."""
        practices = [
            "Follow established coding standards",
            "Implement comprehensive testing",
            "Document implementation decisions"
        ]
        
        if self._safe_tag_check("frontend", context_tags):
            practices.extend([
                "Ensure cross-browser compatibility",
                "Optimize for mobile devices",
                "Implement accessibility standards"
            ])
        
        if self._safe_tag_check("backend", context_tags):
            practices.extend([
                "Implement proper error handling",
                "Use appropriate caching strategies",
                "Follow API design principles"
            ])
        
        return practices
    
    async def _generate_common_pitfalls(self, complexity: str) -> List[str]:
        """Generate common pitfalls based on complexity."""
        base_pitfalls = [
            "Insufficient testing coverage",
            "Poor error handling",
            "Inadequate documentation"
        ]
        
        if complexity == "complex":
            base_pitfalls.extend([
                "Underestimating integration complexity",
                "Insufficient stakeholder communication",
                "Inadequate rollback planning"
            ])
        
        return base_pitfalls
    
    async def _estimate_step_duration(self, work_item: Dict[str, Any]) -> timedelta:
        """Estimate step duration based on work item characteristics."""
        complexity = work_item.get("complexity", "moderate")
        item_type = work_item.get("item_type", "task")
        
        # Base duration estimates (in hours)
        duration_map = {
            "task": {"simple": 2, "moderate": 8, "complex": 24},
            "epic": {"simple": 40, "moderate": 80, "complex": 160},
            "initiative": {"simple": 160, "moderate": 320, "complex": 640}
        }
        
        hours = duration_map.get(item_type, duration_map["task"]).get(
            complexity, duration_map["task"]["moderate"]
        )
        
        return timedelta(hours=hours)
    
    async def _create_steps_from_hierarchy(
        self, 
        tree: HierarchyNode, 
        context: PlanningContext
    ) -> List[ExecutionStep]:
        """Create execution steps from hierarchy tree."""
        steps = []
        
        async def process_node(node: HierarchyNode):
            # Create step for current node
            step = await self._create_execution_step(node.work_item_id, context)
            steps.append(step)
            
            # Process children
            for child in node.children:
                await process_node(child)
        
        await process_node(tree)
        return steps
    
    def _safe_tag_check(self, tag: str, context_tags: Any) -> bool:
        """Safely check if a tag is in context_tags, handling arrays."""
        try:
            if context_tags is None:
                return False
            
            # Handle numpy arrays
            if hasattr(context_tags, 'tolist'):
                context_tags = context_tags.tolist()
            
            # Handle string representation of lists - safe check for numpy arrays
            if isinstance(context_tags, str):
                try:
                    if context_tags.startswith('[') and context_tags.endswith(']'):
                        try:
                            import ast
                            context_tags = ast.literal_eval(context_tags)
                        except (ValueError, SyntaxError):
                            return tag in context_tags
                    else:
                        return tag in context_tags
                except Exception:
                    return False
            
            # Handle iterables
            if hasattr(context_tags, '__iter__'):
                return tag in list(context_tags)
            else:
                return tag == str(context_tags)
        except Exception:
            return False
    
    async def _sort_steps_by_dependencies(self, steps: List[ExecutionStep]) -> List[ExecutionStep]:
        """Sort steps based on dependencies using topological sort."""
        # Create dependency graph
        graph = defaultdict(list)
        in_degree = defaultdict(int)
        step_map = {step.work_item_id: step for step in steps}
        
        for step in steps:
            in_degree[step.step_id] = 0
        
        for step in steps:
            for dep_id in step.dependencies:
                if dep_id in step_map:
                    dep_step = step_map[dep_id]
                    graph[dep_step.step_id].append(step.step_id)
                    in_degree[step.step_id] += 1
        
        # Topological sort
        queue = deque([step_id for step_id in in_degree if in_degree[step_id] == 0])
        sorted_step_ids = []
        
        while queue:
            step_id = queue.popleft()
            sorted_step_ids.append(step_id)
            
            for neighbor in graph[step_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Map back to steps
        step_id_map = {step.step_id: step for step in steps}
        return [step_id_map[step_id] for step_id in sorted_step_ids if step_id in step_id_map]
    
    async def _analyze_critical_path(self, steps: List[ExecutionStep]) -> CriticalPath:
        """Analyze critical path in execution sequence."""
        if not steps:
            return CriticalPath(
                path_steps=[],
                total_duration=timedelta(0),
                bottlenecks=[],
                optimization_opportunities=[],
                parallel_opportunities=[]
            )
        
        # Find longest path (critical path)
        path_steps = [step.step_id for step in steps]
        total_duration = sum(
            (step.estimated_duration or timedelta(0) for step in steps),
            timedelta(0)
        )
        
        # Identify bottlenecks (steps with longest duration)
        bottlenecks = [
            step.step_id for step in steps
            if step.estimated_duration and step.estimated_duration > timedelta(hours=16)
        ]
        
        # Identify optimization opportunities
        optimization_opportunities = [
            "Consider parallel execution for independent tasks",
            "Break down complex tasks into smaller units",
            "Optimize resource allocation"
        ]
        
        # Identify parallel opportunities
        parallel_opportunities = await self._identify_parallel_opportunities(steps)
        
        return CriticalPath(
            path_steps=path_steps,
            total_duration=total_duration,
            bottlenecks=bottlenecks,
            optimization_opportunities=optimization_opportunities,
            parallel_opportunities=parallel_opportunities
        )
    
    async def _identify_parallel_opportunities(
        self, 
        steps: List[ExecutionStep]
    ) -> List[List[str]]:
        """Identify steps that can be executed in parallel."""
        parallel_groups = []
        
        # Group steps by dependencies
        independent_steps = [
            step.step_id for step in steps 
            if not step.dependencies and step.parallel_eligible
        ]
        
        if len(independent_steps) > 1:
            parallel_groups.append(independent_steps)
        
        return parallel_groups
    
    async def _assess_execution_risks(
        self,
        steps: List[ExecutionStep],
        hierarchy_analysis: Optional[HierarchyAnalysis]
    ) -> RiskAssessment:
        """Assess execution risks for the plan."""
        risk_factors = []
        high_risk_steps = []
        
        for step in steps:
            # Assess complexity risk
            if step.ai_guidance and step.ai_guidance.estimated_complexity == "complex":
                risk_factors.append(RiskFactor(
                    risk_id=generate_uuid(),
                    description=f"High complexity task: {step.title}",
                    probability=0.7,
                    impact=RiskLevel.HIGH,
                    affected_steps=[step.step_id],
                    mitigation_strategies=[
                        "Break down into smaller tasks",
                        "Increase testing coverage",
                        "Add additional review checkpoints"
                    ]
                ))
                high_risk_steps.append(step.step_id)
            
            # Assess dependency risk
            if len(step.dependencies) > 3:
                risk_factors.append(RiskFactor(
                    risk_id=generate_uuid(),
                    description=f"High dependency count: {step.title}",
                    probability=0.5,
                    impact=RiskLevel.MEDIUM,
                    affected_steps=[step.step_id],
                    mitigation_strategies=[
                        "Validate dependencies early",
                        "Create fallback plans",
                        "Implement dependency monitoring"
                    ]
                ))
        
        # Determine overall risk level
        overall_risk = RiskLevel.LOW
        if len(high_risk_steps) > len(steps) * 0.3:
            overall_risk = RiskLevel.HIGH
        elif len(high_risk_steps) > 0:
            overall_risk = RiskLevel.MEDIUM
        
        return RiskAssessment(
            overall_risk_level=overall_risk,
            risk_factors=risk_factors,
            high_risk_steps=high_risk_steps,
            recommended_mitigations=[
                "Implement comprehensive testing strategy",
                "Establish clear communication channels",
                "Create detailed rollback procedures"
            ],
            monitoring_points=[
                "Dependency validation checkpoints",
                "Progress milestone reviews",
                "Quality gate assessments"
            ]
        )
    
    async def _optimize_resource_allocation(
        self,
        steps: List[ExecutionStep],
        context: PlanningContext
    ) -> ResourceAllocation:
        """Optimize resource allocation for execution steps."""
        # Simple round-robin allocation for now
        agent_assignments = defaultdict(list)
        
        if context.target_agent:
            # Assign all to target agent
            agent_assignments[context.target_agent] = [step.step_id for step in steps]
        else:
            # Distribute across available capacity
            for i, step in enumerate(steps):
                agent_id = f"agent_{i % 3}"  # Distribute across 3 agents
                agent_assignments[agent_id].append(step.step_id)
        
        return ResourceAllocation(
            agent_assignments=dict(agent_assignments),
            parallel_capacity=context.resource_limits.get("max_parallel_tasks", 3),
            optimization_score=0.8  # Mock score
        )
    
    async def _calculate_estimates(
        self, 
        steps: List[ExecutionStep]
    ) -> Tuple[Optional[timedelta], Optional[float]]:
        """Calculate total duration and effort estimates."""
        total_duration = sum(
            (step.estimated_duration or timedelta(0) for step in steps),
            timedelta(0)
        )
        
        # Mock effort calculation (story points)
        total_effort = len(steps) * 5.0  # 5 story points per step average
        
        return total_duration, total_effort
    
    async def _calculate_confidence_score(
        self,
        steps: List[ExecutionStep],
        risk_assessment: RiskAssessment
    ) -> float:
        """Calculate confidence score for the plan."""
        base_score = 0.8
        
        # Reduce confidence based on risk level
        risk_penalty = {
            RiskLevel.LOW: 0.0,
            RiskLevel.MEDIUM: 0.1,
            RiskLevel.HIGH: 0.3,
            RiskLevel.CRITICAL: 0.5
        }
        
        penalty = risk_penalty.get(risk_assessment.overall_risk_level, 0.0)
        
        # Reduce confidence for complex steps
        complex_steps = sum(
            1 for step in steps
            if step.ai_guidance and step.ai_guidance.estimated_complexity == "complex"
        )
        complexity_penalty = min(complex_steps * 0.05, 0.2)
        
        return max(0.1, base_score - penalty - complexity_penalty)
    
    async def _identify_optimizations(
        self,
        steps: List[ExecutionStep],
        critical_path: CriticalPath
    ) -> List[str]:
        """Identify optimization opportunities."""
        optimizations = []
        
        # Check for parallelization opportunities
        if critical_path.parallel_opportunities:
            optimizations.append(
                f"Parallelize {len(critical_path.parallel_opportunities)} groups of independent tasks"
            )
        
        # Check for bottlenecks
        if critical_path.bottlenecks:
            optimizations.append(
                f"Address {len(critical_path.bottlenecks)} identified bottlenecks"
            )
        
        # Check for resource optimization
        if len(steps) > 5:
            optimizations.append("Consider load balancing across multiple agents")
        
        return optimizations
    
    async def _optimize_for_parallelism(
        self, 
        steps: List[ExecutionStep]
    ) -> List[ExecutionStep]:
        """Optimize execution sequence for parallel execution."""
        # Mark independent steps as parallel eligible
        for step in steps:
            if not step.dependencies:
                step.parallel_eligible = True
        
        return steps