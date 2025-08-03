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
from mcp_jive.lancedb_manager import LanceDBManager
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
    
    def __init__(self, config: ServerConfig, lancedb_manager: LanceDBManager):
        self.config = config
        self.lancedb_manager = lancedb_manager
        self.collection_name = "WorkItem"
        self.logger = logging.getLogger(__name__)
        
    async def initialize(self) -> None:
        """Initialize the hierarchy manager."""
        try:
            # Ensure the WorkItem collection exists
            await self._ensure_collection_exists()
            self.logger.info("Hierarchy manager initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize hierarchy manager: {e}")
            raise
    
    async def _ensure_collection_exists(self) -> None:
        """Ensure the WorkItem table exists in LanceDB."""
        try:
            # LanceDB tables are created automatically when first accessed
            # Just ensure the database connection is working
            await self.lancedb_manager.ensure_tables_exist()
            self.logger.info(f"✅ LanceDB table '{self.collection_name}' ready")
        except Exception as e:
            self.logger.error(f"Failed to ensure table exists: {e}")
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
            # Query LanceDB for work items with the specified parent_id
            results = await self.lancedb_manager.search_work_items(
                query_text="",
                filters={"parent_id": parent_id},
                limit=1000
            )
            
            children = []
            for result in results:
                # Convert result to WorkItem with proper field mapping
                from ..models.workflow import WorkItemType, WorkItemStatus, Priority
                
                # Convert string values to enums
                item_type_str = result.get("item_type", "task")
                try:
                    work_item_type = WorkItemType(item_type_str)
                except ValueError:
                    work_item_type = WorkItemType.TASK
                
                status_str = result.get("status", "backlog")
                try:
                    work_item_status = WorkItemStatus(status_str)
                except ValueError:
                    work_item_status = WorkItemStatus.BACKLOG
                
                priority_str = result.get("priority", "medium")
                try:
                    work_item_priority = Priority(priority_str)
                except ValueError:
                    work_item_priority = Priority.MEDIUM
                
                work_item = WorkItem(
                    id=result.get("id", ""),
                    title=result.get("title", ""),
                    description=result.get("description", ""),
                    type=work_item_type,  # Correct field name
                    status=work_item_status,
                    priority=work_item_priority,
                    parent_id=result.get("parent_id"),
                    project_id=result.get("project_id", "default-project"),  # Required field with default
                    assignee=result.get("assignee"),  # Correct field name
                    reporter=result.get("assignee", "system"),  # Required field, use assignee or default
                    created_at=result.get("created_at"),
                    updated_at=result.get("updated_at"),
                    estimated_hours=result.get("estimated_hours"),
                    actual_hours=result.get("actual_hours"),
                    progress_percentage=result.get("progress", 0.0),  # Correct field name
                    tags=result.get("tags", []),
                    dependencies=result.get("dependencies", []),
                    autonomous_executable=result.get("autonomous_executable", False),
                    execution_instructions=result.get("execution_instructions")
                )
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
            self.logger.error(f"Failed to get children for {parent_id}: {e}")
            raise

    async def get_hierarchy(self, root_id: str, max_depth: int = 10) -> WorkItemHierarchy:
        """Get complete hierarchy starting from a root work item.
        
        Args:
            root_id: ID of the root work item
            max_depth: Maximum depth to traverse
            
        Returns:
            Complete hierarchy structure
        """
        try:
            # Get the root work item
            root_item = await self.get_work_item(root_id)
            if not root_item:
                raise ValueError(f"Root work item {root_id} not found")
            
            # Build hierarchy recursively
            hierarchy = await self._build_hierarchy_recursive(
                root_item, max_depth, current_depth=0
            )
            
            return hierarchy
            
        except Exception as e:
            self.logger.error(f"Failed to get hierarchy for {root_id}: {e}")
            raise
    
    async def _build_hierarchy_recursive(
        self, 
        work_item: WorkItem, 
        max_depth: int, 
        current_depth: int
    ) -> WorkItemHierarchy:
        """Recursively build hierarchy structure."""
        children_hierarchies = []
        
        if current_depth < max_depth:
            children = await self.get_children(work_item.id)
            for child in children:
                child_hierarchy = await self._build_hierarchy_recursive(
                    child, max_depth, current_depth + 1
                )
                children_hierarchies.append(child_hierarchy)
        
        return WorkItemHierarchy(
            work_item=work_item,
            children=children_hierarchies,
            depth=current_depth
        )
    
    async def get_work_item(self, work_item_id: str) -> Optional[WorkItem]:
        """Get a work item by ID.
        
        Args:
            work_item_id: ID of the work item
            
        Returns:
            WorkItem if found, None otherwise
        """
        try:
            # Use LanceDB to get the work item
            result = await self.lancedb_manager.get_work_item(work_item_id)
            
            if result:
                # Map LanceDB fields to WorkItem model fields
                from ..models.workflow import WorkItemType, WorkItemStatus, Priority
                
                # Convert string values to enums
                item_type_str = result.get("item_type", "task")
                try:
                    work_item_type = WorkItemType(item_type_str)
                except ValueError:
                    work_item_type = WorkItemType.TASK
                
                status_str = result.get("status", "backlog")
                try:
                    work_item_status = WorkItemStatus(status_str)
                except ValueError:
                    work_item_status = WorkItemStatus.BACKLOG
                
                priority_str = result.get("priority", "medium")
                try:
                    work_item_priority = Priority(priority_str)
                except ValueError:
                    work_item_priority = Priority.MEDIUM
                
                return WorkItem(
                    id=result.get("id", ""),
                    title=result.get("title", ""),
                    description=result.get("description", ""),
                    type=work_item_type,  # Correct field name
                    status=work_item_status,
                    priority=work_item_priority,
                    parent_id=result.get("parent_id"),
                    project_id=result.get("project_id", "default-project"),  # Required field with default
                    assignee=result.get("assignee"),  # Correct field name
                    reporter=result.get("assignee", "system"),  # Required field, use assignee or default
                    created_at=result.get("created_at"),
                    updated_at=result.get("updated_at"),
                    estimated_hours=result.get("estimated_hours"),
                    actual_hours=result.get("actual_hours"),
                    progress_percentage=result.get("progress", 0.0),  # Correct field name
                    tags=result.get("tags", []),
                    dependencies=result.get("dependencies", []),
                    autonomous_executable=result.get("autonomous_executable", False),
                    execution_instructions=result.get("execution_instructions")
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get work item {work_item_id}: {e}")
            return None
    
    async def validate_hierarchy_rules(self, child_type: WorkItemType, parent_id: Optional[str]) -> bool:
        """Validate if a parent-child relationship is allowed.
        
        Args:
            child_type: Type of the child work item
            parent_id: ID of the parent work item (None for root items)
            
        Returns:
            True if relationship is valid, False otherwise
        """
        if parent_id is None:
            # Only initiatives can be root items
            return child_type == WorkItemType.INITIATIVE
        
        # Get parent work item
        parent_item = await self.get_work_item(parent_id)
        if not parent_item:
            return False
        
        # Check if parent type is allowed for this child type
        allowed_parents = self.HIERARCHY_RULES.get(child_type, [])
        return WorkItemType(parent_item.item_type) in allowed_parents
    
    async def calculate_progress(self, work_item_id: str) -> ProgressCalculation:
        """Calculate progress for a work item based on its children.
        
        Args:
            work_item_id: ID of the work item
            
        Returns:
            Progress calculation with completion percentage and status breakdown
        """
        try:
            children = await self.get_children(work_item_id, include_nested=True)
            
            if not children:
                # Leaf node - progress is based on its own status
                work_item = await self.get_work_item(work_item_id)
                if work_item:
                    completion = 100.0 if work_item.status == WorkItemStatus.DONE else 0.0
                    return ProgressCalculation(
                        total_items=1,
                        completed_items=1 if work_item.status == WorkItemStatus.DONE else 0,
                        completion_percentage=completion,
                        status_breakdown={work_item.status: 1}
                    )
            
            # Calculate based on children
            total_items = len(children)
            completed_items = sum(1 for child in children if child.status == WorkItemStatus.DONE)
            completion_percentage = (completed_items / total_items * 100) if total_items > 0 else 0.0
            
            # Status breakdown
            status_breakdown = {}
            for child in children:
                status = WorkItemStatus(child.status)
                status_breakdown[status] = status_breakdown.get(status, 0) + 1
            
            return ProgressCalculation(
                total_items=total_items,
                completed_items=completed_items,
                completion_percentage=completion_percentage,
                status_breakdown=status_breakdown
            )
            
        except Exception as e:
            self.logger.error(f"Failed to calculate progress for {work_item_id}: {e}")
            raise
    
    async def get_ancestors(self, work_item_id: str) -> List[WorkItem]:
        """Get all ancestors of a work item (parent, grandparent, etc.).
        
        Args:
            work_item_id: ID of the work item
            
        Returns:
            List of ancestor work items, ordered from immediate parent to root
        """
        try:
            ancestors = []
            current_item = await self.get_work_item(work_item_id)
            
            while current_item and current_item.parent_id:
                parent = await self.get_work_item(current_item.parent_id)
                if parent:
                    ancestors.append(parent)
                    current_item = parent
                else:
                    break
            
            return ancestors
            
        except Exception as e:
            self.logger.error(f"Failed to get ancestors for {work_item_id}: {e}")
            raise
    
    async def get_root_items(self, project_id: Optional[str] = None) -> List[WorkItem]:
        """Get all root work items (items without parents).
        
        Args:
            project_id: Optional project ID to filter by
            
        Returns:
            List of root work items
        """
        try:
            filters = {"parent_id": None}
            if project_id:
                filters["project_id"] = project_id
            
            results = await self.lancedb_manager.search_work_items(
                query_text="",
                filters=filters,
                limit=1000
            )
            
            root_items = []
            for result in results:
                work_item = WorkItem(
                    id=result.get("id", ""),
                    title=result.get("title", ""),
                    description=result.get("description", ""),
                    item_type=result.get("item_type", "task"),
                    status=result.get("status", "pending"),
                    priority=result.get("priority", "medium"),
                    parent_id=result.get("parent_id"),
                    project_id=result.get("project_id"),
                    created_at=result.get("created_at"),
                    updated_at=result.get("updated_at"),
                    created_by=result.get("created_by"),
                    assigned_to=result.get("assigned_to"),
                    tags=result.get("tags", []),
                    metadata=result.get("metadata", {})
                )
                root_items.append(work_item)
            
            return root_items
            
        except Exception as e:
            self.logger.error(f"Failed to get root items: {e}")
            raise
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        try:
            # LanceDB cleanup is handled by the manager
            self.logger.info("Hierarchy manager cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during hierarchy manager cleanup: {e}")