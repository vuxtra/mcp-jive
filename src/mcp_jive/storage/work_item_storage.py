"""Work Item Storage Implementation.

Provides a unified storage interface for work items using LanceDB as the backend.
This class abstracts the database operations and provides a clean API for
the consolidated tools to interact with work item data.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from uuid import uuid4

from ..lancedb_manager import LanceDBManager
from ..models.workflow import WorkItem, WorkItemType, WorkItemStatus, Priority
# Removed circular import - ProgressCalculator will be injected

logger = logging.getLogger(__name__)


class WorkItemStorage:
    """Storage layer for work items using LanceDB backend."""
    
    def __init__(self, lancedb_manager: Optional[LanceDBManager] = None, progress_calculator=None):
        """Initialize the work item storage.
        
        Args:
            lancedb_manager: LanceDB manager instance
            progress_calculator: Progress calculator instance (injected dependency)
        """
        self.lancedb_manager = lancedb_manager
        self.progress_calculator = progress_calculator
        self.is_initialized = False
        
        # Namespace context
        self.current_namespace: Optional[str] = None
        
    async def initialize(self) -> None:
        """Initialize the storage backend."""
        if self.is_initialized:
            return
            
        if self.lancedb_manager and not self.lancedb_manager._initialized:
            await self.lancedb_manager.initialize()
            
        # Progress calculator should be injected via dependency injection
        # self.progress_calculator is set in __init__ or can be set later
            
        self.is_initialized = True
        logger.info("WorkItemStorage initialized successfully")
        
    async def cleanup(self) -> None:
        """Cleanup storage resources."""
        if self.lancedb_manager:
            await self.lancedb_manager.cleanup()
        self.is_initialized = False
        
    async def create_work_item(self, work_item_data: Union[Dict[str, Any], WorkItem]) -> Dict[str, Any]:
        """Create a new work item.
        
        Args:
            work_item_data: Work item data as dict or WorkItem model
            
        Returns:
            Created work item data
        """
        if not self.lancedb_manager:
            raise RuntimeError("LanceDB manager not available")
            
        # Convert WorkItem model to dict if needed
        if isinstance(work_item_data, WorkItem):
            data = work_item_data.model_dump()
        else:
            data = work_item_data.copy()
            
        # Ensure required fields
        if 'id' not in data:
            data['id'] = str(uuid4())
        if 'created_at' not in data:
            data['created_at'] = datetime.utcnow().isoformat()
        if 'updated_at' not in data:
            data['updated_at'] = datetime.utcnow().isoformat()
            
        # Ensure required list fields have default values
        if 'tags' not in data or data['tags'] is None:
            data['tags'] = []
        if 'dependencies' not in data or data['dependencies'] is None:
            data['dependencies'] = []
        if 'context_tags' not in data or data['context_tags'] is None:
            data['context_tags'] = []
        if 'acceptance_criteria' not in data or data['acceptance_criteria'] is None:
            data['acceptance_criteria'] = []
            
        # Ensure required string fields have default values
        if 'metadata' not in data or data['metadata'] is None:
            data['metadata'] = '{}'
            
        # Map common field names
        if 'type' in data and 'item_type' not in data:
            data['item_type'] = data.pop('type')  # Remove 'type' after mapping
        if 'item_id' not in data:
            data['item_id'] = data['id']
            
        # Generate sequence number and order index if not provided
        if 'sequence_number' not in data or data['sequence_number'] is None:
            sequence_number, order_index = await self._generate_sequence_number(data.get('parent_id'))
            data['sequence_number'] = sequence_number
            data['order_index'] = order_index
        elif 'order_index' not in data or data['order_index'] is None:
            data['order_index'] = 0
            
        # Store in LanceDB
        await self.lancedb_manager.create_work_item(data)
        
        logger.info(f"Created work item: {data['id']}")
        return data
        
    async def get_work_item(self, work_item_id: str) -> Optional[Dict[str, Any]]:
        """Get a work item by ID.
        
        Args:
            work_item_id: Work item ID
            
        Returns:
            Work item data or None if not found
        """
        if not self.lancedb_manager:
            raise RuntimeError("LanceDB manager not available")
            
        try:
            # Search by ID in LanceDB
            table = await self.lancedb_manager.get_table("WorkItem")
            results = table.search().where(f"id = '{work_item_id}'").limit(1).to_pandas()
            
            if len(results) > 0:
                # Convert pandas row to dict
                work_item = results.iloc[0].to_dict()
                # Use LanceDBManager's comprehensive numpy conversion
                work_item = self.lancedb_manager._convert_numpy_to_python(work_item)
                return work_item
            return None
            
        except Exception as e:
            logger.error(f"Error getting work item {work_item_id}: {e}")
            return None
            
    async def update_work_item(self, work_item_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a work item.
        
        Args:
            work_item_id: Work item ID
            updates: Fields to update
            
        Returns:
            Updated work item data
        """
        if not self.lancedb_manager:
            raise RuntimeError("LanceDB manager not available")
            
        # Get existing work item
        existing = await self.get_work_item(work_item_id)
        if not existing:
            raise ValueError(f"Work item {work_item_id} not found")
            
        # Merge updates
        updated_data = existing.copy()
        updated_data.update(updates)
        updated_data['updated_at'] = datetime.utcnow().isoformat()
        
        # Check if parent_id changed - regenerate sequence number if so
        old_parent_id = existing.get('parent_id')
        new_parent_id = updated_data.get('parent_id')
        
        if old_parent_id != new_parent_id:
            # Parent changed, regenerate sequence number
            sequence_number, order_index = await self._generate_sequence_number(new_parent_id)
            updated_data['sequence_number'] = sequence_number
            updated_data['order_index'] = order_index
            logger.info(f"Regenerated sequence number for work item {work_item_id}: {sequence_number}")
        
        # Delete old record and create new one (LanceDB update pattern)
        table = await self.lancedb_manager.get_table("WorkItem")
        table.delete(f"id = '{work_item_id}'")
        
        # Create updated record
        await self.lancedb_manager.create_work_item(updated_data)
        
        # Trigger progress propagation if progress or status changed
        if self.progress_calculator and ('progress' in updates or 'status' in updates):
            try:
                await self.progress_calculator.update_work_item_progress(
                    work_item_id, 
                    progress=updates.get('progress'),
                    status=updates.get('status'),
                    propagate_to_parents=True
                )
                logger.info(f"Progress propagation triggered for work item: {work_item_id}")
            except Exception as e:
                logger.error(f"Error during progress propagation for {work_item_id}: {e}")
        
        logger.info(f"Updated work item: {work_item_id}")
        return updated_data
        
    async def delete_work_item(self, work_item_id: str) -> bool:
        """Delete a work item.
        
        Args:
            work_item_id: Work item ID
            
        Returns:
            True if deleted, False if not found
        """
        if not self.lancedb_manager:
            raise RuntimeError("LanceDB manager not available")
            
        try:
            table = await self.lancedb_manager.get_table("WorkItem")
            table.delete(f"id = '{work_item_id}'")
            logger.info(f"Deleted work item: {work_item_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting work item {work_item_id}: {e}")
            return False
    
    async def batch_update_order_indices(self, updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Batch update order indices for multiple work items.
        
        Args:
            updates: List of dicts with 'id', 'order_index', and 'sequence_number'
            
        Returns:
            Dict with success status and results
        """
        if not self.lancedb_manager:
            raise RuntimeError("LanceDB manager not available")
            
        results = {
            "success": True,
            "updated_count": 0,
            "failed_updates": [],
            "errors": []
        }
        
        try:
            for update in updates:
                work_item_id = update.get('id')
                if not work_item_id:
                    results["errors"].append("Missing work item ID in update")
                    continue
                    
                try:
                    # Get existing work item
                    existing = await self.get_work_item(work_item_id)
                    if not existing:
                        results["failed_updates"].append({
                            "id": work_item_id,
                            "error": "Work item not found"
                        })
                        continue
                    
                    # Update order_index and sequence_number
                    update_data = {
                        "order_index": update.get('order_index', existing.get('order_index', 0)),
                        "sequence_number": update.get('sequence_number', existing.get('sequence_number')),
                        "updated_at": datetime.utcnow().isoformat()
                    }
                    
                    # Update in database
                    await self.update_work_item(work_item_id, update_data)
                    results["updated_count"] += 1
                    
                except Exception as e:
                    results["failed_updates"].append({
                        "id": work_item_id,
                        "error": str(e)
                    })
                    results["errors"].append(f"Failed to update {work_item_id}: {e}")
                    
            if results["failed_updates"] or results["errors"]:
                results["success"] = False
                
            logger.info(f"Batch updated {results['updated_count']} work items")
            return results
            
        except Exception as e:
            logger.error(f"Error in batch update: {e}")
            return {
                "success": False,
                "updated_count": 0,
                "failed_updates": [],
                "errors": [str(e)]
            }
            
    async def get_all_work_items(self) -> List[Dict[str, Any]]:
        """Get all work items without any limit.
        
        Returns:
            List of all work item data
        """
        if not self.lancedb_manager:
            raise RuntimeError("LanceDB manager not available")
            
        try:
            # Get all work items by using a very high limit
            work_items = await self.lancedb_manager.list_work_items(
                filters=None,
                limit=10000,  # High limit to get all items
                offset=0
            )
            
            # Apply comprehensive numpy conversion to all items
            converted_items = []
            for item in work_items:
                converted_item = self.lancedb_manager._convert_numpy_to_python(item)
                converted_items.append(converted_item)
                    
            return converted_items
            
        except Exception as e:
            logger.error(f"Error getting all work items: {e}")
            return []
            
    async def list_work_items(self, 
                             limit: int = 100, 
                             offset: int = 0,
                             filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """List work items with optional filtering.
        
        Args:
            limit: Maximum number of items to return
            offset: Number of items to skip
            filters: Optional filters to apply
            
        Returns:
            List of work item data
        """
        if not self.lancedb_manager:
            raise RuntimeError("LanceDB manager not available")
            
        try:
            # Use the LanceDB manager's list_work_items method which properly handles getting all items
            work_items = await self.lancedb_manager.list_work_items(
                filters=filters,
                limit=limit,
                offset=offset
            )
            
            # Apply comprehensive numpy conversion to all items
            converted_items = []
            for item in work_items:
                converted_item = self.lancedb_manager._convert_numpy_to_python(item)
                converted_items.append(converted_item)
                    
            return converted_items
            
        except Exception as e:
            logger.error(f"Error listing work items: {e}")
            return []
            
    async def search_work_items(self, 
                               query: str, 
                               limit: int = 10,
                               search_type: str = "vector") -> List[Dict[str, Any]]:
        """Search work items using vector similarity or text search.
        
        Args:
            query: Search query
            limit: Maximum number of results
            search_type: Type of search ("vector" or "text")
            
        Returns:
            List of matching work items with scores
        """
        if not self.lancedb_manager:
            raise RuntimeError("LanceDB manager not available")
            
        try:
            if search_type == "vector":
                # Use LanceDB vector search
                results = await self.lancedb_manager.search_work_items(
                    query=query,
                    search_type="vector",
                    limit=limit
                )
            else:
                # Use text-based search
                results = await self.lancedb_manager.search_work_items(
                    query=query,
                    search_type="keyword",
                    limit=limit
                )
                
            return results
            
        except Exception as e:
            logger.error(f"Error searching work items: {e}")
            return []
            
    async def get_work_item_children(self, parent_id: str) -> List[Dict[str, Any]]:
        """Get child work items for a parent.
        
        Args:
            parent_id: Parent work item ID
            
        Returns:
            List of child work items
        """
        return await self.list_work_items(filters={"parent_id": parent_id})
        
    async def query_work_items(self, 
                              filters: Dict[str, Any],
                              limit: int = 100,
                              offset: int = 0) -> Dict[str, Any]:
        """Query work items with complex filters.
        
        Args:
            filters: Query filters
            limit: Maximum number of items
            offset: Number of items to skip
            
        Returns:
            Query results with pagination info
        """
        items = await self.list_work_items(limit=limit, offset=offset, filters=filters)
        
        return {
            "items": items,
            "total": len(items),  # Note: This is approximate for pagination
            "page": (offset // limit) + 1,
            "per_page": limit
        }
    
    async def get_work_item_dependencies(self, work_item_id: str) -> List[Dict[str, Any]]:
        """Get dependencies for a work item.
        
        Args:
            work_item_id: ID of the work item
            
        Returns:
            List of dependency work items
        """
        work_item = await self.get_work_item(work_item_id)
        if not work_item:
            return []
        
        dependencies = work_item.get('dependencies', [])
        if isinstance(dependencies, str):
            try:
                import json
                dependencies = json.loads(dependencies)
            except:
                dependencies = []
        
        dependency_items = []
        for dep_id in dependencies:
            dep_item = await self.get_work_item(dep_id)
            if dep_item:
                dependency_items.append(dep_item)
        
        return dependency_items
    
    async def _generate_sequence_number(self, parent_id: Optional[str] = None) -> tuple[str, int]:
        """Generate sequence number and order index for a work item.
        
        Args:
            parent_id: Parent work item ID (None for top-level items)
            
        Returns:
            Tuple of (sequence_number, order_index)
        """
        if not self.lancedb_manager:
            raise RuntimeError("LanceDB manager not available")
            
        try:
            table = await self.lancedb_manager.get_table("WorkItem")
            
            if parent_id is None:
                # Top-level item - find highest sequence number
                results = table.search().where("parent_id IS NULL OR parent_id = ''").to_pandas()
                if len(results) == 0:
                    return "1", 1
                    
                # Find highest top-level sequence number
                max_sequence = 0
                for _, row in results.iterrows():
                    seq_num = row.get('sequence_number', '0')
                    if seq_num and '.' not in str(seq_num):
                        try:
                            num = int(seq_num)
                            max_sequence = max(max_sequence, num)
                        except (ValueError, TypeError):
                            continue
                            
                next_sequence = max_sequence + 1
                return str(next_sequence), next_sequence
            else:
                # Child item - find parent's sequence and highest child number
                parent_results = table.search().where(f"id = '{parent_id}'").limit(1).to_pandas()
                if len(parent_results) == 0:
                    # Parent not found, treat as top-level
                    return await self._generate_sequence_number(None)
                    
                parent_sequence = parent_results.iloc[0].get('sequence_number', '1')
                
                # Find children of this parent
                children_results = table.search().where(f"parent_id = '{parent_id}'").to_pandas()
                
                # Find highest child sequence number
                max_child_num = 0
                parent_prefix = f"{parent_sequence}."
                
                for _, row in children_results.iterrows():
                    seq_num = str(row.get('sequence_number', ''))
                    if seq_num.startswith(parent_prefix):
                        try:
                            # Extract the child number (e.g., "1.3" -> 3)
                            child_part = seq_num[len(parent_prefix):]
                            if '.' not in child_part:  # Direct child, not grandchild
                                child_num = int(child_part)
                                max_child_num = max(max_child_num, child_num)
                        except (ValueError, TypeError):
                            continue
                            
                next_child_num = max_child_num + 1
                sequence_number = f"{parent_sequence}.{next_child_num}"
                
                # Calculate order index based on parent's order and child position
                parent_order = parent_results.iloc[0].get('order_index', 0)
                order_index = parent_order * 1000 + next_child_num
                
                return sequence_number, order_index
                
        except Exception as e:
            logger.error(f"Error generating sequence number: {e}")
            # Fallback to simple numbering
            return "1", 1
    
    async def regenerate_all_sequence_numbers(self) -> Dict[str, Any]:
        """Regenerate sequence numbers for all work items in proper hierarchical order.
        
        This method will:
        1. Fetch all work items
        2. Build the hierarchy tree
        3. Regenerate sequence numbers in proper order
        4. Update all work items with new sequence numbers
        
        Returns:
            Dict with operation results and statistics
        """
        if not self.lancedb_manager:
            raise RuntimeError("LanceDB manager not available")
            
        try:
            logger.info("Starting sequence number regeneration for all work items")
            
            # Get all work items
            table = await self.lancedb_manager.get_table("WorkItem")
            all_items = table.search().to_pandas()
            
            if len(all_items) == 0:
                return {
                    "success": True,
                    "message": "No work items found",
                    "updated_count": 0
                }
            
            # Convert to dict for easier manipulation
            items_dict = {}
            for _, row in all_items.iterrows():
                item_data = row.to_dict()
                items_dict[item_data['id']] = item_data
            
            # Build hierarchy tree
            root_items = []
            children_map = {}
            
            for item_id, item in items_dict.items():
                parent_id = item.get('parent_id')
                if not parent_id or parent_id == '':
                    root_items.append(item)
                else:
                    if parent_id not in children_map:
                        children_map[parent_id] = []
                    children_map[parent_id].append(item)
            
            # Sort root items by current order_index or creation date
            root_items.sort(key=lambda x: (x.get('order_index', 0), x.get('created_at', '')))
            
            # Recursively assign sequence numbers
            updated_items = []
            
            def assign_sequence_recursive(items: List[Dict], parent_sequence: str = "") -> None:
                for index, item in enumerate(items):
                    # Generate new sequence number
                    if parent_sequence:
                        new_sequence = f"{parent_sequence}.{index + 1}"
                    else:
                        new_sequence = str(index + 1)
                    
                    # Calculate new order index
                    if parent_sequence:
                        # For child items, use parent's order * 1000 + child position
                        parent_order = 0
                        for parent_item in updated_items:
                            if parent_item['id'] == item.get('parent_id'):
                                parent_order = parent_item.get('order_index', 0)
                                break
                        new_order_index = parent_order * 1000 + (index + 1)
                    else:
                        new_order_index = index + 1
                    
                    # Update item data
                    item['sequence_number'] = new_sequence
                    item['order_index'] = new_order_index
                    item['updated_at'] = datetime.utcnow().isoformat()
                    
                    updated_items.append(item)
                    
                    # Process children if any
                    item_id = item['id']
                    if item_id in children_map:
                        # Sort children by current order_index or creation date
                        children = children_map[item_id]
                        children.sort(key=lambda x: (x.get('order_index', 0), x.get('created_at', '')))
                        assign_sequence_recursive(children, new_sequence)
            
            # Start the recursive assignment
            assign_sequence_recursive(root_items)
            
            # Update all items in the database
            update_count = 0
            errors = []
            
            for item in updated_items:
                try:
                    # Update the item in database
                    await self.update_work_item(item['id'], {
                        'sequence_number': item['sequence_number'],
                        'order_index': item['order_index'],
                        'updated_at': item['updated_at']
                    })
                    update_count += 1
                except Exception as e:
                    error_msg = f"Failed to update {item['id']}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            result = {
                "success": len(errors) == 0,
                "message": f"Regenerated sequence numbers for {update_count} work items",
                "updated_count": update_count,
                "total_items": len(all_items),
                "errors": errors
            }
            
            if errors:
                result["message"] += f" with {len(errors)} errors"
            
            logger.info(f"Sequence number regeneration completed: {result['message']}")
            return result
            
        except Exception as e:
            error_msg = f"Error during sequence number regeneration: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "updated_count": 0,
                "total_items": 0,
                "errors": [error_msg]
            }
    
    async def set_namespace_context(self, namespace: str) -> None:
        """Set the current namespace context for storage operations.
        
        Args:
            namespace: Namespace to set as current context
        """
        logger.debug(f"Setting storage namespace context to: {namespace}")
        self.current_namespace = namespace
        
        # If the LanceDB manager supports namespace switching, update it
        if self.lancedb_manager and hasattr(self.lancedb_manager, 'config'):
            # Create a new LanceDB manager with the new namespace
            from ..lancedb_manager import DatabaseConfig, LanceDBManager
            new_config = DatabaseConfig(
                data_path=self.lancedb_manager.config.data_path,
                namespace=namespace,
                embedding_model=self.lancedb_manager.config.embedding_model,
                device=self.lancedb_manager.config.device,
                normalize_embeddings=self.lancedb_manager.config.normalize_embeddings,
                vector_dimension=self.lancedb_manager.config.vector_dimension,
                batch_size=self.lancedb_manager.config.batch_size,
                timeout=self.lancedb_manager.config.timeout,
                enable_fts=self.lancedb_manager.config.enable_fts,
                max_retries=self.lancedb_manager.config.max_retries,
                retry_delay=self.lancedb_manager.config.retry_delay
            )
            self.lancedb_manager = LanceDBManager(new_config)
            await self.lancedb_manager.initialize()
    
    async def clear_namespace_context(self) -> None:
        """Clear the current namespace context."""
        logger.debug("Clearing storage namespace context")
        self.current_namespace = None
        
        # Reset to default namespace
        if self.lancedb_manager and hasattr(self.lancedb_manager, 'config'):
            from ..lancedb_manager import DatabaseConfig, LanceDBManager
            new_config = DatabaseConfig(
                data_path=self.lancedb_manager.config.data_path,
                namespace=None,  # Default namespace
                embedding_model=self.lancedb_manager.config.embedding_model,
                device=self.lancedb_manager.config.device,
                normalize_embeddings=self.lancedb_manager.config.normalize_embeddings,
                vector_dimension=self.lancedb_manager.config.vector_dimension,
                batch_size=self.lancedb_manager.config.batch_size,
                timeout=self.lancedb_manager.config.timeout,
                enable_fts=self.lancedb_manager.config.enable_fts,
                max_retries=self.lancedb_manager.config.max_retries,
                retry_delay=self.lancedb_manager.config.retry_delay
            )
            self.lancedb_manager = LanceDBManager(new_config)
            await self.lancedb_manager.initialize()
    
    def get_current_namespace(self) -> Optional[str]:
        """Get the current namespace context.
        
        Returns:
            Current namespace or None if not set
        """
        return self.current_namespace