"""Dependency Engine Service.

Handles dependency analysis, validation, and graph operations for work items.
Uses NetworkX for dependency graph analysis and cycle detection.
"""

import logging
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime

import networkx as nx

from ..models.workflow import (
    WorkItem,
    WorkItemDependency,
    DependencyType,
    DependencyGraph,
    ValidationResult,
)
from ..database import WeaviateManager
from ..config import ServerConfig

logger = logging.getLogger(__name__)


class DependencyEngine:
    """Manages work item dependencies and performs graph analysis."""
    
    def __init__(self, config: ServerConfig, weaviate_manager: WeaviateManager):
        self.config = config
        self.weaviate_manager = weaviate_manager
        self.dependency_collection = "WorkItemDependency"
        
    async def initialize(self) -> None:
        """Initialize the dependency engine."""
        try:
            # Ensure the dependency collection exists
            await self._ensure_dependency_collection_exists()
            logger.info("Dependency engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize dependency engine: {e}")
            raise
    
    async def _ensure_dependency_collection_exists(self) -> None:
        """Ensure the WorkItemDependency collection exists in Weaviate."""
        try:
            client = await self.weaviate_manager.get_client()
            
            if not client.collections.exists(self.dependency_collection):
                collection = client.collections.create(
                    name=self.dependency_collection,
                    properties=[
                        {"name": "source_id", "dataType": ["text"]},
                        {"name": "target_id", "dataType": ["text"]},
                        {"name": "dependency_type", "dataType": ["text"]},
                        {"name": "description", "dataType": ["text"]},
                        {"name": "created_at", "dataType": ["date"]},
                        {"name": "created_by", "dataType": ["text"]},
                    ]
                )
                logger.info(f"Created {self.dependency_collection} collection")
            else:
                logger.info(f"{self.dependency_collection} collection already exists")
                
        except Exception as e:
            logger.error(f"Failed to ensure dependency collection exists: {e}")
            raise
    
    async def get_dependencies(self, work_item_id: str) -> List[WorkItemDependency]:
        """Get all dependencies for a work item (both incoming and outgoing).
        
        Args:
            work_item_id: ID of the work item
            
        Returns:
            List of dependencies involving this work item
        """
        try:
            client = await self.weaviate_manager.get_client()
            collection = client.collections.get(self.dependency_collection)
            
            # Query for dependencies where this item is either source or target
            source_response = collection.query.fetch_objects(
                where={
                    "path": ["source_id"],
                    "operator": "Equal",
                    "valueText": work_item_id
                },
                limit=1000
            )
            
            target_response = collection.query.fetch_objects(
                where={
                    "path": ["target_id"],
                    "operator": "Equal",
                    "valueText": work_item_id
                },
                limit=1000
            )
            
            dependencies = []
            
            # Process source dependencies (outgoing)
            for obj in source_response.objects:
                dep = self._weaviate_to_dependency(obj)
                dependencies.append(dep)
            
            # Process target dependencies (incoming)
            for obj in target_response.objects:
                dep = self._weaviate_to_dependency(obj)
                dependencies.append(dep)
            
            return dependencies
            
        except Exception as e:
            logger.error(f"Failed to get dependencies for {work_item_id}: {e}")
            raise
    
    async def get_blocking_dependencies(self, work_item_id: str) -> List[WorkItemDependency]:
        """Get dependencies that block this work item from being executed.
        
        Args:
            work_item_id: ID of the work item
            
        Returns:
            List of blocking dependencies
        """
        try:
            client = await self.weaviate_manager.get_client()
            collection = client.collections.get(self.dependency_collection)
            
            # Query for blocking dependencies (where this item is the target)
            response = collection.query.fetch_objects(
                where={
                    "operator": "And",
                    "operands": [
                        {
                            "path": ["target_id"],
                            "operator": "Equal",
                            "valueText": work_item_id
                        },
                        {
                            "path": ["dependency_type"],
                            "operator": "Equal",
                            "valueText": DependencyType.BLOCKS.value
                        }
                    ]
                },
                limit=1000
            )
            
            dependencies = []
            for obj in response.objects:
                dep = self._weaviate_to_dependency(obj)
                dependencies.append(dep)
            
            return dependencies
            
        except Exception as e:
            logger.error(f"Failed to get blocking dependencies for {work_item_id}: {e}")
            raise
    
    async def validate_dependencies(
        self, 
        work_item_ids: List[str],
        check_circular: bool = True,
        check_missing: bool = True,
        suggest_fixes: bool = False
    ) -> ValidationResult:
        """Validate dependencies for a set of work items.
        
        Checks for:
        - Circular dependencies
        - Invalid dependency types
        - Missing work items
        - Orphaned dependencies
        
        Args:
            work_item_ids: List of work item IDs to validate
            
        Returns:
            ValidationResult with validation status and details
        """
        try:
            from ..models.workflow import ValidationError, ValidationWarning, SuggestedFix
            
            errors = []
            warnings = []
            suggested_fixes = []
            circular_dependencies = []
            orphaned_items = []
            
            # Build dependency graph for analysis
            dependency_graph = await self._build_dependency_graph(work_item_ids)
            
            # Create NetworkX directed graph for cycle detection
            nx_graph = nx.DiGraph()
            
            # Add nodes (work items)
            for work_item_id in work_item_ids:
                nx_graph.add_node(work_item_id)
            
            # Add edges (dependencies)
            for dep in dependency_graph.dependencies:
                if dep.dependency_type == DependencyType.BLOCKS:
                    # Source blocks target, so target depends on source
                    nx_graph.add_edge(dep.target_id, dep.source_id)
                elif dep.dependency_type == DependencyType.DEPENDS_ON:
                    # Source depends on target
                    nx_graph.add_edge(dep.source_id, dep.target_id)
            
            # Check for circular dependencies
            if check_circular:
                try:
                    cycles = list(nx.simple_cycles(nx_graph))
                    if cycles:
                        circular_dependencies = cycles
                        for cycle in cycles:
                            cycle_str = ' -> '.join(cycle + [cycle[0]])
                            errors.append(ValidationError(
                                type="circular_dependency",
                                description=f"Circular dependency detected: {cycle_str}",
                                work_items=cycle
                            ))
                            
                            if suggest_fixes:
                                suggested_fixes.append(SuggestedFix(
                                    type="remove_dependency",
                                    description=f"Remove dependency between {cycle[-1]} and {cycle[0]} to break cycle",
                                    action="remove_dependency",
                                    from_work_item=cycle[-1],
                                    to_work_item=cycle[0]
                                ))
                except Exception as e:
                    warnings.append(ValidationWarning(
                        type="cycle_check_error",
                        description=f"Could not check for cycles: {str(e)}"
                    ))
            
            # Check for missing dependencies
            if check_missing:
                for dep in dependency_graph.dependencies:
                    if dep.source_id not in dependency_graph.work_items:
                        errors.append(ValidationError(
                            type="missing_work_item",
                            description=f"Dependency references non-existent source item: {dep.source_id}",
                            work_items=[dep.source_id]
                        ))
                    if dep.target_id not in dependency_graph.work_items:
                        errors.append(ValidationError(
                            type="missing_work_item",
                            description=f"Dependency references non-existent target item: {dep.target_id}",
                            work_items=[dep.target_id]
                        ))
            
            # Check for orphaned items (items without valid parents in hierarchy)
            for work_item_id in work_item_ids:
                work_item = dependency_graph.work_items.get(work_item_id)
                if work_item and work_item.parent_id:
                    if work_item.parent_id not in dependency_graph.work_items:
                        orphaned_items.append(work_item_id)
                        warnings.append(ValidationWarning(
                            type="orphaned_work_item",
                            description=f"Work item {work_item_id} has invalid parent {work_item.parent_id}",
                            work_item_id=work_item_id
                        ))
            
            # Validate dependency types
            for dep in dependency_graph.dependencies:
                if dep.dependency_type not in [DependencyType.BLOCKS, DependencyType.DEPENDS_ON, DependencyType.RELATES_TO]:
                    errors.append(ValidationError(
                        type="invalid_dependency_type",
                        description=f"Invalid dependency type: {dep.dependency_type}",
                        work_items=[dep.source_id, dep.target_id]
                    ))
            
            # Calculate execution order
            execution_order = []
            if not circular_dependencies:
                try:
                    execution_order = list(nx.topological_sort(nx_graph))
                except nx.NetworkXError:
                    warnings.append(ValidationWarning(
                        type="topological_sort_failed",
                        description="Could not determine execution order"
                    ))
            
            # Calculate graph statistics
            graph_stats = {
                "nodes": nx_graph.number_of_nodes(),
                "edges": nx_graph.number_of_edges(),
                "is_dag": nx.is_directed_acyclic_graph(nx_graph),
                "density": nx.density(nx_graph) if nx_graph.number_of_nodes() > 0 else 0.0
            }
            
            is_valid = len(errors) == 0
            
            return ValidationResult(
                is_valid=is_valid,
                total_work_items=len(work_item_ids),
                errors=errors,
                warnings=warnings,
                suggested_fixes=suggested_fixes,
                execution_order=execution_order,
                graph_stats=graph_stats,
                circular_dependencies=circular_dependencies,
                orphaned_items=orphaned_items
            )
            
        except Exception as e:
            logger.error(f"Failed to validate dependencies: {e}")
            from ..models.workflow import ValidationError
            return ValidationResult(
                is_valid=False,
                total_work_items=len(work_item_ids),
                errors=[ValidationError(
                    type="validation_error",
                    description=f"Validation failed: {str(e)}",
                    work_items=work_item_ids
                )],
                warnings=[],
                suggested_fixes=[],
                execution_order=[],
                graph_stats={},
                circular_dependencies=[],
                orphaned_items=[]
            )
    
    async def get_execution_order(self, work_item_ids: List[str]) -> List[str]:
        """Get the optimal execution order for work items based on dependencies.
        
        Uses topological sorting to determine execution order.
        
        Args:
            work_item_ids: List of work item IDs to order
            
        Returns:
            List of work item IDs in execution order
        """
        try:
            # Build dependency graph
            dependency_graph = await self._build_dependency_graph(work_item_ids)
            
            # Create NetworkX directed graph
            nx_graph = nx.DiGraph()
            
            # Add nodes
            for work_item_id in work_item_ids:
                nx_graph.add_node(work_item_id)
            
            # Add edges based on blocking dependencies
            for dep in dependency_graph.dependencies:
                if dep.dependency_type == DependencyType.BLOCKS:
                    # Source blocks target, so target must wait for source
                    nx_graph.add_edge(dep.source_id, dep.target_id)
                elif dep.dependency_type == DependencyType.DEPENDS_ON:
                    # Source depends on target, so source must wait for target
                    nx_graph.add_edge(dep.target_id, dep.source_id)
            
            # Perform topological sort
            try:
                execution_order = list(nx.topological_sort(nx_graph))
                return execution_order
            except nx.NetworkXError as e:
                # Graph has cycles, cannot determine order
                logger.warning(f"Cannot determine execution order due to cycles: {e}")
                return work_item_ids  # Return original order as fallback
            
        except Exception as e:
            logger.error(f"Failed to get execution order: {e}")
            return work_item_ids  # Return original order as fallback
    
    async def _build_dependency_graph(self, work_item_ids: List[str]) -> DependencyGraph:
        """Build a dependency graph for the given work items."""
        work_items = {}
        all_dependencies = []
        
        # Get work items (this would typically come from hierarchy manager)
        # For now, we'll create a simplified version
        from .hierarchy_manager import HierarchyManager
        hierarchy_manager = HierarchyManager(self.config, self.weaviate_manager)
        
        for work_item_id in work_item_ids:
            work_item = await hierarchy_manager.get_work_item(work_item_id)
            if work_item:
                work_items[work_item_id] = work_item
        
        # Get all dependencies for these work items
        for work_item_id in work_item_ids:
            dependencies = await self.get_dependencies(work_item_id)
            all_dependencies.extend(dependencies)
        
        # Remove duplicates
        unique_dependencies = []
        seen_ids = set()
        for dep in all_dependencies:
            if dep.id not in seen_ids:
                unique_dependencies.append(dep)
                seen_ids.add(dep.id)
        
        return DependencyGraph(
            work_items=work_items,
            dependencies=unique_dependencies
        )
    
    async def add_dependency(
        self, 
        source_id: str, 
        target_id: str, 
        dependency_type: DependencyType,
        description: Optional[str] = None,
        created_by: str = "system"
    ) -> WorkItemDependency:
        """Add a new dependency between work items.
        
        Args:
            source_id: ID of the source work item
            target_id: ID of the target work item
            dependency_type: Type of dependency
            description: Optional description
            created_by: User or agent creating the dependency
            
        Returns:
            Created dependency
        """
        try:
            # Validate that this dependency won't create a cycle
            validation = await self.validate_dependencies([source_id, target_id])
            
            dependency = WorkItemDependency(
                source_id=source_id,
                target_id=target_id,
                dependency_type=dependency_type,
                description=description,
                created_by=created_by
            )
            
            # Store in Weaviate
            client = await self.weaviate_manager.get_client()
            collection = client.collections.get(self.dependency_collection)
            
            result = collection.data.insert(
                properties={
                    "source_id": dependency.source_id,
                    "target_id": dependency.target_id,
                    "dependency_type": dependency.dependency_type.value,
                    "description": dependency.description,
                    "created_at": dependency.created_at.isoformat(),
                    "created_by": dependency.created_by,
                }
            )
            
            dependency.id = str(result)
            logger.info(f"Created dependency {dependency.id}: {source_id} -> {target_id}")
            
            return dependency
            
        except Exception as e:
            logger.error(f"Failed to add dependency: {e}")
            raise
    
    async def remove_dependency(self, dependency_id: str) -> bool:
        """Remove a dependency.
        
        Args:
            dependency_id: ID of the dependency to remove
            
        Returns:
            True if removed successfully
        """
        try:
            client = await self.weaviate_manager.get_client()
            collection = client.collections.get(self.dependency_collection)
            
            result = collection.data.delete_by_id(dependency_id)
            
            logger.info(f"Removed dependency {dependency_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove dependency {dependency_id}: {e}")
            return False
    
    def _weaviate_to_dependency(self, weaviate_obj) -> WorkItemDependency:
        """Convert Weaviate object to WorkItemDependency model."""
        properties = weaviate_obj.properties
        
        created_at = properties.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        
        return WorkItemDependency(
            id=str(weaviate_obj.uuid),
            source_id=properties.get('source_id', ''),
            target_id=properties.get('target_id', ''),
            dependency_type=DependencyType(properties.get('dependency_type', 'relates_to')),
            description=properties.get('description'),
            created_at=created_at or datetime.utcnow(),
            created_by=properties.get('created_by', 'unknown'),
        )
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        logger.info("Dependency engine cleanup completed")