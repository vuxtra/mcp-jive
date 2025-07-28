"""Hierarchy Manager Service.

Manages work item hierarchies (Initiative→Epic→Feature→Story→Task)
and provides operations for traversing and manipulating the hierarchy.
"""

import logging
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime

from ..models.workflow import (
    WorkItem,
    WorkItemType,
    WorkItemStatus,
    WorkItemHierarchy,
    ProgressCalculation,
)
from ..database import WeaviateManager
from ..config import ServerConfig

logger = logging.getLogger(__name__)


class HierarchyManager:
    """Manages work item hierarchies and relationships."""
    
    # Define valid parent-child relationships
    HIERARCHY_RULES = {
        WorkItemType.INITIATIVE: [],  # No parents allowed
        WorkItemType.EPIC: [WorkItemType.INITIATIVE],
        WorkItemType.FEATURE: [WorkItemType.EPIC],
        WorkItemType.STORY: [WorkItemType.FEATURE],
        WorkItemType.TASK: [WorkItemType.STORY],
    }
    
    def __init__(self, config: ServerConfig, weaviate_manager: WeaviateManager):
        self.config = config
        self.weaviate_manager = weaviate_manager
        self.collection_name = "WorkItem"
        
    async def initialize(self) -> None:
        """Initialize the hierarchy manager."""
        try:
            # Ensure the WorkItem collection exists
            await self._ensure_collection_exists()
            logger.info("Hierarchy manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize hierarchy manager: {e}")
            raise
    
    async def _ensure_collection_exists(self) -> None:
        """Ensure the WorkItem collection exists in Weaviate."""
        try:
            client = await self.weaviate_manager.get_client()
            
            # Check if collection exists
            if not client.collections.exists(self.collection_name):
                # Create the collection with proper schema
                collection = client.collections.create(
                    name=self.collection_name,
                    properties=[
                        # Core identification
                        {"name": "title", "dataType": ["text"]},
                        {"name": "description", "dataType": ["text"]},
                        {"name": "type", "dataType": ["text"]},
                        {"name": "parent_id", "dataType": ["text"]},
                        {"name": "project_id", "dataType": ["text"]},
                        
                        # Status and priority
                        {"name": "status", "dataType": ["text"]},
                        {"name": "priority", "dataType": ["text"]},
                        
                        # Assignment
                        {"name": "assignee", "dataType": ["text"]},
                        {"name": "reporter", "dataType": ["text"]},
                        
                        # Timing
                        {"name": "created_at", "dataType": ["date"]},
                        {"name": "updated_at", "dataType": ["date"]},
                        {"name": "due_date", "dataType": ["date"]},
                        
                        # Estimation and progress
                        {"name": "estimated_hours", "dataType": ["number"]},
                        {"name": "actual_hours", "dataType": ["number"]},
                        {"name": "progress_percentage", "dataType": ["number"]},
                        
                        # Autonomous execution
                        {"name": "autonomous_executable", "dataType": ["boolean"]},
                        {"name": "execution_instructions", "dataType": ["text"]},
                        
                        # Metadata
                        {"name": "tags", "dataType": ["text[]"]},
                        {"name": "labels", "dataType": ["object"]},
                        {"name": "custom_fields", "dataType": ["object"]},
                        
                        # Dependencies
                        {"name": "dependencies", "dataType": ["text[]"]},
                    ]
                )
                logger.info(f"Created {self.collection_name} collection")
            else:
                logger.info(f"{self.collection_name} collection already exists")
                
        except Exception as e:
            logger.error(f"Failed to ensure collection exists: {e}")
            raise
    
    async def get_children(self, parent_id: str, include_nested: bool = False) -> List[WorkItem]:
        """Get direct children of a work item.
        
        Args:
            parent_id: ID of the parent work item
            include_nested: If True, include all nested children recursively
            
        Returns:
            List of child work items
        """
        try:
            client = await self.weaviate_manager.get_client()
            collection = client.collections.get(self.collection_name)
            
            # Query for direct children
            response = collection.query.fetch_objects(
                where={
                    "path": ["parent_id"],
                    "operator": "Equal",
                    "valueText": parent_id
                },
                limit=1000  # Reasonable limit for children
            )
            
            children = []
            for obj in response.objects:
                work_item = self._weaviate_to_work_item(obj)
                children.append(work_item)
            
            if include_nested:
                # Recursively get nested children
                all_children = children.copy()
                for child in children:
                    nested = await self.get_children(child.id, include_nested=True)
                    all_children.extend(nested)
                return all_children
            
            return children
            
        except Exception as e:
            logger.error(f"Failed to get children for {parent_id}: {e}")
            raise
    
    async def get_hierarchy(self, root_id: str, max_depth: int = 10) -> WorkItemHierarchy:
        """Get the complete hierarchy starting from a root work item.
        
        Args:
            root_id: ID of the root work item
            max_depth: Maximum depth to traverse
            
        Returns:
            WorkItemHierarchy with nested children
        """
        try:
            # Get the root work item
            root_item = await self.get_work_item(root_id)
            if not root_item:
                raise ValueError(f"Work item {root_id} not found")
            
            # Build hierarchy recursively
            hierarchy = await self._build_hierarchy_recursive(
                root_item, depth=0, max_depth=max_depth, path=[root_id]
            )
            
            return hierarchy
            
        except Exception as e:
            logger.error(f"Failed to get hierarchy for {root_id}: {e}")
            raise
    
    async def _build_hierarchy_recursive(
        self, 
        work_item: WorkItem, 
        depth: int, 
        max_depth: int, 
        path: List[str]
    ) -> WorkItemHierarchy:
        """Recursively build the work item hierarchy."""
        if depth >= max_depth:
            return WorkItemHierarchy(
                work_item=work_item,
                children=[],
                depth=depth,
                path=path
            )
        
        # Get direct children
        children_items = await self.get_children(work_item.id)
        children_hierarchies = []
        
        for child in children_items:
            # Prevent circular references
            if child.id not in path:
                child_path = path + [child.id]
                child_hierarchy = await self._build_hierarchy_recursive(
                    child, depth + 1, max_depth, child_path
                )
                children_hierarchies.append(child_hierarchy)
        
        return WorkItemHierarchy(
            work_item=work_item,
            children=children_hierarchies,
            depth=depth,
            path=path
        )
    
    async def get_work_item(self, work_item_id: str) -> Optional[WorkItem]:
        """Get a work item by ID."""
        try:
            client = await self.weaviate_manager.get_client()
            collection = client.collections.get(self.collection_name)
            
            # Try to get by UUID first
            try:
                response = collection.query.fetch_object_by_id(work_item_id)
                if response:
                    return self._weaviate_to_work_item(response)
            except Exception:
                # If UUID lookup fails, try searching by title or other fields
                # This is a fallback for cases where work_item_id might not be a UUID
                pass
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get work item {work_item_id}: {e}")
            raise
    
    async def validate_hierarchy_rules(self, work_item: WorkItem) -> Tuple[bool, List[str]]:
        """Validate that a work item follows hierarchy rules.
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        try:
            # Check if parent_id is provided for non-initiative items
            if work_item.type != WorkItemType.INITIATIVE and not work_item.parent_id:
                errors.append(f"{work_item.type.value} items must have a parent")
            
            # Check if initiative has no parent
            if work_item.type == WorkItemType.INITIATIVE and work_item.parent_id:
                errors.append("Initiative items cannot have a parent")
            
            # If parent_id is provided, validate the relationship
            if work_item.parent_id:
                parent = await self.get_work_item(work_item.parent_id)
                if not parent:
                    errors.append(f"Parent work item {work_item.parent_id} not found")
                else:
                    # Check if parent type is valid for this child type
                    valid_parent_types = self.HIERARCHY_RULES.get(work_item.type, [])
                    if parent.type not in valid_parent_types:
                        errors.append(
                            f"{work_item.type.value} cannot be a child of {parent.type.value}"
                        )
            
            return len(errors) == 0, errors
            
        except Exception as e:
            logger.error(f"Failed to validate hierarchy rules: {e}")
            errors.append(f"Validation error: {str(e)}")
            return False, errors
    
    async def calculate_progress(self, work_item_id: str) -> ProgressCalculation:
        """Calculate progress for a work item including its children.
        
        Progress is calculated as:
        - If no children: use direct progress
        - If has children: weighted average of children's progress
        """
        try:
            work_item = await self.get_work_item(work_item_id)
            if not work_item:
                raise ValueError(f"Work item {work_item_id} not found")
            
            children = await self.get_children(work_item_id)
            
            if not children:
                # No children, use direct progress
                return ProgressCalculation(
                    work_item_id=work_item_id,
                    direct_progress=work_item.progress_percentage,
                    calculated_progress=work_item.progress_percentage,
                    child_count=0,
                    completed_children=0,
                    calculation_method="direct"
                )
            
            # Calculate based on children
            total_progress = 0.0
            completed_count = 0
            
            for child in children:
                child_calc = await self.calculate_progress(child.id)
                total_progress += child_calc.calculated_progress
                if child_calc.calculated_progress >= 100.0:
                    completed_count += 1
            
            calculated_progress = total_progress / len(children) if children else 0.0
            
            return ProgressCalculation(
                work_item_id=work_item_id,
                direct_progress=work_item.progress_percentage,
                calculated_progress=calculated_progress,
                child_count=len(children),
                completed_children=completed_count,
                calculation_method="children_average"
            )
            
        except Exception as e:
            logger.error(f"Failed to calculate progress for {work_item_id}: {e}")
            raise
    
    async def get_ancestors(self, work_item_id: str) -> List[WorkItem]:
        """Get all ancestors of a work item up to the root."""
        ancestors = []
        current_id = work_item_id
        
        try:
            while current_id:
                work_item = await self.get_work_item(current_id)
                if not work_item:
                    break
                
                if work_item.parent_id:
                    parent = await self.get_work_item(work_item.parent_id)
                    if parent:
                        ancestors.append(parent)
                        current_id = parent.id
                    else:
                        break
                else:
                    break
            
            return ancestors
            
        except Exception as e:
            logger.error(f"Failed to get ancestors for {work_item_id}: {e}")
            raise
    
    def _weaviate_to_work_item(self, weaviate_obj) -> WorkItem:
        """Convert Weaviate object to WorkItem model."""
        properties = weaviate_obj.properties
        
        # Handle datetime fields
        created_at = properties.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        
        updated_at = properties.get('updated_at')
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
        
        due_date = properties.get('due_date')
        if isinstance(due_date, str):
            due_date = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
        
        return WorkItem(
            id=str(weaviate_obj.uuid),
            title=properties.get('title', ''),
            description=properties.get('description'),
            type=WorkItemType(properties.get('type', 'task')),
            parent_id=properties.get('parent_id'),
            project_id=properties.get('project_id', ''),
            status=WorkItemStatus(properties.get('status', 'backlog')),
            priority=properties.get('priority', 'medium'),
            assignee=properties.get('assignee'),
            reporter=properties.get('reporter', ''),
            created_at=created_at or datetime.utcnow(),
            updated_at=updated_at or datetime.utcnow(),
            due_date=due_date,
            estimated_hours=properties.get('estimated_hours'),
            actual_hours=properties.get('actual_hours'),
            progress_percentage=properties.get('progress_percentage', 0.0),
            autonomous_executable=properties.get('autonomous_executable', False),
            execution_instructions=properties.get('execution_instructions'),
            tags=properties.get('tags', []),
            labels=properties.get('labels', {}),
            custom_fields=properties.get('custom_fields', {}),
            dependencies=properties.get('dependencies', []),
        )
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        logger.info("Hierarchy manager cleanup completed")