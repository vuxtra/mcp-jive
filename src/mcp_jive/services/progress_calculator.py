"""Unified Progress Calculator Service.

Provides consistent progress calculation and automatic propagation
across the entire work item hierarchy.
"""

import logging
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime

from ..models.workflow import (
    WorkItem,
    WorkItemType,
    WorkItemStatus,
    ProgressCalculation,
)
# Removed direct import to avoid circular dependency
# WorkItemStorage will be injected as dependency

logger = logging.getLogger(__name__)


class ProgressCalculator:
    """Unified progress calculation service."""
    
    def __init__(self, storage):
        """Initialize progress calculator with storage dependency.
        
        Args:
            storage: WorkItemStorage instance (injected dependency)
        """
        self.storage = storage
        self.logger = logging.getLogger(__name__)
        
    async def calculate_work_item_progress(self, work_item_id: str) -> float:
        """Calculate progress for a single work item.
        
        Args:
            work_item_id: ID of the work item
            
        Returns:
            Progress percentage (0-100)
        """
        try:
            work_item = await self.storage.get_work_item(work_item_id)
            if not work_item:
                self.logger.warning(f"Work item not found: {work_item_id}")
                return 0.0
                
            # Get children to determine if this is a leaf node
            children = await self._get_children(work_item_id)
            
            if not children:
                # Leaf node - use explicit progress if set, otherwise calculate from status
                if work_item.get("progress") is not None:
                    return float(work_item["progress"])
                else:
                    return self._calculate_leaf_progress(work_item)
            else:
                # Parent node - always calculate based on children, ignore explicit progress
                return await self._calculate_parent_progress(children)
                
        except Exception as e:
            self.logger.error(f"Failed to calculate progress for {work_item_id}: {e}")
            return 0.0
            
    def _calculate_leaf_progress(self, work_item: Dict) -> float:
        """Calculate progress for a leaf work item based on its status.
        
        Args:
            work_item: Work item data
            
        Returns:
            Progress percentage (0-100)
        """
        status = work_item.get("status", "not_started")
        
        # Unified status-to-progress mapping
        status_progress_map = {
            "completed": 100.0,
            "done": 100.0,  # Backend uses 'done'
            "in_progress": 50.0,  # More conservative than frontend's 60%
            "blocked": 25.0,  # Slightly less than frontend's 30%
            "not_started": 0.0,
            "backlog": 0.0,  # Backend uses 'backlog'
            "cancelled": 0.0,
        }
        
        return status_progress_map.get(status.lower(), 0.0)
        
    async def _calculate_parent_progress(self, children: List[Dict]) -> float:
        """Calculate progress for a parent work item based on its children.
        
        Args:
            children: List of child work items
            
        Returns:
            Progress percentage (0-100)
        """
        if not children:
            return 0.0
            
        total_progress = 0.0
        total_children = len(children)
        
        for child in children:
            # For leaf nodes (children with no children), always calculate from status
            # to ensure consistency between status and progress
            child_children = await self._get_children(child["id"])
            
            if not child_children:
                # Leaf node - calculate from status to ensure consistency
                child_progress = self._calculate_leaf_progress(child)
            else:
                # Parent node - use stored progress or calculate recursively
                child_progress = child.get("progress")
                if child_progress is not None:
                    child_progress = float(child_progress)
                else:
                    # Recursively calculate for parent children
                    child_progress = await self._calculate_parent_progress(child_children)
            
            total_progress += child_progress
            
        return total_progress / total_children if total_children > 0 else 0.0
        
    async def update_work_item_progress(self, work_item_id: str, 
                                      progress: Optional[float] = None,
                                      status: Optional[str] = None,
                                      propagate: bool = True) -> Dict[str, any]:
        """Update work item progress and optionally propagate to parents.
        
        Args:
            work_item_id: ID of the work item to update
            progress: Explicit progress percentage (0-100)
            status: New status for the work item
            propagate: Whether to propagate changes to parent items
            
        Returns:
            Dict with update results and affected items
        """
        try:
            work_item = await self.storage.get_work_item(work_item_id)
            if not work_item:
                return {
                    "success": False,
                    "error": f"Work item not found: {work_item_id}"
                }
                
            update_data = {}
            affected_items = [work_item_id]
            
            # Handle status update
            if status:
                update_data["status"] = status
                
                # Auto-set progress based on status if not explicitly provided
                if progress is None:
                    if status.lower() in ["completed", "done"]:
                        update_data["progress"] = 100.0
                        update_data["completed_at"] = datetime.now().isoformat()
                    elif status.lower() in ["not_started", "backlog"]:
                        update_data["progress"] = 0.0
                    elif status.lower() == "in_progress":
                        # Only set progress if not already set
                        if work_item.get("progress") is None:
                            update_data["progress"] = 50.0
                            
            # Handle explicit progress update
            if progress is not None:
                update_data["progress"] = max(0.0, min(100.0, float(progress)))
                
                # Auto-update status based on progress if not explicitly provided
                if status is None:
                    if progress >= 100.0:
                        update_data["status"] = "completed"
                        update_data["completed_at"] = datetime.now().isoformat()
                    elif progress > 0.0:
                        update_data["status"] = "in_progress"
                    else:
                        update_data["status"] = "not_started"
                        
            # Update the work item
            if update_data:
                await self.storage.update_work_item(work_item_id, update_data)
                self.logger.info(f"Updated progress for {work_item_id}: {update_data}")
                
            # Propagate changes to parent hierarchy
            if propagate:
                parent_updates = await self._propagate_progress_to_parents(work_item_id)
                affected_items.extend(parent_updates)
                
            return {
                "success": True,
                "work_item_id": work_item_id,
                "updates": update_data,
                "affected_items": affected_items,
                "message": f"Progress updated for {len(affected_items)} items"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to update progress for {work_item_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
            
    async def _propagate_progress_to_parents(self, work_item_id: str) -> List[str]:
        """Propagate progress changes up the hierarchy.
        
        Args:
            work_item_id: ID of the work item that was updated
            
        Returns:
            List of parent work item IDs that were updated
        """
        updated_parents = []
        
        try:
            # Get the work item to find its parent
            work_item = await self.storage.get_work_item(work_item_id)
            if not work_item or not work_item.get("parent_id"):
                return updated_parents
                
            parent_id = work_item["parent_id"]
            
            # Calculate new progress for the parent
            children = await self._get_children(parent_id)
            if children:
                new_progress = await self._calculate_parent_progress(children)
                
                # Determine if parent status should be updated based on children
                update_data = {
                    "progress": new_progress,
                    "updated_at": datetime.now().isoformat()
                }
                
                # Check if all children are completed to update parent status
                all_completed = all(
                    child.get("status", "").lower() in ["completed", "done"] 
                    for child in children
                )
                
                # Check if any children are in progress
                any_in_progress = any(
                    child.get("status", "").lower() == "in_progress" 
                    for child in children
                )
                
                # Update parent status based on children's status
                if all_completed and new_progress >= 100.0:
                    update_data["status"] = "completed"
                    update_data["completed_at"] = datetime.now().isoformat()
                elif any_in_progress or new_progress > 0.0:
                    # Only update to in_progress if not already completed
                    parent_item = await self.storage.get_work_item(parent_id)
                    if parent_item and parent_item.get("status", "").lower() != "completed":
                        update_data["status"] = "in_progress"
                
                # Update parent progress and status
                await self.storage.update_work_item(parent_id, update_data)
                
                updated_parents.append(parent_id)
                self.logger.info(f"Updated parent {parent_id} progress to {new_progress}%")
                
                # Recursively propagate to grandparents
                grandparent_updates = await self._propagate_progress_to_parents(parent_id)
                updated_parents.extend(grandparent_updates)
                
        except Exception as e:
            self.logger.error(f"Failed to propagate progress from {work_item_id}: {e}")
            
        return updated_parents
        
    async def _get_children(self, parent_id: str) -> List[Dict]:
        """Get direct children of a work item.
        
        Args:
            parent_id: ID of the parent work item
            
        Returns:
            List of child work items
        """
        try:
            # Get all work items and filter by parent_id
            all_items = await self.storage.list_work_items(limit=10000)
            children = [item for item in all_items if item.get("parent_id") == parent_id]
            return children
        except Exception as e:
            self.logger.error(f"Failed to get children for {parent_id}: {e}")
            return []
            
    async def recalculate_hierarchy_progress(self, root_id: Optional[str] = None) -> Dict[str, any]:
        """Recalculate progress for an entire hierarchy.
        
        Args:
            root_id: Root work item ID (if None, recalculates all)
            
        Returns:
            Dict with recalculation results
        """
        try:
            updated_items = []
            
            if root_id:
                # Recalculate specific hierarchy
                updated_items = await self._recalculate_subtree(root_id)
            else:
                # Recalculate all hierarchies (find root items)
                all_items = await self.storage.list_work_items(limit=10000)
                root_items = [item for item in all_items if not item.get("parent_id")]
                
                for root_item in root_items:
                    subtree_updates = await self._recalculate_subtree(root_item["id"])
                    updated_items.extend(subtree_updates)
                    
            return {
                "success": True,
                "updated_items": updated_items,
                "count": len(updated_items),
                "message": f"Recalculated progress for {len(updated_items)} items"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to recalculate hierarchy progress: {e}")
            return {
                "success": False,
                "error": str(e)
            }
            
    async def _recalculate_subtree(self, work_item_id: str) -> List[str]:
        """Recalculate progress for a work item and all its descendants.
        
        Args:
            work_item_id: Root of the subtree to recalculate
            
        Returns:
            List of updated work item IDs
        """
        updated_items = []
        
        try:
            # Get children first
            children = await self._get_children(work_item_id)
            
            # Recursively recalculate children first (bottom-up)
            for child in children:
                child_updates = await self._recalculate_subtree(child["id"])
                updated_items.extend(child_updates)
                
            # Now recalculate this item's progress
            new_progress = await self.calculate_work_item_progress(work_item_id)
            
            # Update if progress changed
            work_item = await self.storage.get_work_item(work_item_id)
            current_progress = work_item.get("progress", 0)
            
            if abs(new_progress - current_progress) > 0.01:  # Avoid unnecessary updates
                await self.storage.update_work_item(work_item_id, {
                    "progress": new_progress,
                    "updated_at": datetime.now().isoformat()
                })
                updated_items.append(work_item_id)
                self.logger.info(f"Recalculated {work_item_id} progress: {current_progress}% -> {new_progress}%")
                
        except Exception as e:
            self.logger.error(f"Failed to recalculate subtree for {work_item_id}: {e}")
            
        return updated_items