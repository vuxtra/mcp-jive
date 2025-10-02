"""Memory Storage Layer for MCP Jive.

Provides storage and retrieval operations for Architecture Memory and Troubleshoot Memory
using LanceDB with full namespace isolation support.
"""

import json
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple
from uuid import uuid4

from ..models.memory import (
    ArchitectureItem,
    TroubleshootItem,
    ArchitectureItemSummary,
    TroubleshootItemMatch
)
from ..lancedb_manager import LanceDBManager

logger = logging.getLogger(__name__)


class ArchitectureMemoryStorage:
    """Storage layer for Architecture Memory items."""

    def __init__(self, db_manager: LanceDBManager):
        """Initialize Architecture Memory storage.

        Args:
            db_manager: LanceDB manager instance
        """
        self.db_manager = db_manager
        self.table_name = "ArchitectureMemory"

    async def create(self, item: ArchitectureItem) -> ArchitectureItem:
        """Create a new architecture item.

        Args:
            item: Architecture item to create

        Returns:
            Created architecture item with ID

        Raises:
            ValueError: If slug already exists
        """
        # Check if slug already exists
        existing = await self.get_by_slug(item.unique_slug)
        if existing:
            raise ValueError(f"Architecture item with slug '{item.unique_slug}' already exists")

        # Ensure ID is set
        if not item.id:
            item.id = str(uuid4())

        # Prepare data for LanceDB
        data = {
            'id': item.id,
            'unique_slug': item.unique_slug,
            'title': item.title,
            'ai_when_to_use': item.ai_when_to_use,
            'ai_requirements': item.ai_requirements,
            'keywords': item.keywords,
            'children_slugs': item.children_slugs,
            'related_slugs': item.related_slugs,
            'linked_epic_ids': item.linked_epic_ids,
            'tags': item.tags,
            'created_on': item.created_on,
            'last_updated_on': datetime.now(timezone.utc),
            'metadata': json.dumps(item.metadata)
        }

        # Add to LanceDB
        await self.db_manager.add_data(
            table_name=self.table_name,
            data=[data],
            text_field='ai_requirements'  # Use requirements for vector embedding
        )

        logger.info(f"Created architecture item: {item.unique_slug} ({item.id})")
        return item

    async def get_by_id(self, item_id: str) -> Optional[ArchitectureItem]:
        """Retrieve architecture item by ID.

        Args:
            item_id: Architecture item ID

        Returns:
            Architecture item or None if not found
        """
        results = await self.db_manager.search_data(
            table_name=self.table_name,
            query=None,
            filters={'id': item_id},
            limit=1
        )

        if not results:
            return None

        return self._to_model(results[0])

    async def get_by_slug(self, slug: str) -> Optional[ArchitectureItem]:
        """Retrieve architecture item by unique slug.

        Args:
            slug: Unique slug

        Returns:
            Architecture item or None if not found
        """
        results = await self.db_manager.search_data(
            table_name=self.table_name,
            query=None,
            filters={'unique_slug': slug.lower()},
            limit=1
        )

        if not results:
            return None

        return self._to_model(results[0])

    async def update(self, item: ArchitectureItem) -> ArchitectureItem:
        """Update an existing architecture item.

        Args:
            item: Architecture item with updates

        Returns:
            Updated architecture item

        Raises:
            ValueError: If item not found
        """
        # Verify item exists
        existing = await self.get_by_id(item.id)
        if not existing:
            raise ValueError(f"Architecture item with ID '{item.id}' not found")

        # Update timestamp
        item.last_updated_on = datetime.now(timezone.utc)

        # Prepare data for update
        data = {
            'id': item.id,
            'unique_slug': item.unique_slug,
            'title': item.title,
            'ai_when_to_use': item.ai_when_to_use,
            'ai_requirements': item.ai_requirements,
            'keywords': item.keywords,
            'children_slugs': item.children_slugs,
            'related_slugs': item.related_slugs,
            'linked_epic_ids': item.linked_epic_ids,
            'tags': item.tags,
            'created_on': item.created_on,
            'last_updated_on': item.last_updated_on,
            'metadata': json.dumps(item.metadata)
        }

        # Update in LanceDB (delete and re-add with new embeddings)
        await self.db_manager.delete_data(
            table_name=self.table_name,
            filters={'id': item.id}
        )

        await self.db_manager.add_data(
            table_name=self.table_name,
            data=[data],
            text_field='ai_requirements'
        )

        logger.info(f"Updated architecture item: {item.unique_slug} ({item.id})")
        return item

    async def delete(self, item_id: str) -> bool:
        """Delete an architecture item.

        Args:
            item_id: Architecture item ID

        Returns:
            True if deleted, False if not found
        """
        # Verify item exists
        existing = await self.get_by_id(item_id)
        if not existing:
            return False

        # Delete from LanceDB
        await self.db_manager.delete_data(
            table_name=self.table_name,
            filters={'id': item_id}
        )

        logger.info(f"Deleted architecture item: {existing.unique_slug} ({item_id})")
        return True

    async def list_all(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ArchitectureItem]:
        """List architecture items with optional filtering.

        Args:
            filters: Optional filters to apply
            limit: Maximum number of items to return
            offset: Number of items to skip

        Returns:
            List of architecture items
        """
        results = await self.db_manager.search_data(
            table_name=self.table_name,
            query=None,
            filters=filters,
            limit=limit
        )

        return [self._to_model(r) for r in results[offset:offset + limit]]

    async def search(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[ArchitectureItem, float]]:
        """Search architecture items using semantic search.

        Args:
            query: Search query
            limit: Maximum number of results
            filters: Optional filters

        Returns:
            List of (ArchitectureItem, relevance_score) tuples
        """
        results = await self.db_manager.search_data(
            table_name=self.table_name,
            query=query,
            filters=filters,
            limit=limit
        )

        return [(self._to_model(r), r.get('_distance', 0.0)) for r in results]

    async def get_children(self, slug: str) -> List[ArchitectureItem]:
        """Get all children of an architecture item.

        Args:
            slug: Parent item slug

        Returns:
            List of child architecture items
        """
        parent = await self.get_by_slug(slug)
        if not parent or not parent.children_slugs:
            return []

        children = []
        for child_slug in parent.children_slugs:
            child = await self.get_by_slug(child_slug)
            if child:
                children.append(child)

        return children

    async def get_related(self, slug: str) -> List[ArchitectureItem]:
        """Get all related architecture items.

        Args:
            slug: Item slug

        Returns:
            List of related architecture items
        """
        item = await self.get_by_slug(slug)
        if not item or not item.related_slugs:
            return []

        related = []
        for related_slug in item.related_slugs:
            related_item = await self.get_by_slug(related_slug)
            if related_item:
                related.append(related_item)

        return related

    def _to_model(self, data: Dict[str, Any]) -> ArchitectureItem:
        """Convert LanceDB data to ArchitectureItem model.

        Args:
            data: Raw data from LanceDB

        Returns:
            ArchitectureItem model instance
        """
        return ArchitectureItem(
            id=data['id'],
            unique_slug=data['unique_slug'],
            title=data['title'],
            ai_when_to_use=data.get('ai_when_to_use', []),
            ai_requirements=data['ai_requirements'],
            keywords=data.get('keywords', []),
            children_slugs=data.get('children_slugs', []),
            related_slugs=data.get('related_slugs', []),
            linked_epic_ids=data.get('linked_epic_ids', []),
            tags=data.get('tags', []),
            created_on=data['created_on'],
            last_updated_on=data['last_updated_on'],
            metadata=json.loads(data.get('metadata', '{}'))
        )


class TroubleshootMemoryStorage:
    """Storage layer for Troubleshoot Memory items."""

    def __init__(self, db_manager: LanceDBManager):
        """Initialize Troubleshoot Memory storage.

        Args:
            db_manager: LanceDB manager instance
        """
        self.db_manager = db_manager
        self.table_name = "TroubleshootMemory"

    async def create(self, item: TroubleshootItem) -> TroubleshootItem:
        """Create a new troubleshoot item.

        Args:
            item: Troubleshoot item to create

        Returns:
            Created troubleshoot item with ID

        Raises:
            ValueError: If slug already exists
        """
        # Check if slug already exists
        existing = await self.get_by_slug(item.unique_slug)
        if existing:
            raise ValueError(f"Troubleshoot item with slug '{item.unique_slug}' already exists")

        # Ensure ID is set
        if not item.id:
            item.id = str(uuid4())

        # Prepare data for LanceDB
        # Combine use cases and solutions for better semantic search
        search_text = f"{' '.join(item.ai_use_case)} {item.ai_solutions}"

        data = {
            'id': item.id,
            'unique_slug': item.unique_slug,
            'title': item.title,
            'ai_use_case': item.ai_use_case,
            'ai_solutions': item.ai_solutions,
            'keywords': item.keywords,
            'tags': item.tags,
            'usage_count': item.usage_count,
            'success_count': item.success_count,
            'created_on': item.created_on,
            'last_updated_on': datetime.now(timezone.utc),
            'metadata': json.dumps(item.metadata)
        }

        # Add to LanceDB
        await self.db_manager.add_data(
            table_name=self.table_name,
            data=[data],
            text_field=search_text  # Combined text for embedding
        )

        logger.info(f"Created troubleshoot item: {item.unique_slug} ({item.id})")
        return item

    async def get_by_id(self, item_id: str) -> Optional[TroubleshootItem]:
        """Retrieve troubleshoot item by ID.

        Args:
            item_id: Troubleshoot item ID

        Returns:
            Troubleshoot item or None if not found
        """
        results = await self.db_manager.search_data(
            table_name=self.table_name,
            query=None,
            filters={'id': item_id},
            limit=1
        )

        if not results:
            return None

        return self._to_model(results[0])

    async def get_by_slug(self, slug: str) -> Optional[TroubleshootItem]:
        """Retrieve troubleshoot item by unique slug.

        Args:
            slug: Unique slug

        Returns:
            Troubleshoot item or None if not found
        """
        results = await self.db_manager.search_data(
            table_name=self.table_name,
            query=None,
            filters={'unique_slug': slug.lower()},
            limit=1
        )

        if not results:
            return None

        return self._to_model(results[0])

    async def update(self, item: TroubleshootItem) -> TroubleshootItem:
        """Update an existing troubleshoot item.

        Args:
            item: Troubleshoot item with updates

        Returns:
            Updated troubleshoot item

        Raises:
            ValueError: If item not found
        """
        # Verify item exists
        existing = await self.get_by_id(item.id)
        if not existing:
            raise ValueError(f"Troubleshoot item with ID '{item.id}' not found")

        # Update timestamp
        item.last_updated_on = datetime.now(timezone.utc)

        # Prepare data for update
        search_text = f"{' '.join(item.ai_use_case)} {item.ai_solutions}"

        data = {
            'id': item.id,
            'unique_slug': item.unique_slug,
            'title': item.title,
            'ai_use_case': item.ai_use_case,
            'ai_solutions': item.ai_solutions,
            'keywords': item.keywords,
            'tags': item.tags,
            'usage_count': item.usage_count,
            'success_count': item.success_count,
            'created_on': item.created_on,
            'last_updated_on': item.last_updated_on,
            'metadata': json.dumps(item.metadata)
        }

        # Update in LanceDB (delete and re-add with new embeddings)
        await self.db_manager.delete_data(
            table_name=self.table_name,
            filters={'id': item.id}
        )

        await self.db_manager.add_data(
            table_name=self.table_name,
            data=[data],
            text_field=search_text
        )

        logger.info(f"Updated troubleshoot item: {item.unique_slug} ({item.id})")
        return item

    async def delete(self, item_id: str) -> bool:
        """Delete a troubleshoot item.

        Args:
            item_id: Troubleshoot item ID

        Returns:
            True if deleted, False if not found
        """
        # Verify item exists
        existing = await self.get_by_id(item_id)
        if not existing:
            return False

        # Delete from LanceDB
        await self.db_manager.delete_data(
            table_name=self.table_name,
            filters={'id': item_id}
        )

        logger.info(f"Deleted troubleshoot item: {existing.unique_slug} ({item_id})")
        return True

    async def list_all(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[TroubleshootItem]:
        """List troubleshoot items with optional filtering.

        Args:
            filters: Optional filters to apply
            limit: Maximum number of items to return
            offset: Number of items to skip

        Returns:
            List of troubleshoot items
        """
        results = await self.db_manager.search_data(
            table_name=self.table_name,
            query=None,
            filters=filters,
            limit=limit
        )

        return [self._to_model(r) for r in results[offset:offset + limit]]

    async def search(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[TroubleshootItem, float]]:
        """Search troubleshoot items using semantic search.

        Args:
            query: Search query (problem description)
            limit: Maximum number of results
            filters: Optional filters

        Returns:
            List of (TroubleshootItem, relevance_score) tuples
        """
        results = await self.db_manager.search_data(
            table_name=self.table_name,
            query=query,
            filters=filters,
            limit=limit
        )

        return [(self._to_model(r), r.get('_distance', 0.0)) for r in results]

    async def increment_usage(self, item_id: str, success: bool = False) -> None:
        """Increment usage count for a troubleshoot item.

        Args:
            item_id: Troubleshoot item ID
            success: Whether the solution was successful
        """
        item = await self.get_by_id(item_id)
        if not item:
            return

        item.usage_count += 1
        if success:
            item.success_count += 1

        await self.update(item)
        logger.info(f"Incremented usage for {item.unique_slug}: usage={item.usage_count}, success={item.success_count}")

    def _to_model(self, data: Dict[str, Any]) -> TroubleshootItem:
        """Convert LanceDB data to TroubleshootItem model.

        Args:
            data: Raw data from LanceDB

        Returns:
            TroubleshootItem model instance
        """
        return TroubleshootItem(
            id=data['id'],
            unique_slug=data['unique_slug'],
            title=data['title'],
            ai_use_case=data.get('ai_use_case', []),
            ai_solutions=data['ai_solutions'],
            keywords=data.get('keywords', []),
            tags=data.get('tags', []),
            usage_count=data.get('usage_count', 0),
            success_count=data.get('success_count', 0),
            created_on=data['created_on'],
            last_updated_on=data['last_updated_on'],
            metadata=json.loads(data.get('metadata', '{}'))
        )